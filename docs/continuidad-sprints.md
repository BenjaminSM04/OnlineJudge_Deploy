# Estado vigente de la continuación

## Defensa y entrega funcional

La instrucción vigente autoriza merges y entrenamiento real con sintéticos; el
piloto se conserva como propuesta documental no ejecutada, fuera del cierre
funcional. PR #50/#123/#3 fusionados y main verificado; sincronizador activo con
gates. Ramas de continuación backend/deploy: `codex/defensa-entrega`.

Resultados: 301 pruebas Django; 144 variantes y 36 controles observados en el
juez; dataset 96/24/24; clasificador y QLoRA reales (tres épocas, 500,49 s), GGUF
Q4_K_M y tres pistas generadas en la aplicación con login y veredictos reales.
Ver `docs/defensa/README.md` y `docs/defensa/evidencias.json`. No se tocó el servidor.

## Registro anterior

El registro anterior se conserva debajo como historia. Trabajo actual en
`D:\Juez Virtual\OnlineJudge_Deploy_revision`; el checkout original permanece limpio.
Ramas: backend `codex/revision-y-compatibilidad`, frontend `codex/version-compilacion`,
deploy `codex/integracion-conservacion`. PR 50/123/3; backend #38 ya fue fusionado.
Sin acceso al alojamiento. Los apartados posteriores conservan el historial.

## Revisión de entrega del 24/10

Ver `entrega.md` y `evidencias/entrega-local.json`: 291 pruebas Django, 8 del motor,
14 flujos de interfaz y seis envíos reales al juez en un nuevo proyecto sintético.
Se corrigieron plazo acumulado HTTP (cabeceras/cuerpo/goteo), procedencia entrenable
de GGUF y planilla vinculada al contenido completo. Reexportados 54 borradores,
sin aprobar ninguno. El sincronizador antiguo de main está `disabled_manually`
hasta integrar el gate del PR #3. No se hizo merge ni despliegue adicional.

## Evidencia anterior

- Backend `d9cb562`: 242 pruebas sobre PG17 y CI/GitGuardian verdes. Incluye
  la regresión del limitador Redis y actualización acotada de Go.
- Frontend `1dd30ea`: 13 pruebas más regresiones de backports, DLL/build de ambas
  entradas, auditoría con excepciones acotadas, CI/GitGuardian verdes.
- `verify_upgrade.py` pasó en `lizardjudge-upgrade-20261023-c`: 21 tablas originales,
  PG10→17, secuencias/objetos, archivos restaurados en otro volumen, Redis restaurado,
  clave/sesión histórica y rollback anterior a escrituras. No se usó servidor.
- Chromium: 14 comprobaciones reales del panel, docente, preferencias/mascota,
  móvil 320/375/1280, oscuro/teclado/movimiento reducido, editor, uploads CSRF,
  descarga y previsualización CSV. Fuente: `scripts/verify_ui.py`.
- Protocolo de juez: AC reales en seis lenguajes con imagen por digest. Go necesitó
  compilación serial y presupuesto frío de 30/60 s. Configuración persistida no se
  reemplaza al arrancar: `update_go_compiler_budget` propone solo la entrada heredada
  exacta y requiere `--apply`; preserva personalizaciones.
- Carga de fallback: 24 respuestas, concurrencia 4, p50 103 ms/p95 169 ms local,
  cuatro rechazos de cuota comprobados; muestra RAM 281.5 MiB, pico no medido.
- Trivy de imagen combinada: 0 altas/críticas, 5 medias/1 baja. Yarn sigue mostrando
  avisos de herramientas heredadas; consultar inventario/backports/caducidad, no
  afirmar auditoría limpia. pip-audit y CI del backend no hallaron avisos conocidos.
- Revisión independiente: se reprodujeron/corrigieron guard inline, ruta GGUF,
  historia Git CI, nivel histórico y presupuesto de lectura. Regresiones en
  `scripts/test_tutor_engine.py` y suite Django.

Ensayo real navegador→cola→juez aprobado en seis lenguajes y un logro único.

