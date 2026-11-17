"""Guardado automático local de las evaluaciones (para conservar v1 y v2 entre semanas).

Cada proyecto se guarda en ``evaluaciones/<id>.json`` y sus PDF en ``evaluaciones/<id>_<pdf>.pdf``.
La carpeta está en .gitignore: puede contener documentos del caso.
"""

import json
import os
from pathlib import Path

from .state import Proyecto

CARPETA = Path(os.getenv("EVALUACIONES_DIR") or Path(__file__).resolve().parent.parent / "evaluaciones")


def _carpeta() -> Path:
    CARPETA.mkdir(parents=True, exist_ok=True)
    return CARPETA


def guardar(p: Proyecto) -> None:
    ruta = _carpeta() / f"{p.id}.json"
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(p.a_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ruta)  # escritura atómica: nunca queda un JSON a medias


def guardar_pdf(p: Proyecto, clave: str, datos: bytes) -> str:
    ruta = _carpeta() / f"{p.id}_{clave}.pdf"
    ruta.write_bytes(datos)
    return str(ruta)


def cargar(pid: str) -> Proyecto:
    return Proyecto.de_dict(json.loads((_carpeta() / f"{pid}.json").read_text(encoding="utf-8")))


def listar() -> list[dict]:
    filas = []
    for ruta in sorted(_carpeta().glob("*.json"), key=lambda r: r.stat().st_mtime, reverse=True):
        try:
            d = json.loads(ruta.read_text(encoding="utf-8"))
            filas.append({"id": d["id"], "nombre": d["nombre"], "creado": d["creado"],
                          "versiones": sum(1 for v in ("v1", "v2") if d.get(v))})
        except (json.JSONDecodeError, KeyError):
            continue
    return filas
