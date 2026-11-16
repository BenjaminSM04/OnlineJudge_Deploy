# =============================================================================
# Imagen combinada desde el código de ambos repositorios.
# Contexto: raíz del deploy, con OnlineJudge/ y OnlineJudgeFE/.
# =============================================================================

# --- Etapa 1: Compilar el Frontend ---
FROM node:22-alpine AS frontend-builder

# Git permite instalar dependencias cuyo origen sea un repositorio.
RUN apk add --no-cache git

WORKDIR /fe

# Necesario para webpack 3 con Node 18+
ENV NODE_OPTIONS=--openssl-legacy-provider

# Copiar archivos de dependencias primero (mejor uso de cache de Docker)
COPY ./OnlineJudgeFE/package.json ./OnlineJudgeFE/yarn.lock ./
COPY ./OnlineJudgeFE/build/patch-legacy-dependencies.js ./build/
RUN yarn install --frozen-lockfile --non-interactive

# Copiar el código fuente del frontend y compilar.
COPY ./OnlineJudgeFE/ ./

# El identificador real se suministra desde CI o docker compose build.
ARG FRONTEND_COMMIT=local
ENV SOURCE_COMMIT=$FRONTEND_COMMIT

RUN yarn test:tutor && yarn build:dll && yarn build


# --- Etapa 2: Imagen final del Backend ---
FROM python:3.12-alpine
ARG TARGETARCH
ARG TARGETVARIANT
ARG BACKEND_SOURCE=OnlineJudge

ENV OJ_ENV=production
WORKDIR /app

COPY ${BACKEND_SOURCE}/deploy/requirements.txt /app/deploy/

# Instalar dependencias del sistema y Python
# psycopg2: libpq-dev
# pillow: libjpeg-turbo-dev zlib-dev freetype-dev
RUN --mount=type=cache,target=/etc/apk/cache,id=apk-cache-$TARGETARCH$TARGETVARIANT-final \
    --mount=type=cache,target=/root/.cache/pip,id=pip-cache-$TARGETARCH$TARGETVARIANT-final \
    set -ex && \
    apk add gcc libc-dev python3-dev libpq libpq-dev libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev freetype freetype-dev supervisor openssl nginx curl unzip && \
    pip install -r /app/deploy/requirements.txt && \
    apk del gcc libc-dev python3-dev libpq-dev libjpeg-turbo-dev zlib-dev freetype-dev

# Copiar el código del backend.
COPY ${BACKEND_SOURCE}/ /app/

# Copiar el frontend compilado desde la etapa 1
COPY --from=frontend-builder --link /fe/dist/ /app/dist/

RUN sed -i 's/\r$//' ./deploy/entrypoint.sh && chmod -R u=rwX,go=rX ./ && chmod +x ./deploy/entrypoint.sh

ARG BACKEND_COMMIT=local
ARG FRONTEND_COMMIT=local
ARG INTEGRATION_COMMIT=local
LABEL org.opencontainers.image.revision=$INTEGRATION_COMMIT \
      org.lizardjudge.backend.revision=$BACKEND_COMMIT \
      org.lizardjudge.frontend.revision=$FRONTEND_COMMIT
HEALTHCHECK --start-period=90s --interval=5s --timeout=5s --retries=5 CMD [ "/usr/local/bin/python3", "/app/deploy/health_check.py" ]
EXPOSE 8000
ENTRYPOINT [ "/app/deploy/entrypoint.sh" ]