CI de integración `c50e136` (gitlinks exactos d9cb562/1dd30ea), detalle en
`evidencias/ci-integracion.json`:

- Ejecución PR 40056198026 aprobada en el runner: 242 pruebas sobre PG17, migración
  histórica con 21 tablas/archivos/Redis/clave/sesión y rollback previo a escrituras,
  14 comprobaciones Chromium, seis lenguajes del juez, seis envíos reales AC,
  fallback p95 106 ms (sin modelo), Trivy HIGH/CRITICAL 0 y motor 503 sin artefactos.
- Ejecución push 40056195214: las mismas verificaciones pasaron, pero **GHCR rechazó
  el manifiesto** (`denied`) de `ghcr.io/benjaminsm04/lizardjudge`. El paquete ya
  existía, vacío y sin acceso de escritura para Actions de este repositorio.
  El rechazo no se repitió en las ejecuciones siguientes.
- Integración `cf7174e` (backend `767fbb9`, frontend `1dd30ea`): PR 40059325399 y
  push 40059321280 aprobados; **imágenes publicadas** en GHCR con etiquetas OCI de
  los tres SHA verificadas tras `pull`: `lizardjudge@sha256:0cc12d14…` y
  `lizardjudge-tutor@sha256:bccc2207…`. Publicar no es desplegar: el servidor no
  se tocó.

