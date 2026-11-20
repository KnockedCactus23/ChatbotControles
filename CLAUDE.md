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
8. **Navegación entre secciones** (`st.segmented_control`, clave `vista`; decisión del equipo, 2026-11-17): siempre Contexto, Reporte inicial y Reporte actualizado (estos dos cuando existen). La Evaluación 56 y la Validación PDF 2 solo aparecen mientras son el paso en curso. Las vistas de etapas pasadas son de **solo lectura**: no se regenera la ficha ni se sube el PDF 2 desde ellas, para no romper R10–R12. Al avanzar de etapa (`etapa_vista`), la vista pasa al paso nuevo. En los reportes las matrices van **plegadas** (`<details>` de `panel.matriz`, con filtros por estado) porque alargan mucho la página: la v1 en el reporte inicial, y la v2 y la v1 (dos plegables) en el actualizado. Solo en la Evaluación 56 en curso la matriz va abierta (`abierta=True`).

Proyecto académico de equipo. **Decisión del equipo (2026-11-17): usa la API de Claude** con el SDK oficial `anthropic` (antes era Gemini gratuito; se cambió por la calidad del razonamiento). No mezclar otros proveedores ni capas como LangChain. Este archivo se llama CLAUDE.md solo porque es la configuración de Claude Code (asistente de desarrollo).

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
- **Vista ejecutiva y vista técnica** (2026-11-19; plan por fases, en curso: Fases 1 a 4 listas). Lo que sale de la ejecutiva se queda en la técnica. Decisiones:
  - Áreas fijas en `controls.AREAS`: 7 grupos de controles; la madurez por área usa la fórmula global (`state.madurez_por_area`).
  - La **severidad la calcula el código**: probabilidad × impacto (1-5 cada uno; ≥15 alta, 8-14 media, <8 baja; `state.severidad_de`). El modelo ya no la escribe.
  - Campos ejecutivos sin IDs ni jerga (`veredicto`, `impactos_negocio`, `peticiones`, `consecuencia_negocio`): `state.validar_ejecutivo` descarta impactos con cifras que no están en la ficha ni en la matriz y señala jerga en la bitácora.
  - Proyección «hoy → estimado» (`state.proyeccion`) suponiendo implementadas las salvaguardas de las iniciativas; siempre se rotula «estimación».
  - Evaluaciones anteriores: horizonte deducido del tipo (`horizonte_de`, marcado como estimación) y nivel de riesgo desde la severidad más alta (`nivel_riesgo`); el mapa de riesgos, los impactos y las peticiones se ocultan con aviso.
  - Selector «Ejecutivo / Técnico» (`st.segmented_control`, clave `modo`, en la URL `?modo=`) junto al título de los dos reportes; Ejecutivo por defecto. La vista ejecutiva vive en `chatbot/ejecutiva.py` (clases `e-`): veredicto, 3 indicadores, qué está en juego, estado por control (barra 100 % apilada por control, nombre en español sin id, de peor a mejor madurez; reemplazó a «madurez por área» el 2026-11-19, aunque `AREAS` sigue en el código), mapa 5×5, plan con antes/después y peticiones. Vocabulario: «medida», «confianza del diagnóstico», «Sin evidencia». En v2 usa `riesgos_v2`, `roadmap` y el cambio desde la v1.
  - **Estados: punto de color + palabra** (reemplaza «el estado es forma»). Paleta azul / ámbar / bermellón / dos grises, escalonada en luminosidad para daltonismo y escala de grises. Los tintes de zona se mezclan en sRGB (en OKLCH el matiz se desvía hacia morado o verde en Noche).
  - **Interacciones (Fase 3, en `panel.script()`):** clic en un estado (leyenda o segmento de barra) = filtro global: `body[data-filtro]` oculta las filas `[data-estados]` sin ese estado, filtra las matrices y muestra «Mostrando N … · Quitar filtro» (conteos de `[data-conteos]`); los estados con 0 se deshabilitan (antes, elegirlos ponía todo en gris). Clic en un riesgo o iniciativa (`[data-abre]`) abre el panel lateral con la ficha oculta `[data-ficha]` de `panel.fichas()` (la ejecutiva sin ids ni salvaguardas); Esc, X o clic fuera lo cierran, el foco queda atrapado y vuelve al origen. En la técnica, el riesgo ya no se despliega: abre el panel. El clic en un área se descartó al quitar «Madurez por área».
  - **Vista técnica (Fase 4):** conserva todo lo anterior (postura completa, ahora sin recorte; estado por control; riesgos; roadmap; matrices; pendientes y «Por qué es preliminar»). La severidad es punto + palabra con «P4 × I5» debajo, y el roadmap tiene columna «Plazo» (estimado en evaluaciones anteriores). El índice lateral muestra las secciones de la vista activa.
  - **El script de `st.html` no puede contener etiquetas HTML** (ni en cadenas ni en comentarios, p. ej. «<details>»): Streamlit lo descarta sin aviso. Se construye el DOM con `createElement`.
  - Pendientes de fases siguientes: PDF ejecutivo de 2-3 páginas (cumple el límite de 5) y técnico sin límite, visor de evidencia con PyMuPDF.

