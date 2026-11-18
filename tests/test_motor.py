"""Flujo completo del agente con Gemini simulado: ficha → 56 → reporte → PDF 2 → v2, y exportación."""

import csv
import io
import json
from types import SimpleNamespace

import openpyxl
import pytest
from pypdf import PdfReader

from chatbot import controls, exportar
from chatbot.documentos import Documento
from chatbot.engine import ErrorChatbot, Motor
from chatbot.reporte_pdf import ficha_pdf, reporte_pdf
from chatbot.state import Proyecto
from tests.conftest import PAGINAS

FICHA = {
    "nombre_organizacion": "Comercial Ficticia", "resumen_ejecutivo": "Comercio con 140 empleados.",
    "dimensiones": {k: {"resumen": "", "faltante": "", "hallazgos": []} for k in
                    ["organizacion", "procesos", "infraestructura", "activos", "identidades", "proteccion", "recuperacion",
                     "monitoreo", "gobierno", "restricciones"]},
    "informacion_faltante": ["Configuración del firewall"], "ambiguedades": [],
    "perfil_riesgo": {"sector": "Comercio", "tamano": "mediana", "amenazas": [], "prioridad_controles": ["CIS-11", "CIS-10"]},
}
FICHA["dimensiones"]["proteccion"]["hallazgos"] = [
    {"dato": "Antivirus en todos los equipos", "pagina": 2, "seccion": "Perfil", "cita": "Todos los equipos cuentan con antivirus Defender"},
    {"dato": "EDR", "pagina": 1, "seccion": "", "cita": "Cuentan con EDR CrowdStrike"},
]


def _evaluacion(ids):
    evals = []
    for sid in ids:
        if sid == "10.1":
            evals.append({"id": sid, "aplicabilidad": "aplica", "estado": "implementado", "justificacion": "Antivirus en todos",
                          "pagina": 1, "seccion": "Perfil", "cita": "Todos los equipos cuentan con antivirus Defender", "observaciones": ""})
        elif sid == "11.1":
            evals.append({"id": sid, "aplicabilidad": "aplica", "estado": "implementado", "justificacion": "Respaldo en nube",
                          "pagina": 2, "seccion": "", "cita": "Respaldo inmutable en la nube", "observaciones": ""})  # inventada
        elif sid == "17.1":
            continue  # el modelo "olvida" una salvaguarda
        else:
            evals.append({"id": sid, "aplicabilidad": "por_determinar", "estado": "no_verificado", "justificacion": "",
                          "pagina": 0, "seccion": "", "cita": "", "observaciones": ""})
    return {"evaluaciones": evals}


def _reporte():
    riesgo = {"titulo": "R", "descripcion": "d", "activo_proceso": "ERP", "deficiencia": "x", "consecuencia": "y",
              "severidad": "alta", "justificacion": "z", "salvaguardas": ["10.1", "11.1"]}
    ini = {"titulo": "I", "descripcion": "d", "riesgos": [1], "salvaguardas": ["11.1"], "beneficio": "b",
           "esfuerzo": "bajo", "prioridad": 1, "tipo": "quick_win"}
    res = {"postura_inicial": "p", "controles_mayores_brechas": [], "informacion_faltante": [], "principales_riesgos": "r",
           "resultados_preliminares": "pre"}
    return {"resumen_ejecutivo": res, "riesgos": [riesgo] * 5, "iniciativas": [dict(ini, prioridad=n) for n in range(5, 0, -1)]}