Continuación 24/10 (backend PR #50 sobre `main`, deploy en esta misma rama):

- Kit de revisión: `export_tutor_review_sheet`/`apply_tutor_review_sheet` con
  revisor único distinto del autor, notas obligatorias y todo o nada; guía
  `OnlineJudge/docs/ai-tutor/kit-revision.md`. Planilla de los 54 borradores generada
  localmente en `respaldos/` para el equipo. Ninguna decisión fue aplicada.
- Configuración de despliegue: booleanos `true/false` además de `1/0`, con fallo
  cerrado ante valores desconocidos (antes `COOKIE_SECURE=true` dejaba la cookie sin
  `Secure`), alias `DJANGO_ALLOWED_HOSTS`/`DJANGO_CSRF_TRUSTED_ORIGINS` y `/healthz`.
- **Defecto del motor corregido**: `urlopen(timeout=0.5)` en el motor y
  `timeout=(1, 0.5)` en el backend esperaban una respuesta que llama.cpp sin
  streaming solo envía al terminar; toda generación de más de 0,5 s caía al respaldo
  y abría el circuito. Ahora `MODEL_TIMEOUT_S` (8 s) y `AI_TUTOR_ENGINE_TIMEOUT`
  (10 s), validados entre 1 y 30 s, con regresiones de generación lenta y goteo.
- Medición real de dos candidatos (`evidencias/medicion-modelos.json`), sobre
  borradores no aprobados: con los límites de producción (2 CPU, 3 GB) y la
  petición exacta del motor, Qwen2.5-Coder-1.5B Q4_K_M usa 1,1 GB con p50 6,7 s y
  p95 10,5 s, y 39/54 respuestas llegan en 8 s aceptadas por el guard; Qwen3-1.7B
  Q8_0 llega al límite de 3 GB con p50 39 s y no es viable. Con el plazo anterior
  ninguna respuesta llegaba. Aceptado por el guard no equivale a adecuado: varias
  respuestas proponen la corrección directa; falta revisión humana con la rúbrica.
- Entorno QLoRA comprobado en RTX 2060 SUPER 8 GB (`evidencias/entorno-entrenamiento.json`):
  CUDA 12.6, capa NF4 y gradientes LoRA correctos. El entrenador usaba bf16 emulado
  en Turing; ahora usa fp16 con capacidad < 8.0. No se entrenó: no hay dataset aprobado.
- Ensayo real desde la procedencia privada instalada hacia la nueva (detalle solo
  local): 17 tablas con recuentos/hash idénticos, `django_migrations` 77→90 sin
  pérdidas, sin pendientes, migraciones JSON sin SQL y rollback previo a escrituras.
  La restauración de archivos ahora conserva el propietario numérico original.

Restante: revisión humana (planilla), selección, entrenamiento y piloto según
`cierre-con-el-equipo.md`; reconciliar la instalación real antes de desplegar
(sección siguiente). El Action programado de `main` del deploy sincroniza sin
controles: tras la fusión del backend, su próxima ejecución combinaría Django 5.2
con el compose PG10 de `main` hasta integrar este PR #3.

## Hacia la instalación real (Coolify) sin perder datos

El backend #38 se fusionó en `main` (`e8e2f7b`, mismo árbol que `d9cb562`); su
rama se eliminó. El servidor sigue usando los repositorios privados de entrega y
no depende de estos repos públicos. Análisis local de solo lectura (no publicado,
porque contiene detalles privados) del historial de migraciones privado frente al
nuevo:

- El grafo es compatible: Django ignora filas aplicadas que no conoce, hay una sola
  hoja por app y no aparece `InconsistentMigrationHistory`. Cinco migraciones de
  campos JSON tienen nombres distintos y operaciones idénticas: sobre columnas ya
  `jsonb` no emiten SQL efectivo. `ai_tutor` y `practice` solo crean tablas nuevas.
  No renombrar ni copiar migraciones ni editar `django_migrations` a mano.
- Riesgos reales, fuera del grafo: Django 5.2 exige PostgreSQL ≥ 14 (confirmar la
  versión instalada y, si es menor, usar la transición PG17 de este repositorio);
  nombres de variables y booleanos de entorno, healthcheck y argumentos del
  entrypoint esperados por la configuración privada; correcciones funcionales que
  existen solo en la rama privada (p. ej. dificultad en importación/exportación
  QDUOJ) y deben integrarse por su propio PR en el repositorio que corresponda.
- Antes de cualquier ventana: copia real restaurada en un entorno aislado,
  `showmigrations`, `migrate --plan`, `sqlmigrate` de las migraciones JSON,
  `migrate` dos veces, recuentos por tabla y rollback a la imagen anterior antes
  de abrir escrituras. El operador decide la procedencia que despliega.

Decisión: se conserva este registro y las ramas ya autorizadas como plan de trabajo,
sin recrear worktrees ni pedir otra autorización para publicar las mismas ramas.
Las correcciones privadas fueron identificadas y permanecen separadas; no se
copian a repositorios públicos ni se opera Coolify.

---


## Registro anterior (histórico)

# Continuidad de implementación

## Objetivo vigente

Completar todo lo técnicamente ejecutable de las 30 historias y los requisitos
adicionales del documento del usuario, conservando Vue 2 y los datos. No operar
el servidor. Commits y documentación en español, sin coautorías. No cerrar
aprobaciones humanas, entrenamiento o piloto sin evidencia real.

## Estado de trabajo

- Worktree: `D:/Juez Virtual/OnlineJudge_Deploy_revision`.
- Ramas publicadas previas: deploy `codex/integracion-conservacion` (PR 3),
  backend `codex/conservacion-arranque` (PR 38), frontend
  `codex/version-compilacion` (PR 123). Continuar sobre ellas y reescribir sus
  descripciones alrededor del alcance final; todavía no integrar a main.
- El checkout original permanece intacto. Mantener el Action de sincronización,
  pero añadir sus gates de compatibilidad y pruebas antes de promover gitlinks.
- `docs/tablero-inicial.json` conserva los 30 responsables, pesos y estados
  consultados. PB-06 a PB-09 figuran Done, aunque no estaban completos en main;
  no se alteraron estados a ciegas.

## Implementado en esta continuación, todavía sin publicar

- Django 5.2.18/Python 3.12, DRF actualizado, URLs compatibles, Sentry SDK,
  eliminación de la extensión antigua de reconexión, saneamiento nh3 al escribir
  y leer HTML histórico. Migraciones aditivas para tutor y mascota.
- Explicaciones conservadoras, contexto por lista positiva, feedback idempotente,
  tres niveles de pista validados, conceptos versionados, valoración y métricas.
- Motor con timeout/circuito y respaldo determinista/estático. Guard de texto.
- Logros históricos persistentes sin FK al problema, preferencias privadas,
  reconciliación antes del arranque y overview de práctica.
- Dataset versionado, particiones por problema, checksums, revisión explícita,
  clasificador NB, evaluación por categoría/lenguaje y entrenamiento LoRA/QLoRA
  condicionado a selección documentada y datos aprobados.
- Panel Vue 2, edición pedagógica, mascota SVG, inicio personal y tema oscuro.
- CSRF real en uploads, firmas de imágenes/adjuntos, guard de ZIP, unidades FPS,
  cabeceras de descarga y aislamiento por contexto de los decoradores de permiso.
- `tutor_engine/` y `compose.tutor.yml`: servicio interno sin puerto público,
  checksums y readiness cerrada sin artefactos aprobados.

## Verificación actual

- 233 pruebas Django completas aprobadas con `oj.test_settings` sobre PostgreSQL
  17 en `compose.sprints.yml`, proyecto `lizardjudge-sprints-20261023`.
- La imagen de frontend compiló con las ocho pruebas existentes después de
  incorporar tutor, mascota y edición pedagógica. Se modificó CSRF después: debe
  repetirse build y ampliar pruebas de componentes/navegación.
- 54 variantes ejecutadas en contenedores aislados, seis lenguajes, tres problemas
  y tres mutaciones. Borradores y observaciones en
  `OnlineJudge/docs/ai-tutor/variantes/`. Cero aprobaciones humanas.
- Entorno privado de pruebas: `respaldos/runtime/environment.json` (credenciales
  sintéticas nuevas), `tests.log`, imágenes `lizardjudge-sprints:local` y
  `lizardjudge-sprints-frontend:local`. No publicar respaldos ni este entorno.
- Imagen del motor construida; el contenedor temporal
  `lizardjudge-tutor-readiness-check` está en red none, sin modelos. Verificar
  respuesta 503 y retirarlo tras el ensayo.

## Siguiente trabajo necesario

1. Completar notebook y documentación de benchmark/revisión/piloto sin inventar
   ejecuciones de entrenamiento ni métricas de modelos ausentes.
2. Ensayar actualización real: exportar backend histórico `72fc563` para construir
   una imagen de origen Django 3.2; sembrar datos en PostgreSQL 10, respaldar,
   restaurar a 17 en volumen nuevo y aplicar migraciones modernas. Comparar datos
   originales, archivos, clave y sesión, y probar reversión antes de escrituras.
   El antiguo `scripts/verify_deploy.py` no sirve todavía para el backend moderno:
   espera Django 3.2 sobre PostgreSQL 10. Sustituir el gate de CI por este ensayo
   coordinado y conservar las herramientas de respaldo compatibles.
3. Añadir pruebas HTTP/UI reales de tutor y mascota, móvil/teclado/tema, eventos y
   errores de red; repetir full Django/build/lint/checks de migraciones.
4. Completar observabilidad de fallos, concurrencia de feedback/logros y revisión
   de guard/contexto. Validar el motor real en modo no disponible, sin simular una
   inferencia generativa ejecutada.
5. Revisar juez real de seis lenguajes, protocolos y presupuestos. La imagen local
   `lizardjudge-judge:verification` tiene GCC13, Java21, Python3.12, Go1.27 y Node24;
   el Compose publicado usa el juez upstream 1.6.1. No atribuir al segundo las
   capacidades verificadas solo en la imagen local.
6. Auditoría actual de dependencias e imágenes, CI en los tres repositorios,
   gates de sincronización; publicar commits comprobados, esperar CI/GitGuardian.
7. Matriz final por historia y evidencias. Mantener pendientes reales PB-04/PB-07
   revisión humana, exportación histórica autorizada, selección/ajuste/evaluación
   real del modelo, hardware objetivo y piloto consentido PB-29.
