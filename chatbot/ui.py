"""Capa visual: tokens CSS y piezas HTML para la app Streamlit.

Arquetipo "craft oscuro": neutros fríos de croma muy bajo, bordes de 1px,
un solo acento (verde azulado) y colores de estado con el mismo peso.
Momento firma: el anillo de implementación y la matriz de controles en la barra lateral.

Todo texto que viene del usuario o de Claude pasa por ``esc()`` antes de
insertarse en HTML.
"""

import time
from html import escape as _escape

from .controls import catalogo, control, salvaguarda
from .prompts import DIMENSIONES, NOMBRE_AGENTE
from .state import ESTADOS, ETIQUETA, ETIQUETA_APLICABILIDAD, SITUACION_RIESGO, formato_pct

ETIQUETA_CORTA = {"implementado": "Implementado", "parcial": "Parcial", "no_implementado": "No implementado",
                  "no_verificado": "No verificado", "no_aplicable": "No aplicable"}
TAMANO = {"micro": "Micro", "pequena": "Pequeña", "mediana": "Mediana", "grande": "Grande"}
IMPACTO = {"critico": "Crítico", "alto": "Alto", "medio": "Medio"}
ESTADO_INICIATIVA = {"completada": "Completada", "en_progreso": "En progreso", "pendiente": "Pendiente"}


def esc(texto) -> str:
    return _escape(str(texto or ""), quote=True)


# --------------------------------------------------------------------------- CSS
CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap");
/* Identidad "Pizarra cálida" (Día, en :root) y "Grafito" (Noche, en [data-theme="dark"]), del mockup aprobado
   (mockup/resumen.html). ui.tema_script() pone data-theme según el tema que Streamlit aplicó; antes de que corra,
   prefers-color-scheme da la primera pintura correcta. Los nombres antiguos (--bg, --text-1…) son alias. */
:root {
  --paper: oklch(0.945 0.006 85); --surface: oklch(0.972 0.005 85); --sunken: oklch(0.918 0.007 85); --side: oklch(0.928 0.007 85);
  --ink: oklch(0.27 0.012 255); --ink-2: oklch(0.40 0.011 255); --ink-3: oklch(0.485 0.010 255);
  --rule: oklch(0.875 0.007 85); --rule-2: oklch(0.78 0.008 85); --rule-strong: var(--rule-2); --line-control: oklch(0.62 0.01 85);
  --accent: oklch(0.47 0.055 228); --accent-strong: oklch(0.40 0.055 228); --accent-tint: oklch(0.90 0.022 228);
  --on-accent: oklch(0.98 0.004 85);
  --st-implementado: oklch(0.58 0.075 158); --st-parcial: oklch(0.71 0.095 78); --st-no_implementado: oklch(0.57 0.105 33);
  --st-no_verificado: oklch(0.56 0.010 255); --st-no_aplicable: oklch(0.84 0.006 85); --st-sin_ig1: oklch(0.875 0.007 85);
  --tint-implementado: oklch(0.91 0.03 158); --tint-parcial: oklch(0.92 0.040 80); --tint-no_implementado: oklch(0.90 0.040 33);
  --tint-no_aplicable: oklch(0.918 0.007 85);
  --seg-ink: oklch(0.22 0.01 255);
  --shadow-1: 0 1px 0 oklch(1 0 0 / .6) inset, 0 1px 2px oklch(0.3 0.02 85 / .06), 0 0 0 1px var(--rule);
  --shadow-2: 0 8px 24px oklch(0.3 0.02 85 / .14), 0 0 0 1px var(--rule);
  --pop: var(--shadow-2);
  --highlight: 0 1px 0 oklch(1 0 0 / .6) inset;
  --font: "Geist", system-ui, sans-serif; --font-display: var(--font); --font-text: var(--font);
  --mono: "Geist Mono", ui-monospace, Menlo, monospace;
  --r-sm: 3px; --r-md: 6px; --r-lg: 10px; --r-full: 9999px;
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --spring-bouncy: linear(0, 0.1, 0.323, 0.577, 0.803, 0.97, 1.073, 1.119, 1.124, 1.105, 1.074, 1.042, 1.016, 0.998, 0.988, 0.984, 0.985, 0.988, 0.992, 0.996, 0.999, 1.001, 1.002, 1.002, 1);
  color-scheme: light;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: oklch(0.205 0.005 255); --surface: oklch(0.240 0.006 255); --sunken: oklch(0.180 0.005 255); --side: oklch(0.225 0.006 255);
  --ink: oklch(0.925 0.005 85); --ink-2: oklch(0.80 0.006 85); --ink-3: oklch(0.68 0.007 85);
  --rule: oklch(0.300 0.006 255); --rule-2: oklch(0.38 0.007 255); --rule-strong: var(--rule-2); --line-control: oklch(0.50 0.008 255);
  --accent: oklch(0.74 0.065 222); --accent-strong: oklch(0.82 0.06 222); --accent-tint: oklch(0.32 0.035 225);
  --on-accent: oklch(0.20 0.01 255);
  --st-implementado: oklch(0.70 0.085 158); --st-parcial: oklch(0.78 0.095 80); --st-no_implementado: oklch(0.68 0.110 33);
  --st-no_verificado: oklch(0.62 0.010 255); --st-no_aplicable: oklch(0.40 0.006 255); --st-sin_ig1: oklch(0.30 0.006 255);
  --tint-implementado: oklch(0.32 0.045 158); --tint-parcial: oklch(0.34 0.050 80); --tint-no_implementado: oklch(0.33 0.055 33);
  --tint-no_aplicable: oklch(0.28 0.006 255);
  --seg-ink: oklch(0.20 0.01 255);
  --shadow-1: 0 1px 0 oklch(1 0 0 / .04) inset, 0 0 0 1px var(--rule);
  --shadow-2: 0 8px 24px oklch(0 0 0 / .45), 0 0 0 1px var(--rule-2);
  --pop: var(--shadow-2);
  --highlight: 0 1px 0 oklch(1 0 0 / .04) inset;
  color-scheme: dark;
} }
:root[data-theme="dark"] {
  --paper: oklch(0.205 0.005 255); --surface: oklch(0.240 0.006 255); --sunken: oklch(0.180 0.005 255); --side: oklch(0.225 0.006 255);
  --ink: oklch(0.925 0.005 85); --ink-2: oklch(0.80 0.006 85); --ink-3: oklch(0.68 0.007 85);
  --rule: oklch(0.300 0.006 255); --rule-2: oklch(0.38 0.007 255); --rule-strong: var(--rule-2); --line-control: oklch(0.50 0.008 255);
  --accent: oklch(0.74 0.065 222); --accent-strong: oklch(0.82 0.06 222); --accent-tint: oklch(0.32 0.035 225);
  --on-accent: oklch(0.20 0.01 255);
  --st-implementado: oklch(0.70 0.085 158); --st-parcial: oklch(0.78 0.095 80); --st-no_implementado: oklch(0.68 0.110 33);
  --st-no_verificado: oklch(0.62 0.010 255); --st-no_aplicable: oklch(0.40 0.006 255); --st-sin_ig1: oklch(0.30 0.006 255);
  --tint-implementado: oklch(0.32 0.045 158); --tint-parcial: oklch(0.34 0.050 80); --tint-no_implementado: oklch(0.33 0.055 33);
  --tint-no_aplicable: oklch(0.28 0.006 255);
  --seg-ink: oklch(0.20 0.01 255);
  --shadow-1: 0 1px 0 oklch(1 0 0 / .04) inset, 0 0 0 1px var(--rule);
  --shadow-2: 0 8px 24px oklch(0 0 0 / .45), 0 0 0 1px var(--rule-2);
  --pop: var(--shadow-2);
  --highlight: 0 1px 0 oklch(1 0 0 / .04) inset;
  color-scheme: dark;
}
/* Alias de los nombres anteriores: el resto de la hoja los sigue usando. */
:root, :root[data-theme] {
  --bg: var(--paper); --surface-1: var(--surface); --surface-2: var(--sunken); --surface-3: var(--surface);
  --text-1: var(--ink); --text-2: var(--ink-2); --text-3: var(--ink-3);
  --border: var(--rule); --border-strong: var(--rule-strong);
  --accent-subtle: var(--accent-tint); --accent-glow: color-mix(in oklch, var(--accent) 35%, transparent);
  --st-cubierto: var(--st-implementado); --st-no_cubierto: var(--st-no_implementado); --st-desconocido: var(--st-no_verificado);
  --elev-1: var(--shadow-1); --elev-2: var(--shadow-2);
}