## Stack
- Python 3.14 (el `python3` del sistema es 3.15 y algunas dependencias aún no tienen wheels).
- `anthropic`, `streamlit`, `python-dotenv`, `openpyxl` (importador y Excel), `pypdf` (texto del PDF para verificar citas), `fpdf2` (reporte ejecutivo en PDF; fuentes estándar con cp1252, sin fuentes del sistema).
- **Modelo elegido en la UI** (desplegable de la barra lateral, `engine.MODELOS`: Sonnet 5.5 por defecto, Haiku 5.5 para depurar, Opus 5.5); ya no va en `.env` (2026-11-18).
  - Se guarda en `Proyecto.modelo` en la primera llamada y queda fijo desde que existe la ficha: un solo modelo por evaluación (consistencia).
  - `app.py` asigna `motor.modelo = p.modelo` antes de cada tarea.
- Sonnet 5.5: `temperature`/`top_p` dan 400 (sin semilla); el razonamiento es adaptativo (no se manda `thinking`) y el esfuerzo es fijo (`engine.ESFUERZO`); cambiarlo entre llamadas invalida la caché. Forced `tool_choice` da 400: se usa `output_config.format` (JSON Schema).
- `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`) en Sonnet/Opus 5.5: si el clasificador de seguridad declina (p. ej. "cyber"), el servidor reintenta en otro modelo. Haiku 5.5 no lo admite (`CON_FALLBACK`).
- Usar casos ficticios o los del profesor.

