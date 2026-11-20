"""Reporte ejecutivo en PDF (Fase 6): la vista ejecutiva en 2-3 páginas A4, para un director.

- Mismo contenido y vocabulario que ``ejecutiva.py`` («medida», «confianza del diagnóstico», «Sin evidencia»), sin
  ids de CIS, páginas ni jerga. Lo técnico va en el reporte técnico (``reporte_pdf.reporte_pdf``).
- Gráficas vectoriales (fpdf2): nunca se pixelan al ampliar o imprimir.
- Legibles en escala de grises: los estados son la paleta de la app (azul, ámbar, bermellón y dos grises) con
  luminancias escalonadas (grises 82 / 184 / 116 / 152 / 212) y «Sin evidencia» además va rayado. El estado siempre
  lleva su palabra o su número al lado; nunca depende solo del color.
- Las proyecciones se rotulan «estimación». Las evaluaciones anteriores a la vista ejecutiva muestran los valores
  calculados o un aviso en lugar de la sección.
"""

from fpdf import FPDF

from .controls import catalogo
from .ejecutiva import AVISO_ANTERIOR, ESFUERZO, ESTADO_EJECUTIVO, HORIZONTE, LINEA_FINAL, _oracion, _severidad
from .panel import _primera_oracion, nombre_corto
from .reporte_pdf import FONDO, LINEA, TENUE, TINTA, _inicio, _Reporte, _t
from .state import ESTADOS, Proyecto, horizonte_de, indicadores, nivel_riesgo, proyeccion, severidad_de

# Tokens de estado de la app (modo Día) convertidos de OKLCH a sRGB.
ESTADO_RGB = {"implementado": (26, 97, 155), "parcial": (235, 179, 75), "no_implementado": (206, 86, 31),
              "no_verificado": (148, 153, 158), "no_aplicable": (214, 212, 208)}
BLANCO = (255, 255, 255)
SOBRE = {"implementado": BLANCO, "no_implementado": BLANCO}  # texto sobre el segmento; el resto, tinta
COLOR_SEV = {"alta": "no_implementado", "media": "parcial", "baja": "implementado"}
COLOR_NIVEL = {"Alto": "no_implementado", "Medio": "parcial", "Bajo": "implementado"}
# Tinte de cada zona del mapa: intensidades distintas para que también se separen en gris (192 / 234 / 217).
ZONA = {"alta": 0.45, "media": 0.30, "baja": 0.22}
ACENTO_EJ = (50, 98, 116)


def _mezcla(rgb: tuple, k: float) -> tuple:
    return tuple(round(c * k + 255 * (1 - k)) for c in rgb)


def _pct(v: float | None) -> str:
    return "No determinable" if v is None else f"{v:.0f}%"


def _delta(antes, ahora, unidad: str = " pts") -> str:
    if antes is None or ahora is None:
        return ""
    d = ahora - antes
    if abs(d) < 0.05:
        return "Sin cambio desde la evaluación inicial"
    return f"{'+' if d > 0 else '-'}{abs(d):.0f}{unidad} desde la evaluación inicial"


