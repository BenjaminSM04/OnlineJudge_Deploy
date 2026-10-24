# Estado vigente de la continuación

El registro anterior se conserva debajo como historia. Trabajo actual en
`D:\Juez Virtual\OnlineJudge_Deploy_revision`; el checkout original permanece limpio.
Ramas: backend `codex/conservacion-arranque`, frontend `codex/version-compilacion`,
deploy `codex/integracion-conservacion`. PR 38/123/3; no merge ni alojamiento.

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
Restante inmediato: publicar integración con gitlinks exactos, esperar CI/GHCR, actualizar evidencia
de las 30 historias sin marcar aprobaciones inexistentes. Matriz en
`estado-sprints.md`; pendientes humanos/modelo/hardware/piloto permanecen explícitos.

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
