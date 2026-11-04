# ChatbotControles — Asistente de diagnóstico de controles de ciberseguridad

## Qué es
Chatbot conversacional que entrevista al **responsable de ciberseguridad** de una empresa y:
1. Recibe el contexto de la empresa (el usuario siempre inicia la conversación).
2. Hace un **análisis inicial** de controles con base en **ISO/IEC 27002:2022** y **CIS Controls v8**.
3. Para los controles que no quedaron claros, hace **preguntas cerradas (Sí / No)** — no se suben evidencias.
4. Actualiza el estado de cada control con cada respuesta.
5. Con el contexto completo, entrega un **reporte**: controles cubiertos / parciales / no cubiertos, **quick wins** y **recomendaciones** priorizadas.

Proyecto académico de equipo. **Decisión del equipo (2026-11-03): el chatbot usa la API gratuita de Google Gemini** mediante el SDK oficial `google-genai` (se descartó la API de Claude porque requiere pago aparte). No mezclar otros proveedores ni capas como LangChain. Este archivo se llama CLAUDE.md solo porque es la configuración de Claude Code, que se usa como asistente de desarrollo.

## Stack
- Python 3.14 (el `python3` del sistema es 3.15 y algunas dependencias aún no tienen wheels; usar `python3.14`).
- `google-genai` (SDK oficial de Gemini), `streamlit` (UI de chat), `python-dotenv`.
- Modelo por defecto `gemini-3.5-flash-lite` (plan gratuito, estable). No usar `gemini-2.5-flash`: está obsoleto y desde el 2026-12-01 se redirige a 3.5 Flash-Lite.
- Plan gratuito: tiene límites por minuto y por día (error 429), y **Google puede usar el contenido para mejorar sus productos**, así que no se deben ingresar datos reales o sensibles de empresas; usar casos ficticios.
- Sin base de datos: el estado vive en `st.session_state` durante la sesión.

## Estructura
```
app.py                     # UI Streamlit (chat, botones Sí/No, panel de estado, reporte)
chatbot/
  controls.py              # Catálogo de dominios de control (mapeo ISO 27002 ↔ CIS v8)
  state.py                 # Estado de la evaluación (estados por control, cola de preguntas)
  prompts.py               # System prompts
  schemas.py               # JSON Schemas de salida estructurada
  engine.py                # Llamadas a la API de Gemini (análisis, seguimiento, reporte)
  ui.py                    # Diseño: tokens CSS (OKLCH) y piezas HTML (anillo, matriz, tarjeta, reporte)
.streamlit/config.toml     # Tema base de Streamlit (colores hex derivados de los tokens, fuente Geist)
tests/test_state.py        # Pruebas de la lógica sin llamar a la API
.env.example               # Variables de entorno (GEMINI_API_KEY, GEMINI_MODEL)
```

## Flujo de la conversación
1. **Contexto** → el usuario describe su empresa. `engine.analyze()` devuelve (salida estructurada JSON): mensaje, estado inicial por control y una lista de preguntas cerradas para los controles `desconocido`.
2. **Preguntas cerradas** → la UI las muestra una por una con botones **Sí / No**. La respuesta se aplica de forma determinista en Python (`Sí → cubierto`, `No → no_cubierto`) **sin llamar a la API** (ahorra costo).
3. **Texto libre** en cualquier momento → `engine.follow_up()` reenvía el estado actual a Gemini, que puede reclasificar controles o añadir preguntas.
4. **Reporte** → cuando no quedan preguntas (o el usuario lo pide), `engine.report()` genera resumen ejecutivo, quick wins y recomendaciones. La tabla de cobertura se calcula en Python a partir del estado (fuente de verdad).

## Convenciones
- Código y comentarios en español; identificadores en español sin acentos (`estado`, `control_id`).
- Estados de control válidos: `cubierto`, `parcial`, `no_cubierto`, `desconocido`.
- El **estado en Python es la fuente de verdad**; Gemini propone cambios y Python los valida (ids y estados permitidos) antes de aplicarlos.
- Salidas de Gemini siempre por **salida estructurada** (`response_mime_type="application/json"` + `response_json_schema`); nunca parsear texto libre. Gemini no garantiza todas las restricciones del esquema, así que se debe validar en Python (usar `.get()` con valores por defecto).
- Modelo configurable con `GEMINI_MODEL` en `.env`. No cambiar el modelo por defecto sin que el equipo lo decida.
- Nunca escribir la API key en el código ni subir `.env` (está en `.gitignore`).
- No inventar números de control: usar solo los del catálogo en `chatbot/controls.py`.

## Diseño (UI)
- Arquetipo "craft oscuro": neutros fríos, bordes de 1px, un solo acento verde azulado; los estados (cubierto/parcial/no cubierto/por confirmar) comparten L y C en OKLCH. Todos los colores salen de los tokens de `ui.CSS`; no poner hex sueltos.
- Momento firma: la matriz de postura y el anillo de cobertura de la barra lateral (las celdas que cambian laten y el anillo se llena desde el valor anterior). El resto de la UI se mantiene sobrio; sin emojis, con íconos `:material/...:`.
- `st.html` sanitiza su contenido: **elimina los `<svg>`** (usar CSS: `conic-gradient`, `mask` con data URI) y **descarta un `<style>` completo si contiene el carácter `<`**, incluso dentro de un comentario (escribir `\3c` en CSS).
- Todo texto de Gemini o del usuario va por `ui.esc()` antes de insertarse en HTML.
- Respetar `prefers-reduced-motion` (ya está en el CSS) y revisar en 375px y en escritorio.

## Comandos
```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # y poner GEMINI_API_KEY (gratis en aistudio.google.com/apikey)
streamlit run app.py
python -m pytest -q             # pruebas sin API
```

## Forma de trabajo con Claude Code (obligatorio)
- **Notificar al usuario después de terminar cada cambio**: al acabar cada archivo o cambio relevante, decir en el chat qué se cambió y por qué, en una o dos líneas. Además, `.claude/settings.json` lanza una notificación de macOS tras cada edición.
- **Notificar y preguntar en cada decisión**: ante cualquier decisión de diseño no trivial (librería, estructura, modelo, cambio de flujo, borrar archivos), preguntar al usuario antes de actuar, o, si es un default obvio, avisar explícitamente qué se decidió. Los hooks notifican cuando Claude espera una respuesta o un permiso.
- Responder en español.