class _Ejecutivo(_Reporte):
    # ------------------------------------------------------------ primitivas
    def espacio(self, mm: float):
        """Salto de página si no caben ``mm`` milímetros (para no partir una gráfica)."""
        if self.get_y() + mm > self.h - self.b_margin:
            self.add_page()

    def alto(self, ancho: float, texto: str, tam: float, interlinea: float, estilo: str = "") -> float:
        self.set_font("Helvetica", estilo, tam)
        return self.multi_cell(ancho, interlinea, _t(texto), dry_run=True, output="HEIGHT")

    def texto(self, x: float, y: float, ancho: float, texto: str, tam: float, interlinea: float, estilo: str = "",
              color: tuple = TINTA, alinear: str = "L") -> float:
        """Escribe un bloque en (x, y) y devuelve la y final."""
        self.set_xy(x, y)
        self.set_font("Helvetica", estilo, tam)
        self.set_text_color(*color)
        self.multi_cell(ancho, interlinea, _t(texto), align=alinear, new_x="LEFT", new_y="NEXT")
        return self.get_y()

    def punto(self, x: float, y: float, estado: str, d: float = 2.4):
        self.set_fill_color(*ESTADO_RGB[estado])
        self.ellipse(x, y, d, d, style="F")
        if estado == "no_verificado":
            self.set_draw_color(*BLANCO)
            self.set_line_width(0.25)
            self.line(x + 0.3, y + d - 0.3, x + d - 0.3, y + 0.3)

    def rayado(self, x: float, y: float, w: float, h: float, paso: float = 1.3):
        """Líneas blancas a 45° dentro del rectángulo (marca «Sin evidencia» también en gris)."""
        self.set_draw_color(*BLANCO)
        self.set_line_width(0.28)
        t = -h
        while t < w:
            lo, hi = max(0.0, -t), min(h, w - t)
            if lo < hi:
                self.line(x + t + lo, y + h - lo, x + t + hi, y + h - hi)
            t += paso

    def segmento(self, x: float, y: float, w: float, h: float, estado: str, valor: int | None = None):
        self.set_fill_color(*ESTADO_RGB[estado])
        self.rect(x, y, w, h, style="F")
        if estado == "no_verificado":
            self.rayado(x, y, w, h)
        if valor is not None and w >= 3.6:
            self.set_font("Helvetica", "B", 6.8)
            self.set_text_color(*SOBRE.get(estado, TINTA))
            if estado == "no_verificado":  # sobre el rayado, la cifra va en una pastilla
                ancho = self.get_string_width(str(valor)) + 1.6
                self.set_fill_color(*ESTADO_RGB[estado])
                self.rect(x + (w - ancho) / 2, y + h / 2 - 1.5, ancho, 3, style="F")
                self.set_text_color(*BLANCO)
            self.set_xy(x, y)
            self.cell(w, h, str(valor), align="C")

    def leyenda(self, x: float, y: float, conteos: dict | None = None):
        for e in ESTADOS:
            self.segmento(x, y + 0.4, 3.2, 2.6, e)
            etiqueta = ESTADO_EJECUTIVO[e] + (f" {conteos[e]}" if conteos is not None else "")
            self.set_xy(x + 4.2, y)
            self.set_font("Helvetica", "", 7.6)
            self.set_text_color(*TINTA)
            self.cell(0, 3.4, _t(etiqueta))
            x += 4.2 + self.get_string_width(_t(etiqueta)) + 6
        self.set_y(y + 5)

    def aviso(self, texto: str):
        y = self.get_y()
        alto = self.alto(self.ancho - 8, texto, 8.2, 4.1, "I") + 4
        self.set_fill_color(*FONDO)
        self.rect(self.l_margin, y, self.ancho, alto, style="F")
        self.texto(self.l_margin + 4, y + 2, self.ancho - 8, texto, 8.2, 4.1, "I", TENUE)
        self.set_y(y + alto + 2)


# ---------------------------------------------------------------------------------------- secciones
def _veredicto(pdf: _Ejecutivo, res: dict, riesgos: list[dict]):
    nivel, calculado = nivel_riesgo(res, riesgos)
    frase = res.get("veredicto") or res.get("titular") or _primera_oracion(res.get("postura_inicial"))
    nota = ("Nivel calculado con la severidad de los cinco riesgos (evaluación anterior a la vista ejecutiva)."
            if calculado and nivel else "")
    x, y, izq = pdf.l_margin, pdf.get_y() + 4, 44
    ancho_frase = pdf.ancho - izq - 10
    alto = max(20, pdf.alto(ancho_frase, frase, 11.5, 5.6, "B") + (pdf.alto(ancho_frase, nota, 7.4, 3.6) if nota else 0) + 9)
    pdf.set_fill_color(*_mezcla(ESTADO_RGB[COLOR_NIVEL.get(nivel, "no_verificado")], 0.14))
    pdf.rect(x, y, pdf.ancho, alto, style="F")
    pdf.texto(x + 5, y + 5, izq - 6, "Nivel de riesgo", 7.8, 4, color=TENUE)
    pdf.punto(x + 5, y + 11.2, COLOR_NIVEL.get(nivel, "no_verificado"), 3.2)
    pdf.texto(x + 10, y + 10, izq - 10, nivel or "Sin determinar", 14, 5.6, "B")
    fin = pdf.texto(x + izq, y + 4.5, ancho_frase, frase, 11.5, 5.6, "B")
    if nota:
        pdf.texto(x + izq, fin + 1, ancho_frase, nota, 7.4, 3.6, "I", TENUE)
    pdf.set_y(y + alto + 4)


