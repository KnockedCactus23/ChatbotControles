"""Centinela IG1 — agente de evaluación de CIS Controls v8.1 IG1 (actividad M3.6).

Etapas: contexto (PDF 1) → validación de la ficha → evaluación de las 56 salvaguardas →
reporte inicial (v1) → avance de iniciativas (PDF 2) con validación del auditor → reporte (v2).

Las llamadas a Gemini se piden con ``pedir()`` y se ejecutan al FINAL del script, cuando la
página ya se dibujó con los controles deshabilitados; así no quedan botones viejos activos.
Todo se guarda automáticamente en ``evaluaciones/`` para conservar v1 y v2 entre sesiones.
"""

import streamlit as st
from dotenv import load_dotenv

from chatbot import almacen, exportar, ui
from chatbot.controls import CatalogoNoEncontrado, atribucion, catalogo
from chatbot.documentos import Documento, leer_pdf
from chatbot.engine import ErrorChatbot, Motor
from chatbot.prompts import NOMBRE_AGENTE
from chatbot.reporte_pdf import reporte_pdf
from chatbot.state import Proyecto, ahora, estado_control

load_dotenv()
st.set_page_config(page_title=NOMBRE_AGENTE, page_icon=":material/shield:", layout="wide")
st.html(ui.CSS)

AVATAR = {"assistant": ":material/shield:", "user": ":material/person:"}
TITULO_TAREA = {
    "explicar": ("Preparando la explicación", "El agente describe su objetivo, alcance y criterios…"),
    "ficha": ("Interpretando el contexto", "Leo el documento y armo la ficha por dimensiones, verificando cada cita…"),
    "evaluar": ("Evaluando las 56 salvaguardas", "Comparo el documento con la descripción oficial de cada salvaguarda IG1…"),
    "reporte": ("Redactando el reporte inicial", "Resumen ejecutivo, cinco riesgos y cinco iniciativas a partir de la matriz…"),
    "pdf2": ("Analizando el avance de iniciativas", "Comparo el PDF 2 con la evaluación inicial; propondré cambios para tu validación…"),
    "v2": ("Actualizando el diagnóstico", "Recalculo indicadores y actualizo riesgos y roadmap con los cambios aprobados…"),
    "consulta": ("Consultando al agente", "Reviso la evidencia registrada…"),
}

try:
    catalogo()
except CatalogoNoEncontrado as e:
    st.error(f"Falta el catálogo de CIS Controls. {e}", icon=":material/dataset:")
    st.stop()


def nuevo(proyecto: Proyecto | None = None):
    st.session_state.proyecto = proyecto or Proyecto()
    st.session_state.tarea = None
    st.session_state.impl_previa = 0.0
    st.session_state.estados_previos = {}


if "proyecto" not in st.session_state or not hasattr(st.session_state.proyecto, "ficha_validada"):
    nuevo()
if "motor" not in st.session_state:
    try:
        st.session_state.motor = Motor()
    except ErrorChatbot as e:
        st.session_state.motor = None
        st.session_state.error_inicio = str(e)

p: Proyecto = st.session_state.proyecto
motor: Motor | None = st.session_state.motor
tarea = st.session_state.tarea
ocupado = tarea is not None


def guardar():
    if p.documentos:
        almacen.guardar(p)


def pedir(tipo: str, **datos):
    st.session_state.tarea = {"tipo": tipo, **datos}
    st.rerun()


def decir(texto: str, rol: str = "assistant"):
    p.chat.append({"tipo": "texto", "role": rol, "content": texto})


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    ind = p.vigente.indicadores() if p.vigente else None
    st.html(ui.postura(ind, st.session_state.impl_previa))
    st.session_state.impl_previa = (ind or {}).get("implementacion") or 0.0
    if p.vigente:
        estados = {c.id: estado_control(p.vigente.matriz, c.id) for c in catalogo().controles}
        previos = st.session_state.estados_previos
        cambiados = {cid for cid, e in estados.items() if previos and previos.get(cid) != e}
        st.html(ui.matriz_controles(estados, cambiados))
        st.session_state.estados_previos = estados

    guardadas = almacen.listar()
    if guardadas:
        opciones = {g["id"]: f'{g["nombre"]} · {g["creado"]} · {g["versiones"]} versión(es)' for g in guardadas}
        elegida = st.selectbox("Evaluaciones guardadas", list(opciones), format_func=opciones.get, disabled=ocupado,
                               index=list(opciones).index(p.id) if p.id in opciones else 0)
        if st.button("Abrir evaluación", icon=":material/folder_open:", use_container_width=True,
                     disabled=ocupado or elegida == p.id):
            nuevo(almacen.cargar(elegida)); st.rerun()
    if st.button("Nueva evaluación", icon=":material/add:", use_container_width=True, disabled=ocupado):
        nuevo(); st.rerun()
    if p.avisos:
        with st.expander(f"Bitácora de validaciones · {len(p.avisos)}"):
            st.html(ui.avisos(p.avisos))

