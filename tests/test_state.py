"""Reglas del agente que se hacen cumplir en Python (sin llamar a la API).

Cada prueba apunta a una penalización de la actividad M3.6: omitir salvaguardas, inventar
evidencias, declarar incumplimiento por falta de información, cambiar puntuaciones sin
justificación, perder el diagnóstico inicial o contradecir matriz e indicadores.
"""

import pytest

from chatbot import almacen, controls
from chatbot.documentos import Documento, verificar_cita
from chatbot.state import (Proyecto, Resultado, citas_repetidas, estado_iniciativas, indicadores, lotes_por_control,
                           normalizar_ficha, situacion_riesgos, validar_reporte, validar_resultado)
from tests.conftest import PAGINAS


@pytest.fixture
def doc():
    return Documento("pdf1", "caso.pdf", "pdf", PAGINAS)


def _proyecto(doc) -> Proyecto:
    p = Proyecto()
    p.documentos["pdf1"] = doc
    p.iniciar_v1()
    return p


# ----------------------------------------------------------- citas (R3, R6)
def test_cita_exacta_tolerante_y_pagina_corregida(doc):
    assert verificar_cita(doc, "Todos los equipos cuentan con antivirus Defender", 1) == 1
    assert verificar_cita(doc, "todos los   EQUIPOS cuentan con antivirus defender.", None) == 1  # mayúsculas/espacios
    assert verificar_cita(doc, "El ERP se respalda diariamente a un NAS", 1) == 2               # página corregida
    assert verificar_cita(doc, "Cuentan con MFA para todos los usuarios", 1) is None              # inventada


def test_estado_sin_cita_valida_queda_no_verificado(doc):
    r, avisos = validar_resultado({"id": "10.1", "estado": "implementado", "aplicabilidad": "aplica",
                                   "justificacion": "Tienen EDR", "cita": "EDR CrowdStrike en servidores", "pagina": 1}, doc)
    assert r.estado == "no_verificado" and r.cita == "" and avisos


def test_no_implementado_sin_evidencia_no_es_incumplimiento(doc):
    """R8: ausencia de evidencia ≠ incumplimiento confirmado."""
    r, _ = validar_resultado({"id": "7.1", "estado": "no_implementado", "aplicabilidad": "aplica",
                              "justificacion": "No se menciona", "cita": ""}, doc)
    assert r.estado == "no_verificado"
    r2, _ = validar_resultado({"id": "17.1", "estado": "no_implementado", "aplicabilidad": "aplica",
                               "justificacion": "Sin plan", "cita": "No existe un plan de respuesta a incidentes", "pagina": 2}, doc)
    assert r2.estado == "no_implementado" and r2.fuente == "pdf1" and r2.pagina == 2


def test_no_aplicable_requiere_justificacion_y_cita(doc):
    r, _ = validar_resultado({"id": "12.1", "estado": "no_aplicable", "aplicabilidad": "no_aplica",
                              "justificacion": "No", "cita": "Empresa ficticia de comercio con 140 empleados", "pagina": 1}, doc)
    assert r.estado == "no_verificado"
    r2, _ = validar_resultado({"id": "12.1", "estado": "no_aplicable", "aplicabilidad": "aplica",
                               "justificacion": "La empresa no opera infraestructura de red propia según el documento.",
                               "cita": "Empresa ficticia de comercio con 140 empleados", "pagina": 1}, doc)
    assert r2.estado == "no_aplicable" and r2.aplicabilidad == "no_aplica"


# --------------------------------------------------- completitud de la matriz
def test_matriz_siempre_completa_aunque_el_modelo_omita(doc):
    p = _proyecto(doc)
    p.aplicar_lote([{"id": "10.1", "estado": "implementado", "aplicabilidad": "aplica", "justificacion": "Antivirus",
                     "cita": "Todos los equipos cuentan con antivirus Defender", "pagina": 1}], doc)
    p.completar_faltantes(controls.catalogo().ids_ig1())
    assert len(p.v1.matriz) == len(controls.catalogo().ids_ig1())
    assert all(r.justificacion for r in p.v1.matriz.values())
    assert p.v1.matriz["10.1"].estado == "implementado"
    assert p.v1.matriz["1.1"].estado == "no_verificado"


