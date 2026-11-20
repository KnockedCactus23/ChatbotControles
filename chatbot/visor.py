"""Visor de evidencia (Fase 5): ubica la cita de cada salvaguarda en el PDF y prepara la página para mostrarla.

- La página se dibuja una sola vez con PyMuPDF como PNG en ``static/visor/`` (servida por Streamlit con
  ``server.enableStaticServing``; la carpeta está en .gitignore). Todas las citas de una página comparten la imagen.
- El resaltado son rectángulos normalizados (0-1) que el script del panel pinta en amarillo sobre la imagen.
- Búsqueda en tres pasos:
  1. ``page.search_for(cita)`` tal cual.
  2. La cita normalizada (espacios, saltos de línea, comillas tipográficas, puntos suspensivos de los extremos).
  3. Por fragmentos: separa en «…» y en fin de oración (citas que unen celdas de una tabla) y, en cada trozo, busca
     el tramo más largo que aparezca. Cuenta como hallada si se resalta al menos el 40 % de las palabras.
  Primero se busca en la página indicada y después en las demás. Si no aparece, el visor abre la página citada
  sin resaltado y avisa «No se encontró la cita exacta».
- Documentos sin PDF (texto pegado o archivo perdido) se muestran como texto con la cita marcada.
"""

import hashlib
import re
from functools import lru_cache
from pathlib import Path

import pymupdf

CARPETA = Path(__file__).resolve().parent.parent / "static" / "visor"
URL = "app/static/visor"
ZOOM = 2.0            # 144 ppp: nítido en pantallas de alta densidad
VENTANA = 6           # en el tercer paso se prueban tramos de hasta 2 × VENTANA palabras
MIN_FRAGMENTOS = 0.4  # fracción de palabras resaltadas para aceptar la búsqueda por fragmentos

_COMILLAS = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "´": "'", " ": " "})
_TROZOS = re.compile(r"\s*…\s*|(?<=[.;:])\s+")  # puntos suspensivos y fin de oración o de celda
_SUSPENSIVOS = re.compile(r"\s*(?:…|\.\.\.|\[\s*…\s*\]|\[\s*\.\.\.\s*\])\s*")


def normalizar(texto: str) -> str:
    t = re.sub(r"\s+", " ", (texto or "").translate(_COMILLAS)).strip()
    t = t.strip("\"' ")
    return _SUSPENSIVOS.sub(" … ", t).strip(" …")