def _indicadores(pdf: _Ejecutivo, ind: dict, riesgos: list[dict], previo: dict | None, riesgos_previos):
    impl, conf = ind["implementacion"], ind["cobertura"]
    altos = sum(1 for r in riesgos if _severidad(r) == "alta")
    total = len(riesgos) or 5
    gap = 4
    w = (pdf.ancho - 2 * gap) / 3
    y = pdf.get_y()
    p = previo or {}
    tarjetas = [
        ("Madurez en ciberseguridad", _pct(impl),
         "Qué tanto de lo básico ya está en marcha, entre las medidas que se pudieron comprobar.",
         _delta(p.get("implementacion"), impl) if previo else ""),
        ("Confianza del diagnóstico", _pct(conf),
         f"De las medidas que aplican, qué parte se pudo comprobar con documentos. {ind['no_verificado']} siguen sin evidencia.",
         _delta(p.get("cobertura"), conf) if previo else ""),
        ("Riesgos altos", f"{altos} de {total}", "Riesgos con probabilidad e impacto altos para el negocio.",
         _delta(sum(1 for r in riesgos_previos if _severidad(r) == "alta"), altos, "")
         if riesgos_previos is not None else ""),
    ]
    alto = max(21.5 + pdf.alto(w - 8, nota, 7.2, 3.5) + (pdf.alto(w - 8, delta, 7.2, 3.5, "B") + 0.6 if delta else 0) + 3.5
               for _, _, nota, delta in tarjetas)
    for k, (nombre, cifra, nota, delta) in enumerate(tarjetas):
        x = pdf.l_margin + k * (w + gap)
        pdf.set_draw_color(*LINEA)
        pdf.set_line_width(0.25)
        pdf.rect(x, y, w, alto, style="D")
        pdf.texto(x + 4, y + 3.5, w - 8, nombre, 8, 4, "B", TENUE)
        pdf.texto(x + 4, y + 8.5, w - 8, cifra, 20, 9, "B")
        if k == 0 and impl is not None:  # barra de madurez
            pdf.set_fill_color(*_mezcla(ESTADO_RGB["implementado"], 0.18))
            pdf.rect(x + 4, y + 18.5, w - 8, 1.8, style="F")
            pdf.set_fill_color(*ESTADO_RGB["implementado"])
            pdf.rect(x + 4, y + 18.5, (w - 8) * impl / 100, 1.8, style="F")
        if k == 2:  # un punto por riesgo; relleno = alto
            for n in range(total):
                cx = x + 4 + n * 4.2
                if n < altos:
                    pdf.punto(cx, y + 18, "no_implementado", 2.6)
                else:
                    pdf.set_draw_color(*TENUE)
                    pdf.set_line_width(0.25)
                    pdf.ellipse(cx, y + 18, 2.6, 2.6, style="D")
        fin = pdf.texto(x + 4, y + 21.5, w - 8, nota, 7.2, 3.5, color=TENUE)
        if delta:
            pdf.texto(x + 4, fin + 0.6, w - 8, delta, 7.2, 3.5, "B")
    pdf.set_y(y + alto + 2)


def _en_juego(pdf: _Ejecutivo, res: dict):
    impactos = res.get("impactos_negocio") or []
    pdf.titulo_seccion("Qué está en juego", "Lo que la situación actual significa para el negocio.")
    if not impactos:
        pdf.aviso(AVISO_ANTERIOR.format(que="los impactos de negocio"))
        return
    gap, n = 4, len(impactos)
    w = (pdf.ancho - gap * (n - 1)) / n
    alto = max(pdf.alto(w - 8, x.get("titulo"), 9.2, 4.4, "B") + pdf.alto(w - 8, x.get("linea"), 8.2, 4) for x in impactos) + 9
    pdf.espacio(alto + 2)
    y = pdf.get_y()
    for k, x in enumerate(impactos):
        xx = pdf.l_margin + k * (w + gap)
        pdf.set_fill_color(*FONDO)
        pdf.rect(xx, y, w, alto, style="F")
        fin = pdf.texto(xx + 4, y + 3.5, w - 8, x.get("titulo"), 9.2, 4.4, "B")
        pdf.texto(xx + 4, fin + 1, w - 8, x.get("linea"), 8.2, 4, color=(60, 66, 74))
    pdf.set_y(y + alto + 2)