def test_lotes_cubren_todas_las_salvaguardas_sin_partir_controles():
    lotes = lotes_por_control(tamano_max=5)
    assert sum(lotes, []) == controls.catalogo().ids_ig1()


# ------------------------------------------------------------- indicadores
def test_formulas_de_la_actividad():
    m = {f"{i}.1": Resultado(f"{i}.1") for i in range(1, 11)}
    for sid, est in [("1.1", "implementado"), ("2.1", "implementado"), ("3.1", "parcial"), ("4.1", "no_implementado"),
                     ("5.1", "no_aplicable")]:
        m[sid].estado = est
    i = indicadores(m)
    assert (i["implementado"], i["parcial"], i["no_implementado"], i["no_verificado"], i["no_aplicable"]) == (2, 1, 1, 5, 1)
    assert i["implementacion"] == round(100 * (2 + 0.5) / 4, 1)   # 62.5
    assert i["cobertura"] == round(100 * 4 / (10 - 1), 1)          # 44.4


def test_implementacion_no_determinable_sin_evaluables():
    i = indicadores({"1.1": Resultado("1.1")})
    assert i["implementacion"] is None and i["cobertura"] == 0.0


# ---------------------------------------------- línea base y PDF 2 (R10-R12)
def _con_v1_cerrada(doc) -> Proyecto:
    p = _proyecto(doc)
    p.v1.matriz["10.1"] = Resultado("10.1", "parcial", "aplica", "Solo PCs", "pdf1", 1, "", "antivirus Defender")
    p.cerrar_v1({"riesgos": [], "iniciativas": []})
    p.documentos["pdf2"] = Documento("pdf2", "avance.pdf", "pdf",
                                     ["Iniciativa 1. Se implementó MFA para el 100% de los usuarios de correo."])
    return p


def test_v1_queda_fija_al_cerrarse(doc):
    p = _con_v1_cerrada(doc)
    with pytest.raises(ValueError):
        p.aplicar_lote([{"id": "1.1", "estado": "implementado"}], doc)


def test_cambios_requieren_cita_y_aprobacion(doc):
    p = _con_v1_cerrada(doc)
    p.registrar_cambios([
        {"id": "6.1", "estado_propuesto": "implementado", "justificacion": "MFA total", "iniciativa": "MFA",
         "cita": "Se implementó MFA para el 100% de los usuarios de correo", "pagina": 1},
        {"id": "11.1", "estado_propuesto": "implementado", "justificacion": "Respaldo en nube", "iniciativa": "Respaldo",
         "cita": "Se configuró un respaldo inmutable en la nube", "pagina": 1},
    ], p.documentos["pdf2"])
    assert [c.cita_verificada for c in p.cambios] == [True, False]
    with pytest.raises(ValueError):
        p.decidir("11.1", "aprobado")  # sin evidencia verificable no se puede aprobar
    p.decidir("6.1", "aprobado")
    modificados = p.crear_v2()
    assert modificados == ["6.1"]
    assert p.v2.matriz["6.1"].estado == "implementado" and p.v2.matriz["6.1"].fuente == "pdf2"
    assert p.v1.matriz["6.1"].estado == "no_verificado"  # la línea base no cambió
    assert p.v2.matriz["11.1"].estado == p.v1.matriz["11.1"].estado
    assert sum(1 for s in p.v1.matriz if p.v1.matriz[s].estado != p.v2.matriz[s].estado) == 1  # R11


def test_cambios_pendientes_o_rechazados_no_modifican(doc):
    p = _con_v1_cerrada(doc)
    p.registrar_cambios([{"id": "6.1", "estado_propuesto": "implementado", "justificacion": "MFA", "iniciativa": "MFA",
                          "cita": "Se implementó MFA para el 100% de los usuarios de correo", "pagina": 1}], p.documentos["pdf2"])
    p.decidir("6.1", "rechazado")
    assert p.crear_v2() == []
    assert p.v2.indicadores() == p.v1.indicadores()


