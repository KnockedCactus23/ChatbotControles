"""Dashboard de los reportes (Reporte inicial v1 y Reporte actualizado v2), según el mockup aprobado
(mockup/resumen.html): más gráfica que texto; el texto completo queda en los entregables descargables.

Clases con prefijo ``d-`` para no chocar con las de ``ui.py`` (que siguen sirviendo a los HTML descargables).
Cada pieza que lleva un estado marca ``data-e`` para el resaltado cruzado por estado (la leyenda del resumen).
Las interacciones (resaltado, vínculo riesgos ↔ roadmap, "Leer más", filtros de la matriz, índice lateral y
entrada animada) viven en ``script()``, un único script con delegación de eventos que se instala una vez.

Todo texto que viene de Claude o del usuario pasa por ``esc()``. ``st.html`` elimina ``<svg>``: los chevrons
se dibujan con CSS.
"""

from .controls import catalogo, control, salvaguarda
from .state import ESTADOS, ETIQUETA_APLICABILIDAD, SITUACION_RIESGO, Resultado, horizonte_de, severidad_de
from .ui import ETIQUETA_CORTA, ESTADO_INICIATIVA, esc

UNIDAD = 30          # px por salvaguarda en "Estado por control": la misma escala en todas las filas
TOP_BRECHAS = 5      # controles con mayores brechas que se abren para ver por qué
ESFUERZO = {"bajo": 1, "medio": 2, "alto": 3}
HORIZONTE = {"0-30": "Primeros 30 días", "30-90": "De 30 a 90 días", "90-180": "De 90 a 180 días"}

