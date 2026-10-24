# Estado de las 30 historias

Se conservan los diez sprints, responsables y 174 SP del tablero. “Implementado”
significa código y prueba bajo revisión en los tres PR; no implica merge, aprobación
humana ni despliegue. Ninguna historia se cierra solamente por tener archivos.
PR backend #38, frontend #123, integración #3, en los repositorios originales.

| Historia | Sprint | SP | Responsables originales | Evidencia y pendiente real |
| --- | --- | --- | --- | --- |
| PB-01 | 1 | 5 | BenjaminSM04 | Configuración y acceso servidor; pruebas de permisos/CSRF. Implementado, revisión/integración. |
| PB-02 | 1 | 5 | SamuelVicente937, BenjaminCalle1233 | Sesiones/intentos, concurrencia, nivel al instante del envío e historia protegida. Implementado, revisión/integración. |
| PB-04 | 1 | 3 | Auza056 | Esquema, guía y ejemplos de seis lenguajes; falta aprobación pedagógica humana real. |
| PB-03 | 2 | 5 | BenjaminSM04, SamuelVicente937 | Versiones inmutables con trigger DB y sesiones fijadas; edición/activación docente en UI. Implementado, revisión/integración. |
| PB-05 | 2 | 5 | Auza056 | Exportador autorizado y anonimización; no se exportó historia real. Falta autorización y muestra revisada. |
| PB-06 | 2 | 8 | SamuelVicente937, BenjaminCalle1233 | 54 variantes ejecutadas, imagen/hash/observaciones reproducibles; son borradores, cobertura limitada y revisión pendiente. |
| PB-07 | 3 | 8 | SamuelVicente937, Auza056 | Validador y herramienta de revisión, autor distinto del revisor; falta etiquetado/acuerdo/aprobación reales. |
| PB-08 | 3 | 5 | BenjaminCalle1233 | Pipeline de particiones por problema, procedencia, hashes y contaminación; falta dataset humano aprobado. |
| PB-09 | 3 | 5 | BenjaminSM04 | Diagnóstico de compilación por evidencia mínima, sin rutas ni causas inventadas. Implementado y probado. |
| PB-10 | 4 | 5 | SamuelVicente937 | Explicador conservador de tiempo/memoria/ejecución; no infiere señal o línea sin evidencia. Implementado y probado. |
| PB-11 | 4 | 8 | BenjaminSM04 | Clasificador NB y umbral de validación, probado con fixtures; entrenamiento sobre datos aprobados pendiente. |
| PB-12 | 4 | 5 | BenjaminCalle1233, Auza056 | Evaluador held-out, macro F1, confusión, soporte y lenguaje/baseline; resultados reales pendientes. |
| PB-13 | 5 | 5 | BenjaminSM04 | Benchmark común de candidatos y evidencia; faltan dos modelos medidos, memoria y selección revisada. |
| PB-19 | 5 | 5 | SamuelVicente937, BenjaminCalle1233 | Contexto por lista positiva, relación de entregas, redacción y pruebas señuelo. Implementado, revisión de seguridad. |
| PB-14 | 5 | 8 | Auza056 | Notebook reproducible y validado estructuralmente; no ejecutado con GPU/dataset aprobados. |
| PB-15 | 6 | 8 | BenjaminSM04, SamuelVicente937 | Entrenador LoRA/QLoRA, checkpoints, semillas, hashes y puertas de selección; no hay ajuste ni artefacto real. |
| PB-16 | 6 | 5 | BenjaminCalle1233, Auza056 | Criterios y reporte de evaluación preparados; falta evaluación humana/adversarial del modelo real. |
| PB-17 | 7 | 8 | BenjaminSM04 | Motor/red internos, manifiesto/checksums y readiness cerrada sin modelos. Inferencia real depende PB-15/PB-16. |
| PB-18 | 7 | 8 | BenjaminCalle1233 | Endpoint autenticado por sesión, propiedad/CSRF/cuotas/idempotencia. Implementado y probado. |
| PB-25 | 7 | 5 | SamuelVicente937, Auza056 | Exclusión servidor de concursos/evaluaciones y entregas relacionadas. Implementado y probado. |
| PB-20 | 8 | 8 | SamuelVicente937 | Panel completo, estados, reintentos, móvil/teclado/tema; Chromium y componentes. Implementado, revisión de usuario. |
| PB-21 | 8 | 5 | BenjaminCalle1233 | Último intento resuelto por servidor, fuente/incertidumbre y valoración única. Implementado y probado. |
| PB-24 | 8 | 5 | BenjaminSM04, Auza056 | Guard/regresiones, contexto acotado y salida segura; filtros heurísticos no garantizan ausencia semántica de soluciones. Falta evaluación del modelo. |
| PB-22 | 9 | 8 | BenjaminCalle1233, Auza056 | Tres niveles y nuevo intento posterior; sin salto/retroceso ni niveles escritos por cliente. Implementado y probado. |
| PB-23 | 9 | 5 | SamuelVicente937 | Conceptos y explicaciones fijados a versión; UI docente/alumno. Implementado y probado. |
| PB-26 | 9 | 5 | BenjaminSM04 | Respaldo determinista/estático, circuito, límites de tamaño y presupuesto total. Implementado y probado. |
| PB-27 | 9 | 3 | BenjaminCalle1233 | Métricas únicas, agregados p50/p95/utilidad/versiones y purga dry-run de 90 días. Implementado y probado. |
| PB-28 | 10 | 8 | BenjaminSM04, BenjaminCalle1233 | Suite, Chromium, migración/recuperación, juez y carga local; faltan hardware objetivo, modelo real y aprobación del reporte. |
| PB-29 | 10 | 5 | Auza056 | Protocolo/instrumentos y resultados explícitamente vacíos. Piloto no ejecutado; requiere autorización y consentimiento. |
| PB-30 | 10 | 3 | SamuelVicente937 | Guías de actualización/recuperación/uso/riesgos y ensayo aislado. Falta revisión de otro integrante e instalación por operador. |

El tablero inicial marcaba PB-06–PB-09 Done sin que todo su código/evidencia
estuviera en el checkout público. La implementación recupera los componentes
técnicos, pero no convierte revisiones o entrenamiento ausentes en hechos.
El registro de auditoría debe conservar esa discrepancia al actualizar estados.

La mascota, práctica personal, tema, CSRF/archivos y actualización Django/PG17 son
requisitos transversales adicionales. La verificación no toca el servidor real.
La relación con las ramas de entrega privada fue comprobada: contienen correcciones
propias y continúan separadas e intactas. No se copiaron sus archivos privados a
estos repositorios públicos ni se afirma que ambas historias de migraciones sean
intercambiables. El operador debe identificar la procedencia del backend instalado.

No se promete completar aprobaciones mediante automatización. Recursos externos
concretos: autorización para historia, revisores pedagógicos, dataset aprobado,
dos candidatos con memoria medida, GPU/hardware objetivo y participantes consentidos.
