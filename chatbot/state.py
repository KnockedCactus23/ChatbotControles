"""Modelo de datos del proyecto de evaluación. Es la fuente de verdad: Claude propone, Python valida.

Reglas que se hacen cumplir AQUÍ (no se confía solo en el prompt):
- La matriz siempre tiene las 56 salvaguardas IG1 (lo que falte queda "No verificado").
- Implementado / Parcial / No implementado / No aplicable exigen una cita que aparezca en el
  documento; si la cita no existe, la salvaguarda queda "No verificado" (R3, R6, R8).
- Los indicadores se calculan con las fórmulas de la actividad, siempre desde la matriz.
- La versión inicial (v1) nunca se modifica después de cerrarse; los cambios del PDF 2 crean
  la versión v2 y solo aplican los aprobados por el auditor (R10, R11, R12).
"""

import copy
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime

from .controls import AREAS, catalogo, control, salvaguarda
from .documentos import Documento, verificar_cita

ESTADOS = ("implementado", "parcial", "no_implementado", "no_verificado", "no_aplicable")
ETIQUETA = {"implementado": "Implementado", "parcial": "Parcialmente implementado", "no_implementado": "No implementado",
            "no_verificado": "No verificado", "no_aplicable": "No aplicable"}
VALOR = {"implementado": 1.0, "parcial": 0.5, "no_implementado": 0.0}  # No verificado y No aplicable: —
EVALUABLES = tuple(VALOR)
APLICABILIDAD = ("aplica", "no_aplica", "por_determinar")
ETIQUETA_APLICABILIDAD = {"aplica": "Aplica", "no_aplica": "No aplica", "por_determinar": "Por determinar"}

SIN_INFORMACION = "Información no documentada; pendiente de verificación."


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ------------------------------------------------------------------ salvaguarda
@dataclass
class Resultado:
    id: str
    estado: str = "no_verificado"
    aplicabilidad: str = "por_determinar"
    justificacion: str = ""
    fuente: str = ""          # "pdf1" | "pdf2" | "" (sin evidencia)
    pagina: int | None = None
    seccion: str = ""
    cita: str = ""
    observaciones: str = SIN_INFORMACION

    def evidencia(self, documentos: dict | None = None) -> str:
        if self.fuente in ("pdf1", "pdf2"):
            doc = (documentos or {}).get(self.fuente)
            nombre = doc.etiqueta if doc else self.fuente.upper()
            partes = [nombre] + ([f"p. {self.pagina}"] if self.pagina else []) + ([self.seccion] if self.seccion else [])
            return " · ".join(partes)
        return "Sin evidencia documental"


def matriz_vacia() -> dict[str, Resultado]:
    return {sid: Resultado(sid) for sid in catalogo().ids_ig1()}


def validar_resultado(item: dict, doc: Documento) -> tuple[Resultado, list[str]]:
    """Convierte la propuesta del modelo en un Resultado que respeta las reglas de evidencia."""
    sid = item["id"]
    avisos = []
    estado = item.get("estado") if item.get("estado") in ESTADOS else "no_verificado"
    aplic = item.get("aplicabilidad") if item.get("aplicabilidad") in APLICABILIDAD else "por_determinar"
    r = Resultado(sid, estado, aplic, (item.get("justificacion") or "").strip(), "",
                  item.get("pagina") or None, (item.get("seccion") or "").strip(), (item.get("cita") or "").strip(),
                  (item.get("observaciones") or "").strip())

    if r.estado != "no_verificado":
        pagina = verificar_cita(doc, r.cita, r.pagina)
        if pagina is None:
            motivo = "sin cita" if not r.cita else f"la cita «{r.cita[:120]}» no aparece en {doc.etiqueta}"
            avisos.append(f"{sid}: el modelo propuso «{ETIQUETA[r.estado]}» pero {motivo}; queda No verificado (R3, R6, R8).")
            r.observaciones = (f"El agente propuso «{ETIQUETA[r.estado]}», pero no se encontró evidencia verificable en "
                               f"{doc.etiqueta}; queda pendiente de verificación. " + r.observaciones).strip()
            r.estado, r.aplicabilidad, r.cita, r.pagina, r.seccion = "no_verificado", "por_determinar", "", None, ""
        else:
            if r.pagina != pagina:
                avisos.append(f"{sid}: página corregida de {r.pagina} a {pagina} según el texto del documento.")
            r.pagina, r.fuente = pagina, doc.clave

    if r.estado == "no_aplicable":
        r.aplicabilidad = "no_aplica"
        if len(r.justificacion) < 15:
            avisos.append(f"{sid}: «No aplicable» sin justificación suficiente; queda No verificado.")
            r.estado, r.aplicabilidad, r.fuente = "no_verificado", "por_determinar", ""
    elif r.aplicabilidad == "no_aplica":
        r.aplicabilidad = "aplica" if r.estado in EVALUABLES else "por_determinar"
    if r.estado in EVALUABLES and r.aplicabilidad == "por_determinar":
        r.aplicabilidad = "aplica"
    if r.estado == "no_verificado":
        r.fuente, r.pagina, r.seccion, r.cita = "", None, "", ""
        if not r.observaciones:
            r.observaciones = SIN_INFORMACION
        if not r.justificacion:
            r.justificacion = "El documento no contiene información suficiente para establecer su estado."
    return r, avisos


