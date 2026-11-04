"""Capa visual: tokens CSS y piezas HTML para la app Streamlit.

Arquetipo "craft oscuro": neutros fríos de croma muy bajo, bordes de 1px,
un solo acento (verde azulado) y colores de estado con el mismo peso.
Momento firma: la matriz de postura + anillo de cobertura en la barra lateral.

Todo texto que viene del usuario o de Gemini pasa por ``esc()`` antes de
insertarse en HTML.
"""

from html import escape as _escape

from .controls import CONTROLES, CONTROLES_POR_ID

ETIQUETA = {"cubierto": "Cubierto", "parcial": "Parcial", "no_cubierto": "No cubierto", "desconocido": "Por confirmar"}
ORDEN_ESTADOS = ("cubierto", "parcial", "no_cubierto", "desconocido")


def esc(texto) -> str:
    return _escape(str(texto or ""), quote=True)


# --------------------------------------------------------------------------- CSS
CSS = """
<style>
:root {
  --hue-base: 255; --hue-accent: 175;
  --bg: oklch(0.155 0.006 var(--hue-base));
  --surface-1: oklch(0.185 0.007 var(--hue-base));
  --surface-2: oklch(0.215 0.008 var(--hue-base));
  --surface-3: oklch(0.245 0.009 var(--hue-base));
  --text-1: oklch(0.96 0.004 var(--hue-base));
  --text-2: oklch(0.74 0.008 var(--hue-base));
  --text-3: oklch(0.60 0.010 var(--hue-base));
  --border: oklch(1 0 0 / 0.08);
  --border-strong: oklch(1 0 0 / 0.15);
  --accent: oklch(0.78 0.13 var(--hue-accent));
  --accent-subtle: color-mix(in oklch, var(--accent) 14%, transparent);
  --accent-glow: color-mix(in oklch, var(--accent) 40%, transparent);
  --on-accent: oklch(0.18 0.03 var(--hue-accent));
  /* Estados: misma L y C, solo cambia el tono */
  --st-cubierto: oklch(0.74 0.15 155);
  --st-parcial: oklch(0.80 0.14 80);
  --st-no_cubierto: oklch(0.68 0.18 25);
  --st-desconocido: oklch(0.52 0.012 var(--hue-base));
  --highlight: inset 0 1px 0 oklch(1 0 0 / 0.05);
  --elev-1: 0 0 0 1px var(--border), var(--highlight);
  --elev-2: 0 0 0 1px var(--border), var(--highlight), 0 2px 4px oklch(0 0 0 / .2), 0 8px 24px oklch(0 0 0 / .25);
  --r-sm: 6px; --r-md: 10px; --r-lg: 16px; --r-full: 9999px;
  --mono: "Geist Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --spring-bouncy: linear(0, 0.1, 0.323, 0.577, 0.803, 0.97, 1.073, 1.119, 1.124, 1.105, 1.074, 1.042, 1.016, 0.998, 0.988, 0.984, 0.985, 0.988, 0.992, 0.996, 0.999, 1.001, 1.002, 1.002, 1);
}

/* ---------- Base de Streamlit ---------- */
.stApp { -webkit-font-smoothing: antialiased; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stMainBlockContainer"], [data-testid="stBottomBlockContainer"] {
  max-width: 980px; padding-left: clamp(16px, 4vw, 40px); padding-right: clamp(16px, 4vw, 40px);
}
[data-testid="stMainBlockContainer"] { padding-top: 40px; }
[data-testid="stSidebar"] { border-right: 1px solid var(--border); }
[data-testid="stSidebarContent"] { padding-top: 8px; }
h1, h2, h3 { text-wrap: balance; }
p { text-wrap: pretty; }

/* Chat */
[data-testid="stChatMessage"] { background: transparent; padding: 12px 0; gap: 14px; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li { color: var(--text-2); line-height: 1.65; max-width: 68ch; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong { color: var(--text-1); font-weight: 550; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"][aria-label*="user"] {
  background: var(--surface-1); box-shadow: var(--elev-1); border-radius: var(--r-lg); padding: 14px 18px; margin: 8px 0;
}
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"], [data-testid="stChatMessageAvatarCustom"] {
  background: var(--surface-2); box-shadow: 0 0 0 1px var(--border); border-radius: var(--r-sm); color: var(--text-2);
}
[data-testid="stChatInput"] { border-radius: var(--r-lg); transition: box-shadow 150ms var(--ease-out); }
/* Streamlit mide mal la altura inicial cuando solo hay placeholder */
[data-testid="stChatInput"] textarea:placeholder-shown { height: auto !important; }
[data-testid="stChatInput"]:focus-within { box-shadow: 0 0 0 1px var(--accent), 0 0 0 4px var(--accent-subtle); }
[data-testid="stBottom"] > div { background: linear-gradient(to top, var(--bg) 70%, transparent); }

/* Botones: hover instantáneo de entrada, salida suave, press con escala */
[data-testid^="stBaseButton"] {
  font-weight: 500; letter-spacing: -0.005em; transition: background-color 150ms var(--ease-out),
  border-color 150ms var(--ease-out), transform 100ms var(--ease-out), box-shadow 150ms var(--ease-out);
}
[data-testid^="stBaseButton"]:hover { transition-duration: 0ms, 0ms, 100ms, 0ms; }
[data-testid^="stBaseButton"]:active { transform: scale(0.98); }
[data-testid^="stBaseButton"]:focus-visible { box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent); outline: none; }
[data-testid="stBaseButton-primary"] { color: var(--on-accent); border: 0; box-shadow: var(--highlight); }
[data-testid="stBaseButton-secondary"] { background: var(--surface-1); border-color: var(--border-strong); color: var(--text-1); }
[data-testid="stBaseButton-secondary"]:hover { background: var(--surface-2); border-color: var(--border-strong); color: var(--text-1); }
[data-testid^="stBaseButton"]:disabled { opacity: .45; }

/* Expanders de la barra lateral */
[data-testid="stExpander"] details { border-color: var(--border); border-radius: var(--r-md); }
[data-testid="stExpander"] summary:hover { background: var(--surface-2); }

/* ---------- Piezas propias ---------- */
.marca { display: flex; align-items: center; gap: 10px; color: var(--text-1); font-weight: 550; letter-spacing: -0.01em; font-size: .95rem; }
.marca::before { content: ""; width: 20px; height: 20px; flex: none; background: var(--accent);
  -webkit-mask: var(--icono-escudo) center / contain no-repeat; mask: var(--icono-escudo) center / contain no-repeat; }
:root { --icono-escudo: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.6' stroke-linejoin='round' stroke-linecap='round'%3E%3Cpath d='M12 2.75 4.5 5.6v5.9c0 4.7 3.2 8.6 7.5 9.75 4.3-1.15 7.5-5.05 7.5-9.75V5.6L12 2.75Z'/%3E%3Cpath d='m8.75 12 2.25 2.25 4.25-4.5'/%3E%3C/svg%3E"); }
.chip { display: inline-flex; align-items: center; gap: 6px; height: 22px; padding: 0 8px; border-radius: var(--r-full);
  font: 500 .72rem/1 var(--mono); color: var(--text-2); background: var(--surface-1); box-shadow: 0 0 0 1px var(--border); white-space: nowrap; }
.mono { font-family: var(--mono); font-size: .8em; letter-spacing: 0; }
.punto { width: 8px; height: 8px; border-radius: 50%; flex: none; background: var(--c, var(--st-desconocido)); }

/* Encabezado + pasos */
.encabezado { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 40px; }
.pasos { display: flex; gap: 6px; list-style: none; margin: 0; padding: 0; }
.pasos li { display: flex; align-items: center; gap: 8px; height: 28px; padding: 0 12px; border-radius: var(--r-full);
  font-size: .8rem; color: var(--text-3); box-shadow: 0 0 0 1px var(--border); }
.pasos li.hecho { color: var(--text-2); }
.pasos li.actual { color: var(--text-1); background: var(--surface-1); box-shadow: 0 0 0 1px var(--border-strong), var(--highlight); }
.pasos li.actual .punto { --c: var(--accent); box-shadow: 0 0 0 3px var(--accent-subtle); }
.pasos li.hecho .punto { --c: var(--text-3); }
.titular { font-size: clamp(1.75rem, 2.4vw + 1rem, 2.5rem); line-height: 1.1; letter-spacing: -0.032em; font-weight: 550;
  color: var(--text-1); margin: 0 0 12px; }
.lead { font-size: 1.06rem; line-height: 1.6; color: var(--text-2); max-width: 60ch; margin: 0 0 32px; }

/* Guía inicial */
.guia { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--border);
  border-radius: var(--r-lg); overflow: hidden; box-shadow: 0 0 0 1px var(--border); margin-bottom: 16px; }
.guia div { background: var(--bg); padding: 16px 18px; }
.guia b { display: block; color: var(--text-1); font-weight: 520; font-size: .9rem; letter-spacing: -0.01em; margin-bottom: 4px; }
.guia span { color: var(--text-3); font-size: .82rem; line-height: 1.5; }
.nota { color: var(--text-3); font-size: .8rem; margin: 8px 0 24px; }

/* Fila compacta de respuesta Sí/No en el chat */
.respuesta { display: flex; align-items: center; gap: 12px; padding: 10px 14px; margin: 2px 0 2px 48px; border-radius: var(--r-md);
  color: var(--text-2); font-size: .86rem; box-shadow: 0 0 0 1px var(--border); }
.respuesta .nombre { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.respuesta .valor { font-weight: 550; color: var(--c); }

/* Tarjeta de verificación */
.st-key-verificacion { background: var(--surface-1); box-shadow: var(--elev-2); border-radius: var(--r-lg);
  padding: 22px 24px 18px; margin: 16px 0 8px; animation: entrar 350ms var(--ease-out-expo) both; }
.verif-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; }
.verif-control { display: flex; align-items: center; gap: 10px; color: var(--text-2); font-size: .85rem; min-width: 0; }
.verif-cuenta { font: 500 .78rem/1 var(--mono); color: var(--text-3); font-variant-numeric: tabular-nums; white-space: nowrap; }
.barra { height: 2px; background: var(--border); border-radius: 2px; overflow: hidden; margin-bottom: 18px; }
.barra i { display: block; height: 100%; background: var(--accent); transform-origin: left; transform: scaleX(var(--p));
  transition: transform 500ms var(--ease-out); }
.verif-pregunta { font-size: 1.16rem; line-height: 1.45; letter-spacing: -0.012em; color: var(--text-1); margin: 0 0 14px; max-width: 60ch; }
.verif-refs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 4px; }
.verif-ayuda { color: var(--text-3); font-size: .78rem; margin-top: 4px; }

/* Barra lateral: anillo + conteos */
.postura { display: flex; align-items: center; gap: 20px; margin: 18px 0 20px; }
@property --pct { syntax: "\\3c number\\3e"; inherits: false; initial-value: 0; }  /* number entre ángulos, escapado: st.html no admite el carácter de menor que en el CSS */
.anillo { position: relative; width: 96px; height: 96px; flex: none; }
.anillo .arco { position: absolute; inset: 0; border-radius: 50%; --pct: var(--hasta);
  background: conic-gradient(var(--accent) calc(var(--pct) * 1%), var(--border-strong) 0);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 7px), #000 calc(100% - 6px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 7px), #000 calc(100% - 6px));
  animation: llenar 1100ms var(--ease-out-expo) both; }
.anillo .halo { position: absolute; inset: -6px; border-radius: 50%; pointer-events: none;
  background: radial-gradient(closest-side, transparent 78%, var(--accent-subtle) 92%, transparent); opacity: calc(var(--hasta) / 100); }
@keyframes llenar { from { --pct: var(--desde); } to { --pct: var(--hasta); } }
.anillo .cifra { position: absolute; inset: 0; display: grid; place-content: center; text-align: center; }
.anillo .cifra b { font-size: 1.6rem; font-weight: 550; letter-spacing: -0.04em; color: var(--text-1); font-variant-numeric: tabular-nums; line-height: 1; }
.anillo .cifra b small { font-size: .55em; color: var(--text-3); font-weight: 500; margin-left: 1px; }
.anillo .cifra span { font-size: .66rem; color: var(--text-3); margin-top: 4px; }
.conteos { display: grid; gap: 7px; flex: 1; margin: 0; padding: 0; list-style: none; }
.conteos li { display: flex; align-items: center; gap: 8px; font-size: .78rem; color: var(--text-2); white-space: nowrap; }
.conteos li b { margin-left: auto; color: var(--text-1); font-weight: 520; font-variant-numeric: tabular-nums; }

/* Momento firma: matriz de postura */
.matriz { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4px; margin-bottom: 8px; }
.celda { position: relative; height: 34px; border-radius: var(--r-sm); display: grid; place-items: center;
  font: 500 .66rem/1 var(--mono); color: var(--c); background: color-mix(in oklch, var(--c) 13%, var(--bg));
  box-shadow: inset 0 0 0 1px color-mix(in oklch, var(--c) 30%, transparent); cursor: default;
  transition: background-color 150ms var(--ease-out); }
.celda.desconocido { color: var(--text-3); background: var(--surface-1); box-shadow: inset 0 0 0 1px var(--border); }
@media (hover: hover) { .celda:hover { background: color-mix(in oklch, var(--c) 24%, var(--bg)); transition-duration: 0ms; } }
.celda.cambio { animation: latido 650ms var(--spring-bouncy) both; }
.celda.cambio::after { content: ""; position: absolute; inset: -1px; border-radius: inherit; pointer-events: none;
  box-shadow: 0 0 0 2px var(--c), 0 0 18px var(--c); animation: halo 1400ms var(--ease-out) both; }
@keyframes latido { from { transform: scale(.82); } to { transform: scale(1); } }
@keyframes halo { from { opacity: .9; } to { opacity: 0; } }
.leyenda { color: var(--text-3); font-size: .72rem; margin: 6px 0 16px; }
.detalle { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
.detalle li { display: grid; gap: 3px; }
.detalle b { font-size: .8rem; font-weight: 520; color: var(--text-1); display: flex; gap: 8px; align-items: baseline; }
.detalle span { font-size: .75rem; color: var(--text-3); line-height: 1.45; }
/* Verificación completa: check que se dibuja + barra de carga mientras llega el reporte */
:root { --icono-check: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5'/%3E%3C/svg%3E");
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1); }
.verif-fin { display: flex; align-items: center; gap: 16px; padding: 4px 0 2px; }
.check { position: relative; width: 44px; height: 44px; flex: none; border-radius: 50%; display: grid; place-items: center;
  background: color-mix(in oklch, var(--st-cubierto) 15%, var(--surface-1)); box-shadow: inset 0 0 0 1.5px var(--st-cubierto);
  animation: aparecer var(--spring-bouncy-dur, 650ms) var(--spring-bouncy) both; }
.check i { width: 22px; height: 22px; background: var(--st-cubierto); clip-path: inset(0 100% 0 0);
  -webkit-mask: var(--icono-check) center / contain no-repeat; mask: var(--icono-check) center / contain no-repeat;
  animation: trazar 420ms var(--ease-out) 240ms forwards; }
.check::after { content: ""; position: absolute; inset: 0; border-radius: 50%; pointer-events: none;
  box-shadow: 0 0 0 1.5px var(--st-cubierto); animation: onda 900ms var(--ease-out) 320ms both; }
@keyframes aparecer { from { transform: scale(.55); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes trazar { to { clip-path: inset(0 0 0 0); } }
@keyframes onda { from { transform: scale(1); opacity: .8; } to { transform: scale(1.8); opacity: 0; } }
.verif-fin-titulo { margin: 0 0 3px; color: var(--text-1); font-weight: 530; font-size: 1.05rem; letter-spacing: -0.014em; }
.verif-fin-texto { margin: 0; color: var(--text-2); font-size: .86rem; }
.barra.carga { position: relative; margin-bottom: 18px; }
.barra.carga::after { content: ""; position: absolute; inset: 0; width: 30%;
  background: linear-gradient(90deg, transparent, oklch(1 0 0 / .7), transparent); animation: barrido 1500ms var(--ease-in-out) infinite; }
@keyframes barrido { from { transform: translateX(-100%); } to { transform: translateX(340%); } }

/* Reporte */
.reporte { margin-top: 56px; padding-top: 48px; border-top: 1px solid var(--border); }
.reporte h2 { font-size: clamp(1.5rem, 1.6vw + 1rem, 2rem); letter-spacing: -0.028em; font-weight: 550; color: var(--text-1); margin: 0 0 12px; line-height: 1.15; }
.reporte h3 { font-size: 1.05rem; letter-spacing: -0.015em; font-weight: 530; color: var(--text-1); margin: 56px 0 16px; }
.resumen { color: var(--text-2); font-size: 1.04rem; line-height: 1.65; max-width: 65ch; white-space: pre-line; }
.cobertura { display: grid; grid-template-columns: auto 1fr; gap: 28px; align-items: center; margin-top: 32px;
  padding: 22px 24px; background: var(--surface-1); border-radius: var(--r-lg); box-shadow: var(--elev-1); }
.cobertura .pct { font-size: 2.75rem; font-weight: 550; letter-spacing: -0.045em; color: var(--text-1); line-height: 1; font-variant-numeric: tabular-nums; }
.cobertura .pct small { display: block; font-size: .78rem; letter-spacing: 0; color: var(--text-3); font-weight: 400; margin-top: 8px; }
.apilada { display: flex; height: 10px; border-radius: var(--r-full); overflow: hidden; gap: 2px; margin-bottom: 12px; }
.apilada i { background: var(--c); }
.leyenda-rep { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: .8rem; color: var(--text-2); }
.leyenda-rep span { display: inline-flex; align-items: center; gap: 7px; }
.leyenda-rep b { color: var(--text-1); font-weight: 520; font-variant-numeric: tabular-nums; }
.tabla-envoltura { overflow-x: auto; border-radius: var(--r-lg); box-shadow: 0 0 0 1px var(--border); }
table.controles { width: 100%; border-collapse: collapse; font-size: .84rem; min-width: 680px; }
table.controles th { text-align: left; font-weight: 500; color: var(--text-3); font-size: .74rem; padding: 10px 14px; background: var(--surface-1); border-bottom: 1px solid var(--border); }
table.controles td { padding: 12px 14px; border-bottom: 1px solid var(--border); vertical-align: top; color: var(--text-2); }
table.controles tr:last-child td { border-bottom: 0; }
table.controles tbody tr { transition: background-color 150ms var(--ease-out); }
table.controles tbody tr:hover { background: var(--surface-1); transition-duration: 0ms; }
table.controles td.ctrl { color: var(--text-1); }
table.controles td.ctrl .mono { color: var(--text-3); display: block; margin-bottom: 2px; }
table.controles td.refs { font: .74rem/1.5 var(--mono); color: var(--text-3); }
table.controles td.just { color: var(--text-3); font-size: .8rem; max-width: 36ch; }
.estado { display: inline-flex; align-items: center; gap: 7px; white-space: nowrap; color: var(--text-1); font-size: .8rem; }
.riesgos { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.riesgos li { padding: 4px 0 4px 16px; border-left: 2px solid var(--st-no_cubierto); color: var(--text-2); line-height: 1.6; max-width: 70ch; }
.wins { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.win { padding: 18px 20px; background: var(--surface-1); border-radius: var(--r-lg); box-shadow: var(--elev-1);
  transition: box-shadow 150ms var(--ease-out); }
.win:hover { box-shadow: 0 0 0 1px var(--border-strong), var(--highlight); transition-duration: 0ms; }
.win.destacado { grid-column: span 2; background: linear-gradient(180deg, color-mix(in oklch, var(--accent) 7%, var(--surface-1)), var(--surface-1)); }
.win h4 { margin: 0 0 6px; font-size: .98rem; font-weight: 530; letter-spacing: -0.012em; color: var(--text-1); }
.win p { margin: 0 0 14px; color: var(--text-2); font-size: .86rem; line-height: 1.6; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.plazos { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; }
.plazo h5 { margin: 0 0 12px; font: 500 .78rem/1 var(--mono); color: var(--text-3); padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.rec { padding: 12px 0 16px; border-bottom: 1px solid var(--border); }
.rec:last-child { border-bottom: 0; }
.rec b { display: block; color: var(--text-1); font-weight: 520; font-size: .9rem; letter-spacing: -0.01em; margin: 8px 0 4px; }
.rec p { margin: 0 0 8px; color: var(--text-2); font-size: .84rem; line-height: 1.6; }
.prioridad { --c: var(--st-desconocido); color: var(--c); background: color-mix(in oklch, var(--c) 12%, transparent); box-shadow: inset 0 0 0 1px color-mix(in oklch, var(--c) 30%, transparent); }
.prioridad.alta { --c: var(--st-no_cubierto); } .prioridad.media { --c: var(--st-parcial); }
.vacio { color: var(--text-3); font-size: .85rem; }

@keyframes entrar { from { opacity: 0; transform: translateY(6px); } }

@media (max-width: 720px) {
  .guia, .wins, .plazos { grid-template-columns: 1fr; }
  .win.destacado { grid-column: auto; }
  .cobertura { grid-template-columns: 1fr; gap: 16px; }
  .respuesta { margin-left: 0; }
  .encabezado { margin-bottom: 28px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
  .check i { clip-path: none; }  /* sin animación, el check se muestra completo */
}
</style>
"""