# ------------------------------------------------------------------ cuerpo
st.html(ui.encabezado(p.etapa))
if motor is None:
    st.error(f"{st.session_state.get('error_inicio')}. Copia `.env.example` como `.env` y pon tu `GEMINI_API_KEY` "
             "(gratis en aistudio.google.com/apikey).", icon=":material/key:")
    st.stop()

lugar_progreso = st.empty()  # cada etapa lo reubica junto a su botón principal


def exportes():
    st.html(ui.seccion("Entregables", "Matriz (Excel con todas las hojas o CSV) y reporte ejecutivo en PDF o HTML."))
    col = st.columns(5)
    col[0].download_button("Excel completo", exportar.excel(p), file_name=f"centinela_ig1_{p.id}.xlsx",
                           icon=":material/table_view:", use_container_width=True)
    if p.v1:
        col[1].download_button("Matriz v1 (CSV)", exportar.csv_matriz(p, p.v1), file_name=f"matriz_v1_{p.id}.csv",
                               icon=":material/csv:", use_container_width=True)
    if p.v2:
        col[2].download_button("Matriz v2 (CSV)", exportar.csv_matriz(p, p.v2), file_name=f"matriz_v2_{p.id}.csv",
                               icon=":material/csv:", use_container_width=True)
    col[3].download_button("Reporte ejecutivo (PDF)", reporte_pdf(p), file_name=f"reporte_{p.id}.pdf",
                           mime="application/pdf", icon=":material/picture_as_pdf:", use_container_width=True)
    col[4].download_button("Reporte ejecutivo (HTML)", exportar.reporte_html(p), file_name=f"reporte_{p.id}.html",
                           icon=":material/article:", use_container_width=True)


def reporte_v1():
    rep = p.v1.reporte
    riesgos = rep.get("riesgos", [])
    st.html(ui.seccion("Dashboard ejecutivo · v1", "Valores calculados por el sistema a partir de la matriz."))
    st.html(ui.tablero(p.v1.indicadores(), len(riesgos), len(rep.get("iniciativas", []))))
    st.html(ui.seccion("Resumen ejecutivo"))
    st.html(ui.resumen_ejecutivo(rep.get("resumen_ejecutivo", {})))
    st.html(ui.seccion("Cinco riesgos principales", "Cada riesgo se relaciona solo con salvaguardas que son brecha en la matriz."))
    st.html(ui.riesgos(riesgos))
    st.html(ui.seccion("Roadmap de cinco iniciativas"))
    st.html(ui.roadmap(rep.get("iniciativas", []), [r["titulo"] for r in riesgos]))
    with st.expander("Matriz de las 56 salvaguardas · v1 (evaluación inicial)"):
        st.html(ui.matriz56(p.v1, p.documentos))


etapa = p.etapa

