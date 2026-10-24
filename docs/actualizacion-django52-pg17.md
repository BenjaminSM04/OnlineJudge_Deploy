# Actualización y recuperación conservando datos

Esta versión coordina Django 5.2/Python 3.12/PostgreSQL 17 con el frontend Vue 2.
El servidor real queda a cargo del operador. No ejecutar un `pull && up` sobre
la instalación antigua: primero preparar y comprobar el destino. Nunca conectar
PostgreSQL 17 al directorio físico de PostgreSQL 10 ni usar `down -v`.

El Compose nuevo exige `OJ_PG17_VOLUME` **externo y existente**. Esto evita crear
silenciosamente una base vacía al actualizar. La definición `pgdata` histórica
se conserva. Un nombre de volumen nuevo no constituye una migración de sus datos.
`.env.example` no contiene credenciales: completar en privado con las vigentes,
sin mostrarlas ni reemplazarlas. Conservar nombre de proyecto Compose, DB, usuario,
contraseña, token del juez, clave Django, archivos y Redis.

## Ensayo automatizado independiente

Desde un checkout limpio con ambos submódulos y Docker Linux:

```sh
python scripts/verify_upgrade.py --project lizardjudge-upgrade-ensayo-unico --keep-running
python scripts/verify_ui.py --project lizardjudge-upgrade-ensayo-unico
python scripts/test_tutor_engine.py
python scripts/verify_judge.py
python scripts/verify_submission_e2e.py --project lizardjudge-upgrade-ensayo-unico
python scripts/verify_engine_unavailable.py
```

El primer comando exige un proyecto nuevo y genera credenciales sintéticas en
memoria. No reutilizar un nombre con datos. Construye el backend histórico
`72fc56327644e8a48e350c40a383a7949b984217` desde Git y la versión candidata.
Comprueba dump, restauración en PG17 separado, columnas originales de 21 tablas,
secuencias, objetos grandes, rechazo de destino poblado y respaldo alterado,
reversión sobre PG10 antes de escrituras y migraciones actuales. Restaura Redis
y /data en volúmenes nuevos, conserva clave y una sesión autenticada histórica.
Los reportes quedan en `respaldos/`, excluidos de Git. `--keep-running` mantiene
el ensayo; `docker compose -p NOMBRE -f compose.upgrade-verify.yml stop` lo detiene
sin eliminar volúmenes. El puerto de interfaz de ensayo es loopback 18082.

## Preparación por el operador

1. Guardar SHA de los tres repositorios, imágenes con digest y Compose/configuración
   privados anteriores. Inspeccionar los montajes efectivos mediante `docker inspect`;
   no deducir los nombres por la carpeta local. Crear una copia fuera del host y
   comprobar capacidad libre para dump, volumen nuevo y recuperación.
2. Ensayar primero sobre una copia autorizada aislada. Validar recuentos, permisos,
   archivos, concursos, sesiones y tiempos con la historia real, sin enviar datos
   al motor. No publicar respaldos o estadísticas que permitan reidentificación.
3. Programar mantenimiento, cerrar acceso de escritura, drenar cola y juez y detener
   backend/trabajadores/juez antes del respaldo. Evitar escritores externos.
   Guardar Redis mediante `redis-cli SAVE` y copiar `/data/dump.rdb` del contenedor
   exacto. Contiene sesiones/colas; guardar hash y permisos restrictivos.
4. Respaldar /data del backend detenido con `backup/files_backup.py --container
   CONTENEDOR --output RUTA_PRIVADA/backend-data.tar.gz`. Incluye clave, adjuntos,
   avatares, configuración y casos privados. No compartir ese archivo.
5. Detener PostgreSQL antiguo antes de montar su volumen en el servicio de
   migración. Definir `OJ_PG10_VOLUME` con el nombre inspeccionado y crear un volumen
   nuevo explícito para `OJ_PG17_VOLUME`; verificar que son diferentes. Levantar
   únicamente servicios de `compose.migration.yml` con perfil `migracion` y un
   proyecto de mantenimiento separado. No levantar dos PostgreSQL sobre un volumen.