/* ---------- Base de Streamlit ---------- */
.stApp { -webkit-font-smoothing: antialiased; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stMainBlockContainer"], [data-testid="stBottomBlockContainer"] {
  max-width: 1100px; padding-left: clamp(16px, 4vw, 40px); padding-right: clamp(16px, 4vw, 40px);
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
.marca { display: flex; align-items: center; gap: 10px; color: var(--text-1); font-weight: 600; letter-spacing: -0.01em; font-size: 15px; }
.chip { display: inline-flex; align-items: center; gap: 6px; height: 22px; padding: 0 8px; border-radius: var(--r-full);
  font: 500 .72rem/1 var(--mono); color: var(--text-2); background: var(--surface-1); box-shadow: 0 0 0 1px var(--border); white-space: nowrap; }
.mono { font-family: var(--mono); font-size: .8em; letter-spacing: 0; }
.punto { width: 8px; height: 8px; border-radius: 50%; flex: none; background: var(--c, var(--st-desconocido)); }

/* Encabezado: etapas como pasos (completado ✓, actual, pendiente) */
.encabezado { margin-bottom: 24px; }
.pasos { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; list-style: none; margin: 0; padding: 0; font-size: 12px; color: var(--ink-3); }
.pasos li { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px 3px 4px; border-radius: 99px; margin: 0; }
.pasos li + li::before { content: ""; width: 20px; height: 1px; background: var(--rule-2); margin: 0 6px 0 -4px; }
.pasos li i { width: 18px; height: 18px; border-radius: 50%; display: grid; place-items: center; font-style: normal; font-size: 10px;
  font-weight: 600; line-height: 1; text-box: trim-both cap alphabetic; box-shadow: inset 0 0 0 1.5px var(--rule-2); color: var(--ink-3); }
.pasos li.hecho { color: var(--ink-2); }
.pasos li.hecho i { background: var(--ink-3); color: var(--paper); box-shadow: none; }
.pasos li.actual { background: var(--surface); color: var(--ink); font-weight: 500; box-shadow: 0 0 0 1px var(--rule); }
.pasos li.actual i { background: var(--accent); color: var(--on-accent); box-shadow: none; }
@media (max-width: 640px) {
  .pasos { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; padding-bottom: 2px; }
  .pasos li { flex: none; white-space: nowrap; }
}
.titular { font-size: 26px; line-height: 32px; letter-spacing: -0.02em; font-weight: 600; color: var(--text-1); margin: 0 0 6px; }
.lead { font-size: 14px; line-height: 1.6; color: var(--text-2); max-width: 70ch; margin: 0 0 28px; }

/* Guía inicial */
.guia { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--border);
  border-radius: var(--r-lg); overflow: hidden; box-shadow: 0 0 0 1px var(--border); margin-bottom: 16px; }
.guia div { background: var(--bg); padding: 16px 18px; }
.guia b { display: block; color: var(--text-1); font-weight: 520; font-size: .9rem; letter-spacing: -0.01em; margin-bottom: 4px; }
.guia span { color: var(--text-3); font-size: .82rem; line-height: 1.5; }
.nota { color: var(--text-3); font-size: .8rem; margin: 8px 0 24px; }

/* Fila compacta (cambios propuestos del PDF 2) */
.respuesta { display: flex; align-items: center; gap: 12px; padding: 10px 14px; margin: 2px 0 2px 48px; border-radius: var(--r-md);
  color: var(--text-2); font-size: .86rem; box-shadow: 0 0 0 1px var(--border); }
