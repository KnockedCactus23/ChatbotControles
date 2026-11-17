"""Catálogo CIS de prueba y utilidades comunes.

El JSON real no está en el repositorio (licencia CC BY-NC-ND), así que las pruebas usan un
catálogo con la MISMA estructura y textos inventados: 18 controles con 3 salvaguardas cada uno
(una por IG), es decir, 18 salvaguardas IG1 en lugar de 56.
"""

import json

import pytest

from chatbot import controls, prompts


def catalogo_falso() -> dict:
    return {
        "fuente": "Catálogo de prueba", "autor": "Equipo", "licencia": "—", "url": "", "url_licencia": "",
        "controles": [
            {"numero": n, "titulo": f"Control de prueba {n}", "descripcion": f"Descripción de prueba del control {n}.",
             "salvaguardas": [
                 {"id": f"{n}.{i}", "titulo": f"Salvaguarda {n}.{i}", "descripcion": f"Criterio de prueba {n}.{i}.",
                  "clase_activo": "Devices", "funcion": "Protect", "ig": i}
                 for i in (1, 2, 3)]}
            for n in range(1, 19)
        ],
    }


def _limpiar_caches():
    controls._cargar.cache_clear()
    for f in prompts.TODOS:
        f.cache_clear()


@pytest.fixture(autouse=True)
def catalogo_de_prueba(tmp_path, monkeypatch):
    ruta = tmp_path / "cis_prueba.json"
    ruta.write_text(json.dumps(catalogo_falso()), encoding="utf-8")
    monkeypatch.setenv("CIS_CATALOGO", str(ruta))
    _limpiar_caches()
    yield
    _limpiar_caches()


# Documento de caso de prueba: 2 páginas de texto (simula el texto extraído de un PDF).
PAGINAS = [
    "Perfil. Empresa ficticia de comercio con 140 empleados.\nTodos los equipos cuentan con antivirus Defender con firmas automáticas.",
    "Respaldos. El ERP se respalda diariamente a un NAS en la misma oficina.\nNo existe un plan de respuesta a incidentes documentado.",
]