def _controles(pdf: _Ejecutivo, matriz: dict):
    filas = []
    for c in catalogo().controles:
        ids = [x.id for x in c.ig1 if x.id in matriz]
        if ids:
            filas.append((c, indicadores({i: matriz[i] for i in ids})))
    filas.sort(key=lambda f: (f[1]["implementacion"] is None, f[1]["implementacion"] or 0, -f[1]["no_implementado"]))
    alto_fila = 4.9
    pdf.espacio(28 + alto_fila * len(filas))
    pdf.titulo_seccion("Estado por control",
                       "Cómo están las medidas de cada control, del más débil al más sólido. El número dentro de cada "
                       "tramo es la cantidad de medidas; el porcentaje es la madurez del control.")
    pdf.leyenda(pdf.l_margin, pdf.get_y(), indicadores(matriz))
    pdf.ln(1)
    nombre_w, valor_w = 62, 22
    barra_w = pdf.ancho - nombre_w - valor_w - 4
    for c, ind in filas:
        pdf.espacio(alto_fila + 1)  # nunca partir una barra entre dos páginas
        y = pdf.get_y()
        pdf.set_xy(pdf.l_margin, y)
        pdf.set_font("Helvetica", "", 8.2)
        pdf.set_text_color(*TINTA)
        nombre = _t(c.nombre)
        pdf.cell(pdf.get_string_width(nombre) + 1.5, alto_fila - 1, nombre)
        pdf.set_font("Helvetica", "", 6.8)
        pdf.set_text_color(*TENUE)
        pdf.cell(nombre_w - pdf.get_string_width(nombre) - 1.5, alto_fila - 1,
                 _t(f"{ind['total']} medida{'s' if ind['total'] != 1 else ''}"))
        x = pdf.l_margin + nombre_w
        for e in ESTADOS:
            if ind[e]:
                w = barra_w * ind[e] / ind["total"]
                pdf.segmento(x, y + 0.4, w, alto_fila - 1.8, e, ind[e])
                x += w
        pdf.set_xy(pdf.l_margin + nombre_w + barra_w + 4, y)
        valor = "Sin evidencia" if ind["implementacion"] is None else f"{ind['implementacion']:.0f}%"
        pdf.set_font("Helvetica", "B" if ind["implementacion"] is not None else "I", 8.2)
        pdf.set_text_color(*(TINTA if ind["implementacion"] is not None else TENUE))
        pdf.cell(valor_w, alto_fila - 1, _t(valor), align="R")
        pdf.set_y(y + alto_fila)
    pdf.ln(1)


def _bola(pdf: _Ejecutivo, bx: float, by: float, d: float, n: int):
    """Número del riesgo dentro de un círculo de tinta."""
    pdf.set_fill_color(*TINTA)
    pdf.ellipse(bx, by, d, d, style="F")
    pdf.set_xy(bx, by)
    pdf.set_font("Helvetica", "B", 6.8 if d > 4 else 5.6)
    pdf.set_text_color(*BLANCO)
    pdf.cell(d, d, str(n), align="C")


