"""Pruebas de la lógica sin llamar a la API (el cliente de Gemini se simula)."""

import json
from types import SimpleNamespace

from chatbot.controls import CONTROLES
from chatbot.engine import Motor
from chatbot.state import Evaluacion


def test_estado_inicial_todo_desconocido():
    ev = Evaluacion()
    assert ev.resumen()["desconocido"] == len(CONTROLES)
    assert ev.porcentaje_cobertura() == 0


def test_valida_ids_y_estados():
    ev = Evaluacion()
    avisos = ev.aplicar_actualizaciones([
        {"control_id": "BCK-01", "estado": "cubierto", "justificacion": "Respaldos diarios"},
        {"control_id": "XXX-99", "estado": "cubierto", "justificacion": ""},
        {"control_id": "MAL-01", "estado": "tal_vez", "justificacion": ""},
    ], "analisis")
    assert ev.controles["BCK-01"].estado == "cubierto"
    assert len(avisos) == 2


def test_cola_cubre_todos_los_desconocidos_y_si_no():
    ev = Evaluacion()
    ev.aplicar_actualizaciones([{"control_id": "BCK-01", "estado": "cubierto", "justificacion": "x"}], "analisis")
    ev.encolar_preguntas([{"control_id": "IAM-03", "pregunta": "¿Usan MFA en Microsoft 365?"}])
    assert ev.preguntas_pendientes[0].pregunta == "¿Usan MFA en Microsoft 365?"
    assert len(ev.preguntas_pendientes) == len(CONTROLES) - 1  # todos menos BCK-01

    ev.responder(True)
    assert ev.controles["IAM-03"].estado == "cubierto"
    ev.responder(False)
    assert ev.controles[ev.preguntas_pendientes[0].control_id].estado == "desconocido"
    assert ev.resumen()["no_cubierto"] == 1


def _respuesta_falsa(payload: dict):
    return SimpleNamespace(text=json.dumps(payload), prompt_feedback=None, candidates=[])


def test_motor_con_cliente_simulado(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    motor = Motor()
    llamadas = []

    def generar(**kwargs):
        llamadas.append(kwargs)
        return _respuesta_falsa({
            "mensaje": "Entendido.",
            "actualizaciones": [{"control_id": "MAL-01", "estado": "cubierto", "justificacion": "Usan EDR"}],
            "preguntas_cerradas": [{"control_id": "BCK-01", "pregunta": "¿Tienen respaldo offline?"}],
        })

    monkeypatch.setattr(motor.client.models, "generate_content", generar)
    ev = Evaluacion()
    datos = motor.analyze("Somos una pyme de 50 personas con EDR en todos los equipos.", ev)

    assert datos["mensaje"] == "Entendido."
    assert ev.controles["MAL-01"].estado == "cubierto"
    assert ev.pregunta_actual().control_id == "BCK-01"
    cfg = llamadas[0]["config"]
    assert cfg.response_mime_type == "application/json" and cfg.response_json_schema
    assert motor.historial[-1]["role"] == "model"

    motor.follow_up("También tenemos firewall.", ev)
    # Historial append-only: el segundo request extiende el primero sin editarlo.
    assert llamadas[1]["contents"][:2] == llamadas[0]["contents"] + [motor.historial[1]]


def test_sin_api_key(monkeypatch):
    import pytest
    from chatbot.engine import ErrorChatbot
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ErrorChatbot):
        Motor()
