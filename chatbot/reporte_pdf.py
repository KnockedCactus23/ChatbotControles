"""Reporte ejecutivo en PDF (Entregable 3), con el mismo contenido que el reporte HTML.

Usa fpdf2 con las fuentes estándar del PDF: no depende de fuentes del sistema, así que se genera
igual en macOS, Windows y Linux. Esas fuentes usan cp1252 (cubre el español); los pocos símbolos
fuera de esa tabla se sustituyen.

Diseño claro y sobrio pensado para imprimir: A4 vertical, tipografía pequeña y tablas compactas
para acercarse al límite de cinco páginas de la actividad. La matriz completa va en el Excel/CSV.
"""

from fpdf import FPDF
from fpdf.fonts import FontFace

from . import prompts
from .controls import atribucion, control
from .prompts import DIMENSIONES
from .state import ESTADOS, ETIQUETA, SITUACION_RIESGO, Proyecto, Version, formato_pct

# Paleta de impresión (RGB). Coherente con los tokens de estado de la app, pero sobre fondo blanco.
TINTA = (24, 28, 34)
TENUE = (92, 100, 112)
LINEA = (214, 218, 224)
FONDO = (244, 246, 248)
ACENTO = (38, 84, 160)
COLOR_ESTADO = {"implementado": (34, 139, 84), "parcial": (196, 140, 20), "no_implementado": (196, 60, 52),
                "no_verificado": (110, 118, 130), "no_aplicable": (150, 156, 166)}
ESTADO_INICIATIVA = {"completada": "Completada", "en_progreso": "En progreso", "pendiente": "Pendiente"}
TAMANO = {"micro": "Micro", "pequena": "Pequeña", "mediana": "Mediana", "grande": "Grande"}
IMPACTO = {"critico": "Crítico", "alto": "Alto", "medio": "Medio"}

_SUSTITUTOS = {"≥": ">=", "≤": "<=", "✓": "Sí", "✗": "No", "\u2192": "->", "←": "<-", "≈": "~", "×": "x", "−": "-",
               " ": " ", " ": " ", "​": ""}


def _md(texto) -> str:
    """Texto del modelo dentro de una celda con markdown: neutraliza **, __ y -- para que no cambien el formato."""
    return _t(texto).replace("**", "*").replace("__", "_").replace("--", "\u2013")


def _b(texto) -> str:
    return f"**{_md(texto)}**" if texto else ""


def _t(texto) -> str:
    """Texto seguro para las fuentes estándar (cp1252)."""
    s = "" if texto is None else str(texto)
    for a, b in _SUSTITUTOS.items():
        s = s.replace(a, b)
    return s.encode("cp1252", "replace").decode("cp1252")


