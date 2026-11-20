"""Vista ejecutiva de los reportes (v1 y v2): para un director, no para un técnico (2026-11-19).

Sin ids de CIS, números de salvaguarda, páginas ni jerga. Vocabulario: «medida» en lugar de salvaguarda,
«confianza del diagnóstico» en lugar de cobertura y «Sin evidencia» en lugar de No verificado. Todo lo que se
quita de aquí sigue en la vista técnica y en el reporte técnico.

Los números salen del código (``state``): madurez, confianza, madurez por área, severidad y proyección. Del
modelo solo vienen los textos ejecutivos (veredicto, impactos, peticiones, consecuencia de negocio), ya validados
por ``state.validar_ejecutivo``. Las evaluaciones anteriores a estos campos se ven con valores calculados o con la
sección oculta y un aviso.

Clases con prefijo ``e-``; las animaciones de entrada reutilizan las de ``panel`` (``data-cuenta`` y ``d-crece``).
Sin el carácter de menor que en el CSS (st.html descarta el <style> completo).
"""

from .controls import catalogo
from .panel import _primera_oracion, conteos, fichas, nombre_corto, seccion
from .state import ESTADOS, Resultado, horizonte_de, indicadores, nivel_riesgo, proyeccion, severidad_de
from .ui import esc

LINEA_FINAL = "Diagnóstico preliminar basado en documentos; sujeto a validación del auditor."
AYUDA_CONFIANZA = ("De las medidas que aplican a la empresa, qué parte se pudo comprobar con los documentos. "
                   "Si es baja, la madurez se calculó con pocas medidas y puede cambiar al recibir más información.")
# Vocabulario ejecutivo de los estados (la vista técnica conserva el original).
ESTADO_EJECUTIVO = {"implementado": "Implementado", "parcial": "Parcial", "no_implementado": "No implementado",
                    "no_verificado": "Sin evidencia", "no_aplicable": "No aplica"}
HORIZONTE = {"0-30": "Primeros 30 días", "30-90": "De 30 a 90 días", "90-180": "De 90 a 180 días"}
ESFUERZO = {"bajo": "Esfuerzo bajo", "medio": "Esfuerzo medio", "alto": "Esfuerzo alto"}
# Nivel de riesgo y severidad: el color de la marca (nunca el del texto) sale de la paleta de estados.
COLOR_NIVEL = {"Alto": "no_implementado", "Medio": "parcial", "Bajo": "implementado"}
COLOR_SEV = {"alta": "no_implementado", "media": "parcial", "baja": "implementado"}

