# Distribución de interfaces a automatizar — LizardJudge Univalle

Sistema bajo prueba: https://lj.isilp.com (portal de estudiantes) y https://lj.isilp.com/admin/ (panel de docentes/administración).
Stack: pytest + selenium + allure. Cada estudiante entrega **su propio** Word y **su propio** Test Suite (`tests/test_<tema>.py`) con todos los test cases que cubran sus interfaces.

El Word de cada estudiante debe tener: nombre, capturas de **sus** interfaces y descripción de las funcionalidades de cada una.

> Importante: es el sistema en producción. Usar solo cuentas de prueba, no registrar usuarios falsos en masa y no enviar soluciones repetidas. Las pantallas marcadas con 🔒 piden sesión; el panel admin pide credenciales de docente/administrador (pedirlas al docente).

## Resumen del reparto (6 interfaces por persona)

| # | Tema | Interfaces |
|---|---|---|
| Estudiante 1 | Acceso y cuenta | Login, Registro, Recuperar contraseña, Perfil 🔒, Ajustes 🔒, Admin: login |
| Estudiante 2 | Problemas y envíos | Lista de problemas, Detalle de problema, Estado de envíos, Detalle de envío, Admin: lista de problemas, Admin: crear/editar problema |
| Estudiante 3 | Concursos y rankings | Portada, Lista de concursos 🔒, Detalle de concurso 🔒, Ranking ACM, Ranking OI, Admin: concursos |
| Estudiante 4 | Informativo, global y administración | Acerca de, FAQ, Notas del parche, Página 404, Elementos globales (navbar, tema, idioma, footer), Admin: anuncios, usuarios, configuración, servidores de juicio, operaciones masivas y depuración de casos |

---

## Estudiante 1 — Acceso y cuenta

| Interfaz | URL | Qué contiene |
|---|---|---|
| Login | modal en `/` (botón «Iniciar Sesión») | Usuario, contraseña, enlace a registro y «Olvidé mi Contraseña». |
| Registro | modal en `/` (botón «Registrarse») | Formulario de alta; enlace de vuelta a login. |
| Recuperar contraseña | `/apply-reset-password` | Campo de correo, botón «Enviar correo de restablecimiento», «Volver a iniciar sesión». |
| Perfil 🔒 | `/user-home` | Perfil del usuario y su actividad. |
| Ajustes 🔒 | `/setting` (profile, account, security) | Edición de perfil, cuenta y seguridad (contraseña). |
| Admin: login | `/admin/login` | Usuario, contraseña, «Acceder al panel», «Volver al portal de estudiantes». |

Casos sugeridos: login válido/inválido/campos vacíos, validaciones del registro, usuario duplicado, recuperación con correo válido/inválido, redirección de rutas protegidas sin sesión, cierre de sesión, login de admin válido/inválido.

## Estudiante 2 — Problemas y envíos

| Interfaz | URL | Qué contiene |
|---|---|---|
| Lista de problemas | `/problem` | Tabla (ID, título, autor, nivel, total de envíos, tasa de AC), filtros por dificultad y etiquetas, botón «Reiniciar», paginación. |
| Detalle de problema | `/problem/BAS-SUMA-001` | Descripción, entrada/salida, ejemplos, editor de código con selector de lenguaje y tema, botón «Enviar», «Iniciar entrenamiento» 🔒, panel de información y estadísticas. |
| Estado de envíos | `/status` | Tabla de envíos (fecha, ID, estado, problema, tiempo, memoria, lenguaje, autor), filtros y «Actualizar». |
| Detalle de envío | `/status/:id` | Resultado del juez, código enviado y salida por caso. |
| Admin: problemas | `/admin/problems` | Listado y administración de problemas. |
| Admin: crear/editar problema | `/admin/problem/create`, `/admin/problem/edit/:id` | Formulario del problema, casos de prueba, lenguajes y límites. |

Casos sugeridos: filtros y reinicio, orden y paginación, apertura de detalle, cambio de lenguaje/tema del editor, enviar sin sesión, filtros del estado, campos obligatorios del formulario admin.

## Estudiante 3 — Concursos y rankings

| Interfaz | URL | Qué contiene |
|---|---|---|
| Portada | `/` | Banner, accesos «Explorar problemas» y «Conocer el juez», concurso destacado, anuncios. |
| Lista de concursos 🔒 | `/contest` | Concursos con estado, fecha, duración y tipo (hoy redirige a la portada con el login si no hay sesión). |
| Detalle de concurso 🔒 | `/contest/3` | Información, problemas, envíos, ranking y anuncios del concurso. |
| Ranking ACM | `/acm-rank` | Podio y tabla (usuario, AC, total, calificación). |
| Ranking OI | `/oi-rank` | Tabla por puntaje; hoy muestra «Sin Datos». |
| Admin: concursos | `/admin/contest`, `/contest/create`, `/contest/:id/edit`, `/contest/:id/problems`, `/contest/:id/announcement` | Alta y edición de concursos, sus problemas y anuncios. |

Casos sugeridos: elementos de la portada y sus enlaces, acceso a concursos sin sesión, estructura de las tablas de ranking, orden por AC, paginación, formulario de crear concurso y sus validaciones.

## Estudiante 4 — Informativo, elementos globales y administración

| Interfaz | URL | Qué contiene |
|---|---|---|
| Acerca de | `/about` | Compiladores y comandos (C, C++, Java, Python, Go, JavaScript) y explicación de resultados. |
| FAQ | `/faq` | Preguntas frecuentes del juez. |
| Notas del parche | `/changelog` | Historial de versiones (hoy v2.2.1). |
| Página 404 | cualquier ruta inexistente | Pantalla de error. |
| Elementos globales | todas las páginas | Navbar (Inicio, Problemas, Concursos, Ranking, Acerca de), modo oscuro, selector de idioma, botones de sesión, footer. |
| Administración | `/admin/announcement`, `/user`, `/conf`, `/judge-server`, `/problem/batch_ops`, `/prune-test-case` | Anuncios, usuarios, configuración, servidores de juicio, operaciones masivas y depuración de casos de prueba. |

Casos sugeridos: contenido y enlaces de cada página informativa, navegación del navbar, persistencia del modo oscuro y del idioma, 404, acceso a rutas admin sin credenciales, listados del panel.

---

## Nota para el encargado de grupo

- Las interfaces públicas fueron verificadas navegando el sitio. Las pantallas 🔒 y las del panel admin salen de las rutas del código publicado; su contenido exacto se confirma con una cuenta de prueba y credenciales de docente.
- Si no hay credenciales de admin para todos, el panel se puede reasignar para que nadie quede con menos carga.
