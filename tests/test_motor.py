"""Flujo completo del agente con Gemini simulado: ficha → 56 → reporte → PDF 2 → v2, y exportación."""

import csv
import io
import re
import json
from types import SimpleNamespace

import openpyxl
import pytest
from pypdf import PdfReader

from chatbot import controls, engine, exportar
from chatbot.documentos import Documento
from chatbot.engine import ErrorChatbot, Motor
from chatbot.pdf_ejecutivo import reporte_ejecutivo_pdf
from chatbot.reporte_pdf import ficha_pdf, reporte_pdf
from chatbot.state import Proyecto, lotes_por_control
from tests.conftest import PAGINAS

FICHA = {
    "nombre_organizacion": "Comercial Ficticia", "resumen_contexto": "Comercio con 140 empleados.",
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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    # El catálogo de prueba (18 salvaguardas) cabe en un lote; con lotes de 6 se comprueba la caché entre lotes.
    monkeypatch.setattr(engine, "lotes_por_control", lambda: lotes_por_control(tamano_max=6))
    motor = Motor(modelo="claude-sonnet-5-5")
    llamadas = []

    def generar(**kw):
        llamadas.append(kw)
        sistema = " ".join(b["text"] for b in kw["system"])
        texto_usuario = " ".join(b.get("text", "") for b in kw["messages"][0]["content"])
        if "Etapa 2" in sistema:
            datos = FICHA
        elif "Etapa 3 —" in sistema:
            ids = texto_usuario.split("sin omitir ninguna): ")[1].split(", ")
            datos = _evaluacion([i.strip() for i in ids])
        elif "Etapa 5 —" in sistema and "quedaron sin decisión" in texto_usuario:
            # Segunda pasada: el esquema exige exactamente una decisión por cada salvaguarda que faltaba.
            datos = {"decisiones": [{"id": "5.1", "tipo": "sin_cambio", "estado_propuesto": "no_verificado",
                                     "motivo_sin_cambio": "sin_evidencia", "justificacion": "El PDF 2 no la documenta",
                                     "iniciativa": "MFA", "pagina": 0, "seccion": "", "cita": ""}]}
        elif "Etapa 5 —" in sistema:
            # Relaciona 6.1 y 5.1, pero solo decide sobre 6.1: la omisión de 5.1 debe quedar registrada (F1).
            datos = {"iniciativas": [{"nombre": "MFA", "que_mejoro": "MFA total", "salvaguardas": ["6.1", "5.1"],
                                      "alcance": "completa", "pendientes": [{"detalle": "Cuenta de GCP", "salvaguardas": []}],
                                      "riesgos_que_reduce": [], "evidencia": []}],
                     "decisiones": [{"id": "6.1", "tipo": "cambio_estado", "estado_propuesto": "implementado",
                                     "motivo_sin_cambio": "", "justificacion": "MFA", "iniciativa": "MFA",
                                     "pagina": 1, "seccion": "", "cita": "MFA para el 100% de los usuarios"}],
                     "alertas": ["El PDF 2 está fechado antes que el PDF 1."]}
        elif "Etapa 5.6" in sistema:
            base = _reporte()
            # El modelo "afirma" que los riesgos se redujeron: el sistema debe ignorarlo (F4, F5).
            datos = {"resumen_cambios": "MFA", "riesgos": [{"titulo": "R", "situacion": "reducido", "explicacion": ""}] * 5,
                     "iniciativas_estado": [{"titulo": "I", "estado": "completada", "explicacion": "x"}] * 5,
                     "riesgos_v2": [dict(base["riesgos"][0], titulo=f"Riesgo vigente {n}") for n in range(1, 6)],
                     "resumen_ejecutivo": base["resumen_ejecutivo"], "roadmap": base["iniciativas"]}
        elif "Etapas 3.5 y 4" in sistema:
            datos = _reporte()
        else:
            datos = {"mensaje": "Explicación del agente"}
        uso = SimpleNamespace(input_tokens=200, output_tokens=100, cache_creation_input_tokens=0,
                              cache_read_input_tokens=9000)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=json.dumps(datos))], stop_reason="end_turn",
                               model=kw["model"], usage=uso)

    cliente = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=generar)))
    cliente.with_options = lambda **_: cliente
    motor.client = cliente
    return motor, llamadas


