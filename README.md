# Diagnóstico de controles de ciberseguridad

Chatbot que entrevista al responsable de ciberseguridad de una empresa y evalúa sus controles con base en **ISO/IEC 27002:2022** y **CIS Controls v8**.

1. El usuario describe el contexto de su empresa.
2. El chatbot hace un análisis inicial y clasifica 23 dominios de control como cubierto, parcial, no cubierto o por confirmar.
3. Para lo que no quedó claro, hace preguntas cerradas de **Sí / No**. No se suben evidencias.
4. Al terminar entrega un reporte con:
   - el estado de cada control,
   - los riesgos principales,
   - **quick wins**,
   - una hoja de ruta de recomendaciones.

Está hecho con **Python + Streamlit** y usa la **API gratuita de Google Gemini** (SDK oficial `google-genai`).

---

## Requisitos previos

| Requisito | Detalle |
|---|---|
| **Python 3.12, 3.13 o 3.14** | El código necesita 3.12 o superior. Python 3.15 todavía puede fallar al instalar dependencias porque algunas no tienen versión compilada para él. Comprueba tu versión con `python3 --version`. |
| **Git** | Para clonar el repositorio. |
| **Cuenta de Google** | Para obtener una API key gratuita de Gemini. |

Si no tienes una versión compatible:
- **macOS:** `brew install python@3.14`
- **Windows / Linux:** descárgala de [python.org](https://www.python.org/downloads/).

---

## Paso a paso

### 1. Clona el repositorio

```bash
git clone <URL-del-repositorio> ChatbotControles
```
```bash
cd ChatbotControles
```

### 2. Crea un entorno virtual

El entorno virtual (`.venv`) aísla las dependencias del proyecto. No se sube al repositorio, así que cada persona debe crear el suyo.

**macOS / Linux:**
```bash
python3.14 -m venv .venv
```
Si tienes 3.12 o 3.13, cambia `python3.14` por tu versión.

**Windows (PowerShell):**
```powershell
py -3.14 -m venv .venv
```

### 3. Instala las dependencias

**macOS / Linux:**
```bash
.venv/bin/pip install -r requirements.txt
```

**Windows:**
```powershell
.venv\Scripts\pip install -r requirements.txt
```

### 4. Obtén tu API key de Gemini (gratis)

1. Entra a **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)** con tu cuenta de Google.
2. Da clic en **Create API key** y cópiala.

### 5. Configura el archivo `.env`

Copia la plantilla:

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows:**
```powershell
copy .env.example .env
```

Abre `.env` y pega tu key, sin comillas ni espacios:

```
GEMINI_API_KEY=AIza...tu_key...
GEMINI_MODEL=gemini-3.5-flash-lite
```

> `.env` está en `.gitignore` y **nunca debe subirse al repositorio**. Cada integrante usa su propia key.

### 6. Ejecuta el chatbot

**macOS / Linux:**
```bash
.venv/bin/streamlit run app.py
```

**Windows:**
```powershell
.venv\Scripts\streamlit run app.py
```

Se abrirá en el navegador en **http://localhost:8501**. Para detenerlo, presiona `Ctrl + C` en la terminal.

### 7. (Opcional) Corre las pruebas

Las pruebas simulan a Gemini, así que no gastan cuota ni necesitan API key.

**macOS / Linux:**
```bash
.venv/bin/python -m pytest -q
```

**Windows:**
```powershell
.venv\Scripts\python -m pytest -q
```

Deben pasar las 5 pruebas.

---

## Cómo usarlo

1. **Describe tu empresa:** sector, tamaño, infraestructura, sistemas críticos, datos que manejan y medidas de seguridad actuales. También puedes pulsar **"Probar con una empresa ficticia"** para ver una demo.
2. **Responde las preguntas** con **Sí, lo tenemos** o **No lo tenemos**. En cualquier momento puedes escribir una aclaración en el chat y el análisis se ajusta.
3. **Revisa el reporte.** Aparece al contestar la última pregunta, o antes con **"Generar reporte ahora"** en la barra lateral.

La barra lateral muestra en todo momento:
- la cobertura estimada,
- una matriz con el estado de cada control,
- el detalle de cada control agrupado por estado.

> **Usa empresas ficticias.** En el plan gratuito de Gemini, Google puede usar el contenido enviado para mejorar sus productos. No ingreses datos reales ni sensibles de una empresa.

---

## Configuración

Variables en `.env`:

| Variable | Obligatoria | Valor por defecto | Descripción |
|---|---|---|---|
| `GEMINI_API_KEY` | Sí | — | Tu API key de Google AI Studio. |
| `GEMINI_MODEL` | No | `gemini-3.5-flash-lite` | Modelo de Gemini. Una alternativa gratuita con más calidad, pero aún en preview, es `gemini-3.8-flash`. |

El plan gratuito tiene **límites por minuto y por día**. Los de tu proyecto aparecen en [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit). Una evaluación completa usa solo 2 o 3 llamadas, porque las respuestas Sí/No se procesan localmente.

---

## Estructura del proyecto

```
app.py                  Interfaz Streamlit: chat, tarjeta Sí/No, barra lateral y reporte
chatbot/
  controls.py           Catálogo de 23 dominios de control (mapeo ISO 27002 ↔ CIS v8)
  state.py              Estado de la evaluación y cola de preguntas (fuente de verdad)
  prompts.py            Instrucciones para Gemini
  schemas.py            Esquemas JSON de las respuestas estructuradas
  engine.py             Llamadas a la API de Gemini (análisis, seguimiento, reporte)
  ui.py                 Diseño: CSS y piezas HTML
.streamlit/config.toml  Tema visual de Streamlit
tests/test_state.py     Pruebas (sin llamar a la API)
.env.example            Plantilla de variables de entorno
requirements.txt        Dependencias
CLAUDE.md               Contexto del proyecto para Claude Code (asistente de desarrollo)
```

---

## Problemas comunes

| Mensaje o síntoma | Solución |
|---|---|
| `Falta GEMINI_API_KEY en el archivo .env` | No existe `.env`, o la variable está mal escrita. Repite el paso 5. |
| `API key inválida` | Revisa que copiaste la key completa, sin comillas ni espacios. |
| `Se alcanzó el límite gratuito de Gemini` | Espera un minuto. Si es el límite diario, se reinicia a la medianoche, hora del Pacífico. |
| `El modelo '...' no existe` | Revisa el valor de `GEMINI_MODEL` en `.env`. |
| `command not found: python3.14` | Usa la versión de Python que tengas (3.12 o superior) o instálala (ver Requisitos previos). |
| Falla `pip install` con errores de compilación | Probablemente usas Python 3.15. Crea el entorno con 3.12–3.14. |
| `AttributeError: module 'chatbot.ui' has no attribute ...` tras actualizar el código | Streamlit conservó en memoria la versión anterior de un módulo. Detén el servidor con `Ctrl + C` y vuelve a ejecutarlo. |
| El puerto 8501 está ocupado | Ejecuta `streamlit run app.py --server.port 8502`. |
