"""El importador del Excel de CIS, con un Excel pequeño creado en la prueba (textos inventados)."""

import openpyxl
import pytest

from scripts.importar_cis import COLUMNAS, convertir


def _excel(tmp_path, filas):
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Controls v8.1.2"
    hoja.append(COLUMNAS)
    for f in filas:
        hoja.append(f)
    ruta = tmp_path / "cis.xlsx"
    libro.save(ruta)
    return ruta


def _filas_completas(salvaguardas_control_3=10):
    filas = []
    for n in range(1, 19):
        filas.append([f"{n}\xa0", None, None, None, f"Control {n}", f"Descripción {n}", None, None, None])
        total = salvaguardas_control_3 if n == 3 else 2
        for i in range(1, total + 1):
            # Excel guarda "3.10" como número 3.1: el importador debe reconstruir el id.
            filas.append([str(n), float(f"{n}.{i}"), "Devices", "Protect", f"Salvaguarda {n}.{i}",
                          f"Criterio {n}.{i}", "x" if i == 1 else None, "x", "x"])
    return filas


def test_convierte_y_reconstruye_ids_terminados_en_cero(tmp_path):
    datos = convertir(_excel(tmp_path, _filas_completas()))
    assert len(datos["controles"]) == 18
    ids = [s["id"] for s in datos["controles"][2]["salvaguardas"]]
    assert ids[-1] == "3.10" and len(set(ids)) == 10
    s1, s2 = datos["controles"][0]["salvaguardas"]
    assert (s1["ig"], s2["ig"]) == (1, 2)
    assert datos["licencia"] == "CC BY-NC-ND 4.0"


def test_rechaza_excel_incompleto(tmp_path):
    with pytest.raises(ValueError):
        convertir(_excel(tmp_path, _filas_completas()[:5]))
