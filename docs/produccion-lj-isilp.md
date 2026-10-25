# Puesta en producción de lj.isilp.com

## Versión y datos

Usar `compose.produccion.yml` y un archivo privado basado en
`.env.produccion.example`. Seleccionar `OJ_APP_IMAGE` por SHA/digest publicado
después de la CI. El perfil no compila código en el servidor ni activa la IA
experimental. No emplear `compose.defensa.yml` ni sus cuentas, flags o volúmenes.

Este archivo requiere rutas existentes y un volumen PG17 externo; una variable
rellenada no acredita que corresponda a la instalación vigente. Inspeccionar los
montajes de Coolify y seguir [migración y recuperación](actualizacion-django52-pg17.md)
antes de arrancar. No cambiar el nombre de proyecto ni los montajes históricos
sin mapearlos y restaurarlos explícitamente. Conservar clave Django y contraseñas.
Conservar también la configuración y el formato persistido de Redis. Este perfil
no enciende AOF automáticamente sobre un directorio histórico con solo RDB.
Detener la instancia anterior antes de arrancar otra sobre el mismo almacenamiento;
nunca ejecutar dos Redis o dos PostgreSQL sobre un mismo directorio.
Si la instalación privada usa volúmenes nombrados en lugar de bind mounts, adaptar
los montajes a esos volúmenes externos exactos; no sustituirlos por carpetas vacías.

Validar sin mostrar valores:

```sh
docker compose --env-file /ruta/privada/produccion.env -f compose.produccion.yml config --quiet
```

El proceso de actualización exige respaldo fuera del host, ensayo de restauración
con copia real, mantenimiento, cola drenada y comparación antes de abrir escrituras.
Los ensayos sintéticos de CI no certifican los datos reales de este servidor.

## Dominio, proxy y comprobaciones

Configurar DNS y certificado para `lj.isilp.com`. HTTPS termina en el proxy.
El puerto de la aplicación solo se publica en loopback; un proxy en contenedor
debe compartir la red `web` y acceder a `oj-backend:8000`, o adaptar esa red a
la red efectiva de Coolify. No publicar PostgreSQL, Redis o juez.
`TRUST_PROXY_HTTPS=1` solo cuando el proxy controla la cabecera correspondiente.
Las cookies son seguras; verificar sesión, CSRF y recuperación con HTTPS real.
Configurar la URL del sitio en administración como `https://lj.isilp.com`.

Comprobar `/healthz`, migraciones, sesión histórica, casos privados, archivos,
seis lenguajes, cola, límites del juez y registro/correo antes de reabrir acceso.
Los límites iniciales del juez no son un estudio de capacidad; medir memoria,
procesos y concurrencia con el hardware y lenguajes reales y ajustar por evidencia.
Configurar monitor externo, alertas de disco/cola/juez, rotación y respaldo periódico
con restauración ensayada. No reiniciar versiones antiguas sobre datos nuevos.

## Resend por SMTP

En Administración → Configuración → SMTP, pulsar **Usar Resend**:

- Servidor `smtp.resend.com`, puerto `465`, cifrado SSL/TLS.
- Usuario `resend`, contraseña: API key de Resend ingresada solo en el formulario privado.
- Correo: un remitente autorizado en un dominio verificado en Resend. Por ejemplo,
  `notificaciones@isilp.com` únicamente si ese dominio y remitente están habilitados;
  conocer `lj.isilp.com` no demuestra que la verificación esté hecha.
- Alternativa: puerto `587`, cifrado STARTTLS; no activar SSL y STARTTLS a la vez.

El usuario SMTP y el remitente son independientes. Al editar, una contraseña vacía
conserva la anterior; la API no devuelve la clave. Elegir Resend no guarda nada
automáticamente ni reemplaza la contraseña. Ingresar la nueva clave si se cambia
de proveedor. El transporte verifica certificados y limita la conexión a 15 s.

Verificar el dominio y los registros DNS indicados por Resend; no inventar valores
DKIM/SPF. Probar envío a un destinatario propio desde la administración y luego
recuperación de contraseña con URL pública correcta. Comprobar recepción y eventos
en Resend: aceptar SMTP no garantiza entrega en bandeja de entrada.
No se envían correos externos en las pruebas automatizadas; usan transporte simulado.

Fuente: [documentación oficial de SMTP de Resend](https://resend.com/docs/send-with-smtp).

## Administración y casos escritos

Los menús del editor usan el idioma activo y traducciones completas de tabla,
alineación, enlaces e imágenes. Cambiar el idioma reconstruye las barras sin
descartar el formulario; los editores liberan sus recursos al salir.
Los casos escritos admiten hasta 100 pares y
1 MiB total. Conservan espacios y texto UTF-8, normalizando CRLF como el importador ZIP.
Los casos privados son distintos de los ejemplos públicos del enunciado.
Pulsar **Aplicar casos de texto** prepara un conjunto nuevo y después **Guardar**
vincula el problema. Reemplazar exige confirmación y conserva los archivos previos.
ZIP sigue disponible para archivos grandes y juez especial.
Para editar un conjunto existente, usar **Cargar casos guardados**. Si hay texto
modificado, se solicita confirmación antes de descartarlo. No se permite guardar
el problema con cambios de texto que todavía no se aplicaron.

La regresión `scripts/verify_admin_production.py --project NOMBRE_DE_DEMOSTRACION`
comprueba login, idiomas, guardado, casos privados, dos veredictos reales, páginas
administrativas y móvil. Solo admite un proyecto de defensa con estado privado
local; nunca apuntarla al servidor. La suite SMTP simula el transporte.

## IA y alcance de la liberación

La aplicación de producción usa tutor de respaldo con IA generativa apagada.
El artefacto QLoRA entregado es `technical-demo`, no una aprobación pedagógica.
Para habilitar el modelo normal quedan evaluación humana independiente, manifiesto
compatible, medición de capacidad/plazos y prueba de caída y respaldo. El piloto
académico continúa como propuesta documental; no bloquea liberar el juez.

La auditoría de dependencias conserva los backports y excepciones acotadas de
Vue 2/Webpack descritos en `OnlineJudgeFE/docs/seguridad/`. No equivale a ausencia
de alertas en Dependabot. Las excepciones altas/críticas caducan el 22/11/2026;
no extenderlas automáticamente ni desactivar la auditoría.