6. Respaldar/restaurar con las herramientas que comprueban origen/destino:

```sh
python backup/database.py backup --project PROYECTO_MANTENIMIENTO --compose-file compose.migration.yml --source oj-postgres10 --target oj-postgres17 --directory RUTA_PRIVADA/respaldo-nuevo --writers-stopped
python backup/database.py restore --project PROYECTO_MANTENIMIENTO --compose-file compose.migration.yml --source oj-postgres10 --target oj-postgres17 --directory RUTA_PRIVADA/respaldo-nuevo --writers-stopped
```

El directorio de respaldo debe ser nuevo. La restauración rechaza destino con
tablas, secuencias u objetos grandes, almacenamiento compartido y hash alterado.
Compara todas las filas/secuencias/objetos antes de abrir el backend moderno.
Si un destino parcialmente restaurado requiere recuperación, conservarlo para
diagnóstico y elegir otro volumen nuevo; no borrar el original para “reintentar”.

7. Detener los PostgreSQL del proyecto de mantenimiento. Configurar el Compose
   de aplicación con el volumen PG17 verificado, hosts reales explícitos,
   `CSRF_TRUSTED_ORIGINS` con esquema, `COOKIE_SECURE=1` en HTTPS y confianza en
   proxy solo si la cabecera proviene de un proxy controlado. Mantener /data y Redis.
   Las migraciones se ejecutan antes de servir y se detiene el arranque si fallan.
8. Sin abrir escrituras, comprobar health, `manage.py check`, migraciones, acceso
   administrativo, sesión previa, problemas/entregas, descargas y juez. El arranque
   reconcilia logros históricos sin cambiar entregas. Conservar hash/recuentos
   anteriores y nuevos. Abrir acceso solo tras aceptar la comparación.

## Reversión

La configuración de lenguajes también es un dato persistido: cambiar `languages.py`
no sobrescribe lo almacenado. Para Go heredado, `manage.py update_go_compiler_budget`
propone la coincidencia exacta antigua; solo `--apply` actualiza esa entrada a
compilación serial y 30/60 segundos CPU/real. Conserva entradas personalizadas.
Ensayar explícitamente con la imagen del juez elegida antes de aplicar; el ensayo
E2E realiza esta transición únicamente en su fixture aislado. No usar
`reset_languages` para actualizar una instalación con personalizaciones.

Antes de abrir escrituras, detener backend/juez nuevos, volver a imágenes/Compose
anteriores sobre PG10 **original preservado**, Redis y /data correspondientes.
No conectar el backend antiguo a PG17 migrado ni ejecutar reversión destructiva
de migraciones sobre la única copia. El ensayo automatizado comprueba este punto.

Después de nuevas escrituras, PG10 ya está desactualizado: volver directamente
perdería actividad. Detener escrituras y preparar recuperación o conciliación
aprobada con respaldos y registro de actividad; no prometer rollback sin pérdida
automático en ese punto. Reversión de modelo: apagar flag, volver al directorio
aprobado anterior y verificar su digest/readiness. Configuración pedagógica: crear
otro borrador a partir del contenido correcto; sesiones existentes siguen fijadas.

Recuperación de archivos en un volumen nuevo vacío: `backup/files_restore.py
--source-container CONTENEDOR_DETENIDO --target-volume VOLUMEN_NUEVO --archive
RUTA_PRIVADA/backend-data.tar.gz`. Verifica checksum, separación y destino vacío;
rechaza enlaces/dispositivos y no sobrescribe datos. Conservar el contenedor
original permite verificar los montajes sin inferencias. Restaurar Redis por
separado en un volumen nuevo antes de iniciar el backend y verificar sesión.

Revisión por otro integrante y ensayo autorizado con datos/hardware reales siguen
pendientes. No hay acceso ni cambios al servidor en las verificaciones locales.