# ------------------------------------------------------------------------------------------- CSS
# Sin el carácter de menor que en ninguna parte (st.html descarta el <style> completo).
CSS = """
<style>
.d-sec { display: grid; gap: 14px; margin: 40px 0 0; scroll-margin-top: 80px; }
.d-sec-cab { display: grid; gap: 2px; }
.d-sec h2 { font-size: 21px; line-height: 28px; letter-spacing: -0.015em; font-weight: 600; color: var(--ink); margin: 0; padding: 0; }
.d-sec-sub { font-size: 13px; color: var(--ink-3); line-height: 1.5; }
.d-tarjeta { background: var(--surface); border-radius: 10px; box-shadow: var(--shadow-1); }
.d-mono { font-family: var(--mono); font-size: 12px; font-weight: 500; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; }
.d-num { font-variant-numeric: tabular-nums; }
.d-chev { width: 28px; height: 28px; display: grid; place-items: center; border-radius: 6px; color: var(--ink-3); flex: none;
  transition: transform 140ms ease-out, background-color 80ms; }
.d-chev::before { content: ""; width: 7px; height: 7px; border-right: 1.6px solid currentColor; border-bottom: 1.6px solid currentColor;
  transform: translateY(-2px) rotate(45deg); }
details[open] > summary .d-chev { transform: rotate(180deg); }
summary:hover .d-chev { background: var(--sunken); color: var(--ink); }
.d-det > summary { list-style: none; cursor: pointer; }
.d-det > summary::-webkit-details-marker { display: none; }

/* Cabecera del reporte */
.d-cab h1 { font-size: 26px; line-height: 32px; letter-spacing: -0.02em; font-weight: 600; color: var(--ink); margin: 0; padding: 0; }
.d-cab h1 span { color: var(--ink-3); font-weight: 400; }
.d-cab-sub { font-size: 13px; color: var(--ink-3); margin-top: 2px; }

/* Marcas de estado: un punto de color junto a la palabra (paleta segura para daltonismo y escala de grises) */
.d-m { width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex: none; }
.d-m-implementado { background: var(--st-implementado); }
.d-m-parcial { background: var(--st-parcial); }
.d-m-no_implementado { background: var(--st-no_implementado); }
.d-m-no_verificado { background: var(--st-no_verificado); }
.d-m-no_aplicable { background: var(--st-no_aplicable); }
.d-s { display: block; height: 100%; border-radius: 3px; box-sizing: border-box; }

/* Resaltado cruzado por estado (momento firma) */
[data-e] { transition: opacity 160ms ease-out, filter 160ms ease-out; }
body[data-foco="implementado"] [data-e]:not([data-e="implementado"]),
body[data-foco="parcial"] [data-e]:not([data-e="parcial"]),
body[data-foco="no_implementado"] [data-e]:not([data-e="no_implementado"]),
body[data-foco="no_verificado"] [data-e]:not([data-e="no_verificado"]),
body[data-foco="no_aplicable"] [data-e]:not([data-e="no_aplicable"]) { opacity: .16; filter: saturate(.3); }

/* Resumen: KPIs + distribución */
.d-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); }
.d-kpi { padding: 18px 20px; display: grid; gap: 6px; align-content: start; }
.d-kpi + .d-kpi { border-left: 1px solid var(--rule); }
.d-kpi-nombre { font-size: 12px; font-weight: 500; color: var(--ink-3); }
.d-kpi-cifra { font-size: 30px; line-height: 36px; font-weight: 600; letter-spacing: -0.03em; color: var(--ink); font-variant-numeric: tabular-nums; }
.d-kpi-cifra small { font-size: .5em; font-weight: 500; color: var(--ink-3); letter-spacing: 0; margin-left: 1px; }
.d-kpi-cifra .d-nd { font-size: 15px; letter-spacing: -0.01em; font-weight: 500; }
.d-kpi-nota { font-size: 12px; line-height: 18px; color: var(--ink-3); }
.d-kpi-nota b { color: var(--ink); font-weight: 600; }
.d-delta { display: inline-flex; align-items: center; gap: 6px; font: 500 11px/16px var(--mono); color: var(--ink-2); }
.d-delta::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--ink-3); }
.d-delta.d-mejor::before { background: var(--st-implementado); }
.d-delta.d-peor::before { background: var(--st-no_implementado); }
.d-barra { height: 6px; border-radius: 3px; background: var(--sunken); overflow: hidden; }
.d-barra i { display: block; height: 100%; border-radius: 3px; background: var(--accent); transform-origin: left; }
.d-barra i.d-mala { background: var(--st-no_implementado); }
.d-distribucion { padding: 16px 20px 18px; border-top: 1px solid var(--rule); display: grid; gap: 12px; }
.d-apilada { display: flex; gap: 2px; height: 16px; }
.d-leyenda { display: flex; flex-wrap: wrap; gap: 4px; }
.d-leyenda button { display: inline-flex; align-items: center; gap: 7px; border: 0; background: transparent; padding: 4px 9px 4px 6px;
  border-radius: 6px; font: 400 12px/18px var(--font); color: var(--ink-2); cursor: pointer; transition: background-color 80ms, opacity 160ms; }
.d-leyenda button:hover, .d-leyenda button[aria-pressed="true"] { background: var(--sunken); color: var(--ink); }
.d-leyenda button:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.d-leyenda b { color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }

/* Postura */
.d-postura { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); }
.d-postura > div { padding: 20px; }
.d-postura > div + div { border-left: 1px solid var(--rule); }
.d-titular { font-size: 18px; line-height: 27px; color: var(--ink); font-weight: 500; letter-spacing: -0.01em; margin: 0 0 4px; text-wrap: pretty; }
.d-dato { display: grid; gap: 6px; margin-top: 12px; }
.d-dato-cab { display: flex; justify-content: space-between; gap: 12px; font-size: 12px; color: var(--ink-3); }
.d-dato-cab b { color: var(--ink); font-weight: 600; white-space: nowrap; font-variant-numeric: tabular-nums; }
.d-largo { font-size: 13px; line-height: 21px; color: var(--ink-2); margin: 18px 0 0; white-space: pre-line; }
.d-largo:not(.d-abierto) { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.d-leer { border: 0; background: none; padding: 0; margin-top: 6px; font: 500 12px/18px var(--font); color: var(--accent); cursor: pointer; }
.d-leer:hover { text-decoration: underline; }
.d-mini { font-size: 12px; font-weight: 500; color: var(--ink-3); margin: 0 0 10px; padding: 0; }
.d-mini + .d-etiquetas + .d-mini { margin-top: 18px; }
.d-etiquetas { display: flex; flex-wrap: wrap; gap: 6px; }
.d-etiqueta { font-size: 12px; line-height: 18px; padding: 3px 9px; border-radius: 99px; background: var(--sunken); color: var(--ink);
  border: 1px solid var(--rule); display: inline-flex; gap: 6px; align-items: baseline; }
.d-etiqueta.d-grave { background: var(--tint-no_implementado); border-color: transparent; }
.d-etiqueta .d-mono { color: var(--ink-3); font-size: 11px; font-weight: 400; }

/* Estado por control */
.d-ccab, .d-crow { display: grid; grid-template-columns: 330px minmax(0, 1fr) 28px; gap: 16px; align-items: center; padding: 6px 12px 6px 18px; }
.d-ccab { font-size: 11px; font-weight: 500; color: var(--ink-3); border-bottom: 1px solid var(--rule); padding-top: 10px; padding-bottom: 8px; }
.d-cnom { display: flex; align-items: center; min-width: 0; font-size: 13px; line-height: 18px; color: var(--ink); }
.d-cnom .d-nombre { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.d-cnom .d-mono { margin-right: 8px; color: var(--ink); flex: none; }
.d-rank { flex: none; display: inline-block; font-size: 10px; line-height: 15px; font-weight: 600; color: var(--ink);
  background: var(--tint-no_implementado); border-radius: 3px; padding: 0 5px; margin-left: 8px; }
.d-rank.d-nuevo { background: var(--accent-tint); }
.d-cbarra { display: flex; align-items: center; gap: 10px; min-width: 0; }
.d-segs { display: flex; gap: 2px; height: 18px; flex: none; }
.d-segs .d-s { display: grid; place-items: center; font-size: 11px; font-weight: 600; color: var(--seg-ink); min-width: 18px;
  font-variant-numeric: tabular-nums; line-height: 1; text-box: trim-both cap alphabetic; }
.d-segs .d-s[data-e="implementado"], .d-segs .d-s[data-e="no_implementado"] { color: var(--seg-ink-fuerte); }
.d-segs .d-s[data-e="no_aplicable"] { color: var(--ink-2); }
.d-cpct { font-size: 12px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; white-space: nowrap; }
.d-cpct.d-nd { color: var(--ink-3); font-weight: 500; }
.d-cd + .d-cd { border-top: 1px solid var(--rule); }
details.d-cd > summary:hover { background: color-mix(in oklch, var(--sunken) 55%, transparent); }
details.d-cd[open] { background: var(--sunken); }
.d-cdet { padding: 2px 18px 14px; display: grid; gap: 10px; }
.d-cdet p { margin: 0; font-size: 13px; line-height: 21px; max-width: 90ch; color: var(--ink-2); }
.d-lista-sv { display: flex; flex-wrap: wrap; gap: 6px; }
.d-sv { display: inline-flex; gap: 6px; align-items: center; font-size: 12px; padding: 2px 8px 2px 6px; border-radius: 4px;
  background: var(--surface); border: 1px solid var(--rule); color: var(--ink); }
.d-sv .d-mono { font-size: 11px; }

/* Riesgos */
.d-riesgo > summary { display: grid; grid-template-columns: 22px minmax(0, 1fr) 84px 220px 28px; gap: 14px; align-items: center;
  padding: 12px 12px 12px 18px; transition: background-color 80ms; }
.d-riesgos.d-con-sit .d-riesgo > summary { grid-template-columns: 22px minmax(0, 1fr) 84px 150px 190px 28px; }
.d-riesgo + .d-riesgo { border-top: 1px solid var(--rule); }
.d-riesgo > summary:hover { background: color-mix(in oklch, var(--sunken) 55%, transparent); }
.d-riesgo[open] { background: var(--sunken); }
.d-rnum { font-size: 13px; font-weight: 600; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.d-rtitulo { font-size: 14px; color: var(--ink); font-weight: 500; line-height: 20px; min-width: 0; }
.d-rtitulo small { display: block; font-size: 12px; color: var(--ink-3); font-weight: 400; line-height: 18px; }
/* Severidad: punto de color + palabra, como los estados */
.d-sevp { display: grid; gap: 1px; justify-items: start; }
.d-sevp small { font: 500 11px/14px var(--mono); color: var(--ink-3); font-variant-numeric: tabular-nums; }
.d-sev { font-size: 12px; font-weight: 500; color: var(--ink); justify-self: start; display: inline-flex; gap: 7px; align-items: center; white-space: nowrap; }
.d-sev::before { content: ""; width: 9px; height: 9px; border-radius: 50%; background: var(--st-no_verificado); }
.d-sev.d-alta::before { background: var(--st-no_implementado); }
.d-sev.d-media::before { background: var(--st-parcial); }
.d-sev.d-baja::before { background: var(--st-implementado); }
.d-plazo { font-size: 12px; color: var(--ink-2); white-space: nowrap; }
.d-plazo small { display: block; font-size: 11px; color: var(--ink-3); font-style: italic; }
.d-sit { display: grid; gap: 3px; justify-items: start; }
.d-sit small { font-size: 11px; color: var(--ink-3); }
.d-rbarra { display: grid; grid-template-columns: 1fr auto; gap: 10px; align-items: center; }
.d-rbarra .d-apilada { height: 8px; }
.d-rbarra small { font-size: 12px; color: var(--ink-3); white-space: nowrap; }
.d-rdetalle { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; padding: 0 18px 18px 54px; }
.d-rdetalle h3 { font-size: 11px; font-weight: 500; color: var(--ink-3); margin: 0 0 2px; padding: 0; }
.d-rdetalle p { margin: 0; font-size: 13px; line-height: 20px; color: var(--ink-2); }
.d-rdetalle .d-ancho { grid-column: 1 / -1; }

/* Vínculo riesgos ↔ roadmap */
.d-vinculo { transition: opacity 160ms ease-out, background-color 160ms; }
body.d-con-vinculo .d-vinculo:not(.d-activo) { opacity: .35; }
body.d-con-vinculo .d-vinculo.d-activo { background: var(--accent-tint) !important; }
.d-chip-r { font-size: 12px; line-height: 18px; padding: 2px 8px; border-radius: 99px; background: var(--sunken); border: 1px solid var(--rule);
  color: var(--ink); white-space: nowrap; display: inline-flex; gap: 5px; }
.d-chip-r .d-mono { color: var(--ink-3); font-size: 11px; font-weight: 400; }
.d-chips { display: flex; flex-wrap: wrap; gap: 4px; }

/* Roadmap */
.d-roadmap { overflow-x: auto; }
.d-rm { width: 100%; border-collapse: collapse; min-width: 760px; }
.d-rm th { font-size: 11px; font-weight: 500; color: var(--ink-3); text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--rule);
  white-space: nowrap; background: transparent; }
.d-rm td { padding: 12px 14px; border-top: 1px solid var(--rule); border-bottom: 0; vertical-align: middle; font-size: 13px; color: var(--ink-2); }
.d-rm tbody tr:first-child td { border-top: 0; }
.d-prio { font-size: 13px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; }
.d-ini { color: var(--ink); font-weight: 500; line-height: 19px; }
.d-ini small { display: block; color: var(--ink-3); font-weight: 400; font-size: 12px; line-height: 17px; margin-top: 2px; }
.d-tipo { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 99px; white-space: nowrap; color: var(--ink); }
.d-tipo.d-qw { background: var(--accent-tint); }
.d-tipo.d-pr { background: var(--sunken); box-shadow: inset 0 0 0 1px var(--rule-2); }
.d-esfuerzo { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; width: 72px; }
.d-esfuerzo i { height: 8px; border-radius: 2px; background: var(--sunken); box-shadow: inset 0 0 0 1px var(--rule); }
.d-esfuerzo i.d-on { background: var(--ink-3); box-shadow: none; }
.d-esf-txt { font-size: 11px; color: var(--ink-3); margin-top: 3px; }
.d-estado-ini { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 99px; white-space: nowrap; color: var(--ink); background: var(--sunken); }
.d-estado-ini.d-completada { background: var(--tint-implementado); }
.d-estado-ini.d-en_progreso { background: var(--tint-parcial); }

/* Matriz */
.d-matriz > summary { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 12px 14px 18px; border-radius: 10px; }
.d-matriz > summary:hover { background: color-mix(in oklch, var(--sunken) 55%, transparent); }
.d-matriz[open] > summary { border-bottom: 1px solid var(--rule); border-radius: 10px 10px 0 0; }
.d-matriz h2 { font-size: 21px; line-height: 28px; letter-spacing: -0.015em; font-weight: 600; color: var(--ink); margin: 0; padding: 0; }
.d-filtros { display: flex; flex-wrap: wrap; gap: 6px; padding: 12px 18px; border-bottom: 1px solid var(--rule); }
.d-filtro { border: 1px solid var(--rule-2); background: var(--surface); color: var(--ink-2); border-radius: 99px; padding: 3px 10px;
  font: 500 12px/18px var(--font); cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.d-filtro[aria-pressed="true"] { background: var(--accent-tint); border-color: transparent; color: var(--ink); }
.d-filtro b { font-variant-numeric: tabular-nums; }
.d-mx-marco { overflow: auto; max-height: 640px; }
.d-mx { width: 100%; border-collapse: collapse; min-width: 820px; }
.d-mx th { position: sticky; top: 0; background: var(--sunken); font-size: 11px; font-weight: 500; color: var(--ink-3); text-align: left;
  padding: 8px 12px; z-index: 1; }
.d-mx td { padding: 10px 12px; border-top: 1px solid var(--rule); border-bottom: 0; font-size: 13px; line-height: 19px; vertical-align: top; color: var(--ink-2); }
.d-mx td.d-sid { white-space: nowrap; color: var(--ink); }
.d-mx .d-sal { color: var(--ink); max-width: 30ch; }
.d-mx .d-sal small { display: block; color: var(--ink-3); font-size: 12px; margin-top: 2px; }
.d-mx .d-est { display: inline-flex; gap: 6px; align-items: center; white-space: nowrap; font-size: 12px; font-weight: 500; color: var(--ink); }
.d-mx .d-aplic { display: block; font-size: 11px; color: var(--ink-3); margin-top: 3px; }
.d-mx .d-cita { color: var(--ink-3); font-size: 12px; margin-top: 4px; display: block; }
.d-mx .d-obs { color: var(--ink-3); font-size: 12px; margin-top: 4px; display: block; }
.d-mx .d-pag { font-family: var(--mono); font-size: 11px; white-space: nowrap; padding: 1px 6px; background: var(--sunken); border-radius: 3px; color: var(--ink-2); }
.d-mx tr.d-cambio td { background: color-mix(in oklch, var(--accent) 8%, transparent); }
.d-matriz[data-filtro="implementado"] tbody tr:not([data-e="implementado"]),
.d-matriz[data-filtro="parcial"] tbody tr:not([data-e="parcial"]),
.d-matriz[data-filtro="no_implementado"] tbody tr:not([data-e="no_implementado"]),
.d-matriz[data-filtro="no_verificado"] tbody tr:not([data-e="no_verificado"]),
.d-matriz[data-filtro="no_aplicable"] tbody tr:not([data-e="no_aplicable"]) { display: none; }

/* Pendientes */
.d-dos { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; }
.d-dos .d-tarjeta { padding: 18px 20px; display: grid; gap: 12px; align-content: start; }
.d-dos h3 { font-size: 14px; line-height: 20px; font-weight: 600; color: var(--ink); margin: 0; padding: 0; }
.d-dos h3 span { color: var(--ink-3); font-weight: 400; font-size: 13px; }
.d-faltante { margin: 0; padding: 0 0 0 16px; display: grid; gap: 6px; font-size: 13px; line-height: 19px; color: var(--ink); }
.d-razones { margin: 0; padding: 0; list-style: none; display: grid; gap: 10px; }
.d-razones li { display: grid; grid-template-columns: 26px 1fr; gap: 10px; font-size: 13px; line-height: 19px; color: var(--ink); }
.d-razones b { font-size: 15px; font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }
.d-nota { font-size: 12px; color: var(--ink-3); padding: 10px 14px; border: 1px dashed var(--rule-2); border-radius: 8px; }

/* Índice lateral (scrollspy) y estado compacto */
.d-lado-marca { font-size: 15px; font-weight: 600; color: var(--ink); letter-spacing: -0.01em; padding: 0 8px; margin: 2px 0 16px; }
.d-lado-marca small { display: block; font-weight: 400; font-size: 12px; color: var(--ink-3); letter-spacing: 0; }
.d-indice { display: grid; gap: 1px; margin-bottom: 18px; }
.d-indice-titulo { font-size: 11px; font-weight: 500; color: var(--ink-3); padding: 0 8px 6px; }
.d-indice a { position: relative; display: flex; justify-content: space-between; align-items: center; padding: 6px 8px 6px 12px;
  border-radius: 6px; color: var(--ink-2) !important; text-decoration: none !important; font-size: 13px; transition: background-color 80ms, color 80ms; }
.d-indice a:hover { background: color-mix(in oklch, var(--sunken) 70%, transparent); color: var(--ink) !important; }
.d-indice a::before { content: ""; position: absolute; left: 2px; top: 8px; bottom: 8px; width: 2px; border-radius: 2px; background: transparent; transition: background-color 120ms; }
.d-indice a[aria-current="true"] { background: var(--surface); color: var(--ink) !important; font-weight: 500; box-shadow: var(--shadow-1); }
.d-indice a[aria-current="true"]::before { background: var(--accent); }
.d-indice a .d-mono { color: var(--ink-3); font-size: 11px; font-weight: 400; }
.d-lado-estado { display: grid; gap: 10px; padding: 0 8px; margin-bottom: 20px; }
.d-lado-cifras { display: flex; gap: 20px; }
.d-lado-cifras div { display: grid; }
.d-lado-cifras b { font-size: 22px; line-height: 28px; font-weight: 600; letter-spacing: -0.02em; color: var(--ink); font-variant-numeric: tabular-nums; }
.d-lado-cifras b small { font-size: .55em; color: var(--ink-3); font-weight: 500; }
.d-lado-cifras span { font-size: 11px; color: var(--ink-3); }
.d-lado-conteos { margin: 0; padding: 0; list-style: none; display: grid; gap: 5px; }
.d-lado-conteos li { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--ink-2); }
.d-lado-conteos b { margin-left: auto; color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }

/* Entrada: barra que se llena por segmentos (solo con movimiento permitido; el script pone d-cargando) */
@media (prefers-reduced-motion: no-preference) {
  .d-crece .d-s { transform-origin: left; transition: transform 380ms cubic-bezier(.2, .8, .2, 1), opacity 160ms ease-out, filter 160ms ease-out; }
  .d-crece.d-cargando .d-s { transform: scaleX(0); }
  .d-crece .d-barra i { transition: transform 700ms cubic-bezier(.2, .8, .2, 1); }
  .d-crece.d-cargando .d-barra i { transform: scaleX(0); }
}
@media (prefers-reduced-motion: reduce) { .d-chev, [data-e], .d-vinculo { transition: none !important; } }

/* Filtro por estado (Fase 3): las filas que no tienen el estado elegido se ocultan; el aviso flota abajo */
body[data-filtro="implementado"] [data-estados]:not([data-estados~="implementado"]),
body[data-filtro="parcial"] [data-estados]:not([data-estados~="parcial"]),
body[data-filtro="no_implementado"] [data-estados]:not([data-estados~="no_implementado"]),
body[data-filtro="no_verificado"] [data-estados]:not([data-estados~="no_verificado"]),
body[data-filtro="no_aplicable"] [data-estados]:not([data-estados~="no_aplicable"]) { display: none !important; }
.d-leyenda button:disabled { opacity: .45; cursor: default; background: transparent; }
.d-principal .d-s[data-e], .e-pila .d-s[data-e], .d-segs .d-s[data-e] { cursor: pointer; }
.d-filtro-aviso { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); z-index: 1000001; display: flex; align-items: center;
  gap: 10px; padding: 8px 8px 8px 14px; border-radius: 999px; background: var(--ink); color: var(--paper); font: 400 13px/18px var(--font);
  box-shadow: 0 8px 24px color-mix(in srgb, black 25%, transparent); white-space: nowrap; }
.d-filtro-aviso b { font-weight: 600; }
.d-filtro-aviso .d-m { box-shadow: 0 0 0 1.5px var(--paper); }
.d-filtro-aviso button { border: 0; border-radius: 999px; padding: 4px 12px; background: color-mix(in srgb, var(--paper) 18%, transparent);
  color: var(--paper); font: 500 12px/18px var(--font); cursor: pointer; }
.d-filtro-aviso button:hover, .d-filtro-aviso button:focus-visible { background: color-mix(in srgb, var(--paper) 30%, transparent); outline: none; }

/* Panel lateral de riesgos e iniciativas (Fase 3). Las fichas viajan ocultas en la página; el script las copia al panel. */
.d-fichas { display: none; }
[data-abre] { cursor: pointer; }
[data-abre]:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.d-riesgo[data-abre] .d-chev::before { transform: translateX(-2px) rotate(-45deg); }
.d-rm tr[data-abre]:hover td { background: color-mix(in oklch, var(--sunken) 55%, transparent); }
.d-cajon-fondo { position: fixed; inset: 0; z-index: 1000002; background: color-mix(in srgb, black 30%, transparent); opacity: 0;
  transition: opacity 180ms ease-out; }
.d-cajon { position: fixed; top: 0; right: 0; bottom: 0; z-index: 1000003; width: min(460px, 100vw); overflow-y: auto; box-sizing: border-box;
  padding: 20px 24px 32px; background: var(--surface); color: var(--ink); font-family: var(--font); box-shadow: -12px 0 32px color-mix(in srgb, black 18%, transparent);
  transform: translateX(100%); transition: transform 220ms cubic-bezier(.2, .8, .2, 1); }
.d-cajon-abierto .d-cajon-fondo { opacity: 1; }
.d-cajon-abierto .d-cajon { transform: none; }
.d-cajon-cerrar { position: sticky; top: 0; float: right; width: 32px; height: 32px; border: 0; border-radius: 8px; background: var(--sunken);
  color: var(--ink); font: 400 20px/1 var(--font); cursor: pointer; }
.d-cajon-cerrar:hover, .d-cajon-cerrar:focus-visible { background: var(--rule); outline: 2px solid var(--accent); outline-offset: 1px; }
.d-cajon .d-ficha-tipo { font-size: 12px; font-weight: 500; color: var(--ink-3); margin: 6px 0 4px; }
.d-cajon h2 { font-size: 21px; line-height: 27px; font-weight: 600; letter-spacing: -0.015em; margin: 0 40px 4px 0; padding: 0; color: var(--ink); }
.d-cajon h3 { font-size: 12px; font-weight: 600; color: var(--ink-3); margin: 22px 0 8px; padding: 0; letter-spacing: 0; }
.d-cajon p { font-size: 14px; line-height: 21px; color: var(--ink-2); margin: 0; }
.d-cajon .d-ficha-sub { font-size: 13px; color: var(--ink-3); }
.d-ficha-meta { display: flex; flex-wrap: wrap; gap: 8px 14px; margin-top: 12px; font-size: 13px; color: var(--ink-2); }
.d-ficha-meta span { display: inline-flex; align-items: center; gap: 7px; }
.d-ficha-meta .d-m { width: 10px; height: 10px; }
.d-ficha-escalas { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.d-ficha-escala { padding: 12px 14px; border-radius: 8px; background: var(--sunken); display: grid; gap: 4px; align-content: start; }
.d-ficha-escala b { font-size: 22px; line-height: 26px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; }
.d-ficha-escala b small { font-size: 13px; font-weight: 400; color: var(--ink-3); }
.d-ficha-escala span { font-size: 12px; font-weight: 500; color: var(--ink-3); }
.d-ficha-escala p { font-size: 12px; line-height: 17px; }
.d-ficha-enlaces { display: grid; gap: 6px; }
.d-ficha-enlaces button { display: grid; grid-template-columns: 26px minmax(0, 1fr) auto; gap: 10px; align-items: center; text-align: left;
  border: 0; border-radius: 8px; padding: 10px 12px; background: var(--sunken); color: var(--ink); font: 500 13px/18px var(--font); cursor: pointer; }
.d-ficha-enlaces button:hover, .d-ficha-enlaces button:focus-visible { background: var(--accent-tint); outline: none; }
.d-ficha-enlaces button small { font-weight: 400; color: var(--ink-3); font-size: 12px; }
.d-ficha-enlaces button i { font-style: normal; color: var(--ink-3); }
.d-ficha-enlaces .d-mono { color: var(--ink-3); }
.d-ficha-aporte { display: flex; align-items: baseline; gap: 8px; }
.d-ficha-aporte b { font-size: 26px; line-height: 30px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; }
.d-cajon .d-lista-sv { display: flex; flex-wrap: wrap; gap: 6px; }
@media (prefers-reduced-motion: reduce) { .d-cajon, .d-cajon-fondo { transition: none; } }
/* Visor de evidencia (Fase 5): divide la pantalla; el PDF queda a la derecha y la matriz se reacomoda a la izquierda. */
:root { --visor-w: min(48vw, 820px); --visor-marca: oklch(0.91 0.17 100 / 0.5); --visor-borde: oklch(0.78 0.16 92); }
.d-mx .d-ev { display: inline-flex; align-items: center; gap: 6px; border: 1px solid transparent; cursor: pointer; line-height: 18px; }
.d-mx .d-ev i { width: 5px; height: 5px; border-top: 1.5px solid currentColor; border-right: 1.5px solid currentColor; transform: rotate(45deg); opacity: .7; }
.d-mx .d-ev:hover { border-color: var(--rule-2); color: var(--ink); }
.d-mx .d-ev:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; color: var(--ink); }
.d-mx tr.d-ev-actual td { background: color-mix(in srgb, var(--accent) 9%, transparent); }
.d-mx tr.d-ev-actual .d-ev { border-color: var(--accent); color: var(--ink); }
@media (min-width: 1200px) { body.d-con-visor [data-testid="stMain"] { padding-right: var(--visor-w); }
  /* Con la pantalla dividida la matriz queda en ID, salvaguarda, estado y evidencia; la justificación pasa al visor. */
  body.d-con-visor .d-mx { min-width: 0; }
  body.d-con-visor .d-mx th, body.d-con-visor .d-mx td { padding-left: 8px; padding-right: 8px; }
  body.d-con-visor .d-mx .d-pag { padding: 1px 4px; white-space: normal; text-align: left; }
  body.d-con-visor .d-mx th:nth-child(4), body.d-con-visor .d-mx td:nth-child(4) { display: none; } }
.d-visor { position: fixed; top: 0; right: 0; bottom: 0; z-index: 1000001; width: var(--visor-w); box-sizing: border-box; display: flex; flex-direction: column;
  background: var(--surface); color: var(--ink); font-family: var(--font); border-left: 1px solid var(--rule);
  box-shadow: -12px 0 32px color-mix(in srgb, black 12%, transparent); transform: translateX(100%); transition: transform 220ms cubic-bezier(.2, .8, .2, 1); }
.d-visor-abierto { transform: none; }
.d-visor-cab { position: relative; padding: 16px 64px 14px 22px; border-bottom: 1px solid var(--rule); }
.d-visor-doc { font: 500 12px/16px var(--mono); color: var(--ink-3); margin: 0 0 4px; font-variant-numeric: tabular-nums; }
.d-visor h2 { font-size: 16px; line-height: 22px; font-weight: 600; letter-spacing: -0.01em; margin: 0; padding: 0; color: var(--ink); }
.d-visor h2 b { font-family: var(--mono); font-weight: 500; color: var(--ink-3); margin-right: 8px; }
.d-visor-estado { display: flex; align-items: center; gap: 8px; margin: 10px 0 0; font-size: 13px; color: var(--ink-2); }
.d-visor-estado::before { content: ""; width: 14px; height: 10px; border-radius: 2px; background: var(--visor-marca); outline: 1px solid var(--visor-borde); flex: none; }
.d-visor-estado[data-modo="no_encontrada"]::before { background: transparent; outline: 1px dashed var(--ink-3); }
.d-visor-estado[data-modo="no_encontrada"] { color: var(--ink); font-weight: 500; }
.d-visor-cita { margin: 10px 0 0; padding: 0 0 0 12px; border-left: 2px solid var(--rule-2); font-size: 13px; line-height: 19px; color: var(--ink-2);
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.d-visor-just { margin: 8px 0 0; font-size: 13px; line-height: 19px; color: var(--ink-2); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.d-visor-just b { font-weight: 600; color: var(--ink); }
.d-visor-cerrar { position: absolute; top: 14px; right: 16px; width: 32px; height: 32px; border: 0; border-radius: 8px; background: var(--sunken);
  color: var(--ink); font: 400 20px/1 var(--font); cursor: pointer; }
.d-visor-cerrar:hover, .d-visor-cerrar:focus-visible { background: var(--rule); outline: 2px solid var(--accent); outline-offset: 1px; }
.d-visor-hoja { flex: 1; overflow: auto; background: var(--sunken); padding: 18px; overscroll-behavior: contain; }
.d-visor-pagina { position: relative; margin: 0 auto; max-width: 900px; background: white; box-shadow: 0 1px 3px color-mix(in srgb, black 18%, transparent);
  min-height: 300px; }
.d-visor-pagina img { display: block; width: 100%; height: auto; }
.d-visor-pagina { cursor: zoom-in; }
.d-visor-pagina.d-visor-zoom { width: 200%; max-width: none; cursor: zoom-out; }
.d-visor-pagina:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.d-visor-marca { position: absolute; background: var(--visor-marca); mix-blend-mode: multiply; border-radius: 2px; box-shadow: 0 0 0 1px var(--visor-borde); pointer-events: none; }
.d-visor-texto { max-width: 760px; margin: 0 auto; padding: 24px 28px; background: var(--surface); border: 1px solid var(--rule); white-space: pre-wrap;
  font-size: 13px; line-height: 21px; color: var(--ink-2); }
.d-visor-texto mark { background: var(--visor-marca); color: var(--ink); box-shadow: 0 0 0 1px var(--visor-borde); border-radius: 2px; }
.d-visor-pie { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 10px 16px; border-top: 1px solid var(--rule); }
.d-visor-pie span { font: 500 12px var(--mono); color: var(--ink-3); font-variant-numeric: tabular-nums; }
.d-visor-pie button { height: 34px; padding: 0 14px; border: 1px solid var(--rule-2); border-radius: 6px; background: var(--surface); color: var(--ink);
  font: 500 13px var(--font); cursor: pointer; }
.d-visor-pie button:hover:not(:disabled) { background: var(--sunken); }
.d-visor-pie button:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.d-visor-pie button:disabled { opacity: .45; cursor: default; }
@media (max-width: 1199px) { :root { --visor-w: min(640px, 100vw); } }
@media (max-width: 860px) { :root { --visor-w: 100vw; }
  .d-visor { border-left: 0; } .d-visor-hoja { padding: 10px; } }
@media (prefers-reduced-motion: reduce) { .d-visor { transition: none; } }

/* Responsivo */
@media (max-width: 860px) {
  .d-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .d-kpi { padding: 14px; }
  .d-kpi-cifra { font-size: 24px; line-height: 30px; }
  .d-kpi:nth-child(odd) { border-left: 0; }
  .d-kpi:nth-child(n+3) { border-top: 1px solid var(--rule); }
  .d-postura, .d-dos { grid-template-columns: 1fr; }
  .d-postura > div + div { border-left: 0; border-top: 1px solid var(--rule); }
  .d-ccab { display: none; }
  .d-crow { grid-template-columns: minmax(0, 1fr) 28px; gap: 6px 10px; padding: 8px 12px 8px 14px; }
  .d-crow .d-cbarra { grid-column: 1; grid-row: 2; }
  .d-crow .d-chev, .d-crow .d-sin-chev { grid-row: 1 / span 2; grid-column: 2; }
  .d-riesgo > summary, .d-riesgos.d-con-sit .d-riesgo > summary { grid-template-columns: 18px minmax(0, 1fr) 28px; padding-left: 14px; }
  .d-riesgo .d-sevp, .d-riesgo .d-rbarra, .d-riesgo .d-sit { grid-column: 2; }
  .d-riesgo .d-chev { grid-column: 3; grid-row: 1 / span 4; }
  .d-rdetalle { grid-template-columns: 1fr; padding-left: 46px; }
}
</style>
"""


