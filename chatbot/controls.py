"""Catálogo normativo: CIS Controls v8.1, Implementation Group 1 (56 salvaguardas).

- Única referencia normativa del agente (regla R2): no se usan otros marcos.
- Los textos oficiales de CIS (títulos, descripciones, IG) NO viven en el repositorio: su
  licencia (CC BY-NC-ND 4.0) no permite redistribuirlos modificados. Se leen de
  ``chatbot/data/cis_v8_1_2.json``, generado con ``scripts/importar_cis.py`` desde el Excel
  oficial, y se usan sin modificar (en inglés) como criterio de evaluación.
- Aquí solo hay lo que escribió el equipo: nombres cortos en español de los 18 controles.
- Las 56 salvaguardas IG1 están en 15 controles; los controles 13, 16 y 18 no tienen
  salvaguardas IG1 y se muestran como "sin salvaguardas IG1".
"""

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

RUTA_CATALOGO = Path(__file__).parent / "data" / "cis_v8_1_2.json"

# Decisión del equipo (actividad M3.6): se evalúa SIEMPRE y SOLO el IG1.
IG_EVALUADO = 1
TOTAL_IG1_OFICIAL = 56


class CatalogoNoEncontrado(Exception):
    """Falta el JSON de CIS: hay que generarlo desde el Excel oficial."""


@dataclass(frozen=True)
class Salvaguarda:
    id: str            # "11.4"
    control_id: str    # "CIS-11"
    titulo: str        # oficial, inglés
    descripcion: str   # oficial, inglés (criterio de evaluación)
    clase_activo: str
    funcion: str
    ig: int            # IG mínimo en el que aplica (1, 2 o 3)


@dataclass(frozen=True)
class Control:
    id: str                      # "CIS-11"
    numero: int
    nombre: str                  # nombre corto en español (del equipo)
    titulo_oficial: str          # inglés
    descripcion: str             # oficial, inglés
    salvaguardas: tuple[Salvaguarda, ...]

    @property
    def ig1(self) -> tuple[Salvaguarda, ...]:
        return tuple(s for s in self.salvaguardas if s.ig <= IG_EVALUADO)


# Nombres en español de los 18 Controles CIS (redacción del equipo, no traducción oficial).
NOMBRES = {
    1: "Inventario de activos empresariales", 2: "Inventario de software", 3: "Protección de datos",
    4: "Configuración segura", 5: "Gestión de cuentas", 6: "Gestión del control de accesos",
    7: "Gestión continua de vulnerabilidades", 8: "Registros de auditoría", 9: "Protección de correo y navegador",
    10: "Defensas contra malware", 11: "Recuperación de datos", 12: "Infraestructura de red",
    13: "Monitoreo y defensa de la red", 14: "Concientización y capacitación", 15: "Gestión de proveedores de servicios",
    16: "Seguridad del software de aplicación", 17: "Respuesta a incidentes", 18: "Pruebas de penetración",
}


@dataclass(frozen=True)
class Catalogo:
    controles: tuple[Control, ...]
    metadatos: dict

    @property
    def por_id(self) -> dict[str, Control]:
        return {c.id: c for c in self.controles}

    @property
    def salvaguardas(self) -> dict[str, Salvaguarda]:
        return {s.id: s for c in self.controles for s in c.salvaguardas}

    def ig1(self) -> list[Salvaguarda]:
        """Las salvaguardas en alcance, en orden oficial (1.1, 1.2, 2.1, ...)."""
        return [s for c in self.controles for s in c.ig1]

    def ids_ig1(self) -> list[str]:
        return [s.id for s in self.ig1()]


def _ruta() -> Path:
    return Path(os.getenv("CIS_CATALOGO") or RUTA_CATALOGO)


@lru_cache(maxsize=4)
def _cargar(ruta: str) -> Catalogo:
    p = Path(ruta)
    if not p.exists():
        raise CatalogoNoEncontrado(
            f"No existe {p}. Descarga el Excel de CIS Controls v8.1 desde https://www.cisecurity.org/controls/v8-1 "
            "y ejecuta: python scripts/importar_cis.py \"ruta/al/archivo.xlsx\"")
    datos = json.loads(p.read_text(encoding="utf-8"))
    controles = []
    for c in datos["controles"]:
        cid = f"CIS-{c['numero']:02d}"
        salv = tuple(Salvaguarda(s["id"], cid, s["titulo"], s["descripcion"], s["clase_activo"], s["funcion"], int(s["ig"]))
                     for s in c["salvaguardas"])
        controles.append(Control(cid, c["numero"], NOMBRES[c["numero"]], c["titulo"], c["descripcion"], salv))
    meta = {k: v for k, v in datos.items() if k != "controles"}
    return Catalogo(tuple(controles), meta)


# Vista ejecutiva: los 15 controles con IG1 agrupados en 7 áreas de negocio (decisión del equipo, 2026-11-19).
# Mapeo fijo en código; la madurez de cada área usa la misma fórmula que la implementación global.
AREAS = (
    ("activos", "Activos y software", (1, 2)),
    ("identidades", "Identidades y accesos", (5, 6)),
    ("datos", "Protección de datos", (3,)),
    ("equipos", "Equipos y vulnerabilidades", (4, 7, 9, 10, 12)),
    ("monitoreo", "Monitoreo y respuesta", (8, 17)),
    ("continuidad", "Continuidad", (11,)),
    ("personas", "Personas y proveedores", (14, 15)),
)


def area_de_control(numero: int) -> str | None:
    return next((clave for clave, _, numeros in AREAS if numero in numeros), None)


def catalogo() -> Catalogo:
    return _cargar(str(_ruta()))


def control(cid: str) -> Control:
    return catalogo().por_id[cid]


def salvaguarda(sid: str) -> Salvaguarda | None:
    return catalogo().salvaguardas.get(sid)


def atribucion() -> str:
    m = catalogo().metadatos
    return (f"{m.get('fuente', 'CIS Critical Security Controls v8.1')} © {m.get('autor', 'Center for Internet Security, Inc.')}. "
            f"Licencia {m.get('licencia', 'CC BY-NC-ND 4.0')}.")