@pytest.fixture
def motor_simulado(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    motor = Motor()
    llamadas = []

    def generar(**kw):
        llamadas.append(kw)
        sistema = kw["config"].system_instruction
        texto_usuario = " ".join(p.get("text", "") for p in kw["contents"][0]["parts"] if isinstance(p, dict))
        if "Etapa 2" in sistema:
            datos = FICHA
        elif "Etapa 3 —" in sistema:
            ids = texto_usuario.split("sin omitir ninguna): ")[1].split(", ")
            datos = _evaluacion([i.strip() for i in ids])
        elif "Etapa 5 —" in sistema:
            datos = {"iniciativas": [{"nombre": "MFA", "que_mejoro": "MFA total", "salvaguardas": ["6.1"], "alcance": "completa",
                                      "pendientes": "", "riesgos_que_reduce": [], "evidencia": []}],
                     "cambios": [{"id": "6.1", "estado_propuesto": "implementado", "justificacion": "MFA", "iniciativa": "MFA",
                                  "pagina": 1, "seccion": "", "cita": "MFA para el 100% de los usuarios"}]}
        elif "Etapa 5.6" in sistema:
            base = _reporte()
            datos = {"resumen_cambios": "MFA", "riesgos": [{"titulo": "R", "situacion": "permanece", "explicacion": ""}] * 5,
                     "iniciativas_estado": [{"titulo": "I", "estado": "en_progreso", "explicacion": ""}] * 5,
                     "resumen_ejecutivo": base["resumen_ejecutivo"], "roadmap": base["iniciativas"]}
        elif "Etapas 3.5 y 4" in sistema:
            datos = _reporte()
        else:
            datos = {"mensaje": "Explicación del agente"}
        return SimpleNamespace(text=json.dumps(datos), prompt_feedback=None, candidates=[])

    monkeypatch.setattr(motor.client.models, "generate_content", generar)
    return motor, llamadas


def test_flujo_completo(motor_simulado):
    motor, llamadas = motor_simulado
    p = Proyecto()
    p.documentos["pdf1"] = Documento("pdf1", "caso", "texto", PAGINAS)

    assert "Centinela IG1" in llamadas[0]["config"].system_instruction if motor.explain() else False

    motor.context_sheet(p)
    hallazgos = p.ficha["dimensiones"]["proteccion"]["hallazgos"]
    assert [h["verificada"] for h in hallazgos] == [True, False] and hallazgos[0]["pagina"] == 1
    assert p.nombre == "Comercial Ficticia"

    motor.evaluate(p)
    ids = controls.catalogo().ids_ig1()
    assert list(p.v1.matriz) == ids                                   # no se omite ninguna
    assert p.v1.matriz["10.1"].estado == "implementado"
    assert p.v1.matriz["11.1"].estado == "no_verificado"             # cita inventada → descartada
    assert p.v1.matriz["17.1"].estado == "no_verificado"             # omitida → visible como pendiente
    assert "preguntas" not in llamadas[-1]["config"].response_json_schema["properties"]  # sin preguntas Sí/No
    cfg = llamadas[-1]["config"]
    assert cfg.temperature == 0 and cfg.seed is not None              # reproducible (R9)
    assert "R8." in cfg.system_instruction and "Criterio de prueba 10.1" in cfg.system_instruction
    assert "Criterio de prueba 10.2" not in cfg.system_instruction    # solo IG1

    motor.report(p)
    assert p.v1.cerrada
    assert all("10.1" not in r["salvaguardas"] for r in p.v1.reporte["riesgos"])   # 10.1 está implementada
    assert [i["prioridad"] for i in p.v1.reporte["iniciativas"]] == [1, 2, 3, 4, 5]

    p.documentos["pdf2"] = Documento("pdf2", "avance", "texto", ["Se activó MFA para el 100% de los usuarios de correo."])
    motor.analyze_initiatives(p)
    assert p.cambios[0].cita_verificada
    p.decidir("6.1", "aprobado")
    p.crear_v2()
    motor.updated_report(p)
    assert p.etapa == "actualizado"
    assert p.v1.matriz["6.1"].estado == "no_verificado" and p.v2.matriz["6.1"].estado == "implementado"

    # Exportación: Excel con todas las hojas y CSV con todas las salvaguardas.
    libro = openpyxl.load_workbook(io.BytesIO(exportar.excel(p)))
    assert {"Contexto", "Matriz v1", "Matriz v2", "Indicadores", "Cambios PDF 2", "Roadmap v1", "Roadmap v2"} <= set(libro.sheetnames)
    assert libro["Matriz v1"].max_row == len(ids) + 1
    filas = list(csv.reader(io.StringIO(exportar.csv_matriz(p, p.v2).decode("utf-8-sig"))))
    assert len(filas) == len(ids) + 1 and filas[0][0] == "ID CIS"
    html = exportar.reporte_html(p)
    assert "Cambios derivados del PDF 2" in html and "Roadmap de cinco iniciativas" in html
    assert "R12." in exportar.prompt_maestro_md()

    # Reporte ejecutivo en PDF: válido, con v1 y v2, y dentro del límite de 5 páginas de la actividad.
    pdf = PdfReader(io.BytesIO(reporte_pdf(p)))
    texto = " ".join(pg.extract_text() for pg in pdf.pages)
    assert len(pdf.pages) <= 5
    assert "Cinco riesgos principales" in texto and "Cambios derivados del PDF 2" in texto and "Roadmap actualizado" in texto

    # Ficha de contexto exportable: las 10 dimensiones, la evidencia y los ajustes del equipo.
    p.ajustes.append({"fecha": "2026-11-17 10:00", "texto": "Microsoft 365 es un servicio contratado."})
    texto = " ".join(pg.extract_text() for pg in PdfReader(io.BytesIO(ficha_pdf(p))).pages)
    assert "Ficha de contexto" in texto and "Recuperación" in texto and "Restricciones" in texto
    assert "Todos los equipos cuentan con antivirus Defender" in texto and "Microsoft 365 es un servicio contratado" in texto
    html = exportar.ficha_html(p)
    assert "Perfil de riesgo" in html and "Microsoft 365 es un servicio contratado" in html


def test_sin_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ErrorChatbot):
        Motor()