def indicadores(matriz: dict[str, Resultado]) -> dict:
    """Fórmulas de la actividad (sección 3.4). Siempre desde la matriz; nunca los calcula el modelo."""
    n = {e: 0 for e in ESTADOS}
    for r in matriz.values():
        n[r.estado] += 1
    total = len(matriz)
    evaluables = n["implementado"] + n["parcial"] + n["no_implementado"]
    implementacion = (round(100 * (n["implementado"] + 0.5 * n["parcial"]) / evaluables, 1) if evaluables else None)
    base = total - n["no_aplicable"]
    cobertura = round(100 * evaluables / base, 1) if base else None
    return {"total": total, **n, "evaluables": evaluables, "implementacion": implementacion, "cobertura": cobertura}


def formato_pct(valor: float | None) -> str:
    return "No determinable" if valor is None else f"{valor:.1f}%"


def estado_control(matriz: dict[str, Resultado], cid: str) -> str:
    """Estado resumido de un control (solo para la matriz visual; los indicadores son por salvaguarda)."""
    ids = [s.id for s in control(cid).ig1]
    if not ids:
        return "sin_ig1"
    estados = [matriz[i].estado for i in ids if i in matriz]
    aplicables = [e for e in estados if e != "no_aplicable"]
    if not aplicables:
        return "no_aplicable"
    conocidos = [e for e in aplicables if e in EVALUABLES]
    if not conocidos:
        return "no_verificado"
    if all(e == "implementado" for e in aplicables):
        return "implementado"
    if all(e == "no_implementado" for e in conocidos) and len(conocidos) == len(aplicables):
        return "no_implementado"
    return "parcial"


def brechas_por_control(matriz: dict[str, Resultado]) -> list[dict]:
    """Controles ordenados de mayor a menor brecha: primero los No implementado y Parciales confirmados."""
    filas = []
    for c in catalogo().controles:
        ids = [s.id for s in c.ig1]
        if not ids:
            continue
        sub = {i: matriz[i] for i in ids}
        ind = indicadores(sub)
        brecha = ind["no_implementado"] + 0.5 * ind["parcial"]
        filas.append({"control_id": c.id, "nombre": c.nombre, "salvaguardas": len(ids), "brecha": brecha,
                      "no_implementado": ind["no_implementado"], "parcial": ind["parcial"],
                      "no_verificado": ind["no_verificado"], "implementacion": ind["implementacion"]})
    return sorted(filas, key=lambda f: (-f["brecha"], -f["no_verificado"]))


# ------------------------------------------------------------- vista ejecutiva
HORIZONTES = ("0-30", "30-90", "90-180")


def severidad_de(probabilidad, impacto) -> str | None:
    """Severidad = probabilidad × impacto (1 a 5 cada uno): 15 o más alta, 8 a 14 media, menos de 8 baja.
    La calcula el código para que el mapa de riesgos y «Riesgos altos» siempre cuadren."""
    if not all(isinstance(x, int) and 1 <= x <= 5 for x in (probabilidad, impacto)):
        return None
    producto = probabilidad * impacto
    return "alta" if producto >= 15 else "media" if producto >= 8 else "baja"


def madurez_por_area(matriz: dict[str, Resultado]) -> list[dict]:
    """Las 7 áreas de controls.AREAS, de peor a mejor. Madurez = la fórmula de la implementación global sobre las
    salvaguardas del área; None si ninguna es evaluable (va al final)."""
    filas = []
    for clave, nombre, numeros in AREAS:
        ids = [s.id for c in catalogo().controles if c.numero in numeros for s in c.ig1]
        if not ids:
            continue
        ind = indicadores({i: matriz[i] for i in ids if i in matriz})
        filas.append({"clave": clave, "nombre": nombre, "controles": [f"CIS-{n:02d}" for n in numeros],
                      "salvaguardas": ids, "madurez": ind["implementacion"], "cobertura": ind["cobertura"], **{
                          e: ind[e] for e in ESTADOS}})
    return sorted(filas, key=lambda f: (f["madurez"] is None, f["madurez"] if f["madurez"] is not None else 0))


