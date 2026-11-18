"""Reintentos ante errores temporales de Claude, con un servidor HTTP local que imita la API (sin API real)."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import anthropic
import pytest

from chatbot import engine
from chatbot.engine import ErrorChatbot, Motor

RESPUESTA_OK = {
    "id": "msg_prueba", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
    "content": [{"type": "text", "text": json.dumps({"mensaje": "Entendido."})}],
    "stop_reason": "end_turn", "stop_sequence": None,
    "usage": {"input_tokens": 12, "output_tokens": 5, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 9000},
}
TIPO_ERROR = {529: "overloaded_error", 500: "api_error", 400: "invalid_request_error", 429: "rate_limit_error"}


def _servidor(fallos: int, codigo: int = 529, demoras: tuple[float, ...] = (), respuesta: dict | None = None):
    """Responde `codigo` las primeras `fallos` veces y luego 200; la llamada i tarda demoras[i] s.
    Devuelve (url, llamadas, cerrar). `llamadas` guarda el cuerpo JSON de cada solicitud."""
    llamadas = []

    class Manejador(BaseHTTPRequestHandler):
        def do_POST(self):
            llamadas.append(json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)))))
            if len(llamadas) <= len(demoras):
                time.sleep(demoras[len(llamadas) - 1])
            if len(llamadas) <= fallos:
                cuerpo, estado = {"type": "error", "error": {"type": TIPO_ERROR.get(codigo, "api_error"),
                                                             "message": "Overloaded"}}, codigo
            else:
                cuerpo, estado = respuesta or RESPUESTA_OK, 200
            datos = json.dumps(cuerpo).encode()
            self.send_response(estado)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(datos)))
            self.send_header("retry-after-ms", "10")  # que los reintentos de prueba no esperen segundos reales
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
    monkeypatch.setattr(anthropic._base_client, "INITIAL_RETRY_DELAY", 0.01)
    monkeypatch.setattr(anthropic._base_client, "MAX_RETRY_DELAY", 0.02)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(engine, "TIMEOUT_S", 0.5)


def _motor(url: str) -> Motor:
    return Motor(modelo="claude-sonnet-5-5", base_url=url)


def _llamada(motor: Motor) -> dict:
    return motor._llamar("# Tarea: prueba", [{"type": "text", "text": "hola"}], {"type": "object"}, etapa="Prueba")


INTENTOS = engine.REINTENTOS + 1


def test_saturacion_temporal_se_reintenta_y_funciona(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=2)
    try:
        datos = _llamada(_motor(url))
    finally:
        cerrar()
    assert datos["mensaje"] == "Entendido."
    assert len(llamadas) == 3  # 2 fallos + 1 éxito


def test_saturacion_persistente_muestra_mensaje_claro(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=99)
    try:
        with pytest.raises(ErrorChatbot, match="saturado"):
            _llamada(_motor(url))
    finally:
        cerrar()
    assert len(llamadas) == INTENTOS


def test_error_permanente_no_se_reintenta(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=99, codigo=400)
    try:
        with pytest.raises(ErrorChatbot):
            _llamada(_motor(url))
    finally:
        cerrar()
    assert len(llamadas) == 1


def test_respuesta_lenta_se_corta_y_se_reintenta(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=0, demoras=(1.5,))  # la primera pasa del límite
    try:
        datos = _llamada(_motor(url))
    finally:
        cerrar()
    assert datos["mensaje"] == "Entendido."
    assert len(llamadas) == 2


def test_respuesta_colgada_no_deja_cargando_para_siempre(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=0, demoras=(1.5,) * INTENTOS)
    inicio = time.time()
    try:
        with pytest.raises(ErrorChatbot, match="tardó"):
            _llamada(_motor(url))
    finally:
        cerrar()
    assert len(llamadas) == INTENTOS
    assert time.time() - inicio < INTENTOS * 0.5 + 2  # timeout de prueba 0.5 s por intento


def test_solicitud_cacheable_y_esquema_compatible(reintentos_rapidos):
    """Lo que realmente se envía: caché solo donde se reutiliza, sin minItems/maxItems y con reintento ante rechazos."""
    url, llamadas, cerrar = _servidor(fallos=0)
    motor = _motor(url)
    esquema = {"type": "object", "properties": {"x": {"type": "array", "items": {"type": "string"},
                                                       "minItems": 5, "maxItems": 5}}}
    contenido = [{"type": "text", "text": "documento", "cache_control": {"type": "ephemeral"}},
                 {"type": "text", "text": "hola"}]
    try:
        motor._llamar("# Tarea: prueba", contenido, esquema, etapa="Prueba", cachear=True)
        motor._llamar("# Tarea: prueba", contenido, esquema, etapa="Única")
    finally:
        cerrar()
    cuerpo, unica = llamadas
    assert cuerpo["system"][1]["cache_control"] == {"type": "ephemeral"}       # 5 min: lotes y consultas seguidas
    assert cuerpo["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in json.dumps(unica)                             # llamada única: no paga escritura
    assert "R8." in cuerpo["system"][0]["text"] and cuerpo["system"][1]["text"] == "# Tarea: prueba"
    assert "minItems" not in json.dumps(cuerpo["output_config"]["format"]["schema"])
    assert cuerpo["output_config"]["effort"] == "high" and "temperature" not in cuerpo
    assert cuerpo["fallbacks"] == "default"
    assert motor.consumo[0]["cache_leida"] == 9000 and motor.consumo[0]["etapa"] == "Prueba"


def test_rechazo_por_seguridad_se_informa(reintentos_rapidos):
    url, _, cerrar = _servidor(fallos=0, respuesta={**RESPUESTA_OK, "content": [], "stop_reason": "refusal",
                                                    "stop_details": {"type": "refusal", "category": "cyber",
                                                                     "explanation": ""}})
    try:
        with pytest.raises(ErrorChatbot, match="declinó"):
            _llamada(_motor(url))
    finally:
        cerrar()


def test_respuesta_cortada_por_longitud_se_informa(reintentos_rapidos):
    url, _, cerrar = _servidor(fallos=0, respuesta={**RESPUESTA_OK, "stop_reason": "max_tokens"})
    try:
        with pytest.raises(ErrorChatbot, match="se cortó"):
            _llamada(_motor(url))
    finally:
        cerrar()


def test_haiku_no_usa_fallback_y_razona_en_medium(reintentos_rapidos):
    url, llamadas, cerrar = _servidor(fallos=0)
    try:
        Motor(modelo="claude-haiku-5-5", base_url=url)._llamar("# Tarea", [{"type": "text", "text": "hola"}],
                                                                {"type": "object"})
    finally:
        cerrar()
    assert "fallbacks" not in llamadas[0]
    assert llamadas[0]["output_config"]["effort"] == "medium"   # en "high" agotaba el límite solo razonando


def _resolver(nodo, defs):
    if isinstance(nodo, dict):
        if "$ref" in nodo:
            return _resolver(defs[nodo["$ref"].split("/")[-1]], defs)
        return {k: _resolver(v, defs) for k, v in nodo.items() if k != "$defs"}
    if isinstance(nodo, list):
        return [_resolver(v, defs) for v in nodo]
    return nodo


def test_esquemas_compactados_conservan_todas_las_restricciones():
    """La ficha excedía el límite de gramática de la API ("compiled grammar is too large"). Los subesquemas
    repetidos van a $defs; al resolver las referencias debe quedar exactamente el mismo esquema."""
    from chatbot import controls, schemas
    from chatbot.engine import _esquema_para_api, _sin_restricciones_de_arreglo

    ids = controls.catalogo().ids_ig1()
    for esquema in (schemas.ficha(), schemas.reporte(), schemas.iniciativas_pdf2(), schemas.reporte_actualizado(),
                    schemas.evaluacion(ids[:5]), schemas.decisiones_faltantes(ids[:3])):
        compacto = _esquema_para_api(esquema)
        assert _resolver(compacto, compacto.get("$defs", {})) == _sin_restricciones_de_arreglo(esquema)
    ficha = _esquema_para_api(schemas.ficha())
    assert len(json.dumps(ficha)) < 0.5 * len(json.dumps(schemas.ficha()))   # las 10 dimensiones, definidas una vez
