"""Reintentos ante errores temporales de Gemini, con un servidor HTTP local simulado (sin API real)."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from chatbot import engine
from chatbot.engine import ErrorChatbot, Motor

RESPUESTA_OK = {
    "candidates": [{
        "content": {"role": "model", "parts": [{"text": json.dumps({
            "mensaje": "Entendido.", "actualizaciones": [], "preguntas_cerradas": []})}]},
        "finishReason": "STOP",
    }]
}
ERROR_503 = {"error": {"code": 503, "status": "UNAVAILABLE", "message": "This model is currently experiencing high demand."}}


def _servidor(fallos: int, codigo: int = 503, demoras: tuple[float, ...] = ()):
    """Responde `codigo` las primeras `fallos` veces y luego 200; la llamada i tarda demoras[i] s.
    Devuelve (url, llamadas, cerrar)."""
    llamadas = []

    class Manejador(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            llamadas.append(self.path)
            if len(llamadas) <= len(demoras):
                time.sleep(demoras[len(llamadas) - 1])
            if len(llamadas) <= fallos:
                cuerpo, estado = {**ERROR_503, "error": {**ERROR_503["error"], "code": codigo}}, codigo
            else:
                cuerpo, estado = RESPUESTA_OK, 200
            datos = json.dumps(cuerpo).encode()
            self.send_response(estado)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            try:
                self.wfile.write(datos)
            except OSError:  # el cliente ya cortó por timeout
                pass

        def log_message(self, *args):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_port}", llamadas, srv.shutdown


@pytest.fixture
def reintentos_rapidos(monkeypatch):
    """Mismas reglas de reintento, pero sin esperar segundos reales."""
    rapido = engine.REINTENTOS.model_copy(update={"initial_delay": 0.01, "max_delay": 0.02, "jitter": 0})
    monkeypatch.setattr(engine, "REINTENTOS", rapido)
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setattr(engine, "TIMEOUT_S", 0.5)


def _llamada(url: str) -> dict:
    return Motor(base_url=url)._llamar("sistema", [{"text": "hola"}], {"type": "object"})


def test_503_temporal_se_reintenta_y_funciona(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=2)
    try:
        datos = _llamada(url)
    finally:
        cerrar()
    assert datos["mensaje"] == "Entendido."
    assert len(llamadas) == 3  # 2 fallos + 1 éxito


def test_503_persistente_muestra_mensaje_claro(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=99)
    try:
        with pytest.raises(ErrorChatbot, match="saturado"):
            _llamada(url)
    finally:
        cerrar()
    assert len(llamadas) == engine.REINTENTOS.attempts


def test_error_permanente_no_se_reintenta(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=99, codigo=400)
    try:
        with pytest.raises(ErrorChatbot):
            _llamada(url)
    finally:
        cerrar()
    assert len(llamadas) == 1


def test_respuesta_lenta_se_corta_y_se_reintenta(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=0, demoras=(1.5,))  # la primera pasa del límite
    try:
        datos = _llamada(url)
    finally:
        cerrar()
    assert datos["mensaje"] == "Entendido."
    assert len(llamadas) == 2


def test_respuesta_colgada_no_deja_cargando_para_siempre(reintentos_rapidos):
    intentos = engine.REINTENTOS.attempts
    url, llamadas, cerrar = _servidor(fallos=0, demoras=(1.5,) * intentos)
    inicio = time.time()
    try:
        with pytest.raises(ErrorChatbot, match="tardó"):
            _llamada(url)
    finally:
        cerrar()
    assert len(llamadas) == intentos
    assert time.time() - inicio < intentos * 0.5 + 2  # timeout de prueba 0.5 s por intento