# ----------------------------------------------------------------------------------- utilidades
def _m(e: str) -> str:
    return f'<span class="d-m d-m-{e}" data-e="{e}" aria-hidden="true"></span>'


def _conteo(ids, matriz: dict[str, Resultado]) -> dict[str, int]:
    c = {e: 0 for e in ESTADOS}
    for i in ids:
        if i in matriz:
            c[matriz[i].estado] += 1
    return c


def _pct(c: dict[str, int]) -> float | None:
    d = c["implementado"] + c["parcial"] + c["no_implementado"]
    return (c["implementado"] + c["parcial"] / 2) / d * 100 if d else None


def _seg(e: str, n: int, estilo: str, texto: bool = False) -> str:
    return (f'<span class="d-s" data-e="{e}" style="background:var(--st-{e});{estilo}" title="{ETIQUETA_CORTA[e]}: {n}">'
            f'{n if texto else ""}</span>')


def _apilada(c: dict[str, int], clase: str = "") -> str:
    return (f'<div class="d-apilada {clase}">'
            + "".join(_seg(e, c[e], f"flex:{c[e]}") for e in ESTADOS if c[e]) + "</div>")


def _sv(sid: str, matriz: dict[str, Resultado]) -> str:
    e = matriz[sid].estado if sid in matriz else "no_verificado"
    return f'<span class="d-sv">{_m(e)}<span class="d-mono">{esc(sid)}</span>{ETIQUETA_CORTA[e]}</span>'


