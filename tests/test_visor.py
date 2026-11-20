"""Visor de evidencia (Fase 5): búsqueda de la cita en el PDF, imagen de la página y datos para la matriz."""

import pymupdf
import pytest

from chatbot import panel, visor
from chatbot.documentos import Documento
from chatbot.state import Resultado, Version, matriz_vacia

PARRAFO = ("El reporte de Intune del 20 de octubre de 2026 muestra 112 dispositivos registrados en la consola "
           "corporativa. Recursos Humanos reporta 145 colaboradores activos.")


@pytest.fixture
def pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(visor, "CARPETA", tmp_path / "img")
    visor._localizar.cache_clear()
    ruta = tmp_path / "caso.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Portada del caso ficticio.")
    pag = doc.new_page()
    # El párrafo se parte en varias líneas, como en un PDF real.
    pag.insert_textbox(pymupdf.Rect(72, 72, 330, 400), PARRAFO, fontsize=11)
    doc.save(ruta)
    return ruta


def test_cita_exacta_en_varias_lineas(pdf):
    r = visor.localizar(pdf, 2, "El reporte de Intune del 20 de octubre de 2026 muestra 112 dispositivos registrados")
    assert r["modo"] == "exacta" and r["pagina"] == 2 and r["total"] == 2
    assert len(r["rects"]) >= 2  # una marca por línea
    assert all(0 <= v <= 1 for rect in r["rects"] for v in rect)


def test_comillas_espacios_y_pagina_equivocada(pdf):
    r = visor.localizar(pdf, 1, "“Recursos  Humanos\nreporta 145 colaboradores activos.”")
    assert r["modo"] == "exacta" and r["pagina"] == 2  # se corrige la página


def test_fragmentos_unidos_con_puntos_suspensivos(pdf):
    r = visor.localizar(pdf, 2, "El reporte de Intune del 20 de octubre … Recursos Humanos reporta 145 colaboradores")
    assert r["modo"] == "fragmentos" and r["rects"]


def test_cita_inexistente_abre_la_pagina_sin_resaltado(pdf):
    r = visor.localizar(pdf, 2, "La empresa cuenta con un SOC propio que opera las veinticuatro horas")
    assert r == {"modo": "no_encontrada", "pagina": 2, "rects": [], "total": 2}


def test_imagen_se_dibuja_una_vez(pdf):
    nombre = visor.imagen(pdf, 2)
    archivo = visor.CARPETA / nombre
    assert archivo.exists() and archivo.read_bytes()[:4] == b"\x89PNG"
    antes = archivo.stat().st_mtime_ns
    assert visor.imagen(pdf, 2) == nombre and archivo.stat().st_mtime_ns == antes


def test_evidencias_y_matriz(pdf):
    m = matriz_vacia()
    sid, otro, texto = list(m)[:3]
    m[sid] = Resultado(sid, "parcial", "aplica", "Hay inventario parcial.", "pdf1", 2, "", "muestra 112 dispositivos registrados")
    m[otro] = Resultado(otro, "no_implementado", "aplica", "Sin evidencia.", "pdf1", 2, "", "")  # sin cita: sin visor
    m[texto] = Resultado(texto, "implementado", "aplica", "Lo dice el texto.", "pdf2", 1, "", "respaldo diario")
    docs = {"pdf1": Documento("pdf1", "caso.pdf", "pdf", ["Portada", PARRAFO], str(pdf)),
            "pdf2": Documento("pdf2", "Texto proporcionado", "texto", ["Se hace un respaldo diario cifrado."])}
    ev = visor.evidencias(m, docs, "abc")
    assert set(ev) == {sid, texto}
    assert ev[sid]["modo"] == "exacta" and ev[sid]["img"].startswith("app/static/visor/")
    assert ev[texto]["modo"] == "texto" and "respaldo diario" in ev[texto]["texto"]

    html = panel.matriz(Version("v1", "2026-11-19", m), docs, "Matriz", "", "matriz", evidencias=ev)
    assert f'data-ev="matriz:{sid}"' in html and f'data-evid="matriz:{sid}"' in html
    assert f'data-ev="matriz:{otro}"' not in html
    assert "<button" not in panel.matriz(Version("v1", "2026-11-19", m), docs, "Matriz", "", "matriz").split("<tbody>")[1]


def test_pdf_perdido_usa_el_texto(tmp_path):
    m = matriz_vacia()
    sid = next(iter(m))
    m[sid] = Resultado(sid, "parcial", "aplica", "x", "pdf1", 1, "", "respaldo diario")
    docs = {"pdf1": Documento("pdf1", "caso.pdf", "pdf", ["Hay respaldo diario."], str(tmp_path / "no_existe.pdf"))}
    assert visor.evidencias(m, docs, "abc")[sid]["modo"] == "texto"


def test_script_sin_etiquetas_html():
    import re
    cuerpo = panel.script().removeprefix("<script>").removesuffix("</script>")
    assert not re.search(r"<[a-zA-Z/!]", cuerpo)  # st.html descarta el script si las lleva