CSS = """
<style>
.e-aviso { font-size: 13px; color: var(--ink-3); padding: 12px 16px; border: 1px dashed var(--rule-2); border-radius: 8px; margin: 0; }
.e-punto { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex: none; background: var(--c); }

/* 1. Veredicto */
.e-veredicto { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 28px; align-items: center; padding: 26px 28px;
  border-radius: 12px; background: color-mix(in srgb, var(--c) var(--e-tinte, 13%), var(--surface)); box-shadow: inset 4px 0 0 var(--c), var(--shadow-1); }
.e-nivel { display: grid; gap: 4px; }
.e-nivel span { font-size: 12px; font-weight: 500; color: var(--ink-3); }
.e-nivel b { display: flex; align-items: center; gap: 12px; font-size: 38px; line-height: 42px; font-weight: 600; letter-spacing: -0.03em; color: var(--ink); white-space: nowrap; }
.e-nivel b .e-punto { width: 16px; height: 16px; }
.e-frase { font-size: 20px; line-height: 29px; font-weight: 500; letter-spacing: -0.012em; color: var(--ink); margin: 0; text-wrap: pretty; }
.e-calc { display: block; font-size: 12px; line-height: 18px; font-weight: 400; color: var(--ink-3); margin-top: 8px; letter-spacing: 0; }

/* 2. Indicadores */
.e-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.e-kpi { padding: 20px 22px; display: grid; gap: 8px; align-content: start; position: relative; }
.e-kpi + .e-kpi { border-left: 1px solid var(--rule); }
.e-kpi-nombre { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: var(--ink-2); }
.e-kpi-cuerpo { display: flex; align-items: center; gap: 16px; }
.e-cifra { font-size: 34px; line-height: 40px; font-weight: 600; letter-spacing: -0.03em; color: var(--ink); font-variant-numeric: tabular-nums; }
.e-cifra small { font-size: .5em; font-weight: 500; color: var(--ink-3); letter-spacing: 0; margin-left: 2px; }
.e-cifra .e-nd { font-size: 16px; font-weight: 500; letter-spacing: -0.01em; }
.e-nota { font-size: 12px; line-height: 18px; color: var(--ink-3); }
.e-dona { width: 64px; height: 64px; border-radius: 50%; flex: none;
  background: conic-gradient(var(--accent) calc(var(--v) * 1%), var(--sunken) 0);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 9px), #000 calc(100% - 8px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 9px), #000 calc(100% - 8px)); }
.e-ayuda { position: relative; width: 18px; height: 18px; border-radius: 50%; display: inline-grid; place-items: center; cursor: help;
  font: 600 11px/1 var(--font); color: var(--ink-3); box-shadow: inset 0 0 0 1.3px var(--rule-2); }
.e-ayuda:hover, .e-ayuda:focus-visible { color: var(--ink); box-shadow: inset 0 0 0 1.3px var(--ink-3); outline: none; }
.e-ayuda-texto { position: absolute; left: 50%; top: calc(100% + 8px); transform: translateX(-50%); width: 260px; z-index: 5;
  padding: 10px 12px; border-radius: 8px; background: var(--ink); color: var(--paper); font: 400 12px/18px var(--font);
  opacity: 0; visibility: hidden; transition: opacity 120ms ease-out; pointer-events: none; text-align: left; }
.e-ayuda:hover .e-ayuda-texto, .e-ayuda:focus-visible .e-ayuda-texto { opacity: 1; visibility: visible; }
.e-puntos { display: flex; gap: 5px; }
.e-puntos i { width: 12px; height: 12px; border-radius: 50%; background: var(--sunken); box-shadow: inset 0 0 0 1px var(--rule); }
.e-puntos i.e-on { background: var(--st-no_implementado); box-shadow: none; }
.e-delta { font: 500 11px/16px var(--mono); color: var(--ink-2); }

/* 3. Qué está en juego */
.e-impactos { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.e-impacto { padding: 18px 20px; display: grid; gap: 6px; align-content: start; }
.e-impacto h3 { font-size: 15px; line-height: 21px; font-weight: 600; color: var(--ink); margin: 0; padding: 0; letter-spacing: -0.01em; }
.e-impacto p { font-size: 13px; line-height: 20px; color: var(--ink-2); margin: 0; }

/* 4. Estado por control: barras 100 % apiladas, de peor a mejor */
.e-controles { padding: 10px 20px 16px; display: grid; }
.e-leyenda { display: flex; flex-wrap: wrap; gap: 6px 16px; padding: 6px 0 12px; border-bottom: 1px solid var(--rule); margin-bottom: 4px; }
.e-leyenda.d-leyenda { gap: 4px; }
.e-control { display: grid; grid-template-columns: minmax(170px, 250px) minmax(0, 1fr) 54px; gap: 16px; align-items: center; padding: 8px 0; }
.e-control-nombre { font-size: 13px; color: var(--ink); line-height: 18px; }
.e-control-nombre small { display: block; font-size: 11px; color: var(--ink-3); }
.e-pila { display: flex; gap: 2px; height: 14px; }
.e-pila .d-s { border-radius: 3px; min-width: 6px; }
.e-control-valor { text-align: right; font-size: 14px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; }
.e-control-valor.e-nd { font-size: 12px; font-weight: 400; color: var(--ink-3); }

/* 5. Mapa de riesgos */
.e-mapa { display: grid; grid-template-columns: minmax(0, 420px) minmax(0, 1fr); gap: 28px; padding: 20px; align-items: start; }
.e-rejilla { display: grid; grid-template-columns: 22px repeat(5, minmax(0, 1fr)); grid-template-rows: repeat(5, 54px) 22px; gap: 3px; }
.e-celda { border-radius: 4px; background: color-mix(in srgb, var(--c) var(--e-zona, 24%), var(--surface)); display: flex; flex-wrap: wrap;
  align-items: center; justify-content: center; gap: 4px; padding: 2px; }
.e-eje { display: grid; place-items: center; font: 500 11px/1 var(--mono); color: var(--ink-3); }
.e-eje-titulo { font-size: 11px; color: var(--ink-3); }
.e-bola { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font: 600 12px/1 var(--font);
  background: var(--ink); color: var(--paper); box-shadow: 0 0 0 2px var(--surface); }
.e-lista-riesgos { margin: 0; padding: 0; list-style: none; display: grid; gap: 14px; }
.e-lista-riesgos li { display: grid; grid-template-columns: 26px minmax(0, 1fr); gap: 12px; padding: 8px; margin: -8px; border-radius: 8px; }
.e-lista-riesgos li:hover { background: var(--sunken); }
button.e-bola { border: 0; padding: 0; cursor: pointer; }
button.e-bola:hover { transform: scale(1.12); }
.e-ini[data-abre]:hover { box-shadow: 0 0 0 1px var(--rule-2), var(--shadow-1); }
.e-lista-riesgos h3 { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 14px; line-height: 20px; font-weight: 600; color: var(--ink); margin: 0; padding: 0; }
.e-lista-riesgos p { font-size: 13px; line-height: 19px; color: var(--ink-2); margin: 2px 0 0; }
.e-sev { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 500; color: var(--ink-2); }
.e-sev .e-punto { width: 8px; height: 8px; }

/* 6. Plan */
.e-plan { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; position: relative; }
.e-fase { display: grid; gap: 10px; align-content: start; }
.e-fase-cab { display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 600; color: var(--ink); padding-bottom: 10px;
  border-bottom: 2px solid var(--rule-2); }
.e-fase-cab .d-mono { color: var(--ink-3); font-weight: 400; }
.e-ini { padding: 14px 16px; display: grid; gap: 8px; }
.e-ini h3 { font-size: 14px; line-height: 20px; font-weight: 600; color: var(--ink); margin: 0; padding: 0; }
.e-ini-meta { display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; color: var(--ink-3); }
.e-chip { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 4px; background: var(--sunken); color: var(--ink-2); font-size: 12px; }
.e-vacio { font-size: 12px; color: var(--ink-3); padding: 14px 0; }
.e-estim { font-size: 11px; color: var(--ink-3); font-style: italic; }
.e-antes { padding: 18px 20px; display: grid; gap: 12px; margin-top: 12px; }
.e-antes-fila { display: grid; grid-template-columns: 90px minmax(0, 1fr) 64px; gap: 14px; align-items: center; font-size: 13px; color: var(--ink-2); }
.e-antes-fila b { font-size: 15px; font-weight: 600; color: var(--ink); text-align: right; font-variant-numeric: tabular-nums; }
.e-antes .d-barra { height: 12px; border-radius: 6px; }
.e-antes .d-barra i { border-radius: 6px; }
.e-antes .d-barra i.e-estimada { background: repeating-linear-gradient(135deg, var(--accent) 0 6px, color-mix(in oklch, var(--accent) 70%, var(--surface)) 6px 10px); }
.e-antes-titulo { font-size: 14px; font-weight: 600; color: var(--ink); }

/* 7. Peticiones */
.e-peticiones { margin: 0; padding: 18px 20px; list-style: none; display: grid; gap: 12px; counter-reset: pet; }
.e-peticiones li { display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 12px; font-size: 14px; line-height: 21px; color: var(--ink); counter-increment: pet; }
.e-peticiones li::before { content: counter(pet); width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center;
  font: 600 12px/1 var(--font); background: var(--accent-tint); color: var(--ink); }
.e-final { font-size: 12px; color: var(--ink-3); margin: 12px 0 0; }

:root[data-theme="dark"] .e-vista { --e-tinte: 20%; --e-zona: 34%; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .e-vista { --e-tinte: 20%; --e-zona: 34%; } }
@media (max-width: 860px) {
  .e-veredicto { grid-template-columns: 1fr; gap: 14px; padding: 20px; }
  .e-nivel b { font-size: 30px; line-height: 34px; }
  .e-frase { font-size: 17px; line-height: 25px; }
  .e-kpis, .e-impactos, .e-plan { grid-template-columns: 1fr; }
  .e-kpi + .e-kpi { border-left: 0; border-top: 1px solid var(--rule); }
  .e-control { grid-template-columns: minmax(0, 1fr) auto; gap: 6px 12px; }
  .e-control .e-pila { grid-column: 1 / -1; grid-row: 2; }
  .e-mapa { grid-template-columns: 1fr; padding: 16px; }
  .e-rejilla { grid-template-rows: repeat(5, 46px) 22px; }
  .e-celda { gap: 2px; align-content: center; }
  .e-celda .e-bola { width: 20px; height: 20px; font-size: 11px; box-shadow: 0 0 0 1.5px var(--surface); }
  .e-antes-fila { grid-template-columns: 70px minmax(0, 1fr) 54px; }
}
</style>
"""


