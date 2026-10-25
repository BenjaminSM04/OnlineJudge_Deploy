# Preguntas y respuestas para la defensa

| Pregunta | Respuesta verificable |
| --- | --- |
| ¿Qué aporta el proyecto? | Entrenamiento guiado integrado al juez, versiones pedagógicas, pistas progresivas, valoración y práctica personal, con operación y recuperación comprobadas. |
| ¿Por qué Vue 2? | Se conservó la arquitectura solicitada para reducir el riesgo de reconstruir toda la interfaz. La deuda y las excepciones de dependencias permanecen documentadas. |
| ¿La IA decide Accepted? | No. El juez ejecuta los casos; el tutor no modifica código, resultado ni puntuación. |
| ¿Puede usarse en concursos? | El servidor excluye concursos y evaluaciones del tutor; ocultar un botón no es el control de acceso. |
| ¿Por qué Django 5.2 y PostgreSQL 17? | La actualización es coordinada: el backend moderno requiere PostgreSQL compatible y no debe arrancarse sobre el compose histórico PG10. |
| ¿Se preservan los datos? | El ensayo compara columnas y registros originales, secuencias/objetos, archivos, clave y sesión Redis en volúmenes separados. Una instalación real necesita su propio respaldo y ensayo autorizado. |
| ¿Qué se entrenó? | Un clasificador Naive Bayes y un adaptador QLoRA real sobre sintéticos, con partición por problema y manifiestos/checksums. No se usaron entregas de estudiantes. |
| ¿Por qué QLoRA? | Cuantiza el modelo base a NF4 y ajusta adaptadores pequeños; permitió ejecutar el experimento en 8 GB de VRAM. Se usó fp16 porque la GPU Turing no tiene bf16 nativo. |
| ¿Cuántos ejemplos hay? | 144 variantes observadas y 36 controles AC, en seis problemas/seis lenguajes. 96 train, 24 validation y 24 test. |
| ¿Qué significa el F1 del clasificador? | El macro F1 considera seis categorías. En el experimento cuatro tienen soporte y dos no. El veredicto separa fuertemente las cuatro familias; no se demuestra diagnóstico causal fino ni distinción entre errores conceptuales y lógicos dentro de WA. |
| ¿La pérdida baja prueba calidad pedagógica? | No. Mide ajuste a los objetivos textuales sintéticos. La evaluación técnica registra formato, guard y tiempos; no demuestra aprendizaje ni utilidad con estudiantes. |
| ¿Se está entrenando con test? | No. Los problemas de test no entran en train o validación. La semilla y las particiones se conservan en el manifiesto. |
| ¿Puede dar una solución completa? | El prompt y el guard lo restringen, pero el filtro es heurístico. No se afirma garantía semántica absoluta; ante salida rechazada se usa respaldo. |
| ¿Qué pasa si el modelo cae? | Timeout, circuito y validación de salida provocan respaldo determinista o pistas/conceptos docentes. El juez sigue funcionando. |
| ¿Por qué tres pistas? | Separan concepto, localización y estrategia. El servidor exige un nuevo intento juzgado posterior antes de avanzar; releer un nivel conserva su respuesta. |
| ¿Qué evita cambiar una configuración antigua? | Versiones inmutables y sesiones fijadas a una versión. Las correcciones se activan como nuevas versiones. |
| ¿Por qué no se publican los pesos en Git? | Son artefactos grandes, versionados por manifiesto/hash y separados del código. La demostración los monta en solo lectura. |
| ¿El merge ya actualiza el servidor? | No. CI/GHCR y servidor son etapas distintas. Coolify y los repositorios privados siguen bajo control del operador. |
| ¿Se hizo el piloto? | No. Se entrega protocolo e instrumentos como propuesta. No se presentan participantes, consentimientos ni resultados de campo. |
| ¿Qué falta para validar eficacia educativa? | Una evaluación con población real, revisión pedagógica y diseño experimental apropiado; queda fuera del cierre funcional solicitado. |
