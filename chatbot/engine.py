"""Llamadas a la API de Claude (SDK oficial `anthropic`) para cada etapa de la actividad.

1. explain(): prueba preliminar del agente (Etapa 1.5).
2. context_sheet(): ficha de contexto a partir del PDF 1 (Etapa 2), con citas verificadas.
3. evaluate(): las 56 salvaguardas IG1 en lotes por control (Etapa 3).
4. report(): resumen ejecutivo, 5 riesgos y 5 iniciativas; cierra la versión v1 (Etapas 3.5 y 4).
5. analyze_initiatives(): PDF 2 → propuestas de cambio sujetas a validación (Etapa 5).
6. updated_report(): diagnóstico v2 con comparación (Etapa 5.6).
7. ask(): preguntas del auditor sobre las decisiones del agente (no cambia estados).

Ahorro de tokens sin tocar la calidad:
- Caché de prompts donde hay reutilización real: los 3 lotes de la evaluación comparten bloque común, documento y
  ficha (~30K tokens) con el mismo esquema; los lotes 2 y 3 los leen de caché (5 % del precio en Sonnet 5.5).
  También la ficha regenerada con un ajuste y las consultas seguidas. El esquema de salida es parte del prefijo
  cacheado, así que entre etapas distintas no hay reutilización posible y ahí no se paga la escritura.
- El PDF se envía como texto con marcas de página (el mismo texto contra el que se verifican las citas), no como
  archivo: ~1/3 de los tokens y citas más fáciles de verificar. Un PDF sin texto (escaneo) se envía como archivo.
- La ficha va resumida a las etapas posteriores (sus citas ya están en la matriz) y el JSON va compacto.
- max_tokens por etapa para evitar respuestas desbocadas.
Salida estructurada (JSON Schema) en todas las etapas; el código valida y completa lo que el esquema no puede exigir.
"""

import base64
import json
import os
from pathlib import Path

import anthropic

from . import prompts, schemas
from .controls import catalogo
from .documentos import Documento, verificar_cita
from .state import (ETIQUETA, SITUACION_RIESGO, Proyecto, brechas_por_control, citas_repetidas, estado_iniciativas,
                    formato_pct, lotes_por_control, normalizar_ficha, situacion_riesgos, validar_reporte)

MODELO_POR_DEFECTO = "claude-sonnet-5-5"
# Modelos que se pueden elegir en la barra lateral (se guarda con cada evaluación; uno solo por evaluación).
MODELOS = {"claude-sonnet-5-5": "Claude Sonnet 5.5 · recomendado",
           "claude-haiku-5-5": "Claude Haiku 5.5 · para depurar",
           "claude-opus-5-5": "Claude Opus 5.5 · máxima capacidad (2× el costo)"}
# Esfuerzo de razonamiento: el valor por defecto de cada modelo, fijo en todas las llamadas (cambiarlo entre
# llamadas invalidaría la caché). Haiku 5.5 en "high" gastó los 24K tokens de la ficha solo en razonar y no
# respondió; en "medium" (su valor por defecto) la generó completa con ~10K.
ESFUERZO = {"claude-haiku-5-5": "medium"}
ESFUERZO_POR_DEFECTO = "high"
REINTENTOS = 3                             # el SDK reintenta 408/409/429/5xx/529, timeouts y fallos de conexión
TIMEOUT_S = 120
TIMEOUT_LARGO_S = 420                      # evaluación y reportes: salidas largas con razonamiento
# Tope de salida por tarea (incluye el razonamiento). Holgado: cortarse obliga a repetir la llamada completa.
MAX_TOKENS = {"explicar": 6000, "ficha": 32000, "evaluar": 32000, "reporte": 24000, "pdf2": 32000,
              "faltantes": 16000, "v2": 32000, "consulta": 8000}
# Modelos con reintento del lado del servidor si el clasificador de seguridad declina (p. ej. categoría "cyber",
# posible en una evaluación de ciberseguridad). Haiku 5.5 no lo admite.
CON_FALLBACK = ("claude-sonnet-5-5", "claude-opus-5-5", "claude-fable-5-2", "claude-fable-5-1")
# USD por millón de tokens: entrada, salida, lectura de caché (para el registro de consumo; precios de 2026-11).
PRECIOS = {"claude-sonnet-5-5": (2.00, 10.00, 0.10), "claude-opus-5-5": (4.00, 20.00, 0.20),
           "claude-haiku-5-5": (0.10, 0.50, 0.01)}


