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
from .state import ESTADOS, ETIQUETA_APLICABILIDAD, SITUACION_RIESGO, Resultado
from .ui import ETIQUETA_CORTA, ESTADO_INICIATIVA, esc

UNIDAD = 30          # px por salvaguarda en "Estado por control": la misma escala en todas las filas
TOP_BRECHAS = 5      # controles con mayores brechas que se abren para ver por qué
ESFUERZO = {"bajo": 1, "medio": 2, "alto": 3}

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

/* Marcas de estado: una sola codificación (lleno, a medias, tachado, punteado, gris claro) */
.d-m { width: 12px; height: 12px; border-radius: 2px; display: inline-block; flex: none; box-sizing: border-box; }
.d-m-implementado { background: var(--st-implementado); }
.d-m-parcial { border: 1.5px solid var(--st-parcial); background: linear-gradient(to right, var(--st-parcial) 50%, transparent 50%); }
.d-m-no_implementado { border: 1.5px solid var(--st-no_implementado);
  background: linear-gradient(135deg, transparent 41%, var(--st-no_implementado) 41% 59%, transparent 59%); }
.d-m-no_verificado { border: 1.5px dashed var(--st-no_verificado); }
.d-m-no_aplicable { background: var(--st-no_aplicable); }
.d-s { display: block; height: 100%; border-radius: 3px; box-sizing: border-box; }
.d-s[data-e="no_verificado"] { background: transparent !important; border: 1.5px dashed var(--st-no_verificado); }

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
.d-segs .d-s[data-e="no_verificado"], .d-segs .d-s[data-e="no_aplicable"] { color: var(--ink-2); }
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
.d-riesgo > summary { display: grid; grid-template-columns: 22px minmax(0, 1fr) 64px 220px 28px; gap: 14px; align-items: center;
  padding: 12px 12px 12px 18px; transition: background-color 80ms; }