# ------------------------------------------------------------------------------------- utilidades
def _c(estado: str) -> str:
    return f"--c: var(--st-{estado})"


def _pct(valor: float | None) -> str:
    if valor is None:
        return '<span class="e-nd">No determinable</span>'
    return f'<span data-cuenta="{valor:.0f}" data-dec="0">{valor:.0f}</span><small>%</small>'


def _delta(antes, ahora, unidad: str = " pts") -> str:
    if antes is None or ahora is None or not isinstance(antes, (int, float)):
        return ""
    d = ahora - antes
    if abs(d) < 0.05:
        return '<span class="e-delta">Sin cambio desde la evaluación inicial</span>'
    return f'<span class="e-delta">{"+" if d > 0 else "−"}{abs(d):.0f}{unidad} desde la evaluación inicial</span>'


def _aviso(texto: str) -> str:
    return f'<p class="e-aviso">{esc(texto)}</p>'


AVISO_ANTERIOR = "Esta evaluación se generó antes de la vista ejecutiva y no trae {que}. Aparecerá al generar un reporte nuevo."


def _severidad(r: dict) -> str | None:
    return severidad_de(r.get("probabilidad"), r.get("impacto")) or r.get("severidad")


def _oracion(texto: str) -> str:
    texto = " ".join(str(texto or "").split())
    corte = texto.find(". ")
    return texto[:corte + 1] if corte > 0 else texto