class ErrorChatbot(Exception):
    """Error presentable al usuario."""


def _json(datos) -> str:
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":"))


def matriz_compacta(proyecto: Proyecto, version=None) -> list[dict]:
    """El nombre de cada salvaguarda ya está en el catálogo del prompt: aquí solo el id."""
    v = version or proyecto.vigente
    return [{"id": r.id, "estado": ETIQUETA[r.estado], "aplicabilidad": r.aplicabilidad, "justificacion": r.justificacion,
             "evidencia": r.evidencia(proyecto.documentos), "cita": r.cita, "observaciones": r.observaciones}
            for r in v.matriz.values()]


def ficha_resumida(ficha: dict | None) -> dict:
    """Ficha para las etapas posteriores a la evaluación: sin las citas de cada hallazgo (la evidencia ya está en la
    matriz y en el documento), pero con todo lo interpretado: resúmenes, faltantes, ambigüedades y perfil de riesgo."""
    f = ficha or {}
    return {"nombre_organizacion": f.get("nombre_organizacion"), "resumen_contexto": f.get("resumen_contexto"),
            "dimensiones": {k: {"resumen": d.get("resumen", ""), "hallazgos": [h.get("dato") for h in d.get("hallazgos", [])],
                                "faltante": d.get("faltante", "")} for k, d in (f.get("dimensiones") or {}).items()},
            "informacion_faltante": f.get("informacion_faltante", []), "ambiguedades": f.get("ambiguedades", []),
            "perfil_riesgo": f.get("perfil_riesgo", {})}


def _sin_restricciones_de_arreglo(schema):
    """La salida estructurada de Claude no admite minItems/maxItems: se quitan del esquema enviado y el código
    exige los conteos (completar_faltantes, segunda pasada de la Etapa 5, validar_reporte)."""
    if isinstance(schema, dict):
        return {k: _sin_restricciones_de_arreglo(v) for k, v in schema.items() if k not in ("minItems", "maxItems")}
    if isinstance(schema, list):
        return [_sin_restricciones_de_arreglo(v) for v in schema]
    return schema


def _esquema_para_api(schema: dict) -> dict:
    """Prepara un esquema para la salida estructurada de Claude:
    1. quita minItems/maxItems (no los admite; los conteos los exige el código);
    2. mueve a `$defs` los subesquemas repetidos (las 10 dimensiones de la ficha, las listas de ids…) y los
       referencia con `$ref`. Mismas restricciones, pero la gramática que compila la API es mucho menor: sin esto,
       la ficha excede el límite ("The compiled grammar is too large")."""
    limpio = _sin_restricciones_de_arreglo(schema)
    conteo: dict[str, int] = {}

    def contar(nodo):
        if isinstance(nodo, dict):
            conteo[json.dumps(nodo, sort_keys=True)] = conteo.get(json.dumps(nodo, sort_keys=True), 0) + 1
            for v in nodo.values():
                contar(v)
        elif isinstance(nodo, list):
            for v in nodo:
                contar(v)

    contar(limpio)
    defs: dict[str, dict] = {}
    nombres: dict[str, str] = {}

    def reemplazar(nodo, raiz=False):
        if isinstance(nodo, list):
            return [reemplazar(v) for v in nodo]
        if not isinstance(nodo, dict):
            return nodo
        clave = json.dumps(nodo, sort_keys=True)
        interno = {k: (reemplazar(v) if k not in ("properties",) else {p: reemplazar(x) for p, x in v.items()})
                   for k, v in nodo.items()}
        if not raiz and conteo.get(clave, 0) > 1 and len(clave) > 60:
            if clave not in nombres:
                nombres[clave] = f"d{len(nombres) + 1}"
                defs[nombres[clave]] = interno
            return {"$ref": f"#/$defs/{nombres[clave]}"}
        return interno

    resultado = reemplazar(limpio, raiz=True)
    if defs:
        resultado["$defs"] = defs
    return resultado


