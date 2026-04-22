# =============================================================================
# Dockerfile para OnlineJudge (Backend + Frontend desde cÃ³digo local)
# Build context: directorio raÃ­z del proyecto (donde estÃ¡n OnlineJudge/ y OnlineJudgeFE/)
# =============================================================================

# --- Etapa 1: Compilar el Frontend ---
FROM node:18-alpine AS frontend-builder

# git es necesario porque config/dev.env.js ejecuta "git rev-parse HEAD"
RUN apk add --no-cache git

WORKDIR /fe

# Copiar archivos de dependencias primero (mejor uso de cache de Docker)
COPY ./OnlineJudgeFE/package.json ./OnlineJudgeFE/package-lock.json* ./
RUN npm install --legacy-peer-deps

# Copiar el resto del cÃ³digo fuente del frontend y compilar
COPY ./OnlineJudgeFE/ ./

# Inicializar un repo git dummy (el .git real se excluye por .dockerignore)
# Esto es necesario porque config/dev.env.js ejecuta "git rev-parse HEAD"
RUN git init && git add -A && git -c user.email="build@local" -c user.name="build" commit -m "build" --allow-empty

RUN npm run build:dll && npm run build


# --- Etapa 2: Imagen final del Backend ---
FROM python:3.12-alpine
ARG TARGETARCH
ARG TARGETVARIANT

ENV OJ_ENV production
WORKDIR /app

COPY ./OnlineJudge/deploy/requirements.txt /app/deploy/

# Instalar dependencias del sistema y Python
# psycopg2: libpq-dev
# pillow: libjpeg-turbo-dev zlib-dev freetype-dev
RUN --mount=type=cache,target=/etc/apk/cache,id=apk-cache-$TARGETARCH$TARGETVARIANT-final \
    --mount=type=cache,target=/root/.cache/pip,id=pip-cache-$TARGETARCH$TARGETVARIANT-final \
    set -ex && \
    apk add gcc libc-dev python3-dev libpq libpq-dev libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev freetype freetype-dev supervisor openssl nginx curl unzip && \
    pip install -r /app/deploy/requirements.txt && \
    apk del gcc libc-dev python3-dev libpq-dev libjpeg-turbo-dev zlib-dev freetype-dev

# Copiar cÃ³digo del backend
COPY ./OnlineJudge/ /app/

# Copiar el frontend compilado desde la etapa 1
COPY --from=frontend-builder --link /fe/dist/ /app/dist/

RUN sed -i 's/\r$//' ./deploy/entrypoint.sh && chmod -R u=rwX,go=rX ./ && chmod +x ./deploy/entrypoint.sh

HEALTHCHECK --interval=5s CMD [ "/usr/local/bin/python3", "/app/deploy/health_check.py" ]
EXPOSE 8000
ENTRYPOINT [ "/app/deploy/entrypoint.sh" ]
