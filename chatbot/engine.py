"""Llamadas a la API de Gemini (SDK oficial google-genai).

- analyze(): primer análisis del contexto de la empresa.
- follow_up(): mensajes libres posteriores (con el estado actual adjunto).
- report(): reporte final (llamada independiente, sin historial).

Todas las salidas usan salida estructurada (JSON Schema), así que nunca se
parsea texto libre.
"""

import json
import os

from google import genai
from google.genai import errors, types

from . import prompts, schemas
from .state import Evaluacion

MODELO_POR_DEFECTO = "gemini-3.5-flash-lite"


class ErrorChatbot(Exception):
    """Error presentable al usuario."""


class Motor:
    def __init__(self, modelo: str | None = None):
        self.modelo = modelo or os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ErrorChatbot("Falta GEMINI_API_KEY en el archivo .env")
        self.client = genai.Client(api_key=api_key)
        self.historial: list[dict] = []  # conversación de análisis (solo se agrega, nunca se edita)

    # ------------------------------------------------------------------ util
    def _llamar(self, system: str, contents: list[dict], schema: dict) -> tuple[str, dict]:
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema,
            temperature=0.3,
        )
        try:
            resp = self.client.models.generate_content(model=self.modelo, contents=contents, config=config)
        except errors.ClientError as e:
            if e.code == 429:
                raise ErrorChatbot("Se alcanzó el límite gratuito de Gemini (por minuto o por día). "
                                   "Espera un momento y reintenta.") from e
            if e.code in (400, 403) and "API key" in str(e):
                raise ErrorChatbot("API key inválida. Revisa GEMINI_API_KEY en tu archivo .env.") from e
            if e.code == 404:
                raise ErrorChatbot(f"El modelo '{self.modelo}' no existe o no está disponible. "
                                   "Cambia GEMINI_MODEL en .env.") from e
            raise ErrorChatbot(f"Gemini rechazó la solicitud ({e.code}): {e.message}") from e
        except errors.ServerError as e:
            raise ErrorChatbot(f"Error del servidor de Gemini ({e.code}). Reintenta en unos segundos.") from e
        except errors.APIError as e:
            raise ErrorChatbot(f"Error de la API de Gemini: {e.message}") from e
        except OSError as e:
            raise ErrorChatbot("No se pudo conectar con la API de Gemini. Revisa tu conexión.") from e

        if resp.prompt_feedback and resp.prompt_feedback.block_reason:
            raise ErrorChatbot("Gemini bloqueó el mensaje por sus filtros de seguridad. Reformúlalo e inténtalo de nuevo.")
        texto = resp.text
        if not texto:
            motivo = resp.candidates[0].finish_reason if resp.candidates else "desconocido"
            raise ErrorChatbot(f"Gemini no devolvió contenido (motivo: {motivo}).")
        try:
            return texto, json.loads(texto)
        except json.JSONDecodeError as e:
            raise ErrorChatbot("La respuesta de Gemini se cortó o no es JSON válido. Reintenta.") from e

    # ------------------------------------------------------------- análisis
    def analyze(self, contexto: str, evaluacion: Evaluacion) -> dict:
        evaluacion.contexto_empresa = contexto
        return self._turno(f"Contexto de la empresa, descrito por su responsable de ciberseguridad:\n\n{contexto}",
                           evaluacion, fuente="analisis")

    def follow_up(self, mensaje: str, evaluacion: Evaluacion) -> dict:
        evaluacion.contexto_empresa += f"\n\nInformación adicional: {mensaje}"
        estado = json.dumps(evaluacion.como_json(), ensure_ascii=False)
        pendientes = [p.control_id for p in evaluacion.preguntas_pendientes]
        contenido = (
            f"Estado actual de los controles (incluye respuestas Sí/No ya dadas): {estado}\n"
            f"Controles con pregunta pendiente: {pendientes}\n\n"
            f"Nuevo mensaje del responsable:\n{mensaje}"
        )
        return self._turno(contenido, evaluacion, fuente="seguimiento")

    def _turno(self, contenido: str, evaluacion: Evaluacion, fuente: str) -> dict:
        mensajes = self.historial + [{"role": "user", "parts": [{"text": contenido}]}]
        texto, datos = self._llamar(prompts.SYSTEM_ANALISIS, mensajes, schemas.ANALISIS)
        self.historial = mensajes + [{"role": "model", "parts": [{"text": texto}]}]
        datos["avisos"] = evaluacion.aplicar_actualizaciones(datos.get("actualizaciones", []), fuente)
        evaluacion.encolar_preguntas(datos.get("preguntas_cerradas", []))
        datos.setdefault("mensaje", "")
        return datos

    # --------------------------------------------------------------- reporte
    def report(self, evaluacion: Evaluacion) -> dict:
        contenido = (
            f"Contexto de la empresa:\n{evaluacion.contexto_empresa}\n\n"
            f"Estado final de los controles:\n{json.dumps(evaluacion.como_json(), ensure_ascii=False, indent=1)}\n\n"
            f"Cobertura estimada: {evaluacion.porcentaje_cobertura()}%"
        )
        _, datos = self._llamar(prompts.SYSTEM_REPORTE, [{"role": "user", "parts": [{"text": contenido}]}], schemas.REPORTE)
        for clave in ("riesgos_principales", "quick_wins", "recomendaciones"):
            datos.setdefault(clave, [])
        datos.setdefault("resumen_ejecutivo", "")
        return datos
