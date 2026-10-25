# Guion de defensa — diez minutos

## 0:00–1:00 · Problema y objetivo

El juez automatiza la evaluación de programas, pero un veredicto no explica por sí
solo cómo continuar aprendiendo. LizardJudge añade entrenamiento guiado sin alterar
el veredicto, la puntuación ni las reglas de los concursos. El objetivo demostrado
es integrar esos servicios de forma funcional, con aislamiento y recuperación.

## 1:00–2:00 · Arquitectura y decisiones

Mostrar navegador Vue 2 → Nginx/Django → PostgreSQL/Redis/Dramatiq → juez aislado.
El tutor usa un motor interno y llama.cpp; el backend decide propiedad, nivel y
contexto. El navegador no puede habilitar ayuda en concursos ni elegir entregas
ajenas. Se conservó Vue 2 para mantener el sistema y se coordinó Django/PG17.

## 2:00–4:30 · Demostración del estudiante

1. Ingresar con `estudiante-demo`; abrir `DEF-SUMA` e iniciar entrenamiento.
2. Elegir Python3. Enviar una expresión incorrecta y esperar el Wrong Answer real.
3. Abrir Ayuda del tutor y pedir Pista 1. Identificar fuente, incertidumbre y aviso
   de demostración si responde el modelo experimental.
4. Mostrar que Pista 2 exige otro intento juzgado posterior. Enviar una modificación
   incorrecta, esperar el juez y pedir Pista 2. Repetir el ciclo para Pista 3.
5. Enviar una solución correcta. Mostrar Accepted y el logro/mascota de Mi práctica.
   Repetir AC no incrementa el número de problemas distintos resueltos.

Usar una instancia nueva para ensayar este guion completo; el sistema conserva el
historial y el máximo de ayuda. El verificador automatizado realiza este mismo ciclo
con login real, navegador, API, cola y juez; no inserta veredictos en la base.

## 4:30–5:30 · Demostración docente

Ingresar con `docente-demo`. Abrir la configuración del problema, guardar otro
borrador y activar una versión. Explicar que las sesiones existentes siguen
ligadas a su versión original; las nuevas usan la versión activada. Mostrar
conceptos y sus explicaciones. No editar versiones activadas directamente.

## 5:30–7:00 · Datos, clasificador y ajuste del modelo

Mostrar los 144 ejemplos sintéticos y las 36 soluciones de control ejecutadas en
el mismo juez de la aplicación. Las cuatro familias observadas son compilación,
ejecución, lógica y tiempo. La partición es por problema: 96/24/24 y cero duplicados
entre conjuntos. Se conservaron las revisiones como borradores.

Mostrar los informes reales del clasificador y QLoRA. El ajuste usa un modelo de
1,5B, NF4, LoRA r=8/alpha=16, fp16, semilla 2026 y tres épocas en RTX 2060 SUPER.
El entrenamiento duró 500,49 segundos. Los prompts y el formato de conversación
se comparten con la inferencia. Test se mantiene separado de validación.

La exactitud en estas cuatro familias no demuestra reconocer cualquier error de
programación: el veredicto es una característica fuerte y dos categorías no están
representadas. La pérdida del modelo tampoco mide aprendizaje de estudiantes.

## 7:00–8:30 · Seguridad y recuperación

Mostrar evidencia de permisos, CSRF, propiedad, cuotas, idempotencia, exclusión de
concursos y contexto sin casos privados/soluciones oficiales. La salida pasa un
guard heurístico; si falla, el sistema recurre al respaldo. No prometer una garantía
semántica absoluta ni una certificación completa del sandbox.

Explicar la actualización PG10→17 en almacenamiento separado, comparación de
datos/archivos/Redis y conservación de la clave y sesión. El rollback se ensayó
antes de abrir escrituras; después exige preservar y conciliar la actividad nueva.

## 8:30–10:00 · Entrega y límites

Mostrar main, CI y los artefactos por SHA, junto con la demostración local y su guía.
Separar publicación de imágenes e instalación en el servidor. Presentar el piloto
como propuesta no ejecutada, sin participantes ni resultados inventados. El sistema
funcional y el experimento sintético son lo entregado; la eficacia pedagógica y la
validación con una población real quedan como ampliaciones.
