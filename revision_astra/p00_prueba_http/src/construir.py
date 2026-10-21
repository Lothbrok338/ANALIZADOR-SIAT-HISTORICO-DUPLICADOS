"""Genera un paquete de flujo heredado, autocontenido y reproducible.

Referencia de empaquetado: p0/flujo/construir.py del commit indicado en
evidencia/origen.json. No importa ni ejecuta código del repositorio de origen.
Uso: python flujo/construir.py [--salida DIRECTORIO]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import uuid
import zipfile

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE = "CAJA AYACUCHO - 00 PRUEBA HTTP"
ARCHIVO = "CAJA_AYACUCHO_00_PRUEBA_HTTP"
MARCADOR = "https://pendiente-url-pruebas.invalid/health"
FECHA_ZIP = (2026, 10, 21, 0, 0, 0)
FECHA_PAQUETE = "2026-10-21T00:00:00Z"
ESQUEMA = "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#"


def identidad(parte):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"caja-ayacucho:p00-prueba-http:v1:{parte}"))


def compose(valor, despues=None):
    return {"type": "Compose", "inputs": valor, "runAfter": despues or {}}


def terminar(codigo, mensaje):
    return {"type": "Terminate", "inputs": {"runStatus": "Failed", "runError": {
        "code": codigo, "message": mensaje}}, "runAfter": {}}


def condicion(expresion, si, no=None, despues=None):
    return {"type": "If", "expression": expresion, "actions": si,
            "else": {"actions": no or {}}, "runAfter": despues or {}}


def construir_definicion():
    url = "outputs('URL_NORMALIZADA')"
    partes = "outputs('PARTES_URL')"
    diag = "outputs('DIAGNOSTICO_HTTP')"
    estado = f"{diag}?['estado_accion']"
    codigo = f"{diag}?['codigo_http']"
    error = f"toLower({diag}?['codigo_error'])"
    # El orden distingue respuestas HTTP (incluidos 408/504) de un timeout local.
    clasificacion = (
        f"@if(and(greaterOrEquals({codigo},100),not(and(greaterOrEquals({codigo},200),less({codigo},300)))),"
        "'ERROR_HTTP',"
        f"if(and(equals({estado},'Succeeded'),greaterOrEquals({codigo},200),less({codigo},300)),"
        "'RESPUESTA_SATISFACTORIA',"
        f"if(or(equals({estado},'TimedOut'),contains({error},'timeout'),contains({error},'timedout')),"
        f"'TIMEOUT',if(equals({codigo},0),'FALLO_CONEXION','ERROR_TECNICO'))))"
    )
    mensaje = (
        "@if(equals(outputs('ESTADO_RESULTADO'),'RESPUESTA_SATISFACTORIA'),"
        "'GET /health respondió con HTTP 2xx. La semántica del cuerpo sigue pendiente de confirmar.',"
        "if(equals(outputs('ESTADO_RESULTADO'),'ERROR_HTTP'),"
        f"concat('GET /health devolvió HTTP ',string({codigo}),'. Revise la API de pruebas; no se reintentó.'),"
        "if(equals(outputs('ESTADO_RESULTADO'),'TIMEOUT'),"
        "'La petición agotó el tiempo de espera. Revise disponibilidad y latencia de la API de pruebas.',"
        "if(equals(outputs('ESTADO_RESULTADO'),'FALLO_CONEXION'),"
        "'No se obtuvo una respuesta HTTP. Revise URL, DNS, TLS, conectividad y políticas del entorno.',"
        "'La acción HTTP falló pese a tener un código 2xx. Revise el detalle técnico en su historial.'))))"
    )
    acciones = {
        "PARAM_URL_PRUEBAS": compose(MARCADOR),
        "URL_NORMALIZADA": compose("@trim(string(outputs('PARAM_URL_PRUEBAS')))",
                                   {"PARAM_URL_PRUEBAS": ["Succeeded"]}),
        "BLOQUEAR_CONFIGURACION_PENDIENTE": condicion(
            f"@or(empty({url}),contains(toLower({url}),'pendiente-url-pruebas'),contains(toLower({url}),'.invalid'))",
            {"DETENER_CONFIGURACION_PENDIENTE": terminar(
                "CONFIGURACION_PENDIENTE",
                "Configure PARAM_URL_PRUEBAS con la URL HTTPS completa de pruebas terminada en /health. No se envió ninguna petición HTTP.")},
            despues={"URL_NORMALIZADA": ["Succeeded"]}),
        "PARSEAR_URL": {"type": "Scope", "actions": {
            "PARTES_URL": compose({"esquema": f"@uriScheme({url})", "host": f"@uriHost({url})",
                                   "ruta": f"@uriPath({url})", "consulta": f"@uriQuery({url})"})},
            "runAfter": {"BLOQUEAR_CONFIGURACION_PENDIENTE": ["Succeeded"]}},
        "DETENER_URL_NO_INTERPRETABLE": {
            **terminar("CONFIGURACION_INVALIDA", "La URL no se puede interpretar. Use una URL HTTPS de pruebas terminada en /health, sin credenciales ni parámetros."),
            "runAfter": {"PARSEAR_URL": ["Failed", "TimedOut"]}},
        "VALIDAR_URL": condicion(
            f"@and(equals(toLower({partes}?['esquema']),'https'),not(empty({partes}?['host'])),"
            f"equals({partes}?['ruta'],'/health'),empty({partes}?['consulta']),"
            f"not(contains({url},'@')),not(contains({url},'#')),not(contains({url},'?')),"
            f"not(contains({url},' ')),not(contains({url},decodeUriComponent('%5C'))),"
            f"not(contains({url},decodeUriComponent('%0A'))),not(contains({url},decodeUriComponent('%0D'))),"
            f"not(contains({url},decodeUriComponent('%09'))))",
            {},
            {"DETENER_CONFIGURACION_INVALIDA": terminar(
                "CONFIGURACION_INVALIDA",
                "Use una URL HTTPS de pruebas con ruta exacta /health, sin usuario, contraseña, query, fragmento ni espacios. No se envió ninguna petición HTTP.")},
            {"PARSEAR_URL": ["Succeeded"]}),
        "HTTP_HEALTH": {
            "type": "Http",
            "inputs": {"method": "GET", "uri": f"@{url}", "retryPolicy": {"type": "None"}},
            # WDL sitúa limit al nivel de la acción, fuera de inputs.
            "limit": {"timeout": "PT30S"},
            "operationOptions": "DisableAsyncPattern",
            "runAfter": {"VALIDAR_URL": ["Succeeded"]}},
        "DIAGNOSTICO_HTTP": compose({
            "estado_accion": "@actions('HTTP_HEALTH')?['status']",
            "codigo_http": "@int(coalesce(actions('HTTP_HEALTH')?['outputs']?['statusCode'],0))",
            "codigo_error": "@string(coalesce(actions('HTTP_HEALTH')?['error']?['code'],''))",
            "cuerpo_respuesta": "@take(string(coalesce(actions('HTTP_HEALTH')?['outputs']?['body'],'')),1000)"
        }, {"HTTP_HEALTH": ["Succeeded", "Failed", "TimedOut"]}),
        "ESTADO_RESULTADO": compose(clasificacion, {"DIAGNOSTICO_HTTP": ["Succeeded"]}),
        "RESULTADO": compose({
            "estado": "@outputs('ESTADO_RESULTADO')", "mensaje": mensaje,
            "codigo_http": f"@{codigo}", "estado_accion": f"@{estado}",
            "codigo_error": f"@{diag}?['codigo_error']",
            "cuerpo_respuesta_hasta_1000_caracteres": f"@{diag}?['cuerpo_respuesta']"
        }, {"ESTADO_RESULTADO": ["Succeeded"]}),
        "FINALIZAR": condicion("@equals(outputs('ESTADO_RESULTADO'),'RESPUESTA_SATISFACTORIA')",
            {"TERMINAR_OK": {"type": "Terminate", "inputs": {"runStatus": "Succeeded"}, "runAfter": {}}},
            {"TERMINAR_ERROR": terminar("@outputs('ESTADO_RESULTADO')", "@outputs('RESULTADO')?['mensaje']")},
            {"RESULTADO": ["Succeeded"]})
    }
    return {
        "$schema": ESQUEMA, "contentVersion": "1.0.0.0",
        "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                       "$connections": {"defaultValue": {}, "type": "Object"}},
        "triggers": {"manual": {"type": "Request", "kind": "Button", "inputs": {
            "schema": {"type": "object", "properties": {}, "required": []}}}},
        "actions": acciones, "outputs": {}
    }


def archivos_paquete(definicion):
    recurso, interno = identidad("resource"), identidad("definition")
    base = f"Microsoft.Flow/flows/{recurso}"
    envoltura = {
        "name": interno, "id": f"/providers/Microsoft.Flow/flows/{interno}", "type": "Microsoft.Flow/flows",
        "properties": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
                       "displayName": NOMBRE, "definition": definicion, "connectionReferences": {},
                       "flowFailureAlertSubscribed": False, "isManaged": False}}
    return {
        "manifest.json": {"schema": "1.0", "details": {
            "displayName": NOMBRE,
            "description": "Prueba técnica manual GET /health a una futura API de pruebas. URL pendiente; sin datos de negocio.",
            "createdTime": FECHA_PAQUETE, "packageTelemetryId": identidad("telemetry"),
            "creator": "N/A", "sourceEnvironment": ""},
            "resources": {recurso: {"type": "Microsoft.Flow/flows", "suggestedCreationType": "New",
                "creationType": "New, Update", "details": {"displayName": NOMBRE}, "configurableBy": "User",
                "hierarchy": "Root", "dependsOn": []}}},
        "Microsoft.Flow/flows/manifest.json": {"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [recurso]}},
        f"{base}/apisMap.json": {}, f"{base}/connectionsMap.json": {},
        f"{base}/definition.json": envoltura
    }


def json_bytes(valor):
    return json.dumps(valor, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def zip_bytes(archivos):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for ruta, contenido in archivos.items():
            info = zipfile.ZipInfo(ruta, date_time=FECHA_ZIP)
            info.create_system, info.compress_type, info.external_attr = 3, zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(info, json_bytes(contenido))
    return buffer.getvalue()


def generar(salida):
    definicion = construir_definicion()
    archivos = archivos_paquete(definicion)
    (salida / "flujo").mkdir(parents=True, exist_ok=True)
    (salida / "dist").mkdir(parents=True, exist_ok=True)
    (salida / "flujo" / f"{ARCHIVO}_definition.json").write_text(
        json.dumps(definicion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for ruta, valor in archivos.items():
        destino = salida / "paquete" / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(json_bytes(valor))
    destino = salida / "dist" / f"{ARCHIVO}.zip"
    destino.write_bytes(zip_bytes(archivos))
    huella = hashlib.sha256(destino.read_bytes()).hexdigest()
    destino.with_suffix(".zip.sha256").write_text(f"{huella}  {destino.name}\n", encoding="utf-8")
    return destino, huella


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=RAIZ)
    args = parser.parse_args()
    ruta, huella = generar(args.salida.resolve())
    print(ruta)
    print("SHA-256:", huella)