.d-riesgos.d-con-sit .d-riesgo > summary { grid-template-columns: 22px minmax(0, 1fr) 64px 150px 190px 28px; }
.d-riesgo + .d-riesgo { border-top: 1px solid var(--rule); }
.d-riesgo > summary:hover { background: color-mix(in oklch, var(--sunken) 55%, transparent); }
.d-riesgo[open] { background: var(--sunken); }
.d-rnum { font-size: 13px; font-weight: 600; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.d-rtitulo { font-size: 14px; color: var(--ink); font-weight: 500; line-height: 20px; min-width: 0; }
.d-rtitulo small { display: block; font-size: 12px; color: var(--ink-3); font-weight: 400; line-height: 18px; }
.d-sev { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; color: var(--ink); justify-self: start;
  display: inline-flex; gap: 6px; align-items: center; background: var(--sunken); white-space: nowrap; }
.d-sev::before { content: ""; width: 3px; height: 11px; border-radius: 1px; background: var(--ink-3); }
.d-sev.d-alta { background: var(--tint-no_implementado); } .d-sev.d-alta::before { background: var(--st-no_implementado); }
.d-sev.d-media { background: var(--tint-parcial); } .d-sev.d-media::before { background: var(--st-parcial); }
.d-sev.d-baja { background: var(--tint-implementado); } .d-sev.d-baja::before { background: var(--st-implementado); }
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
  .d-riesgo .d-sev, .d-riesgo .d-rbarra, .d-riesgo .d-sit { grid-column: 2; }
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
    leyenda = "".join(f'<button type="button" data-foco="{e}" aria-pressed="false">{_m(e)}{ETIQUETA_CORTA[e]} <b>{ind[e]}</b></button>'
                      for e in ESTADOS)
    return (f'<section class="d-tarjeta d-crece" id="d-resumen" data-seccion="resumen" aria-label="Resumen" style="scroll-margin-top:80px">'
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
    largo = (f'<p class="d-largo">{esc(texto)}</p><button type="button" class="d-leer" aria-expanded="false">Leer más ▾</button>'
             if texto else "")
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
        cuerpo += (f'<details class="d-cd d-det"><summary>{fila}</summary><div class="d-cdet">'
                   f'{texto}<div class="d-lista-sv">{"".join(_sv(i, matriz) for i in ids)}</div></div></details>')
    return (f'<div class="d-tarjeta"><div class="d-ccab"><span>Control</span><span>Salvaguardas por estado · implementación</span>'
            f'<span></span></div>{cuerpo}</div>')


# --------------------------------------------------------------------------------------- riesgos
def _sev(s: str | None) -> str:
    s = s if s in ("alta", "media", "baja") else ""
    return f'<span class="d-sev d-{s}">{esc((s or "—").capitalize())}</span>'


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
        cuerpo += (f'<details class="d-riesgo d-det d-vinculo" data-riesgo="{grupo}{i}"><summary>'
                   f'<span class="d-rnum">{i}</span>'
                   f'<span class="d-rtitulo">{esc(r.get("titulo"))}<small>{esc(r.get("activo_proceso"))}</small></span>'
                   f'{_sev(r.get("severidad"))}{sit}'
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
        filas += (f'<tr class="d-vinculo" data-riesgos="{" ".join(f"{grupo}{n}" for n in rs)}">'
                  f'<td class="d-prio">{x.get("prioridad", i + 1)}</td>'
                  f'<td><div class="d-ini">{esc(x.get("titulo"))}<small>{esc(x.get("beneficio"))}</small></div></td>'
                  f'<td><div class="d-chips">{chips}</div></td>'
                  f'<td><span class="d-tipo {"d-qw" if qw else "d-pr"}">{"Quick win" if qw else "Proyecto"}</span></td>'
                  f'<td><div class="d-esfuerzo">{bloques}</div><div class="d-esf-txt">{esc((x.get("esfuerzo") or "").capitalize())}</div></td>'
                  f'<td class="d-mono" title="{esc(", ".join(sv))}">{len(sv)}</td>{est}</tr>')
    extra = "<th>Estado</th>" if estados is not None else ""
    return (f'<div class="d-tarjeta d-roadmap"><table class="d-rm"><thead><tr><th>#</th><th>Iniciativa</th><th>Reduce</th>'
            f'<th>Tipo</th><th>Esfuerzo</th><th>Salvaguardas</th>{extra}</tr></thead><tbody>{filas}</tbody></table></div>')


# ---------------------------------------------------------------------------------------- matriz
def matriz(version, documentos: dict, titulo: str, sub: str, id_: str, resaltar: set[str] = frozenset(),
           abierta: bool = False) -> str:
    """Matriz de las 56 salvaguardas plegada, con filtros por estado (el filtro lo aplica el CSS con data-filtro)."""
    ind = version.indicadores()
    filas = ""
    for c in catalogo().controles:
        for s in c.ig1:
            r = version.matriz[s.id]
            aplic = (f'<span class="d-aplic">{ETIQUETA_APLICABILIDAD[r.aplicabilidad]}</span>'
                     if r.aplicabilidad != "aplica" else "")
            cita = f'<span class="d-cita">“{esc(r.cita)}”</span>' if r.cita else ""
            obs = f'<span class="d-obs">{esc(r.observaciones)}</span>' if r.observaciones else ""
            ev = (f'<span class="d-pag">{esc(r.evidencia(documentos))}</span>' if r.fuente
                  else '<span class="d-sec-sub">—</span>')
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
            f'<th>Justificación, cita y observaciones</th><th>Evidencia</th></tr></thead><tbody>{filas}</tbody></table></div></details>')


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
  const f = ev.target.closest('.d-leyenda [data-foco]');
  if (f) { fijado = fijado === f.dataset.foco ? null : f.dataset.foco; marcarLeyenda(); enfocar(fijado); return; }
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
  if (!d.querySelector('.d-leyenda') && (fijado || d.body.dataset.foco)) { fijado = null; enfocar(null); }
  if (!d.querySelector('[data-riesgo]')) d.body.classList.remove('d-con-vinculo');
};
new MutationObserver(revisar).observe(d.body, {childList: true, subtree: true});
revisar();
})();</script>"""
