"""Llamadas a la API de Gemini (SDK oficial google-genai) para cada etapa de la actividad.

1. explain(): prueba preliminar del agente (Etapa 1.5).
2. context_sheet(): ficha de contexto a partir del PDF 1 (Etapa 2), con citas verificadas.
3. evaluate(): las 56 salvaguardas IG1 en lotes por control (Etapa 3).
4. report(): resumen ejecutivo, 5 riesgos y 5 iniciativas; cierra la versión v1 (Etapas 3.5 y 4).
5. analyze_initiatives(): PDF 2 → propuestas de cambio sujetas a validación (Etapa 5).
6. updated_report(): diagnóstico v2 con comparación (Etapa 5.6).
7. ask(): preguntas del auditor sobre las decisiones del agente (no cambia estados).

Todas las salidas usan salida estructurada (JSON Schema); temperatura 0 y semilla fija para que
el agente sea reproducible (R9).
"""

import json
import os
from pathlib import Path

import httpx
from google import genai
from google.genai import errors, types

from . import prompts, schemas
from .controls import catalogo
from .documentos import Documento, verificar_cita
from .state import (ETIQUETA, SITUACION_RIESGO, Proyecto, brechas_por_control, citas_repetidas, estado_iniciativas,
                    formato_pct, lotes_por_control, nombre_salvaguarda, normalizar_ficha, situacion_riesgos,
                    validar_reporte)

MODELO_POR_DEFECTO = "gemini-3.5-flash-lite"

# Reintentos automáticos (los hace el SDK) solo para errores temporales: saturación del modelo,
# límite por minuto, fallos del servidor, y también timeouts y errores de conexión.
REINTENTOS = types.HttpRetryOptions(
    attempts=4,  # 1 intento + 3 reintentos
    initial_delay=1.0,
    max_delay=8.0,
    exp_base=2,
    jitter=0.5,
    http_status_codes=[408, 429, 500, 502, 503, 504],
)

# Límite por intento. En el plan gratuito la latencia varía mucho (de 3 s a ~2 min para la misma
# llamada). Las llamadas con PDF y salidas largas (evaluación, reportes) usan un límite mayor.
TIMEOUT_S = 30
TIMEOUT_LARGO_S = 120
SEMILLA = 7


class ErrorChatbot(Exception):
    """Error presentable al usuario."""


def _json(datos) -> str:
    return json.dumps(datos, ensure_ascii=False)


def matriz_compacta(proyecto: Proyecto, version=None) -> list[dict]:
    v = version or proyecto.vigente
    return [{"id": r.id, "salvaguarda": nombre_salvaguarda(r.id), "estado": ETIQUETA[r.estado],
             "aplicabilidad": r.aplicabilidad, "justificacion": r.justificacion,
             "evidencia": r.evidencia(proyecto.documentos), "cita": r.cita, "observaciones": r.observaciones}
            for r in v.matriz.values()]