.respuesta .nombre { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.respuesta .valor { font-weight: 550; color: var(--c); }

.barra { height: 2px; background: var(--border); border-radius: 2px; overflow: hidden; margin-bottom: 18px; }
.barra i { display: block; height: 100%; background: var(--accent); transform-origin: left; transform: scaleX(var(--p));
  transition: transform 500ms var(--ease-out); }

/* Barra lateral: anillo + conteos */
.postura { display: flex; flex-wrap: wrap; align-items: center; gap: 16px 20px; margin: 18px 0 20px; }
.postura .conteos { min-width: 170px; }
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
.anillo .cifra b { font-family: var(--font-display); font-size: 1.75rem; font-weight: 500; letter-spacing: -0.02em; color: var(--text-1); font-variant-numeric: tabular-nums; line-height: 1; }
.anillo .cifra b small { font-size: .55em; color: var(--text-3); font-weight: 500; margin-left: 1px; }
.anillo .cifra span { font-size: .66rem; color: var(--text-3); margin-top: 4px; }
.conteos { display: grid; gap: 7px; flex: 1; margin: 0; padding: 0; list-style: none; }
.conteos li { display: flex; align-items: center; gap: 8px; font-size: .78rem; color: var(--text-2); white-space: nowrap; }
.conteos li b { margin-left: auto; color: var(--text-1); font-weight: 520; font-variant-numeric: tabular-nums; }

/* Momento firma: matriz de postura */
.matriz { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4px; margin-bottom: 8px; }
.celda { position: relative; height: 34px; border-radius: var(--r-sm); display: grid; place-items: center;
  font: 500 .66rem/1 var(--mono); color: var(--ink); background: color-mix(in oklch, var(--c) 16%, var(--bg));
  box-shadow: inset 0 0 0 1px color-mix(in oklch, var(--c) 55%, transparent); cursor: default;
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
  background: linear-gradient(90deg, transparent, var(--accent-glow), transparent); animation: barrido 1500ms var(--ease-in-out) infinite; }
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
.prioridad { --c: var(--st-desconocido); color: var(--ink); background: color-mix(in oklch, var(--c) 16%, transparent); box-shadow: inset 0 0 0 1px color-mix(in oklch, var(--c) 55%, transparent); }
.prioridad.alta { --c: var(--st-no_cubierto); } .prioridad.media { --c: var(--st-parcial); }
.vacio { color: var(--text-3); font-size: .85rem; }


/* Perfil de riesgo */
.perfil { background: var(--surface-1); box-shadow: var(--elev-1); border-radius: var(--r-lg); padding: 22px 24px;
  margin: 12px 0 8px 48px; animation: entrar 350ms var(--ease-out-expo) both; }
.perfil.en-reporte { margin: 56px 0 0; animation: none; }
.perfil-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
.perfil-top h3 { margin: 0; font-size: 1rem; font-weight: 550; letter-spacing: -0.012em; color: var(--text-1); }
.chip.ig { color: var(--on-accent); background: var(--accent); box-shadow: none; }
.perfil-resumen { color: var(--text-2); font-size: .9rem; line-height: 1.6; margin: 0 0 18px; max-width: 70ch; }
.perfil-datos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 28px; margin-bottom: 20px; }
.perfil h4 { margin: 0 0 6px; font: 500 .72rem/1.2 var(--mono); color: var(--text-3); }
.perfil-datos ul { margin: 0; padding-left: 16px; color: var(--text-2); font-size: .82rem; line-height: 1.55; }
.amenazas { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
.amenazas li { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; align-items: baseline; padding: 12px 14px;
  border-radius: var(--r-md); box-shadow: 0 0 0 1px var(--border); }
.amenazas b { color: var(--text-1); font-weight: 520; font-size: .88rem; }
.amenazas .razon { grid-column: 2; color: var(--text-3); font-size: .8rem; line-height: 1.5; }
.amenazas .chips { grid-column: 2; margin-top: 4px; }
.impacto { --c: var(--st-desconocido); color: var(--ink); background: color-mix(in oklch, var(--c) 16%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in oklch, var(--c) 55%, transparent); }
.impacto.critico { --c: var(--st-no_cubierto); } .impacto.alto { --c: var(--st-parcial); }

/* Evaluación en curso */
.progreso { display: flex; align-items: center; gap: 16px; padding: 4px 0 2px; }
.pulso { width: 10px; height: 10px; margin: 0 7px; flex: none; border-radius: 50%; background: var(--accent);
  animation: pulso 1400ms var(--ease-out) infinite; }
@keyframes pulso { from { box-shadow: 0 0 0 0 var(--accent-glow); } to { box-shadow: 0 0 0 12px transparent; } }

/* Detalle de salvaguardas */
.postura-perfil { display: flex; flex-wrap: wrap; gap: 6px; margin: -6px 0 18px; }
.salv-lista { margin: 6px 0 0; padding: 0; list-style: none; display: grid; gap: 4px; }
.salv-lista li { font-size: .76rem; color: var(--text-3); line-height: 1.45; }
.salv-lista li .mono { color: var(--c); margin-right: 6px; }
.atribucion { color: var(--text-3); font-size: .72rem; line-height: 1.5; margin-top: 48px; max-width: 80ch; }


/* ---------- Actividad M3.6: 5 estados oficiales (tokens arriba) ---------- */
.celda.sin_ig1 { color: var(--text-3); background: transparent; box-shadow: inset 0 0 0 1px var(--border); opacity: .55; }
.celda.no_verificado { color: var(--text-3); background: var(--surface-1); box-shadow: inset 0 0 0 1px var(--border); }

/* Tablero */
.tablero { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; background: var(--border);
  border-radius: var(--r-lg); overflow: hidden; box-shadow: 0 0 0 1px var(--border); margin: 8px 0 12px; }
.tablero > div { background: var(--surface-1); padding: 18px 20px; }
.tablero b { display: block; font-size: 30px; font-weight: 600; letter-spacing: -0.03em;
  color: var(--text-1); font-variant-numeric: tabular-nums; line-height: 36px; }
.tablero b.nd { font-size: 1.05rem; letter-spacing: -0.01em; padding-top: 10px; }
.tablero span { display: block; font-size: .8rem; color: var(--text-2); margin-top: 6px; }
.tablero small { display: block; font-size: .72rem; color: var(--text-3); margin-top: 4px; line-height: 1.4; }
.tablero .delta { font: 500 .74rem/1 var(--mono); margin-top: 8px; color: var(--st-cubierto); }
.tablero .delta.neg { color: var(--st-no_cubierto); } .tablero .delta.cero { color: var(--text-3); }
.conteo-estados { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: .8rem; color: var(--text-2); margin: 4px 0 8px; }
.conteo-estados span { display: inline-flex; align-items: center; gap: 7px; }
.conteo-estados b { color: var(--text-1); font-weight: 520; font-variant-numeric: tabular-nums; }

/* Ficha de contexto */
.ficha { margin: 8px 0 16px; }
.ficha-resumen { color: var(--text-2); font-size: .94rem; line-height: 1.7; max-width: 72ch; white-space: pre-line; margin: 0 0 24px; }
.dims { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.dim { padding: 16px 18px; border-radius: var(--r-lg); background: var(--surface-1); box-shadow: var(--elev-1); }
.dim h4 { margin: 0 0 2px; font-size: .92rem; font-weight: 540; color: var(--text-1); letter-spacing: -0.01em; }
.dim .que { font-size: .72rem; color: var(--text-3); margin: 0 0 10px; }
.dim p { margin: 0 0 8px; font-size: .83rem; color: var(--text-2); line-height: 1.55; }
.dim ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; }
.dim li { font-size: .8rem; color: var(--text-2); line-height: 1.5; }
.ev { font: 500 .68rem/1 var(--mono); color: var(--text-3); white-space: nowrap; margin-left: 6px; }
.ev.ok { color: var(--st-cubierto); } .ev.mal { color: var(--st-no_cubierto); }
.dim .falta { color: var(--text-3); font-size: .76rem; margin-top: 8px; }
.listas { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; margin-top: 20px; }
.listas h4 { margin: 0 0 8px; font: 500 .74rem/1.2 var(--mono); color: var(--text-3); }
.listas ul { margin: 0; padding-left: 18px; color: var(--text-2); font-size: .84rem; line-height: 1.6; }

/* Matriz de 56 salvaguardas */
table.matriz56 { width: 100%; border-collapse: collapse; font-size: .8rem; min-width: 980px; }
table.matriz56 th { text-align: left; font-weight: 500; color: var(--text-3); font-size: .72rem; padding: 9px 12px;
  background: var(--surface-1); border-bottom: 1px solid var(--border); position: sticky; top: 0; }
table.matriz56 td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; color: var(--text-2); line-height: 1.5; }
table.matriz56 tr.grupo td { background: var(--surface-1); color: var(--text-1); font-weight: 520; font-size: .78rem; padding: 8px 12px; }
table.matriz56 tr.grupo td .mono { color: var(--text-3); margin-right: 8px; }
table.matriz56 tr.cambio td { background: color-mix(in oklch, var(--accent) 7%, transparent); }
table.matriz56 td.id { font: 500 .76rem/1.4 var(--mono); color: var(--text-1); white-space: nowrap; }
table.matriz56 td.titulo { color: var(--text-1); min-width: 180px; }
table.matriz56 td.cita { color: var(--text-3); font-style: italic; max-width: 32ch; }
table.matriz56 td.obs { color: var(--text-3); max-width: 30ch; }
table.matriz56 td.ev { white-space: normal; font-size: .72rem; }
.estado-chip { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; color: var(--text-1); font-size: .76rem; }

