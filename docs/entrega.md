# Entrega técnica de LizardJudge — 24/10/2026

## Entrega vigente para defensa

El cierre funcional solicitado incluye ahora entrenamiento QLoRA real y una
demostración experimental integrada, sobre datos exclusivamente sintéticos.
Se fusionaron backend #50, frontend #123 y deploy #3; el sincronizador ya usa
gates y está activo. La continuación se entrega por sus nuevos PR de defensa.
Ver [guía vigente](defensa/README.md), [guion](defensa/guion.md) y
[resultados verificables](defensa/evidencias.json): 301 pruebas Django,
144 variantes/36 controles y tres pistas del modelo en el navegador.

El piloto es una propuesta no ejecutada y queda fuera del cierre funcional por
decisión del responsable. El modo normal conserva aprobaciones y modelo apagado
por defecto; el perfil técnico admite el artefacto experimental explícito. La
instalación real sigue a cargo del operador.

## Registro de la revisión anterior

La versión candidata permite practicar, juzgar envíos y usar el tutor de respaldo,
con mascota personal y tema adaptable. Conserva Vue 2 y añade la transición
coordinada Django 5.2/Python 3.12/PostgreSQL 17. Las ramas están preparadas para
revisión; esto no certifica instalación en producción ni cierre de los diez
sprints académicos. El tutor generativo permanece deshabilitado.

## Contenido entregado

| Componente | Comportamiento comprobable |
| --- | --- |
| Juez | Envíos desde navegador por API, Dramatiq y juez; C, C++, Java, Python3, Golang y JavaScript. |
| Tutor | Sesiones propias ligadas a versión pedagógica, explicación del último intento, tres pistas progresivas, conceptos y valoración. Excluye concursos y entregas ajenas. |
| Respaldo | Explicadores conservadores y pistas/conceptos docentes; cuotas, idempotencia, circuito y plazos acotados. No exige descargar modelos. |
| Configuración docente | Borradores y activación inmutable; las sesiones anteriores conservan su versión. |
| Práctica | Logro único por problema normal aceptado completo, evolución de mascota, aspectos desbloqueados y preferencias privadas. |
| Interfaz | Vue 2, claro/oscuro, móvil, teclado y movimiento reducido. |
| Datos | Respaldo y restauración en volúmenes separados, comprobación de filas/columnas, secuencias y objetos; conservación de clave, archivos y sesión Redis. |
| Investigación | Variantes sintéticas, revisión CSV, particiones sin contaminación, clasificador/evaluación y entrenador condicionado a aprobaciones. Estas herramientas no representan resultados académicos ya obtenidos. |

## Evidencia de esta revisión

Se repitió el ensayo `lizardjudge-upgrade-entrega-20261024-a` con datos sintéticos.
La suite actualizada corrió en su PostgreSQL 17 después de reproducir los defectos.
Los resultados sanitizados están en [evidencias/entrega-local.json](evidencias/entrega-local.json).

- 291 pruebas Django aprobadas; esquema sin cambios pendientes.
- 8 pruebas del motor, incluidos cuerpo tardío y goteo en cabeceras/cuerpo.
- 14 comprobaciones Chromium/API, sin errores JavaScript, a 320/375/1280 píxeles.
  Los veredictos de este ensayo de interfaz son sintéticos y no prueban el juez.
- Ensayo distinto: seis envíos reales navegador → API → cola → juez, todos AC,
  sin sembrar veredictos y con un solo logro para el problema repetido.
- Protocolo directo del juez también aprobado en seis lenguajes.
- Actualización histórica: 21 tablas originales conservadas, archivos y Redis
  restaurados en volúmenes nuevos, misma clave/sesión y reversión antes de escrituras.
- Carga del respaldo: 24 respuestas, concurrencia 4, p95 77,44 ms, cuatro rechazos
  de cuota comprobados. No mide inferencia ni rendimiento del servidor real.
- Motor real sin artefactos: health y feedback 503, raíz de solo lectura, sin red
  externa ni privilegios. No se presentó un modelo no aprobado como integrado.