def conteos(ind: dict) -> str:
    """Conteo por estado para el aviso del filtro («Mostrando N …»): "implementado:3 parcial:30 …"."""
    return " ".join(f"{e}:{ind[e]}" for e in ESTADOS)


def _cab(id_: str, titulo: str, sub: str = "") -> str:
    return (f'<div class="d-sec-cab"><h2>{esc(titulo)}</h2>'
            + (f'<span class="d-sec-sub">{esc(sub)}</span>' if sub else "") + "</div>")


def seccion(id_: str, titulo: str, sub: str, cuerpo: str) -> str:
    """Sección con ancla para el índice lateral (``id`` y ``data-seccion``)."""
    return f'<section class="d-sec" id="d-{id_}" data-seccion="{id_}">{_cab(id_, titulo, sub)}{cuerpo}</section>'


def _primera_oracion(texto: str) -> str:
    """Respaldo del titular para evaluaciones anteriores al campo: la primera oración que habla de la postura
    (la primera del texto suele describir a la empresa); si ninguna, la primera."""
    texto = " ".join(str(texto or "").split())
    oraciones, inicio = [], 0
    for i, ch in enumerate(texto):
        if ch == "." and (i + 1 == len(texto) or texto[i + 1] == " ") and i - inicio > 30:
            oraciones.append(texto[inicio:i + 1].strip())
            inicio = i + 1
    if inicio < len(texto):
        oraciones.append(texto[inicio:].strip())
    return next((o for o in oraciones if "postura" in o.lower()), oraciones[0] if oraciones else "")[:220]


def nombre_corto(r: dict) -> str:
    """Nombre corto del riesgo; las evaluaciones anteriores al campo usan el inicio del activo afectado."""
    if r.get("nombre_corto"):
        return r["nombre_corto"]
    base = str(r.get("activo_proceso") or r.get("titulo") or "")
    for sep in ("(", ",", ";", " y "):
        base = base.split(sep)[0]
    palabras = base.split()
    return " ".join(palabras[:3]) + ("…" if len(palabras) > 3 else "")


# ------------------------------------------------------------------------------------- cabecera
def cabecera(titulo: str, version: str, sub: str) -> str:
    return (f'<div class="d-cab"><h1>{esc(titulo)} <span>· {esc(version)}</span></h1>'
            f'<div class="d-cab-sub">{esc(sub)}</div></div>')


# -------------------------------------------------------------------------------------- resumen
def _delta(a, b, unidad: str, menos_es_mejor: bool = False) -> str:
    if a is None or b is None:
        return ""
    d = b - a
    if abs(d) < 0.05:
        return '<span class="d-delta">sin cambio vs v1</span>'
    mejor = (d < 0) if menos_es_mejor else (d > 0)
    num = f"{d:+.1f}" if unidad == "pts" else f"{d:+.0f}"
    return f'<span class="d-delta {"d-mejor" if mejor else "d-peor"}">{num} {unidad} vs v1</span>'


def resumen(ind: dict, previo: dict | None = None) -> str:
    """KPIs del mismo tamaño + barra apilada de las 56 salvaguardas + leyenda interactiva (resaltado por estado)."""
    def cifra(v, dec: int, pct: bool) -> str:
        if v is None:
            return '<div class="d-kpi-cifra"><span class="d-nd">No determinable</span></div>'
        return (f'<div class="d-kpi-cifra"><span data-cuenta="{v}" data-dec="{dec}">{v:.{dec}f}</span>'
                + ("<small>%</small>" if pct else "") + "</div>")

    impl, cob = ind["implementacion"], ind["cobertura"]
    por_cerrar = ind["no_implementado"] + ind["parcial"]
    aplicables = ind["total"] - ind["no_aplicable"]
    p = previo or {}
    d_impl = _delta(p.get("implementacion"), impl, "pts") if previo else ""
    d_cob = _delta(p.get("cobertura"), cob, "pts") if previo else ""
    d_cerrar = _delta(p["no_implementado"] + p["parcial"], por_cerrar, "", True) if previo else ""
    d_nv = _delta(p.get("no_verificado"), ind["no_verificado"], "", True) if previo else ""
    barra = f'<div class="d-barra"><i style="width:{impl or 0:.1f}%"></i></div>' if impl is not None else ""
    kpis = (f'<div class="d-kpi"><div class="d-kpi-nombre">Implementación</div>{cifra(impl, 1, True)}{barra}'
            f'<div class="d-kpi-nota">Sobre las {ind["evaluables"]} salvaguardas evaluables</div>{d_impl}</div>'
            f'<div class="d-kpi"><div class="d-kpi-nombre">Cobertura</div>{cifra(cob, 1, True)}'
            f'<div class="d-kpi-nota">{ind["evaluables"]} de {aplicables} aplicables con evidencia</div>{d_cob}</div>'
            f'<div class="d-kpi"><div class="d-kpi-nombre">Por cerrar</div>{cifra(por_cerrar, 0, False)}'
            f'<div class="d-kpi-nota"><b>{ind["no_implementado"]}</b> sin implementar · {ind["parcial"]} parciales</div>{d_cerrar}</div>'
            f'<div class="d-kpi"><div class="d-kpi-nombre">Sin evidencia</div>{cifra(ind["no_verificado"], 0, False)}'
            f'<div class="d-kpi-nota">No verificadas; pueden mover el porcentaje</div>{d_nv}</div>')
    leyenda = "".join(f'<button type="button" data-foco="{e}" aria-pressed="false"{" disabled" if not ind[e] else ""}>'
                      f'{_m(e)}{ETIQUETA_CORTA[e]} <b>{ind[e]}</b></button>' for e in ESTADOS)
    return (f'<section class="d-tarjeta d-crece" id="d-resumen" data-seccion="resumen" aria-label="Resumen" data-conteos="{conteos(ind)}" style="scroll-margin-top:80px">'
            f'<div class="d-kpis">{kpis}</div><div class="d-distribucion">'
            f'{_apilada(ind, "d-principal")}'
            f'<div class="d-leyenda" role="group" aria-label="Resaltar un estado en toda la página">{leyenda}</div></div></section>')


