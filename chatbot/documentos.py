"""Documentos de evidencia del caso (PDF 1: contexto, PDF 2: iniciativas, o texto pegado).

El texto de cada página se extrae localmente para VERIFICAR las
citas que devuelve el modelo (reglas R3 y R6): si una cita no aparece en el documento, la
conclusión no se acepta como evidencia documental.
"""

import io
import re
import unicodedata
from dataclasses import dataclass, field

from pypdf import PdfReader

UMBRAL_CITA = 0.8  # fracción de palabras de la cita que deben aparecer en la página


@dataclass
class Documento:
    clave: str                 # "pdf1" | "pdf2"
    nombre: str                # nombre del archivo o "Texto proporcionado"
    tipo: str                  # "pdf" | "texto"
    paginas: list[str] = field(default_factory=list)
    archivo: str = ""          # ruta local del PDF guardado (se reenvía como archivo solo si no tiene texto extraíble)

    @property
    def etiqueta(self) -> str:
        base = {"pdf1": "PDF 1", "pdf2": "PDF 2"}.get(self.clave, self.clave)
        return f"{base} (texto)" if self.tipo == "texto" else base

    def texto_completo(self) -> str:
        return "\n\n".join(f"[Página {i}]\n{t}" for i, t in enumerate(self.paginas, 1))

    def a_dict(self) -> dict:
        return {"clave": self.clave, "nombre": self.nombre, "tipo": self.tipo, "paginas": self.paginas, "archivo": self.archivo}

    @classmethod
    def de_dict(cls, d: dict) -> "Documento":
        return cls(d["clave"], d["nombre"], d["tipo"], d.get("paginas", []), d.get("archivo", ""))


def leer_pdf(datos: bytes) -> list[str]:
    lector = PdfReader(io.BytesIO(datos))
    return [(p.extract_text() or "") for p in lector.pages]


def _normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", sin_acentos.lower())).strip()


def _cobertura(cita: str, pagina: str) -> float:
    palabras = [p for p in _normalizar(cita).split() if len(p) > 2]
    if not palabras:
        return 0.0
    texto = _normalizar(pagina)
    if " ".join(palabras) in texto or _normalizar(cita) in texto:
        return 1.0
    presentes = set(texto.split())
    return sum(1 for p in palabras if p in presentes) / len(palabras)


def verificar_cita(doc: Documento, cita: str, pagina: int | None = None) -> int | None:
    """Devuelve la página (1..n) donde aparece la cita, o None si no aparece en el documento.
    Prueba primero la página indicada por el modelo y luego todas las demás."""
    if not cita or not cita.strip() or not doc.paginas:
        return None
    orden = list(range(1, len(doc.paginas) + 1))
    if pagina and 1 <= pagina <= len(doc.paginas):
        orden.remove(pagina)
        orden.insert(0, pagina)
    for n in orden:
        if _cobertura(cita, doc.paginas[n - 1]) >= UMBRAL_CITA:
            return n
    return None