def proyeccion(matriz: dict[str, Resultado], iniciativas: list[dict]) -> dict:
    """ESTIMACIÓN de la implementación si las salvaguardas de las iniciativas pasan a Implementado. Usa la misma
    fórmula de los indicadores; 'aportes' es lo que suma cada iniciativa por sí sola (en puntos porcentuales)."""
    hoy = indicadores(matriz)["implementacion"]

    def con(ids) -> float | None:
        m = {k: (Resultado(k, "implementado") if k in ids and v.estado != "no_aplicable" else v) for k, v in matriz.items()}
        return indicadores(m)["implementacion"]

    todas = {s for ini in iniciativas for s in ini.get("salvaguardas", []) if s in matriz}
    aportes = []
    for ini in iniciativas:
        valor = con({s for s in ini.get("salvaguardas", []) if s in matriz})
        aportes.append(round(valor - hoy, 1) if valor is not None and hoy is not None else None)
    return {"hoy": hoy, "estimado": con(todas) if todas else hoy, "aportes": aportes}


def horizonte_de(ini: dict) -> tuple[str, bool]:
    """Horizonte de la iniciativa y si es una estimación. Las evaluaciones anteriores no lo traen: se deduce del
    tipo (quick win → 0-30 días; proyecto → 90-180) y se marca como estimación."""
    if ini.get("horizonte") in HORIZONTES:
        return ini["horizonte"], False
    return ("0-30" if ini.get("tipo") == "quick_win" else "90-180"), True


def nivel_riesgo(res: dict, riesgos: list[dict]) -> tuple[str | None, bool]:
    """Nivel global (Alto/Medio/Bajo) y si se calculó. Sin el campo del modelo, sale de la severidad más alta."""
    if (res or {}).get("nivel_riesgo") in ("Alto", "Medio", "Bajo"):
        return res["nivel_riesgo"], False
    sev = {r.get("severidad") for r in riesgos or []}
    for s, nivel in (("alta", "Alto"), ("media", "Medio"), ("baja", "Bajo")):
        if s in sev:
            return nivel, True
    return None, True


# --------------------------------------------------------------------- versiones
@dataclass
class Version:
    nombre: str
    fecha: str
    matriz: dict[str, Resultado]
    reporte: dict | None = None
    cerrada: bool = False  # True cuando ya tiene reporte: a partir de ahí no se modifica

    def indicadores(self) -> dict:
        return indicadores(self.matriz)

    def a_dict(self) -> dict:
        return {"nombre": self.nombre, "fecha": self.fecha, "reporte": self.reporte, "cerrada": self.cerrada,
                "matriz": {k: asdict(v) for k, v in self.matriz.items()}}

    @classmethod
    def de_dict(cls, d: dict) -> "Version":
        return cls(d["nombre"], d["fecha"], {k: Resultado(**v) for k, v in d["matriz"].items()}, d.get("reporte"),
                   d.get("cerrada", False))


@dataclass
class Cambio:
    """Propuesta de actualización de una salvaguarda a partir del PDF 2 (sujeta a validación)."""
    id: str
    estado_inicial: str
    estado_propuesto: str
    justificacion: str
    iniciativa: str = ""
    pagina: int | None = None
    seccion: str = ""
    cita: str = ""
    cita_verificada: bool = False
    decision: str = "pendiente"  # pendiente | aprobado | rechazado
    tipo: str = "estado"         # "estado" (cambia el estado) | "evidencia" (mismo estado, cita y justificación nuevas)

    @property
    def aprobable(self) -> bool:
        """Solo con cita verificada en el PDF 2, y que cambie algo: el estado o la evidencia."""
        return self.cita_verificada and (self.tipo == "evidencia" or self.estado_propuesto != self.estado_inicial)


