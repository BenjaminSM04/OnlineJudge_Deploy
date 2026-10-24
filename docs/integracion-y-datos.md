# Integración y conservación de datos

## Repositorios

`OnlineJudge/` y `OnlineJudgeFE/` son checkouts independientes de
`BenjaminSM04/PS2B2026-JuezVirtual_Backend` y
`BenjaminSM04/PS2B2026-JuezVirtual_frontend`. Que estén juntos permite compilar y
probar el sistema. El deploy conserva sus gitlinks y el Action
`update-submodules.yml`, que sincroniza las ramas `main`. Los commits del backend
y frontend se publican en sus respectivos repositorios.

Los cambios de esta entrega se preparan en ramas `codex/` para revisarlos antes
de que la sincronización de `main` los incorpore. Ninguna herramienta de este
documento conecta al servidor. El operador realiza el despliegue.

## Estado de la plataforma

Esta entrega mantiene Vue 2, su arquitectura y `yarn.lock`. La imagen instala
con Yarn Classic `--frozen-lockfile`, ejecuta las ocho pruebas existentes de
componentes/navegación y compila ambas entradas. `FRONTEND_COMMIT` permite incluir
el commit real sin fabricar un repositorio Git en la imagen.

El backend se actualizó a Django 5.2/Python 3.12 y PostgreSQL 17. El Compose exige
un volumen externo PG17 preparado; conserva la definición del volumen histórico.
**Antes de actualizar una instalación existente**, seguir
[el procedimiento de migración y reversión](actualizacion-django52-pg17.md).
El ensayo histórico anterior queda como evidencia de su versión, no como guía
vigente para ejecutar Django 5.2 sobre PostgreSQL 10.

El arranque deja de crear administradores con contraseña conocida. Los usuarios
existentes no se eliminan ni se reinician sus contraseñas. Para una instalación
nueva, cree el administrador explícitamente en una terminal:

```sh
docker compose exec oj-backend python manage.py inituser --username administrador --action create_super_admin
```

Se solicita y confirma la contraseña sin mostrarla. Se exige longitud mínima de
12 caracteres y los validadores configurados. Si el usuario existe, la creación
se rechaza sin cambiarlo. `--action reset` sigue siendo una operación explícita.

## Ensayo independiente

Requisitos: Docker con contenedores Linux y Python 3 en el host. Desde la raíz:

```sh
docker build --build-arg FRONTEND_COMMIT="$(git -C OnlineJudgeFE rev-parse HEAD)" -t lizardjudge-revision:local .
python3 scripts/verify_deploy.py --project lizardjudge-verificacion-ensayo01
```

En PowerShell use `$commitFrontend = git -C OnlineJudgeFE rev-parse HEAD` y pase
`--build-arg "FRONTEND_COMMIT=$commitFrontend"`. Ejecute el script con `python`.
Elija un nombre de proyecto **nuevo** para cada ensayo. `compose.verify.yml` se
usa solo: no se combina con el Compose habitual. Crea volúmenes independientes
para PostgreSQL 10, PostgreSQL 17 y archivos; el HTTP solo escucha en loopback.
No inicia un juez real ni utiliza `./data` o el volumen `pgdata` del servidor.
El script genera credenciales aleatorias en memoria para cada proyecto nuevo;
no se guardan en el repositorio ni se reutilizan credenciales del servidor.

El ensayo aplica migraciones, ejecuta las pruebas de tutor y administrador,
crea datos sintéticos relacionados, comprueba HTTP y reinicio, respalda archivos
y restaura lógicamente de 10 a 17. Compara todos los registros por hashes
canónicos, cantidades, secuencias y objetos grandes. Comprueba que no puede
sobrescribir un destino poblado ni aceptar un respaldo alterado. Al terminar
detiene sus contenedores y **conserva** volúmenes y evidencias en `respaldos/`.

La memoria del comparador crece con el número de hashes de filas. Prevea espacio
y memoria suficientes al ensayar una copia de tamaño real. No se imprimen los
registros, códigos, contraseñas ni el contenido de las claves.

## Preparación de una actualización real

Antes de actualizar, inventaríe el nombre real del proyecto Compose, los commits,
imágenes por digest, montajes, tamaño y versión de BD, configuración privada y
servicios que escriben. Incluya backend, trabajadores, juez, herramientas
externas, Redis, archivos fuera de `/data` y montajes anidados. No cambie el
nombre del proyecto: eso podría crear un volumen vacío con otro nombre.

1. Ensaye primero sobre una copia autorizada y protegida del sistema real. El
   ensayo sintético no certifica que no existan incompatibilidades en esa copia.