def _huella(ruta: Path) -> str:
    st = ruta.stat()
    return hashlib.sha1(f"{ruta.resolve()}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:10]


def _norm_rects(rects, pagina) -> list[tuple[float, float, float, float]]:
    w, h = pagina.rect.width, pagina.rect.height
    vistos, salida = set(), []
    for r in rects:
        t = (round(r.x0 / w, 4), round(r.y0 / h, 4), round(r.x1 / w, 4), round(r.y1 / h, 4))
        if t not in vistos:
            vistos.add(t)
            salida.append(t)
    return sorted(salida, key=lambda t: (t[1], t[0]))


def _buscar_en(pagina, cita: str) -> tuple[str, list]:
    """('exacta' | 'fragmentos' | '', rectángulos) para una página."""
    if hits := pagina.search_for(cita):
        return "exacta", hits
    limpia = normalizar(cita)
    if limpia and limpia != cita and "…" not in limpia and (hits := pagina.search_for(limpia)):
        return "exacta", hits
    palabras_total, cubiertas, rects = 0, 0, []
    for trozo in (p.strip(" .;:") for p in _TROZOS.split(limpia)):
        palabras = trozo.split()
        palabras_total += len(palabras)
        # Segmentación codiciosa: desde cada palabra, el tramo más largo (hasta VENTANA*2 palabras) que esté en la
        # página. Así se recuperan las citas que unen celdas de una tabla o frases separadas.
        k = 0
        while k < len(palabras):
            for fin in range(min(len(palabras), k + VENTANA * 2), k + 1, -1):
                tramo = " ".join(palabras[k:fin])
                if len(tramo) >= 10 and (hits := pagina.search_for(tramo)):
                    rects += hits
                    cubiertas += fin - k
                    k = fin
                    break
            else:
                k += 1
    if palabras_total and cubiertas / palabras_total >= MIN_FRAGMENTOS:
        return "fragmentos", rects
    return "", []


@lru_cache(maxsize=512)
def _localizar(ruta: str, huella: str, pagina: int, cita: str) -> tuple[str, int, tuple, int]:
    with pymupdf.open(ruta) as doc:
        n = doc.page_count
        orden = list(range(1, n + 1))
        if 1 <= pagina <= n:
            orden.remove(pagina)
            orden.insert(0, pagina)
        mejor = None
        for num in orden:
            modo, rects = _buscar_en(doc[num - 1], cita)
            if modo == "exacta":
                return modo, num, tuple(_norm_rects(rects, doc[num - 1])), n
            if modo and mejor is None:
                mejor = (modo, num, tuple(_norm_rects(rects, doc[num - 1])), n)
        return mejor or ("no_encontrada", pagina if 1 <= pagina <= n else 1, (), n)


def localizar(ruta: str | Path, pagina: int | None, cita: str) -> dict:
    """Ubica la cita. Devuelve {modo, pagina, rects, total}; modo es 'exacta', 'fragmentos' o 'no_encontrada'."""
    ruta = Path(ruta)
    modo, num, rects, total = _localizar(str(ruta), _huella(ruta), int(pagina or 0), cita or "")
    return {"modo": modo, "pagina": num, "rects": list(rects), "total": total}


def imagen(ruta: str | Path, pagina: int, carpeta: Path | None = None) -> str:
    """Dibuja la página (si no está ya en caché) y devuelve su nombre de archivo dentro de ``static/visor``."""
    ruta = Path(ruta)
    carpeta = carpeta or CARPETA
    nombre = f"{_huella(ruta)}_p{pagina}.png"
    destino = carpeta / nombre
    if not destino.exists():
        carpeta.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(ruta) as doc:
            pix = doc[pagina - 1].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), alpha=False)
            tmp = destino.with_suffix(".tmp")
            pix.save(str(tmp), output="png")
            tmp.replace(destino)
    return nombre


def _ruta_pdf(doc, pid: str, carpeta_evaluaciones: Path | None) -> Path | None:
    candidatos = [Path(doc.archivo)] if doc.archivo else []
    if carpeta_evaluaciones is not None:
        candidatos.append(carpeta_evaluaciones / f"{pid}_{doc.clave}.pdf")
    return next((c for c in candidatos if c.is_file()), None)


def evidencias(matriz: dict, documentos: dict, pid: str = "", carpeta_evaluaciones: Path | None = None) -> dict[str, dict]:
    """Datos del visor por salvaguarda con cita: documento, página, imagen y rectángulos (o el texto de la página)."""
    salida = {}
    for sid, r in matriz.items():
        doc = documentos.get(r.fuente) if r.fuente else None
        if not doc or not (r.cita or "").strip():
            continue
        base = {"doc": doc.etiqueta, "cita": r.cita, "total": len(doc.paginas)}
        ruta = _ruta_pdf(doc, pid, carpeta_evaluaciones) if doc.tipo == "pdf" else None
        if ruta:
            try:
                loc = localizar(ruta, r.pagina, r.cita)
                salida[sid] = {**base, **loc, "img": f"{URL}/{imagen(ruta, loc['pagina'])}"}
                continue
            except Exception:  # PDF dañado o ilegible: se cae al texto extraído
                pass
        num = r.pagina if r.pagina and 1 <= r.pagina <= len(doc.paginas) else 1
        texto = doc.paginas[num - 1] if doc.paginas else ""
        salida[sid] = {**base, "modo": "texto", "pagina": num, "rects": [], "texto": texto}
    return salida