# ---------------------------------------------------------------------- proyecto
@dataclass
class Proyecto:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    nombre: str = "Evaluación sin nombre"
    creado: str = field(default_factory=ahora)
    documentos: dict[str, Documento] = field(default_factory=dict)
    ficha: dict | None = None
    ficha_validada: bool = False
    ajustes: list[dict] = field(default_factory=list)      # Etapa 2.5: ajustes registrados por el equipo
    v1: Version | None = None
    v2: Version | None = None
    iniciativas: list[dict] = field(default_factory=list)  # análisis del PDF 2
    cambios: list[Cambio] = field(default_factory=list)
    sin_cambio: list[dict] = field(default_factory=list)    # salvaguardas relacionadas que quedan igual, con motivo (F1)
    alertas: list[str] = field(default_factory=list)        # contradicciones y fechas del PDF 2 (C1, C2)
    consumo: list[dict] = field(default_factory=list)       # tokens y costo estimado de cada llamada a Claude
    modelo: str = ""                                        # modelo de Claude de esta evaluación (uno solo)
    chat: list[dict] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)        # bitácora de validaciones automáticas

    # ----------------------------------------------------------------- etapas
    @property
    def etapa(self) -> str:
        if self.v2 and self.v2.cerrada:
            return "actualizado"
        if self.v2 or self.cambios or "pdf2" in self.documentos:
            return "iniciativas"
        if self.v1 and self.v1.cerrada:
            return "reporte"
        if self.v1:
            return "evaluacion"
        return "contexto"

    @property
    def vigente(self) -> Version | None:
        return self.v2 or self.v1

    # ----------------------------------------------------------- evaluación
    def iniciar_v1(self) -> None:
        self.v1 = Version("v1 · Evaluación inicial", ahora(), matriz_vacia())

    def aplicar_lote(self, items: list[dict], doc: Documento) -> None:
        if self.v1 is None or self.v1.cerrada:
            raise ValueError("La evaluación inicial ya está cerrada; los cambios van a la versión v2.")
        vistos = set()
        for item in items:
            sid = item.get("id")
            if sid not in self.v1.matriz or sid in vistos:
                continue
            vistos.add(sid)
            r, avisos = validar_resultado(item, doc)
            self.v1.matriz[sid] = r
            self.avisos.extend(avisos)

    def completar_faltantes(self, ids_esperados: list[str]) -> None:
        """R: no se omiten salvaguardas. Las que el modelo no devolvió quedan No verificado, visibles."""
        for sid in ids_esperados:
            r = self.v1.matriz[sid]
            if not r.justificacion:
                r.justificacion = "El agente no devolvió una evaluación para esta salvaguarda."
                r.observaciones = SIN_INFORMACION
                self.avisos.append(f"{sid}: el modelo no la evaluó; se registró como No verificado.")

    def cerrar_v1(self, reporte: dict) -> None:
        self.v1.reporte = reporte
        self.v1.cerrada = True

    # --------------------------------------------------------------- PDF 2
    def registrar_cambios(self, decisiones: list[dict], doc: Documento, relacionadas=()) -> None:
        """Registra UNA decisión por salvaguarda (F1): cambio de estado, actualización de evidencia (F9) o sin cambio.
        Las salvaguardas relacionadas con una iniciativa que se quedaron sin decisión se registran como tales,
        para que la omisión quede a la vista del auditor."""
        base = self.v1.matriz
        self.cambios, self.sin_cambio = [], []
        vistos = set()
        for d in decisiones:
            sid = d.get("id")
            if sid not in base or sid in vistos:
                continue
            vistos.add(sid)
            tipo = d.get("tipo") or "cambio_estado"
            nuevo = d.get("estado_propuesto") if d.get("estado_propuesto") in ESTADOS else base[sid].estado
            if tipo == "cambio_estado" and nuevo == base[sid].estado:
                tipo = "actualizar_evidencia"  # mismo estado: lo que cambia es la evidencia
            if tipo == "sin_cambio":
                self.sin_cambio.append({"id": sid, "motivo": d.get("motivo_sin_cambio") or "sin_evidencia",
                                        "detalle": (d.get("justificacion") or "").strip(), "iniciativa": d.get("iniciativa", "")})
                continue
            pagina = verificar_cita(doc, d.get("cita", ""), d.get("pagina"))
            c = Cambio(sid, base[sid].estado, nuevo if tipo == "cambio_estado" else base[sid].estado,
                       (d.get("justificacion") or "").strip(), d.get("iniciativa", ""), pagina or d.get("pagina"),
                       (d.get("seccion") or "").strip(), (d.get("cita") or "").strip(), pagina is not None,
                       tipo="estado" if tipo == "cambio_estado" else "evidencia")
            if not c.cita_verificada:
                self.avisos.append(f"{sid}: propuesta sin cita verificable en el PDF 2; no se puede aprobar.")
            self.cambios.append(c)
        for sid in dict.fromkeys(relacionadas):
            if sid in base and sid not in vistos:
                self.sin_cambio.append({"id": sid, "motivo": "sin_decision", "iniciativa": "",
                                        "detalle": "El agente no emitió una decisión para esta salvaguarda relacionada."})
                self.avisos.append(f"{sid}: relacionada con una iniciativa del PDF 2, pero el agente no emitió decisión; "
                                   "revísala manualmente (F1).")

    def decidir(self, sid: str, decision: str) -> None:
        for c in self.cambios:
            if c.id == sid:
                if decision == "aprobado" and not c.aprobable:
                    raise ValueError("Solo se pueden aprobar cambios con evidencia verificable en el PDF 2.")
                c.decision = decision

    def crear_v2(self) -> list[str]:
        """Copia la v1 y aplica SOLO los cambios aprobados (R10, R11). Devuelve los ids modificados."""
        matriz = copy.deepcopy(self.v1.matriz)
        modificados = []
        for c in self.cambios:
            if c.decision != "aprobado":
                continue
            anterior = matriz[c.id]
            if c.tipo == "evidencia":  # F9: mismo estado, evidencia vigente del PDF 2
                matriz[c.id] = Resultado(
                    c.id, anterior.estado, anterior.aplicabilidad, c.justificacion, "pdf2", c.pagina, c.seccion, c.cita,
                    f"Evidencia actualizada con el PDF 2 (iniciativa «{c.iniciativa}»); el estado no cambia. Aprobado por el auditor.")
                continue
            matriz[c.id] = Resultado(
                c.id, c.estado_propuesto, "no_aplica" if c.estado_propuesto == "no_aplicable" else "aplica",
                c.justificacion, "pdf2", c.pagina, c.seccion, c.cita,
                f"Actualizado desde «{ETIQUETA[anterior.estado]}» por la iniciativa «{c.iniciativa}» (aprobado por el auditor).")
            modificados.append(c.id)
        self.v2 = Version("v2 · Evaluación actualizada", ahora(), matriz)
        return modificados

    # ----------------------------------------------------------- persistencia
    def a_dict(self) -> dict:
        return {
            "id": self.id, "nombre": self.nombre, "creado": self.creado,
            "documentos": {k: d.a_dict() for k, d in self.documentos.items()},
            "ficha": self.ficha, "ficha_validada": self.ficha_validada, "ajustes": self.ajustes,
            "v1": self.v1.a_dict() if self.v1 else None, "v2": self.v2.a_dict() if self.v2 else None,
            "iniciativas": self.iniciativas, "cambios": [asdict(c) for c in self.cambios],
            "sin_cambio": self.sin_cambio, "alertas": self.alertas, "consumo": self.consumo, "modelo": self.modelo, "chat": self.chat,
            "avisos": self.avisos,
        }

    @classmethod
    def de_dict(cls, d: dict) -> "Proyecto":
        p = cls(
            id=d["id"], nombre=d["nombre"], creado=d["creado"],
            documentos={k: Documento.de_dict(v) for k, v in d.get("documentos", {}).items()},
            ficha=normalizar_ficha(d.get("ficha")), ficha_validada=d.get("ficha_validada", False), ajustes=d.get("ajustes", []),
            v1=Version.de_dict(d["v1"]) if d.get("v1") else None, v2=Version.de_dict(d["v2"]) if d.get("v2") else None,
            iniciativas=d.get("iniciativas", []), cambios=[Cambio(**c) for c in d.get("cambios", [])],
            sin_cambio=d.get("sin_cambio", []), alertas=d.get("alertas", []), consumo=d.get("consumo", []), modelo=d.get("modelo", ""),
            chat=[m for m in d.get("chat", []) if m.get("tipo") != "respuesta"], avisos=d.get("avisos", []))
        p._descartar_declaraciones()
        return p

    def _descartar_declaraciones(self) -> None:
        """Evaluaciones guardadas antes de quitar las preguntas Sí/No: esas respuestas no son evidencia
        documental, así que la salvaguarda vuelve a No verificado."""
        for version in (self.v1, self.v2):
            if not version:
                continue
            for sid, r in version.matriz.items():
                if r.fuente == "declaracion":
                    version.matriz[sid] = Resultado(sid, justificacion=(
                        "Se descartó una respuesta Sí/No del responsable: solo cuenta la evidencia documental."))
                    self.avisos.append(f"{sid} ({version.nombre}): se descartó una respuesta Sí/No; queda No verificado.")