## Estructura
```
app.py                     # UI por etapas; tareas lentas con pedir() y ejecución al FINAL del script
chatbot/
  controls.py              # Catálogo CIS IG1 desde data/cis_v8_1_2.json; nombres en español del equipo
  documentos.py            # Documento (páginas de texto), leer_pdf(), verificar_cita()
  state.py                 # Resultado, Version, Cambio, Proyecto; validar_resultado(), indicadores(), validar_reporte()
  prompts.py               # Prompt maestro (identidad, alcance, R1–R12, escala) + tarea por etapa; DIMENSIONES
  schemas.py               # JSON Schemas por etapa (sus minItems/maxItems se quitan al enviar: Claude no los admite; el código exige los conteos)
  engine.py                # explain, context_sheet, evaluate, report, analyze_initiatives, updated_report, ask; caché y consumo
  almacen.py               # guardar/cargar/listar proyectos en evaluaciones/ (EVALUACIONES_DIR para pruebas)
  exportar.py              # excel(p, "v1"|"v2"), reporte_html(p, "v1"|"v2"), csv_matriz, ficha_html (_pagina_html); prompt_maestro_md()
  reporte_pdf.py           # reporte_pdf(p, "v1"|"v2") (Entregable 3; cada uno debe caber en 5 páginas, lo verifica test_motor) y ficha_pdf()
  ui.py                    # Tokens CSS (OKLCH) y piezas HTML (también las de los HTML descargables)
  panel.py                 # Dashboard de los reportes v1/v2 (mockup aprobado), índice lateral y su script
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
- Consistencia (R9): no hay temperatura ni semilla en Sonnet 5.5; la consistencia la dan las instrucciones fijas, la salida estructurada y las reglas deterministas del código.

## Convenciones
- Código y comentarios en español; identificadores sin acentos.
- El estado en Python es la fuente de verdad; Claude propone y Python valida.
- Salida estructurada siempre (`output_config.format` con `json_schema`); validar en Python con `.get()`. Revisar `stop_reason` (`refusal`, `max_tokens`) antes de leer el contenido.
- Nunca escribir la API key en el código ni subir `.env`.
- **Licencia CIS (CC BY-NC-ND 4.0):** nunca versionar ni traducir/modificar los textos de CIS; se usan en inglés tal cual. El prompt maestro exportado NO incluye el catálogo. Mostrar `controls.atribucion()`.
- Las pruebas usan un catálogo falso (`CIS_CATALOGO`); no dependen del Excel ni del JSON real.
- `REINTENTOS`=3 (lo hace el SDK: 408/409/429/5xx/529, timeouts y conexión); `TIMEOUT_S`=120 y `TIMEOUT_LARGO_S`=420 por intento. No añadir un bucle propio.
- **Ahorro de tokens (no romperlo):**
  - **Caché de prompts (5 min) solo donde hay reutilización**, con `_llamar(..., cachear=True)`: lotes de la evaluación, ficha regenerada y consultas. **El esquema de salida es parte del prefijo cacheado:** dos llamadas con esquemas distintos no comparten caché. Por eso los 3 lotes usan el MISMO esquema (los 56 ids) y el código filtra los de cada lote; con un esquema por lote se midieron 0 tokens leídos. Las llamadas únicas (reportes, PDF 2) no se cachean: pagarían la escritura (1.25x) sin leerla. `prompts.base()` va primero e idéntico; nada variable antes de los puntos de caché.
  - **Esquemas compactos:** `_esquema_para_api()` quita `minItems`/`maxItems` y mueve subesquemas repetidos a `$defs`. Sin esto, la ficha da 400 "compiled grammar is too large".
  - **Esfuerzo por modelo:** `ESFUERZO` = el valor por defecto de cada uno (Sonnet 5.5 "high", Haiku 5.5 "medium"). Haiku en "high" gastó los 24K tokens de la ficha razonando, sin responder.
  - **Prefijo de mensajes.** Documento y contexto llevan `cache_control` (5 min) para que los lotes de la evaluación, la segunda pasada de la Etapa 5 y las consultas seguidas los lean de caché. Lo que cambia (lote, pregunta) va al final.
  - **Documento como texto paginado** (`Documento.texto_completo()`), no como PDF; solo un PDF sin texto va como archivo.
  - **Payload compacto.** `ficha_resumida()` sin citas para las etapas posteriores, JSON compacto y `matriz_compacta()` sin nombres (están en el catálogo). `MAX_TOKENS` por etapa.
  - **Consumo.** `Motor.consumo` → `Proyecto.consumo` (se guarda con la evaluación; la app ya no lo muestra, 2026-11-19). Verificar `cache_read_input_tokens` > 0 tras cambiar prompts.
- Tareas lentas en la UI: `pedir(tipo)` → rerun con controles deshabilitados → se ejecutan al final del script con la tarjeta de progreso en `lugar_progreso`.

## Diseño (UI)
- **Identidad "Pizarra cálida" (Día) y "Grafito" (Noche)** (2026-11-18), del mockup aprobado `mockup/resumen.html` (reemplaza a "Dictamen técnico").
  - Tokens en `ui.CSS`: Día en `:root`, Noche en `:root[data-theme="dark"]` (y en `prefers-color-scheme` para la primera pintura). Los nombres antiguos (`--bg`, `--text-1`, `--st-cubierto`…) son alias de los nuevos (`--paper`, `--ink`, `--st-implementado`…). No hex sueltos.
  - Tipografía: **solo Geist** (interfaz, títulos y cifras) y **Geist Mono** con números tabulares (IDs, folios). Títulos de sección 21px > títulos de tarjeta.
  - **El estado es un punto de color junto a la palabra** (2026-11-19): azul (Implementado), ámbar (Parcial), bermellón (No implementado), gris medio (No verificado / «Sin evidencia» en la vista ejecutiva) y gris claro (No aplicable). Los colores `st-*` solo pintan marcas y fondos (`tint-*`, `color-mix`); el texto va en `ink`. Nunca texto en color de estado.
- **Dashboard de los reportes: `chatbot/panel.py`** (clases `d-`). Los HTML descargables siguen usando `ui.tablero/riesgos/roadmap/resumen_ejecutivo`, que conservan todo el texto: no mezclarlos.
  - Piezas: `resumen` (4 KPIs del mismo tamaño, barra apilada y leyenda), `postura`, `controles` (segmentos a escala fija y %; toda fila se abre con sus salvaguardas y solo los 5 de mayor brecha traen además su explicación), `riesgos` (fila plegable con «N salvaguardas»), `roadmap` (chips «R1 nombre corto», esfuerzo en bloques), `matriz`, `pendientes`, `indice` y `estado_lateral`.
  - Barra lateral: en los reportes, **índice de secciones** que marca la visible; en las demás etapas, un resumen compacto de indicadores. Modelo y evaluaciones guardadas debajo.
  - Descargas en un menú **«Descargar»** (`st.popover`) junto al título del reporte.
  - Campos del reporte para el dashboard (`titular`, `datos_clave`, `brechas_clave`, `bases`, `nombre_corto` del riesgo): los valida `state.validar_presentacion()` contra la matriz. Un «X de Y» solo queda si ambos números aparecen en su salvaguarda. Las evaluaciones anteriores usan respaldos calculados en `panel` (oración con «postura», nombre corto desde el activo).
  - **Interacciones en `panel.script()`**: un solo script con delegación de eventos, instalado una vez con `st.html(..., unsafe_allow_javascript=True)` (corre en la página, sin iframe).
    - Resaltado cruzado por estado desde la leyenda (`body[data-foco]` atenúa todo `[data-e]` distinto; con clic queda fijo).
    - Vínculo riesgos ↔ roadmap (`data-riesgo` / `data-riesgos`, con grupo `a` = v1 y `b` = vigentes v2).
    - «Leer más», filtros de la matriz (`data-filtro` y CSS) e índice con scrollspy.
    - Entrada animada: cifras de 0 a su valor y barra que se llena (menos de 1 s). No se anima con `prefers-reduced-motion` ni en pestañas ocultas; el HTML ya trae los valores finales.
- **Temas de Streamlit:** `[theme.light]` y `[theme.dark]` en `.streamlit/config.toml`, con los hex de los tokens. `ui.tema_script()` lee el fondo que Streamlit aplicó y pone `data-theme` en la raíz; no usar `st.context.theme` (puede estar desfasado al cambiar de tema).
- **Selector Día/Noche** (`ui.selector_tema()` en la barra lateral). Escribe `"Light"`/`"Dark"` en `localStorage["stActiveTheme-<ruta>-v2"]`, que es donde Streamlit lee el tema, y recarga la página.
  - Para volver al mismo lugar, `app.py` mantiene `?evaluacion=<id>&vista=<sección>` en la URL y los restaura al iniciar sesión. Solo acepta ids hexadecimales de 10 caracteres.
  - El selector se deshabilita mientras corre una tarea.
- Tras cambiar `ui.py`, reiniciar el servidor de Streamlit: conserva en memoria la versión anterior del módulo.
- `st.html` sanitiza (DOMPurify, perfil HTML): **elimina `<svg>`** (los chevrons se dibujan con CSS) y **descarta un `<style>` completo si contiene `<`** (incluso en comentarios; usar `\3c`). Conserva `details`, `button`, `data-*` y `aria-*`.
- Todo texto de Claude o del usuario pasa por `ui.esc()`.
- **`st.chat_input` nunca en la raíz**, siempre dentro de `st.container(key="chat")`. En la raíz, Streamlit lo fija abajo y activa "pegarse al final" (`stAppScrollToBottomContainer`), que arrastra la página hasta abajo al cambiar de sección o abrir un plegable.
- Al cambiar de sección se sube al inicio con `ui.subir_al_inicio()` (`st.html(..., unsafe_allow_javascript=True)`), solo cuando cambia `vista_mostrada`.
- Respetar `prefers-reduced-motion`; revisar en 375px y escritorio.

## Comandos
```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/importar_cis.py "ruta/CIS_Controls_Version_8.1.2___March_2025.xlsx"   # genera el catálogo local
cp .env.example .env            # y poner ANTHROPIC_API_KEY (platform.claude.com → API keys)
streamlit run app.py
python -m pytest -q             # 46 pruebas sin API
python scripts/exportar_prompt.py   # regenera docs/prompt_maestro_centinela_ig1.md
```

## Forma de trabajo con Claude Code (obligatorio)
- **Notificar al usuario después de terminar cada cambio**: al acabar cada archivo o cambio relevante, decir en el chat qué se cambió y por qué, en una o dos líneas.
- **Notificar y preguntar en cada decisión**: ante cualquier decisión de diseño no trivial (librería, estructura, modelo, cambio de flujo, borrar archivos), preguntar al usuario antes de actuar, o, si es un default obvio, avisar explícitamente qué se decidió. Los hooks (en `.claude/settings.json`, local: `.claude/` está en `.gitignore`) notifican cuando Claude espera una respuesta o un permiso.
- Responder en español.
