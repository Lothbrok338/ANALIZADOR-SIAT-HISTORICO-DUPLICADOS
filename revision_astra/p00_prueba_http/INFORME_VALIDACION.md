# Informe de validación — 21 de octubre de 2026

**Validación estática realizada. Importación y ejecución en el tenant pendientes.**

Resultado final: **10 de 10 grupos de comprobaciones estáticas superados**, con 19 casos sintéticos de URL, 19 de clasificación de resultados y 9 mutaciones rechazadas por el validador. La evidencia ejecutable está en `evidencia/validacion.json`. No hay comprobaciones estáticas pendientes o fallidas en la versión entregada. Las pruebas reales descritas más abajo permanecen pendientes.

ZIP: `dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip`, 3.411 bytes, cinco archivos JSON, un recurso de flujo, cero conexiones y 16 acciones, de las cuales una es HTTP.

SHA-256:

```text
7d8816b1bf874771b63faffd5a83e20c956ec7e195bb7392690c1aa121078a2d
```

Referencia de origen: [commit 456ca36efb3124e34295c911aff7833f6a7eacdb](https://github.com/Lothbrok338/control-depositos-cbba/commit/456ca36efb3124e34295c911aff7833f6a7eacdb), rama `deploy/p10-api` de `Lothbrok338/control-depositos-cbba`. El acceso se comprobó mediante GitHub conectado. Todas las lecturas finales se fijaron al commit, no a una rama móvil. Se recalcularon SHA-256 y Git blob SHA-1 de las cinco referencias consultadas; coinciden con la evidencia de origen.

| Referencia | Inspección realizada |
|---|---|
| `P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_V5.zip` | CRC, cinco entradas, todos los JSON, manifiestos, mapas y envoltura |
| `p0/flujo/construir.py` | Funciones de empaquetado, UUIDv5, metadatos fijos y compresión |
| `p0/flujo/P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_definition.json` | Lectura completa y equivalencia exacta con la definición dentro del ZIP |
| `p9/wdl.py` | Parámetros WDL vacíos y patrones de acciones/runAfter utilizados por el generador de referencia |
| `p0/flujo/INSTRUCCIONES_IMPORTACION.md` | Identificación del procedimiento Import Package (Legacy) |

El desarrollo está en `/workspace/caja-ayacucho-p00`, repositorio local independiente, rama `caja-ayacucho/p00-prueba-http`. No tiene remotos. Las referencias descargadas están separadas, fuera de la entrega. No se ejecutó el generador original, no se escribió al repositorio de origen y no se publicó ninguna rama. No se verificaron todas las integraciones externas que podrían desplegar al publicar; por ello se mantuvo la entrega local conforme al encargo. No hubo despliegues, merge, importaciones ni activaciones.

**Método conservado y adaptaciones.** Se reutilizó el diseño de paquete heredado con `manifest.json`, `Microsoft.Flow/flows/manifest.json` y, bajo un UUID de recurso, `apisMap.json`, `connectionsMap.json` y `definition.json`. Se conservan la versión de esquema 1.0, la envoltura `Microsoft.Flow/flows`, los campos de manifiesto, dos identidades diferenciadas para recurso y definición, UUIDv5, fecha fija, orden de entradas, JSON UTF-8 compacto y ZIP DEFLATE. El nuevo generador es autónomo y no depende de módulos del proyecto de origen.

Se adaptaron el nombre, descripción, fecha e identidades a Caja Ayacucho. El namespace determinista es `caja-ayacucho:p00-prueba-http:v1`. Se sustituyeron el disparador y las acciones de negocio por un botón manual, guardas de configuración, HTTP GET y diagnóstico. Se eliminaron recursos, dependencias y referencias de conexiones: los dos mapas permanecen presentes pero vacíos. La lista de recursos contiene solamente el flujo con `dependsOn: []`. Los parámetros estándar `$authentication` y `$connections` conservan valores vacíos; no contienen credenciales.

El timeout se coloca en `HTTP_HEALTH.limit.timeout`, al nivel de la acción conforme a la documentación WDL; no se copia la ubicación bajo `inputs` del generador original. Se usa `PT30S`, sin reintentos ni sondeo asíncrono. Durante la comprobación inicial, el esquema publicado rechazó la grafía `retryPolicy.type = none`; se ajustó a su enumeración `None` y la validación final tiene cero errores. La aceptación del importador y del diseñador aún requiere el tenant.

**Comandos y resultados.** Entorno usado: Python 3.12.14, zlib 1.3.2 y jsonschema 4.26.0. Comandos desde `/workspace/caja-ayacucho-p00`:

```sh
python flujo/construir.py
python pruebas/validar.py --referencias /workspace/referencias-caja-ayacucho --informe evidencia/validacion.json
python -m zipfile -t dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip
sha256sum dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip
git diff --check
git remote -v
```

El validador ejecuta internamente el generador dos veces, en directorios temporales distintos, mediante `python flujo/construir.py --salida <directorio>`. Compara byte a byte el ZIP, los cinco auxiliares y la definición legible con la entrega. Ambas reconstrucciones coinciden. También verifica la huella declarada. La reproducción binaria se comprobó con las versiones indicadas; otras versiones de zlib pueden producir diferencias de compresión.

En una copia sin las referencias descargadas, `python pruebas/validar.py` ejecuta los nueve grupos autocontenidos. Para repetir el décimo, descargar las cinco rutas indicadas en `evidencia/origen.json` exactamente del commit registrado, respetar su estructura y pasar ese directorio mediante `--referencias`. Los hashes impiden aceptar referencias diferentes. Los comandos de validación no acceden a red ni importan flujos.

| Grupo | Resultado y alcance |
|---|---|
| Integridad y JSON | PASS: CRC, cinco entradas únicas, rutas seguras, JSON estricto sin claves duplicadas |
| Manifiestos e identidad | PASS: assetPaths y recurso coherentes, identidad interna y UUIDv5 propios, nombre exacto en tres ubicaciones |
| Dependencias y destinos | PASS: mapas vacíos, cero conexiones, ningún ID heredado; únicos literales URL: marcador y esquema WDL |
| Auxiliares | PASS: definición y cinco archivos coinciden con el ZIP; lectura de todos los JSON de la entrega |
| Grafo y guardas | PASS: dependencias existentes, sin ciclos, referencias de expresiones resueltas; bloqueo previo domina la acción HTTP |
| Configuración HTTP | PASS: una acción GET, sin cuerpo ni autenticación, timeout limitado, política None y DisableAsyncPattern |
| Expresiones sintéticas | PASS: 19 URLs y 19 resultados; mensajes y clasificación evaluados con un intérprete local limitado |
| Sensibilidad | PASS: nueve alteraciones rechazadas, incluyendo bypass del bloqueo, POST, cuerpo, reintentos y falta de timeout |
| Esquema WDL | PASS: cero errores frente a la copia del esquema publicado por Microsoft cuyo hash se conserva |
| Regeneración y origen | PASS: dos reconstrucciones idénticas, SHA-256 correcto, referencias y estructura contrastadas |

La tabla resume áreas; `evidencia/validacion.json` contiene los diez grupos exactos del ejecutable. La revisión de valores literales, la lista permitida de URLs y los patrones de secretos no encontraron credenciales, conexiones personales, destinos productivos ni identidades de entorno. Los UUID originales se compararon únicamente con la referencia separada y no aparecen en el nuevo ZIP. Las referencias de trazabilidad al repositorio original se conservan en la documentación, no como dependencias operativas.

**Límites de la evidencia.** El esquema WDL público es de la familia Logic Apps: no es un esquema del importador heredado y no certifica compatibilidad completa de Power Automate. El evaluador local comprueba solamente el subconjunto de funciones utilizado; no es el motor Microsoft y su parseo de URI no sustituye al del tenant. Las guardas y runAfter se inspeccionan estructuralmente. No se ha demostrado comportamiento real mediante estas pruebas.

Quedan pendientes: importación como flujo nuevo, guardado y Flow Checker; aceptación de mapas vacíos, botón manual, expresiones y configuración HTTP; licencia Premium y DLP; error de marcador sin tráfico; respuestas 2xx/4xx/5xx; DNS/TLS y timeout; visibilidad del resultado y estado final. Se debe medir la duración efectiva de `PT30S` y comprobar el número de solicitudes en registros del servidor, incluidos 202 y 429. Una cancelación manual o un fallo del propio motor puede impedir el diagnóstico final. Algunos fallos de infraestructura pueden aparecer como HTTP 502/504: se clasifican por el código observado y se investigan en el historial.

El endpoint, ausencia de redirecciones y semántica del cuerpo aún deben acordarse. El flujo conserva el marcador y no prueba ninguna API. La compatibilidad TO-BE v0.3 se limita a los puntos del encargo; no se examinó un documento TO-BE completo adicional. La entrega queda pendiente de revisión técnica por Astra y de autorización del usuario para la importación y prueba real.

Fuentes técnicas complementarias: [esquema WDL](https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json), [acciones y timeout](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-actions-triggers), [patrón HTTP asíncrono](https://learn.microsoft.com/en-us/azure/connectors/connectors-native-http), [botón manual en definiciones de cloud flows](https://learn.microsoft.com/en-us/power-automate/manage-flows-with-code) e [importación heredada](https://learn.microsoft.com/en-us/power-automate/export-import-flow-non-solution).