# --------------------------------------------------------------------------------------- secciones
def veredicto(res: dict, riesgos: list[dict]) -> str:
    nivel, calculado = nivel_riesgo(res, riesgos)
    frase = res.get("veredicto") or res.get("titular") or _primera_oracion(res.get("postura_inicial"))
    nota = ('<span class="e-calc">Nivel calculado con la severidad de los cinco riesgos (evaluación anterior a la vista '
            'ejecutiva).</span>') if calculado and nivel else ""
    color = COLOR_NIVEL.get(nivel, "no_verificado")
    return (f'<section class="e-veredicto" id="d-veredicto" data-seccion="veredicto" style="{_c(color)};scroll-margin-top:80px">'
            f'<div class="e-nivel"><span>Nivel de riesgo</span><b><i class="e-punto" aria-hidden="true"></i>'
            f'{esc(nivel or "Sin determinar")}</b></div>'
            f'<p class="e-frase">{esc(frase)}{nota}</p></section>')


def indicadores_clave(ind: dict, riesgos: list[dict], previo: dict | None = None, riesgos_previos=None) -> str:
    impl, conf = ind["implementacion"], ind["cobertura"]
    altos = sum(1 for r in riesgos if _severidad(r) == "alta")
    total = len(riesgos) or 5
    p = previo or {}
    dona = f'<div class="e-dona" style="--v:{impl or 0:.1f}" aria-hidden="true"></div>' if impl is not None else ""
    puntos = "".join(f'<i class="{"e-on" if n < altos else ""}"></i>' for n in range(total))
    d_altos = ""
    if riesgos_previos is not None:
        antes = sum(1 for r in riesgos_previos if _severidad(r) == "alta")
        d_altos = _delta(antes, altos, "")
    return (
        '<section class="d-tarjeta e-kpis" aria-label="Indicadores clave">'
        f'<div class="e-kpi"><div class="e-kpi-nombre">Madurez en ciberseguridad</div>'
        f'<div class="e-kpi-cuerpo">{dona}<div class="e-cifra">{_pct(impl)}</div></div>'
        f'<div class="e-nota">Qué tanto de lo básico ya está en marcha, entre las medidas que se pudieron comprobar.</div>'
        f'{_delta(p.get("implementacion"), impl) if previo else ""}</div>'
        f'<div class="e-kpi"><div class="e-kpi-nombre">Confianza del diagnóstico'
        f'<span class="e-ayuda" tabindex="0" role="note" aria-label="{esc(AYUDA_CONFIANZA)}">?'
        f'<span class="e-ayuda-texto" aria-hidden="true">{esc(AYUDA_CONFIANZA)}</span></span></div>'
        f'<div class="e-cifra">{_pct(conf)}</div>'
        f'<div class="e-nota">{ind["no_verificado"]} medidas siguen sin evidencia en los documentos.</div>'
        f'{_delta(p.get("cobertura"), conf) if previo else ""}</div>'
        f'<div class="e-kpi"><div class="e-kpi-nombre">Riesgos altos</div>'
        f'<div class="e-cifra"><span data-cuenta="{altos}" data-dec="0">{altos}</span><small>&nbsp;de {total}</small></div>'
        f'<div class="e-puntos" aria-hidden="true">{puntos}</div>'
        f'<div class="e-nota">Riesgos con probabilidad e impacto altos para el negocio.</div>{d_altos}</div>'
        '</section>')


