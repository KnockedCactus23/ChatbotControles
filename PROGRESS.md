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
- Rediseño visual "craft oscuro", después reemplazado por "Dictamen técnico" (tokens OKLCH, anillo de implementación con CSS, tarjeta de progreso y checkmark al terminar).
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
  - Las matrices de ambos reportes van plegadas y se despliegan con un clic. Se probó mostrarlas abiertas, pero alargaban demasiado la página. Se quitaron las copias plegables del reporte inicial dentro de la validación del PDF 2 y del reporte actualizado, porque ya se llega a él desde la barra.
- **Botones por sección y entregables separados por versión:**
  - Contexto: solo la ficha (PDF/HTML).
  - Reporte inicial: matriz v1, Excel v1 y reporte ejecutivo inicial (PDF/HTML).
  - Reporte actualizado: matriz v2, Excel v2 y reporte ejecutivo final (PDF/HTML).
  - El Excel v2 y el reporte final no incluyen la matriz ni el reporte de la v1; solo la comparación de indicadores. Cada reporte PDF de la evaluación de prueba ocupa 3 páginas.
- **Cambio de proveedor: de Gemini a la API de Claude** (Claude Sonnet 5.5 por defecto; Haiku 5.5 para depurar). Optimizado para ahorrar tokens sin bajar la calidad:
  - caché de prompts donde se reutiliza (lotes de la evaluación, ficha regenerada, chat);
  - documento como texto paginado en vez del PDF;
  - ficha resumida y JSON compacto en las etapas posteriores;
  - `max_tokens` por etapa.
  - Se añadieron el panel de consumo (tokens, caché y costo estimado por llamada) y el reintento del servidor si el filtro de seguridad declina.
  - Ya no hay temperatura 0 ni semilla (Sonnet 5.5 no las admite); la consistencia la dan las reglas del código.
  - Corrección tras la primera prueba con Haiku:
    - **400 "compiled grammar is too large"** en la ficha. Se resolvió compactando los esquemas con `$defs` (6.5K → 2.5K caracteres, mismas restricciones), verificado contra la API con Haiku y Sonnet.
    - Haiku en esfuerzo "high" agotaba el límite razonando; ahora usa su valor por defecto, "medium".
    - La caché no se leía entre lotes porque el esquema cambiaba por lote; ahora es el mismo.
  - Prueba real con Haiku 5.5 sobre NexoPay (ficha + 56 salvaguardas): 39 de 39 citas de la ficha verificadas, cobertura 69.6 %, implementación 48.7 %, US$0.031 en total. Los lotes 2 y 3 leyeron 32K tokens de la caché.
  - El modelo se elige en un desplegable de la barra lateral (ya no en `.env`). Se guarda con la evaluación y queda fijo desde la ficha.
  - Pendiente: corrida completa con Sonnet 5.5 (≈ US$1–1.60).
- **Correcciones del análisis del prompt (F1–F10, A–D).** Se aplicaron todas salvo B3 y D2 (ver abajo).
  - Etapa 5: una decisión por salvaguarda relacionada, con segunda pasada si falta alguna; actualización de evidencia; pendientes por salvaguarda; alertas de contradicciones y fechas.
  - Etapa 5.6: situación de riesgos e iniciativas calculada en código, severidad residual, 5 riesgos vigentes (v2) para el roadmap y solo cambios aprobados como mitigación.
  - Prompt maestro: tabla de decisión Parcial / No implementado, pertinencia de citas, BYOD, "por determinar", criterios de severidad y esfuerzo, iniciativas dentro de IG1, R12 concreto y la guía sectorial solo para ponderar.
  - Prueba real con Gemini sobre NexoPay: las 17 salvaguardas relacionadas recibieron decisión (antes, 8 cambios se omitían), 7.3 actualizó su evidencia y el riesgo 1 quedó mitigado. Ninguna iniciativa quedó "completada" con salvaguardas sin implementar.
  - **No aplicadas:** B3 (la actividad exige exactamente 5 riesgos y 5 iniciativas; ahora el sistema avisa cuando el formato obliga a incluir uno sin brecha) y D2 (corregir la v1 rompería su inmutabilidad, que es requisito; las correcciones respaldadas por el PDF 2 entran como actualización de evidencia en la v2).