La CI vuelve a construir y comprobar la pareja exacta de gitlinks de cada commit;
consulte los checks de [deploy #3](https://github.com/BenjaminSM04/OnlineJudge_Deploy/pull/3),
[backend #50](https://github.com/BenjaminSM04/PS2B2026-JuezVirtual_Backend/pull/50) y
[frontend #123](https://github.com/BenjaminSM04/PS2B2026-JuezVirtual_frontend/pull/123).
Los informes antiguos conservan sus SHA y no acreditan automáticamente una revisión nueva.
GHCR publica por SHA después de los checks; publicar una imagen no despliega el servicio.

## Defectos corregidos al revisar la continuación

1. El timeout se renovaba después de cabeceras tardías. El transporte HTTP ahora
   aplica el tiempo restante en cada operación de socket, incluso al leer cabeceras.
   La reproducción de 1,4 s con presupuesto de 1 s falla antes del cambio y pasa
   después. Motor y backend comparten la implementación y no hacen reintentos.
2. El entrenador intentaba cargar safetensors desde el repositorio GGUF medido.
   Una selección GGUF exige `training_model` separado, fijado y coincidente con la
   procedencia del benchmark revisado; no se adivina una identidad ni una revisión.
3. La planilla omitía incertidumbre y procedencia. Ahora muestra ambos campos y
   vincula el contenido completo mediante SHA-256. Un cambio posterior invalida
   la decisión. Se reexportó la planilla local de 54 borradores, sin decisiones.

El sincronizador antiguo de `main` se pausó temporalmente para evitar que combine
el backend ya fusionado con PostgreSQL 10. Mantenerlo deshabilitado hasta integrar
el gate del deploy y verificar la pareja de submódulos. No se modificó el servidor.

## Demostración local reproducible

Usar un checkout con los gitlinks de esta rama, Docker Linux, Python y Playwright.
Elegir un nombre nuevo; el puerto loopback 18082 debe estar libre. No combinar
estos archivos con la configuración real ni reusar un proyecto con datos.

```sh
python scripts/verify_upgrade.py --project lizardjudge-upgrade-demo-nuevo --keep-running
python scripts/verify_ui.py --project lizardjudge-upgrade-demo-nuevo
python scripts/verify_judge.py
python scripts/verify_submission_e2e.py --project lizardjudge-upgrade-demo-nuevo
python scripts/load_test_ai_tutor.py --project lizardjudge-upgrade-demo-nuevo
python scripts/test_tutor_engine.py
python scripts/verify_engine_unavailable.py
```

Playwright: instalar la versión fijada en `.github/workflows/verify-deploy.yml` y
su Chromium. El primer comando ejecuta también la suite. Los siguientes crean
fixtures adicionales en el ensayo, nunca participantes de un piloto.

Para acceder manualmente a `http://127.0.0.1:18082/admin`, crear un administrador
en ese proyecto con `manage.py inituser --action create_super_admin --username
demostracion`, mediante `docker compose ... exec oj-backend`. La terminal solicita
contraseña; no hay una cuenta automática conocida. Los secretos del ensayo solo
viven en memoria durante su creación: no recrear contenedores con otro entorno.
Detenerlo con `docker compose -p NOMBRE -f compose.upgrade-verify.yml stop` conserva
volúmenes y evidencia. No usar limpieza general de Docker.

La [guía pedagógica](../OnlineJudge/docs/ai-tutor/guia-pedagogica.md) explica el flujo
del docente y estudiante, niveles, incertidumbre, valoración y mascota. La
[operación del tutor](../OnlineJudge/docs/ai-tutor/operacion.md) explica métricas,
retención, flags, recursos y revisión de artefactos.

## Integración e instalación

El backend #38 está fusionado; #50 contiene la compatibilidad y estas correcciones.
Frontend #123 y deploy #3 continúan separados. Revisarlos como una entrega
coordinada; el gitlink del deploy debe corresponder al árbol realmente evaluado,
y la sincronización posterior debe superar sus gates. No promover ciegamente
el backend moderno al compose histórico. No se hizo merge automático.

Antes del servidor: identificar su procedencia, restaurar una copia autorizada
aislada, comprobar migraciones y funciones propias de los repositorios privados,
y seguir [actualización y recuperación](actualizacion-django52-pg17.md). Los
detalles privados permanecen fuera de Git. El operador conserva claves, archivos,
Redis y PostgreSQL de origen. El rollback solo está demostrado antes de abrir
escrituras; después requiere conciliación que preserve la actividad nueva.

## Pendientes que impiden declarar los diez sprints cerrados

- Revisión real de los 54 borradores, acuerdo entre dos revisores y dataset aprobado.
- Autorización institucional antes de exportar entregas históricas.
- Selección humana sobre respuestas y recursos medidos en una muestra aprobada.
- Entrenamiento real, conversión/evaluación del artefacto ajustado y revisión por
  alguien distinto de quien lo entrenó. No encender el flag antes de esa evidencia.
- Validación en hardware objetivo, aprobación del reporte y piloto consentido.
- Integración coordinada de PR e instalación por el operador tras ensayo autorizado.

Responsables y pasos en [cierre-con-el-equipo.md](cierre-con-el-equipo.md); matriz
de las 30 historias en [estado-sprints.md](estado-sprints.md). No se cambiaron sus
responsables ni estimaciones. No existe una revisión o consentimiento implícitos
en un test verde, una planilla vacía o una respuesta aceptada por el guard.

La deuda de dependencias Vue 2/Webpack/Babel permanece explícita. Los backports
tienen regresiones e integridad comprobada; las excepciones altas/críticas
caducan el 22/11/2026. No se informa “cero vulnerabilidades” a partir de esas
excepciones ni se renuevan automáticamente. Ver inventario del frontend.