def test_flujo_completo(motor_simulado):
    motor, llamadas = motor_simulado
    p = Proyecto()
    p.documentos["pdf1"] = Documento("pdf1", "caso", "texto", PAGINAS)

    assert "Centinela IG1" in llamadas[0]["system"][0]["text"] if motor.explain() else False

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
    assert "preguntas" not in llamadas[-1]["output_config"]["format"]["schema"]["properties"]  # sin preguntas Sí/No
    sistema = " ".join(b["text"] for b in llamadas[-1]["system"])
    assert "R8." in sistema and "Criterio de prueba 10.1" in sistema
    assert "Criterio de prueba 10.2" not in sistema                   # solo IG1
    # Ahorro de tokens: el bloque común es idéntico en todas las llamadas (caché) y los lotes de la evaluación
    # comparten documento + ficha cacheados; solo cambia la lista de salvaguardas, al final.
    assert len({c["system"][0]["text"] for c in llamadas}) == 1
    lotes = [c for c in llamadas if "Etapa 3 —" in c["system"][1]["text"]]
    assert len(lotes) > 1 and all(c["messages"][0]["content"][:2] == lotes[0]["messages"][0]["content"][:2] for c in lotes)
    assert lotes[0]["messages"][0]["content"][1]["cache_control"] == {"type": "ephemeral"}
    # El esquema es parte del prefijo cacheado: debe ser el mismo en todos los lotes (si no, la caché no se lee).
    assert all(c["output_config"] == lotes[0]["output_config"] for c in lotes)
    assert "[Página 1]" in lotes[0]["messages"][0]["content"][0]["text"]  # texto paginado, no el PDF
    assert '"cita"' not in lotes[0]["messages"][0]["content"][1]["text"]  # ficha resumida: sin citas repetidas

    motor.report(p)
    assert p.v1.cerrada
    assert all("10.1" not in r["salvaguardas"] for r in p.v1.reporte["riesgos"])   # 10.1 está implementada
    assert [i["prioridad"] for i in p.v1.reporte["iniciativas"]] == [1, 2, 3, 4, 5]

    p.documentos["pdf2"] = Documento("pdf2", "avance", "texto", ["Se activó MFA para el 100% de los usuarios de correo."])
    motor.analyze_initiatives(p)
    assert p.cambios[0].cita_verificada and p.cambios[0].tipo == "estado"
    # F1: 5.1 quedó sin decisión en la primera pasada; la segunda la obtuvo con su motivo.
    assert [(x["id"], x["motivo"]) for x in p.sin_cambio] == [("5.1", "sin_evidencia")]
    assert any("segunda pasada" in a for a in p.avisos)
    segunda = llamadas[-1]
    assert segunda["output_config"]["format"]["schema"]["properties"]["decisiones"]["items"]["properties"]["id"]["enum"] == ["5.1"]
    assert segunda["messages"][0]["content"][:2] == llamadas[-2]["messages"][0]["content"][:2]  # mismo prefijo cacheado
    assert p.alertas == ["El PDF 2 está fechado antes que el PDF 1."]                                   # C2
    p.decidir("6.1", "aprobado")
    p.crear_v2()
    rep = motor.updated_report(p)
    assert p.etapa == "actualizado"
    # Situación calculada por el sistema: los riesgos solo usan 11.1, que no cambió → permanece (no "reducido").
    assert all(r["situacion"] == "permanece" and r["severidad_residual"] == "alta" for r in rep["riesgos"])
    assert all(e["estado"] == "pendiente" for e in rep["iniciativas_estado"])        # 11.1 sigue sin implementar
    assert [r["titulo"] for r in rep["riesgos_v2"]] == [f"Riesgo vigente {n}" for n in range(1, 6)]  # F7
    instruccion = llamadas[-1]["messages"][0]["content"][0]["text"]
    assert "CALCULADA por el sistema" in instruccion and "NO aprobados" in instruccion
    assert p.v1.matriz["6.1"].estado == "no_verificado" and p.v2.matriz["6.1"].estado == "implementado"

    # Exportación por versión: lo inicial (v1) y lo final (v2) nunca se mezclan.
    inicial = openpyxl.load_workbook(io.BytesIO(exportar.excel(p, "v1")))
    final = openpyxl.load_workbook(io.BytesIO(exportar.excel(p, "v2")))
    assert {"Contexto", "Matriz v1", "Indicadores", "Riesgos v1", "Roadmap v1"} <= set(inicial.sheetnames)
    assert not {"Matriz v2", "Roadmap v2", "Cambios PDF 2", "Riesgos v2"} & set(inicial.sheetnames)
    assert {"Contexto", "Matriz v2", "Indicadores", "Riesgos v2", "Roadmap v2", "Cambios PDF 2"} <= set(final.sheetnames)
    assert not {"Matriz v1", "Roadmap v1", "Riesgos v1"} & set(final.sheetnames)
    assert inicial["Matriz v1"].max_row == final["Matriz v2"].max_row == len(ids) + 1
    estado_6_1 = {n: next(r[4].value for r in libro[f"Matriz {v}"].iter_rows(min_row=2) if r[0].value == "6.1")
                  for n, libro, v in (("v1", inicial, "v1"), ("v2", final, "v2"))}
    assert estado_6_1 == {"v1": "No verificado", "v2": "Implementado"}             # matrices distintas
    assert final["Indicadores"].max_row == 3 and inicial["Indicadores"].max_row == 2  # v2 se compara con v1
    filas = list(csv.reader(io.StringIO(exportar.csv_matriz(p, p.v2).decode("utf-8-sig"))))
    assert len(filas) == len(ids) + 1 and filas[0][0] == "ID CIS"
    html_v1, html_v2 = exportar.reporte_html(p, "v1"), exportar.reporte_html(p, "v2")
    assert "Reporte técnico inicial" in html_v1 and "Cambios derivados del PDF 2" not in html_v1
    assert "Reporte técnico final" in html_v2 and "Cambios derivados del PDF 2" in html_v2 and "Roadmap actualizado" in html_v2
    assert "R12." in exportar.prompt_maestro_md()

    # Reportes técnicos en PDF: uno por versión, completos (con su matriz) y sin límite de páginas.
    pdf_v1, pdf_v2 = (PdfReader(io.BytesIO(reporte_pdf(p, v))) for v in ("v1", "v2"))
    t1, t2 = (" ".join(pg.extract_text() for pg in d.pages) for d in (pdf_v1, pdf_v2))
    assert "Reporte técnico inicial" in t1 and "Cinco riesgos principales" in t1 and "Cambios derivados del PDF 2" not in t1
    assert "Reporte técnico final" in t2 and "Cambios derivados del PDF 2" in t2 and "Roadmap actualizado" in t2
    assert "Cinco riesgos principales" not in t2
    assert "Matriz de las 56 salvaguardas · v1" in t1 and "Matriz de las 56 salvaguardas · v2" in t2
    assert "Matriz de las 56 salvaguardas · v1" not in t2  # la v2 no repite la matriz v1

    # Reportes ejecutivos en PDF: 2-3 páginas (cumplen el límite de 5 de la actividad), sin ids de CIS.
    for cual in ("v1", "v2"):
        lector = PdfReader(io.BytesIO(reporte_ejecutivo_pdf(p, cual)))
        texto = " ".join(pg.extract_text() for pg in lector.pages)
        assert len(lector.pages) <= 3
        assert ("Reporte ejecutivo inicial" if cual == "v1" else "Reporte ejecutivo final") in texto
        assert "Estado por control" in texto and "Plan" in texto and "Lo que necesitamos de ustedes" in texto
        assert "estimación" in texto or "Esta evaluación se generó antes" in texto
        assert not re.search(r"(?<![\d.])\d{1,2}\.\d{1,2}(?![\d%])", texto.replace("v8.1", "")), "ids de CIS en el ejecutivo"
    assert "desde la evaluación inicial" in " ".join(pg.extract_text() for pg in PdfReader(io.BytesIO(reporte_ejecutivo_pdf(p, "v2"))).pages)

    # Ficha de contexto exportable: las 10 dimensiones, la evidencia y los ajustes del equipo.
    p.ajustes.append({"fecha": "2026-11-17 10:00", "texto": "Microsoft 365 es un servicio contratado."})
    texto = " ".join(pg.extract_text() for pg in PdfReader(io.BytesIO(ficha_pdf(p))).pages)
    assert "Ficha de contexto" in texto and "Recuperación" in texto and "Restricciones" in texto
    assert "Todos los equipos cuentan con antivirus Defender" in texto and "Microsoft 365 es un servicio contratado" in texto
    html = exportar.ficha_html(p)
    assert "Perfil de riesgo" in html and "Microsoft 365 es un servicio contratado" in html


def test_sin_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    with pytest.raises(ErrorChatbot):
        Motor()