# --------------------------------------------------------- Etapa 1-2: contexto
if etapa == "contexto" and not p.ficha:
    st.html(ui.titular(f"Soy {NOMBRE_AGENTE}.",
                       "Consultor de ciberseguridad especializado en CIS Controls v8.1. Interpreto el contexto de tu "
                       "organización, evalúo las 56 salvaguardas IG1 con base solo en la evidencia documental y propongo "
                       "iniciativas para reducir tus riesgos. Lo que no esté documentado queda como «No verificado»."))
    if st.button("Prueba preliminar: ¿cómo trabajas?", icon=":material/psychology:", disabled=ocupado):
        decir("Explica cuál es tu objetivo, qué salvaguardas CIS evaluarás, cuáles son tus criterios para determinar el "
              "estado de implementación y qué harás cuando no tengas suficiente información.", "user")
        pedir("explicar")
    st.html(ui.seccion("PDF 1 · Contexto empresarial", "Carga el documento del caso. Cada conclusión del agente citará su página."))
    archivo = st.file_uploader("PDF 1 — Contexto empresarial", type=["pdf"], disabled=ocupado, label_visibility="collapsed")
    with st.expander("¿No tienes el PDF? Pega el contexto como texto"):
        texto = st.text_area("Contexto de la empresa", height=180, disabled=ocupado)
    lugar_progreso = st.empty()
    if st.button("Analizar contexto", type="primary", icon=":material/plagiarism:", disabled=ocupado or not (archivo or texto.strip())):
        if archivo:
            datos = archivo.getvalue()
            try:
                paginas = leer_pdf(datos)
            except Exception:
                st.error("No pude leer el PDF. Verifica que no esté protegido o dañado."); st.stop()
            if not any(t.strip() for t in paginas):
                st.warning("El PDF no tiene texto extraíble (¿es un escaneo?). Las citas no podrán verificarse.")
            p.documentos["pdf1"] = Documento("pdf1", archivo.name, "pdf", paginas, almacen.guardar_pdf(p, "pdf1", datos))
        else:
            p.documentos["pdf1"] = Documento("pdf1", "Texto proporcionado", "texto", [texto.strip()])
        guardar()
        pedir("ficha")

elif etapa == "contexto":
    st.html(ui.titular("Ficha de contexto empresarial",
                       "Antes de evaluar, valida la interpretación del agente (R1). Cada hallazgo indica si su cita se "
                       "encontró en el documento."))
    st.html(ui.ficha(p.ficha, p.documentos["pdf1"].etiqueta))
    st.html(ui.seccion("Validación del equipo (Etapa 2.4)",
                       "¿Interpretó bien la infraestructura? ¿Identificó los servicios críticos? ¿Confundió servicios cloud con "
                       "infraestructura propia? ¿Supuso herramientas que no aparecen? ¿Identificó la información faltante? "
                       "¿Hay contradicciones o ambigüedades?"))
    ajuste = st.text_area("Ajuste a la interpretación (se registra como ajuste del agente, Etapa 2.5)", disabled=ocupado,
                          placeholder="Ej.: Microsoft 365 es un servicio contratado, no infraestructura propia.")
    lugar_progreso = st.empty()
    c1, c2 = st.columns([1, 1.4])
    if c1.button("Regenerar la ficha con este ajuste", icon=":material/edit_note:", disabled=ocupado or not ajuste.strip(),
                 use_container_width=True):
        p.ajustes.append({"fecha": ahora(), "texto": ajuste.strip()})
        guardar()
        pedir("ficha", ajuste=ajuste.strip())
    if c2.button("Validar la ficha y evaluar las 56 salvaguardas", type="primary", icon=":material/fact_check:",
                 disabled=ocupado, use_container_width=True):
        p.ficha_validada = True
        guardar()
        pedir("evaluar")
    if p.ajustes:
        with st.expander(f"Ajustes registrados · {len(p.ajustes)}"):
            for a in p.ajustes:
                st.markdown(f"- **{a['fecha']}** — {a['texto']}")

# ----------------------------------------------------- Etapa 3: evaluación
elif etapa == "evaluacion":
    ind = p.v1.indicadores()
    st.html(ui.titular("Evaluación inicial de las 56 salvaguardas",
                       "Cada estado se apoya en una cita verificada del documento. Lo que no está documentado queda como "
                       "«No verificado» (nunca como incumplimiento)."))
    st.html(ui.tablero(ind))
    st.html(ui.seccion("Cerrar la evaluación inicial",
                       "Genera el resumen ejecutivo, los cinco riesgos y el roadmap. La versión v1 queda fija como línea base."))
    lugar_progreso = st.empty()
    if st.button("Generar el reporte inicial (cierra la versión v1)", type="primary", icon=":material/description:",
                 disabled=ocupado):
        pedir("reporte")
    st.html(ui.seccion("Matriz de las 56 salvaguardas · v1", "Incluye todas las salvaguardas, también las no verificadas."))
    st.html(ui.matriz56(p.v1, p.documentos))