# -------------------------------------------------------------------------------------- postura
def postura(res: dict, matriz: dict[str, Resultado]) -> str:
    titular = res.get("titular") or _primera_oracion(res.get("postura_inicial"))
    datos = ""
    for d in res.get("datos_clave") or []:
        ancho = 100 * d["valor"] / d["total"] if d.get("total") else 0
        mala = ' class="d-mala"' if d.get("sentido") == "desfavorable" else ""
        datos += (f'<div class="d-dato"><div class="d-dato-cab"><span>{esc(d.get("etiqueta"))}</span>'
                  f'<b>{d["valor"]} de {d["total"]}</b></div><div class="d-barra"><i{mala} style="width:{ancho:.1f}%"></i></div></div>')
    texto = res.get("postura_inicial") or ""
    largo = f'<p class="d-largo d-abierto">{esc(texto)}</p>' if texto else ""  # vista técnica: postura completa
    brechas = res.get("brechas_clave")
    if not brechas:  # evaluaciones anteriores al campo: los No implementado, uno por control
        vistos, brechas = set(), []
        for sid, r in matriz.items():
            cid = salvaguarda(sid).control_id if salvaguarda(sid) else ""
            if r.estado == "no_implementado" and cid not in vistos:
                vistos.add(cid)
                brechas.append({"etiqueta": control(cid).nombre, "salvaguarda": sid})
        brechas = brechas[:6]
    etiquetas = lambda lista, clase: "".join(
        f'<span class="d-etiqueta {clase}">{esc(x.get("etiqueta"))} <span class="d-mono">{esc(x.get("salvaguarda"))}</span></span>'
        for x in lista)
    derecha = f'<h3 class="d-mini">Brechas más graves</h3><div class="d-etiquetas">{etiquetas(brechas, "d-grave")}</div>'
    if res.get("bases"):
        derecha += f'<h3 class="d-mini">Bases aprovechables</h3><div class="d-etiquetas">{etiquetas(res["bases"], "")}</div>'
    return (f'<div class="d-tarjeta d-postura"><div><p class="d-titular">{esc(titular)}</p>{datos}{largo}</div>'
            f'<div>{derecha}</div></div>')


# ------------------------------------------------------------------------------ estado por control
def controles(matriz: dict[str, Resultado], mayores: list[dict], cambiados: set[str] = frozenset()) -> str:
    """Una fila por control con salvaguardas IG1: segmentos por estado (misma escala) y % justo después.
    Los cinco con mayores brechas van primero y se abren con su explicación."""
    explic = {b["control_id"]: b.get("explicacion", "") for b in mayores}
    rango = {b["control_id"]: i for i, b in enumerate(mayores[:TOP_BRECHAS], 1)}
    filas = []
    for c in catalogo().controles:
        ids = [s.id for s in c.ig1]
        if ids:
            cnt = _conteo(ids, matriz)
            filas.append((c, ids, cnt, _pct(cnt)))
    filas.sort(key=lambda f: (rango.get(f[0].id, 99), f[3] is None, f[3] or 0, f[0].numero))
    cuerpo = ""
    for c, ids, cnt, pct in filas:
        segs = "".join(_seg(e, cnt[e], f"width:{cnt[e] * UNIDAD}px", True) for e in ESTADOS if cnt[e])
        p = '<span class="d-cpct d-nd">Sin evidencia</span>' if pct is None else f'<span class="d-cpct">{pct:.0f}%</span>'
        marca = (f'<span class="d-rank">Brecha {rango[c.id]}</span>' if c.id in rango else "")
        if cambiados & set(ids):
            marca += '<span class="d-rank d-nuevo">Cambió en v2</span>'
        # Todas las filas se abren: muestran sus salvaguardas; solo las de mayor brecha llevan además la explicación.
        fila = (f'<div class="d-crow"><span class="d-cnom"><span class="d-mono">{c.id}</span>'
                f'<span class="d-nombre" title="{esc(c.nombre)}">{esc(c.nombre)}</span>{marca}</span>'
                f'<span class="d-cbarra"><span class="d-segs">{segs}</span>{p}</span><span class="d-chev"></span></div>')
        texto = f'<p>{esc(explic.get(c.id))}</p>' if c.id in rango and explic.get(c.id) else ""
        estados = " ".join(e for e in ESTADOS if cnt[e])
        cuerpo += (f'<details class="d-cd d-det" data-estados="{estados}"><summary>{fila}</summary><div class="d-cdet">'
                   f'{texto}<div class="d-lista-sv">{"".join(_sv(i, matriz) for i in ids)}</div></div></details>')
    return (f'<div class="d-tarjeta"><div class="d-ccab"><span>Control</span><span>Salvaguardas por estado · implementación</span>'
            f'<span></span></div>{cuerpo}</div>')


# --------------------------------------------------------------------------------------- riesgos
def _sev(s: str | None) -> str:
    s = s if s in ("alta", "media", "baja") else ""
    return f'<span class="d-sev d-{s}">{esc((s or "—").capitalize())}</span>'


def _sevp(r: dict) -> str:
    """Severidad del riesgo (la calcula el código con probabilidad × impacto) y, si existen, ambas escalas."""
    sev = severidad_de(r.get("probabilidad"), r.get("impacto")) or r.get("severidad")
    escalas = (f'<small title="Probabilidad × impacto">P{r["probabilidad"]} × I{r["impacto"]}</small>'
               if severidad_de(r.get("probabilidad"), r.get("impacto")) else "")
    return f'<span class="d-sevp">{_sev(sev)}{escalas}</span>'


def riesgos(lista: list[dict], matriz: dict[str, Resultado], grupo: str, situacion: list[dict] | None = None) -> str:
    """Filas plegables: número, título y activo, severidad, (situación tras las mejoras), barra de estados de sus
    salvaguardas y "N salvaguardas". ``grupo`` separa los riesgos v1 de los vigentes v2 en el vínculo con el roadmap."""
    cuerpo = ""
    for i, r in enumerate(lista, 1):
        sv = r.get("salvaguardas", [])
        sit = ""
        extra = ""
        if situacion is not None:
            s = situacion[i - 1] if i <= len(situacion) else {}
            clave = s.get("situacion") if s.get("situacion") in SITUACION_RIESGO else "permanece"
            residual = s.get("severidad_residual")
            sit = (f'<span class="d-sit"><span class="d-estado-ini d-{"completada" if clave == "mitigado" else "en_progreso" if clave == "reducido" else ""}">'
                   f'{SITUACION_RIESGO[clave]}</span>' + (f'<small>Residual: {esc(residual)}</small>' if residual else "") + "</span>")
            if s.get("explicacion"):
                extra = f'<div class="d-ancho"><h3>Tras las mejoras</h3><p>{esc(s.get("explicacion"))}</p></div>'
        cuerpo += (f'<details class="d-riesgo d-det d-vinculo" data-riesgo="{grupo}{i}" data-abre="r-{grupo}{i}"><summary>'
                   f'<span class="d-rnum">{i}</span>'
                   f'<span class="d-rtitulo">{esc(r.get("titulo"))}<small>{esc(r.get("activo_proceso"))}</small></span>'
                   f'{_sevp(r)}{sit}'
                   f'<span class="d-rbarra">{_apilada(_conteo(sv, matriz))}<small>{len(sv)} salvaguarda{"s" if len(sv) != 1 else ""}</small></span>'
                   f'<span class="d-chev"></span></summary><div class="d-rdetalle">'
                   + (f'<div class="d-ancho"><p>{esc(r.get("descripcion"))}</p></div>' if r.get("descripcion") else "")
                   + f'<div><h3>Deficiencia</h3><p>{esc(r.get("deficiencia"))}</p></div>'
                   f'<div><h3>Consecuencia probable</h3><p>{esc(r.get("consecuencia"))}</p></div>'
                   f'<div><h3>Severidad</h3><p>{esc(r.get("justificacion"))}</p></div>{extra}'
                   f'<div class="d-lista-sv d-ancho">{"".join(_sv(x, matriz) for x in sv)}</div></div></details>')
    clase = " d-con-sit" if situacion is not None else ""
    return f'<div class="d-tarjeta d-riesgos{clase}">{cuerpo}</div>'


# --------------------------------------------------------------------------------------- roadmap
def _plazo(x: dict) -> str:
    h, estimado = horizonte_de(x)
    return f'{h} días' + ("<small>estimado</small>" if estimado else "")


def roadmap(lista: list[dict], riesgos_ref: list[dict], grupo: str, estados: list[dict] | None = None) -> str:
    """Tabla: prioridad, iniciativa y beneficio, riesgos que reduce (chips con nombre corto), tipo, esfuerzo en
    bloques y cuántas salvaguardas mueve. Con ``estados`` (v2) añade si está completada, en progreso o pendiente."""
    filas = ""
    for i, x in enumerate(lista):
        rs = [n for n in x.get("riesgos", []) if 0 < n <= len(riesgos_ref)]
        chips = "".join(f'<span class="d-chip-r"><span class="d-mono">R{n}</span>{esc(nombre_corto(riesgos_ref[n - 1]))}</span>' for n in rs)
        e = ESFUERZO.get(x.get("esfuerzo"), 0)
        bloques = "".join(f'<i class="{"d-on" if k <= e else ""}"></i>' for k in (1, 2, 3))
        qw = x.get("tipo") == "quick_win"
        sv = x.get("salvaguardas", [])
        est = ""
        if estados is not None:
            s = estados[i] if i < len(estados) else {}
            clave = s.get("estado", "pendiente")
            est = (f'<td><span class="d-estado-ini d-{esc(clave)}" title="{esc(s.get("explicacion"))}">'
                   f'{ESTADO_INICIATIVA.get(clave, "Pendiente")}</span></td>')
        filas += (f'<tr class="d-vinculo" data-riesgos="{" ".join(f"{grupo}{n}" for n in rs)}" data-abre="i-{grupo}{i + 1}" '
                  f'tabindex="0" role="button" aria-label="Ver detalle de la iniciativa {i + 1}">'
                  f'<td class="d-prio">{x.get("prioridad", i + 1)}</td>'
                  f'<td><div class="d-ini">{esc(x.get("titulo"))}<small>{esc(x.get("beneficio"))}</small></div></td>'
                  f'<td><div class="d-chips">{chips}</div></td>'
                  f'<td><span class="d-tipo {"d-qw" if qw else "d-pr"}">{"Quick win" if qw else "Proyecto"}</span></td>'
                  f'<td><span class="d-plazo">{_plazo(x)}</span></td>'
                  f'<td><div class="d-esfuerzo">{bloques}</div><div class="d-esf-txt">{esc((x.get("esfuerzo") or "").capitalize())}</div></td>'
                  f'<td class="d-mono" title="{esc(", ".join(sv))}">{len(sv)}</td>{est}</tr>')
    extra = "<th>Estado</th>" if estados is not None else ""
    return (f'<div class="d-tarjeta d-roadmap"><table class="d-rm"><thead><tr><th>#</th><th>Iniciativa</th><th>Reduce</th>'
            f'<th>Tipo</th><th>Plazo</th><th>Esfuerzo</th><th>Salvaguardas</th>{extra}</tr></thead><tbody>{filas}</tbody></table></div>')


