# Proveniencia de la copia de revisión

Repositorio de referencia: `Lothbrok338/control-depositos-cbba`. Rama de referencia: `deploy/p10-api`. Commit utilizado: [`456ca36efb3124e34295c911aff7833f6a7eacdb`](https://github.com/Lothbrok338/control-depositos-cbba/commit/456ca36efb3124e34295c911aff7833f6a7eacdb). El acceso se comprobó y las lecturas finales se fijaron a ese commit.

Las tres referencias obligatorias examinadas fueron:

- [P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_V5.zip](https://github.com/Lothbrok338/control-depositos-cbba/blob/456ca36efb3124e34295c911aff7833f6a7eacdb/P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_V5.zip).
- [p0/flujo/construir.py](https://github.com/Lothbrok338/control-depositos-cbba/blob/456ca36efb3124e34295c911aff7833f6a7eacdb/p0/flujo/construir.py).
- [p0/flujo/P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_definition.json](https://github.com/Lothbrok338/control-depositos-cbba/blob/456ca36efb3124e34295c911aff7833f6a7eacdb/p0/flujo/P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_definition.json).

También se consultaron `p9/wdl.py` y `p0/flujo/INSTRUCCIONES_IMPORTACION.md` de ese mismo commit. [origen.json](evidencia/origen.json) contiene los SHA-256 y Git blob SHA-1. Las referencias operativas originales no se copian a esta carpeta.

El commit de desarrollo que produjo la entrega es **`06232da9f7602b92696c1c4be57dbe25be04efec`**, del repositorio local independiente `/workspace/caja-ayacucho-p00`, rama **`caja-ayacucho/p00-prueba-http`**. El commit de desarrollo es anterior al de organización/publicación de esta copia. Al iniciar la preparación de publicación no había remotos configurados; el nombre del repositorio de referencia no establece por sí mismo un destino de escritura.

El usuario confirmó posteriormente [Lothbrok338/ANALIZADOR-SIAT-HISTORICO-DUPLICADOS](https://github.com/Lothbrok338/ANALIZADOR-SIAT-HISTORICO-DUPLICADOS) como destino y autorizó reutilizarlo para Caja Ayacucho. Se configuró ese repositorio como remoto `origin` de lectura y escritura del mismo repositorio local, conservando la rama existente. El estado de las comprobaciones previas se registra en [comprobaciones_publicacion.json](evidencia/comprobaciones_publicacion.json). Los informes históricos se mantienen intactos y describen el estado anterior, cuando todavía no existía remoto.

Tras el error 403 al consultar webhooks, el usuario autorizó expresamente el commit y push a `caja-ayacucho/p00-prueba-http`, aceptando la incertidumbre sobre automatizaciones externas. No se afirma haber descartado esos webhooks. La autorización excluye comandos de despliegue, cambios de integraciones y merges.

SHA-256 del paquete original y de esta copia:

```text
7d8816b1bf874771b63faffd5a83e20c956ec7e195bb7392690c1aa121078a2d
```

Se reutilizó el método de paquete de flujo heredado: manifiesto raíz, manifiesto bajo `Microsoft.Flow/flows/` y directorio del recurso con `apisMap.json`, `connectionsMap.json` y `definition.json`. Se conservaron versión 1.0, envoltura `Microsoft.Flow/flows`, UUIDv5 separados para recurso y definición, JSON UTF-8 compacto, orden y fecha fijos de entradas y compresión ZIP DEFLATE.

En el desarrollo original se adaptaron nombre, identidad y metadatos a Caja Ayacucho; se sustituyeron disparador y acciones de negocio por un botón manual, comprobaciones de URL, GET `/health` y diagnóstico. Se eliminaron OneDrive, conexiones y dependencias; los mapas permanecen vacíos. Se configuraron timeout `PT30S` al nivel de la acción, política de reintentos `None` y `DisableAsyncPattern`. Esas adaptaciones pertenecen al commit de desarrollo indicado y no se modifican para publicar.

Esta organización añade únicamente documentación de navegación, huellas, evidencia nueva y un adaptador de rutas. [equivalencia.json](evidencia/equivalencia.json) registra 13 archivos copiados byte a byte desde `git show 06232da9f7602b92696c1c4be57dbe25be04efec:<ruta>`:

| Ruta original | Ruta de revisión |
|---|---|
| `flujo/construir.py` | [src/construir.py](src/construir.py) |
| `flujo/CAJA_AYACUCHO_00_PRUEBA_HTTP_definition.json` | [src/definition.json](src/definition.json) |
| `pruebas/validar.py` y `pruebas/expresiones.py` | [tests/validar.py](tests/validar.py) y [tests/expresiones.py](tests/expresiones.py) |
| `vendor/` y `requirements-validacion.txt` | `src/vendor/` y [src/requirements-validacion.txt](src/requirements-validacion.txt) |
| `evidencia/origen.json` | [evidencia/origen.json](evidencia/origen.json) |
| `evidencia/validacion.json` | [evidencia/validacion_original.json](evidencia/validacion_original.json) |
| Informes e instrucciones originales | Mismos nombres en esta carpeta |
| ZIP y archivo `.zip.sha256` | Mismos nombres bajo [dist/](dist/) |

El informe histórico mantiene sus rutas y fecha originales. La nueva [validacion_revision.json](evidencia/validacion_revision.json) identifica las mismas entradas por sus hashes, la versión del adaptador y los resultados completos de la ejecución desde la carpeta revisable. Una nueva fecha o el número de JSON del directorio temporal no modifica el flujo ni sustituye la evidencia histórica.

**Validación estática realizada. Importación y ejecución en el tenant pendientes.** La publicación en GitHub facilita la revisión; no equivale a aprobación técnica ni a validación en Power Automate.
