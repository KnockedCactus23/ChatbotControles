# ChatbotControles — "Centinela IG1", agente de evaluación CIS Controls v8.1 IG1

## Qué es
Agente de IA para la actividad **M3.6** (diseño de un agente para la evaluación integral de CIS Controls v8.1 — IG1). Actúa como consultor de ciberseguridad:
1. **Etapa 1:** identidad, alcance, reglas R1–R12 y escala en un **prompt maestro** (`prompts.prompt_maestro()`). Se entrega como archivo (`scripts/exportar_prompt.py` → `docs/prompt_maestro_centinela_ig1.md`), **no** como botón de la app: la actividad lo pide como entregable, no como función. Prueba preliminar: `engine.explain()`.
2. **Etapa 2:** lee el **PDF 1** (contexto) y genera la **ficha de contexto** en 10 dimensiones con página y cita por hallazgo. El equipo la valida; los ajustes se registran (`Proyecto.ajustes`).
3. **Etapa 3:** evalúa las **56 salvaguardas IG1** (3 lotes por control) → matriz con aplicabilidad, 5 estados, justificación, evidencia, cita y observaciones; indicadores con las fórmulas oficiales.
4. **Etapas 3.5–4:** resumen ejecutivo (postura, controles con mayores brechas, información faltante, riesgos, resultados preliminares), **5 riesgos**, **5 iniciativas** (quick win / proyecto) y dashboard. Cierra la **v1**.
5. **Etapa 5:** lee el **PDF 2**, propone cambios con cita; el auditor aprueba, rechaza o deja pendiente; se crea la **v2** solo con los aprobados y su reporte comparativo.
6. **Sin preguntas Sí/No al cliente** (decisión del equipo, 2026-11-17: apegarse a la actividad). Solo cuenta la evidencia documental. Al cargar evaluaciones antiguas, `Proyecto._descartar_declaraciones()` devuelve a No verificado las respuestas Sí/No (`fuente == "declaracion"`). No reintroducir preguntas sin preguntar al equipo.
7. **Chat de consultas** (`engine.ask`, solo lectura, no cambia estados): la entrada solo existe en la ficha de contexto ya generada y en los reportes (`reporte`, `actualizado`) — `CHAT_ACTIVO` en `app.py`. El historial se muestra siempre (ahí salen la prueba preliminar y los errores). Usa la **vista** (no la etapa), así que también funciona al consultar la ficha o el reporte inicial desde etapas posteriores.
8. **Navegación entre secciones** (`st.segmented_control`, clave `vista`; decisión del equipo, 2026-11-17): siempre Contexto, Reporte inicial y Reporte actualizado (estos dos cuando existen). La Evaluación 56 y la Validación PDF 2 solo aparecen mientras son el paso en curso. Las vistas de etapas pasadas son de **solo lectura**: no se regenera la ficha ni se sube el PDF 2 desde ellas, para no romper R10–R12. Al avanzar de etapa (`etapa_vista`), la vista pasa al paso nuevo. En los reportes las matrices van **plegadas** (`st.expander`) porque alargan mucho la página: la v1 en el reporte inicial, y la v2 y la v1 en pestañas en el actualizado. Solo en la Evaluación 56 en curso la matriz va abierta.

Proyecto académico de equipo. **Decisión del equipo (2026-11-03): usa la API gratuita de Google Gemini** con el SDK oficial `google-genai`. No mezclar otros proveedores ni capas como LangChain. Este archivo se llama CLAUDE.md solo porque es la configuración de Claude Code (asistente de desarrollo).

## Decisiones del equipo (no cambiarlas sin preguntar)
- Alcance: **solo IG1** (56 salvaguardas; están en 15 controles: 13, 16 y 18 no tienen IG1). `controls.IG_EVALUADO = 1`.
- **Única referencia normativa: CIS v8.1 IG1 (R2).** ISO 27002 se eliminó por completo.
- Nombre del agente: **Centinela IG1** (`prompts.NOMBRE_AGENTE`).
- Guardado automático local en `evaluaciones/` (ignorado por git) para conservar v1 y v2 entre semanas.
- Escala obligatoria: `implementado`=1, `parcial`=0.5, `no_implementado`=0, `no_verificado`=—, `no_aplicable`=—.
- Sin botón de descarga del prompt maestro en la UI (2026-11-17); el chat solo en contexto con ficha y en reportes (2026-11-17).
- **Entregables separados por versión** (2026-11-17), sin mezclarse:
  - Contexto: solo la ficha (PDF/HTML).
  - Reporte inicial: matriz v1, Excel v1 y reporte inicial.
  - Reporte actualizado: matriz v2, Excel v2 y reporte final.
  - El Excel v2 y el reporte final no repiten la matriz v1 ni el reporte inicial; solo comparan indicadores.

