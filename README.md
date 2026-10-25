# LizardJudge — Online Judge | Universidad Privada del Valle

<div align="center">

![Estado](https://img.shields.io/badge/estado-entrega%20funcional-blue?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Vue](https://img.shields.io/badge/Frontend-Vue.js%202-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)

**Plataforma de juez en línea para evaluación automática de problemas de programación.**

Proyecto académico desarrollado para la materia de **Sistemas II** — Universidad Privada del Valle (UNIVALLE).

</div>

La [guía de defensa y entrega](docs/defensa/README.md) reúne la demostración local,
el guion, las preguntas y los resultados reales del experimento QLoRA sintético.
El piloto se conserva como propuesta documental, sin resultados de campo inventados.

```sh
python scripts/defense_demo.py init --project lizardjudge-defensa-mi-entrega --build
```

Este perfil crea sus propios datos ficticios y publica solo loopback. Para usar el
modelo ajustado, montar su directorio con `--model-directory`; ver la guía.

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

El sistema está compuesto por **4 servicios Docker** que trabajan en conjunto:

```
┌─────────────────────────────────────────────────┐
│                  Docker Compose                 │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Redis   │  │ Postgres │  │ Judge Server │  │
│  │ (Cache)  │  │  (Base   │  │ (Evaluador   │  │
│  │          │  │  de Datos)│  │  de código)  │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │               │          │
│       └──────┬───────┘───────────────┘          │
│              │                                  │
│     ┌────────▼─────────┐                        │
│     │   OJ Backend     │                        │
│     │  (Django + Nginx  │                        │
│     │  + Frontend Vue) │                        │
│     │                  │                        │
│     │  Puerto 80 (HTTP)│                        │
│     │  Puerto 443(HTTPS│)                       │
│     └──────────────────┘                        │
└─────────────────────────────────────────────────┘
```

| Servicio | Tecnología | Función |
|----------|-----------|---------|
| **oj-backend** | Python 3.12 / Django / Nginx | API REST + serve del frontend compilado |
| **oj-judge** | C/C++ Sandbox | Ejecuta y evalúa las soluciones de forma segura |
| **oj-postgres** | PostgreSQL 17 | Base de datos relacional; volumen restaurado explícito |
| **oj-redis** | Redis 7 | Caché y cola de tareas |

---

## Instalación y Ejecución

Para actualizar una instalación existente, lea primero
[Actualización y recuperación](docs/actualizacion-django52-pg17.md).
No ejecutar la instalación rápida sobre una base PostgreSQL 10 existente.
La [guía de entrega](docs/entrega.md) reúne evidencias y aprobaciones pendientes.
El tutor generativo permanece apagado hasta la evaluación del modelo.

### Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo.
- Espacio para dos bases independientes, imágenes y respaldos durante el ensayo.
- El perfil opcional de modelos reserva hasta 3 GB adicionales para llama.cpp.
- Conexión a internet (solo la primera vez, para descargar imágenes base).

### Pasos

1. **Clonar el repositorio:**

   ```bash
   git clone --recurse-submodules https://github.com/BenjaminSM04/OnlineJudge_Deploy
   cd OnlineJudge_Deploy
   ```

2. **Verificar primero en un entorno sintético aislado:**

   ```bash
   python scripts/verify_upgrade.py --project lizardjudge-upgrade-demostracion-01 --keep-running
   ```

   El nombre debe ser nuevo. El comando construye ambas versiones, ensaya la
   recuperación y ejecuta la suite. Genera credenciales efímeras en memoria y
   escucha solo en `http://127.0.0.1:18082`. No utiliza datos del servidor.
   No recree sus contenedores con otro entorno; para repetir elija otro nombre.

3. **Verificar que todos los contenedores estén saludables:**

   ```bash
   docker ps -a
   ```

   El backend y los servicios de este proyecto deben estar saludables. El ensayo
   mantiene separados origen, destino y Redis restaurado; conserva sus volúmenes.

4. **Acceder a la plataforma:**

   | URL | Descripción |
   |-----|-------------|
   | `http://127.0.0.1:18082` | Página principal del ensayo |
   | `http://127.0.0.1:18082/admin` | Panel de administración del ensayo |

   En una instalación nueva, cree el administrador explícitamente:

   ```bash
   docker compose -p lizardjudge-upgrade-demostracion-01 -f compose.upgrade-verify.yml exec oj-backend python manage.py inituser --username administrador --action create_super_admin
   ```

   La contraseña se solicita en la terminal. Una actualización conserva los usuarios existentes.

   El ensayo no inicia el juez: `verify_submission_e2e.py` lo prepara y comprueba
   mediante seis envíos reales; consulte la guía de entrega.

Para una instalación nueva independiente, prepare un `.env` privado desde
`.env.example`, cree explícitamente un volumen PG17 nuevo y asígnelo a
`OJ_PG17_VOLUME`. Para actualizar, este volumen debe contener la restauración
verificada; crear uno vacío no migra nada. En HTTP local `COOKIE_SECURE=0`;
en HTTPS real `COOKIE_SECURE=1`, con hosts y orígenes explícitos.

---

## Estructura del Proyecto

```
OnlineJudgeDeploy/
├── Dockerfile              # Build multi-stage (Frontend + Backend)
├── docker-compose.yml      # Orquestación de servicios
├── .dockerignore            # Excluye node_modules, .git, etc.
├── .gitignore
├── README.md
│
├── OnlineJudge/            # Backend (Python/Django)
│   ├── account/            # Módulo de autenticación
│   ├── announcement/       # Módulo de anuncios
│   ├── contest/            # Módulo de concursos
│   ├── problem/            # Módulo de problemas
│   ├── submission/         # Módulo de envíos
│   ├── judge/              # Integración con el judge server
│   ├── deploy/             # Configuración de despliegue (Nginx, Supervisor)
│   ├── oj/                 # Configuración principal de Django
│   └── manage.py
│
├── OnlineJudgeFE/          # Frontend (Vue.js 2)
│   ├── src/                # Código fuente
│   ├── build/              # Scripts de Webpack
│   ├── config/             # Configuración de entornos
│   └── package.json
│
└── data/                   # Datos persistentes (generado por Docker, no se sube)
    ├── backend/
    ├── postgres/
    └── redis/
```

---

## Comandos útiles

```bash
# Revisar y detener solo el ensayo, conservando sus volúmenes
docker compose -p lizardjudge-upgrade-demostracion-01 -f compose.upgrade-verify.yml ps
docker compose -p lizardjudge-upgrade-demostracion-01 -f compose.upgrade-verify.yml logs --tail 50 oj-backend
docker compose -p lizardjudge-upgrade-demostracion-01 -f compose.upgrade-verify.yml stop
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
