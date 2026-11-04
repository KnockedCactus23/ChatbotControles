"""JSON Schemas para salidas estructuradas (output_config.format)."""

from .controls import ESTADOS, IDS_CONTROLES

_ACTUALIZACION = {
    "type": "object",
    "properties": {
        "control_id": {"type": "string", "enum": IDS_CONTROLES},
        "estado": {"type": "string", "enum": list(ESTADOS)},
        "justificacion": {"type": "string"},
    },
    "required": ["control_id", "estado", "justificacion"],
    "additionalProperties": False,
}

_PREGUNTA = {
    "type": "object",
    "properties": {
        "control_id": {"type": "string", "enum": IDS_CONTROLES},
        "pregunta": {"type": "string"},
    },
    "required": ["control_id", "pregunta"],
    "additionalProperties": False,
}

ANALISIS = {
    "type": "object",
    "properties": {
        "mensaje": {"type": "string"},
        "actualizaciones": {"type": "array", "items": _ACTUALIZACION},
        "preguntas_cerradas": {"type": "array", "items": _PREGUNTA},
    },
    "required": ["mensaje", "actualizaciones", "preguntas_cerradas"],
    "additionalProperties": False,
}

_QUICK_WIN = {
    "type": "object",
    "properties": {
        "titulo": {"type": "string"},
        "descripcion": {"type": "string"},
        "control_id": {"type": "string", "enum": IDS_CONTROLES},
        "esfuerzo": {"type": "string", "enum": ["bajo", "medio"]},
        "impacto": {"type": "string", "enum": ["medio", "alto"]},
    },
    "required": ["titulo", "descripcion", "control_id", "esfuerzo", "impacto"],
    "additionalProperties": False,
}

_RECOMENDACION = {
    "type": "object",
    "properties": {
        "prioridad": {"type": "string", "enum": ["alta", "media", "baja"]},
        "titulo": {"type": "string"},
        "descripcion": {"type": "string"},
        "controles": {"type": "array", "items": {"type": "string", "enum": IDS_CONTROLES}},
        "plazo": {"type": "string", "enum": ["0-3 meses", "3-6 meses", "6-12 meses"]},
    },
    "required": ["prioridad", "titulo", "descripcion", "controles", "plazo"],
    "additionalProperties": False,
}

REPORTE = {
    "type": "object",
    "properties": {
        "resumen_ejecutivo": {"type": "string"},
        "riesgos_principales": {"type": "array", "items": {"type": "string"}},
        "quick_wins": {"type": "array", "items": _QUICK_WIN},
        "recomendaciones": {"type": "array", "items": _RECOMENDACION},
    },
    "required": ["resumen_ejecutivo", "riesgos_principales", "quick_wins", "recomendaciones"],
    "additionalProperties": False,
}
