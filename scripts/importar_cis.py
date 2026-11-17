"""Convierte el Excel oficial de CIS Controls v8.1.x a un JSON que usa el chatbot.

Uso:
    python scripts/importar_cis.py "/ruta/CIS_Controls_Version_8.1.2___March_2025.xlsx"

Genera chatbot/data/cis_v8_1_2.json (ignorado por git). El contenido de CIS se guarda
SIN MODIFICAR (en inglés): su licencia es CC BY-NC-ND 4.0, que no permite distribuir
versiones modificadas o traducidas. Por eso el JSON no se sube al repositorio y cada
integrante lo genera desde el Excel descargado de https://www.cisecurity.org/controls/v8-1
"""

import json
import sys
from pathlib import Path

import openpyxl

DESTINO = Path(__file__).resolve().parent.parent / "chatbot" / "data" / "cis_v8_1_2.json"
COLUMNAS = ["CIS Control", "CIS Safeguard", "Asset Class", "Security Function", "Title", "Description", "IG1", "IG2", "IG3"]


def _texto(valor) -> str:
    return str(valor or "").replace("\xa0", " ").strip()


def convertir(ruta_excel: str | Path) -> dict:
    libro = openpyxl.load_workbook(ruta_excel, read_only=True, data_only=True)
    hoja = next((libro[n] for n in libro.sheetnames if n.lower().startswith("controls")), None)
    if hoja is None:
        raise ValueError(f"No encontré la hoja 'Controls ...' en el Excel. Hojas: {libro.sheetnames}")

    filas = hoja.iter_rows(values_only=True)
    encabezado = [_texto(c) for c in next(filas)]
    if encabezado[: len(COLUMNAS)] != COLUMNAS:
        raise ValueError(f"Columnas inesperadas: {encabezado}. Se esperaban: {COLUMNAS}")

    controles: dict[int, dict] = {}
    for fila in filas:
        control, salvaguarda, clase, funcion, titulo, descripcion, ig1, ig2, ig3 = (list(fila) + [None] * 9)[:9]
        if not _texto(control):
            continue
        numero = int(float(_texto(control)))
        if not _texto(salvaguarda):  # fila del control
            controles[numero] = {"numero": numero, "titulo": _texto(titulo),
                                 "descripcion": _texto(descripcion), "salvaguardas": []}
            continue
        ig = 1 if _texto(ig1) else 2 if _texto(ig2) else 3 if _texto(ig3) else None
        if ig is None:
            raise ValueError(f"La salvaguarda {salvaguarda} no tiene IG marcado")
        # Excel guarda los ids como número: "3.10" llega como 3.1. Se reconstruye por posición
        # (las salvaguardas vienen en orden N.1, N.2, ...) y se valida contra el valor numérico.
        sid = f"{numero}.{len(controles[numero]['salvaguardas']) + 1}"
        if float(sid) != float(_texto(salvaguarda)):
            raise ValueError(f"Orden inesperado: se esperaba {sid} y el Excel dice {salvaguarda}")
        controles[numero]["salvaguardas"].append({
            "id": sid, "titulo": _texto(titulo), "descripcion": _texto(descripcion),
            "clase_activo": _texto(clase), "funcion": _texto(funcion), "ig": ig,
        })

    if sorted(controles) != list(range(1, 19)):
        raise ValueError(f"Se esperaban los controles 1 a 18 y se encontraron: {sorted(controles)}")
    return {
        "fuente": f"CIS Critical Security Controls ({hoja.title})",
        "autor": "Center for Internet Security, Inc. (CIS®)",
        "url": "https://www.cisecurity.org/controls/v8-1",
        "licencia": "CC BY-NC-ND 4.0",
        "url_licencia": "https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode",
        "controles": [controles[n] for n in sorted(controles)],
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    datos = convertir(sys.argv[1])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(c["salvaguardas"]) for c in datos["controles"])
    print(f"Listo: {len(datos['controles'])} controles y {total} salvaguardas → {DESTINO}")


if __name__ == "__main__":
    main()