- **Nueva identidad visual "Dictamen técnico" con modos Día y Noche** (2026-11-18):
  - Diseñada como sistema de diseño (tokens, tipografía, 7 componentes y portada). El cuaderno para revisión está en `docs/identidad_visual_centinela.pdf`.
  - Aplicada a la app: temas de Streamlit en `config.toml`, tokens con alias en `ui.py`, marcas de estado por forma y Newsreader en títulos y cifras.
  - Selector Día/Noche en la barra lateral, que recarga y vuelve a la misma evaluación y sección por la URL.
  - Contraste verificado en ambos modos; la etiqueta de estado y las celdas de control llevan el texto en tinta, nunca en color de estado.
- **Desplazamiento corregido:** la página ya no baja sola al cambiar de sección o al abrir una matriz. La causa era el chat fijo abajo de Streamlit, que activa "pegarse al final"; ahora el chat va en su sección y cada sección nueva empieza arriba. Comprobado en el navegador.
- **Ficha de contexto exportable en PDF y HTML** (`ficha_pdf`, `ficha_html`). Incluye las 10 dimensiones con página, cita y verificación de cada hallazgo, la información faltante, las ambigüedades, el perfil de riesgo y los ajustes del equipo (Etapa 2.5). Se descarga desde la propia ficha y desde los entregables de los reportes.
- Bitácora de validaciones visible en la barra lateral.

### 2026-11-17 — Ajustes posteriores
- Se quitó el botón "Prompt maestro (.md)" de la app. La actividad lo pide como entregable, no como función. Ahora se genera con `scripts/exportar_prompt.py` en `docs/`.
- El chat con Centinela solo está disponible en la ficha de contexto (después de analizar el PDF 1), en el reporte inicial y en el reporte actualizado. No aparece antes de subir algo ni durante la evaluación o la validación de cambios.
- Se quitó el botón "Usar una empresa ficticia de ejemplo": el contexto se carga como PDF o como texto pegado.
- **Se eliminaron las preguntas Sí/No / No lo sé al cliente** para apegarse a la actividad. El agente ya no las genera (prompt y esquema), la app no las muestra y no cuentan en la matriz. Las respuestas de evaluaciones guardadas antes del cambio se descartan al abrirlas y la salvaguarda queda No verificado, con registro en la bitácora.
- README con capacidades, entradas aceptadas y salidas. Este archivo, PROGRESS.md.

### 2026-11-18 — Rediseño visual (mockup aprobado)
- Mockup en `mockup/resumen.html`, iterado con el equipo; después se implementó en la app.
- **Identidad nueva:** Día "Pizarra cálida" (menos brillante) y Noche "Grafito". Solo Geist y Geist Mono; texto secundario más oscuro (pensado para ≥ 4.5:1).
- **Reportes como dashboard (`chatbot/panel.py`)**, con más gráficas y menos texto. El texto completo sigue en los PDF/HTML descargables.
  - KPIs del mismo tamaño y barra apilada de las 56 salvaguardas.
  - Postura con titular y cifras «X de Y».
  - Estado por control con segmentos.
  - Riesgos plegables y roadmap con chips de riesgo y esfuerzo en bloques.
  - Matriz plegable con filtros y pendientes.
  - El reporte actualizado muestra los deltas frente a v1, «Cambió en v2», la situación de cada riesgo y el estado de cada iniciativa.
- **Interacciones:**
  - resaltado de un estado en toda la página desde la leyenda;
  - riesgos ↔ iniciativas al pasar el cursor;
  - índice lateral que marca la sección;
  - menú «Descargar»;
  - etapas como pasos.