def _cache(bloque: dict) -> dict:
    return {**bloque, "cache_control": {"type": "ephemeral"}}


class Motor:
    def __init__(self, modelo: str | None = None, base_url: str | None = None):
        self.modelo = modelo or MODELO_POR_DEFECTO  # app.py lo fija con el modelo de la evaluación antes de cada tarea
        if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
            raise ErrorChatbot("Falta ANTHROPIC_API_KEY en el archivo .env")
        # base_url solo en pruebas, para apuntar a un servidor simulado.
        self.client = anthropic.Anthropic(base_url=base_url, max_retries=REINTENTOS, timeout=TIMEOUT_S)
        self.consumo: list[dict] = []  # una fila por llamada; app.py la copia al proyecto

    # ------------------------------------------------------------------ util
    def _llamar(self, tarea: str, contenido: list[dict], schema: dict, timeout_s: float | None = None,
                max_tokens: int = 16000, etapa: str = "", cachear: bool = False) -> dict:
        """Una llamada con salida estructurada. `tarea` es la instrucción de la etapa; el bloque común va antes.

        Caché: el esquema de salida forma parte del prefijo cacheado, así que solo se reutiliza entre llamadas de la
        MISMA etapa (lotes de la evaluación, ficha regenerada, consultas seguidas). Solo esas llevan `cachear=True`;
        en las llamadas únicas, escribir en caché costaría 25 % más sin volver a leerse."""
        timeout_s = timeout_s or TIMEOUT_S
        sistema = [{"type": "text", "text": prompts.base()}, {"type": "text", "text": tarea}]
        if cachear:
            sistema[-1] = _cache(sistema[-1])
        else:
            contenido = [{k: v for k, v in b.items() if k != "cache_control"} for b in contenido]
        extra = {}
        if self.modelo in CON_FALLBACK:
            extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
        try:
            resp = self.client.with_options(timeout=timeout_s).beta.messages.create(
                model=self.modelo,
                max_tokens=max_tokens,
                system=sistema,
                messages=[{"role": "user", "content": contenido}],
                output_config={"effort": ESFUERZO.get(self.modelo, ESFUERZO_POR_DEFECTO),
                               "format": {"type": "json_schema", "schema": _esquema_para_api(schema)}},
                **extra,
            )
        except anthropic.APITimeoutError as e:
            raise ErrorChatbot(f"Claude tardó más de {timeout_s:.0f} s en responder en cada intento. "
                               "Vuelve a intentarlo en un minuto.") from e
        except anthropic.AuthenticationError as e:
            raise ErrorChatbot("API key inválida. Revisa ANTHROPIC_API_KEY en tu archivo .env.") from e
        except anthropic.PermissionDeniedError as e:
            raise ErrorChatbot("Tu API key no tiene permiso para usar este modelo.") from e
        except anthropic.NotFoundError as e:
            raise ErrorChatbot(f"El modelo '{self.modelo}' no existe o no está disponible. "
                               "Elige otro modelo en la barra lateral.") from e
        except anthropic.RateLimitError as e:
            raise ErrorChatbot("Se alcanzó el límite de uso por minuto de tu cuenta de Claude. "
                               "Espera un momento y reintenta.") from e
        except anthropic.BadRequestError as e:
            if "credit balance" in str(e).lower():
                raise ErrorChatbot("Tu cuenta de Claude no tiene saldo suficiente. Recarga créditos en "
                                   "platform.claude.com.") from e
            raise ErrorChatbot(f"Claude rechazó la solicitud: {e.message}") from e
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                raise ErrorChatbot("Claude está saturado o con fallas en este momento y no respondió tras varios "
                                   "reintentos. Espera un minuto y vuelve a intentarlo.") from e
            raise ErrorChatbot(f"Error de la API de Claude ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ErrorChatbot("No se pudo conectar con la API de Claude. Revisa tu conexión.") from e

        self._registrar(etapa or "llamada", resp)
        if resp.stop_reason == "refusal":
            categoria = getattr(getattr(resp, "stop_details", None), "category", None)
            raise ErrorChatbot("Claude declinó esta solicitud por sus filtros de seguridad"
                               + (f" (categoría: {categoria})" if categoria else "") + ".")
        if resp.stop_reason == "max_tokens":
            sin_texto = not any(b.type == "text" for b in resp.content)
            raise ErrorChatbot("La respuesta de Claude se cortó por el límite de longitud de esta etapa"
                               + (" (lo gastó todo en razonar, sin llegar a responder)" if sin_texto else "")
                               + ". Vuelve a intentarlo; si se repite, sube el límite en MAX_TOKENS (chatbot/engine.py).")
        texto = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            return json.loads(texto)
        except json.JSONDecodeError as e:
            raise ErrorChatbot("La respuesta de Claude no es JSON válido. Reintenta.") from e

    def _registrar(self, etapa: str, resp) -> None:
        u = getattr(resp, "usage", None)
        if u is None:
            return
        fila = {"etapa": etapa, "modelo": getattr(resp, "model", self.modelo), "entrada": u.input_tokens or 0,
                "cache_escrita": getattr(u, "cache_creation_input_tokens", 0) or 0,
                "cache_leida": getattr(u, "cache_read_input_tokens", 0) or 0, "salida": u.output_tokens or 0}
        p_in, p_out, p_read = PRECIOS.get(self.modelo, PRECIOS[MODELO_POR_DEFECTO])
        # Escritura de caché de 5 min: 1.25x el precio de entrada.
        fila["usd"] = round((fila["entrada"] * p_in + fila["cache_escrita"] * p_in * 1.25 + fila["cache_leida"] * p_read
                             + fila["salida"] * p_out) / 1e6, 4)
        self.consumo.append(fila)

    @staticmethod
    def _documento(doc: Documento, cachear: bool = True) -> dict:
        """El documento como texto con marcas de página (el mismo texto contra el que se verifican las citas).
        Solo un PDF sin texto extraíble (escaneo) se envía como archivo."""
        if not any(t.strip() for t in doc.paginas) and doc.archivo and Path(doc.archivo).exists():
            bloque = {"type": "document", "title": f"{doc.etiqueta} — {doc.nombre}",
                      "source": {"type": "base64", "media_type": "application/pdf",
                                 "data": base64.standard_b64encode(Path(doc.archivo).read_bytes()).decode()}}
        else:
            bloque = {"type": "text", "text": f"<documento nombre=\"{doc.etiqueta} — {doc.nombre}\">\n"
                                              f"{doc.texto_completo()}\n</documento>"}
        return _cache(bloque) if cachear else bloque

    @staticmethod
    def _texto(texto: str, cachear: bool = False) -> dict:
        bloque = {"type": "text", "text": texto}
        return _cache(bloque) if cachear else bloque

    # ------------------------------------------------------------- Etapa 1.5
    def explain(self) -> str:
        datos = self._llamar(prompts.sistema_explicacion(),
                             [self._texto("Explica tu objetivo, alcance, criterios y qué harás cuando no tengas "
                                          "suficiente información.")],
                             schemas.MENSAJE, max_tokens=MAX_TOKENS["explicar"], etapa="Prueba preliminar")
        return datos.get("mensaje", "")

    # --------------------------------------------------------------- Etapa 2
    def context_sheet(self, proyecto: Proyecto, ajuste: str = "") -> dict:
        doc = proyecto.documentos["pdf1"]
        contenido = [self._documento(doc)]  # cacheado: regenerar la ficha con un ajuste lo reutiliza
        if ajuste:
            contenido.append(self._texto(f"Ajuste solicitado por el equipo auditor sobre la ficha anterior: {ajuste}\n"
                                         f"Ficha anterior: {_json(proyecto.ficha)}"))
        else:
            contenido.append(self._texto("Genera la ficha de contexto de este documento."))
        ficha = normalizar_ficha(self._llamar(prompts.sistema_ficha(), contenido, schemas.ficha(), TIMEOUT_LARGO_S,
                                              MAX_TOKENS["ficha"], "Ficha de contexto", cachear=True))
        # Verificación de citas (R3, R6): cada hallazgo queda marcado como verificado o no.
        for dim in ficha.get("dimensiones", {}).values():
            for h in dim.get("hallazgos", []):
                pagina = verificar_cita(doc, h.get("cita", ""), h.get("pagina"))
                h["verificada"] = pagina is not None
                if pagina:
                    h["pagina"] = pagina
                else:
                    proyecto.avisos.append(f"Ficha: la cita «{h.get('cita', '')[:100]}» no aparece en {doc.etiqueta}.")
        proyecto.ficha = ficha
        proyecto.ficha_validada = False
        if ficha.get("nombre_organizacion"):
            proyecto.nombre = ficha["nombre_organizacion"]
        return ficha

    # --------------------------------------------------------------- Etapa 3
    def evaluate(self, proyecto: Proyecto, progreso=None) -> None:
        doc = proyecto.documentos["pdf1"]
        proyecto.iniciar_v1()
        lotes = lotes_por_control()
        # Documento y ficha son el mismo prefijo en los 3 lotes: se escriben en caché en el primero y se leen
        # (al 5 % del precio) en los demás. Solo cambia la lista de salvaguardas, que va al final.
        fijo = [self._documento(doc), self._texto(f"Ficha de contexto validada:\n{_json(ficha_resumida(proyecto.ficha))}",
                                                  cachear=True)]
        esquema = schemas.evaluacion(catalogo().ids_ig1())
        for i, lote in enumerate(lotes, 1):
            if progreso:
                progreso(i, len(lotes), lote)
            pedido = self._texto(f"Evalúa estas {len(lote)} salvaguardas IG1 (todas, sin omitir ninguna): {', '.join(lote)}")
            # Mismo esquema (los 56 ids) en todos los lotes: el esquema es parte del prefijo cacheado y uno por lote
            # anulaba la caché (medido: 0 tokens leídos). El código acepta solo los ids del lote.
            datos = self._llamar(prompts.sistema_evaluacion(), fijo + [pedido], esquema, TIMEOUT_LARGO_S,
                                 MAX_TOKENS["evaluar"], f"Evaluación lote {i}", cachear=True)
            ajenas = [e.get("id") for e in datos.get("evaluaciones", []) if e.get("id") not in lote]
            if ajenas:
                proyecto.avisos.append(f"Lote {i}: se ignoraron {', '.join(map(str, ajenas))}, que no eran de este lote.")
            datos["evaluaciones"] = [e for e in datos.get("evaluaciones", []) if e.get("id") in lote]
            proyecto.aplicar_lote(datos.get("evaluaciones", []), doc)
        proyecto.completar_faltantes(catalogo().ids_ig1())
        proyecto.avisos.extend(citas_repetidas(proyecto.v1.matriz))

    # --------------------------------------------------------- Etapas 3.5 y 4
    def _contexto_reporte(self, proyecto: Proyecto, version) -> tuple[str, list[str]]:
        ind = version.indicadores()
        brechas = [b for b in brechas_por_control(version.matriz) if b["brecha"] > 0][:5]
        ids = [b["control_id"] for b in brechas]
        texto = (f"Ficha de contexto:\n{_json(ficha_resumida(proyecto.ficha))}\n\n"
                 f"Matriz de las 56 salvaguardas ({version.nombre}):\n{_json(matriz_compacta(proyecto, version))}\n\n"
                 f"Indicadores calculados por el sistema (úsalos tal cual): total {ind['total']}, implementadas {ind['implementado']}, "
                 f"parciales {ind['parcial']}, no implementadas {ind['no_implementado']}, no verificadas {ind['no_verificado']}, "
                 f"no aplicables {ind['no_aplicable']}; implementación {formato_pct(ind['implementacion'])} "
                 f"(sobre salvaguardas evaluables); cobertura de la evaluación {formato_pct(ind['cobertura'])}.\n\n"
                 f"Controles con mayores brechas (ya ordenados): {_json(brechas)}")
        return texto, ids

    def report(self, proyecto: Proyecto) -> dict:
        texto, ids = self._contexto_reporte(proyecto, proyecto.v1)
        rep = self._llamar(prompts.sistema_reporte(), [self._texto(texto)], schemas.reporte(), TIMEOUT_LARGO_S,
                           MAX_TOKENS["reporte"], "Reporte inicial")
        proyecto.avisos.extend(validar_reporte(rep, proyecto.v1.matriz, ids, texto_fuente=_json(proyecto.ficha)))
        proyecto.cerrar_v1(rep)
        return rep

    # --------------------------------------------------------------- Etapa 5
    def analyze_initiatives(self, proyecto: Proyecto) -> list[dict]:
        doc = proyecto.documentos["pdf2"]
        # Sin caché: la segunda pasada usa otro esquema y no podría reutilizarla.
        fijo = [self._documento(doc), self._texto(
            f"Contexto de la empresa (ficha):\n{_json(ficha_resumida(proyecto.ficha))}\n\n"
            f"Matriz inicial v1 de las 56 salvaguardas:\n{_json(matriz_compacta(proyecto, proyecto.v1))}\n\n"
            f"Diagnóstico inicial, riesgos y roadmap original:\n{_json(proyecto.v1.reporte)}", cachear=True)]
        datos = self._llamar(prompts.sistema_iniciativas(), fijo + [self._texto("Procesa el nuevo documento.")],
                             schemas.iniciativas_pdf2(), TIMEOUT_LARGO_S, MAX_TOKENS["pdf2"], "PDF 2")
        relacionadas = []
        for ini in datos.get("iniciativas", []):
            relacionadas += ini.get("salvaguardas", [])
            for ev in ini.get("evidencia", []):
                pagina = verificar_cita(doc, ev.get("cita", ""), ev.get("pagina"))
                ev["verificada"] = pagina is not None
                if pagina:
                    ev["pagina"] = pagina
        decisiones = datos.get("decisiones", [])
        # F1: toda salvaguarda relacionada necesita una decisión. Si el modelo omitió alguna, se le piden
        # exactamente esas (el esquema obliga a una por id), igual que la evaluación obliga a las 56.
        decididas = {d.get("id") for d in decisiones}
        faltan = [s for s in dict.fromkeys(relacionadas) if s not in decididas]
        if faltan:
            proyecto.avisos.append(f"Etapa 5: el modelo no decidió sobre {', '.join(faltan)}; se le pidió una segunda pasada.")
            pedido = self._texto(
                f"Análisis de iniciativas ya hecho:\n{_json(datos.get('iniciativas', []))}\n\n"
                f"Emite UNA decisión para CADA una de estas salvaguardas relacionadas, que quedaron sin decisión: "
                f"{', '.join(faltan)}. Revisa el nuevo documento para cada una por separado.")
            extra = self._llamar(prompts.sistema_iniciativas(), fijo + [pedido], schemas.decisiones_faltantes(faltan),
                                 TIMEOUT_LARGO_S, MAX_TOKENS["faltantes"], "PDF 2 (segunda pasada)")
            decisiones += extra.get("decisiones", [])
        proyecto.iniciativas = datos.get("iniciativas", [])
        proyecto.alertas = [a for a in datos.get("alertas", []) if a.strip()]
        proyecto.registrar_cambios(decisiones, doc, relacionadas)
        return proyecto.iniciativas

    def updated_report(self, proyecto: Proyecto) -> dict:
        v1, v2 = proyecto.v1, proyecto.v2
        texto, ids = self._contexto_reporte(proyecto, v2)
        i1 = v1.indicadores()
        riesgos_v1 = v1.reporte.get("riesgos", [])
        roadmap_v1 = v1.reporte.get("iniciativas", [])
        # F4-F6: la situación de riesgos e iniciativas la decide el sistema con reglas fijas sobre la matriz v2.
        sit = situacion_riesgos(riesgos_v1, v1.matriz, v2.matriz)
        est = estado_iniciativas(roadmap_v1, v1.matriz, v2.matriz)
        aprobados = [{"id": c.id, "tipo": c.tipo, "de": ETIQUETA[c.estado_inicial], "a": ETIQUETA[c.estado_propuesto],
                      "justificacion": c.justificacion} for c in proyecto.cambios if c.decision == "aprobado"]
        no_aprobados = [{"id": c.id, "propuesto": ETIQUETA[c.estado_propuesto], "decision": c.decision}
                        for c in proyecto.cambios if c.decision != "aprobado"]
        calculado_r = [{"riesgo": n, "titulo": r.get("titulo"), "salvaguardas": r.get("salvaguardas", []),
                        "situacion": s["situacion"], "severidad_original": r.get("severidad"),
                        "severidad_residual": s["severidad_residual"], "mejoraron": s["mejoradas"],
                        "siguen_con_brecha": s["pendientes"]} for n, (r, s) in enumerate(zip(riesgos_v1, sit), 1)]
        calculado_i = [{"iniciativa": n, "titulo": x.get("titulo"), "salvaguardas": x.get("salvaguardas", []),
                        "estado": e["estado"], "mejoraron": e["mejoradas"], "siguen_con_brecha": e["pendientes"]}
                       for n, (x, e) in enumerate(zip(roadmap_v1, est), 1)]
        texto += (f"\n\nEvaluación inicial v1 — indicadores: implementación {formato_pct(i1['implementacion'])}, "
                  f"cobertura {formato_pct(i1['cobertura'])}. Reporte v1 (riesgos y roadmap originales):\n{_json(v1.reporte)}\n\n"
                  f"Cambios APROBADOS (los únicos que modifican la matriz):\n{_json(aprobados)}\n\n"
                  f"Cambios NO aprobados (no pueden citarse como mitigación):\n{_json(no_aprobados)}\n\n"
                  f"Lo que reporta el nuevo documento (para 'información faltante'; no es evidencia aprobada):\n"
                  f"{_json(proyecto.iniciativas)}\n\n"
                  f"Situación de los riesgos originales CALCULADA por el sistema (no la cambies):\n{_json(calculado_r)}\n\n"
                  f"Estado de las iniciativas originales CALCULADO por el sistema (no lo cambies):\n{_json(calculado_i)}")
        rep = self._llamar(prompts.sistema_reporte_actualizado(), [self._texto(texto)], schemas.reporte_actualizado(),
                           TIMEOUT_LARGO_S, MAX_TOKENS["v2"], "Reporte actualizado")
        # Lo calculado manda sobre lo que el modelo haya escrito; el modelo solo aporta las explicaciones.
        explic = rep.get("riesgos") or []
        rep["riesgos"] = [{"titulo": r.get("titulo", ""), "salvaguardas": r.get("salvaguardas", []),
                           "severidad": r.get("severidad", ""), **s,
                           "explicacion": explic[n].get("explicacion", "") if n < len(explic) else ""}
                          for n, (r, s) in enumerate(zip(riesgos_v1, sit))]
        explic = rep.get("iniciativas_estado") or []
        rep["iniciativas_estado"] = [{"titulo": x.get("titulo", ""), **e,
                                      "explicacion": explic[n].get("explicacion", "") if n < len(explic) else ""}
                                     for n, (x, e) in enumerate(zip(roadmap_v1, est))]
        for n, r in enumerate(rep["riesgos"], 1):
            if not r["explicacion"].strip():
                r["explicacion"] = (f"{SITUACION_RIESGO[r['situacion']]} según la matriz v2. Mejoraron: "
                                    f"{', '.join(r['mejoradas']) or 'ninguna'}; siguen con brecha: {', '.join(r['pendientes']) or 'ninguna'}.")
                proyecto.avisos.append(f"Riesgo original {n}: sin explicación del modelo; se completó con la matriz.")
        proyecto.avisos.extend(validar_reporte(rep, v2.matriz, ids, clave_roadmap="roadmap", clave_riesgos="riesgos_v2",
                                              texto_fuente=_json([proyecto.ficha, proyecto.iniciativas])))
        v2.reporte = rep
        v2.cerrada = True
        return rep

    # --------------------------------------------------------------- consultas
    def ask(self, proyecto: Proyecto, pregunta: str) -> str:
        # Ficha y matriz se cachean: preguntas seguidas solo pagan la pregunta nueva.
        fijo = (f"Ficha de contexto:\n{_json(ficha_resumida(proyecto.ficha))}"
                + (f"\n\nMatriz vigente ({proyecto.vigente.nombre}):\n{_json(matriz_compacta(proyecto))}" if proyecto.vigente else ""))
        return self._llamar(prompts.sistema_consulta(), [self._texto(fijo, cachear=True),
                                                         self._texto(f"Pregunta del auditor: {pregunta}")],
                            schemas.MENSAJE, TIMEOUT_LARGO_S, MAX_TOKENS["consulta"], "Consulta", cachear=True).get("mensaje", "")
