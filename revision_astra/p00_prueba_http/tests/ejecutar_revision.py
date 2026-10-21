"""Adapta las rutas de la copia de revisión al validador original sin editarlo.

Usa un directorio temporal con la estructura original, verifica las copias y
ejecuta las mismas pruebas. No modifica el flujo ni los artefactos de entrada.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE_ZIP = "CAJA_AYACUCHO_00_PRUEBA_HTTP.zip"
ESPERADO = "7d8816b1bf874771b63faffd5a83e20c956ec7e195bb7392690c1aa121078a2d"
COMMIT_DESARROLLO = "06232da9f7602b92696c1c4be57dbe25be04efec"


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--referencias", type=Path, help="Directorio de referencias originales; opcional")
    parser.add_argument("--informe", type=Path, help="Nuevo informe de esta ejecución; no sobrescribir el histórico")
    args = parser.parse_args()
    equivalencia = json.loads((RAIZ / "evidencia/equivalencia.json").read_text(encoding="utf-8"))
    if equivalencia["commit_desarrollo"] != COMMIT_DESARROLLO or equivalencia["sha256_zip"] != ESPERADO:
        raise ValueError("La procedencia no corresponde a la entrega solicitada")
    for item in equivalencia["archivos"]:
        ruta = RAIZ / item["copia_revision"]
        if huella(ruta) != item["sha256"]:
            raise ValueError(f"La copia difiere de la entrega: {item['copia_revision']}")
    paquete = RAIZ / "dist" / NOMBRE_ZIP
    if huella(paquete) != ESPERADO:
        raise ValueError("El ZIP no coincide con el SHA-256 esperado")
    historico = json.loads((RAIZ / "evidencia/validacion_original.json").read_text(encoding="utf-8"))
    prueba_sha = next(p for p in historico["pruebas"] if p["prueba"] == "sha256_entregable")
    if prueba_sha["detalle"] != ESPERADO or historico["resultado"] != "PASS":
        raise ValueError("La evidencia histórica no corresponde al ZIP")
    if args.informe:
        protegidos = {(RAIZ / i["copia_revision"]).resolve() for i in equivalencia["archivos"]}
        protegidos.update((RAIZ / p).resolve() for p in ["evidencia/equivalencia.json", "SHA256SUMS.txt"])
        if args.informe.resolve() in protegidos:
            raise ValueError("El informe nuevo no puede reemplazar un artefacto de la entrega original")

    with tempfile.TemporaryDirectory(prefix="caja-ayacucho-revision-") as temp:
        raiz_temporal = Path(temp)
        # Restituye las rutas que espera el validador conservado byte a byte.
        for item in equivalencia["archivos"]:
            destino = raiz_temporal / item["original"]
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RAIZ / item["copia_revision"], destino)
        with zipfile.ZipFile(paquete) as z:
            if z.testzip() is not None:
                raise ValueError("ZIP corrupto")
            for info in z.infolist():
                ruta = Path(info.filename)
                if ruta.is_absolute() or ".." in ruta.parts or not info.filename.endswith(".json"):
                    raise ValueError("Entrada ZIP inesperada")
                destino = raiz_temporal / "paquete" / ruta
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_bytes(z.read(info))
        comando = [sys.executable, "-B", "pruebas/validar.py"]
        if args.referencias:
            comando += ["--referencias", str(args.referencias.resolve())]
        comando += ["--informe", "resultado_revision.json"]
        ejecucion = subprocess.run(comando, cwd=raiz_temporal, text=True, capture_output=True)
        print(ejecucion.stdout, end="")
        if ejecucion.stderr:
            print(ejecucion.stderr, file=sys.stderr, end="")
        reporte = raiz_temporal / "resultado_revision.json"
        resultado = json.loads(reporte.read_text(encoding="utf-8")) if reporte.exists() else None
        entradas = {item["copia_revision"]: huella(RAIZ / item["copia_revision"]) for item in equivalencia["archivos"]}
        for item in equivalencia["archivos"]:
            if entradas[item["copia_revision"]] != item["sha256"]:
                raise ValueError("Un artefacto de entrada cambió durante la validación")
        salida = {
            "fecha": datetime.now(ZoneInfo("America/La_Paz")).isoformat(),
            "tipo": "Nueva ejecución de las pruebas originales desde la copia de revisión",
            "commit_desarrollo": COMMIT_DESARROLLO, "sha256_zip": ESPERADO,
            "comando_revision": [sys.executable, *sys.argv],
            "comando_validador_en_directorio_temporal": comando,
            "sha256_adaptador": huella(Path(__file__)), "sha256_entradas": entradas,
            "stdout_completo": ejecucion.stdout, "stderr_completo": ejecucion.stderr,
            "codigo_salida": ejecucion.returncode, "resultado_validador_original": resultado,
            "copias_originales_sin_modificar": True,
            "estado": "Validación estática realizada. Importación y ejecución en el tenant pendientes."
        }
        if args.informe:
            args.informe.parent.mkdir(parents=True, exist_ok=True)
            args.informe.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return ejecucion.returncode


if __name__ == "__main__":
    raise SystemExit(main())