# ------------------------------------------------- Etapas 3.5-4: reporte v1
elif etapa == "reporte":
    st.html(ui.titular("Reporte inicial", f"{p.nombre} · línea base v1 del {p.v1.fecha}. Esta versión ya no se modifica."))
    reporte_v1()
    exportes()
    st.html(ui.seccion("Etapa 5 · Avance de iniciativas (PDF 2)",
                       "El agente parte de esta evaluación (no de cero) y propone cambios que tú validas como auditor."))
    archivo2 = st.file_uploader("PDF 2 — Avance de iniciativas", type=["pdf"], disabled=ocupado, label_visibility="collapsed")
    lugar_progreso = st.empty()
    if st.button("Analizar el avance de iniciativas", type="primary", icon=":material/upload_file:",
                 disabled=ocupado or not archivo2):
        datos = archivo2.getvalue()
        p.documentos["pdf2"] = Documento("pdf2", archivo2.name, "pdf", leer_pdf(datos), almacen.guardar_pdf(p, "pdf2", datos))
        guardar()
        pedir("pdf2")

# ------------------------------------------------ Etapa 5: validar cambios
elif etapa == "iniciativas":
    st.html(ui.titular("Validación de cambios propuestos",
                       "Actúa como auditor: aprueba los cambios con sustento, rechaza los que no lo tengan y deja pendientes "
                       "los que requieran información. Solo los aprobados actualizan las métricas (R11, R12)."))
    if p.v2 and not p.v2.cerrada:
        lugar_progreso = st.empty()
        if st.button("Generar el reporte actualizado", type="primary", icon=":material/refresh:", disabled=ocupado):
            pedir("v2")
    elif not p.iniciativas and not p.cambios:
        lugar_progreso = st.empty()
        if st.button("Reintentar el análisis del PDF 2", type="primary", icon=":material/refresh:", disabled=ocupado):
            pedir("pdf2")
    else:
        st.html(ui.seccion("Iniciativas reportadas en el PDF 2"))
        st.html(ui.iniciativas_pdf2(p.iniciativas))
        st.html(ui.seccion("Propuesta de actualización",
                           "Los cambios sin cita verificable en el PDF 2 no se pueden aprobar."))
        if not p.cambios:
            st.info("El agente no propuso cambios de estado: la evidencia del PDF 2 no fue suficiente.")
        for c in p.cambios:
            st.html(ui.cambio_fila(c))
            opciones = ["pendiente", "aprobado", "rechazado"] if (c.cita_verificada and c.estado_propuesto != c.estado_inicial) \
                else ["pendiente", "rechazado"]
            etiquetas = {"pendiente": "Pendiente", "aprobado": "Aprobar", "rechazado": "Rechazar"}
            decision = st.radio(f"Decisión {c.id}", opciones, index=opciones.index(c.decision) if c.decision in opciones else 0,
                                format_func=etiquetas.get, horizontal=True, key=f"dec_{c.id.replace('.', '_')}",
                                disabled=ocupado, label_visibility="collapsed")
            if decision != c.decision:
                p.decidir(c.id, decision); guardar()
        aprobados = sum(c.decision == "aprobado" for c in p.cambios)
        lugar_progreso = st.empty()
        if st.button(f"Aplicar {aprobados} cambio(s) aprobado(s) y actualizar el diagnóstico", type="primary",
                     icon=":material/published_with_changes:", disabled=ocupado):
            p.crear_v2(); guardar()
            pedir("v2")
    with st.expander("Reporte inicial (v1) — referencia"):
        reporte_v1()