def _c(estado: str) -> str:
    return f"--c: var(--st-{estado})"


# --------------------------------------------------------------- encabezado
def encabezado(fase: str) -> str:
    pasos = [("contexto", "Contexto"), ("verificacion", "Verificación"), ("reporte", "Reporte")]
    idx = [p[0] for p in pasos].index(fase)
    items = "".join(
        f'<li class="{"actual" if i == idx else "hecho" if i < idx else ""}"'
        f'{" aria-current=\"step\"" if i == idx else ""}><span class="punto"></span>{nombre}</li>'
        for i, (_, nombre) in enumerate(pasos)
    )
    return (f'<header class="encabezado"><div class="marca">Diagnóstico de controles'
            f'<span class="chip">ISO/IEC 27002:2022 · CIS v8</span></div>'
            f'<ol class="pasos" aria-label="Progreso">{items}</ol></header>')


def titular(texto: str, lead: str) -> str:
    return f'<h1 class="titular">{esc(texto)}</h1><p class="lead">{esc(lead)}</p>'


GUIA = [
    ("Sector y tamaño", "Industria, número de empleados y sedes."),
    ("Infraestructura", "On-premise, nube, trabajo remoto, redes."),
    ("Sistemas críticos", "ERP, e-commerce, correo, apps propias."),
    ("Datos que manejan", "Personales, financieros, de salud, propiedad intelectual."),
    ("Medidas actuales", "Antivirus, respaldos, MFA, firewall, políticas."),
    ("Equipo y proveedores", "Quién gestiona TI y seguridad, servicios externos."),
]