# ---------------------------------------------------------------------------------------- matriz
def _evidencia_visor(clave: str, s, e: dict, r: Resultado) -> str:
    """Datos ocultos que el script del visor lee al abrir la evidencia ``clave`` (sin HTML: solo atributos)."""
    rects = ";".join(",".join(f"{v:.4f}" for v in r) for r in e.get("rects") or [])
    return (f'<div data-evid="{clave}" data-doc="{esc(e["doc"])}" data-pagina="{e["pagina"]}" data-total="{e["total"]}" '
            f'data-modo="{e["modo"]}" data-img="{esc(e.get("img", ""))}" data-rects="{rects}" data-sid="{s.id}" '
            f'data-titulo="{esc(s.titulo)}" data-estado="{ETIQUETA_CORTA[r.estado]}" data-just="{esc(r.justificacion)}" data-cita="{esc(e["cita"])}" data-texto="{esc(e.get("texto", ""))}"></div>')


def matriz(version, documentos: dict, titulo: str, sub: str, id_: str, resaltar: set[str] = frozenset(),
           abierta: bool = False, evidencias: dict | None = None) -> str:
    """Matriz de las 56 salvaguardas plegada, con filtros por estado (el filtro lo aplica el CSS con data-filtro).
    Con ``evidencias`` (de ``visor.evidencias``), la evidencia es un botón que abre el visor con la cita resaltada."""
    ind = version.indicadores()
    evidencias = evidencias or {}
    filas, datos_visor = "", ""
    for c in catalogo().controles:
        for s in c.ig1:
            r = version.matriz[s.id]
            aplic = (f'<span class="d-aplic">{ETIQUETA_APLICABILIDAD[r.aplicabilidad]}</span>'
                     if r.aplicabilidad != "aplica" else "")
            cita = f'<span class="d-cita">“{esc(r.cita)}”</span>' if r.cita else ""
            obs = f'<span class="d-obs">{esc(r.observaciones)}</span>' if r.observaciones else ""
            if s.id in evidencias:
                clave = f"{id_}:{s.id}"
                datos_visor += _evidencia_visor(clave, s, evidencias[s.id], r)
                ev = (f'<button type="button" class="d-pag d-ev" data-ev="{clave}" aria-label="Ver la evidencia de {s.id} '
                      f'en el documento">{esc(r.evidencia(documentos))}<i aria-hidden="true"></i></button>')
            elif r.fuente:
                ev = f'<span class="d-pag">{esc(r.evidencia(documentos))}</span>'
            else:
                ev = '<span class="d-sec-sub">—</span>'
            filas += (f'<tr data-e="{r.estado}" class="{"d-cambio" if s.id in resaltar else ""}">'
                      f'<td class="d-sid d-mono">{s.id}</td>'
                      f'<td class="d-sal">{esc(s.titulo)}<small>{esc(c.nombre)}</small></td>'
                      f'<td><span class="d-est">{_m(r.estado)}{ETIQUETA_CORTA[r.estado]}</span>{aplic}</td>'
                      f'<td>{esc(r.justificacion)}{cita}{obs}</td><td>{ev}</td></tr>')
    filtros = (f'<button type="button" class="d-filtro" aria-pressed="true" data-filtro="">Todas <b>{ind["total"]}</b></button>'
               + "".join(f'<button type="button" class="d-filtro" aria-pressed="false" data-filtro="{e}">{_m(e)}{ETIQUETA_CORTA[e]} '
                         f'<b>{ind[e]}</b></button>' for e in ESTADOS if ind[e]))
    return (f'<details{" open" if abierta else ""} class="d-tarjeta d-matriz d-det" id="d-{id_}" data-seccion="{id_}" data-filtro="" style="margin-top:40px;scroll-margin-top:80px">'
            f'<summary><div class="d-sec-cab"><h2>{esc(titulo)}</h2><span class="d-sec-sub">{esc(sub)}</span></div>'
            f'<span class="d-chev"></span></summary><div class="d-filtros">{filtros}</div>'
            f'<div class="d-mx-marco"><table class="d-mx"><thead><tr><th>ID</th><th>Salvaguarda</th><th>Estado</th>'
            f'<th>Justificación, cita y observaciones</th><th>Evidencia</th></tr></thead><tbody>{filas}</tbody></table></div>'
            f'<div class="d-evs" hidden>{datos_visor}</div></details>')


# ------------------------------------------------------------------------------------ pendientes
def pendientes(res: dict, ind: dict) -> str:
    faltante = "".join(f"<li>{esc(x)}</li>" for x in res.get("informacion_faltante") or []) or "<li>Nada relevante.</li>"
    razones = f'<li><b>{ind["no_verificado"]}</b><span>salvaguardas sin evidencia documental (No verificado).</span></li>'
    if ind["no_aplicable"]:
        razones += (f'<li><b>{ind["no_aplicable"]}</b><span>salvaguarda{"s" if ind["no_aplicable"] != 1 else ""} '
                    'marcada No aplicable; el auditor debe confirmarlo.</span></li>')
    texto = res.get("resultados_preliminares") or ""
    largo = (f'<p class="d-largo" style="margin-top:4px">{esc(texto)}</p>'
             '<button type="button" class="d-leer" aria-expanded="false">Leer más ▾</button>' if texto else "")
    return (f'<div class="d-dos"><div class="d-tarjeta"><h3>Información que falta <span>· {ind["no_verificado"]} salvaguardas sin evidencia</span></h3>'
            f'<ul class="d-faltante">{faltante}</ul></div>'
            f'<div class="d-tarjeta"><h3>Por qué es preliminar</h3><ul class="d-razones">{razones}</ul><div>{largo}</div>'
            f'<div class="d-nota">El reporte descargable (PDF y HTML) conserva la redacción completa de cada sección.</div></div></div>')


# -------------------------------------------------------------------------------- barra lateral
def marca_lateral(nombre_agente: str, organizacion: str = "") -> str:
    return f'<div class="d-lado-marca">{esc(nombre_agente)}' + (f"<small>{esc(organizacion)}</small>" if organizacion else "") + "</div>"


def indice(items: list[tuple[str, str, int | None]]) -> str:
    """Índice de secciones del reporte; el script marca la sección visible (aria-current)."""
    enlaces = "".join(f'<a href="#d-{i}" aria-current="{"true" if n == 0 else "false"}">{esc(t)}'
                      + (f'<span class="d-mono">{c}</span>' if c is not None else "") + "</a>"
                      for n, (i, t, c) in enumerate(items))
    return f'<nav class="d-indice" aria-label="Secciones del reporte"><div class="d-indice-titulo">En este reporte</div>{enlaces}</nav>'


def estado_lateral(ind: dict) -> str:
    """Resumen compacto para las etapas que no son reporte (contexto, evaluación, validación del PDF 2)."""
    def pct(v):
        return f'{v:.1f}<small>%</small>' if v is not None else "—"
    conteos = "".join(f'<li>{_m(e)}{ETIQUETA_CORTA[e]}<b>{ind[e]}</b></li>' for e in ESTADOS)
    return (f'<div class="d-lado-estado"><div class="d-lado-cifras"><div><b>{pct(ind["implementacion"])}</b><span>Implementación</span></div>'
            f'<div><b>{pct(ind["cobertura"])}</b><span>Cobertura</span></div></div>'
            f'{_apilada(ind)}<ul class="d-lado-conteos">{conteos}</ul></div>')


# ------------------------------------------------------------------------------- panel lateral
SEV_ESTADO = {"alta": "no_implementado", "media": "parcial", "baja": "implementado"}


def _enlace(destino: str, numero: int, texto: str, extra: str = "") -> str:
    return (f'<button type="button" data-abre="{destino}"><span class="d-mono">{numero}</span>'
            f'<span>{esc(texto)}' + (f'<br><small>{esc(extra)}</small>' if extra else "") + '</span><i aria-hidden="true">›</i></button>')


def fichas(riesgos: list[dict], iniciativas: list[dict], grupo: str, matriz: dict[str, Resultado], tecnica: bool,
           aportes: list | None = None, situacion: list[dict] | None = None, estados: list[dict] | None = None) -> str:
    """Contenido oculto del panel lateral: una ficha por riesgo (``r-<grupo><n>``) y por iniciativa (``i-<grupo><n>``).
    El script la copia al panel al hacer clic. La vista ejecutiva no lleva salvaguardas ni ids; la técnica, sí."""
    medida = "salvaguarda" if tecnica else "medida"
    salida = ""
    for n, r in enumerate(riesgos, 1):
        sev = severidad_de(r.get("probabilidad"), r.get("impacto")) or r.get("severidad")
        meta = (f'<span>{_m(SEV_ESTADO[sev])}Severidad {sev}</span>' if sev in SEV_ESTADO else "")
        cuerpo = f'<h3>Qué puede pasar</h3><p>{esc(r.get("consecuencia_negocio") or r.get("consecuencia"))}</p>'
        if r.get("probabilidad") and r.get("impacto"):
            cuerpo += ('<h3>Probabilidad e impacto</h3><div class="d-ficha-escalas">'
                       f'<div class="d-ficha-escala"><span>Probabilidad</span><b>{r["probabilidad"]}<small> de 5</small></b>'
                       f'<p>{esc(r.get("justificacion_probabilidad"))}</p></div>'
                       f'<div class="d-ficha-escala"><span>Impacto</span><b>{r["impacto"]}<small> de 5</small></b>'
                       f'<p>{esc(r.get("justificacion_impacto"))}</p></div></div>')
        else:
            cuerpo += ('<h3>Probabilidad e impacto</h3><p class="d-ficha-sub">Esta evaluación se generó antes de calificarlos por '
                       'separado.</p>')
        if situacion is not None and n <= len(situacion):
            st_ = situacion[n - 1]
            cuerpo += (f'<h3>Tras las mejoras</h3><p>{SITUACION_RIESGO.get(st_.get("situacion"), "")}'
                       + (f' · residual {esc(st_.get("severidad_residual"))}' if st_.get("severidad_residual") else "")
                       + "</p>" + (f'<p style="margin-top:6px">{esc(st_.get("explicacion"))}</p>' if st_.get("explicacion") else ""))
        reducen = [(j, x) for j, x in enumerate(iniciativas, 1) if n in (x.get("riesgos") or [])]
        enlaces = "".join(_enlace(f"i-{grupo}{j}", j, x.get("titulo"), HORIZONTE[horizonte_de(x)[0]]) for j, x in reducen)
        cuerpo += (f'<h3>Iniciativas que lo reducen</h3>'
                   + (f'<div class="d-ficha-enlaces">{enlaces}</div>' if enlaces else '<p class="d-ficha-sub">Ninguna iniciativa del plan lo reduce.</p>'))
        if tecnica:
            sv = r.get("salvaguardas", [])
            for titulo_, campo in (("Descripción", "descripcion"), ("Deficiencia", "deficiencia"),
                                   ("Consecuencia técnica", "consecuencia"), ("Severidad", "justificacion")):
                if r.get(campo) and not (campo == "consecuencia" and not r.get("consecuencia_negocio")):
                    cuerpo += f'<h3>{titulo_}</h3><p>{esc(r.get(campo))}</p>'
            cuerpo += (f'<h3>Salvaguardas que lo sostienen · {len(sv)}</h3>'
                       f'<div class="d-lista-sv">{"".join(_sv(x, matriz) for x in sv)}</div>')
        salida += (f'<div class="d-ficha" data-ficha="r-{grupo}{n}"><p class="d-ficha-tipo">Riesgo {n}</p>'
                   f'<h2>{esc(nombre_corto(r))}</h2><p class="d-ficha-sub">{esc(r.get("titulo"))}</p>'
                   f'<div class="d-ficha-meta">{meta}</div>{cuerpo}</div>')
    for j, x in enumerate(iniciativas, 1):
        h, estimado = horizonte_de(x)
        meta = (f'<span>{HORIZONTE[h]}{" (plazo estimado)" if estimado else ""}</span>'
                f'<span>Esfuerzo {esc(x.get("esfuerzo") or "—")}</span>'
                f'<span>{"Quick win" if x.get("tipo") == "quick_win" else "Proyecto"}</span>')
        if estados is not None and j <= len(estados):
            meta += f'<span>{ESTADO_INICIATIVA.get(estados[j - 1].get("estado"), "Pendiente")}</span>'
        cuerpo = f'<p style="margin-top:14px">{esc(x.get("descripcion") or x.get("beneficio"))}</p>'
        if x.get("beneficio") and x.get("descripcion"):
            cuerpo += f'<h3>Beneficio esperado</h3><p>{esc(x.get("beneficio"))}</p>'
        rs = [n for n in x.get("riesgos", []) if 0 < n <= len(riesgos)]
        enlaces = "".join(_enlace(f"r-{grupo}{n}", n, nombre_corto(riesgos[n - 1]), riesgos[n - 1].get("titulo")) for n in rs)
        cuerpo += (f'<h3>Riesgos que reduce</h3>'
                   + (f'<div class="d-ficha-enlaces">{enlaces}</div>' if enlaces else '<p class="d-ficha-sub">No apunta a ninguno de los cinco riesgos.</p>'))
        aporte = aportes[j - 1] if aportes and j <= len(aportes) else None
        if aporte is not None:
            cuerpo += (f'<h3>Aporte a la madurez</h3><div class="d-ficha-aporte"><b>+{aporte:.1f}</b><span class="d-ficha-sub">'
                       f'puntos · estimación</span></div><p class="d-ficha-sub" style="margin-top:4px">Si sus {medida}s quedan '
                       f'implementadas y todo lo demás sigue igual.</p>')
        if tecnica:
            sv = x.get("salvaguardas", [])
            cuerpo += (f'<h3>Salvaguardas que cierra · {len(sv)}</h3>'
                       f'<div class="d-lista-sv">{"".join(_sv(s_, matriz) for s_ in sv)}</div>')
        salida += (f'<div class="d-ficha" data-ficha="i-{grupo}{j}"><p class="d-ficha-tipo">Iniciativa {j}</p>'
                   f'<h2>{esc(x.get("titulo"))}</h2><div class="d-ficha-meta">{meta}</div>{cuerpo}</div>')
    return f'<div class="d-fichas" aria-hidden="true">{salida}</div>'


