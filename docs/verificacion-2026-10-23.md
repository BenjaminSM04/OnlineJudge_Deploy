# Evidencia de integración — 23 de octubre de 2026

Este informe corresponde al primer corte de conservación (`46e0bec`/`bce42e1`).
La entrega ampliada, sus pruebas y pendientes se registran en
`continuidad-sprints.md`, `estado-sprints.md` y `actualizacion-django52-pg17.md`.
Las versiones y cifras siguientes son históricas.

Entorno local Docker, proyectos `lizardjudge-verificacion-20261023` y
`lizardjudge-verificacion-final-20261023`. Datos exclusivamente sintéticos.
El checkout de trabajo original y sus submódulos permanecen sin modificaciones;
los cambios están en el worktree `OnlineJudge_Deploy_revision`.

## Cambios

- Backend `46e0bec`: arranque sin administrador automático, ingreso interactivo
  validado, preservación de cuentas y clave, fallo cerrado, usuario de procesos
  coherente y ayuda de desarrollo sin eliminación de contenedores o claves.
- Frontend `bce42e1`: identificador de compilación configurable, conservando Vue 2.
- Deploy: Yarn con lockfile congelado, pruebas durante el build, entorno aislado,
  respaldo protegido, restauración lógica a almacenamiento nuevo y CI de ensayo.
- La sincronización existente de submódulos y el Compose habitual no se cambian.

## Resultados locales

| Comprobación | Resultado |
| --- | --- |
| Imagen combinada y ambas entradas del frontend | Compilación correcta con Node 22 y Python 3.12 |
| Pruebas de componentes y navegación | 8 aprobadas |
| Pruebas Django de tutor y comando administrativo | 74 aprobadas |
| System check | Sin incidencias |
| Nginx, Gunicorn y Dramatiq | Saludables |
| HTTP `/`, `/admin/`, `/api/website` | 200 |
| Migraciones con base inaccesible | Arranque cancelado, código 1 |
| Reinicio | Cuenta, hash de contraseña, entrega, intento, archivo y clave conservados |
| Restauración lógica 10 a 17 | 24 tablas, 199 filas y 20 secuencias coincidentes |
| Destino con datos | Operación rechazada sin sobrescritura |
| Dump modificado | Checksum rechazado |
| Archivo de respaldo | Clave y archivo sintético verificados sin extraer sobre el origen |

El ensayo detectó el `CREATE SCHEMA public` incluido por el dump antiguo. La
restauración omite únicamente esa entrada del índice del archivo, conservando
el esquema de initdb; no elimina esquemas. El resto se restaura transaccionalmente.
Los volúmenes y respaldos locales se conservan para inspección y están excluidos
de Git y del contexto de imagen.

## Límites y continuidad

No hubo acceso, migraciones ni despliegue en el servidor. No se ha ensayado una
copia real de producción. No se cambia la conexión de la aplicación a 17.
Django 5.2, la revisión de seguridad completa, los diez sprints del documento,
la mascota y las pruebas con juez real de seis lenguajes siguen pendientes;
esta entrega prepara la integración y la conservación de datos.

El backend sigue en Django 3.2.25, fuera de soporte, con compatibilidad oficial
insuficiente para el Python 3.12 de la imagen. El arranque y las pruebas locales
no certifican soporte, seguridad integral ni compatibilidad de toda la aplicación
con PostgreSQL 17. Debe resolverse antes de completar el cambio de plataforma.

Las ramas publicadas se entregan como borradores de PR para evitar que el Action
de sincronización propague una integración sin revisar. No se publican respaldos,
claves, resultados inventados ni datos de alumnos. El estado del CI remoto se
consulta en GitHub y se distingue de estos resultados locales.