def en_juego(res: dict) -> str:
    impactos = res.get("impactos_negocio") or []
    if not impactos:
        return _aviso(AVISO_ANTERIOR.format(que="los impactos de negocio"))
    return '<div class="e-impactos">' + "".join(
        f'<article class="d-tarjeta e-impacto"><h3>{esc(x.get("titulo"))}</h3><p>{esc(x.get("linea"))}</p></article>'
        for x in impactos) + "</div>"


def controles(matriz: dict[str, Resultado]) -> str:
    """Una barra 100 % apilada por cada control con IG1 (nombre en español, sin id), de peor a mejor madurez; la
    madurez usa la fórmula global. Los segmentos llevan data-e para el filtro por estado."""
    filas = []
    for c in catalogo().controles:
        ids = [x.id for x in c.ig1 if x.id in matriz]
        if not ids:
            continue
        ind = indicadores({i: matriz[i] for i in ids})
        filas.append((c, ind))
    filas.sort(key=lambda f: (f[1]["implementacion"] is None, f[1]["implementacion"] or 0, -f[1]["no_implementado"]))
    cuerpo = ""
    for c, ind in filas:
        total = ind["total"]
        segs = "".join(f'<span class="d-s" data-e="{e}" style="flex:{ind[e]} 1 0;background:var(--st-{e})" '
                       f'title="{ESTADO_EJECUTIVO[e]}: {ind[e]}"></span>' for e in ESTADOS if ind[e])
        resumen = ", ".join(f"{ind[e]} {ESTADO_EJECUTIVO[e].lower()}" for e in ESTADOS if ind[e])
        valor = (f'<span class="e-control-valor e-nd">Sin evidencia</span>' if ind["implementacion"] is None
                 else f'<span class="e-control-valor">{ind["implementacion"]:.0f}%</span>')
        cuerpo += (f'<div class="e-control" data-estados="{" ".join(e for e in ESTADOS if ind[e])}">'
                   f'<span class="e-control-nombre">{esc(c.nombre)}'
                   f'<small>{total} medida{"s" if total != 1 else ""}</small></span>'
                   f'<div class="e-pila d-principal" role="img" aria-label="{esc(c.nombre)}: {resumen}">{segs}</div>{valor}</div>')
    total = indicadores(matriz)
    leyenda = "".join(f'<button type="button" data-foco="{e}" aria-pressed="false"{"" if total[e] else " disabled"}>'
                      f'<i class="d-m d-m-{e}" data-e="{e}" aria-hidden="true"></i>{ESTADO_EJECUTIVO[e]} <b>{total[e]}</b></button>'
                      for e in ESTADOS)
    return (f'<div class="d-tarjeta e-controles d-crece"><div class="e-leyenda d-leyenda" role="group" '
            f'aria-label="Filtrar por estado">{leyenda}</div>{cuerpo}</div>')


