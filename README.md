# LizardJudge — Online Judge | Universidad Privada del Valle

<div align="center">

![Estado](https://img.shields.io/badge/estado-entrega%20funcional-blue?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Vue](https://img.shields.io/badge/Frontend-Vue.js%202-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)

**Plataforma de juez en línea para evaluación automática de problemas de programación.**

Proyecto académico desarrollado para la materia de **Sistemas II** — Universidad Privada del Valle (UNIVALLE).

</div>

**Versión 2.2.3** — backend 2.2.3, frontend 2.2.2, PostgreSQL 17 y tutor con
modelo QLoRA opcional. Las herramientas de ensayo y defensa de la 2.1 están en
[`legado/v2.1/`](legado/v2.1/) y no se usan con esta versión.

---

## Descripción

LizardJudge es una plataforma web de tipo **Online Judge** que permite a estudiantes y docentes:

- **Crear y gestionar problemas** de programación con casos de prueba automáticos.
- **Enviar soluciones** en múltiples lenguajes de programación.
- **Evaluación automática** con retroalimentación instantánea (Accepted, Wrong Answer, Time Limit, etc.).
- **Rankings y concursos** con soporte para modalidades ACM/ICPC y OI.
- **Panel de administración** completo para gestión de usuarios, problemas y concursos.

---

## Arquitectura

Desde la 2.2 el frontend y el backend son imágenes separadas, compiladas desde
los submódulos `OnlineJudgeFE/` y `OnlineJudge/`:

```
 navegador ──► oj-frontend (nginx, puerto 80) ──► oj-backend (Django, 8000)
                                                    │      │       ▲
                                    oj-postgres ◄───┘      ▼       │ latidos
                                    oj-redis  ◄──────── cola ──► oj-judge
                         (opcional) oj-tutor ──► oj-model (llama.cpp)
```

| Servicio | Tecnología | Función |
|----------|-----------|---------|
| **oj-frontend** | Vue 2 + nginx sin privilegios | Sirve la interfaz y reenvía `/api` y `/public` |
| **oj-backend** | Python 3.12 / Django 5.2 | API REST, colas y tareas |
| **oj-migrate** | Misma imagen del backend | Aplica migraciones al arrancar y termina |
| **oj-judge** | Sandbox C/C++ | Ejecuta y evalúa las soluciones de forma aislada |
| **oj-postgres** | PostgreSQL 17 | Base de datos |
| **oj-redis** | Redis 7 | Caché y cola de tareas |
| **oj-tutor / oj-model** | Opcionales (`compose.tutor.yml`) | Explicaciones y «Proponer con IA» con el modelo aprobado |

---

## Instalación y ejecución

### Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (o Docker Engine con Compose v2) en marcha.
- Unos 6 GB de disco para imágenes; 2,5 GB de RAM extra si se activa el tutor con modelo.
- Internet la primera vez, para descargar dependencias e imágenes base.

### Pasos

1. **Clonar con los submódulos:**

   ```bash
   git clone --recurse-submodules https://github.com/BenjaminSM04/OnlineJudge_Deploy
   cd OnlineJudge_Deploy
   ```

   Si ya estaba clonado: `git pull && git submodule update --init --recursive`.

2. **Crear el archivo `.env`** a partir del ejemplo y completar los dos secretos:

   ```bash
   cp .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(32))"   # úselo para POSTGRES_PASSWORD
   python -c "import secrets; print(secrets.token_urlsafe(40))"   # úselo para JUDGE_SERVER_TOKEN
   ```

3. **Compilar y levantar:**

   ```bash
   docker compose up -d --build
   ```

   La primera compilación tarda varios minutos. Para incluir el tutor con modelo:

   ```bash
   docker compose -f docker-compose.yml -f compose.tutor.yml up -d --build
   ```

4. **Crear el administrador** (la contraseña se pide en la terminal):

   ```bash
   docker compose exec oj-backend python manage.py create_admin --username admin
   ```

5. **Entrar** en `http://localhost` (o el puerto de `OJ_HTTP_PORT`) y en
   `http://localhost/admin` para el panel.

Para comprobar que todo funciona sin tocar su instalación:
`bash scripts/verify_stack.sh` levanta un proyecto aparte en `http://127.0.0.1:18090`
y verifica interfaz, API y juez (luego bórrelo con
`docker compose -p lizardjudge-prueba --env-file .verification/ci.env down -v`).

### Dominio y HTTPS

Con un dominio propio, añádalo a `DJANGO_ALLOWED_HOSTS`. Si un proxy (Cloudflare,
Traefik, Caddy…) sirve HTTPS delante del puerto 80, ponga además
`DJANGO_CSRF_TRUSTED_ORIGINS=https://su-dominio`, `COOKIE_SECURE=1` y
`TRUST_PROXY_HTTPS=1`.

### Datos

Todo se guarda en volúmenes de Docker con nombre (base, Redis, casos de prueba,
archivos públicos y configuración). `docker compose down` los conserva;
**`docker compose down -v` los borra**. Las instalaciones de la 2.1 guardaban
datos en `./data` y en un volumen PG17 externo: para pasarlos a esta versión,
restaure el volcado de PostgreSQL y copie `data/backend/test_case` y
`data/backend/public` a los volúmenes nuevos antes de abrir el sitio
(ver [`legado/v2.1/`](legado/v2.1/)).

---

## Estructura del proyecto

```
OnlineJudge_Deploy/
├── docker-compose.yml      # Stack completo (compila desde los submódulos)
├── compose.tutor.yml       # Tutor con modelo (opcional)
├── .env.example            # Variables a copiar en .env
├── scripts/
│   ├── verify_stack.sh            # Prueba el stack en un proyecto aislado
│   └── check_submodule_checks.py  # Exige CI verde antes de mover los submódulos
├── backup/                 # Respaldo de base y archivos
├── docs/                   # Documentación del proyecto y de los sprints
├── legado/v2.1/            # Compose, scripts y guías de la versión 2.1
├── OnlineJudge/            # Backend (submódulo, Django)
└── OnlineJudgeFE/          # Frontend (submódulo, Vue 2)
```

---

## Comandos útiles

```bash
docker compose ps                         # estado de los servicios
docker compose logs --tail 100 oj-backend # registros del backend
git pull && git submodule update --init --recursive && docker compose up -d --build  # actualizar
docker compose stop                       # detener conservando los datos
```

---

## Equipo

| Rol | Nombre |
|-----|--------|
| Desarrolladores | Alvaro Benjamin Saenz Molina, Brisa Sindel Criales Mayta, Grisel Abigail Aranda Ojeda, Brenda Michelle Alanoca Challco |
| Materia | Proyecto de Sistemas II |
| Universidad | Universidad Privada del Valle (UNIVALLE) |

---

## Basado en

Este proyecto está basado en [QingdaoU/OnlineJudge](https://github.com/QingdaoU/OnlineJudge), una plataforma de juez en línea de código abierto, adaptada y personalizada para uso académico en UNIVALLE.

---

## Licencia

Este proyecto es de uso académico. El código base original está bajo la licencia [MIT](https://opensource.org/licenses/MIT).
