"""JSON Schemas para salidas estructuradas de cada etapa (enums con los ids del catálogo IG1)."""

from .controls import catalogo
from .prompts import DIMENSIONES
from .state import APLICABILIDAD, ESTADOS


def _obj(propiedades: dict) -> dict:
    return {"type": "object", "properties": propiedades, "required": list(propiedades), "additionalProperties": False}


def _lista(items: dict, exactos: int | None = None) -> dict:
    esquema = {"type": "array", "items": items}
    if exactos:
        esquema.update(minItems=exactos, maxItems=exactos)
    return esquema


_TEXTO = {"type": "string"}
_TEXTOS = _lista(_TEXTO)
_PAGINA = {"type": "integer"}


def _enum(valores) -> dict:
    return {"type": "string", "enum": list(valores)}


def _ids_controles() -> dict:
    return _enum(c.id for c in catalogo().controles)


def _ids_ig1() -> dict:
    return _enum(catalogo().ids_ig1())


MENSAJE = _obj({"mensaje": _TEXTO})


def ficha() -> dict:
    hallazgo = _obj({"dato": _TEXTO, "pagina": _PAGINA, "seccion": _TEXTO, "cita": _TEXTO})
    dimension = _obj({"resumen": _TEXTO, "hallazgos": _lista(hallazgo), "faltante": _TEXTO})
    return _obj({
        "nombre_organizacion": _TEXTO,
        "dimensiones": _obj({k: dimension for k, _, _ in DIMENSIONES}),
        "resumen_contexto": _TEXTO,  # distinto del "resumen_ejecutivo" de los reportes (D5)
        "informacion_faltante": _TEXTOS,
        "ambiguedades": _TEXTOS,
        "perfil_riesgo": _obj({
            "sector": _TEXTO,
            "tamano": _enum(["micro", "pequena", "mediana", "grande"]),
            "amenazas": _lista(_obj({
                "amenaza": _TEXTO, "impacto": _enum(["critico", "alto", "medio"]),
                "por_que_en_este_negocio": _TEXTO, "controles": _lista(_ids_controles())})),
            "prioridad_controles": _lista(_ids_controles()),
        }),
    })


def evaluacion(ids_lote: list[str]) -> dict:
    return _obj({
        "evaluaciones": _lista(_obj({
            "id": _enum(ids_lote),
            "aplicabilidad": _enum(APLICABILIDAD),
            "estado": _enum(ESTADOS),
            "justificacion": _TEXTO,
            "pagina": _PAGINA,
            "seccion": _TEXTO,
            "cita": _TEXTO,
            "observaciones": _TEXTO,
        }), exactos=len(ids_lote)),
    })


def _resumen_ejecutivo() -> dict:
    return _obj({
        "postura_inicial": _TEXTO,
        "controles_mayores_brechas": _lista(_obj({"control_id": _ids_controles(), "explicacion": _TEXTO})),
        "informacion_faltante": _TEXTOS,
        "principales_riesgos": _TEXTO,
        "resultados_preliminares": _TEXTO,
    })


def _riesgo() -> dict:
    return _obj({
        "titulo": _TEXTO, "descripcion": _TEXTO, "activo_proceso": _TEXTO, "deficiencia": _TEXTO,
        "consecuencia": _TEXTO, "severidad": _enum(["alta", "media", "baja"]), "justificacion": _TEXTO,
        "salvaguardas": _lista(_ids_ig1()),
    })


def _iniciativa() -> dict:
    return _obj({
        "titulo": _TEXTO, "descripcion": _TEXTO, "riesgos": _lista({"type": "integer", "enum": [1, 2, 3, 4, 5]}),
        "salvaguardas": _lista(_ids_ig1()), "beneficio": _TEXTO, "esfuerzo": _enum(["bajo", "medio", "alto"]),
        "prioridad": {"type": "integer", "enum": [1, 2, 3, 4, 5]}, "tipo": _enum(["quick_win", "proyecto"]),
    })


def reporte() -> dict:
    return _obj({
        "resumen_ejecutivo": _resumen_ejecutivo(),
        "riesgos": _lista(_riesgo(), exactos=5),
        "iniciativas": _lista(_iniciativa(), exactos=5),
    })


TIPOS_DECISION = ["cambio_estado", "actualizar_evidencia", "sin_cambio"]
MOTIVOS_SIN_CAMBIO = ["", "sin_evidencia", "evidencia_parcial", "pendiente_declarado", "sin_mejora"]


def _decision(ids=None) -> dict:
    return _obj({
        "id": _enum(ids) if ids else _ids_ig1(), "tipo": _enum(TIPOS_DECISION), "estado_propuesto": _enum(ESTADOS),
        "motivo_sin_cambio": _enum(MOTIVOS_SIN_CAMBIO), "justificacion": _TEXTO, "iniciativa": _TEXTO,
        "pagina": _PAGINA, "seccion": _TEXTO, "cita": _TEXTO,
    })


def decisiones_faltantes(ids: list[str]) -> dict:
    """Segunda pasada de la Etapa 5: exactamente una decisión por cada salvaguarda que quedó sin decidir (F1)."""
    return _obj({"decisiones": _lista(_decision(ids), exactos=len(ids))})


def iniciativas_pdf2() -> dict:
    evidencia = _obj({"salvaguarda": _ids_ig1(), "pagina": _PAGINA, "seccion": _TEXTO, "cita": _TEXTO})
    pendiente = _obj({"detalle": _TEXTO, "salvaguardas": _lista(_ids_ig1())})
    return _obj({
        "iniciativas": _lista(_obj({
            "nombre": _TEXTO, "que_mejoro": _TEXTO, "salvaguardas": _lista(_ids_ig1()), "evidencia": _lista(evidencia),
            "alcance": _enum(["completa", "parcial"]), "pendientes": _lista(pendiente), "riesgos_que_reduce": _TEXTOS,
        })),
        # Una decisión por CADA salvaguarda relacionada (F1); el código detecta las que falten.
        "decisiones": _lista(_decision()),
        "alertas": _TEXTOS,
    })


def reporte_actualizado() -> dict:
    """La situación de los riesgos y el estado de las iniciativas los calcula el sistema (state.py);
    el modelo solo redacta su explicación. riesgos_v2 es la lista vigente a la que apunta el roadmap (F7)."""
    return _obj({
        "resumen_cambios": _TEXTO,
        "riesgos": _lista(_obj({"titulo": _TEXTO, "explicacion": _TEXTO}), exactos=5),
        "iniciativas_estado": _lista(_obj({"titulo": _TEXTO, "explicacion": _TEXTO}), exactos=5),
        "riesgos_v2": _lista(_riesgo(), exactos=5),
        "resumen_ejecutivo": _resumen_ejecutivo(),
        "roadmap": _lista(_iniciativa(), exactos=5),
    })