2. Cierre escrituras y acceso de usuarios, drene las evaluaciones y detenga
   backend, juez y todos los trabajadores y escritores externos. No basta con
   ocultar un botón. Mantenga PostgreSQL disponible para el respaldo.
3. Respalde la configuración privada fuera de Git, incluidos `.env`, los secretos
   vigentes y la configuración del proxy. No genere claves nuevas al actualizar.
4. Cree un respaldo nuevo y un manifiesto protegido. Sustituya `PROYECTO_REAL` por
   el nombre comprobado; los comandos siguientes los ejecuta el operador:

```sh
python3 backup/database.py backup --project PROYECTO_REAL --compose-file docker-compose.yml --directory respaldos/antes-actualizacion --writers-stopped
python3 backup/files_backup.py --container CONTENEDOR_BACKEND_DETENIDO --output respaldos/antes-actualizacion/backend-data.tar.gz
```

El dump usa formato custom, sin instrucciones para borrar la base, y se valida
antes de emitir el manifiesto. Los archivos se leen desde los montajes del
contenedor detenido, en modo de solo lectura, incluyendo montajes anidados en
`/data`. El archivo conserva permisos y propietarios. Copie también otros
almacenamientos que el inventario sitúe fuera de `/data`. Verifique la suma del
archivo `.tar.gz.sha256` antes de restaurar; mantenga una copia fuera del host.
En Windows proteja también el directorio mediante sus ACL: `chmod` no sustituye
los permisos NTFS. Los respaldos contienen material privado y no se publican.

Si necesita conservar sesiones, preserve Redis y su persistencia. Durante el
cierre de escrituras fuerce un `SAVE`, detenga Redis y respalde su montaje
`/data`, además de la configuración correspondiente. No sustituya el Redis
existente por el del ensayo. Si hay roles PostgreSQL adicionales, respalde
también los globales y adapte los propietarios/permisos: el dump de aplicación
usa `--no-owner --no-acl` y asume el rol de aplicación precreado.

## Transición de PostgreSQL 10 a 17

`compose.migration.yml` añade exclusivamente un servicio con volumen nuevo
`pgdata17`. Conserve en el entorno privado la contraseña real de la instalación;
no copie las credenciales sintéticas de `compose.verify.yml`.

```sh
docker compose -p PROYECTO_REAL -f docker-compose.yml -f compose.migration.yml up -d --wait oj-postgres17
python3 backup/database.py restore --project PROYECTO_REAL --compose-file docker-compose.yml --compose-file compose.migration.yml --directory respaldos/antes-actualizacion --writers-stopped
```

La restauración comprueba checksum, almacenamiento diferente, versión de destino
y ausencia de tablas, secuencias u objetos grandes. Usa una única transacción y
se detiene ante errores. Después compara los datos y secuencias con el
manifiesto. No cambia el host del backend ni abre escrituras. Puede repetir solo
la comparación con la acción `verify`, usando los mismos argumentos.

**No conecte aún el backend legado a PostgreSQL 17.** Primero complete y pruebe
la actualización compatible de Django. Durante el corte posterior, con las
escrituras todavía cerradas, configure el nuevo host y ejecute las migraciones
de esquema revisadas y cualquier reconciliación histórica necesaria. Valide
usuarios, autenticación, permisos, problemas, concursos, entregas, tutor,
archivos, secuencias, cola, heartbeat y veredictos reales antes de abrir acceso.
El comparador corresponde al estado inmediatamente posterior a la restauración,
antes de migraciones que legítimamente cambien el esquema o los datos.

Nunca monte el directorio físico de PostgreSQL 10 en PostgreSQL 17. No elimine
`pgdata`, los archivos anteriores ni los respaldos después de restaurar.

## Recuperación

Antes de abrir escrituras en 17 puede cancelar el corte, volver a los commits e
imágenes anteriores y mantener la conexión a la base 10 intacta. Verifique la
clave de aplicación y los montajes originales antes de volver a iniciar. Los
scripts no eliminan ni actualizan el origen.

Después de abrir escrituras en 17, volver a 10 descartaría la información nueva:
mantenga las escrituras cerradas, respalde 17 y resuelva hacia delante o prepare
una recuperación específica que conserve los cambios. No ejecute un rollback
automático de volumen ni migraciones inversas que eliminen datos.

Una restauración de archivos se ensaya en un almacenamiento nuevo, verificando
primero su checksum y después contenidos, permisos y claves. No extraiga un
archivo sobre los datos originales como método de prueba.
