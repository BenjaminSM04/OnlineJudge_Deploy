# 🏛️ LizardJudge — Online Judge | Universidad Privada del Valle

<div align="center">

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Vue](https://img.shields.io/badge/Frontend-Vue.js%202-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)

**Plataforma de juez en línea para evaluación automática de problemas de programación.**

Proyecto académico desarrollado para la materia de **Sistemas II** — Universidad Privada del Valle (UNIVALLE).

</div>

---

## 📋 Descripción

LizardJudge es una plataforma web de tipo **Online Judge** que permite a estudiantes y docentes:

- 📝 **Crear y gestionar problemas** de programación con casos de prueba automáticos.
- ⚡ **Enviar soluciones** en múltiples lenguajes de programación.
- ✅ **Evaluación automática** con retroalimentación instantánea (Accepted, Wrong Answer, Time Limit, etc.).
- 🏆 **Rankings y concursos** con soporte para modalidades ACM/ICPC y OI.
- 👥 **Panel de administración** completo para gestión de usuarios, problemas y concursos.

---

## 🏗️ Arquitectura

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
| **oj-postgres** | PostgreSQL 10 | Base de datos relacional |
| **oj-redis** | Redis 4 | Caché y cola de tareas |

---

## 🚀 Instalación y Ejecución

### Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo.
- Al menos **2 GB de RAM** disponible para Docker.
- Conexión a internet (solo la primera vez, para descargar imágenes base).

### Pasos

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/BenjaminSM04/OnlineJudge_Deploy
   cd OnlineJudge_Deploy
   ```

2. **Construir y levantar los servicios:**

   ```bash
   docker-compose up -d --build
   ```

   > ⏱️ La primera vez tardará entre **5 a 15 minutos** mientras se descargan las dependencias y se compila el frontend.

3. **Verificar que todos los contenedores estén saludables:**

   ```bash
   docker ps -a
   ```

   Deberías ver los 4 contenedores con estado `Up` y el backend con `(healthy)`.

4. **Acceder a la plataforma:**

   | URL | Descripción |
   |-----|-------------|
   | `http://localhost` | Página principal del juez |
   | `http://localhost/admin` | Panel de administración |

   **Credenciales por defecto del administrador:**
   - **Usuario:** `root`
   - **Contraseña:** `rootroot`

   > ⚠️ **Cambiar la contraseña del administrador después del primer inicio de sesión.**

---

## 📁 Estructura del Proyecto

```
OnlineJudgeDeploy/
├── Dockerfile              # Build multi-stage (Frontend + Backend)
├── docker-compose.yml      # Orquestación de servicios
├── .dockerignore            # Excluye node_modules, .git, etc.
├── .gitignore
├── README.md
│
├── OnlineJudge/            # 🔧 Backend (Python/Django)
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
├── OnlineJudgeFE/          # 🎨 Frontend (Vue.js 2)
│   ├── src/                # Código fuente
│   ├── build/              # Scripts de Webpack
│   ├── config/             # Configuración de entornos
│   └── package.json
│
└── data/                   # 📦 Datos persistentes (generado por Docker, no se sube)
    ├── backend/
    ├── postgres/
    └── redis/
```

---

## 🛠️ Comandos útiles

```bash
# Levantar servicios
docker-compose up -d --build

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs solo del backend
docker-compose logs -f oj-backend

# Detener todos los servicios
docker-compose down

# Detener y ELIMINAR todos los datos (base de datos, etc.)
docker-compose down -v

# Reconstruir solo si hay cambios en el código
docker-compose up -d --build oj-backend
```

---

## 👥 Equipo

| Rol | Nombre |
|-----|--------|
| Desarrolladores | Alvaro Benjamin Saenz Molina, Brisa Sindel Criales Mayta, Grisel Abigail Aranda Ojeda, Brenda Michelle Alanoca Challco |
| Materia | Proyecto de Sistemas II |
| Universidad | Universidad Privada del Valle (UNIVALLE) |

---

## 📚 Basado en

Este proyecto está basado en [QingdaoU/OnlineJudge](https://github.com/QingdaoU/OnlineJudge), una plataforma de juez en línea de código abierto, adaptada y personalizada para uso académico en UNIVALLE.

---

## 📄 Licencia

Este proyecto es de uso académico. El código base original está bajo la licencia [MIT](https://opensource.org/licenses/MIT).