def _mapa(pdf: _Ejecutivo, riesgos: list[dict]):
    completos = riesgos and all(severidad_de(r.get("probabilidad"), r.get("impacto")) for r in riesgos)
    pdf.espacio(82 if completos else 30)
    pdf.titulo_seccion("Mapa de riesgos", "Los cinco riesgos según su probabilidad y su impacto en el negocio (1 a 5).")
    if not completos:
        pdf.aviso(AVISO_ANTERIOR.format(que="la probabilidad y el impacto de cada riesgo"))
        _lista_riesgos(pdf, riesgos, pdf.l_margin, pdf.get_y(), pdf.ancho)
        return
    celda, x0, y0 = 11.5, pdf.l_margin + 9, pdf.get_y() + 5
    pdf.texto(pdf.l_margin, y0 - 5, 30, "Impacto", 7, 3.5, "B", TENUE)
    en = {}
    for n, r in enumerate(riesgos, 1):
        en.setdefault((r["probabilidad"], r["impacto"]), []).append(n)
    for fila, impacto in enumerate(range(5, 0, -1)):
        y = y0 + fila * celda
        pdf.texto(pdf.l_margin + 3, y + celda / 2 - 1.7, 5, str(impacto), 7, 3.5, color=TENUE)
        for col, prob in enumerate(range(1, 6)):
            x = x0 + col * celda
            sev = severidad_de(prob, impacto)
            pdf.set_fill_color(*_mezcla(ESTADO_RGB[COLOR_SEV[sev]], ZONA[sev]))
            pdf.set_draw_color(*BLANCO)
            pdf.set_line_width(0.6)
            pdf.rect(x, y, celda, celda, style="DF")
            bolas = en.get((prob, impacto), [])
            d = 4.6 if len(bolas) <= 2 else 3.3
            filas = [bolas[i:i + 3] for i in range(0, len(bolas), 3)]
            for fi, grupo in enumerate(filas):
                inicio = x + (celda - len(grupo) * (d + 0.4) + 0.4) / 2
                by = y + (celda - len(filas) * (d + 0.4) + 0.4) / 2 + fi * (d + 0.4)
                for k, n in enumerate(grupo):
                    bx = inicio + k * (d + 0.4)
                    _bola(pdf, bx, by, d, n)

    for col in range(5):
        pdf.texto(x0 + col * celda, y0 + 5 * celda + 0.8, celda, str(col + 1), 7, 3.5, color=TENUE, alinear="C")
    pdf.texto(x0, y0 + 5 * celda + 4.6, 5 * celda, "Probabilidad", 7, 3.5, "B", TENUE, "R")
    # Zonas: palabra + tinte (no solo color)
    ly = y0 + 5 * celda + 10
    pdf.texto(pdf.l_margin, ly, 16, "Severidad", 6.8, 3.8, "B", TENUE)
    lx = pdf.l_margin + 14
    for sev in ("alta", "media", "baja"):
        pdf.set_fill_color(*_mezcla(ESTADO_RGB[COLOR_SEV[sev]], ZONA[sev]))
        pdf.rect(lx, ly + 0.3, 3.2, 3.2, style="F")
        pdf.texto(lx + 4.2, ly, 12, sev.capitalize(), 6.8, 3.8, color=TENUE)
        lx += 16
    fin_mapa = ly + 6
    fin_lista = _lista_riesgos(pdf, riesgos, x0 + 5 * celda + 9, y0 - 5, pdf.ancho - (x0 - pdf.l_margin) - 5 * celda - 9)
    pdf.set_y(max(fin_mapa, fin_lista) + 2)


def _lista_riesgos(pdf: _Ejecutivo, riesgos: list[dict], x: float, y: float, ancho: float) -> float:
    for n, r in enumerate(riesgos, 1):
        texto = r.get("consecuencia_negocio") or _oracion(r.get("consecuencia"))
        if x == pdf.l_margin:  # lista a todo el ancho (sin mapa): no separar un riesgo de su texto
            pdf.set_y(y)
            pdf.espacio(pdf.alto(ancho - 7, texto, 8, 3.9) + 8)
            y = pdf.get_y()
        _bola(pdf, x, y + 0.4, 4.4, n)
        tx = x + 7
        pdf.set_xy(tx, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*TINTA)
        nombre = _t(nombre_corto(r))
        pdf.cell(pdf.get_string_width(nombre) + 3, 5, nombre)
        sev = _severidad(r)
        if sev in COLOR_SEV:
            sx = pdf.get_x()
            pdf.punto(sx, y + 1.3, COLOR_SEV[sev], 2.4)
            pdf.set_xy(sx + 3.4, y)
            pdf.set_font("Helvetica", "", 7.6)
            pdf.set_text_color(*TENUE)
            pdf.cell(0, 5, _t(f"Severidad {sev}"))
        y = pdf.texto(tx, y + 5, ancho - 7, texto, 8, 3.9, color=(60, 66, 74)) + 2.6
    return y


