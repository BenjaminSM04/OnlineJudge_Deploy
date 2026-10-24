# Cierre con el equipo: lo que solo pueden hacer personas

La implementación técnica está bajo revisión con evidencia reproducible. Lo que sigue necesita
decisiones, revisiones o permisos humanos reales. Ningún comando de este
repositorio los sustituye y ninguna historia debe cerrarse sin esa evidencia.
Responsables según `estado-sprints.md`.

## 0. Antes de nada (BenjaminSM04)

- Integrar juntos frontend #123 y deploy #3, y revisar backend #50. El backend #38
  ya está en `main`; mientras #3 no esté integrado, el Action programado de `main`
  del deploy sincroniza sin controles y combinaría Django 5.2 con el compose PG10.
  El 24/10/2026 se desactivó temporalmente ese workflow (`disabled_manually`).
  Mantenerlo así hasta integrar el gate de compatibilidad del PR #3 y verificar
  los gitlinks; después reactivarlo explícitamente. No se tocó el servidor.
- Las imágenes `ghcr.io/benjaminsm04/lizardjudge(-tutor):sha-<SHA>` son públicas y
  no se despliegan solas.

## 1. Revisión de borradores (PB-04, PB-07): Auza056 coordina

Duración estimada: 1–2 h por revisor para 54 ejemplos.

1. Leer `OnlineJudge/docs/ai-tutor/guia-etiquetado.md` y `guia-pedagogica.md`.
2. Reexportar la planilla con las columnas de incertidumbre, procedencia y hash
   incorporadas el 24/10/2026; la planilla antigua ya no es válida:
   `python manage.py export_tutor_review_sheet docs/ai-tutor/variantes/ejemplos-borrador.json planilla-<usuario>.csv`
3. Cada revisor llena `decision` (approved/rejected/review), `reviewer` (su usuario
   de GitHub) y `notes`, sin editar las demás columnas. Las correcciones de
   contenido se hacen en el JSON y se vuelve a exportar.
4. Ejercicio de acuerdo (`ejercicio-acuerdo.md`): dos revisores revisan por
   separado la misma muestra y se registra la concordancia. Se conservan ambas
   planillas como evidencia y se aplica solo la decisión acordada:
   `python manage.py apply_tutor_review_sheet ORIGEN.json planilla.csv aprobados-v1.json --reviewer <usuario>`
5. Validar: `python manage.py validate_tutor_examples aprobados-v1.json`.

Con 54 sintéticos de tres problemas la cobertura es limitada. Para un dataset útil
hacen falta más problemas y, si se usa historia real, el paso 2.

## 2. Datos reales (PB-05): requiere autorización institucional

Solicitar por escrito a la carrera/universidad la autorización para usar entregas
históricas anonimizadas (`origen-datos.md`). Sin ese documento no se ejecuta
`export_authorized_submissions`. Guardar la autorización fuera del repositorio
público y registrar solo su referencia.

## 3. Dataset y clasificador (PB-08, PB-11, PB-12): BenjaminCalle1233

Con `aprobados-v1.json`:
`python manage.py tutor_dataset build aprobados-v1.json artefactos/dataset-v1`, luego
`train` y `evaluate` según `modelos-y-dataset.md`. El umbral se elige en
validation; test solo se usa una vez. Revisar macro F1 contra la clase mayoritaria.

## 4. Benchmark y selección (PB-13): BenjaminSM04

Ya existen mediciones reales sobre borradores (`evidencias/medicion-modelos.json`):
solo Qwen2.5-Coder-1.5B Q4_K_M es viable con 2 CPU y 3 GB. Falta:

1. Repetir `OnlineJudge/scripts/benchmark_tutor_models.py` con la muestra aprobada
   y al menos dos candidatos (se puede añadir otro de ≤ 1,5 GB).
2. Que una persona distinta del autor revise cada respuesta con la rúbrica y marque
   `human_review`. Varias respuestas actuales proponen la corrección directa: es
   justamente lo que la rúbrica debe rechazar.
3. Escribir la selección (`model_id`, revisión de 40 hex, licencia, `reviewer`,
   archivo y sha256 del benchmark, `rubric_version`).

## 5. Entrenamiento (PB-14, PB-15): Auza056, BenjaminSM04, SamuelVicente937

El entorno está comprobado en la RTX 2060 SUPER del equipo de BenjaminSM04:

- Python 3.13, venv en `D:\Juez Virtual\venv-entrenamiento` con
  `deploy/requirements-training.txt`. Torch debe instalarse desde
  `https://download.pytorch.org/whl/cu126` (PyPI entrega la versión CPU).
- Registrar `training_model` en selección y candidato del benchmark revisado:
  repositorio safetensors, revisión propia de 40 hex, licencia y referencia de
  procedencia. La revisión del repositorio GGUF no identifica sus pesos base.
  Descargar esa fuente entrenable fijada; opcional: `HF_TOKEN`.
- Ejecutar `train_tutor_model` o el notebook. Un 1,5B en QLoRA cabe en 8 GB.
- Convertir el adaptador fusionado a GGUF con llama.cpp (`convert_hf_to_gguf.py` y
  `llama-quantize` Q4_K_M) y volver a medir con `scripts/measure_tutor_candidates.py`.

## 6. Evaluación del modelo (PB-16, PB-24): BenjaminCalle1233, Auza056

Evaluación humana y adversarial del modelo ajustado sobre test y casos de intento
de extraer soluciones. Firmar `reporte-pb28.md` por alguien distinto del
entrenador y completar `manifest.json` (`decision=integrate`, `reviewer`,
`reviewed_at`). Recién entonces se valora `AI_TUTOR_MODEL_ENABLED=1` en un ensayo.

## 7. Piloto (PB-29): Auza056

Requiere aprobación del docente o comité de ética y consentimiento informado de
cada participante (`piloto/protocolo.md`, `piloto/instrumentos.md`). No usar
usuarios de prueba como participantes. Resultados agregados en `piloto/resultados.md`.

## 8. Paso a la instalación real (PB-30): operador, con otro integrante

1. Consultas de solo lectura sobre la base real: versión de PostgreSQL, filas de
   `django_migrations`, columnas JSON y recuentos por tabla.
2. Copia real restaurada en un entorno aislado y
   `python scripts/verify_upgrade.py --legacy-sha <commit instalado>` como guía del
   ensayo (ya pasó con la procedencia privada sobre datos sintéticos).
3. Variables: `COOKIE_SECURE`, `TRUST_PROXY_HTTPS`, `ALLOWED_HOSTS` (o
   `DJANGO_ALLOWED_HOSTS`), `CSRF_TRUSTED_ORIGINS`, healthcheck `/healthz`.
4. Integrar primero en el repositorio que usa el servidor las correcciones propias
   de la rama privada (p. ej. dificultad QDUOJ), por su PR correspondiente.
5. Ventana de mantenimiento con respaldo, `migrate`, verificación y rollback
   ensayado antes de abrir escrituras (`actualizacion-django52-pg17.md`).