def normalizar_ficha(ficha: dict | None) -> dict | None:
    """D5: la ficha usa "resumen_contexto" (antes "resumen_ejecutivo", que se confundía con el de los reportes)."""
    if ficha and "resumen_contexto" not in ficha and "resumen_ejecutivo" in ficha:
        ficha["resumen_contexto"] = ficha.pop("resumen_ejecutivo")
    return ficha


# ------------------------------------------- situación tras el PDF 2 (reglas fijas, F4-F6)
_RANGO = {"no_verificado": 0, "no_implementado": 0, "parcial": 1, "implementado": 2}
_BAJAR = {"alta": "media", "media": "baja", "baja": "baja"}
SITUACION_RIESGO = {"mitigado": "Mitigado", "reducido": "Reducido", "permanece": "Permanece"}


def _cubierta(r: Resultado) -> bool:
    return r.estado in ("implementado", "no_aplicable")


def _mejoro(v1: dict[str, Resultado], v2: dict[str, Resultado], sid: str) -> bool:
    return v2[sid].estado != "no_aplicable" and _RANGO.get(v2[sid].estado, 0) > _RANGO.get(v1[sid].estado, 0)


def situacion_riesgos(riesgos: list[dict], v1: dict[str, Resultado], v2: dict[str, Resultado]) -> list[dict]:
    """Cada riesgo original se evalúa SOLO con el estado v2 de sus propias salvaguardas (F4, F5):
    todas cubiertas → mitigado (severidad residual baja); alguna mejoró → reducido (un nivel menos);
    ninguna mejoró → permanece (misma severidad)."""
    salida = []
    for r in riesgos:
        ids = [s for s in r.get("salvaguardas", []) if s in v2]
        mejoradas = [s for s in ids if _mejoro(v1, v2, s)]
        sev = r.get("severidad") or "media"
        if ids and all(_cubierta(v2[s]) for s in ids):
            sit, residual = "mitigado", "baja"
        elif mejoradas:
            sit, residual = "reducido", _BAJAR.get(sev, sev)
        else:
            sit, residual = "permanece", sev
        salida.append({"situacion": sit, "severidad_residual": residual, "mejoradas": mejoradas,
                       "pendientes": [s for s in ids if not _cubierta(v2[s])]})
    return salida