/* Riesgos, roadmap y cambios */
table.tabla { width: 100%; border-collapse: collapse; font-size: .82rem; min-width: 760px; }
table.tabla th { text-align: left; font-weight: 500; color: var(--text-3); font-size: .72rem; padding: 9px 12px; background: var(--surface-1);
  border-bottom: 1px solid var(--border); }
table.tabla td { padding: 11px 12px; border-bottom: 1px solid var(--border); vertical-align: top; color: var(--text-2); line-height: 1.5; }
table.tabla td b { color: var(--text-1); font-weight: 520; }
table.tabla tr:last-child td { border-bottom: 0; }
.sev { --c: var(--st-desconocido); } .sev.alta { --c: var(--st-no_cubierto); } .sev.media { --c: var(--st-parcial); } .sev.baja { --c: var(--st-cubierto); }
.sev, .tipo { color: var(--ink); background: color-mix(in oklch, var(--c) 16%, transparent); box-shadow: inset 0 0 0 1px color-mix(in oklch, var(--c) 55%, transparent); }
.tipo { --c: var(--accent); } .tipo.proyecto { --c: var(--st-no_aplicable); }
.resumen-ej { display: grid; gap: 22px; max-width: 78ch; }
.resumen-ej h4 { margin: 0 0 6px; font: 500 .74rem/1.2 var(--mono); color: var(--text-3); }
.resumen-ej p, .resumen-ej li { color: var(--text-2); font-size: .9rem; line-height: 1.65; margin: 0; white-space: pre-line; }
.resumen-ej ul { margin: 0; padding-left: 18px; display: grid; gap: 6px; }
.resumen-ej .preliminar { padding: 12px 14px; border-radius: var(--r-md); box-shadow: inset 0 0 0 1px color-mix(in oklch, var(--st-parcial) 35%, transparent);
  background: color-mix(in oklch, var(--st-parcial) 6%, transparent); }
.inis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.ini { padding: 16px 18px; border-radius: var(--r-lg); background: var(--surface-1); box-shadow: var(--elev-1); }
.ini h4 { margin: 0 0 8px; font-size: .92rem; font-weight: 540; color: var(--text-1); }
.ini p { margin: 0 0 8px; font-size: .8rem; color: var(--text-2); line-height: 1.55; }
.ini p b { color: var(--text-3); font-weight: 500; font: 500 .7rem/1 var(--mono); display: block; margin-bottom: 2px; }
.flecha { color: var(--text-3); margin: 0 6px; }
.seccion-titulo { font-size: 21px; line-height: 28px; letter-spacing: -0.015em; font-weight: 600; color: var(--text-1); margin: 40px 0 4px; }
.seccion-sub { color: var(--text-3); font-size: .84rem; margin: 0 0 16px; max-width: 75ch; line-height: 1.55; }
.aviso { font-size: .76rem; color: var(--text-3); line-height: 1.5; margin: 0 0 4px; }
.vacio { color: var(--text-3); font-size: .85rem; }

@keyframes entrar { from { opacity: 0; transform: translateY(6px); } }

/* ---------- Identidad Dictamen técnico: marcas de estado, etiquetas y controles ---------- */
.marca-estado { inline-size: 11px; block-size: 11px; flex: none; border-radius: var(--r-sm); box-sizing: border-box; display: inline-block; }
.m-implementado { background: var(--st-implementado); }
.m-parcial { border: 1.5px solid var(--st-parcial); background: linear-gradient(to right, var(--st-parcial) 50%, transparent 50%); }
.m-no_implementado { border: 1.5px solid var(--st-no_implementado);
  background: linear-gradient(135deg, transparent 42%, var(--st-no_implementado) 42% 58%, transparent 58%); }
.m-no_verificado { border: 1.5px dashed var(--st-no_verificado); }
.m-no_aplicable { background: var(--st-no_aplicable); }
.estado-chip { gap: 7px; padding: 2px 9px 2px 7px; border-radius: var(--r-sm); font-weight: 600; font-size: .74rem; letter-spacing: .01em; color: var(--ink); }
.estado-chip.e-implementado { background: var(--tint-implementado); }
.estado-chip.e-parcial { background: var(--tint-parcial); }
.estado-chip.e-no_implementado { background: var(--tint-no_implementado); }
.estado-chip.e-no_verificado { background: var(--sunken); }
.estado-chip.e-no_aplicable { background: var(--tint-no_aplicable); }
.conteos li .marca-estado, .conteo-estados .marca-estado { margin-right: 1px; }
/* Bordes de campos con 3:1 (el filete no alcanza) y texto sobre el acento */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"] { border-color: var(--line-control) !important; }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] p { color: var(--on-accent) !important; }
[data-testid="stBaseButton-secondary"] { border-color: var(--line-control); }
/* Selector Día/Noche */
.tema-selector { display: inline-flex; gap: 2px; padding: 3px; background: var(--sunken); border-radius: var(--r-md);
  box-shadow: inset 0 0 0 1px var(--rule); margin: 4px 0 14px; }