class Motor:
    def __init__(self, modelo: str | None = None, base_url: str | None = None):
        self.modelo = modelo or os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ErrorChatbot("Falta GEMINI_API_KEY en el archivo .env")
        self.base_url = base_url  # solo en pruebas, para apuntar a un servidor simulado
        self.client = genai.Client(api_key=api_key, http_options=self._http(TIMEOUT_S))

    def _http(self, timeout_s: float) -> types.HttpOptions:
        return types.HttpOptions(retry_options=REINTENTOS, base_url=self.base_url, timeout=int(timeout_s * 1000))

    # ------------------------------------------------------------------ util
    def _llamar(self, system: str, partes: list, schema: dict, timeout_s: float | None = None) -> dict:
        timeout_s = timeout_s or TIMEOUT_S
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema,
            temperature=0,
            seed=SEMILLA,
            http_options=self._http(timeout_s),
        )
        try:
            resp = self.client.models.generate_content(
                model=self.modelo, contents=[{"role": "user", "parts": partes}], config=config)
        except httpx.TimeoutException as e:
            raise ErrorChatbot(f"Gemini tardó más de {timeout_s:.0f} s en responder en cada intento. "
                               "Suele ser saturación temporal: espera un minuto y vuelve a intentarlo.") from e
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
            if e.code == 503:
                raise ErrorChatbot("Gemini está saturado en este momento y no respondió tras varios reintentos. "
                                   "Espera un minuto y vuelve a intentarlo.") from e
            raise ErrorChatbot(f"Error del servidor de Gemini ({e.code}) tras varios reintentos. "
                               "Vuelve a intentarlo en un minuto.") from e
        except errors.APIError as e:
            raise ErrorChatbot(f"Error de la API de Gemini: {e.message}") from e
        except (httpx.TransportError, OSError) as e:
            raise ErrorChatbot("No se pudo conectar con la API de Gemini. Revisa tu conexión.") from e

        if resp.prompt_feedback and resp.prompt_feedback.block_reason:
            raise ErrorChatbot("Gemini bloqueó el contenido por sus filtros de seguridad.")
        texto = resp.text
        if not texto:
            motivo = resp.candidates[0].finish_reason if resp.candidates else "desconocido"
            raise ErrorChatbot(f"Gemini no devolvió contenido (motivo: {motivo}).")
        try:
            return json.loads(texto)
        except json.JSONDecodeError as e:
            raise ErrorChatbot("La respuesta de Gemini se cortó o no es JSON válido. Reintenta.") from e

    @staticmethod
    def _parte_documento(doc: Documento) -> list:
        """El PDF original se envía como archivo; el texto pegado, como texto con números de página."""
        encabezado = {"text": f"Documento {doc.etiqueta} — {doc.nombre}:"}
        if doc.tipo == "pdf" and doc.archivo and Path(doc.archivo).exists():
            return [encabezado, types.Part.from_bytes(data=Path(doc.archivo).read_bytes(), mime_type="application/pdf")]
        return [encabezado, {"text": doc.texto_completo()}]

    # ------------------------------------------------------------- Etapa 1.5
    def explain(self) -> str:
        datos = self._llamar(prompts.sistema_explicacion(), [{"text": "Explica tu objetivo, alcance, criterios y qué harás "
                             "cuando no tengas suficiente información."}], schemas.MENSAJE)
        return datos.get("mensaje", "")

    # --------------------------------------------------------------- Etapa 2
    def context_sheet(self, proyecto: Proyecto, ajuste: str = "") -> dict:
        doc = proyecto.documentos["pdf1"]
        partes = self._parte_documento(doc)
        if ajuste:
            partes.append({"text": f"Ajuste solicitado por el equipo auditor sobre la ficha anterior: {ajuste}\n"
                                   f"Ficha anterior: {_json(proyecto.ficha)}"})
        ficha = normalizar_ficha(self._llamar(prompts.sistema_ficha(), partes, schemas.ficha(), TIMEOUT_LARGO_S))
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
        for i, lote in enumerate(lotes, 1):
            if progreso:
                progreso(i, len(lotes), lote)
            partes = self._parte_documento(doc) + [{"text": (
                f"Ficha de contexto validada:\n{_json(proyecto.ficha)}\n\n"
                f"Evalúa estas {len(lote)} salvaguardas IG1 (todas, sin omitir ninguna): {', '.join(lote)}")}]
            datos = self._llamar(prompts.sistema_evaluacion(), partes, schemas.evaluacion(lote), TIMEOUT_LARGO_S)
            proyecto.aplicar_lote(datos.get("evaluaciones", []), doc)
        proyecto.completar_faltantes(catalogo().ids_ig1())
        proyecto.avisos.extend(citas_repetidas(proyecto.v1.matriz))

    # --------------------------------------------------------- Etapas 3.5 y 4
    def _contexto_reporte(self, proyecto: Proyecto, version) -> tuple[str, list[str]]:
        ind = version.indicadores()
        brechas = [b for b in brechas_por_control(version.matriz) if b["brecha"] > 0][:5]
        ids = [b["control_id"] for b in brechas]
        texto = (f"Ficha de contexto:\n{_json(proyecto.ficha)}\n\n"
                 f"Matriz de las 56 salvaguardas ({version.nombre}):\n{_json(matriz_compacta(proyecto, version))}\n\n"
                 f"Indicadores calculados por el sistema (úsalos tal cual): total {ind['total']}, implementadas {ind['implementado']}, "
                 f"parciales {ind['parcial']}, no implementadas {ind['no_implementado']}, no verificadas {ind['no_verificado']}, "
                 f"no aplicables {ind['no_aplicable']}; implementación {formato_pct(ind['implementacion'])} "
                 f"(sobre salvaguardas evaluables); cobertura de la evaluación {formato_pct(ind['cobertura'])}.\n\n"
                 f"Controles con mayores brechas (ya ordenados): {_json(brechas)}")
        return texto, ids

    def report(self, proyecto: Proyecto) -> dict:
        texto, ids = self._contexto_reporte(proyecto, proyecto.v1)
        rep = self._llamar(prompts.sistema_reporte(), [{"text": texto}], schemas.reporte(), TIMEOUT_LARGO_S)
        proyecto.avisos.extend(validar_reporte(rep, proyecto.v1.matriz, ids))
        proyecto.cerrar_v1(rep)
        return rep

    # --------------------------------------------------------------- Etapa 5
    def analyze_initiatives(self, proyecto: Proyecto) -> list[dict]:
        doc = proyecto.documentos["pdf2"]
        partes = self._parte_documento(doc) + [{"text": (
            f"Contexto de la empresa (ficha):\n{_json(proyecto.ficha)}\n\n"
            f"Matriz inicial v1 de las 56 salvaguardas:\n{_json(matriz_compacta(proyecto, proyecto.v1))}\n\n"
            f"Diagnóstico inicial, riesgos y roadmap original:\n{_json(proyecto.v1.reporte)}")}]
        datos = self._llamar(prompts.sistema_iniciativas(), partes, schemas.iniciativas_pdf2(), TIMEOUT_LARGO_S)
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
            pedido = partes[:-1] + [{"text": (
                partes[-1]["text"] + f"\n\nAnálisis de iniciativas ya hecho:\n{_json(datos.get('iniciativas', []))}\n\n"
                f"Emite UNA decisión para CADA una de estas salvaguardas relacionadas, que quedaron sin decisión: "
                f"{', '.join(faltan)}. Revisa el nuevo documento para cada una por separado.")}]
            extra = self._llamar(prompts.sistema_iniciativas(), pedido, schemas.decisiones_faltantes(faltan), TIMEOUT_LARGO_S)
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
        rep = self._llamar(prompts.sistema_reporte_actualizado(), [{"text": texto}], schemas.reporte_actualizado(),
                           TIMEOUT_LARGO_S)
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
        proyecto.avisos.extend(validar_reporte(rep, v2.matriz, ids, clave_roadmap="roadmap", clave_riesgos="riesgos_v2"))
        v2.reporte = rep
        v2.cerrada = True
        return rep

    # --------------------------------------------------------------- consultas
    def ask(self, proyecto: Proyecto, pregunta: str) -> str:
        texto = (f"Ficha de contexto:\n{_json(proyecto.ficha)}\n\n"
                 + (f"Matriz vigente ({proyecto.vigente.nombre}):\n{_json(matriz_compacta(proyecto))}\n\n" if proyecto.vigente else "")
                 + f"Pregunta del auditor: {pregunta}")
        return self._llamar(prompts.sistema_consulta(), [{"text": texto}], schemas.MENSAJE, TIMEOUT_LARGO_S).get("mensaje", "")
