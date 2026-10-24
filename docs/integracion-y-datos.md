# Integración y conservación de datos

`OnlineJudge/` y `OnlineJudgeFE/` son repositorios independientes del backend y
frontend originales. El deploy conserva gitlinks; cada cambio se publica en su
repositorio, con mensajes en español y sin coautorías. Juntarlos permite pruebas,
pero no convierte tres ramas en una instalación ya actualizada.

La plataforma candidata usa Django 5.2/Python 3.12/PostgreSQL 17 y Vue 2 con
Webpack/Babel heredados. No conectar este backend a PostgreSQL 10. Las pruebas
de interfaz son 13 más las regresiones de dependencias; se compilan ambas
entradas con `yarn.lock` y `--frozen-lockfile`.

## Procedimiento vigente

La guía única de actualización, respaldo, restauración y reversión es
[actualizacion-django52-pg17.md](actualizacion-django52-pg17.md). El ensayo vigente
es `scripts/verify_upgrade.py`, con `compose.upgrade-verify.yml`, un nombre de
proyecto nuevo y datos sintéticos. `scripts/verify_deploy.py`/`compose.verify.yml`
pertenecen al ensayo histórico sobre Django 3.2/PG10: no usarlos con la imagen
moderna. Las instrucciones antiguas de mezclar el compose principal y el de
migración quedan sustituidas por la guía vigente.

El Compose principal exige un volumen **externo y existente** para PG17. Conservar
volumen PG10, configuración privada, clave, Redis, archivos y usuarios. No borrar
volúmenes, reemplazar secretos, reiniciar contraseñas ni conectar dos instancias
de PostgreSQL al mismo almacenamiento. El servidor lo opera su responsable;
las herramientas de verificación no se conectan a él.

Antes de abrir escrituras, probar reversión al almacenamiento original preservado.
Después de abrirlas, volver a PG10 perdería actividad: cerrar escrituras y resolver
hacia delante o preparar una conciliación aprobada. Los ensayos sintéticos no
sustituyen restaurar una copia autorizada real ni revisar su procedencia.

## Integración de ramas

Backend #38 ya fue fusionado. Backend #50, frontend #123 y deploy #3 conservan la
revisión coordinada pendiente. El sincronizador antiguo de `main` se pausó el
24/10/2026 (`disabled_manually`) para impedir una pareja Django5.2/PG10.
No volver a habilitarlo hasta integrar en `main` el gate de compatibilidad del
PR #3 y verificar los gitlinks. No ejecutar el workflow manualmente como prueba:
escribe en `main`. Ninguna de estas acciones despliega en Coolify.

La [guía de entrega](entrega.md) reúne uso, evidencias y pendientes reales. El
[cierre con el equipo](cierre-con-el-equipo.md) asigna las revisiones humanas.
