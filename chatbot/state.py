"""Modelo de datos del proyecto de evaluación. Es la fuente de verdad: Gemini propone, Python valida.

Reglas que se hacen cumplir AQUÍ (no se confía solo en el prompt):
- La matriz siempre tiene las 56 salvaguardas IG1 (lo que falte queda "No verificado").
- Implementado / Parcial / No implementado / No aplicable exigen una cita que aparezca en el
  documento; si la cita no existe, la salvaguarda queda "No verificado" (R3, R6, R8).
- Los indicadores se calculan con las fórmulas de la actividad, siempre desde la matriz.
- La versión inicial (v1) nunca se modifica después de cerrarse; los cambios del PDF 2 crean
  la versión v2 y solo aplican los aprobados por el auditor (R10, R11, R12).
"""

import copy
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime

from .controls import catalogo, control, salvaguarda
from .documentos import Documento, verificar_cita

ESTADOS = ("implementado", "parcial", "no_implementado", "no_verificado", "no_aplicable")
ETIQUETA = {"implementado": "Implementado", "parcial": "Parcialmente implementado", "no_implementado": "No implementado",
            "no_verificado": "No verificado", "no_aplicable": "No aplicable"}
VALOR = {"implementado": 1.0, "parcial": 0.5, "no_implementado": 0.0}  # No verificado y No aplicable: —
EVALUABLES = tuple(VALOR)
APLICABILIDAD = ("aplica", "no_aplica", "por_determinar")
ETIQUETA_APLICABILIDAD = {"aplica": "Aplica", "no_aplica": "No aplica", "por_determinar": "Por determinar"}
MAX_PREGUNTAS = 15

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
    fuente: str = ""          # "pdf1" | "pdf2" | "declaracion" | "" (sin evidencia)
    pagina: int | None = None
    seccion: str = ""
    cita: str = ""
    observaciones: str = SIN_INFORMACION

    def evidencia(self, documentos: dict | None = None) -> str:
        if self.fuente == "declaracion":
            return "Declaración del responsable (pregunta Sí/No); sin evidencia documental"
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