.tema-selector button { border: 0; background: transparent; cursor: pointer; font: 500 .8rem/1.2 var(--font-text); color: var(--ink-3);
  padding: 5px 14px; border-radius: 4px; transition: background-color 80ms, color 80ms; }
.tema-selector button:hover { color: var(--ink); }
.tema-selector button[aria-pressed="true"] { background: var(--surface); color: var(--ink); font-weight: 600; box-shadow: var(--shadow-1); }
.tema-selector button:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.tema-selector button:disabled { cursor: not-allowed; opacity: .6; }
@media (max-width: 720px) {
  .guia, .wins, .plazos { grid-template-columns: 1fr; }
  .win.destacado { grid-column: auto; }
  .cobertura { grid-template-columns: 1fr; gap: 16px; }
  .respuesta, .perfil { margin-left: 0; }
  .tablero, .dims, .listas, .inis { grid-template-columns: 1fr; }
  .perfil-datos { grid-template-columns: 1fr; }
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


def _chips(ids) -> str:
    return "".join(f'<span class="chip">{esc(i)}</span>' for i in ids)


def _marca(e: str) -> str:
    """Marca de estado: cada estado con su forma (lleno, a medias, tachado, punteado, guion), no solo su color."""
    return f'<span class="marca-estado m-{e}" aria-hidden="true"></span>'


def _estado(e: str) -> str:
    return f'<span class="estado-chip e-{e}">{_marca(e)}{ETIQUETA[e]}</span>'


ORDEN_ESTADOS = ESTADOS
ETAPAS = [("contexto", "Contexto"), ("evaluacion", "Evaluación 56"), ("reporte", "Reporte inicial"),
          ("iniciativas", "Avance con PDF 2"), ("actualizado", "Reporte actualizado")]


# --------------------------------------------------------------- encabezado
def encabezado(etapa: str) -> str:
    """Etapas como pasos: completadas con ✓, la actual resaltada y las pendientes con su número."""
    idx = [p[0] for p in ETAPAS].index(etapa)
    items = "".join(
        f'<li class="{"actual" if i == idx else "hecho" if i < idx else "pendiente"}"'
        f'{" aria-current=\"step\"" if i == idx else ""}><i>{"✓" if i < idx else i + 1}</i>{nombre}</li>'
        for i, (_, nombre) in enumerate(ETAPAS))
    return f'<header class="encabezado"><ol class="pasos" aria-label="Etapas">{items}</ol></header>'


def titular(texto: str, lead: str) -> str:
    return f'<h1 class="titular">{esc(texto)}</h1><p class="lead">{esc(lead)}</p>'


def seccion(titulo: str, sub: str = "") -> str:
    return f'<h2 class="seccion-titulo">{esc(titulo)}</h2>' + (f'<p class="seccion-sub">{esc(sub)}</p>' if sub else "")


# ------------------------------------------------------------- barra lateral
def postura(ind: dict | None, desde: float) -> str:
    if not ind:
        return (f'<div class="marca">{NOMBRE_AGENTE}</div><p class="leyenda">Agente consultor de CIS Controls v8.1 IG1. '
                'Carga el PDF de contexto para comenzar.</p>')
    impl = ind["implementacion"]
    hasta = impl or 0.0
    cifra = f"{impl:.0f}<small>%</small>" if impl is not None else "—"
    conteos = "".join(f'<li>{_marca(e)}{ETIQUETA_CORTA[e]}<b>{ind[e]}</b></li>' for e in ESTADOS)
    return (f'<div class="marca">{NOMBRE_AGENTE}</div>'
            f'<div class="postura"><div class="anillo" role="img" aria-label="Implementación IG1 {esc(formato_pct(impl))}" '
            f'style="--desde:{desde:.1f};--hasta:{hasta:.1f}"><span class="halo" aria-hidden="true"></span>'
            f'<span class="arco" aria-hidden="true"></span><div class="cifra"><b>{cifra}</b><span>implementación</span></div></div>'
            f'<ul class="conteos">{conteos}</ul></div>'
            f'<p class="leyenda">Cobertura de la evaluación: <b>{esc(formato_pct(ind["cobertura"]))}</b></p>')


def matriz_controles(estados: dict[str, str], cambiados: set[str]) -> str:
    celdas = ""
    for c in catalogo().controles:
        e = estados[c.id]
        etiqueta = "Sin salvaguardas IG1" if e == "sin_ig1" else ETIQUETA[e]
        celdas += (f'<div class="celda {e}{" cambio" if c.id in cambiados else ""}" style="{_c(e)}" '
                   f'title="{c.id} · {esc(c.nombre)} — {etiqueta}" role="listitem" aria-label="{esc(c.nombre)}: {etiqueta}">{c.id}</div>')
    return (f'<div class="matriz" role="list" aria-label="Estado por control">{celdas}</div>'
            f'<p class="leyenda">18 Controles CIS. Los controles 13, 16 y 18 no tienen salvaguardas IG1.</p>')


# ------------------------------------------------------------ ficha de contexto
def _evidencia_hallazgo(h: dict, doc_etiqueta: str) -> str:
    pagina = f"p. {h.get('pagina')}" if h.get("pagina") else "s/p"
    if h.get("verificada"):
        return f'<span class="ev ok" title="Cita verificada en el documento">✓ {doc_etiqueta} · {pagina}</span>'
    return f'<span class="ev mal" title="La cita no aparece en el documento">✗ cita no encontrada</span>'


def ficha(f: dict, doc_etiqueta: str = "PDF 1") -> str:
    dims = ""
    for clave, nombre, que in DIMENSIONES:
        d = f.get("dimensiones", {}).get(clave, {})
        hallazgos = "".join(f'<li>{esc(h.get("dato"))}{_evidencia_hallazgo(h, doc_etiqueta)}</li>' for h in d.get("hallazgos", []))
        falta = f'<p class="falta">Falta: {esc(d.get("faltante"))}</p>' if d.get("faltante") else ""
        dims += (f'<div class="dim"><h4>{nombre}</h4><p class="que">{que}</p><p>{esc(d.get("resumen"))}</p>'
                 f'<ul>{hallazgos or "<li class=vacio>Sin información en el documento.</li>"}</ul>{falta}</div>')
    faltante = "".join(f"<li>{esc(x)}</li>" for x in f.get("informacion_faltante", [])) or "<li>Nada relevante.</li>"
    ambig = "".join(f"<li>{esc(x)}</li>" for x in f.get("ambiguedades", [])) or "<li>No se detectaron.</li>"
    p = f.get("perfil_riesgo", {})
    amenazas = "".join(
        f'<li><span class="chip impacto {esc(a.get("impacto"))}">{IMPACTO.get(a.get("impacto"), "")}</span>'
        f'<b>{esc(a.get("amenaza"))}</b><span class="razon">{esc(a.get("por_que_en_este_negocio"))}</span>'
        f'<span class="chips">{_chips(a.get("controles", []))}</span></li>' for a in p.get("amenazas", []))
    return (f'<section class="ficha" aria-label="Ficha de contexto">'
            f'<p class="ficha-resumen">{esc(f.get("resumen_contexto") or f.get("resumen_ejecutivo"))}</p>'
            f'<div class="dims">{dims}</div>'
            f'<div class="listas"><div><h4>Información faltante</h4><ul>{faltante}</ul></div>'
            f'<div><h4>Contradicciones o ambigüedades</h4><ul>{ambig}</ul></div></div>'
            f'<section class="perfil en-reporte"><div class="perfil-top"><h3>Perfil de riesgo</h3><div class="chips">'
            f'<span class="chip">{esc(p.get("sector"))}</span><span class="chip">{TAMANO.get(p.get("tamano"), "")}</span>'
            f'<span class="chip ig">Alcance IG1</span></div></div>'
            f'<h4>Amenazas prioritarias para este negocio</h4><ul class="amenazas">{amenazas}</ul></section></section>')


# ------------------------------------------------------------------ tablero
def _delta(a, b) -> str:
    if a is None or b is None:
        return ""
    d = b - a
    clase = "cero" if abs(d) < 0.05 else ("neg" if d < 0 else "")
    return f'<div class="delta {clase}">{"+" if d > 0 else ""}{d:.1f} pts vs v1</div>'


def tablero(ind: dict, riesgos: int | None = None, iniciativas: int | None = None, previo: dict | None = None) -> str:
    def cifra(v):
        return f'<b>{v:.1f}%</b>' if v is not None else '<b class="nd">No determinable</b>'

    cob_d = _delta(previo["cobertura"], ind["cobertura"]) if previo else ""
    imp_d = _delta(previo["implementacion"], ind["implementacion"]) if previo else ""
    conteos = "".join(f'<span>{_marca(e)}{ETIQUETA[e]} <b>{ind[e]}</b></span>' for e in ESTADOS)
    return (f'<div class="tablero">'
            f'<div>{cifra(ind["cobertura"])}<span>Cobertura IG1</span><small>Salvaguardas evaluadas con información suficiente</small>{cob_d}</div>'
            f'<div>{cifra(ind["implementacion"])}<span>Implementación IG1</span><small>Sobre {ind["evaluables"]} salvaguardas evaluables</small>{imp_d}</div>'
            f'<div><b>{riesgos if riesgos is not None else "—"}</b><span>Riesgos prioritarios</span><small>Identificados para revisión</small></div>'
            f'<div><b>{iniciativas if iniciativas is not None else "—"}</b><span>Iniciativas</span><small>Roadmap propuesto</small></div></div>'
            f'<div class="conteo-estados">Total <b>{ind["total"]}</b>{conteos}</div>')


# ------------------------------------------------------------------ matriz 56
def matriz56(version, documentos: dict, resaltar: set[str] = frozenset()) -> str:
    filas = ""
    for c in catalogo().controles:
        if not c.ig1:
            filas += f'<tr class="grupo"><td colspan="8"><span class="mono">{c.id}</span>{esc(c.nombre)} — sin salvaguardas IG1</td></tr>'
            continue
        filas += f'<tr class="grupo"><td colspan="8"><span class="mono">{c.id}</span>{esc(c.nombre)} · {esc(c.titulo_oficial)}</td></tr>'
        for s in c.ig1:
            r = version.matriz[s.id]
            cita = f"«{esc(r.cita)}»" if r.cita else ""
            filas += (f'<tr class="{"cambio" if s.id in resaltar else ""}"><td class="id">{s.id}</td><td class="titulo">{esc(s.titulo)}</td>'
                      f'<td>{ETIQUETA_APLICABILIDAD[r.aplicabilidad]}</td><td>{_estado(r.estado)}</td>'
                      f'<td>{esc(r.justificacion)}</td><td class="ev">{esc(r.evidencia(documentos))}</td>'
                      f'<td class="cita">{cita}</td><td class="obs">{esc(r.observaciones)}</td></tr>')
    return (f'<div class="tabla-envoltura"><table class="matriz56"><thead><tr><th>ID CIS</th><th>Salvaguarda</th><th>Aplicabilidad</th>'
            f'<th>Estado</th><th>Justificación</th><th>Evidencia</th><th>Cita</th><th>Observaciones</th></tr></thead>'
            f'<tbody>{filas}</tbody></table></div>')


# --------------------------------------------------------- resumen ejecutivo
def resumen_ejecutivo(res: dict) -> str:
    brechas = "".join(
        f'<li><b>{esc(b.get("control_id"))} · {esc(control(b["control_id"]).nombre) if b.get("control_id") in catalogo().por_id else ""}</b>'
        f' — {esc(b.get("explicacion"))}</li>' for b in res.get("controles_mayores_brechas", []))
    faltante = "".join(f"<li>{esc(x)}</li>" for x in res.get("informacion_faltante", []))
    return (f'<div class="resumen-ej">'
            f'<div><h4>Postura de ciberseguridad</h4><p>{esc(res.get("postura_inicial"))}</p></div>'
            f'<div><h4>Controles CIS con mayores brechas</h4><ul>{brechas or "<li>Sin brechas confirmadas.</li>"}</ul></div>'
            f'<div><h4>Información que falta para mayor certeza</h4><ul>{faltante or "<li>—</li>"}</ul></div>'
            f'<div><h4>Principales riesgos</h4><p>{esc(res.get("principales_riesgos"))}</p></div>'
            f'<div class="preliminar"><h4>Resultados preliminares</h4><p>{esc(res.get("resultados_preliminares"))}</p></div></div>')


def riesgos(lista: list[dict], situacion: list[dict] | None = None) -> str:
    filas = ""
    for i, r in enumerate(lista, 1):
        sit = ""
        if situacion and i <= len(situacion):
            s = situacion[i - 1]
            clave = s.get("situacion") if s.get("situacion") in SITUACION_RIESGO else "permanece"
            residual = s.get("severidad_residual")
            sit = (f'<td><span class="chip sev {"baja" if clave != "permanece" else "alta"}">{SITUACION_RIESGO[clave]}</span>'
                   + (f' <span class="chip sev {esc(residual)}">Residual: {esc(residual.capitalize())}</span>' if residual else "")
                   + f'<br>{esc(s.get("explicacion"))}</td>')
        filas += (f'<tr><td><b>{i}. {esc(r.get("titulo"))}</b><br>{esc(r.get("descripcion"))}</td>'
                  f'<td>{esc(r.get("activo_proceso"))}</td><td>{esc(r.get("deficiencia"))}</td><td>{esc(r.get("consecuencia"))}</td>'
                  f'<td><span class="chip sev {esc(r.get("severidad"))}">{esc((r.get("severidad") or "").capitalize())}</span>'
                  f'<br>{esc(r.get("justificacion"))}</td><td>{_chips(r.get("salvaguardas", []))}</td>{sit}</tr>')
    extra = "<th>Tras las mejoras</th>" if situacion else ""
    return (f'<div class="tabla-envoltura"><table class="tabla"><thead><tr><th>Riesgo</th><th>Activo o proceso</th><th>Deficiencia</th>'
            f'<th>Consecuencia probable</th><th>Severidad y justificación</th><th>Salvaguardas</th>{extra}</tr></thead>'
            f'<tbody>{filas}</tbody></table></div>')


def roadmap(lista: list[dict], titulos_riesgos: list[str], estados: list[dict] | None = None) -> str:
    filas = ""
    for i, ini in enumerate(lista):
        rs = ", ".join(f"{n}. {titulos_riesgos[n - 1]}" for n in ini.get("riesgos", []) if 0 < n <= len(titulos_riesgos))
        tipo = ini.get("tipo")
        est = ""
        if estados and i < len(estados):
            e = estados[i]
            est = f'<td><b>{ESTADO_INICIATIVA.get(e.get("estado"), "")}</b><br>{esc(e.get("explicacion"))}</td>'
        filas += (f'<tr><td><b>{ini.get("prioridad")}</b></td><td><b>{esc(ini.get("titulo"))}</b><br>{esc(ini.get("descripcion"))}</td>'
                  f'<td>{esc(rs)}</td><td>{_chips(ini.get("salvaguardas", []))}</td><td>{esc(ini.get("beneficio"))}</td>'
                  f'<td>{esc((ini.get("esfuerzo") or "").capitalize())}</td>'
                  f'<td><span class="chip tipo {esc(tipo)}">{"Quick win" if tipo == "quick_win" else "Inversión o proyecto"}</span></td>{est}</tr>')
    extra = "<th>Estado</th>" if estados else ""
    return (f'<div class="tabla-envoltura"><table class="tabla"><thead><tr><th>Prioridad</th><th>Iniciativa</th><th>Riesgo que reduce</th>'
            f'<th>Salvaguardas</th><th>Beneficio esperado</th><th>Esfuerzo</th><th>Clasificación</th>{extra}</tr></thead>'
            f'<tbody>{filas}</tbody></table></div>')


# ---------------------------------------------------------------- PDF 2
def iniciativas_pdf2(lista: list[dict]) -> str:
    tarjetas = ""
    for ini in lista:
        ev = "".join(
            f'<li>{("<span class=mono>" + esc(e.get("salvaguarda")) + "</span> ") if e.get("salvaguarda") else ""}'
            f'«{esc(e.get("cita"))}» <span class="ev {"ok" if e.get("verificada") else "mal"}">'
            f'{"✓ PDF 2 · p. " + str(e.get("pagina")) if e.get("verificada") else "✗ cita no encontrada"}</span></li>'
            for e in ini.get("evidencia", []))
        tarjetas += (f'<article class="ini"><h4>{esc(ini.get("nombre"))}</h4>'
                     f'<p><b>Qué mejoró</b>{esc(ini.get("que_mejoro"))}</p>'
                     f'<p><b>Mejora</b>{"Completa" if ini.get("alcance") == "completa" else "Parcial"}</p>'
                     f'<p><b>Salvaguardas relacionadas</b></p><div class="chips">{_chips(ini.get("salvaguardas", []))}</div>'
                     f'<p style="margin-top:10px"><b>Evidencia</b></p><ul class="salv-lista">{ev}</ul>'
                     f'<p style="margin-top:10px"><b>Pendiente</b>{_pendientes(ini.get("pendientes"))}</p>'
                     f'<p><b>Riesgos que podría reducir</b>{esc("; ".join(ini.get("riesgos_que_reduce", [])))}</p></article>')
    return f'<div class="inis">{tarjetas}</div>'


def _pendientes(pend) -> str:
    """Pendientes del PDF 2: cada uno indica a qué salvaguardas afecta (F2). Acepta el formato antiguo (texto)."""
    if not pend:
        return "Ninguno"
    if isinstance(pend, str):
        return esc(pend)
    return "<br>".join(f'{esc(x.get("detalle"))} → {esc(", ".join(x.get("salvaguardas", [])) or "ninguna salvaguarda IG1")}'
                       for x in pend)


MOTIVO_SIN_CAMBIO = {"sin_evidencia": "Sin evidencia", "evidencia_parcial": "Evidencia parcial",
                     "pendiente_declarado": "Pendiente declarado", "sin_mejora": "Sin mejora",
                     "sin_decision": "El agente no decidió"}


def sin_cambio(lista: list[dict]) -> str:
    filas = "".join(f'<tr><td class="mono">{esc(x.get("id"))}</td>'
                    f'<td>{esc(salvaguarda(x["id"]).titulo if salvaguarda(x.get("id")) else "")}</td>'
                    f'<td><b>{MOTIVO_SIN_CAMBIO.get(x.get("motivo"), esc(x.get("motivo")))}</b></td>'
                    f'<td>{esc(x.get("detalle"))}</td><td>{esc(x.get("iniciativa"))}</td></tr>' for x in lista)
    return (f'<div class="tabla-envoltura"><table class="tabla"><thead><tr><th>ID</th><th>Salvaguarda</th><th>Motivo</th>'
            f'<th>Detalle</th><th>Iniciativa</th></tr></thead><tbody>{filas}</tbody></table></div>')


def cambio_fila(c) -> str:
    cita = (f'«{esc(c.cita)}» <span class="ev ok">✓ PDF 2 · p. {c.pagina}</span>' if c.cita_verificada
            else '<span class="ev mal">✗ sin evidencia verificable: no se puede aprobar</span>')
    if getattr(c, "tipo", "estado") == "evidencia":   # F9: mismo estado, evidencia nueva
        cambio = f'<span>{_estado(c.estado_inicial)} · actualización de evidencia</span>'
    else:
        cambio = f'<span>{_estado(c.estado_inicial)}<span class="flecha">→</span>{_estado(c.estado_propuesto)}</span>'
    return (f'<div class="respuesta" style="margin-left:0;{_c(c.estado_propuesto)}"><span class="mono">{c.id}</span>'
            f'<span class="nombre">{esc(salvaguarda(c.id).titulo if salvaguarda(c.id) else c.id)}</span>{cambio}</div>'
            f'<p class="aviso" style="margin:6px 0 2px 14px">{esc(c.justificacion)} · Iniciativa: {esc(c.iniciativa)}</p>'
            f'<p class="aviso" style="margin:0 0 4px 14px">{cita}</p>')


def comparacion(i1: dict, i2: dict, modificados: list[str]) -> str:
    def fila(nombre, a, b, pct=False):
        fa = formato_pct(a) if pct else str(a)
        fb = formato_pct(b) if pct else str(b)
        return f"<tr><td>{nombre}</td><td>{fa}</td><td>{fb}</td></tr>"
    filas = (fila("Cobertura IG1", i1["cobertura"], i2["cobertura"], True)
             + fila("Implementación IG1", i1["implementacion"], i2["implementacion"], True)
             + "".join(fila(ETIQUETA[e], i1[e], i2[e]) for e in ESTADOS))
    return (f'<div class="tabla-envoltura"><table class="tabla" style="min-width:420px"><thead><tr><th>Indicador</th>'
            f'<th>v1 · Inicial</th><th>v2 · Actualizada</th></tr></thead><tbody>{filas}</tbody></table></div>'
            f'<p class="seccion-sub" style="margin-top:10px">Salvaguardas modificadas: {esc(", ".join(modificados) or "ninguna")}</p>')


def tema_script() -> str:
    """Sincroniza las piezas propias con el tema que Streamlit aplicó (Día o Noche): lee el fondo real de la app y
    pone data-theme en la raíz. Se revisa cada 400 ms porque Streamlit no avisa cuando cambia el tema."""
    return ('<script>(() => { if (window.__ctTema) return; window.__ctTema = true;'
            'const leer = () => { const el = document.querySelector(".stApp") || document.body;'
            ' const m = getComputedStyle(el).backgroundColor.match(/[\\d.]+/g); if (!m) return;'
            ' const [r, g, b] = m.map(Number); const oscuro = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.45;'
            ' const t = oscuro ? "dark" : "light"; if (document.documentElement.dataset.theme !== t) {'
            '  document.documentElement.dataset.theme = t; document.dispatchEvent(new Event("ct-tema")); } };'
            'leer(); setInterval(leer, 400); })();</script>')


def selector_tema(deshabilitado: bool = False) -> str:
    """Selector Día/Noche. Guarda la elección donde Streamlit la lee (localStorage) y recarga la página; app.py
    conserva la evaluación y la sección abiertas en la URL, así que se vuelve al mismo lugar."""
    dis = " disabled" if deshabilitado else ""
    return (f'<div class="tema-selector" role="group" aria-label="Tema de la interfaz">'
            f'<button type="button" data-tema="Light" aria-pressed="false"{dis}>Día</button>'
            f'<button type="button" data-tema="Dark" aria-pressed="false"{dis}>Noche</button></div>'
            '<script>(() => { document.querySelectorAll(".tema-selector:not([data-listo])").forEach(g => { g.dataset.listo = "1";'
            'const marcar = () => { const t = document.documentElement.dataset.theme === "dark" ? "Dark" : "Light";'
            ' g.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.tema === t))); };'
            'marcar(); document.addEventListener("ct-tema", marcar);'
            'g.querySelectorAll("button").forEach(b => b.addEventListener("click", () => {'
            ' if (b.disabled || b.getAttribute("aria-pressed") === "true") return;'
            ' try { localStorage.setItem("stActiveTheme-" + location.pathname + "-v2", JSON.stringify(b.dataset.tema)); } catch (e) { return; }'
            ' location.reload(); })); }); })();</script>')


def subir_al_inicio() -> str:
    """Lleva la página al inicio (se inserta solo al cambiar de sección). Se repite tras unos instantes porque
    Streamlit dibuja la página por partes. El sello de tiempo hace que el bloque sea nuevo y el script se ejecute."""
    return (f'<script data-t="{time.time_ns()}">(() => {{'
            'const subir = () => {'
            ' const m = document.querySelector(\'[data-testid="stMain"]\');'
            ' [window, document.scrollingElement, m, m && m.parentElement,'
            '  document.querySelector(\'[data-testid="stAppViewContainer"]\')]'
            '  .forEach(e => e && e.scrollTo && e.scrollTo({top: 0, behavior: "instant"}));'
            '};'
            'subir(); [60, 200, 450].forEach(ms => setTimeout(subir, ms));'
            '})();</script>')


def tarjeta_progreso(titulo: str, texto: str) -> str:
    return (f'<div class="barra carga" aria-hidden="true"><i style="--p:1"></i></div>'
            f'<div class="progreso" role="status" aria-live="polite"><span class="pulso" aria-hidden="true"></span>'
            f'<div><p class="verif-fin-titulo">{esc(titulo)}</p><p class="verif-fin-texto">{esc(texto)}</p></div></div>')


def tarjeta_completada(titulo: str, texto: str) -> str:
    return (f'<div class="barra carga" aria-hidden="true"><i style="--p:1"></i></div>'
            f'<div class="verif-fin" role="status" aria-live="polite"><span class="check" aria-hidden="true"><i></i></span>'
            f'<div><p class="verif-fin-titulo">{esc(titulo)}</p><p class="verif-fin-texto">{esc(texto)}</p></div></div>')


def consumo(filas: list[dict]) -> str:
    """Tokens por llamada: la caché aparece como lectura (barata) o escritura; el costo es una estimación."""
    def n(x):
        return f"{x:,}".replace(",", " ")
    cuerpo = "".join(f'<tr><td>{esc(f["etapa"])}</td><td class="mono">{n(f["entrada"])}</td>'
                     f'<td class="mono">{n(f["cache_leida"])}</td><td class="mono">{n(f["cache_escrita"])}</td>'
                     f'<td class="mono">{n(f["salida"])}</td><td class="mono">{f["usd"]:.3f}</td></tr>' for f in filas[-30:])
    leida = sum(f["cache_leida"] for f in filas)
    total = leida + sum(f["entrada"] + f["cache_escrita"] for f in filas)
    return (f'<p class="aviso">Entrada servida desde caché: {100 * leida / total if total else 0:.0f}%</p>'
            f'<div class="tabla-envoltura"><table class="tabla"><thead><tr><th>Etapa</th><th>Entrada</th><th>Caché leída</th>'
            f'<th>Caché escrita</th><th>Salida</th><th>US$</th></tr></thead><tbody>{cuerpo}</tbody></table></div>')


def avisos(lista: list[str]) -> str:
    return "".join(f'<p class="aviso">· {esc(a)}</p>' for a in lista[-40:]) or '<p class="aviso">Sin avisos.</p>'


def atribucion_html(texto: str) -> str:
    return f'<p class="atribucion">Criterios basados en {esc(texto)} Los textos de CIS se usan sin modificar.</p>'