# --------------------------------------------- Etapa 5.6: reporte actualizado
elif etapa == "actualizado":
    rep = p.v2.reporte
    riesgos_v1 = p.v1.reporte.get("riesgos", [])
    aprobados = [c.id for c in p.cambios if c.decision == "aprobado"]
    st.html(ui.titular("Diagnóstico actualizado",
                       f"{p.nombre} · v2 del {p.v2.fecha}. Refleja solo las mejoras documentadas y aprobadas; la v1 se conserva."))
    st.html(ui.seccion("Dashboard ejecutivo · v2 frente a v1"))
    st.html(ui.tablero(p.v2.indicadores(), len(rep.get("riesgos", [])), len(rep.get("roadmap", [])), p.v1.indicadores()))
    st.html(ui.comparacion(p.v1.indicadores(), p.v2.indicadores(), aprobados))
    st.html(ui.seccion("Cambios derivados del PDF 2"))
    st.html(f"<p class='ficha-resumen'>{ui.esc(rep.get('resumen_cambios'))}</p>")
    for c in p.cambios:
        st.html(ui.cambio_fila(c) + f"<p class='aviso' style='margin:0 0 10px 14px'>Decisión del auditor: <b>{c.decision}</b></p>")
    st.html(ui.seccion("Riesgos que cambiaron y riesgos que permanecen"))
    st.html(ui.riesgos(riesgos_v1, rep.get("riesgos")))
    st.html(ui.seccion("Iniciativas del roadmap original: completadas o en progreso"))
    st.html(ui.roadmap(p.v1.reporte.get("iniciativas", []), [r["titulo"] for r in riesgos_v1], rep.get("iniciativas_estado")))
    st.html(ui.seccion("Roadmap actualizado"))
    st.html(ui.roadmap(rep.get("roadmap", []), [r["titulo"] for r in riesgos_v1]))
    st.html(ui.seccion("Resumen ejecutivo actualizado"))
    st.html(ui.resumen_ejecutivo(rep.get("resumen_ejecutivo", {})))
    st.html(ui.seccion("Matrices de las 56 salvaguardas", "Las salvaguardas modificadas en v2 aparecen resaltadas."))
    t1, t2 = st.tabs(["v2 · Actualizada", "v1 · Inicial"])
    with t2:
        st.html(ui.matriz56(p.v1, p.documentos))
    with t1:
        st.html(ui.matriz56(p.v2, p.documentos, set(aprobados)))
    exportes()
    with st.expander("Reporte inicial (v1) completo"):
        reporte_v1()

# ------------------------------------------------------- consultas al agente
mensajes = [m for m in p.chat if m["tipo"] == "texto"]
if mensajes:
    st.html(ui.seccion("Conversación con el agente"))
    for m in mensajes:
        with st.chat_message(m["role"], avatar=AVATAR[m["role"]]):
            st.markdown(m["content"])
# El chat solo se ofrece cuando hay algo que explicar: la ficha del PDF 1 ya generada o un reporte.
# El historial se sigue mostrando en todas las etapas (incluye la prueba preliminar y los errores).
CHAT_ACTIVO = (etapa == "contexto" and bool(p.ficha)) or etapa in ("reporte", "actualizado")
pregunta_usuario = st.chat_input(f"Pregunta a {NOMBRE_AGENTE} por qué tomó una decisión o qué falta…",
                                 disabled=ocupado) if CHAT_ACTIVO else None
if pregunta_usuario:
    decir(pregunta_usuario, "user")
    pedir("consulta", pregunta=pregunta_usuario)

st.html(ui.atribucion_html(atribucion()))

# ------------------------------------------- tareas lentas (al final del script)
if tarea:
    titulo, texto = TITULO_TAREA[tarea["tipo"]]
    with lugar_progreso.container():
        tarjeta = st.empty()
        tarjeta.html(ui.tarjeta_progreso(titulo, texto))
    try:
        tipo = tarea["tipo"]
        if tipo == "explicar":
            decir(motor.explain())
        elif tipo == "ficha":
            motor.context_sheet(p, tarea.get("ajuste", ""))
        elif tipo == "evaluar":
            motor.evaluate(p, progreso=lambda i, n, lote: tarjeta.html(ui.tarjeta_progreso(
                f"Evaluando las 56 salvaguardas · lote {i} de {n}",
                f"Salvaguardas {lote[0]} a {lote[-1]}: comparo el documento con la descripción oficial de cada una…")))
        elif tipo == "reporte":
            motor.report(p)
        elif tipo == "pdf2":
            motor.analyze_initiatives(p)
        elif tipo == "v2":
            motor.updated_report(p)
        elif tipo == "consulta":
            decir(motor.ask(p, tarea["pregunta"]))
    except ErrorChatbot as e:
        decir(f"No pude completar «{titulo.lower()}»: {e}")
        if tarea["tipo"] == "evaluar":
            p.v1 = None  # la evaluación incompleta no se conserva; se puede reintentar desde la ficha
    finally:
        st.session_state.tarea = None
        guardar()
    st.rerun()