## Stack
- Python 3.14 (el `python3` del sistema es 3.15 y algunas dependencias aún no tienen wheels).
- `google-genai`, `streamlit`, `python-dotenv`, `openpyxl` (importador y Excel), `pypdf` (texto del PDF para verificar citas), `fpdf2` (reporte ejecutivo en PDF; fuentes estándar con cp1252, sin fuentes del sistema).
- Modelo por defecto `gemini-3.5-flash-lite` (`GEMINI_MODEL` en `.env`; el equipo usa `gemini-3.1-flash-lite` cuando el otro está saturado). No usar `gemini-2.5-flash` (obsoleto desde 2026-12-01).
- Plan gratuito: límites por minuto/día y **Google puede usar el contenido**: usar casos ficticios o los del profesor.

## Estructura
```
app.py                     # UI por etapas; tareas lentas con pedir() y ejecución al FINAL del script
chatbot/
  controls.py              # Catálogo CIS IG1 desde data/cis_v8_1_2.json; nombres en español del equipo
  documentos.py            # Documento (páginas de texto), leer_pdf(), verificar_cita()
  state.py                 # Resultado, Version, Cambio, Proyecto; validar_resultado(), indicadores(), validar_reporte()
  prompts.py               # Prompt maestro (identidad, alcance, R1–R12, escala) + tarea por etapa; DIMENSIONES
  schemas.py               # JSON Schemas por etapa (minItems/maxItems para 56 por lote, 5 riesgos, 5 iniciativas)
  engine.py                # explain, context_sheet, evaluate, report, analyze_initiatives, updated_report, ask
  almacen.py               # guardar/cargar/listar proyectos en evaluaciones/ (EVALUACIONES_DIR para pruebas)
  exportar.py              # excel(p, "v1"|"v2"), reporte_html(p, "v1"|"v2"), csv_matriz, ficha_html (_pagina_html); prompt_maestro_md()
  reporte_pdf.py           # reporte_pdf(p, "v1"|"v2") (Entregable 3; cada uno debe caber en 5 páginas, lo verifica test_motor) y ficha_pdf()
  ui.py                    # Tokens CSS (OKLCH) y piezas HTML
  data/cis_v8_1_2.json     # NO versionado (licencia CC BY-NC-ND): scripts/importar_cis.py
scripts/importar_cis.py    # Excel oficial CIS v8.1.x → JSON (reconstruye ids como 3.10 que Excel guarda como 3.1)
scripts/exportar_prompt.py # Entregable 1 → docs/prompt_maestro_centinela_ig1.md (sin catálogo CIS; sí se versiona)
docs/                      # Prompt maestro generado; regenerarlo si cambia prompts.py
PROGRESS.md                # Avance del proyecto y pendientes; actualizarlo al cerrar cada bloque de trabajo
tests/                     # conftest (catálogo falso: 18 IG1), test_state (reglas/penalizaciones), test_motor (flujo), importador, reintentos
```

## Reglas que el CÓDIGO hace cumplir (no depender solo del prompt)
- **Nunca omitir salvaguardas:** `Proyecto.completar_faltantes()`; el esquema exige una evaluación por id del lote.
- **No inventar evidencia (R3, R6):** `validar_resultado()` exige cita verificable (`verificar_cita`, umbral 0.8 de palabras) para Implementado/Parcial/No implementado/No aplicable; si no, → No verificado y aviso en `Proyecto.avisos` (bitácora visible).
- **R8:** "No implementado" sin cita → No verificado.
- **Indicadores:** solo `state.indicadores()`; el modelo recibe los números y no los recalcula. `None` → "No determinable".
- **Coherencia informe ↔ matriz:** `validar_reporte()` quita de riesgos/iniciativas las salvaguardas que no son brecha y fija los "controles con mayores brechas" a la lista calculada (`brechas_por_control`).
- **R10–R12:** v1 inmutable una vez `cerrada`; `crear_v2()` copia v1 y aplica solo `Cambio.decision == "aprobado"`; no se puede aprobar sin cita verificada en el PDF 2 (`Cambio.aprobable`).
- **Etapa 5, una decisión por salvaguarda relacionada (F1):**
  - Tipos: `cambio_estado` (mejora o empeoramiento), `actualizar_evidencia` (`Cambio.tipo == "evidencia"`: mismo estado, cita nueva; F9) o `sin_cambio` (va a `Proyecto.sin_cambio` con motivo).
  - Si el modelo omite alguna, `analyze_initiatives` hace una segunda pasada con `schemas.decisiones_faltantes(ids)`, que exige una por id. Lo que siga faltando queda como `sin_decision` en la bitácora.
  - Los pendientes llevan sus salvaguardas (F2). Las alertas del documento van a `Proyecto.alertas` (C1, C2).