def estado_iniciativas(iniciativas: list[dict], v1: dict[str, Resultado], v2: dict[str, Resultado]) -> list[dict]:
    """F6: completada si TODAS sus salvaguardas están Implementado (o No aplicable) en v2; en progreso si al menos
    una mejoró; pendiente si ninguna. Se decide por salvaguardas, no por el nombre de la iniciativa del PDF 2."""
    salida = []
    for ini in iniciativas:
        ids = [s for s in ini.get("salvaguardas", []) if s in v2]
        mejoradas = [s for s in ids if _mejoro(v1, v2, s)]
        if ids and all(_cubierta(v2[s]) for s in ids):
            estado = "completada"
        elif mejoradas:
            estado = "en_progreso"
        else:
            estado = "pendiente"
        salida.append({"estado": estado, "mejoradas": mejoradas, "pendientes": [s for s in ids if not _cubierta(v2[s])]})
    return salida


def citas_repetidas(matriz: dict[str, Resultado]) -> list[str]:
    """A2: la misma cita usada para salvaguardas distintas suele indicar evidencia poco pertinente."""
    por_cita: dict[str, list[str]] = {}
    for sid, r in matriz.items():
        if r.cita:
            por_cita.setdefault(" ".join(r.cita.lower().split()), []).append(sid)
    return [f"{', '.join(ids)}: comparten la misma cita; revisa que sea pertinente para cada salvaguarda (A2)."
            for ids in por_cita.values() if len(ids) > 1]


def validar_reporte(rep: dict, matriz: dict[str, Resultado], ids_brechas: list[str], clave_roadmap: str = "iniciativas",
                    clave_riesgos: str = "riesgos", texto_fuente: str = "") -> list[str]:
    """Evita contradicciones entre matriz e informe (F10):
    - riesgos e iniciativas solo con salvaguardas que son brecha (no implementadas, parciales o no verificadas);
    - un riesgo apoyado solo en No verificado se señala (B1: la incertidumbre no es incumplimiento);
    - "controles con mayores brechas" = la lista calculada, y una explicación vacía se completa con datos de la matriz;
    - los campos de texto vacíos quedan en la bitácora."""
    avisos = []
    brecha = {sid for sid, r in matriz.items() if r.estado in ("no_implementado", "parcial", "no_verificado")}

    def filtrar(item: dict, donde: str):
        quitar = [s for s in item.get("salvaguardas", []) if s not in brecha]
        if quitar:
            avisos.append(f"{donde}: se quitaron {', '.join(quitar)} porque no son brecha en la matriz.")
        item["salvaguardas"] = [s for s in dict.fromkeys(item.get("salvaguardas", [])) if s in brecha]

    def vacios(item: dict, donde: str, campos: tuple):
        faltan = [c for c in campos if not str(item.get(c) or "").strip()]
        if faltan:
            avisos.append(f"{donde}: el modelo dejó vacío {', '.join(faltan)}.")

    for clave, nombre in ((clave_riesgos, "riesgos"), (clave_roadmap, "iniciativas")):
        if clave in rep and len(rep[clave]) != 5:
            avisos.append(f"El modelo devolvió {len(rep[clave])} {nombre} en lugar de 5 (la actividad pide exactamente 5).")
    for i, r in enumerate(rep.get(clave_riesgos, []), 1):
        filtrar(r, f"Riesgo {i}")
        sev = severidad_de(r.get("probabilidad"), r.get("impacto"))
        if sev:
            # La severidad la decide el código; la justificación técnica reúne las dos de una línea.
            r["severidad"] = sev
            r["justificacion"] = (f"Probabilidad {r['probabilidad']}/5: {str(r.get('justificacion_probabilidad') or '').strip()} "
                                  f"Impacto {r['impacto']}/5: {str(r.get('justificacion_impacto') or '').strip()}").strip()
        elif "probabilidad" in r or "impacto" in r:
            avisos.append(f"Riesgo {i}: probabilidad o impacto fuera de la escala 1-5; no se pudo calcular la severidad.")
        vacios(r, f"Riesgo {i}", ("titulo", "descripcion", "consecuencia", "justificacion")
               + (("consecuencia_negocio", "justificacion_probabilidad", "justificacion_impacto") if sev else ()))
        if not r["salvaguardas"]:
            avisos.append(f"Riesgo {i}: no se apoya en ninguna salvaguarda con brecha; el formato de 5 riesgos obligó a "
                          "incluirlo (revisa si sigue siendo vigente).")
        elif all(matriz[s].estado == "no_verificado" for s in r["salvaguardas"]):
            avisos.append(f"Riesgo {i}: se apoya solo en salvaguardas No verificado; es incertidumbre, no una brecha "
                          "confirmada (B1). Conviene tratarlo como necesidad de verificación.")
    roadmap = rep.get(clave_roadmap, [])
    for i, ini in enumerate(roadmap, 1):
        filtrar(ini, f"Iniciativa {i}")
        vacios(ini, f"Iniciativa {i}", ("titulo", "descripcion", "beneficio"))
        if not ini["salvaguardas"]:
            avisos.append(f"Iniciativa {i}: no cierra ninguna salvaguarda con brecha en la matriz.")
        ini["riesgos"] = [n for n in ini.get("riesgos", []) if 1 <= n <= 5]
        if "horizonte" in ini and ini["horizonte"] not in HORIZONTES:
            ini["horizonte"], _ = horizonte_de({"tipo": ini.get("tipo")})
            avisos.append(f"Iniciativa {i}: horizonte no válido; se dedujo de su tipo.")
    roadmap.sort(key=lambda x: x.get("prioridad", 9))
    res = rep.get("resumen_ejecutivo", {})
    if "controles_mayores_brechas" in res:
        explicacion = {c["control_id"]: (c.get("explicacion") or "").strip() for c in res["controles_mayores_brechas"]}
        res["controles_mayores_brechas"] = []
        for cid in ids_brechas:
            texto = explicacion.get(cid, "")
            if not texto:
                texto = _explicacion_brecha(matriz, cid)
                avisos.append(f"{cid}: el modelo no explicó la brecha; se completó con los datos de la matriz.")
            res["controles_mayores_brechas"].append({"control_id": cid, "explicacion": texto})
    avisos += validar_presentacion(res, matriz)
    avisos += validar_ejecutivo(res, rep.get(clave_riesgos, []), matriz, texto_fuente)
    for i, r in enumerate(rep.get(clave_riesgos, []), 1):
        corto = " ".join(str(r.get("nombre_corto") or "").split()[:4])
        if not corto:
            avisos.append(f"Riesgo {i}: el modelo no dio nombre corto; se usará uno derivado del activo.")
        r["nombre_corto"] = corto
    return avisos