def _plan(pdf: _Ejecutivo, inis: list[dict], riesgos: list[dict], matriz: dict):
    columnas = {h: [] for h in HORIZONTE}
    for ini in inis:
        h, estimado = horizonte_de(ini)
        reduce = ", ".join(nombre_corto(riesgos[n - 1]) for n in ini.get("riesgos", []) if 1 <= n <= len(riesgos))
        meta = ESFUERZO.get(ini.get("esfuerzo"), "") + (" · plazo estimado" if estimado else "")
        columnas[h].append((ini.get("titulo") or "", meta, f"Reduce: {reduce}" if reduce else ""))
    gap = 4
    w = (pdf.ancho - 2 * gap) / 3
    altos = {h: sum(pdf.alto(w - 6, t, 8.6, 4.1, "B") + pdf.alto(w - 6, m, 7.2, 3.5) + (pdf.alto(w - 6, r, 7.2, 3.5) if r else 0) + 8
                    for t, m, r in c) for h, c in columnas.items()}
    pdf.espacio(30 + max(max(altos.values(), default=0), 12))
    pdf.titulo_seccion("Plan", "Las cinco iniciativas por plazo y cuánto subiría la madurez al completarlas.")
    y0 = pdf.get_y()
    fin = y0
    for k, (h, tarjetas) in enumerate(columnas.items()):
        x = pdf.l_margin + k * (w + gap)
        pdf.set_xy(x, y0)
        pdf.set_font("Helvetica", "B", 8.4)
        pdf.set_text_color(*TINTA)
        pdf.cell(w - 8, 5, _t(HORIZONTE[h]))
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*TENUE)
        pdf.cell(8, 5, str(len(tarjetas)), align="R")
        pdf.set_draw_color(*TINTA)
        pdf.set_line_width(0.4)
        pdf.line(x, y0 + 5.6, x + w, y0 + 5.6)
        y = y0 + 7.5
        if not tarjetas:
            y = pdf.texto(x, y, w, "Sin iniciativas en este plazo.", 7.6, 3.8, "I", TENUE) + 2
        for titulo, meta, reduce in tarjetas:
            alto = pdf.alto(w - 6, titulo, 8.6, 4.1, "B") + pdf.alto(w - 6, meta, 7.2, 3.5) + (pdf.alto(w - 6, reduce, 7.2, 3.5) if reduce else 0) + 5
            pdf.set_fill_color(*FONDO)
            pdf.rect(x, y, w, alto, style="F")
            yy = pdf.texto(x + 3, y + 2, w - 6, titulo, 8.6, 4.1, "B")
            yy = pdf.texto(x + 3, yy + 0.4, w - 6, meta, 7.2, 3.5, color=TENUE)
            if reduce:
                pdf.texto(x + 3, yy, w - 6, reduce, 7.2, 3.5, color=(60, 66, 74))
            y += alto + 2.5
        fin = max(fin, y)
    pdf.set_y(fin + 1)
    pr = proyeccion(matriz, inis)
    if pr["hoy"] is None or pr["estimado"] is None:
        return
    pdf.espacio(31)
    y = pdf.get_y()
    pdf.set_draw_color(*LINEA)
    pdf.set_line_width(0.25)
    pdf.rect(pdf.l_margin, y, pdf.ancho, 27, style="D")
    pdf.texto(pdf.l_margin + 4, y + 3, pdf.ancho - 8, "Madurez antes y después del plan (estimación)", 8.6, 4.2, "B")
    etiqueta_w, valor_w = 26, 14
    barra_w = pdf.ancho - 8 - etiqueta_w - valor_w - 4
    for k, (nombre, valor, estimado) in enumerate([("Hoy", pr["hoy"], False), ("Al terminar", pr["estimado"], True)]):
        fy = y + 9 + k * 5.6
        pdf.texto(pdf.l_margin + 4, fy, etiqueta_w, nombre, 8, 4, color=TENUE)
        bx = pdf.l_margin + 4 + etiqueta_w
        pdf.set_fill_color(*_mezcla(ESTADO_RGB["implementado"], 0.14))
        pdf.rect(bx, fy + 0.8, barra_w, 2.6, style="F")
        pdf.set_fill_color(*ESTADO_RGB["implementado"])
        pdf.rect(bx, fy + 0.8, barra_w * valor / 100, 2.6, style="F")
        if estimado:  # la estimación va rayada: también se distingue impresa en gris
            pdf.rayado(bx, fy + 0.8, barra_w * valor / 100, 2.6, 1.1)
        pdf.set_xy(bx + barra_w + 2, fy)
        pdf.set_font("Helvetica", "B", 8.4)
        pdf.set_text_color(*TINTA)
        pdf.cell(valor_w, 4, f"{valor:.0f}%", align="R")
    pdf.texto(pdf.l_margin + 4, y + 21, pdf.ancho - 8,
              "Estimación: supone que todas las medidas de las cinco iniciativas quedan implementadas y que el resto sigue igual.",
              7.2, 3.5, "I", TENUE)
    pdf.set_y(y + 29)


