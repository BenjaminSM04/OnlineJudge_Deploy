# Herramientas de la versión 2.1

Esta carpeta conserva lo que usaba el despliegue hasta la 2.1, cuando el
`Dockerfile` combinado metía el frontend compilado dentro de la imagen del
backend y el motor del tutor vivía en este repositorio:

- `Dockerfile` y `tutor_engine/`: imagen combinada y motor del tutor antiguos
  (desde la 2.2 el motor está en `OnlineJudge/tutor_engine/`).
- `compose.*.yml` y `.env.produccion.example`: ensayos de actualización,
  defensa, sprints y la guía de producción de la 2.1.
- `scripts/`: verificaciones y demostración de la defensa.
- `docs/produccion-lj-isilp.md`: guía de producción de la 2.1.

No funcionan con la 2.2.3, porque el backend ya no sirve la interfaz. Se
guardan como referencia y para consultar los resultados de la defensa
(`docs/defensa/`). Para obtener la 2.1 completa y ejecutable, use la etiqueta o
el commit anterior: `git checkout 29c2848 && git submodule update --init`.
