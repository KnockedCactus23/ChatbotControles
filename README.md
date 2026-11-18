# Centinela IG1 — agente de evaluación de CIS Controls v8.1 IG1

Agente de IA que actúa como consultor de ciberseguridad (actividad **M3.6**). Lee los documentos de una organización y evalúa las **56 salvaguardas del Implementation Group 1 (IG1)** de los **CIS Critical Security Controls v8.1**. Esa es su única referencia normativa.

| Etapa | Qué hace el agente |
|---|---|
| 1. Diseño | Identidad, alcance, reglas R1–R12 y escala de estados en un **prompt maestro** (entregable: [`docs/prompt_maestro_centinela_ig1.md`](docs/prompt_maestro_centinela_ig1.md)). Botón de **prueba preliminar** ("¿cómo trabajas?"). |
| 2. Contexto (PDF 1) | **Ficha de contexto** en 10 dimensiones, con página, sección y cita de cada hallazgo, más la información faltante y las ambigüedades. El equipo la valida o registra ajustes. |
| 3. Evaluación | **Matriz de las 56 salvaguardas** con aplicabilidad, uno de los 5 estados, justificación, evidencia, cita y observaciones. Calcula los indicadores de **implementación** y **cobertura** con las fórmulas de la actividad. |
| 4. Reporte | **Resumen ejecutivo**, **5 riesgos**, **roadmap de 5 iniciativas** (quick win o proyecto) y **dashboard**. |
| 5. Iniciativas (PDF 2) | Parte de la evaluación inicial y **propone** cambios con evidencia; el equipo los **aprueba, rechaza o deja pendientes**. Genera la **versión v2** sin perder la v1. |
| Entregables | Separados por versión. En el **reporte inicial**: matriz v1 (CSV), Excel v1 y reporte ejecutivo inicial (PDF o HTML). En el **reporte actualizado**: matriz v2 (CSV), Excel v2 y reporte ejecutivo final (PDF o HTML). En el **contexto**: la ficha en PDF o HTML. El prompt maestro se genera con `scripts/exportar_prompt.py`. |

**Escala obligatoria:** Implementado (1) · Parcialmente implementado (0.5) · No implementado (0) · No verificado (—) · No aplicable (—).

**Protecciones contra las penalizaciones** (las aplica el sistema, no solo el prompt):
- **Ninguna salvaguarda se omite:** si el modelo no devuelve alguna, queda "No verificado" y visible.
- **No hay evidencia inventada:** cada cita se verifica contra el texto del PDF. Si no aparece, la conclusión se descarta y queda "No verificado".
- **No hay incumplimiento por falta de información:** "No implementado" exige una cita que lo confirme (R8).
- **Ningún cambio sin justificación:** los cambios del PDF 2 necesitan una cita verificada y la aprobación del auditor.
- **Ningún cambio omitido en silencio:** cada salvaguarda relacionada con una iniciativa del PDF 2 recibe una decisión: cambio de estado, actualización de evidencia o sin cambio con motivo. Si el modelo omite alguna, el sistema se la vuelve a pedir.
- **El avance de riesgos e iniciativas no lo decide el modelo:** se calcula con reglas fijas sobre la matriz v2. Un riesgo queda mitigado, reducido o igual, con severidad residual; una iniciativa queda completada, en progreso o pendiente.
- **El diagnóstico inicial no se pierde:** la v1 queda fija al cerrarse y todo se guarda automáticamente.
- **Matriz, indicadores e informe no se contradicen:** los indicadores los calcula el sistema desde la matriz, y los riesgos e iniciativas solo pueden citar salvaguardas que son brecha.
- **El agente puede explicar el origen de sus conclusiones:** cada fila tiene página y cita, y puedes preguntarle en el chat por qué decidió algo.
- **Consistencia:** instrucciones fijas, salida estructurada y reglas deterministas en el código. Los estados verificados, los indicadores y la situación de riesgos e iniciativas no dependen del azar del modelo.

El agente **no hace preguntas Sí/No al cliente**: se apega a la actividad y solo usa la evidencia documental de los PDF. Lo que no está documentado queda como No verificado.

Está hecho con **Python + Streamlit** y usa la **API de Claude** (SDK oficial `anthropic`), con **Claude Sonnet 5.5** por defecto.

---

## Capacidades y qué acepta