def validar_presentacion(res: dict, matriz: dict[str, Resultado]) -> list[str]:
    """Campos del dashboard (titular, datos clave, brechas y bases) contra la matriz, para que la gráfica no diga
    algo que la matriz no respalda:
    - un dato "X de Y" solo queda si X <= Y y AMBOS números aparecen en la justificación, cita u observaciones de su
      salvaguarda (el modelo no calcula cifras: las toma de la evidencia);
    - una brecha clave debe ser No implementado o Parcial; una base, Implementado o Parcial."""
    avisos = []
    if not res:
        return avisos
    res["titular"] = str(res.get("titular") or "").strip()

    def numeros(sid: str) -> set[str]:
        r = matriz.get(sid)
        texto = " ".join((r.justificacion, r.cita, r.observaciones)) if r else ""
        return set(re.findall(r"\d+", texto))

    datos = []
    for d in res.get("datos_clave") or []:
        valor, total, sid = d.get("valor"), d.get("total"), d.get("salvaguarda")
        ok = (isinstance(valor, int) and isinstance(total, int) and 0 <= valor <= total and total > 0
              and {str(valor), str(total)} <= numeros(sid) and str(d.get("etiqueta") or "").strip())
        if ok:
            datos.append(d)
        else:
            avisos.append(f"Dato clave «{d.get('etiqueta')}» ({valor} de {total}, {sid}) descartado: la matriz no lo respalda.")
    res["datos_clave"] = datos[:3]
    for clave, validos, nombre in (("brechas_clave", ("no_implementado", "parcial"), "Brecha clave"),
                                   ("bases", ("implementado", "parcial"), "Base aprovechable")):
        quedan = []
        for x in res.get(clave) or []:
            sid = x.get("salvaguarda")
            if sid in matriz and matriz[sid].estado in validos and str(x.get("etiqueta") or "").strip():
                quedan.append(x)
            else:
                avisos.append(f"{nombre} «{x.get('etiqueta')}» ({sid}) descartada: su estado en la matriz no corresponde.")
        res[clave] = quedan[:6]
    return avisos


# Jerga que no debe llegar a la vista ejecutiva (solo se señala: el texto no se reescribe).
JERGA = ("CIS", "IG1", "salvaguarda", "BitLocker", "Entra ID", "Active Directory", "Azure AD", "RDS", "RDP", "MFA", "2FA",
         "EDR", "XDR", "SIEM", "RMM", "VPN", "CVE", "SaaS", "MSP", "endpoint", "hardening", "firewall", "antimalware",
         "SSO", "TLS", "DLP", "GPO", "Intune", "Defender")
_CIFRA = re.compile(r"\d+(?:[.,]\d+)?")