def _peticiones(pdf: _Ejecutivo, res: dict):
    lista = res.get("peticiones") or []
    alto = sum(pdf.alto(pdf.ancho - 10, t, 9, 4.5) + 2 for t in lista) + 26
    pdf.espacio(alto)
    pdf.titulo_seccion("Lo que necesitamos de ustedes", "La información que más mejoraría la confianza del diagnóstico.")
    if not lista:
        pdf.aviso(AVISO_ANTERIOR.format(que="las peticiones de información al cliente"))
    for n, t in enumerate(lista, 1):
        y = pdf.get_y()
        pdf.texto(pdf.l_margin, y, 8, f"{n}.", 9, 4.5, "B")
        pdf.set_y(pdf.texto(pdf.l_margin + 8, y, pdf.ancho - 10, t, 9, 4.5) + 2)
    pdf.ln(2)
    pdf.set_draw_color(*LINEA)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.ancho, pdf.get_y())
    pdf.ln(2)
    pdf.texto(pdf.l_margin, pdf.get_y(), pdf.ancho, LINEA_FINAL, 8, 4, "I", TENUE)


# --------------------------------------------------------------------------------------------- API
def reporte_ejecutivo_pdf(p: Proyecto, cual: str) -> bytes:
    """Reporte ejecutivo de UNA versión en 2-3 páginas. "v2" usa los riesgos vigentes y el roadmap actualizado, y
    muestra el cambio de los indicadores desde la evaluación inicial."""
    v = p.v1 if cual == "v1" else p.v2 if cual == "v2" else None
    if v is None or not v.reporte:
        raise ValueError(f"La versión {cual} aún no tiene reporte.")
    rep = v.reporte
    res = rep.get("resumen_ejecutivo") or {}
    if cual == "v1":
        riesgos, inis, previo, riesgos_previos = rep.get("riesgos") or [], rep.get("iniciativas") or [], None, None
    else:
        riesgos_v1 = p.v1.reporte.get("riesgos", [])
        riesgos = rep.get("riesgos_v2") or riesgos_v1
        inis, previo, riesgos_previos = rep.get("roadmap") or [], p.v1.indicadores(), riesgos_v1
    nombre = "Reporte ejecutivo inicial" if cual == "v1" else "Reporte ejecutivo final"
    pdf = _inicio(p, nombre, f"{v.nombre} del {v.fecha}. Diagnóstico de ciberseguridad básica (CIS Controls v8.1, IG1) "
                             "a partir de los documentos entregados por la empresa.", _Ejecutivo)
    _veredicto(pdf, res, riesgos)
    _indicadores(pdf, v.indicadores(), riesgos, previo, riesgos_previos)
    _en_juego(pdf, res)
    _controles(pdf, v.matriz)
    _mapa(pdf, riesgos)
    _plan(pdf, inis, riesgos, v.matriz)
    _peticiones(pdf, res)
    return bytes(pdf.output())