### Qué puede hacer
- **Analiza las 56 salvaguardas del IG1 desde un archivo:** a partir de un PDF de contexto, clasifica cada salvaguarda en uno de los 5 estados con justificación, página, sección y cita textual. Las 56 siempre aparecen, aunque no haya información.
- **Interpreta el contexto antes de evaluar:** genera una ficha en 10 dimensiones (organización, procesos, infraestructura, activos, identidades, protección, recuperación, monitoreo, gobierno y restricciones). Incluye un perfil de riesgo por sector (hospital, comercio, universidad, etc.) que ordena qué salvaguardas se priorizan.
- **Verifica sus propias citas** contra el texto del documento. Corrige la página si está mal y descarta lo que no encuentra.
- **Calcula los indicadores** de implementación y cobertura con las fórmulas oficiales y los muestra en un dashboard.
- **Redacta el reporte inicial:** resumen ejecutivo, 5 riesgos (activo o proceso, deficiencia, consecuencia, severidad) y un roadmap de 5 iniciativas (quick win o proyecto, beneficio, esfuerzo y prioridad).
- **Procesa el avance de iniciativas (PDF 2):**
  - propone cambios de estado con evidencia, que tú apruebas, rechazas o dejas pendientes;
  - genera una v2 comparada con la v1, que se conserva intacta.
- **Explica sus decisiones** en un chat. Por ejemplo: "¿por qué 10.1 está implementada?" o "¿qué información falta?".
- **Permite navegar** entre la ficha de contexto, el reporte inicial y el reporte actualizado de un análisis (en solo lectura lo que ya está cerrado).
- **Guarda cada evaluación automáticamente** para retomarla otro día, y exporta los entregables.

### Qué acepta

| Entrada | Formato | Dónde |
|---|---|---|
| Contexto de la empresa (PDF 1) | PDF con texto seleccionable, o texto pegado | Pantalla inicial |
| Ajustes a la interpretación | Texto libre; queda registrado como ajuste del agente | Ficha de contexto |
| Avance de iniciativas (PDF 2) | PDF con texto seleccionable | Reporte inicial |
| Decisión del auditor por cambio | Aprobar / Rechazar / Pendiente | Validación de cambios |
| Preguntas al agente | Texto libre en el chat | Ficha de contexto (ya analizada), reporte inicial y reporte actualizado |
| Evaluación guardada | Selección en la barra lateral | Cualquier momento |

### Qué entrega

| Salida | Formato |
|---|---|
| Matriz v1 y Excel v1 *(reporte inicial)* | CSV con las 56 salvaguardas de la evaluación inicial. Excel con contexto, matriz v1, indicadores v1, 5 riesgos, roadmap y ajustes |
| Matriz v2 y Excel v2 *(reporte actualizado)* | CSV con las 56 salvaguardas actualizadas. Excel con contexto, matriz v2, indicadores v1 frente a v2, situación de los riesgos, estado de las iniciativas, roadmap actualizado, cambios del PDF 2 y ajustes. No repite la matriz v1 |
| Reporte ejecutivo inicial / final | **PDF** listo para entregar (A4, máximo 5 páginas cada uno) o HTML con el diseño de la app. El inicial solo usa v1; el final usa v2 y su comparación con v1 |
| Ficha de contexto | PDF o HTML: las 10 dimensiones con página y cita de cada hallazgo, información faltante, ambigüedades, perfil de riesgo y ajustes del equipo. Se descarga desde la sección Contexto |
| Prompt maestro | Markdown, generado con `scripts/exportar_prompt.py` |

### Qué no hace
- No evalúa IG2 ni IG3, ni usa otros marcos como ISO 27002.
- No lee PDF escaneados sin texto: las citas no se podrían verificar.
- No hace preguntas Sí/No al cliente ni toma en cuenta información sin documento.
- No cambia estados desde el chat.

---

## Requisitos previos

| Requisito | Detalle |
|---|---|
| **Python 3.12, 3.13 o 3.14** | El código necesita 3.12 o superior. Python 3.15 todavía puede fallar al instalar dependencias porque algunas no tienen versión compilada para él. Comprueba tu versión con `python3 --version`. |
| **Git** | Para clonar el repositorio. |
| **Cuenta en platform.claude.com** | Para obtener una API key de Claude, con saldo. Una evaluación completa con Sonnet 5.5 cuesta alrededor de un dólar. |
| **Excel de CIS Controls v8.1** | Se descarga gratis de CIS (paso 4). No está en el repositorio por su licencia. |