def _cifras(texto: str) -> set[str]:
    return {c.replace(",", ".") for c in _CIFRA.findall(texto or "")}


def jerga_en(texto: str) -> list[str]:
    """Términos técnicos o ids de salvaguarda/página en un texto para el ejecutivo."""
    encontrados = [t for t in JERGA if re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", texto or "", re.I)]
    ids = set(catalogo().ids_ig1())
    encontrados += sorted({m for m in re.findall(r"(?<![\d.])\d{1,2}\.\d{1,2}(?!\.?\d)", texto or "") if m in ids})
    if re.search(r"\bp(?:p|ág)?\.\s*\d", texto or ""):
        encontrados.append("número de página")
    return encontrados


def validar_ejecutivo(res: dict, riesgos: list[dict], matriz: dict[str, Resultado], texto_fuente: str = "") -> list[str]:
    """Campos de la vista ejecutiva (veredicto, impactos, peticiones, consecuencia de negocio):
    - un impacto de negocio con una cifra que no aparece en la ficha ni en la matriz se descarta (no inventar cifras);
    - jerga, ids o páginas y textos más largos de lo pedido quedan en la bitácora (no se reescriben);
    - se conservan como máximo 3 impactos y 3 peticiones."""
    avisos = []
    if not res or not any(k in res for k in ("veredicto", "impactos_negocio", "peticiones")):
        return avisos  # evaluación anterior a la vista ejecutiva
    ind = indicadores(matriz)
    permitidas = _cifras(texto_fuente) | {c for r in matriz.values() for c in _cifras(" ".join((r.justificacion, r.cita, r.observaciones)))}
    permitidas |= {str(ind[k]) for k in ESTADOS} | {str(ind["total"]), "5", "3"}
    permitidas |= {f"{v:g}" for v in (ind["implementacion"], ind["cobertura"]) if v is not None}

    def revisar(texto: str, donde: str, max_palabras: int | None = None):
        if jerga := jerga_en(texto):
            avisos.append(f"{donde}: lenguaje técnico en la vista ejecutiva ({', '.join(jerga)}).")
        if max_palabras and len(texto.split()) > max_palabras:
            avisos.append(f"{donde}: {len(texto.split())} palabras (máximo {max_palabras}).")

    res["veredicto"] = str(res.get("veredicto") or "").strip()
    revisar(res["veredicto"], "Veredicto", 30)
    impactos = []
    for x in res.get("impactos_negocio") or []:
        titulo, linea = str(x.get("titulo") or "").strip(), str(x.get("linea") or "").strip()
        if not (titulo and linea):
            continue
        ajenas = _cifras(f"{titulo} {linea}") - permitidas - set(catalogo().ids_ig1())  # un id es jerga, no cifra
        if ajenas:
            avisos.append(f"Impacto «{titulo}» descartado: la cifra {', '.join(sorted(ajenas))} no aparece en la ficha ni en la matriz.")
            continue
        revisar(f"{titulo} {linea}", f"Impacto «{titulo}»")
        impactos.append({"titulo": titulo, "linea": linea})
    res["impactos_negocio"] = impactos[:3]
    res["peticiones"] = [t for t in (str(x or "").strip() for x in res.get("peticiones") or []) if t][:3]
    for n, t in enumerate(res["peticiones"], 1):
        revisar(t, f"Petición {n}")
    for clave, minimo in (("impactos_negocio", 3), ("peticiones", 3)):
        if len(res[clave]) < minimo:
            avisos.append(f"Vista ejecutiva: {len(res[clave])} {clave.replace('_', ' ')} en lugar de {minimo}.")
    for i, r in enumerate(riesgos or [], 1):
        if r.get("consecuencia_negocio"):
            revisar(str(r["consecuencia_negocio"]), f"Riesgo {i} (consecuencia de negocio)", 20)
    return avisos


def _explicacion_brecha(matriz: dict[str, Resultado], cid: str) -> str:
    ids = [s.id for s in control(cid).ig1]
    partes = []
    for estado in ("no_implementado", "parcial", "no_verificado"):
        sids = [s for s in ids if matriz[s].estado == estado]
        if sids:
            partes.append(f"{ETIQUETA[estado]}: {', '.join(sids)}")
    return "Según la matriz — " + "; ".join(partes) + "." if partes else "Sin brechas registradas en la matriz."


def lotes_por_control(tamano_max: int = 22) -> list[list[str]]:
    """Agrupa las 56 salvaguardas IG1 en lotes por control completo (para no partir un control)."""
    lotes, actual = [], []
    for c in catalogo().controles:
        ids = [s.id for s in c.ig1]
        if actual and len(actual) + len(ids) > tamano_max:
            lotes.append(actual)
            actual = []
        actual += ids
    if actual:
        lotes.append(actual)
    return lotes


def nombre_salvaguarda(sid: str) -> str:
    s = salvaguarda(sid)
    return s.titulo if s else sid
