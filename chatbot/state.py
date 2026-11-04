"""Estado de la evaluación. Es la fuente de verdad: el modelo (Gemini) propone, Python valida."""

from dataclasses import dataclass, field

from .controls import CONTROLES, CONTROLES_POR_ID, ESTADOS


@dataclass
class EstadoControl:
    estado: str = "desconocido"
    justificacion: str = "Sin información todavía."
    fuente: str = "inicial"  # inicial | analisis | respuesta_si_no | seguimiento


@dataclass
class Pregunta:
    control_id: str
    pregunta: str


@dataclass
class Evaluacion:
    controles: dict[str, EstadoControl] = field(
        default_factory=lambda: {c.id: EstadoControl() for c in CONTROLES}
    )
    preguntas_pendientes: list[Pregunta] = field(default_factory=list)
    contexto_empresa: str = ""

    # ---- cambios propuestos por Gemini ----
    def aplicar_actualizaciones(self, actualizaciones: list[dict], fuente: str) -> list[str]:
        """Aplica cambios validando id y estado. Devuelve advertencias de lo descartado."""
        avisos = []
        for a in actualizaciones:
            cid, est = a.get("control_id"), a.get("estado")
            if cid not in CONTROLES_POR_ID:
                avisos.append(f"Control desconocido descartado: {cid}")
                continue
            if est not in ESTADOS:
                avisos.append(f"Estado inválido descartado para {cid}: {est}")
                continue
            self.controles[cid] = EstadoControl(est, a.get("justificacion", ""), fuente)
        return avisos

    def encolar_preguntas(self, preguntas: list[dict]) -> None:
        """Encola preguntas cerradas solo para controles válidos y aún no resueltos."""
        ya = {p.control_id for p in self.preguntas_pendientes}
        for p in preguntas:
            cid = p.get("control_id")
            if cid in CONTROLES_POR_ID and cid not in ya and self.controles[cid].estado in ("desconocido", "parcial"):
                self.preguntas_pendientes.append(Pregunta(cid, p.get("pregunta") or CONTROLES_POR_ID[cid].pregunta_base))
                ya.add(cid)
        # Red de seguridad: todo control 'desconocido' debe acabar preguntándose.
        for c in CONTROLES:
            if self.controles[c.id].estado == "desconocido" and c.id not in ya:
                self.preguntas_pendientes.append(Pregunta(c.id, c.pregunta_base))
                ya.add(c.id)

    # ---- respuestas cerradas (sin llamar a la API) ----
    def pregunta_actual(self) -> Pregunta | None:
        return self.preguntas_pendientes[0] if self.preguntas_pendientes else None

    def responder(self, tiene_control: bool) -> Pregunta:
        p = self.preguntas_pendientes.pop(0)
        if tiene_control:
            self.controles[p.control_id] = EstadoControl(
                "cubierto", f"El responsable confirmó que sí cuenta con el control. Pregunta: «{p.pregunta}»", "respuesta_si_no")
        else:
            self.controles[p.control_id] = EstadoControl(
                "no_cubierto", f"El responsable indicó que no cuenta con el control. Pregunta: «{p.pregunta}»", "respuesta_si_no")
        return p

    # ---- vistas ----
    def resumen(self) -> dict[str, int]:
        cuenta = {e: 0 for e in ESTADOS}
        for ec in self.controles.values():
            cuenta[ec.estado] += 1
        return cuenta

    def porcentaje_cobertura(self) -> float:
        """cubierto = 1, parcial = 0.5, resto = 0."""
        r = self.resumen()
        return round(100 * (r["cubierto"] + 0.5 * r["parcial"]) / len(CONTROLES), 1)

    def como_json(self) -> list[dict]:
        return [
            {"control_id": cid, "nombre": CONTROLES_POR_ID[cid].nombre,
             "estado": ec.estado, "justificacion": ec.justificacion}
            for cid, ec in self.controles.items()
        ]
