# Importación y configuración pendientes

**Validación estática realizada. Importación y ejecución en el tenant pendientes.** Estas instrucciones se ejecutarán después de la revisión técnica de Astra y de la autorización del usuario. No se ha accedido a un tenant durante esta entrega.

1. En el entorno institucional de pruebas autorizado, abrir Power Automate → **My flows / Mis flujos** → **Import** → **Import Package (Legacy)**. Se necesita un usuario con permiso para importar y capacidad Premium para ejecutar HTTP.
2. Cargar **únicamente** `dist/CAJA_AYACUCHO_00_PRUEBA_HTTP.zip`. Es un paquete de flujo heredado: no usar el importador de soluciones de Power Platform ni cargar el ZIP general de revisión.
3. En **Import setup**, elegir **Create as new / Crear como nuevo**. Confirmar el nombre exacto `CAJA AYACUCHO - 00 PRUEBA HTTP`. No seleccionar actualización de un flujo existente. El manifiesto conserva el campo estándar `New, Update` del método de referencia y sugiere `New`.
4. El paquete no declara conexiones ni otros recursos. No debe solicitar OneDrive, SharePoint o conexiones personales. Si aparecen esas dependencias, detenerse y revisar el archivo seleccionado.
5. Importar y abrir el diseñador. Comprobar el disparador manual, la ausencia de errores de Flow Checker y la conservación del marcador en `PARAM_URL_PRUEBAS`. Confirmar el estado del flujo tras importar; no activar ni ejecutar fuera de la prueba autorizada.
6. En **HTTP_HEALTH**, comprobar método GET, URI tomada de `URL_NORMALIZADA`, timeout `PT30S`, Retry policy **None** y Asynchronous pattern **Off**. La definición no configura paginación, bucles ni autenticación. Verificar cómo el tenant refleja estas propiedades antes de probar.
7. En la prueba autorizada, conservar primero el marcador y ejecutar manualmente. El resultado esperado es `Failed / CONFIGURACION_PENDIENTE` y ninguna invocación de `HTTP_HEALTH`. Registrar evidencia del historial y, cuando exista la API, contrastar sus registros.
8. Una vez confirmada la futura URL, editar solamente **Inputs** de `PARAM_URL_PRUEBAS` y escribir la URL HTTPS completa terminada en `/health`, sin barra final, credenciales, query ni fragmento. Debe ser el destino de pruebas directo, sin redirecciones. Guardar y volver a revisar el flujo.
9. Ejecutar manualmente una vez dentro de la autorización. Abrir **RESULTADO → Outputs** en el historial. No se crea una pantalla de Power Apps ni se envía correo. En fallos de configuración anteriores a HTTP, el código y mensaje aparecen en la acción de terminación correspondiente.

| Valor pendiente | Qué debe confirmarse |
|---|---|
| Entorno institucional de pruebas | Tenant y entorno de destino, propietario institucional, permiso de importación, Premium y políticas DLP |
| URL completa de pruebas | Origen HTTPS autorizado y ruta `/health`; no se proporciona una URL operativa en la entrega |
| Contrato de salud | Método GET inocuo, endpoint directo, códigos esperados, formato y semántica del cuerpo; 2xx es el criterio provisional |
| Acceso al endpoint | Esta versión no envía autenticación. Si la futura API la exige, se necesita una revisión específica; no pegar secretos en el ZIP o en la URL |
| Parámetros efectivos del motor | Aceptación y efecto de `PT30S`, política sin reintentos y patrón asíncrono desactivado |
| Autorización | Revisión de Astra y autorización del usuario para importar y ejecutar |

La guarda valida formato y marcador; no puede decidir si una URL introducida posteriormente pertenece a producción. Esa selección debe confirmarse antes de sustituir el marcador.

Matriz para la prueba real futura, con respuestas técnicas controladas y sin datos financieros:

| Caso | Resultado esperado y evidencia |
|---|---|
| Marcador, vacío o `.invalid` | `CONFIGURACION_PENDIENTE`, HTTP no invocada |
| URL mal formada o ruta distinta | `CONFIGURACION_INVALIDA`, HTTP no invocada |
| HTTP 200 / 204 | `RESPUESTA_SATISFACTORIA`, `Succeeded`, salida visible en RESULTADO |
| HTTP 202 con Location | Una invocación sin sondeo posterior; el criterio provisional acepta 2xx |
| HTTP 400 / 401 / 403 / 404 / 429 / 500 | `ERROR_HTTP`, código conservado, `Failed`, sin reintento |
| HTTP 408 / 504 recibido | `ERROR_HTTP`; se distingue del timeout local por existir un código HTTP |
| DNS, TLS o conexión fallida sin código HTTP | `FALLO_CONEXION`, `Failed`, mensaje comprensible |
| Espera agotada sin respuesta HTTP | `TIMEOUT`, `Failed`; medir duración efectiva y comprobar que el diagnóstico se ejecuta |
| Acción fallida con código 2xx | `ERROR_TECNICO`, para no presentar una respuesta inválida como éxito |

El contrato definitivo debe impedir redirecciones. El número de solicitudes reales se comprobará con registros de la API, especialmente en 202, 429 y errores. No se han ejecutado estas pruebas ni se ha construido un servidor para ellas.

Método confirmado en las instrucciones del repositorio de referencia y en [Microsoft: importar un flujo que no pertenece a una solución](https://learn.microsoft.com/en-us/power-automate/export-import-flow-non-solution).
