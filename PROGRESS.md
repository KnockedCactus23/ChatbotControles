# Avance del proyecto — Centinela IG1

Actualizado: **2026-11-17**. Estado general: **la parte 1 de la actividad M3.6 (etapas 1 a 5) está implementada y probada**. Lo que queda depende del equipo (ver "Pendientes").

---

## Estado por etapa de la actividad M3.6

| Etapa | Qué pide | Estado | Dónde está |
|---|---|---|---|
| 1. Diseño del agente | Identidad, alcance, reglas, escala; prueba preliminar | ✅ | `chatbot/prompts.py` (R1–R12), botón "¿cómo trabajas?", `docs/prompt_maestro_centinela_ig1.md` |
| 2. Contexto (PDF 1) | Ficha de 10 dimensiones, validación y ajustes del equipo | ✅ | `engine.context_sheet`, pantalla de ficha, `Proyecto.ajustes` |
| 3. Evaluación | 56 salvaguardas, 5 estados, evidencia, indicadores con fórmulas oficiales | ✅ | `engine.evaluate` (3 lotes), `state.validar_resultado`, `state.indicadores` |
| 3.5–4. Reporte | Resumen ejecutivo (5 puntos), 5 riesgos, 5 iniciativas, dashboard | ✅ | `engine.report`, `state.validar_reporte`, `ui.tablero` |
| 5. PDF 2 | Cambios con cita, validación del auditor, v2 sin perder v1, reporte comparativo | ✅ | `engine.analyze_initiatives`, `Proyecto.decidir`/`crear_v2`, `engine.updated_report` |

## Entregables

| Entregable | Estado | Cómo obtenerlo |
|---|---|---|
| 1. Agente funcional + prompt maestro + configuración | ✅ | `streamlit run app.py`; prompt en `docs/` (`scripts/exportar_prompt.py`) |
| 2. Matriz CIS IG1 (v1 y v2, Excel/CSV) | ✅ | Botones "Excel completo" y "Matriz v1/v2 (CSV)" |
| 3. Reporte ejecutivo (máx. 5 páginas) | ✅ | Botón "Reporte ejecutivo (PDF)": A4, con v1 y v2. Con la evaluación de prueba ocupa 5 páginas; también se puede descargar en HTML |
| 4. Demostración de 8 minutos | ⏳ equipo | Ejemplos sugeridos abajo |

---

## Bitácora de lo realizado

### 2026-11-03 — Primera versión
- Chatbot en Python + Streamlit que conversaba con el responsable de seguridad, hacía preguntas Sí/No y resumía controles cubiertos y no cubiertos.
- **Decisión:** cambiar de la API de Claude a la **API gratuita de Google Gemini** (`google-genai`).
- `CLAUDE.md`, `.claude/settings.json` con notificaciones, `.env.example` y pruebas sin API.

### Diseño y robustez
- Rediseño visual "craft oscuro" (tokens OKLCH, anillo de implementación con CSS, tarjeta de progreso y checkmark al terminar).
- Se eliminó de la interfaz el nombre del modelo en uso.
- Corregido: la última pregunta Sí/No seguía clicable mientras se procesaba. Ahora las tareas lentas se ejecutan al final del script con los controles deshabilitados.
- **Errores 503 y timeouts de Gemini:** reintentos del SDK (4 intentos sobre 408/429/5xx, timeouts y conexión) y tiempo límite de 30 s, o 120 s en llamadas con PDF o salidas largas. Los errores se muestran en español.
- README con el paso a paso para reproducir desde cero y revisión de secretos antes de subir a GitHub. `.claude/` quedó fuera del repositorio.

### Catálogo CIS oficial
- `scripts/importar_cis.py` convierte el Excel oficial de CIS v8.1.2 a JSON local, sin versionar por la licencia CC BY-NC-ND 4.0. Corrige los ids que Excel guarda como número (3.10 → 3.1).
- El agente evalúa con la **descripción oficial** de cada salvaguarda y usa el sector de la empresa (hospital, comercio, universidad…) para priorizar riesgos.
- **Decisión:** evaluar **solo IG1** (56 salvaguardas en 15 controles; los controles 13, 16 y 18 no tienen salvaguardas IG1).

### 2026-11-17 — Rediseño según la actividad M3.6 ("Agente V1")
- **Decisiones:** nombre **Centinela IG1**, **eliminar ISO 27002 por completo**, conservar por el momento las preguntas Sí/No como apoyo opcional (después se quitaron, ver abajo) y guardar automáticamente en `evaluaciones/`.
- Escala de 5 estados con valores (1, 0.5, 0, —, —) y aplicabilidad (Aplica / No aplica / Por determinar).
- Flujo por etapas: contexto → ficha → evaluación → reporte v1 → PDF 2 → v2.
- **Protecciones contra las penalizaciones aplicadas por el código**, cada una con su prueba:
  - salvaguardas omitidas por el modelo → se completan como No verificado;
  - cada cita se comprueba contra el texto del PDF (`pypdf`, cobertura de palabras ≥ 0.8) y la página se corrige si está mal;
  - "No implementado" sin cita → No verificado (R8);
  - indicadores calculados solo en Python, con "No determinable" si no hay base;
  - los riesgos e iniciativas solo pueden citar salvaguardas que son brecha;
  - la v1 es inmutable al cerrarse y la v2 aplica solo los cambios aprobados con cita verificada;
  - temperatura 0 y semilla fija.