# ------------------------------------------- coherencia matriz ↔ reporte
def test_reporte_no_asocia_riesgos_a_salvaguardas_implementadas(doc):
    p = _proyecto(doc)
    p.v1.matriz["10.1"].estado = "implementado"
    p.v1.matriz["11.1"].estado = "no_implementado"
    rep = {"riesgos": [{"titulo": "Ransomware", "salvaguardas": ["10.1", "11.1"]}],
           "iniciativas": [{"titulo": "B", "prioridad": 2, "riesgos": [1, 9], "salvaguardas": ["10.1"]},
                           {"titulo": "A", "prioridad": 1, "riesgos": [1], "salvaguardas": ["11.1"]}],
           "resumen_ejecutivo": {"controles_mayores_brechas": [{"control_id": "CIS-04", "explicacion": "x"},
                                                               {"control_id": "CIS-11", "explicacion": "Sin respaldo aislado"}]}}
    avisos = validar_reporte(rep, p.v1.matriz, ["CIS-11"])
    assert rep["riesgos"][0]["salvaguardas"] == ["11.1"] and avisos
    assert [i["titulo"] for i in rep["iniciativas"]] == ["A", "B"] and rep["iniciativas"][1]["riesgos"] == [1]
    assert rep["resumen_ejecutivo"]["controles_mayores_brechas"] == [{"control_id": "CIS-11", "explicacion": "Sin respaldo aislado"}]


# ------------------------------------------------------------ persistencia
def test_guardar_y_cargar_conserva_ambas_versiones(doc, tmp_path, monkeypatch):
    monkeypatch.setattr(almacen, "CARPETA", tmp_path)
    p = _con_v1_cerrada(doc)
    p.registrar_cambios([{"id": "6.1", "estado_propuesto": "implementado", "justificacion": "MFA", "iniciativa": "MFA",
                          "cita": "Se implementó MFA para el 100% de los usuarios de correo", "pagina": 1}], p.documentos["pdf2"])
    p.decidir("6.1", "aprobado")
    p.crear_v2()
    p.modelo = "claude-haiku-5-5"
    almacen.guardar(p)
    q = almacen.cargar(p.id)
    assert q.modelo == "claude-haiku-5-5"  # el modelo de la evaluación se conserva
    assert q.v1.indicadores() == p.v1.indicadores() and q.v2.indicadores() == p.v2.indicadores()
    assert q.v1.cerrada and q.cambios[0].decision == "aprobado" and q.etapa == "iniciativas"
    assert [g["id"] for g in almacen.listar()] == [p.id]


def test_respuestas_si_no_guardadas_se_descartan_al_cargar(doc):
    """Evaluaciones antiguas: una respuesta Sí/No no es evidencia documental y no cuenta."""
    p = _proyecto(doc)
    p.v1.matriz["1.1"] = Resultado("1.1", "implementado", "aplica", "El responsable declaró que sí.", "declaracion")
    datos = p.a_dict()
    datos["chat"] = [{"tipo": "respuesta", "id": "1.1", "respuesta": "si"}]
    datos["preguntas_pendientes"], datos["preguntas_hechas"] = [{"id": "2.1", "pregunta": "¿?"}], ["1.1", "2.1"]
    q = Proyecto.de_dict(datos)
    assert q.v1.matriz["1.1"].estado == "no_verificado" and q.v1.matriz["1.1"].fuente == ""
    assert q.chat == [] and q.avisos


# ------------------------------------- Etapa 5.6: situación calculada con reglas fijas (F4, F5, F6)
def _matrices(**v2):
    v1 = {f"{i}.1": Resultado(f"{i}.1", "no_implementado", "aplica") for i in range(1, 6)}
    nueva = {k: Resultado(k, v2.get(k.replace(".", "_"), r.estado), "aplica") for k, r in v1.items()}
    return v1, nueva


def test_riesgo_mitigado_reducido_o_permanece_segun_sus_salvaguardas():
    v1, v2 = _matrices(**{"1_1": "implementado", "2_1": "implementado", "3_1": "parcial"})
    riesgos = [{"salvaguardas": ["1.1", "2.1"], "severidad": "alta"},   # todas implementadas
               {"salvaguardas": ["3.1", "4.1"], "severidad": "alta"},   # una mejoró
               {"salvaguardas": ["4.1", "5.1"], "severidad": "media"}]  # ninguna mejoró (aunque otras sí)
    sit = situacion_riesgos(riesgos, v1, v2)
    assert [(s["situacion"], s["severidad_residual"]) for s in sit] == [("mitigado", "baja"), ("reducido", "media"),
                                                                         ("permanece", "media")]
    assert sit[1]["mejoradas"] == ["3.1"] and sit[1]["pendientes"] == ["3.1", "4.1"]