- **Etapa 5.6, la situación la calcula el código (F4–F6):**
  - `situacion_riesgos()`: mitigado, reducido o permanece, con severidad residual. Solo cuentan las salvaguardas propias de cada riesgo.
  - `estado_iniciativas()`: completada, en progreso o pendiente.
  - Sobrescriben lo que diga el modelo, que solo redacta explicaciones. El modelo recibe por separado los cambios aprobados y los no aprobados (F3).
  - `riesgos_v2` (5 vigentes) es la lista a la que apunta el roadmap v2 (F7).
- **Validaciones del reporte (F10):** `validar_reporte()`
  - completa con la matriz las explicaciones vacías de brechas;
  - señala riesgos apoyados solo en No verificado (B1) y riesgos o iniciativas sin ninguna brecha;
  - registra campos vacíos.
  - Aparte, `citas_repetidas()` señala una misma cita usada en varias salvaguardas (A2).
- La ficha usa `resumen_contexto` (D5); `normalizar_ficha()` convierte las guardadas con `resumen_ejecutivo`.
- Reproducibilidad (R9): temperatura 0 y `SEMILLA` fija.

## Convenciones
- Código y comentarios en español; identificadores sin acentos.
- El estado en Python es la fuente de verdad; Gemini propone y Python valida.
- Salida estructurada siempre (`response_mime_type="application/json"` + `response_json_schema`); validar en Python con `.get()`.
- Nunca escribir la API key en el código ni subir `.env`.
- **Licencia CIS (CC BY-NC-ND 4.0):** nunca versionar ni traducir/modificar los textos de CIS; se usan en inglés tal cual. El prompt maestro exportado NO incluye el catálogo. Mostrar `controls.atribucion()`.
- Las pruebas usan un catálogo falso (`CIS_CATALOGO`); no dependen del Excel ni del JSON real.
- Gemini gratuito: latencia muy variable. `REINTENTOS` (SDK) cubre 429/5xx/timeouts y conexión; `TIMEOUT_S`=30 y `TIMEOUT_LARGO_S`=120 (PDF/salidas largas) por intento. El SDK ya reintenta timeouts: no añadir un bucle propio.
- Tareas lentas en la UI: `pedir(tipo)` → rerun con controles deshabilitados → se ejecutan al final del script con la tarjeta de progreso en `lugar_progreso`.

## Diseño (UI)
- Arquetipo "craft oscuro"; colores de los 5 estados en tokens `--st-implementado`, `--st-parcial`, `--st-no_implementado`, `--st-no_verificado`, `--st-no_aplicable`. No hex sueltos.
- `st.html` sanitiza: **elimina `<svg>`** y **descarta un `<style>` completo si contiene `<`** (incluso en comentarios; usar `\3c`).
- Todo texto de Gemini o del usuario pasa por `ui.esc()`.
- **`st.chat_input` nunca en la raíz**, siempre dentro de `st.container(key="chat")`. En la raíz, Streamlit lo fija abajo y activa "pegarse al final" (`stAppScrollToBottomContainer`), que arrastra la página hasta abajo al cambiar de sección o abrir un plegable.
- Al cambiar de sección se sube al inicio con `ui.subir_al_inicio()` (`st.html(..., unsafe_allow_javascript=True)`), solo cuando cambia `vista_mostrada`.
- Respetar `prefers-reduced-motion`; revisar en 375px y escritorio.

## Comandos
```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/importar_cis.py "ruta/CIS_Controls_Version_8.1.2___March_2025.xlsx"   # genera el catálogo local
cp .env.example .env            # y poner GEMINI_API_KEY (gratis en aistudio.google.com/apikey)
streamlit run app.py
python -m pytest -q             # 31 pruebas sin API
python scripts/exportar_prompt.py   # regenera docs/prompt_maestro_centinela_ig1.md
```

## Forma de trabajo con Claude Code (obligatorio)
- **Notificar al usuario después de terminar cada cambio**: al acabar cada archivo o cambio relevante, decir en el chat qué se cambió y por qué, en una o dos líneas.
- **Notificar y preguntar en cada decisión**: ante cualquier decisión de diseño no trivial (librería, estructura, modelo, cambio de flujo, borrar archivos), preguntar al usuario antes de actuar, o, si es un default obvio, avisar explícitamente qué se decidió. Los hooks (en `.claude/settings.json`, local: `.claude/` está en `.gitignore`) notifican cuando Claude espera una respuesta o un permiso.
- Responder en español.