def guia_inicial() -> str:
    celdas = "".join(f"<div><b>{t}</b><span>{d}</span></div>" for t, d in GUIA)
    return f'<div class="guia" role="list">{celdas}</div>'


# ------------------------------------------------------------- chat / verificación
def fila_respuesta(control_id: str, respuesta: bool) -> str:
    c = CONTROLES_POR_ID[control_id]
    estado = "cubierto" if respuesta else "no_cubierto"
    return (f'<div class="respuesta" style="{_c(estado)}"><span class="punto"></span>'
            f'<span class="mono">{c.id}</span><span class="nombre">{esc(c.nombre)}</span>'
            f'<span class="valor">{"Sí" if respuesta else "No"}</span></div>')


def cabecera_pregunta(control_id: str, pregunta: str, respondidas: int, total: int) -> str:
    c = CONTROLES_POR_ID[control_id]
    refs = "".join(f'<span class="chip">ISO {esc(x.split(" ")[0])}</span>' for x in c.iso27002)
    refs += "".join(f'<span class="chip">{esc(" ".join(x.split(" ")[:2]))}</span>' for x in c.cis_v8)
    p = respondidas / total if total else 0
    return (f'<div class="verif-top"><div class="verif-control"><span class="mono">{c.id}</span>{esc(c.nombre)}</div>'
            f'<span class="verif-cuenta">{respondidas + 1} / {total}</span></div>'
            f'<div class="barra" aria-hidden="true"><i style="--p:{p:.3f}"></i></div>'
            f'<p class="verif-pregunta">{esc(pregunta)}</p><div class="verif-refs">{refs}</div>')


