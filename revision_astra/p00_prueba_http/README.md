# CAJA AYACUCHO - 00 PRUEBA HTTP

Carpeta de revisión para Astra de la entrega producida por el commit `06232da9f7602b92696c1c4be57dbe25be04efec`, en la rama `caja-ayacucho/p00-prueba-http`. El repositorio GitHub de destino autorizado es [Lothbrok338/ANALIZADOR-SIAT-HISTORICO-DUPLICADOS](https://github.com/Lothbrok338/ANALIZADOR-SIAT-HISTORICO-DUPLICADOS). Es una copia de la implementación existente: generador, definición, pruebas originales, ZIP e informes históricos se conservan byte a byte. El único código añadido organiza la ejecución de las pruebas en un directorio temporal con las rutas originales.

**Validación estática realizada. Importación y ejecución en el tenant pendientes.** La publicación en GitHub facilita la revisión; no equivale a aprobación técnica ni a validación en Power Automate.

Las comprobaciones previas encontraron cero workflows, cero ejecuciones de Actions y cero despliegues registrados. La consulta de webhooks devolvió 403; el usuario autorizó expresamente el commit y push aceptando esa incertidumbre y sin continuar la investigación. Esta autorización no permite ejecutar comandos de despliegue, modificar integraciones ni hacer merge. [La evidencia previa al push](evidencia/comprobaciones_publicacion.json) conserva esa limitación.

La prueba comienza con un botón manual, verifica la configuración y contiene una única acción HTTP GET a `/health`. Conserva `https://pendiente-url-pruebas.invalid/health` como marcador bloqueante. Tiene timeout configurado `PT30S`, reintentos `None`, sondeo asíncrono desactivado y diagnóstico visible en el historial. No transmite documentos ni datos financieros. El criterio provisional de éxito es una respuesta 2xx con acción satisfactoria; la semántica del cuerpo debe confirmarse cuando exista la API de pruebas.

El alcance se limita al flujo 00. No construye API, Power Apps, SharePoint, PostgreSQL ni reglas contables. Los puntos TO-BE v0.3 del encargo conservan Power Apps institucional como interfaz futura, Power Automate Premium como orquestador, API Python independiente en Railway, SharePoint para evidencia oficial y PostgreSQL para coordinación temporal y recuperación. El alcance futuro termina en el GLOBAL mensual; Control 1, Control 3 y auditorías institucionales están excluidos.

| Archivo | Contenido |
|---|---|
| [INFORME_VALIDACION.md](INFORME_VALIDACION.md) | Informe histórico conservado; sus rutas corresponden a la estructura original |
| [INSTRUCCIONES_IMPORTACION.md](INSTRUCCIONES_IMPORTACION.md) | Importación futura mediante Import Package (Legacy), configuración y prueba real pendiente |
| [PROVENIENCIA.md](PROVENIENCIA.md) | Origen, commit de desarrollo, método reutilizado y correspondencia de rutas |
| [SHA256SUMS.txt](SHA256SUMS.txt) | Huellas de todos los archivos de revisión, salvo el propio listado |
| [src/construir.py](src/construir.py) | Generador original sin cambios |
| [src/definition.json](src/definition.json) | Definición original completa, con nombre de revisión |
| [src/requirements-validacion.txt](src/requirements-validacion.txt) | Dependencia del validador; el generador usa solo biblioteca estándar |
| [src/vendor/workflowdefinition.schema.json](src/vendor/workflowdefinition.schema.json) | Esquema WDL usado, sin modificaciones |
| [tests/validar.py](tests/validar.py) | Validador original sin cambios |
| [tests/expresiones.py](tests/expresiones.py) | Evaluador limitado original y casos sintéticos usados por el validador |
| [tests/ejecutar_revision.py](tests/ejecutar_revision.py) | Adaptador de rutas para ejecutar las pruebas originales desde esta carpeta |
| [evidencia/origen.json](evidencia/origen.json) | Hashes y enlaces de las referencias examinadas |
| [evidencia/equivalencia.json](evidencia/equivalencia.json) | Correspondencia y hashes de las 13 copias respecto al commit de desarrollo |
| [evidencia/validacion_original.json](evidencia/validacion_original.json) | Resultado histórico completo de la entrega anterior, preservado |
| [evidencia/validacion_revision.json](evidencia/validacion_revision.json) | Nueva ejecución, hashes de entradas y salida completa del validador |
| [evidencia/comprobaciones_publicacion.json](evidencia/comprobaciones_publicacion.json) | Estado de Git, integridad y comprobaciones de publicación |
| [evidencia/preflight_github.json](evidencia/preflight_github.json) | Respuestas resumidas de las consultas de automatizaciones del repositorio destino |
| [dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip](dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip) | ZIP exacto de la entrega ya informada |

**Regeneración y pruebas.** Desde la raíz del mismo repositorio:

```sh
cd revision_astra/p00_prueba_http
python src/construir.py --salida /tmp/caja-ayacucho-p00-regenerado
cmp dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip /tmp/caja-ayacucho-p00-regenerado/dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip
sha256sum -c SHA256SUMS.txt
python -B tests/ejecutar_revision.py
```

El generador conserva su salida original: bajo el directorio indicado crea `dist/`, `paquete/` y `flujo/CAJA_AYACUCHO_00_PRUEBA_HTTP_definition.json`. Debe ejecutarse con `--salida` como arriba para separar la reconstrucción de los archivos revisados. La comparación es binaria; no reemplaza el ZIP entregado. El adaptador verifica las copias y el informe histórico, prepara esas mismas rutas en un directorio temporal y ejecuta `pruebas/validar.py` sin modificarlo. También compara dos regeneraciones internas con el ZIP conservado.

Se comprobó con Python 3.12.14, zlib 1.3.2 y jsonschema 4.26.0. Para las pruebas se necesita `jsonschema==4.26.0`; si falta, instalar [requirements-validacion.txt](src/requirements-validacion.txt) en un entorno virtual fuera de esta carpeta. No se incluyen entornos virtuales ni paquetes instalados. Validar no requiere red: el esquema está incluido.

Sin referencias descargadas se ejecutan nueve grupos autocontenidos. Para repetir también el décimo grupo, disponer de las cinco referencias verificadas en las rutas de `evidencia/origen.json` y ejecutar desde esta carpeta:

```sh
python -B tests/ejecutar_revision.py --referencias /workspace/referencias-caja-ayacucho
```

La evidencia nueva se generó con el mismo comando, añadiendo `--informe evidencia/validacion_revision.json`. No usar ese argumento para reemplazar el informe histórico. Los casos sintéticos incluyen valores ficticios en dominios reservados `.example` y `.invalid`; no son destinos de pruebas operativos ni credenciales reales.

SHA-256 esperado del ZIP:

```text
7d8816b1bf874771b63faffd5a83e20c956ec7e195bb7392690c1aa121078a2d
```

**Valores pendientes:** entorno institucional de pruebas, propietario y permisos; capacidad Premium y DLP; URL HTTPS directa de pruebas con ruta exacta `/health`; contrato de respuesta; revisión técnica por Astra y autorización del usuario para importación y ejecución. Esta versión no envía autenticación. No configurar URLs productivas ni introducir secretos en la URL o el paquete.

**Límites:** las pruebas son estructurales y sintéticas. No se ha importado, guardado ni ejecutado el flujo en un tenant. Deben comprobarse el importador heredado, el diseñador, las expresiones, el bloqueo sin tráfico, los casos HTTP/red/timeout, la duración efectiva y el número de solicitudes en la futura API. La publicación no cambia ese estado.