- **Esquema y prompt del reporte:** campos nuevos (`titular`, `datos_clave`, `brechas_clave`, `bases`, `nombre_corto`), validados contra la matriz (`validar_presentacion`). Las evaluaciones guardadas antes se ven con respaldos hasta regenerar su reporte.
- Dos pruebas nuevas (38 en total). Revisado en el navegador: Día, Noche, 375px y escritorio, sin errores de consola.

- **Vista ejecutiva, Fase 1 (datos), 2026-11-19:**
  - Esquema: probabilidad e impacto (1-5) con justificación, `consecuencia_negocio`, horizonte de iniciativas, nivel de riesgo, veredicto, 3 impactos de negocio y 3 peticiones.
  - Código: severidad por probabilidad × impacto, 7 áreas con su madurez, proyección estimada, valores por defecto para evaluaciones anteriores y validación de jerga y cifras.
  - Prompt de evaluación: la cita debe ser un solo pasaje copiado carácter por carácter (lo necesitará el visor de evidencia).
  - Ejemplo real con Haiku 5.5 sobre una copia de NEXOPAY (US$0.011): un solo aviso (una consecuencia de 21 palabras). Cinco pruebas nuevas (43).

- **Vista ejecutiva, Fase 2 (vista), 2026-11-19:** selector Ejecutivo / Técnico en los dos reportes; `chatbot/ejecutiva.py` con las 7 secciones y animación de entrada (cifras y barras, sin animar con movimiento reducido). Estados como punto de color + palabra en toda la app. Evaluaciones anteriores: nivel calculado, plazos estimados y avisos donde faltan campos. Capturas Día/Noche a 1440 y 375 px sobre una copia de NEXOPAY con el reporte de Haiku. Prueba nueva (44). «Madurez por área» se cambió por «Estado por control»: una barra apilada por control, sin ids, de peor a mejor.

- **Vista ejecutiva, Fase 3 (interacciones), 2026-11-19:** filtro por estado en ambas vistas (controles y matriz, aviso «Mostrando N · Quitar filtro», estados sin medidas deshabilitados) y panel lateral de riesgos e iniciativas (consecuencia, probabilidad e impacto, iniciativas que lo reducen, aporte estimado a la madurez; salvaguardas solo en la técnica). Probado en el navegador con clic, teclado, Esc y clic fuera; móvil a pantalla completa. Prueba nueva (45).

- **Vista ejecutiva, Fase 4 (vista técnica), 2026-11-19:** severidad como punto + palabra con probabilidad × impacto, columna de plazo en el roadmap y postura completa sin «Leer más». Revisado con una v2 de prueba (copia de NEXOPAY en el scratchpad, 3 cambios aprobados): ambas vistas del Reporte actualizado funcionan, con los cambios respecto a la v1. Prueba nueva (46).

---

## Verificación

- **46 pruebas automáticas** sin API ni Excel (`python -m pytest -q`): reglas y penalizaciones, flujo completo simulado, exportación, importador y reintentos.
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
- [ ] Generar un reporte real con Sonnet 5.5 para ver los campos nuevos del dashboard (titular, cifras «X de Y», brechas cortas, nombres cortos de riesgo). Las evaluaciones guardadas usan respaldos. Es una llamada con costo.
- [ ] Vista ejecutiva: Fases 5 y 6 (vista, interacciones, vista técnica, visor de evidencia, exportaciones).
- [ ] Decidir si `mockup/` se versiona o se agrega a `.gitignore`.

## Limitaciones conocidas

- La API de Claude tiene costo (≈ US$1 por evaluación completa con Sonnet 5.5, según la estimación). El consumo real se guarda en cada evaluación (`consumo` en su JSON); el panel de la app se quitó el 2026-11-19.
- PDF escaneados sin texto: las citas no se pueden verificar y todo queda No verificado.
