# CAJA AYACUCHO - 00 PRUEBA HTTP

Paquete preliminar de Power Automate para revisión técnica por Astra. El archivo importable es `dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip`. La entrega general de revisión contiene también fuentes, pruebas y documentación; ese ZIP general no se importa en Power Automate.

**Validación estática realizada. Importación y ejecución en el tenant pendientes.**

El flujo se inicia manualmente, comprueba su configuración y contiene una única acción HTTP `GET` a la ruta `/health`. La URL inicial es `https://pendiente-url-pruebas.invalid/health`; mientras permanezca el marcador, esté vacía o contenga `.invalid`, una terminación con `CONFIGURACION_PENDIENTE` precede a la acción HTTP. Se exige HTTPS y ruta exacta `/health`, sin credenciales, query ni fragmento.

La acción HTTP tiene `limit.timeout = PT30S`, política de reintentos `None` y `DisableAsyncPattern`. No incluye cuerpo, cabeceras de autenticación, documentos ni datos financieros. `RESULTADO` muestra el estado, un mensaje, código HTTP y hasta 1.000 caracteres del cuerpo recibido en el historial de ejecución. Los errores finalizan como `Failed`; un HTTP 2xx con acción satisfactoria finaliza como `Succeeded`.

El contrato es provisional: 2xx significa solamente respuesta HTTP satisfactoria, incluso 202 o 204; todavía no se evalúa un campo `ok`, salud funcional ni contenido JSON concreto. El responsable de la futura API debe confirmar el endpoint directo, su respuesta y que GET no modifica datos. La entrega no construye esa API.

| Archivo | Uso |
|---|---|
| `dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip` | Paquete de flujo para Import Package (Legacy) |
| `dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip.sha256` | Huella del paquete |
| `flujo/construir.py` | Generador autónomo con biblioteca estándar Python |
| `flujo/CAJA_AYACUCHO_00_PRUEBA_HTTP_definition.json` | Definición WDL legible |
| `paquete/` | Los cinco JSON exactos contenidos en el ZIP |
| `pruebas/` | Validación estructural y evaluación local limitada de expresiones |
| `evidencia/origen.json` | Commit, rutas, hashes y fuente del esquema WDL |
| `evidencia/validacion.json` | Resultados de las comprobaciones ejecutadas |
| `INFORME_VALIDACION.md` | Método, comandos, resultados y limitaciones |
| `INSTRUCCIONES_IMPORTACION.md` | Importación futura, valores pendientes y matriz de prueba |

Para regenerar, desde la raíz del repositorio:

```sh
python flujo/construir.py
python pruebas/validar.py
```

El generador no requiere paquetes externos ni red. El validador utiliza `jsonschema==4.26.0`; en un entorno que no lo tenga, instale `requirements-validacion.txt` en un entorno virtual. El esquema está incluido, por lo que validar no descarga nada.

La referencia obligatoria es `Lothbrok338/control-depositos-cbba`, rama `deploy/p10-api`, commit `456ca36efb3124e34295c911aff7833f6a7eacdb`. Se consultaron el ZIP V5, su generador y la definición, más los helpers WDL y las instrucciones de importación. El desarrollo está aislado en un repositorio local independiente, rama `caja-ayacucho/p00-prueba-http`, sin remotos ni workflows de despliegue. No se publicó una rama, no hubo merge y no se modificaron componentes de Control de Depósitos, Tiquipaya o América.

La compatibilidad arquitectónica se revisó contra los puntos TO-BE v0.3 incluidos en el encargo: Power Apps institucional como interfaz futura, Power Automate Premium como orquestador, API Python independiente en Railway, SharePoint como repositorio oficial y PostgreSQL únicamente para coordinación temporal y recuperación. El documento completo TO-BE v0.3 no fue aportado; la aprobación arquitectónica corresponde a Astra. Este paquete no implementa esas otras capas, reglas contables, Control 1, Control 3 ni auditorías institucionales. El alcance futuro sigue terminando en la publicación del GLOBAL mensual.

La importación y prueba real requieren revisión técnica por Astra y autorización posterior del usuario, tal como establece el encargo.