def tarjeta_completada(respondidas: int, completa: bool) -> str:
    titulo = "Verificación completa" if completa else "Generando el reporte"
    detalle = (f"{respondidas} respuesta{'s' if respondidas != 1 else ''} registrada{'s' if respondidas != 1 else ''}. "
               "Estoy redactando tu diagnóstico…")
    return (f'<div class="barra carga" aria-hidden="true"><i style="--p:1"></i></div>'
            f'<div class="verif-fin" role="status" aria-live="polite">'
            f'<span class="check" aria-hidden="true"><i></i></span>'
            f'<div><p class="verif-fin-titulo">{titulo}</p><p class="verif-fin-texto">{detalle}</p></div></div>')


# ------------------------------------------------------------- barra lateral
def postura(resumen: dict, cobertura_desde: float, cobertura: float) -> str:
    conteos = "".join(
        f'<li><span class="punto" style="{_c(e)}"></span>{ETIQUETA[e]}<b>{resumen[e]}</b></li>' for e in ORDEN_ESTADOS)
    return (f'<div class="marca">Postura de seguridad</div>'
            f'<div class="postura"><div class="anillo" role="img" aria-label="Cobertura estimada {cobertura:.0f}%" '
            f'style="--desde:{cobertura_desde:.1f};--hasta:{cobertura:.1f}">'
            f'<span class="halo" aria-hidden="true"></span><span class="arco" aria-hidden="true"></span>'
            f'<div class="cifra"><b>{cobertura:.0f}<small>%</small></b><span>cobertura</span></div></div>'
            f'<ul class="conteos">{conteos}</ul></div>')