def mapa_riesgos(riesgos: list[dict]) -> str:
    if not riesgos or not all(severidad_de(r.get("probabilidad"), r.get("impacto")) for r in riesgos):
        return _aviso(AVISO_ANTERIOR.format(que="la probabilidad y el impacto de cada riesgo"))
    en = {}
    for n, r in enumerate(riesgos, 1):
        en.setdefault((r["probabilidad"], r["impacto"]), []).append(n)
    celdas = ""
    for impacto in range(5, 0, -1):
        celdas += f'<span class="e-eje">{impacto}</span>'
        for prob in range(1, 6):
            bolas = "".join(f'<button type="button" class="e-bola" data-abre="r-x{n}" aria-label="Riesgo {n}: '
                            f'{esc(nombre_corto(riesgos[n - 1]))}">{n}</button>' for n in en.get((prob, impacto), []))
            celdas += f'<div class="e-celda" style="{_c(COLOR_SEV[severidad_de(prob, impacto)])}">{bolas}</div>'
    celdas += '<span></span>' + "".join(f'<span class="e-eje">{n}</span>' for n in range(1, 6))
    rejilla = (f'<div><div class="e-eje-titulo" style="margin:0 0 6px 25px">Impacto ↑</div>'
               f'<div class="e-rejilla" role="img" aria-label="Mapa de probabilidad e impacto de los cinco riesgos">{celdas}</div>'
               f'<div class="e-eje-titulo" style="text-align:right;margin-top:4px">Probabilidad →</div></div>')
    lista = ""
    for n, r in enumerate(riesgos, 1):
        sev = severidad_de(r["probabilidad"], r["impacto"])
        lista += (f'<li data-abre="r-x{n}" tabindex="0" role="button" aria-label="Ver detalle del riesgo {n}">'
                  f'<span class="e-bola">{n}</span><div><h3>{esc(nombre_corto(r))}'
                  f'<span class="e-sev" style="{_c(COLOR_SEV[sev])}"><i class="e-punto" aria-hidden="true"></i>'
                  f'Severidad {sev}</span></h3>'
                  f'<p>{esc(r.get("consecuencia_negocio") or _oracion(r.get("consecuencia")))}</p></div></li>')
    return f'<div class="d-tarjeta e-mapa">{rejilla}<ol class="e-lista-riesgos">{lista}</ol></div>'