# ---------------------------------------------------------------------------------------- script
def script() -> str:
    """Interacciones del dashboard con delegación de eventos: se instala una vez y sirve a todo lo que Streamlit
    vuelva a dibujar. Respeta prefers-reduced-motion (sin cuenta ni barra animadas) y las pestañas ocultas."""
    return """<script>(() => { if (window.__ctPanel) return; window.__ctPanel = true;
const d = document;
const quieto = () => matchMedia('(prefers-reduced-motion: reduce)').matches || d.visibilityState !== 'visible';
let fijado = null;
const enfocar = e => { if (e) d.body.dataset.foco = e; else delete d.body.dataset.foco; };
const marcarLeyenda = () => d.querySelectorAll('.d-leyenda [data-foco]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.foco === fijado)));
// Filtro por estado: oculta las filas sin ese estado (controles y matriz) y muestra «Mostrando N … · Quitar filtro».
const NOMBRE_T = {implementado: 'Implementado', parcial: 'Parcial', no_implementado: 'No implementado', no_verificado: 'No verificado', no_aplicable: 'No aplicable'};
const NOMBRE_E = {...NOMBRE_T, no_verificado: 'Sin evidencia', no_aplicable: 'No aplica'};
let aviso = null;
const filtrar = e => {
  fijado = e; marcarLeyenda(); enfocar(e);
  if (e) d.body.dataset.filtro = e; else delete d.body.dataset.filtro;
  d.querySelectorAll('.d-matriz').forEach(m => { m.dataset.filtro = e || '';
    m.querySelectorAll('.d-filtro').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.filtro === (e || '')))); });
  if (!e) { if (aviso) { aviso.remove(); aviso = null; } return; }
  const fuente = d.querySelector('[data-conteos]');
  const n = fuente ? +((fuente.dataset.conteos.match(new RegExp('(^| )' + e + ':(\\\\d+)')) || [])[2] || 0) : 0;
  const nombre = (d.querySelector('.e-vista') ? NOMBRE_E : NOMBRE_T)[e];
  const medida = d.querySelector('.e-vista') ? (n === 1 ? 'medida' : 'medidas') : (n === 1 ? 'salvaguarda' : 'salvaguardas');
  if (!aviso) { aviso = d.createElement('div'); aviso.className = 'd-filtro-aviso'; aviso.setAttribute('role', 'status'); d.body.appendChild(aviso); }
  aviso.innerHTML = '';
  const m = d.createElement('span'); m.className = 'd-m d-m-' + e; m.dataset.e = e; aviso.appendChild(m);
  const t = d.createElement('span'); t.append('Mostrando '); const b = d.createElement('b'); b.textContent = n; t.append(b, ' ' + medida + ' · ' + nombre); aviso.appendChild(t);
  const q = d.createElement('button'); q.type = 'button'; q.textContent = 'Quitar filtro'; q.addEventListener('click', () => filtrar(null)); aviso.appendChild(q);
};
// Panel lateral: copia la ficha oculta [data-ficha] al panel. Se cierra con Esc, con la X o con clic fuera; el foco
// queda atrapado dentro y vuelve al elemento que lo abrió.
let cajon = null, origen = null;
const cerrar = () => {
  if (!cajon) return; const c = cajon; cajon = null; c.classList.remove('d-cajon-abierto');
  setTimeout(() => c.remove(), quieto() ? 0 : 230);
  if (origen && d.contains(origen)) origen.focus({preventScroll: true}); origen = null;
};
const abrir = (clave, desde) => {
  const f = d.querySelector('[data-ficha="' + clave + '"]'); if (!f) return;
  if (visor) cerrarVisor(false);
  if (!cajon) {
    origen = desde || d.activeElement;
    // Sin HTML en cadenas: st.html descarta el script si lleva etiquetas dentro.
    const el = (tag, clase, attrs) => { const x = d.createElement(tag); x.className = clase;
      Object.entries(attrs || {}).forEach(([k, v]) => x.setAttribute(k, v)); return x; };
    cajon = el('div', 'd-cajon-raiz');
    const fondo = el('div', 'd-cajon-fondo');
    const panel = el('aside', 'd-cajon', {role: 'dialog', 'aria-modal': 'true', tabindex: '-1'});
    const x = el('button', 'd-cajon-cerrar', {type: 'button', 'aria-label': 'Cerrar'}); x.textContent = '×';
    panel.append(x, el('div', 'd-cajon-cuerpo')); cajon.append(fondo, panel); d.body.appendChild(cajon);
    fondo.addEventListener('click', cerrar); x.addEventListener('click', cerrar);
    requestAnimationFrame(() => requestAnimationFrame(() => cajon && cajon.classList.add('d-cajon-abierto')));
  }
  const cuerpo = cajon.querySelector('.d-cajon-cuerpo'); cuerpo.innerHTML = f.innerHTML;
  const panel = cajon.querySelector('.d-cajon'); const h = cuerpo.querySelector('h2');
  if (h) { h.id = 'd-cajon-titulo'; panel.setAttribute('aria-labelledby', 'd-cajon-titulo'); }
  panel.scrollTop = 0; cajon.querySelector('.d-cajon-cerrar').focus({preventScroll: true});
};
// Visor de evidencia: la página del PDF a la derecha con la cita resaltada (rectángulos de visor.py).
const MODO_VISOR = {exacta: 'Cita resaltada en la página', fragmentos: 'Se resaltaron los fragmentos de la cita que aparecen en la página',
  no_encontrada: 'No se encontró la cita exacta; se muestra la página citada', texto: 'Documento sin PDF: se muestra el texto extraído de la página'};
const nuevo = (tag, clase, attrs) => { const x = d.createElement(tag); if (clase) x.className = clase;
  Object.entries(attrs || {}).forEach(([k, v]) => x.setAttribute(k, v)); return x; };
let visor = null, evClave = null;
const botonEv = c => c && d.querySelector('.d-ev[data-ev="' + c + '"]');
const visibles = b => { const m = b && b.closest('.d-matriz'); return m ? [...m.querySelectorAll('.d-ev[data-ev]')].filter(x => x.offsetParent !== null) : []; };
const marcarFila = b => { d.querySelectorAll('tr.d-ev-actual').forEach(t => t.classList.remove('d-ev-actual')); if (b) b.closest('tr').classList.add('d-ev-actual'); };
const cerrarVisor = (devolver = true) => {
  if (!visor) return; const v = visor; visor = null; v.classList.remove('d-visor-abierto'); d.body.classList.remove('d-con-visor');
  setTimeout(() => v.remove(), quieto() ? 0 : 230);
  const b = botonEv(evClave); marcarFila(null); evClave = null; if (devolver && b) b.focus({preventScroll: true});
};
const moverVisor = paso => { const b = botonEv(evClave); const l = visibles(b); const i = l.indexOf(b);
  if (i >= 0 && l[i + paso]) abrirVisor(l[i + paso], true); };
const abrirVisor = (b, navegando) => {
  const info = d.querySelector('[data-evid="' + b.dataset.ev + '"]'); if (!info) return;
  if (cajon) cerrar();
  const g = info.dataset;
  if (!visor) {
    visor = nuevo('aside', 'd-visor', {role: 'dialog', 'aria-modal': 'false', 'aria-labelledby': 'd-visor-titulo', tabindex: '-1'});
    const cab = nuevo('div', 'd-visor-cab');
    cab.append(nuevo('p', 'd-visor-doc'), nuevo('h2', '', {id: 'd-visor-titulo'}), nuevo('p', 'd-visor-just'), nuevo('p', 'd-visor-estado', {role: 'status'}), nuevo('blockquote', 'd-visor-cita'));
    const x = nuevo('button', 'd-visor-cerrar', {type: 'button', 'aria-label': 'Cerrar el visor'}); x.textContent = '×'; cab.append(x);
    const pie = nuevo('div', 'd-visor-pie');
    const ant = nuevo('button', 'd-visor-ant', {type: 'button'}); ant.textContent = '‹ Anterior';
    const sig = nuevo('button', 'd-visor-sig', {type: 'button'}); sig.textContent = 'Siguiente evidencia ›';
    pie.append(ant, nuevo('span'), sig);
    visor.append(cab, nuevo('div', 'd-visor-hoja'), pie); d.body.appendChild(visor);
    x.addEventListener('click', () => cerrarVisor()); ant.addEventListener('click', () => moverVisor(-1)); sig.addEventListener('click', () => moverVisor(1));
    requestAnimationFrame(() => requestAnimationFrame(() => { if (visor) { visor.classList.add('d-visor-abierto'); d.body.classList.add('d-con-visor'); } }));
  }
  evClave = b.dataset.ev; marcarFila(b);
  // La matriz se reacomoda al dividirse la pantalla: se centra la fila cuando termina la transición.
  setTimeout(() => { if (d.contains(b)) b.closest('tr').scrollIntoView({block: 'center', behavior: quieto() ? 'auto' : 'smooth'}); }, navegando ? 0 : 260);
  visor.querySelector('.d-visor-doc').textContent = g.doc + ' · página ' + g.pagina + ' de ' + g.total;
  const h = visor.querySelector('h2'); h.textContent = ''; const id = d.createElement('b'); id.textContent = g.sid; h.append(id, ' ', g.titulo);
  const j = visor.querySelector('.d-visor-just'); j.textContent = ''; const je = d.createElement('b'); je.textContent = g.estado + '. ';
  j.append(je, g.just || ''); j.title = g.just || '';
  const est = visor.querySelector('.d-visor-estado'); est.dataset.modo = g.modo; est.textContent = MODO_VISOR[g.modo] || '';
  visor.querySelector('.d-visor-cita').textContent = '“' + g.cita + '”';
  const hoja = visor.querySelector('.d-visor-hoja'); hoja.innerHTML = ''; hoja.scrollTop = 0;
  if (g.modo === 'texto') {
    const t = nuevo('div', 'd-visor-texto'); const txt = g.texto || ''; const cita = (g.cita || '').trim();
    const i = cita ? txt.toLowerCase().indexOf(cita.toLowerCase()) : -1;
    if (i >= 0) { const m = d.createElement('mark'); m.textContent = txt.slice(i, i + cita.length); t.append(txt.slice(0, i), m, txt.slice(i + cita.length));
      est.textContent = MODO_VISOR.texto + '; la cita está marcada'; }
    else t.textContent = txt;
    hoja.append(t); const m = t.querySelector('mark'); if (m) requestAnimationFrame(() => { hoja.scrollTop = Math.max(0, m.offsetTop - 80); });
  } else {
    const pag = nuevo('div', 'd-visor-pagina', {role: 'button', tabindex: '0', 'aria-pressed': 'false', title: 'Clic para ampliar o reducir la página'}); const img = nuevo('img', '', {alt: 'Página ' + g.pagina + ' de ' + g.doc, decoding: 'async'});
    pag.append(img);
    const marcas = (g.rects || '').split(';').filter(Boolean).map(r => { const [x0, y0, x1, y1] = r.split(',').map(Number);
      const m = nuevo('div', 'd-visor-marca'); Object.assign(m.style, {left: x0 * 100 + '%', top: y0 * 100 + '%', width: (x1 - x0) * 100 + '%', height: (y1 - y0) * 100 + '%'});
      pag.append(m); return y0; });
    const centrar = () => { if (marcas.length) hoja.scrollTop = Math.max(0, Math.min(...marcas) * img.clientHeight - 90); };
    img.addEventListener('load', centrar);
    const ampliar = () => { const z = pag.classList.toggle('d-visor-zoom'); pag.setAttribute('aria-pressed', String(z)); centrar();
      const xs = (g.rects || '').split(';').filter(Boolean).map(r => +r.split(',')[0]); hoja.scrollLeft = z && xs.length ? Math.max(0, Math.min(...xs) * pag.clientWidth - 40) : 0; };
    pag.addEventListener('click', ampliar);
    pag.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); ampliar(); } });
    img.src = g.img; hoja.append(pag);
  }
  const l = visibles(b), i = l.indexOf(b);
  visor.querySelector('.d-visor-pie span').textContent = (i + 1) + ' de ' + l.length;
  visor.querySelector('.d-visor-ant').disabled = i <= 0; visor.querySelector('.d-visor-sig').disabled = i >= l.length - 1;
  if (!navegando) visor.querySelector('.d-visor-cerrar').focus({preventScroll: true});
};
d.addEventListener('keydown', ev => {
  if (ev.key === 'Escape') { if (cajon) { cerrar(); ev.preventDefault(); } else if (visor) { cerrarVisor(); ev.preventDefault(); } else if (fijado) filtrar(null); return; }
  if (cajon && ev.key === 'Tab') {
    const foc = [...cajon.querySelectorAll('button, [href], [tabindex]:not([tabindex="-1"])')];
    if (!foc.length) return; const pri = foc[0], ult = foc[foc.length - 1];
    if (ev.shiftKey && d.activeElement === pri) { ult.focus(); ev.preventDefault(); }
    else if (!ev.shiftKey && d.activeElement === ult) { pri.focus(); ev.preventDefault(); }
    else if (!cajon.contains(d.activeElement)) { pri.focus(); ev.preventDefault(); }
    return;
  }
  const a = ev.target.closest && ev.target.closest('[data-abre]');
  if (a && a.tagName !== 'BUTTON' && a.tagName !== 'DETAILS' && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); abrir(a.dataset.abre, a); }
});
const vincular = (claves, sola) => {
  d.body.classList.toggle('d-con-vinculo', !!claves);
  d.querySelectorAll('[data-riesgo]').forEach(e => e.classList.toggle('d-activo', !!claves && claves.includes(e.dataset.riesgo)));
  d.querySelectorAll('[data-riesgos]').forEach(e => e.classList.toggle('d-activo', !!claves &&
    (sola ? e === sola : e.dataset.riesgos.split(' ').some(r => claves.includes(r)))));
};
d.addEventListener('mouseover', ev => {
  const f = ev.target.closest('.d-leyenda [data-foco]'); if (f && !fijado) enfocar(f.dataset.foco);
  const r = ev.target.closest('[data-riesgo]'); if (r) { vincular([r.dataset.riesgo]); return; }
  const i = ev.target.closest('[data-riesgos]'); if (i && i.dataset.riesgos) vincular(i.dataset.riesgos.split(' '), i);
});
d.addEventListener('mouseout', ev => {
  const f = ev.target.closest('.d-leyenda [data-foco]'); if (f && !f.contains(ev.relatedTarget) && !fijado) enfocar(null);
  const v = ev.target.closest('[data-riesgo],[data-riesgos]'); if (v && !v.contains(ev.relatedTarget)) vincular(null);
});
d.addEventListener('focusin', ev => { const f = ev.target.closest('.d-leyenda [data-foco]'); if (f && !fijado) enfocar(f.dataset.foco); });
d.addEventListener('focusout', ev => { const f = ev.target.closest('.d-leyenda [data-foco]'); if (f && !fijado) enfocar(null); });
d.addEventListener('click', ev => {
  const evb = ev.target.closest('.d-ev[data-ev]');
  if (evb) { ev.preventDefault(); abrirVisor(evb); return; }
  const f = ev.target.closest('.d-leyenda [data-foco]');
  if (f) { filtrar(fijado === f.dataset.foco ? null : f.dataset.foco); return; }
  const sg = ev.target.closest('.d-principal .d-s[data-e], .e-pila .d-s[data-e], .d-segs .d-s[data-e]');
  if (sg) { ev.preventDefault(); filtrar(fijado === sg.dataset.e ? null : sg.dataset.e); return; }
  const ab = ev.target.closest('[data-abre]');
  if (ab) {
    // En un details (riesgos de la vista técnica) solo el resumen abre el panel; el contenido no reacciona.
    if (ab.tagName === 'DETAILS' && !ev.target.closest('summary')) return;
    ev.preventDefault(); abrir(ab.dataset.abre, ab.tagName === 'DETAILS' ? ab.querySelector('summary') : ab); return;
  }
  const l = ev.target.closest('.d-leer');
  if (l) { const t = l.previousElementSibling; const ab = t.classList.toggle('d-abierto');
    l.textContent = ab ? 'Leer menos ▴' : 'Leer más ▾'; l.setAttribute('aria-expanded', String(ab)); return; }
  const fl = ev.target.closest('.d-filtro');
  if (fl) { const m = fl.closest('.d-matriz'); m.dataset.filtro = fl.dataset.filtro;
    m.querySelectorAll('.d-filtro').forEach(x => x.setAttribute('aria-pressed', String(x === fl))); return; }
  const a = ev.target.closest('.d-indice a');
  if (a) { ev.preventDefault(); const s = d.getElementById(a.getAttribute('href').slice(1));
    if (s) s.scrollIntoView({behavior: quieto() ? 'auto' : 'smooth', block: 'start'}); }
});
const espiar = () => {
  const enlaces = [...d.querySelectorAll('.d-indice a')]; if (!enlaces.length) return;
  let actual = enlaces[0]; const lim = innerHeight * 0.35;
  enlaces.forEach(a => { const s = d.getElementById(a.getAttribute('href').slice(1)); if (s && s.getBoundingClientRect().top <= lim) actual = a; });
  enlaces.forEach(a => a.setAttribute('aria-current', String(a === actual)));
};
let pendiente = false;
d.addEventListener('scroll', () => { if (pendiente) return; pendiente = true; requestAnimationFrame(() => { pendiente = false; espiar(); }); }, true);
const entrar = () => {
  d.querySelectorAll('[data-cuenta]:not([data-listo])').forEach(el => {
    el.dataset.listo = '1'; if (quieto()) return;
    const fin = +el.dataset.cuenta, dec = +(el.dataset.dec || 0); let t0 = null;
    const paso = t => { t0 ??= t; const k = Math.min(1, (t - t0) / 700);
      el.textContent = (fin * (1 - Math.pow(1 - k, 3))).toFixed(dec); if (k < 1) requestAnimationFrame(paso); };
    el.textContent = (0).toFixed(dec); requestAnimationFrame(paso);
    setTimeout(() => { el.textContent = fin.toFixed(dec); }, 900);
  });
  d.querySelectorAll('.d-crece:not([data-listo])').forEach(el => {
    el.dataset.listo = '1'; if (quieto()) return;
    el.classList.add('d-cargando'); el.querySelectorAll('.d-principal .d-s').forEach((s, i) => { s.style.transitionDelay = (i * 90) + 'ms'; });
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.remove('d-cargando')));
    setTimeout(() => el.classList.remove('d-cargando'), 900);
  });
};
const revisar = () => {
  entrar(); espiar();
  if (!d.querySelector('.d-leyenda') && (fijado || d.body.dataset.foco)) filtrar(null);
  if (cajon && !d.querySelector('.d-fichas')) cerrar();
  if (visor) { const b = botonEv(evClave); if (!b) cerrarVisor(false); else if (!b.closest('tr').classList.contains('d-ev-actual')) marcarFila(b); }
  if (!d.querySelector('[data-riesgo]')) d.body.classList.remove('d-con-vinculo');
};
new MutationObserver(revisar).observe(d.body, {childList: true, subtree: true});
revisar();
})();</script>"""
