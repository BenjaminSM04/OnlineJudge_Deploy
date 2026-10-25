# Defensa y entrega funcional de LizardJudge

El alcance de esta versión es una plataforma funcional y una demostración técnica
reproducible. Por decisión del responsable del proyecto, el piloto se conserva como
propuesta documental y no bloquea la entrega. No se afirma que haya participantes,
consentimientos, aprobación institucional ni mejora del aprendizaje comprobada.

## Qué se entrega

- Juez con seis lenguajes, problemas y concursos, autenticación y administración.
- Tutor propio por sesión, configuración pedagógica versionada, explicaciones,
  conceptos, tres niveles de pistas, valoración y respaldo cuando falla el modelo.
- Práctica personal, logros únicos, mascota y temas claro/oscuro en Vue 2.
- Actualización Django 5.2/Python 3.12/PostgreSQL 17 con recuperación ensayada.
- Modo de demostración sintética, clasificador entrenado y ajuste QLoRA real.
- CI y publicación de imágenes, pruebas de navegador/cola/juez y guías de operación.

El modo normal conserva sus requisitos de revisión. El modo técnico se habilita
explícitamente, admite únicamente sintéticos no rechazados y mantiene las revisiones
en borrador. Sus manifiestos no se aceptan por defecto en el motor normal.

## Demostración local

Desde el repositorio de integración con sus dos submódulos, Docker Linux y Python:

```sh
python scripts/defense_demo.py init --project lizardjudge-defensa-mi-entrega --port 18084 --build
```

Para usar el modelo ajustado, añadir `--model-directory` con el directorio que
contiene **model.gguf, classifier.json y manifest.json** del experimento técnico.
La ejecución realizada en esta máquina conserva ese directorio en
`artifacts/defensa-final-20261024/runtime-ready`. Los pesos no se incluyen en Git.
El comando imprime la ruta del archivo privado de contraseñas; abrirlo localmente.
Las cuentas son `docente-demo` y `estudiante-demo`, con contraseñas aleatorias.
Nunca copiar ese archivo, claves ni volúmenes de demostración al servidor real.

La interfaz escucha únicamente en `http://127.0.0.1:18084` (o el puerto elegido).
El juez, PostgreSQL, Redis y los modelos no publican puertos. Solo el backend
conecta la red web con la red interna. Se crean volúmenes propios; se rechaza un
nombre que ya tenga datos sin el estado privado correspondiente.

```sh
python scripts/defense_demo.py status --project lizardjudge-defensa-mi-entrega
python scripts/verify_defense_demo.py --project lizardjudge-defensa-mi-entrega
python scripts/defense_demo.py stop --project lizardjudge-defensa-mi-entrega
python scripts/defense_demo.py start --project lizardjudge-defensa-mi-entrega
```

Con modelo, el verificador admite `--require-model`: comprueba que las respuestas
provienen de inferencia real y que muestran el aviso experimental. Ejecutarlo en
una demostración nueva: utiliza los tres niveles de la sesión y conserva después
su historial, entregas y logros. No reinicia el progreso para repetir una prueba.
`stop/start` conserva contraseñas, clave, base, archivos y sesiones Redis. No usar
`down -v`, limpieza general de Docker ni los datos de una instalación existente.

## Reproducir los experimentos

1. `python scripts/generate_defense_dataset.py artifacts/variantes-nuevas` ejecuta
   controles y variantes en el juez fijado. Se publican los 144 borradores y sus
   180 observaciones en `OnlineJudge/docs/ai-tutor/defensa/`.
2. Usar el entorno separado de `OnlineJudge/deploy/requirements-training.txt`;
   Torch CUDA se instala desde su índice oficial. El backend de servicio no lleva
   estas dependencias. El conversor fijado requiere también sentencepiece 0.2.1.
3. `OnlineJudge/scripts/train_technical_demo.py prepare --help` prepara particiones,
   clasificador y selección técnica desde mediciones reales. Fijar la revisión
   safetensors y sus archivos, y pasar los ejemplos de defensa mediante `--examples`.
4. `train_technical_demo.py train DIRECTORIO` ejecuta QLoRA, con reanudación explícita
   y un nombre nuevo si se conserva un intento fallido. No se aprueba ningún ejemplo.
5. `export_technical_model.py --help` fusiona, convierte y cuantiza con llama.cpp
   fijado al commit `c7fc5094179bf8a9c73c18593db714f8da41a402` (b11804).
6. `scripts/evaluate_defense_model.py --help` compara base y ajustado sobre test
   separado; guarda salidas y tiempos reales. Un check de formato no sustituye
   corrección pedagógica. No elegir hiperparámetros mirando test.

## Cómo presentar el trabajo

[Guion de diez minutos](guion.md), [preguntas técnicas](preguntas.md) y
[alcance y evidencias](alcance.md) reúnen el material para la exposición.
La demostración no necesita usuarios reales. Si no hay GPU o modelo disponible,
el juez y el tutor de respaldo siguen funcionando; identificar siempre la fuente
que aparece en pantalla. La revisión pedagógica y el piloto son trabajo futuro.

Para una instalación real se mantiene el procedimiento independiente de
[actualización y recuperación](../actualizacion-django52-pg17.md). La defensa local
no opera Coolify ni certifica que la instalación privada ya esté actualizada.