def plan(iniciativas: list[dict], riesgos: list[dict], matriz: dict[str, Resultado]) -> str:
    columnas = {h: [] for h in HORIZONTE}
    for j, ini in enumerate(iniciativas, 1):
        h, estimado = horizonte_de(ini)
        reduce = "".join(f'<span class="e-chip">{esc(nombre_corto(riesgos[n - 1]))}</span>'
                         for n in ini.get("riesgos", []) if 1 <= n <= len(riesgos))
        columnas[h].append(
            f'<article class="d-tarjeta e-ini" data-abre="i-x{j}" tabindex="0" role="button" '
            f'aria-label="Ver detalle de la iniciativa: {esc(ini.get("titulo"))}"><h3>{esc(ini.get("titulo"))}</h3>'
            f'<div class="e-ini-meta"><span>{ESFUERZO.get(ini.get("esfuerzo"), "")}</span>'
            + ('<span class="e-estim">· plazo estimado</span>' if estimado else "") + "</div>"
            + (f'<div class="e-ini-meta">Reduce: {reduce}</div>' if reduce else "") + "</article>")
    fases = "".join(f'<div class="e-fase"><div class="e-fase-cab">{HORIZONTE[h]}<span class="d-mono">{len(c)}</span></div>'
                    + ("".join(c) or '<div class="e-vacio">Sin iniciativas en este plazo.</div>') + "</div>"
                    for h, c in columnas.items())
    pr = proyeccion(matriz, iniciativas)
    antes = ""
    if pr["hoy"] is not None and pr["estimado"] is not None:
        antes = (f'<div class="d-tarjeta e-antes d-crece"><div class="e-antes-titulo">Madurez antes y después del plan '
                 f'<span class="e-estim">· estimación</span></div>'
                 f'<div class="e-antes-fila"><span>Hoy</span><div class="d-barra"><i style="width:{pr["hoy"]:.1f}%"></i></div>'
                 f'<b>{pr["hoy"]:.0f}%</b></div>'
                 f'<div class="e-antes-fila"><span>Al terminar</span><div class="d-barra"><i class="e-estimada" '
                 f'style="width:{pr["estimado"]:.1f}%"></i></div><b>{pr["estimado"]:.0f}%</b></div>'
                 f'<div class="e-nota">Estimación: supone que todas las medidas de las cinco iniciativas quedan implementadas '
                 f'y que el resto sigue igual.</div></div>')
    return f'<div class="e-plan">{fases}</div>{antes}'


def peticiones(res: dict) -> str:
    lista = res.get("peticiones") or []
    cuerpo = ('<ol class="d-tarjeta e-peticiones">' + "".join(f"<li>{esc(t)}</li>" for t in lista) + "</ol>"
              if lista else _aviso(AVISO_ANTERIOR.format(que="las peticiones de información al cliente")))
    return cuerpo + f'<p class="e-final">{LINEA_FINAL}</p>'


# ------------------------------------------------------------------------------------------ vista
def vista(rep: dict, matriz: dict[str, Resultado], clave_riesgos: str = "riesgos", clave_roadmap: str = "iniciativas",
          previo: dict | None = None, riesgos_previos: list[dict] | None = None) -> tuple[str, list[tuple]]:
    """HTML de la vista ejecutiva y sus secciones para el índice lateral. ``previo`` (indicadores v1) y
    ``riesgos_previos`` solo en el reporte actualizado, para mostrar el cambio desde la evaluación inicial."""
    res = rep.get("resumen_ejecutivo", {}) or {}
    riesgos = rep.get(clave_riesgos) or []
    inis = rep.get(clave_roadmap) or []
    ind = indicadores(matriz)
    html = (veredicto(res, riesgos)
            + f'<div style="margin-top:14px">{indicadores_clave(ind, riesgos, previo, riesgos_previos)}</div>'
            + seccion("en-juego", "Qué está en juego", "Lo que la situación actual significa para el negocio.", en_juego(res))
            + seccion("controles", "Estado por control",
                      "Cómo están las medidas de cada control, del más débil al más sólido. El porcentaje es su madurez.",
                      controles(matriz))
            + seccion("mapa", "Mapa de riesgos", "Los cinco riesgos según su probabilidad y su impacto en el negocio.",
                      mapa_riesgos(riesgos))
            + seccion("plan", "Plan", "Las cinco iniciativas por plazo y cuánto subiría la madurez al completarlas.",
                      plan(inis, riesgos, matriz))
            + seccion("peticiones", "Lo que necesitamos de ustedes",
                      "La información que más mejoraría la confianza del diagnóstico.", peticiones(res)))
    secciones = [("veredicto", "Veredicto", None), ("en-juego", "Qué está en juego", None), ("controles", "Estado por control", 15),
                 ("mapa", "Mapa de riesgos", len(riesgos)), ("plan", "Plan", len(inis)), ("peticiones", "Peticiones", None)]
    html += fichas(riesgos, inis, "x", matriz, tecnica=False, aportes=proyeccion(matriz, inis)["aportes"])
    return f'<div class="e-vista d-crece" data-conteos="{conteos(ind)}">{html}</div>', secciones