def matriz(estados: dict[str, str], cambiados: set[str]) -> str:
    celdas = "".join(
        f'<div class="celda {estados[c.id]}{" cambio" if c.id in cambiados else ""}" style="{_c(estados[c.id])}" '
        f'title="{c.id} · {esc(c.nombre)} — {ETIQUETA[estados[c.id]]}" role="listitem" '
        f'aria-label="{esc(c.nombre)}: {ETIQUETA[estados[c.id]]}">{c.id}</div>'
        for c in CONTROLES)
    return (f'<div class="matriz" role="list" aria-label="Matriz de controles">{celdas}</div>'
            f'<p class="leyenda">Cada celda es un dominio de control. Pasa el cursor para ver su nombre.</p>')


def detalle(controles_estado) -> str:
    items = "".join(
        f'<li><b><span class="mono">{cid}</span>{esc(CONTROLES_POR_ID[cid].nombre)}</b><span>{esc(ec.justificacion)}</span></li>'
        for cid, ec in controles_estado)
    return f'<ul class="detalle">{items}</ul>'


# ------------------------------------------------------------------ reporte
def reporte(rep: dict, evaluacion) -> str:
    r = evaluacion.resumen()
    total = sum(r.values())
    segmentos = "".join(f'<i style="{_c(e)};flex:{r[e]}"></i>' for e in ORDEN_ESTADOS if r[e])
    leyenda = "".join(f'<span><span class="punto" style="{_c(e)}"></span>{ETIQUETA[e]} <b>{r[e]}</b></span>' for e in ORDEN_ESTADOS)

    filas = ""
    for e in ORDEN_ESTADOS:
        for c in CONTROLES:
            ec = evaluacion.controles[c.id]
            if ec.estado != e:
                continue
            iso = ", ".join(x.split(" ")[0] for x in c.iso27002) or "—"
            cis = ", ".join(x.split(" ")[1] for x in c.cis_v8) or "—"
            filas += (f'<tr><td class="ctrl"><span class="mono">{c.id}</span>{esc(c.nombre)}</td>'
                      f'<td class="refs">ISO {esc(iso)}<br>CIS {esc(cis)}</td>'
                      f'<td><span class="estado"><span class="punto" style="{_c(e)}"></span>{ETIQUETA[e]}</span></td>'
                      f'<td class="just">{esc(ec.justificacion)}</td></tr>')

    riesgos = "".join(f"<li>{esc(x)}</li>" for x in rep.get("riesgos_principales", [])) or '<li class="vacio">Sin riesgos reportados.</li>'

    wins = ""
    for i, q in enumerate(rep.get("quick_wins", [])):
        cid = q.get("control_id", "")
        wins += (f'<article class="win{" destacado" if i == 0 else ""}"><h4>{esc(q.get("titulo"))}</h4><p>{esc(q.get("descripcion"))}</p>'
                 f'<div class="chips"><span class="chip">{esc(cid)}</span>'
                 f'<span class="chip">esfuerzo {esc(q.get("esfuerzo"))}</span><span class="chip">impacto {esc(q.get("impacto"))}</span></div></article>')

    orden = {"alta": 0, "media": 1, "baja": 2}
    columnas = ""
    for plazo in ("0-3 meses", "3-6 meses", "6-12 meses"):
        recs = sorted((x for x in rep.get("recomendaciones", []) if x.get("plazo") == plazo),
                      key=lambda x: orden.get(x.get("prioridad"), 3))
        cuerpo = "".join(
            f'<div class="rec"><span class="chip prioridad {esc(x.get("prioridad"))}">prioridad {esc(x.get("prioridad"))}</span>'
            f'<b>{esc(x.get("titulo"))}</b><p>{esc(x.get("descripcion"))}</p>'
            f'<div class="chips">{"".join(f"<span class=chip>{esc(cid)}</span>" for cid in x.get("controles", []))}</div></div>'
            for x in recs) or '<p class="vacio">Sin acciones en este plazo.</p>'
        columnas += f'<div class="plazo"><h5>{plazo}</h5>{cuerpo}</div>'

    return f"""
<section class="reporte" aria-labelledby="titulo-reporte">
  <h2 id="titulo-reporte">Diagnóstico de la empresa</h2>
  <p class="resumen">{esc(rep.get("resumen_ejecutivo"))}</p>
  <div class="cobertura">
    <div class="pct">{evaluacion.porcentaje_cobertura():.0f}%<small>cobertura estimada</small></div>
    <div><div class="apilada" role="img" aria-label="Distribución de {total} controles por estado">{segmentos}</div>
    <div class="leyenda-rep">{leyenda}</div></div>
  </div>
  <h3>Estado de los controles</h3>
  <div class="tabla-envoltura"><table class="controles">
    <thead><tr><th>Control</th><th>Referencias</th><th>Estado</th><th>Justificación</th></tr></thead>
    <tbody>{filas}</tbody></table></div>
  <h3>Riesgos principales</h3><ul class="riesgos">{riesgos}</ul>
  <h3>Quick wins</h3><div class="wins">{wins or '<p class="vacio">Sin quick wins.</p>'}</div>
  <h3>Hoja de ruta</h3><div class="plazos">{columnas}</div>
</section>"""
