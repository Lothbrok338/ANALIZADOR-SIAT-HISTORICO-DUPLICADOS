"""Validación estática del ZIP y casos sintéticos de sus expresiones.

No importa flujos, no llama APIs y no simula el motor completo de Power Automate.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid
import zipfile
from zoneinfo import ZoneInfo

from jsonschema import validators
from expresiones import evaluar, evaluar_objeto

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE = "CAJA AYACUCHO - 00 PRUEBA HTTP"
ARCHIVO = "CAJA_AYACUCHO_00_PRUEBA_HTTP"
MARCADOR = "https://pendiente-url-pruebas.invalid/health"
SCHEMA = "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#"
UUID = re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.I)


def exigir(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)


def no_duplicados(pares):
    resultado = {}
    for k, v in pares:
        exigir(k not in resultado, f"Clave JSON duplicada: {k}")
        resultado[k] = v
    return resultado


def json_estricto(contenido):
    return json.loads(contenido, object_pairs_hook=no_duplicados,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"Constante no JSON: {x}")))


def recorrer(acciones):
    for nombre, accion in acciones.items():
        yield nombre, accion
        yield from recorrer(accion.get("actions", {}))
        yield from recorrer(accion.get("else", {}).get("actions", {}))


def comprobar_grafo(definicion):
    todos = dict(recorrer(definicion["actions"]))
    exigir(len(todos) == len(list(recorrer(definicion["actions"]))), "Nombres de acción duplicados")
    permitidos = {"Compose", "Scope", "If", "Http", "Terminate"}

    def nivel(acciones):
        for nombre, accion in acciones.items():
            exigir(accion["type"] in permitidos, f"Acción fuera de alcance: {nombre}")
            exigir(len(nombre) <= 80, "Nombre demasiado largo")
            for dependencia, estados in accion["runAfter"].items():
                exigir(dependencia in acciones and dependencia != nombre, "runAfter fuera del mismo nivel")
                exigir(bool(estados) and set(estados) <= {"Succeeded", "Failed", "TimedOut", "Skipped"}, "Estados no permitidos")
            nivel(accion.get("actions", {}))
            nivel(accion.get("else", {}).get("actions", {}))
        visitados, pendientes = set(), set()

        def visita(n):
            exigir(n not in pendientes, "Ciclo de dependencias")
            if n in visitados:
                return
            pendientes.add(n)
            for dependencia in acciones[n]["runAfter"]:
                visita(dependencia)
            pendientes.remove(n)
            visitados.add(n)
        for nombre in acciones:
            visita(nombre)
    nivel(definicion["actions"])
    for ref in re.findall(r"(?:outputs|actions|body)\('([^']+)'\)", json.dumps(definicion)):
        exigir(ref in todos, f"Referencia de expresión inexistente: {ref}")


def comprobar_flujo(d):
    exigir(d["$schema"] == SCHEMA, "Esquema inesperado")
    exigir(d["triggers"] == {"manual": {"type": "Request", "kind": "Button", "inputs": {
        "schema": {"type": "object", "properties": {}, "required": []}}}}, "Disparador no manual o recibe datos")
    exigir(d["parameters"] == {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                                  "$connections": {"defaultValue": {}, "type": "Object"}}, "Parámetros heredados")
    comprobar_grafo(d)
    a = d["actions"]
    exigir(set(a) == {"PARAM_URL_PRUEBAS", "URL_NORMALIZADA", "BLOQUEAR_CONFIGURACION_PENDIENTE",
        "PARSEAR_URL", "DETENER_URL_NO_INTERPRETABLE", "VALIDAR_URL", "HTTP_HEALTH", "DIAGNOSTICO_HTTP",
        "ESTADO_RESULTADO", "RESULTADO", "FINALIZAR"}, "Acciones raíz inesperadas")
    exigir(a["PARAM_URL_PRUEBAS"]["inputs"] == MARCADOR, "El entregable debe conservar el marcador")
    exigir(a["PARAM_URL_PRUEBAS"]["runAfter"] == {}, "Inicio inesperado")
    cadena = ["PARAM_URL_PRUEBAS", "URL_NORMALIZADA", "BLOQUEAR_CONFIGURACION_PENDIENTE",
              "PARSEAR_URL", "VALIDAR_URL", "HTTP_HEALTH"]
    for previo, siguiente in zip(cadena, cadena[1:]):
        exigir(a[siguiente]["runAfter"] == {previo: ["Succeeded"]}, "HTTP puede evitar las guardas")
    guardia = a["BLOQUEAR_CONFIGURACION_PENDIENTE"]
    exigir(guardia["else"]["actions"] == {}, "Rama pendiente inesperada")
    bloqueo = list(guardia["actions"].values())
    exigir(len(bloqueo) == 1 and bloqueo[0]["type"] == "Terminate" and bloqueo[0]["runAfter"] == {}, "Bloqueo no incondicional")
    exigir(bloqueo[0]["inputs"]["runStatus"] == "Failed" and bloqueo[0]["inputs"]["runError"]["code"] == "CONFIGURACION_PENDIENTE", "Error de configuración pendiente ausente")
    invalida = a["VALIDAR_URL"]
    exigir(invalida["actions"] == {}, "Rama válida inesperada")
    rechazo = list(invalida["else"]["actions"].values())
    exigir(len(rechazo) == 1 and rechazo[0]["type"] == "Terminate" and rechazo[0]["inputs"]["runError"]["code"] == "CONFIGURACION_INVALIDA", "URL inválida no se bloquea")
    exigir(a["DETENER_URL_NO_INTERPRETABLE"]["runAfter"] == {"PARSEAR_URL": ["Failed", "TimedOut"]}, "Parseo de URL sin captura")
    http = [(n, v) for n, v in recorrer(a) if v["type"] == "Http"]
    exigir(len(http) == 1 and http[0][0] == "HTTP_HEALTH", "Debe existir una sola acción HTTP")
    h = http[0][1]
    exigir(h["inputs"] == {"method": "GET", "uri": "@outputs('URL_NORMALIZADA')", "retryPolicy": {"type": "None"}}, "HTTP contiene datos, autenticación o reintentos")
    exigir(h["limit"] == {"timeout": "PT30S"} and "limit" not in h["inputs"], "Timeout incorrecto")
    exigir(h["operationOptions"] == "DisableAsyncPattern", "Sondeo HTTP no deshabilitado")
    exigir(set(h) == {"type", "inputs", "limit", "operationOptions", "runAfter"}, "Opciones HTTP no previstas")
    exigir(a["DIAGNOSTICO_HTTP"]["runAfter"] == {"HTTP_HEALTH": ["Succeeded", "Failed", "TimedOut"]}, "Captura de resultados incompleta")
    for previo, siguiente in [("DIAGNOSTICO_HTTP", "ESTADO_RESULTADO"), ("ESTADO_RESULTADO", "RESULTADO"), ("RESULTADO", "FINALIZAR")]:
        exigir(a[siguiente]["runAfter"] == {previo: ["Succeeded"]}, "Diagnóstico no secuencial")
    fin = a["FINALIZAR"]
    exigir(fin["actions"]["TERMINAR_OK"]["inputs"] == {"runStatus": "Succeeded"}, "Final satisfactorio incorrecto")
    exigir(fin["else"]["actions"]["TERMINAR_ERROR"]["inputs"] == {
        "runStatus": "Failed", "runError": {"code": "@outputs('ESTADO_RESULTADO')", "message": "@outputs('RESULTADO')?['mensaje']"}}, "Error no visible")


def comprobar_identidad(docs):
    m = docs["manifest.json"]
    exigir(m["schema"] == "1.0" and m["details"]["displayName"] == NOMBRE, "Nombre o esquema incorrecto")
    exigir(m["details"]["sourceEnvironment"] == "" and m["details"]["creator"] == "N/A", "Datos del entorno de origen")
    exigir(len(m["resources"]) == 1, "Recursos ajenos al flujo")
    recurso = next(iter(m["resources"]))
    r = m["resources"][recurso]
    exigir(r == {"type": "Microsoft.Flow/flows", "suggestedCreationType": "New", "creationType": "New, Update",
        "details": {"displayName": NOMBRE}, "configurableBy": "User", "hierarchy": "Root", "dependsOn": []}, "Manifiesto de recurso incorrecto")
    exigir(docs["Microsoft.Flow/flows/manifest.json"] == {"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [recurso]}}, "assetPaths no coincide")
    base = f"Microsoft.Flow/flows/{recurso}"
    exigir(set(docs) == {"manifest.json", "Microsoft.Flow/flows/manifest.json", f"{base}/apisMap.json",
                          f"{base}/connectionsMap.json", f"{base}/definition.json"}, "Estructura del ZIP inesperada")
    exigir(docs[f"{base}/apisMap.json"] == docs[f"{base}/connectionsMap.json"] == {}, "Mapas de conexiones heredados")
    w = docs[f"{base}/definition.json"]
    exigir(w["id"] == f"/providers/Microsoft.Flow/flows/{w['name']}" and w["type"] == "Microsoft.Flow/flows", "Identificador interno incoherente")
    p = w["properties"]
    exigir(p["displayName"] == NOMBRE and p["connectionReferences"] == {}, "Nombre o conexiones de la definición")
    exigir(p["apiId"] == "/providers/Microsoft.PowerApps/apis/shared_logicflows" and not p["isManaged"] and not p["flowFailureAlertSubscribed"], "Envoltura incorrecta")
    propios = {recurso, w["name"], m["details"]["packageTelemetryId"]}
    exigir(len(propios) == 3 and all(uuid.UUID(i).version == 5 for i in propios), "Identidades nuevas incorrectas")
    serializado = json.dumps(docs, ensure_ascii=False)
    exigir(set(UUID.findall(serializado)) == propios, "Identificadores adicionales")
    urls = set(re.findall(r'https?://[^"\s]+', serializado))
    exigir(urls == {MARCADOR, SCHEMA}, "URL adicional o destino no permitido")
    exigir(not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", serializado), "Dirección personal encontrada")
    for patron in [r"(?i)bearer\s+", r"gh[pousr]_[A-Za-z0-9]+", r"AKIA[0-9A-Z]{16}", r"-----BEGIN .*PRIVATE KEY", r"(?i)shared_onedrive|shared_sharepoint|CONTROL_DEPOSITOS|TIQUIPAYA|AMERICA|railway\.app", r'(?i)"(?:authorization|password|secret|token|tenantId|environmentId|connectionName)"\s*:']:
        exigir(not re.search(patron, serializado), "Se encontró un patrón prohibido de identidad, secreto o destino")
    return p["definition"]


def casos_sinteticos(d):
    a = d["actions"]
    urls = [(MARCADOR, True, None), ("", True, None), ("  ", True, None),
            (MARCADOR.upper(), True, None), ("https://otro.invalid/health", True, None),
            ("https://pruebas.example/health", False, True), (" https://pruebas.example/health ", False, True),
            ("http://pruebas.example/health", False, False), ("https://pruebas.example/otra", False, False),
            ("https://pruebas.example/health/", False, False), ("https://pruebas.example/health?q=1", False, False),
            ("https://usuario:clave@pruebas.example/health", False, False), ("https://pruebas.example/health#x", False, False),
            ("https://pruebas.example/health?", False, False), ("https:///health", False, False),
            ("no-es-una-url", False, False), ("https://pruebas.example/a/health", False, False),
            ("https://pruebas.example/hea lth", False, False), ("https://pruebas.example/health\nX", False, False)]
    for url, pendiente, valida in urls:
        out = {"PARAM_URL_PRUEBAS": url}
        out["URL_NORMALIZADA"] = evaluar(a["URL_NORMALIZADA"]["inputs"], out)
        exigir(evaluar(a["BLOQUEAR_CONFIGURACION_PENDIENTE"]["expression"], out) == pendiente, "Guarda de marcador incorrecta")
        if not pendiente:
            out["PARTES_URL"] = evaluar_objeto(a["PARSEAR_URL"]["actions"]["PARTES_URL"]["inputs"], out)
            exigir(evaluar(a["VALIDAR_URL"]["expression"], out) == valida, "Validación sintética de URL incorrecta")
    casos = [("Succeeded", 200, "", "RESPUESTA_SATISFACTORIA"), ("Succeeded", 204, "", "RESPUESTA_SATISFACTORIA"),
             ("Succeeded", 202, "", "RESPUESTA_SATISFACTORIA"), ("Succeeded", 299, "", "RESPUESTA_SATISFACTORIA"),
             ("Failed", 301, "", "ERROR_HTTP"), ("Failed", 400, "BadRequest", "ERROR_HTTP"),
             ("Failed", 401, "Unauthorized", "ERROR_HTTP"), ("Failed", 403, "Forbidden", "ERROR_HTTP"),
             ("Failed", 404, "NotFound", "ERROR_HTTP"), ("Failed", 408, "RequestTimeout", "ERROR_HTTP"),
             ("Failed", 429, "TooManyRequests", "ERROR_HTTP"), ("Failed", 500, "", "ERROR_HTTP"),
             ("Failed", 504, "GatewayTimeout", "ERROR_HTTP"), ("Failed", None, "NameResolutionFailure", "FALLO_CONEXION"),
             ("Failed", None, "TlsFailure", "FALLO_CONEXION"), ("TimedOut", None, "", "TIMEOUT"),
             ("Failed", None, "ActionTimedOut", "TIMEOUT"), ("Failed", None, "HttpRequestTimeout", "TIMEOUT"),
             ("Failed", 200, "InvalidResponse", "ERROR_TECNICO")]
    for status, code, error, expected in casos:
        fixture = {"status": status, "error": {"code": error}}
        if code is not None:
            fixture["outputs"] = {"statusCode": code, "body": "x" * 1500}
        out = {"DIAGNOSTICO_HTTP": evaluar_objeto(a["DIAGNOSTICO_HTTP"]["inputs"], actions={"HTTP_HEALTH": fixture})}
        out["ESTADO_RESULTADO"] = evaluar(a["ESTADO_RESULTADO"]["inputs"], out)
        exigir(out["ESTADO_RESULTADO"] == expected, f"Clasificación incorrecta: {status}/{code}/{error}")
        result = evaluar_objeto(a["RESULTADO"]["inputs"], out)
        exigir(result["estado"] == expected and len(result["mensaje"]) > 30, "Resultado no comprensible")
        exigir(len(result["cuerpo_respuesta_hasta_1000_caracteres"]) <= 1000, "Salida no acotada")
        exigir(evaluar(a["FINALIZAR"]["expression"], out) == (expected == "RESPUESTA_SATISFACTORIA"), "Finalización incorrecta")
    return {"casos_url": len(urls), "casos_resultado": len(casos), "tipo": "evaluación local limitada; no ejecución Power Automate"}


def mutaciones(d):
    cambios = [
        lambda x: x["actions"]["HTTP_HEALTH"].update(runAfter={"PARAM_URL_PRUEBAS": ["Succeeded"]}),
        lambda x: x["actions"]["HTTP_HEALTH"]["inputs"].update(method="POST"),
        lambda x: x["actions"]["HTTP_HEALTH"]["inputs"].update(body={"dato": "no permitido"}),
        lambda x: x["actions"]["HTTP_HEALTH"]["inputs"].update(retryPolicy={"type": "Fixed", "count": 2}),
        lambda x: x["actions"]["HTTP_HEALTH"].update(operationOptions=""),
        lambda x: x["actions"]["HTTP_HEALTH"].pop("limit"),
        lambda x: x["actions"].update(HTTP_EXTRA=copy.deepcopy(x["actions"]["HTTP_HEALTH"])),
        lambda x: x["actions"]["BLOQUEAR_CONFIGURACION_PENDIENTE"].update(actions={}),
        lambda x: x["actions"]["DIAGNOSTICO_HTTP"].update(runAfter={"HTTP_HEALTH": ["Succeeded"]}),
    ]
    for cambiar in cambios:
        modificado = copy.deepcopy(d)
        cambiar(modificado)
        try:
            comprobar_flujo(modificado)
        except (AssertionError, KeyError):
            continue
        raise AssertionError("El validador aceptó una mutación peligrosa")
    return {"mutaciones_rechazadas": len(cambios)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--referencias", type=Path)
    parser.add_argument("--informe", type=Path)
    args = parser.parse_args()
    resultados = []

    def prueba(nombre, funcion):
        try:
            detalle = funcion()
            resultados.append({"prueba": nombre, "resultado": "PASS", "detalle": detalle})
            print("PASS", nombre)
        except Exception as exc:
            resultados.append({"prueba": nombre, "resultado": "FAIL", "detalle": str(exc)})
            print("FAIL", nombre, str(exc))

    ruta = RAIZ / "dist" / f"{ARCHIVO}.zip"
    docs = {}
    d = {}

    def integridad():
        with zipfile.ZipFile(ruta) as z:
            exigir(z.testzip() is None, "CRC incorrecto")
            exigir(len(z.namelist()) == len(set(z.namelist())) == 5, "Entradas duplicadas o faltantes")
            for info in z.infolist():
                exigir(not info.filename.startswith("/") and ".." not in Path(info.filename).parts, "Ruta insegura")
                exigir(info.compress_type == zipfile.ZIP_DEFLATED, "Compresión inesperada")
                docs[info.filename] = json_estricto(z.read(info))
            return {"archivos_json": len(docs), "bytes": ruta.stat().st_size}
    prueba("integridad_zip_y_json_estricto", integridad)

    def identidad():
        d.update(comprobar_identidad(docs))
        return {"recursos_flujo": 1, "conexiones": 0, "nombre": NOMBRE}
    prueba("estructura_identidad_dependencias_y_destinos", identidad)

    def auxiliares():
        exigir(json_estricto((RAIZ / "flujo" / f"{ARCHIVO}_definition.json").read_bytes()) == d, "Definición legible diferente del ZIP")
        for nombre, valor in docs.items():
            exigir(json_estricto((RAIZ / "paquete" / nombre).read_bytes()) == valor, "Archivo auxiliar diferente del ZIP")
        archivos = list(RAIZ.rglob("*.json"))
        for p in archivos:
            if ".git" not in p.parts:
                json_estricto(p.read_bytes())
        return {"json_locales_leidos": len(archivos)}
    prueba("definicion_auxiliares_y_todos_los_json", auxiliares)
    prueba("grafo_guardas_http_timeout_y_errores", lambda: comprobar_flujo(d))
    prueba("casos_sinteticos_expresiones", lambda: casos_sinteticos(d))
    prueba("sensibilidad_del_validador", lambda: mutaciones(d))

    def esquema():
        origen = json_estricto((RAIZ / "evidencia/origen.json").read_bytes())
        contenido = (RAIZ / origen["schema"]["local"]).read_bytes()
        exigir(hashlib.sha256(contenido).hexdigest() == origen["schema"]["sha256"], "Esquema alterado")
        schema = json_estricto(contenido)
        cls = validators.validator_for(schema)
        cls.check_schema(schema)
        errors = list(cls(schema).iter_errors(d))
        exigir(not errors, "; ".join(f"{e.json_path}: {e.message[:180]}" for e in errors[:3]))
        return {"esquema": "Microsoft Logic Apps WDL; no certifica importador de paquetes Power Automate", "errores": len(errors)}
    prueba("esquema_publicado_wdl", esquema)

    def regeneracion():
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(2):
                destino = Path(tmp) / str(i)
                subprocess.run([sys.executable, str(RAIZ / "flujo/construir.py"), "--salida", str(destino)], check=True, capture_output=True)
                exigir((destino / "dist" / ruta.name).read_bytes() == ruta.read_bytes(), "ZIP no reproducible byte a byte")
                for nombre in docs:
                    exigir((destino / "paquete" / nombre).read_bytes() == (RAIZ / "paquete" / nombre).read_bytes(), "Auxiliar no reproducible")
                exigir((destino / "flujo" / f"{ARCHIVO}_definition.json").read_bytes() == (RAIZ / "flujo" / f"{ARCHIVO}_definition.json").read_bytes(), "Definición no reproducible")
        return {"reconstrucciones_limpias": 2, "comparacion": "byte a byte"}
    prueba("regeneracion_determinista", regeneracion)

    def huella():
        actual = hashlib.sha256(ruta.read_bytes()).hexdigest()
        esperado = ruta.with_suffix(".zip.sha256").read_text().split()[0]
        exigir(actual == esperado, "SHA-256 incorrecto")
        return actual
    prueba("sha256_entregable", huella)

    if args.referencias:
        def referencias():
            origen = json_estricto((RAIZ / "evidencia/origen.json").read_bytes())
            for nombre, meta in origen["files"].items():
                b = (args.referencias / nombre).read_bytes()
                exigir(hashlib.sha256(b).hexdigest() == meta["sha256"], "Referencia distinta al commit documentado")
                exigir(hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest() == meta["git_blob_sha"], "Git blob SHA incorrecto")
            with zipfile.ZipFile(args.referencias / "P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_V5.zip") as z:
                exigir(z.testzip() is None, "ZIP de referencia corrupto")
                refdocs = {n: json_estricto(z.read(n)) for n in z.namelist()}
            normalizar = lambda x: {UUID.sub("{flow}", n) for n in x}
            exigir(normalizar(refdocs) == normalizar(docs), "Estructura distinta al paquete de referencia")
            refdef = next(v for k, v in refdocs.items() if k.endswith("/definition.json"))
            exigir(refdef["properties"]["definition"] == json_estricto((args.referencias / "p0/flujo/P0_CARGA_EXTRACTOS_BANCARIOS_CLOUD_definition.json").read_bytes()), "Definición origen no coincide con su ZIP")
            exigir(not set(UUID.findall(json.dumps(refdocs))) & set(UUID.findall(json.dumps(docs))), "Se heredaron identidades del paquete anterior")
            for n in ["manifest.json", "Microsoft.Flow/flows/manifest.json"]:
                exigir(set(refdocs[n]) == set(docs[n]), "Campos de manifiesto incompatibles con referencia")
            nuevo = next(v for k, v in docs.items() if k.endswith("/definition.json"))
            exigir(set(refdef) == set(nuevo) and set(refdef["properties"]) == set(nuevo["properties"]), "Envoltura distinta a referencia")
            return {"commit": origen["commit"], "archivos_comprobados": len(origen["files"]), "identificadores_heredados": 0}
        prueba("referencias_fijadas_y_metodo_de_empaquetado", referencias)

    informe = {"fecha": datetime.now(ZoneInfo("America/La_Paz")).isoformat(),
        "tipo": "Validación estática; sin importación ni ejecución en tenant", "comando": [sys.executable, *sys.argv],
        "python": sys.version.split()[0], "pruebas": resultados,
        "resultado": "PASS" if all(r["resultado"] == "PASS" for r in resultados) else "FAIL",
        "limitaciones": ["El evaluador local no implementa el motor Power Automate.",
            "El esquema WDL no certifica el importador de paquetes ni valida semántica de expresiones.",
            "Timeout efectivo, número de solicitudes de red, redirecciones, licencia Premium y DLP pendientes de prueba real.",
            "Cancelación manual de una ejecución no garantiza que se ejecute su diagnóstico."]}
    if args.informe:
        args.informe.parent.mkdir(parents=True, exist_ok=True)
        args.informe.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(resultados)} grupos; resultado: {informe['resultado']}")
    return 0 if informe["resultado"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