- Exportación: Excel (Contexto, Matriz v1/v2, Indicadores, Riesgos, Roadmaps, Cambios PDF 2, Ajustes), CSV y reporte HTML.
- Reporte ejecutivo descargable directamente en **PDF** (`chatbot/reporte_pdf.py`, con `fpdf2`). La sección v2 resume los riesgos y las iniciativas originales para no repetir la v1. La evaluación de prueba completa (v1 + v2) ocupa 5 páginas.
- El dashboard (app y PDF) ya no muestra las fórmulas de los indicadores; se siguen calculando con las fórmulas oficiales en `state.indicadores()`.
- **Navegación entre secciones de un análisis:**
  - siempre Contexto, Reporte inicial y Reporte actualizado;
  - la Evaluación 56 y la Validación PDF 2 solo mientras son el paso en curso;
  - lo ya cerrado es de solo lectura.
  - La matriz v1 ahora se ve abierta en el reporte inicial. Se quitaron las copias plegables del reporte inicial dentro de la validación del PDF 2 y del reporte actualizado, porque ya se llega a él desde la barra.
- **Ficha de contexto exportable en PDF y HTML** (`ficha_pdf`, `ficha_html`). Incluye las 10 dimensiones con página, cita y verificación de cada hallazgo, la información faltante, las ambigüedades, el perfil de riesgo y los ajustes del equipo (Etapa 2.5). Se descarga desde la propia ficha y desde los entregables de los reportes.
- Bitácora de validaciones visible en la barra lateral.

### 2026-11-17 — Ajustes posteriores
- Se quitó el botón "Prompt maestro (.md)" de la app. La actividad lo pide como entregable, no como función. Ahora se genera con `scripts/exportar_prompt.py` en `docs/`.
- El chat con Centinela solo está disponible en la ficha de contexto (después de analizar el PDF 1), en el reporte inicial y en el reporte actualizado. No aparece antes de subir algo ni durante la evaluación o la validación de cambios.
- Se quitó el botón "Usar una empresa ficticia de ejemplo": el contexto se carga como PDF o como texto pegado.
- **Se eliminaron las preguntas Sí/No / No lo sé al cliente** para apegarse a la actividad. El agente ya no las genera (prompt y esquema), la app no las muestra y no cuentan en la matriz. Las respuestas de evaluaciones guardadas antes del cambio se descartan al abrirlas y la salvaguarda queda No verificado, con registro en la bitácora.
- README con capacidades, entradas aceptadas y salidas. Este archivo, PROGRESS.md.

---

## Verificación

- **23 pruebas automáticas** sin API ni Excel (`python -m pytest -q`): reglas y penalizaciones, flujo completo simulado, exportación, importador y reintentos.
- **Prueba real con Gemini** y dos PDF ficticios, de punta a punta:
  - ficha con 20 de 20 citas verificadas;
  - evaluación v1 con implementación 31.6 % y cobertura 33.9 %, idéntica en dos corridas;
  - v2 con 3 cambios aprobados: implementación 42.5 %;
  - el chat respondió "¿por qué 10.1 está implementada?" citando página y texto.
- Correcciones que el sistema hizo al modelo, **útiles para la demo**:
  - Gemini marcó 7.1 y 7.2 como "No implementado" sin cita; el sistema las dejó en No verificado.
  - Gemini propuso 1.1 como "Implementado" con trabajos pendientes en el PDF 2. Se ajustó la instrucción (ahora propone "Parcial") y la aprobación del auditor sigue siendo el control final.
- Visibilidad del chat comprobada por etapa con `streamlit.testing` (AppTest).

## Pendientes

- [ ] **Commit y push** (lo hace el equipo): `app.py`, `chatbot/`, `tests/`, `requirements.txt`, `README.md`, `CLAUDE.md`, `PROGRESS.md`, `docs/`, `scripts/exportar_prompt.py`.
- [ ] Probar con los **PDF reales del profesor** (solo se probó con casos ficticios).
- [ ] Revisar el PDF con el caso real del profesor: los textos del modelo varían y podría pasar de **5 páginas**.
- [ ] Preparar la **demo de 8 minutos**: una decisión correcta (cita verificada) y un error o limitación (7.1/7.2 o 1.1 arriba).
- [ ] Responder las **preguntas de reflexión** de la actividad (dificultad principal, corrección humana, impacto de las iniciativas, etc.).
- [ ] **Parte 2 de la actividad**, cuando llegue.

## Limitaciones conocidas

- Plan gratuito de Gemini: latencia variable y saturación (503). Si pasa, usar `GEMINI_MODEL=gemini-3.1-flash-lite`.
- PDF escaneados sin texto: las citas no se pueden verificar y todo queda No verificado.