Si no tienes una versión compatible de Python:
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

### 4. Genera el catálogo de CIS Controls

El agente usa como base normativa las descripciones oficiales de las 56 salvaguardas IG1 de CIS Controls v8.1. El importador guarda las 153 salvaguardas, pero solo se evalúan las 56 de IG1.

Ese contenido tiene licencia **CC BY-NC-ND 4.0**:
- se puede usar sin fines comerciales y dando crédito a CIS;
- **no** se puede redistribuir modificado.

Por eso no está en el repositorio: cada integrante lo genera desde el Excel oficial.

1. Descarga el Excel de **CIS Controls v8.1** desde [cisecurity.org/controls/v8-1](https://www.cisecurity.org/controls/v8-1). CIS pide llenar un formulario breve. El archivo se llama algo como `CIS_Controls_Version_8.1.2___March_2025.xlsx`.
2. Conviértelo. Cambia la ruta por la de tu archivo.

**macOS / Linux:**
```bash
.venv/bin/python scripts/importar_cis.py "$HOME/Downloads/CIS_Controls_Version_8.1.2___March_2025.xlsx"
```

**Windows:**
```powershell
.venv\Scripts\python scripts\importar_cis.py "$HOME\Downloads\CIS_Controls_Version_8.1.2___March_2025.xlsx"
```

Debe decir `Listo: 18 controles y 153 salvaguardas`. Esto crea `chatbot/data/cis_v8_1_2.json`, que está en `.gitignore`.

### 5. Obtén tu API key de Claude

1. Entra a **[platform.claude.com](https://platform.claude.com)**, ve a **API keys** y crea una.
2. Revisa que la cuenta tenga saldo (en **Billing**).

### 6. Configura el archivo `.env`

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
ANTHROPIC_API_KEY=sk-ant-...tu_key...
```

El modelo no va en `.env`: se elige en la app (ver "Modelo de Claude" en Configuración).

> `.env` está en `.gitignore` y **nunca debe subirse al repositorio**. Cada integrante usa su propia key.

### 7. Ejecuta el chatbot

**macOS / Linux:**
```bash
.venv/bin/streamlit run app.py
```

**Windows:**
```powershell
.venv\Scripts\streamlit run app.py
```

Se abrirá en el navegador en **http://localhost:8501**. Para detenerlo, presiona `Ctrl + C` en la terminal.

### 8. (Opcional) Corre las pruebas

Las pruebas simulan a Claude y usan un catálogo CIS de prueba, así que no gastan saldo ni necesitan API key ni el Excel.

**macOS / Linux:**
```bash
.venv/bin/python -m pytest -q
```

**Windows:**
```powershell
.venv\Scripts\python -m pytest -q
```

Deben pasar las 36 pruebas.

### 9. (Opcional) Regenera el prompt maestro

El repositorio ya incluye [`docs/prompt_maestro_centinela_ig1.md`](docs/prompt_maestro_centinela_ig1.md). Si cambias las instrucciones en `chatbot/prompts.py`, regenéralo (necesita el catálogo del paso 4):

```bash
.venv/bin/python scripts/exportar_prompt.py
```

---

## Cómo usarlo

1. **Prueba preliminar (opcional):** pulsa **"Prueba preliminar: ¿cómo trabajas?"**. El agente explica su objetivo, alcance, criterios y qué hace cuando falta información.
2. **Carga el PDF 1** (contexto empresarial) y pulsa **Analizar contexto**. Si no tienes PDF, puedes pegar el contexto como texto.
3. **Valida la ficha de contexto:**
   - Revisa cada hallazgo: ✓ significa que la cita se encontró en el documento; ✗ que no se encontró.
   - Si algo está mal interpretado, escribe el ajuste y regenera la ficha. Los ajustes quedan registrados para tu entrega (Etapa 2.5).
   - Cuando esté bien, pulsa **Validar la ficha y evaluar las 56 salvaguardas**.
4. **Revisa la matriz de las 56** junto con el dashboard de indicadores.
5. **Genera el reporte inicial.** Esto cierra la versión **v1**, que ya no se modifica.
6. **Carga el PDF 2** (avance de iniciativas). El agente propone cambios. Como auditor, apruébalos, recházalos o déjalos pendientes; solo los aprobados se aplican.
7. **Aplica los cambios aprobados.** Se genera la versión **v2** con la comparación de indicadores, los riesgos que cambiaron o permanecen, el estado de las iniciativas y el roadmap actualizado.
8. **Descarga los entregables de cada sección:**
   - **Contexto:** la ficha.
   - **Reporte inicial:** matriz v1, Excel v1 y reporte inicial.
   - **Reporte actualizado:** matriz v2, Excel v2 y reporte final.

**Navega entre las secciones del análisis** con la barra bajo el encabezado:
- Siempre: **Contexto**, **Reporte inicial** y **Reporte actualizado** (cuando ya existen).
- Mientras están en curso, también la **Evaluación 56** o la **Validación PDF 2**. Al terminar, su contenido queda en los reportes.
- Las secciones ya cerradas se ven en **solo lectura**: la ficha no se puede regenerar después de evaluar, ni la v1 cambiar después del reporte.

Puedes **preguntarle al agente** en el chat por qué tomó una decisión. Responde citando la página y el texto del documento, pero no cambia estados. El chat está disponible en la ficha de contexto (después de analizar el PDF 1), en el reporte inicial y en el reporte actualizado.

**Modo Día o Noche:** cámbialo con el selector de la parte superior de la barra lateral. La página se recarga y vuelve a la evaluación y la sección donde estabas. Sin elección, sigue el tema del sistema operativo.

**Las evaluaciones se guardan solas** en la carpeta `evaluaciones/`, que no se sube a git. Para retomar una la semana siguiente, elígela en **"Evaluaciones guardadas"**, en la barra lateral.

> **Para la demo:** la bitácora de validaciones de la barra lateral muestra cada vez que el sistema corrigió al modelo. Por ejemplo: "propuso No implementado sin cita; queda No verificado". Es evidencia de una limitación del modelo y de cómo se controla.

> **Usa casos ficticios o los del profesor.** No envíes documentos reales de una empresa sin autorización.

---

## Configuración

Variable en `.env`:

| Variable | Obligatoria | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | Sí | Tu API key de Claude (platform.claude.com). |

**Modelo de Claude:** se elige en el desplegable de la barra lateral.

| Modelo | Para qué |
|---|---|
| **Claude Sonnet 5.5** (por defecto) | Las corridas que se entregan o se muestran. |
| **Claude Haiku 5.5** | Probar o depurar gastando centavos. |
| **Claude Opus 5.5** | Máxima capacidad, al doble de costo que Sonnet. Úsalo solo si Sonnet falla en alguna etapa. |

El modelo se guarda con cada evaluación y queda **fijo desde que se genera la ficha**, para que toda la evaluación use uno solo. Para cambiarlo, crea una nueva evaluación.

**Consumo y costo.** Una evaluación completa hace unas 8 llamadas:
- la ficha;
- 3 lotes de la evaluación;
- el reporte inicial;
- el PDF 2 (más una segunda pasada si faltaron decisiones);
- el reporte actualizado.

Cada pregunta en el chat suma una llamada más. El panel **"Consumo de Claude"** de la barra lateral muestra los tokens y el costo estimado de cada llamada, y qué parte de la entrada salió de la caché.

**Cómo se ahorran tokens sin bajar la calidad:**
- **Caché de prompts:** los 3 lotes de la evaluación comparten el prompt maestro, el catálogo, el documento y la ficha (unos 32K tokens). Los lotes 2 y 3 los leen de la caché, que cuesta el 5 % del precio normal en Sonnet 5.5. Lo mismo pasa al regenerar la ficha con un ajuste y con preguntas seguidas en el chat. Las llamadas que no se repiten no se cachean, para no pagar la escritura.
- **Texto en lugar del PDF:** el documento se envía como texto con marcas de página, que es el mismo texto contra el que se verifican las citas. Usa cerca de un tercio de los tokens. Un PDF escaneado sin texto se envía como archivo.
- **Contexto resumido:** después de la evaluación, la ficha viaja sin las citas de cada hallazgo, porque esas citas ya están en la matriz. Los datos van en JSON compacto.
- **Límite de salida por etapa** (`max_tokens`), para evitar respuestas desbocadas.

**Reintentos y errores:** la app reintenta sola los errores temporales (saturación, límite por minuto, timeouts) hasta 3 veces. Si el filtro de seguridad de Claude declina una solicitud, Sonnet 5.5 la reintenta en otro modelo del lado del servidor (`fallbacks`).

---

## Estructura del proyecto

```
app.py                  Interfaz por etapas (contexto, evaluación, reporte, PDF 2, actualizado)
chatbot/
  controls.py           Catálogo CIS v8.1 IG1 (leído del JSON local; nombres en español)
  documentos.py         Lectura de PDF y verificación de citas contra el texto
  state.py              Proyecto, matriz de 56, 5 estados, indicadores, versiones v1/v2, cambios
  prompts.py            Prompt maestro (identidad, alcance, R1–R12, escala) e instrucciones por etapa
  schemas.py            Esquemas JSON de las respuestas estructuradas
  engine.py             Llamadas a Claude por etapa: caché de prompts, salida estructurada, reintentos y consumo
  almacen.py            Guardado automático en evaluaciones/
  exportar.py           Excel y reporte HTML por versión (v1 o v2), CSV, ficha HTML y prompt maestro
  reporte_pdf.py        Reporte ejecutivo inicial/final y ficha de contexto en PDF (fpdf2)
  ui.py                 Diseño: CSS y piezas HTML
  data/                 cis_v8_1_2.json generado localmente (no se sube al repositorio)
scripts/
  importar_cis.py       Convierte el Excel oficial de CIS al JSON
  exportar_prompt.py    Genera docs/prompt_maestro_centinela_ig1.md (Entregable 1)
docs/                   Prompt maestro (sin textos de CIS)
evaluaciones/           Evaluaciones guardadas y sus PDF (no se suben al repositorio)
tests/                  Pruebas sin API ni Excel (reglas, flujo completo, importador, reintentos)
```

---

## Problemas comunes

| Mensaje o síntoma | Solución |
|---|---|
| `Falta el catálogo de CIS Controls` | No generaste el JSON. Repite el paso 4. |
| Un hallazgo o salvaguarda dice "cita no encontrada" | El modelo citó un texto que no está en el PDF; el sistema lo descartó. Si el dato sí está en el documento, regenera la ficha o la evaluación. |
| `El PDF no tiene texto extraíble` | Es un escaneo sin texto: las citas no podrán verificarse. Usa un PDF con texto seleccionable. |
| `Se esperaban los controles 1 a 18…` o `Columnas inesperadas` al importar | El Excel no es el de CIS Controls v8.1 o cambió de formato. Descarga la versión 8.1.x oficial. |
| `Falta ANTHROPIC_API_KEY en el archivo .env` | No existe `.env`, o la variable está mal escrita. Repite el paso 6. |
| `API key inválida` | Revisa que copiaste la key completa, sin comillas ni espacios. |
| `Tu cuenta de Claude no tiene saldo suficiente` | Recarga créditos en platform.claude.com (Billing). |
| `Claude está saturado o con fallas…` | La app ya reintentó sola. Espera un minuto y vuelve a intentarlo. |
| `Claude tardó más de N s en responder` | Vuelve a intentarlo; las etapas largas tienen hasta 7 minutos por intento. |
| `Se alcanzó el límite de uso por minuto` | Espera un momento. Los límites de tu cuenta están en platform.claude.com. |
| `Claude declinó esta solicitud por sus filtros de seguridad` | Pasa rara vez con contenido de ciberseguridad. Vuelve a intentarlo; si persiste, revisa el documento. |
| `La respuesta de Claude se cortó por el límite de longitud` | Vuelve a intentarlo. Si se repite, sube el valor de esa etapa en `MAX_TOKENS` (`chatbot/engine.py`). |
| `El modelo '...' no existe` | Elige otro modelo en la barra lateral (en una evaluación nueva). |
| `command not found: python3.14` | Usa la versión de Python que tengas (3.12 o superior) o instálala (ver Requisitos previos). |
| Falla `pip install` con errores de compilación | Probablemente usas Python 3.15. Crea el entorno con 3.12–3.14. |
| `AttributeError: module 'chatbot...' has no attribute ...` tras actualizar el código | Streamlit conservó en memoria la versión anterior de un módulo. Detén el servidor con `Ctrl + C` y vuelve a ejecutarlo. |
| El puerto 8501 está ocupado | Ejecuta `streamlit run app.py --server.port 8502`. |

---

## Créditos

Los criterios de evaluación usan los **CIS Critical Security Controls® v8.1** © Center for Internet Security, Inc., con licencia [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode). Los textos de CIS se usan sin modificar y no se redistribuyen en este repositorio. Proyecto académico, sin fines comerciales.