@dataclass
class Pregunta:
    id: str
    pregunta: str


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
    preguntas_pendientes: list[Pregunta] = field(default_factory=list)
    preguntas_hechas: list[str] = field(default_factory=list)
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

    def encolar_preguntas(self, preguntas: list[dict]) -> None:
        """Preguntas Sí/No solo para salvaguardas No verificado, en el orden del modelo, máximo 15."""
        for p in preguntas:
            sid = p.get("id")
            r = self.v1.matriz.get(sid) if self.v1 else None
            if (r is None or r.estado != "no_verificado" or sid in self.preguntas_hechas
                    or len(self.preguntas_hechas) >= MAX_PREGUNTAS or not p.get("pregunta")):
                continue
            self.preguntas_pendientes.append(Pregunta(sid, p["pregunta"]))
            self.preguntas_hechas.append(sid)

    def pregunta_actual(self) -> Pregunta | None:
        return self.preguntas_pendientes[0] if self.preguntas_pendientes else None

    def responder(self, respuesta: str) -> Pregunta:
        """respuesta: "si" | "no" | "no_se". "No sé" mantiene No verificado (R8)."""
        p = self.preguntas_pendientes.pop(0)
        r = self.v1.matriz[p.id]
        if respuesta == "si":
            self.v1.matriz[p.id] = Resultado(
                p.id, "implementado", "aplica", f"El responsable declaró que sí. Pregunta: «{p.pregunta}»", "declaracion",
                observaciones="Declaración sin evidencia documental: conviene respaldarla con un documento.")
        elif respuesta == "no":
            self.v1.matriz[p.id] = Resultado(
                p.id, "no_implementado", "aplica", f"El responsable confirmó que no. Pregunta: «{p.pregunta}»", "declaracion",
                observaciones="Incumplimiento confirmado por el responsable (no por falta de información).")
        else:
            r.observaciones = f"El responsable no supo responder: «{p.pregunta}». {SIN_INFORMACION}"
        self.chat.append({"tipo": "respuesta", "id": p.id, "respuesta": respuesta})
        return p

    def cerrar_v1(self, reporte: dict) -> None:
        self.v1.reporte = reporte
        self.v1.cerrada = True
        self.preguntas_pendientes.clear()

    # --------------------------------------------------------------- PDF 2
    def registrar_cambios(self, propuestas: list[dict], doc: Documento) -> None:
        base = self.v1.matriz
        self.cambios = []
        vistos = set()
        for p in propuestas:
            sid, nuevo = p.get("id"), p.get("estado_propuesto")
            if sid not in base or nuevo not in ESTADOS or sid in vistos:
                continue
            vistos.add(sid)
            pagina = verificar_cita(doc, p.get("cita", ""), p.get("pagina"))
            c = Cambio(sid, base[sid].estado, nuevo, (p.get("justificacion") or "").strip(), p.get("iniciativa", ""),
                       pagina or p.get("pagina"), (p.get("seccion") or "").strip(), (p.get("cita") or "").strip(),
                       pagina is not None)
            if not c.cita_verificada and nuevo != base[sid].estado:
                self.avisos.append(f"{sid}: cambio propuesto sin cita verificable en el PDF 2; no se puede aprobar.")
            self.cambios.append(c)

    def decidir(self, sid: str, decision: str) -> None:
        for c in self.cambios:
            if c.id == sid:
                if decision == "aprobado" and not (c.cita_verificada and c.estado_propuesto != c.estado_inicial):
                    raise ValueError("Solo se pueden aprobar cambios con evidencia verificable que modifiquen el estado.")
                c.decision = decision

    def crear_v2(self) -> list[str]:
        """Copia la v1 y aplica SOLO los cambios aprobados (R10, R11). Devuelve los ids modificados."""
        matriz = copy.deepcopy(self.v1.matriz)
        modificados = []
        for c in self.cambios:
            if c.decision != "aprobado":
                continue
            anterior = matriz[c.id]
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
            "preguntas_pendientes": [asdict(p) for p in self.preguntas_pendientes],
            "preguntas_hechas": self.preguntas_hechas, "chat": self.chat, "avisos": self.avisos,
        }

    @classmethod
    def de_dict(cls, d: dict) -> "Proyecto":
        return cls(
            d["id"], d["nombre"], d["creado"], {k: Documento.de_dict(v) for k, v in d.get("documentos", {}).items()},
            d.get("ficha"), d.get("ficha_validada", False), d.get("ajustes", []),
            Version.de_dict(d["v1"]) if d.get("v1") else None, Version.de_dict(d["v2"]) if d.get("v2") else None,
            d.get("iniciativas", []), [Cambio(**c) for c in d.get("cambios", [])],
            [Pregunta(**p) for p in d.get("preguntas_pendientes", [])], d.get("preguntas_hechas", []),
            d.get("chat", []), d.get("avisos", []))


def validar_reporte(rep: dict, matriz: dict[str, Resultado], ids_brechas: list[str], clave_roadmap: str = "iniciativas") -> list[str]:
    """Evita contradicciones entre matriz e informe: riesgos e iniciativas solo con salvaguardas que son
    brecha (no implementadas, parciales o no verificadas); controles con brecha solo de la lista calculada."""
    avisos = []
    brecha = {sid for sid, r in matriz.items() if r.estado in ("no_implementado", "parcial", "no_verificado")}

    def filtrar(item: dict, donde: str):
        quitar = [s for s in item.get("salvaguardas", []) if s not in brecha]
        if quitar:
            avisos.append(f"{donde}: se quitaron {', '.join(quitar)} porque no son brecha en la matriz.")
        item["salvaguardas"] = [s for s in dict.fromkeys(item.get("salvaguardas", [])) if s in brecha]

    for i, r in enumerate(rep.get("riesgos", []), 1):
        filtrar(r, f"Riesgo {i}")
    roadmap = rep.get(clave_roadmap, [])
    for i, ini in enumerate(roadmap, 1):
        filtrar(ini, f"Iniciativa {i}")
        ini["riesgos"] = [n for n in ini.get("riesgos", []) if 1 <= n <= 5]
    roadmap.sort(key=lambda x: x.get("prioridad", 9))
    res = rep.get("resumen_ejecutivo", {})
    if "controles_mayores_brechas" in res:
        explicacion = {c["control_id"]: c.get("explicacion", "") for c in res["controles_mayores_brechas"]}
        res["controles_mayores_brechas"] = [{"control_id": cid, "explicacion": explicacion.get(cid, "")} for cid in ids_brechas]
    return avisos


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