class _Reporte(FPDF):
    def __init__(self, organizacion: str, documento: str = "Reporte ejecutivo"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.core_fonts_encoding = "windows-1252"  # incluye •, —, comillas tipográficas (latin-1 no)
        self.organizacion = organizacion
        self.documento = documento
        self.set_margins(15, 16, 15)
        self.set_auto_page_break(True, margin=16)
        self.set_title(_t(f"{documento} · {organizacion}"))
        self.set_author(_t(prompts.NOMBRE_AGENTE))
        self.set_creator(_t(prompts.NOMBRE_AGENTE))

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*TENUE)
        self.cell(0, 5, _t(f"{prompts.NOMBRE_AGENTE} · {self.documento} · {self.organizacion}"), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*LINEA)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-11)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*TENUE)
        self.cell(0, 4, _t(atribucion()), align="L")
        self.set_x(self.l_margin)
        self.cell(0, 4, f"{self.page_no()} / {{nb}}", align="R")

    # ------------------------------------------------------------ piezas
    @property
    def ancho(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def titulo_seccion(self, texto: str, sub: str = ""):
        if self.get_y() > self.h - 50:  # no dejar un título huérfano al pie de página
            self.add_page()
        self.ln(3)
        self.set_font("Helvetica", "B", 11.5)
        self.set_text_color(*TINTA)
        self.cell(0, 6.5, _t(texto), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*ACENTO)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.l_margin + 14, self.get_y())
        self.set_line_width(0.2)
        self.ln(1.8)
        if sub:
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*TENUE)
            self.multi_cell(0, 4, _t(sub), new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

    def subtitulo(self, texto: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*TINTA)
        self.cell(0, 5, _t(texto), new_x="LMARGIN", new_y="NEXT")

    def parrafo(self, texto: str, tam: float = 9):
        if not texto:
            return
        self.set_font("Helvetica", "", tam)
        self.set_text_color(*TINTA)
        self.multi_cell(0, tam * 0.5, _t(texto), new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def vinetas(self, items: list[str], tam: float = 8.8):
        self.set_font("Helvetica", "", tam)
        self.set_text_color(*TINTA)
        for it in items:
            if not it:
                continue
            self.set_x(self.l_margin + 2)
            self.multi_cell(self.ancho - 2, tam * 0.48, _t(f"•  {it}"), new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def tabla(self, encabezado: list[str], filas: list[list[str]], anchos: list[float], tam: float = 7.2):
        """Las celdas ya vienen preparadas con _md()/_b() (markdown: **negrita**)."""
        self.set_font("Helvetica", "", tam)
        self.set_text_color(*TINTA)
        self.set_draw_color(*LINEA)
        self.set_fill_color(255, 255, 255)
        cabecera = FontFace(emphasis="BOLD", color=TINTA, fill_color=FONDO)
        with self.table(col_widths=anchos, width=self.ancho, line_height=tam * 0.45, padding=(1.1, 1.3),
                        headings_style=cabecera, text_align="LEFT", borders_layout="HORIZONTAL_LINES",
                        cell_fill_mode="NONE", markdown=True, first_row_as_headings=True) as t:
            fila = t.row()
            for h in encabezado:
                fila.cell(_md(h))
            for datos in filas:
                fila = t.row()
                for valor in datos:
                    fila.cell(valor)
        self.ln(2)

    def tarjetas(self, ind: dict, previo: dict | None = None):
        """Dashboard: implementación y cobertura destacadas, y el conteo por estado."""
        y = self.get_y()
        ancho_kpi = (self.ancho - 4) / 2
        for k, (nombre, clave) in enumerate([("Implementación IG1", "implementacion"), ("Cobertura IG1", "cobertura")]):
            x = self.l_margin + k * (ancho_kpi + 4)
            self.set_fill_color(*FONDO)
            self.rect(x, y, ancho_kpi, 17, style="F")
            self.set_xy(x + 4, y + 2.5)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*TENUE)
            self.cell(ancho_kpi - 8, 4, _t(nombre))
            self.set_xy(x + 4, y + 7)
            self.set_font("Helvetica", "B", 17)
            self.set_text_color(*TINTA)
            valor = formato_pct(ind[clave])
            if previo is not None:
                valor += f"   (v1: {formato_pct(previo[clave])})"
            self.cell(ancho_kpi - 8, 8, _t(valor))
        self.set_y(y + 20)
        ancho_estado = self.ancho / len(ESTADOS)
        y = self.get_y()
        for k, e in enumerate(ESTADOS):
            x = self.l_margin + k * ancho_estado
            self.set_fill_color(*COLOR_ESTADO[e])
            self.rect(x, y + 1.2, 2.2, 2.2, style="F")
            self.set_xy(x + 3.5, y)
            self.set_font("Helvetica", "B", 9.5)
            self.set_text_color(*TINTA)
            self.cell(10, 4.6, str(ind[e]))
            self.set_xy(x + 3.5, y + 4.6)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*TENUE)
            self.cell(ancho_estado - 4, 3.6, _t(ETIQUETA[e]))
        self.set_y(y + 11)


# ------------------------------------------------------------------ bloques
def _resumen(pdf: _Reporte, res: dict, actualizado: bool = False):
    pdf.subtitulo("Postura actualizada" if actualizado else "Postura inicial")
    pdf.parrafo(res.get("postura_inicial"))
    brechas = res.get("controles_mayores_brechas") or []
    if brechas:
        pdf.subtitulo("Controles con mayores brechas")
        pdf.vinetas([f"{b.get('control_id')} · {_nombre_control(b.get('control_id'))}: {b.get('explicacion', '')}"
                     for b in brechas])
    faltante = res.get("informacion_faltante") or []
    if faltante:
        pdf.subtitulo("Información faltante")
        pdf.vinetas(faltante)
    if res.get("principales_riesgos"):
        pdf.subtitulo("Principales riesgos")
        pdf.parrafo(res.get("principales_riesgos"))
    if res.get("resultados_preliminares"):
        pdf.subtitulo("Resultados preliminares")
        pdf.parrafo(res.get("resultados_preliminares"))


def _nombre_control(cid) -> str:
    try:
        return control(cid).nombre
    except Exception:
        return ""


def _riesgos(pdf: _Reporte, lista: list[dict], situacion: list[dict] | None = None):
    filas = []
    for i, r in enumerate(lista):
        sev = (r.get("severidad") or "").lower()
        fila = [f"{_b(f'{i + 1}. ' + r.get('titulo', ''))}\n{_md(r.get('descripcion'))}", _md(r.get("activo_proceso")),
                _md(r.get("deficiencia")), _md(r.get("consecuencia")),
                f"{_b(sev.capitalize())}\n{_md(r.get('justificacion'))}", _md(", ".join(r.get("salvaguardas", [])))]
        if situacion is not None:
            s = situacion[i] if i < len(situacion) else {}
            fila.append(f"{_b('Reducido' if s.get('situacion') == 'reducido' else 'Permanece')}\n{_md(s.get('explicacion'))}")
        filas.append(fila)
    encabezado = ["Riesgo", "Activo o proceso", "Deficiencia", "Consecuencia probable", "Severidad y justificación", "IDs CIS"]
    anchos = [44, 24, 30, 30, 36, 16]
    if situacion is not None:
        encabezado.append("Tras las mejoras")
        anchos = [36, 20, 24, 24, 30, 14, 32]
    pdf.tabla(encabezado, filas, anchos)


def _roadmap(pdf: _Reporte, lista: list[dict], titulos_riesgos: list[str], estados: list[dict] | None = None):
    filas = []
    for i, ini in enumerate(lista):
        rs = ", ".join(f"{n}. {titulos_riesgos[n - 1]}" for n in ini.get("riesgos", []) if 0 < n <= len(titulos_riesgos))
        fila = [_b(ini.get("prioridad", "")), f"{_b(ini.get('titulo'))}\n{_md(ini.get('descripcion'))}", _md(rs),
                _md(", ".join(ini.get("salvaguardas", []))), _md(ini.get("beneficio")),
                _md((ini.get("esfuerzo") or "").capitalize()), _b("Quick win" if ini.get("tipo") == "quick_win" else "Proyecto")]
        if estados is not None:
            e = estados[i] if i < len(estados) else {}
            fila.append(f"{_b(ESTADO_INICIATIVA.get(e.get('estado'), ''))}\n{_md(e.get('explicacion'))}")
        filas.append(fila)
    encabezado = ["#", "Iniciativa", "Riesgo que reduce", "IDs CIS", "Beneficio esperado", "Esfuerzo", "Tipo"]
    anchos = [6, 50, 32, 18, 42, 14, 18]
    if estados is not None:
        encabezado.append("Estado")
        anchos = [6, 40, 26, 15, 34, 13, 15, 31]
    pdf.tabla(encabezado, filas, anchos)


def _riesgos_tras_mejoras(pdf: _Reporte, lista: list[dict], situacion: list[dict]):
    """v2: el detalle de cada riesgo ya está en la sección v1; aquí solo cómo quedó."""
    filas = []
    for i, r in enumerate(lista):
        s = situacion[i] if i < len(situacion) else {}
        clave = s.get("situacion") if s.get("situacion") in SITUACION_RIESGO else "permanece"
        residual = (s.get("severidad_residual") or "").capitalize()
        filas.append([_b(f"{i + 1}. {r.get('titulo', '')}"),
                      _md((r.get("severidad") or "").capitalize() + (f" \u2192 {residual}" if residual else "")),
                      _md(", ".join(r.get("salvaguardas", []))), _b(SITUACION_RIESGO[clave]), _md(s.get("explicacion"))])
    pdf.tabla(["Riesgo (v1)", "Severidad (residual)", "IDs CIS", "Situación", "Explicación"], filas, [48, 22, 20, 18, 72])


def _estado_iniciativas(pdf: _Reporte, lista: list[dict], estados: list[dict]):
    filas = []
    for i, ini in enumerate(lista):
        e = estados[i] if i < len(estados) else {}
        filas.append([_b(ini.get("prioridad", "")), _b(ini.get("titulo")),
                      _md("Quick win" if ini.get("tipo") == "quick_win" else "Proyecto"),
                      _b(ESTADO_INICIATIVA.get(e.get("estado"), "")), _md(e.get("explicacion"))])
    pdf.tabla(["#", "Iniciativa (roadmap v1)", "Tipo", "Estado", "Explicación"], filas, [6, 56, 18, 20, 80])


def _comparacion(pdf: _Reporte, i1: dict, i2: dict, modificados: list[str]):
    filas = [[_b("Implementación IG1"), _md(formato_pct(i1["implementacion"])), _b(formato_pct(i2["implementacion"]))],
             [_b("Cobertura IG1"), _md(formato_pct(i1["cobertura"])), _b(formato_pct(i2["cobertura"]))]]
    filas += [[_md(ETIQUETA[e]), str(i1[e]), str(i2[e])] for e in ESTADOS]
    pdf.tabla(["Indicador", "v1 · Inicial", "v2 · Actualizada"], filas, [80, 50, 50], tam=7.6)
    pdf.parrafo(f"Salvaguardas modificadas: {', '.join(modificados) or 'ninguna'}", tam=8)


def _version(pdf: _Reporte, p: Proyecto, v: Version):
    rep = v.reporte
    es_v2 = v is p.v2
    riesgos_v1 = p.v1.reporte.get("riesgos", [])
    titulos = [r.get("titulo", "") for r in riesgos_v1]
    pdf.titulo_seccion(f"Dashboard · {v.nombre}", f"Fecha: {v.fecha}. Valores calculados por el sistema a partir de la matriz "
                                                  "de las 56 salvaguardas (la matriz completa está en el Excel).")
    pdf.tarjetas(v.indicadores(), p.v1.indicadores() if es_v2 else None)
    if es_v2:
        aprobados = [c.id for c in p.cambios if c.decision == "aprobado"]
        pdf.titulo_seccion("Cambios derivados del PDF 2")
        pdf.parrafo(rep.get("resumen_cambios"))
        _comparacion(pdf, p.v1.indicadores(), v.indicadores(), aprobados)
        if p.cambios:
            pdf.subtitulo("Decisiones del auditor")
            pdf.tabla(["ID", "Cambio", "Justificación", "Evidencia", "Decisión"],
                      [[_b(c.id), _md(f"{ETIQUETA.get(c.estado_inicial, c.estado_inicial)}: evidencia actualizada"
                                     if c.tipo == "evidencia" else
                                     f"{ETIQUETA.get(c.estado_inicial, c.estado_inicial)} \u2192 "
                                     f"{ETIQUETA.get(c.estado_propuesto, c.estado_propuesto)}"),
                        _md(c.justificacion), _md(f"PDF 2 · p. {c.pagina}" if c.cita_verificada else "Cita no verificada"),
                        _b(c.decision.capitalize())] for c in p.cambios],
                      [12, 46, 70, 26, 26])
    pdf.titulo_seccion("Resumen ejecutivo" + (" actualizado" if es_v2 else ""))
    _resumen(pdf, rep.get("resumen_ejecutivo", {}), es_v2)
    if es_v2:
        pdf.titulo_seccion("Riesgos originales: mitigados, reducidos o que permanecen",
                           "Calculado por el sistema con el estado v2 de las salvaguardas de cada riesgo.")
        _riesgos_tras_mejoras(pdf, riesgos_v1, rep.get("riesgos") or [])
        pdf.titulo_seccion("Iniciativas del roadmap original: completadas o en progreso")
        _estado_iniciativas(pdf, p.v1.reporte.get("iniciativas", []), rep.get("iniciativas_estado") or [])
        riesgos_v2 = rep.get("riesgos_v2") or []
        if riesgos_v2:
            pdf.titulo_seccion("Cinco riesgos vigentes (v2)", "El roadmap actualizado apunta a estos riesgos.")
            _riesgos(pdf, riesgos_v2)
        pdf.titulo_seccion("Roadmap actualizado")
        _roadmap(pdf, rep.get("roadmap", []), [r.get("titulo", "") for r in riesgos_v2] or titulos)
    else:
        pdf.titulo_seccion("Cinco riesgos principales",
                           "Cada riesgo se relaciona solo con salvaguardas que son brecha en la matriz.")
        _riesgos(pdf, riesgos_v1)
        pdf.titulo_seccion("Roadmap de cinco iniciativas")
        _roadmap(pdf, rep.get("iniciativas", []), titulos)


# -------------------------------------------------------------------- API
def reporte_pdf(p: Proyecto, cual: str) -> bytes:
    """Reporte ejecutivo de UNA versión. "v1": reporte inicial (solo PDF 1). "v2": reporte final, con los cambios
    del PDF 2 y la comparación de indicadores frente a v1 (sin repetir la matriz ni el reporte inicial)."""
    v = p.v1 if cual == "v1" else p.v2 if cual == "v2" else None
    if v is None or not v.reporte:
        raise ValueError(f"La versión {cual} aún no tiene reporte.")
    usados = ("pdf1",) if cual == "v1" else ("pdf1", "pdf2")
    fuentes = " · ".join(f"{d.etiqueta}: {d.nombre}" for k, d in p.documentos.items() if k in usados)
    nombre = "Reporte ejecutivo inicial" if cual == "v1" else "Reporte ejecutivo final"
    pdf = _inicio(p, nombre, f"{v.nombre} del {v.fecha}. Fuentes: {fuentes}.")
    if p.ficha:
        pdf.titulo_seccion("Contexto de la empresa")
        pdf.parrafo(p.ficha.get("resumen_contexto") or p.ficha.get("resumen_ejecutivo"))
    _version(pdf, p, v)
    return bytes(pdf.output())


def _inicio(p: Proyecto, documento: str, datos: str) -> _Reporte:
    """Primera página: franja de color, título y datos clave (sin portada aparte para ahorrar páginas)."""
    pdf = _Reporte(p.nombre, documento)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_fill_color(*ACENTO)
    pdf.rect(0, 0, pdf.w, 3, style="F")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*ACENTO)
    pdf.cell(0, 5, _t(f"{prompts.NOMBRE_AGENTE} · CIS Controls v8.1 · Implementation Group 1 (56 salvaguardas)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 19)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, 9, _t(f"{documento} · {p.nombre}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TENUE)
    pdf.multi_cell(0, 4.4, _t(datos), new_x="LMARGIN", new_y="NEXT")
    return pdf


def ficha_pdf(p: Proyecto) -> bytes:
    """Ficha de contexto (Etapa 2): resumen, 10 dimensiones con evidencia, información faltante,
    ambigüedades, perfil de riesgo y ajustes registrados por el equipo (Etapa 2.5)."""
    f = p.ficha or {}
    doc = p.documentos.get("pdf1")
    etiqueta = doc.etiqueta if doc else "PDF 1"
    estado = "validada por el equipo" if p.ficha_validada else "pendiente de validación por el equipo"
    pdf = _inicio(p, "Ficha de contexto",
                  f"Fuente: {etiqueta + ' · ' + doc.nombre if doc else '—'}. Ficha {estado}. Generada: {p.creado}.")

    pdf.titulo_seccion("Resumen del contexto")
    pdf.parrafo(f.get("resumen_contexto") or f.get("resumen_ejecutivo"))

    pdf.titulo_seccion("Dimensiones del contexto",
                       "Cada hallazgo indica la página del documento y si su cita se encontró en el texto (verificación automática).")
    for clave, nombre, que in DIMENSIONES:
        d = (f.get("dimensiones") or {}).get(clave, {})
        if pdf.get_y() > pdf.h - 45:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*TINTA)
        pdf.cell(pdf.get_string_width(_t(nombre)) + 2, 5.5, _t(nombre))
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*TENUE)
        pdf.cell(0, 5.5, _t(f"· {que}"), new_x="LMARGIN", new_y="NEXT")
        pdf.parrafo(d.get("resumen") or "Sin información en el documento.", tam=8.6)
        hallazgos = d.get("hallazgos") or []
        if hallazgos:
            filas = []
            for h in hallazgos:
                pagina = f"p. {h.get('pagina')}" if h.get("pagina") else "s/p"
                ev = f"{etiqueta} · {pagina}" + (f"\n{h.get('seccion')}" if h.get("seccion") else "")
                filas.append([_b(h.get("dato")), _md(f"\u201c{h.get('cita', '')}\u201d"), _md(ev),
                              _b("Sí") if h.get("verificada") else _md("No encontrada")])
            pdf.tabla(["Hallazgo", "Cita del documento", "Evidencia", "Verificada"], filas, [42, 92, 30, 16], tam=7)
        if d.get("faltante"):
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*TENUE)
            pdf.multi_cell(0, 4, _t(f"Falta: {d.get('faltante')}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.titulo_seccion("Información faltante")
    pdf.vinetas(f.get("informacion_faltante") or ["Nada relevante."])
    pdf.titulo_seccion("Contradicciones o ambigüedades")
    pdf.vinetas(f.get("ambiguedades") or ["No se detectaron."])

    perfil = f.get("perfil_riesgo") or {}
    pdf.titulo_seccion("Perfil de riesgo",
                       f"Sector: {perfil.get('sector', '—')} · Tamaño: {TAMANO.get(perfil.get('tamano'), '—')} · Alcance: IG1")
    amenazas = perfil.get("amenazas") or []
    if amenazas:
        pdf.tabla(["Amenaza prioritaria", "Impacto", "Por qué en este negocio", "Controles CIS"],
                  [[_b(a.get("amenaza")), _md(IMPACTO.get(a.get("impacto"), a.get("impacto") or "")),
                    _md(a.get("por_que_en_este_negocio")), _md(", ".join(a.get("controles", [])))] for a in amenazas],
                  [46, 16, 90, 28], tam=7.4)
    if perfil.get("prioridad_controles"):
        pdf.parrafo(f"Orden de prioridad de los controles para este negocio: {', '.join(perfil['prioridad_controles'])}.", tam=8)

    if p.ajustes:
        pdf.titulo_seccion("Ajustes registrados por el equipo (Etapa 2.5)")
        pdf.tabla(["Fecha", "Ajuste a la interpretación del agente"],
                  [[_md(a.get("fecha")), _md(a.get("texto"))] for a in p.ajustes], [30, 150], tam=7.6)
    return bytes(pdf.output())