def test_iniciativa_completada_solo_si_todas_sus_salvaguardas_estan_implementadas():
    v1, v2 = _matrices(**{"1_1": "implementado", "2_1": "parcial"})
    est = estado_iniciativas([{"salvaguardas": ["1.1"]}, {"salvaguardas": ["1.1", "2.1"]}, {"salvaguardas": ["3.1"]}], v1, v2)
    assert [e["estado"] for e in est] == ["completada", "en_progreso", "pendiente"]


# ------------------------------------------- Etapa 5: decisiones por salvaguarda (F1, F9, C4)
def test_actualizacion_de_evidencia_conserva_el_estado(doc):
    p = _con_v1_cerrada(doc)
    p.registrar_cambios([{"id": "10.1", "tipo": "actualizar_evidencia", "estado_propuesto": "parcial",
                          "justificacion": "Cobertura MFA al 100%", "iniciativa": "MFA",
                          "cita": "Se implementó MFA para el 100% de los usuarios de correo", "pagina": 1}], p.documentos["pdf2"])
    c = p.cambios[0]
    assert c.tipo == "evidencia" and c.aprobable
    p.decidir("10.1", "aprobado")
    assert p.crear_v2() == []                                    # no cuenta como cambio de estado
    assert p.v2.matriz["10.1"].estado == "parcial" and p.v2.matriz["10.1"].fuente == "pdf2"
    assert p.v1.matriz["10.1"].cita == "antivirus Defender"       # la v1 no se toca


def test_empeoramiento_documentado_se_puede_proponer(doc):
    p = _con_v1_cerrada(doc)
    p.v1.matriz["6.1"].estado = "implementado"
    p.registrar_cambios([{"id": "6.1", "tipo": "cambio_estado", "estado_propuesto": "parcial", "justificacion": "Solo correo",
                          "iniciativa": "MFA", "cita": "Se implementó MFA para el 100% de los usuarios de correo",
                          "pagina": 1}], p.documentos["pdf2"])
    p.decidir("6.1", "aprobado")
    assert p.crear_v2() == ["6.1"] and p.v2.matriz["6.1"].estado == "parcial"


def test_salvaguarda_relacionada_sin_decision_queda_registrada(doc):
    p = _con_v1_cerrada(doc)
    p.registrar_cambios([{"id": "2.1", "tipo": "sin_cambio", "motivo_sin_cambio": "pendiente_declarado",
                          "justificacion": "Falta el inventario de software", "iniciativa": "B"}],
                        p.documentos["pdf2"], relacionadas=["2.1", "3.1"])
    assert [(x["id"], x["motivo"]) for x in p.sin_cambio] == [("2.1", "pendiente_declarado"), ("3.1", "sin_decision")]
    assert any("3.1" in a and "no emitió decisión" in a for a in p.avisos)


# ------------------------------------------------------ validaciones del reporte (F10, B1, A2, D5)
def test_explicacion_vacia_de_brecha_se_completa_con_la_matriz(doc):
    p = _proyecto(doc)
    p.v1.matriz["7.1"].estado = "no_implementado"
    rep = {"riesgos": [{"titulo": "Solo incertidumbre", "descripcion": "d", "consecuencia": "c", "justificacion": "j",
                        "salvaguardas": ["1.1"]}],
           "iniciativas": [], "resumen_ejecutivo": {"controles_mayores_brechas": [{"control_id": "CIS-07", "explicacion": ""}]}}
    avisos = validar_reporte(rep, p.v1.matriz, ["CIS-07"])
    assert "7.1" in rep["resumen_ejecutivo"]["controles_mayores_brechas"][0]["explicacion"]
    assert any("solo en salvaguardas No verificado" in a for a in avisos)          # B1


def test_cita_repetida_entre_salvaguardas_se_senala():
    m = {"8.1": Resultado("8.1", "parcial", cita="Procedimiento de incidentes"),
         "17.1": Resultado("17.1", "parcial", cita="procedimiento de  incidentes"), "1.1": Resultado("1.1")}
    assert len(citas_repetidas(m)) == 1 and "8.1, 17.1" in citas_repetidas(m)[0]


def test_ficha_antigua_se_normaliza():
    assert normalizar_ficha({"resumen_ejecutivo": "x"}) == {"resumen_contexto": "x"}
