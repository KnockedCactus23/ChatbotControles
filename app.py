"""Centinela IG1 — agente de evaluación de CIS Controls v8.1 IG1 (actividad M3.6).

Etapas: contexto (PDF 1) → validación de la ficha → evaluación de las 56 salvaguardas →
reporte inicial (v1) → avance de iniciativas (PDF 2) con validación del auditor → reporte (v2).

Las llamadas a Claude se piden con ``pedir()`` y se ejecutan al FINAL del script, cuando la
página ya se dibujó con los controles deshabilitados; así no quedan botones viejos activos.
Todo se guarda automáticamente en ``evaluaciones/`` para conservar v1 y v2 entre sesiones.
"""

import re

import streamlit as st
from dotenv import load_dotenv

from chatbot import almacen, exportar, panel, ui
from chatbot.controls import CatalogoNoEncontrado, atribucion, catalogo
from chatbot.documentos import Documento, leer_pdf
from chatbot.engine import MODELO_POR_DEFECTO, MODELOS, ErrorChatbot, Motor
from chatbot.prompts import NOMBRE_AGENTE
from chatbot.reporte_pdf import ficha_pdf, reporte_pdf
from chatbot.state import Proyecto, ahora

load_dotenv()
st.set_page_config(page_title=NOMBRE_AGENTE, page_icon=":material/shield:", layout="wide")
st.html(ui.CSS)
st.html(panel.CSS)
st.html(ui.tema_script(), unsafe_allow_javascript=True)  # data-theme según el tema aplicado (Día/Noche)
# Interacciones del dashboard (resaltado por estado, riesgos ↔ roadmap, índice lateral, entrada): una sola vez.
st.html(panel.script(), unsafe_allow_javascript=True)

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
    st.session_state.pop("vista", None)       # al abrir otra evaluación, se muestra su paso actual
    st.session_state.pop("etapa_vista", None)
    st.session_state["vista_mostrada"] = "nueva"  # al abrir otra evaluación también se sube al inicio


if "proyecto" not in st.session_state or not hasattr(st.session_state.proyecto, "ficha_validada"):
    nuevo()
    # Sesión nueva: si la URL trae una evaluación (p. ej. tras cambiar de tema, que recarga la página), se reabre
    # en la misma sección.
    try:
        pid = st.query_params.get("evaluacion", "")
        if re.fullmatch(r"[0-9a-f]{10}", pid):  # solo ids de evaluación: nada de rutas en la URL
            nuevo(almacen.cargar(pid))
            if st.query_params.get("vista"):
                st.session_state.vista = st.query_params["vista"]
                st.session_state.etapa_vista = st.session_state.proyecto.etapa
    except (FileNotFoundError, KeyError, ValueError):
        st.query_params.clear()
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
    st.html(ui.selector_tema(deshabilitado=ocupado), unsafe_allow_javascript=True)
    st.html(panel.marca_lateral(NOMBRE_AGENTE, p.nombre if p.documentos else ""))
    # Se llena más abajo, cuando ya se sabe la sección: índice del reporte o resumen compacto de indicadores.
    lugar_lateral = st.container()

    # Modelo de Claude: se elige aquí y se guarda con la evaluación. Queda fijo desde que existe la ficha,
    # para que toda la evaluación use un solo modelo (consistencia); para cambiarlo, nueva evaluación.
    fijo = bool(p.modelo and p.ficha)
    actual = p.modelo or st.session_state.get("modelo_elegido", MODELO_POR_DEFECTO)
    elegido = st.selectbox("Modelo de Claude", list(MODELOS), format_func=lambda m: MODELOS.get(m, m),
                           index=list(MODELOS).index(actual) if actual in MODELOS else 0, disabled=ocupado or fijo,
                           help="Sonnet 5.5 para más precisión; Haiku 5.5 para pruebas.")
    if fijo:
        st.caption("Fijo en esta evaluación (un solo modelo de principio a fin). Para usar otro, crea una nueva evaluación.")
    else:
        st.session_state.modelo_elegido = elegido

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
    st.error(f"{st.session_state.get('error_inicio')}. Copia `.env.example` como `.env` y pon tu `ANTHROPIC_API_KEY` "
             "(se crea en platform.claude.com, en API keys).", icon=":material/key:")
    st.stop()

lugar_progreso = st.empty()  # cada etapa lo reubica junto a su botón principal


def descargas_ficha(cols):
    """Ficha de contexto (Etapa 2) en PDF y HTML; cols: dos columnas donde van los botones."""
    cols[0].download_button("Ficha de contexto (PDF)", ficha_pdf(p), file_name=f"ficha_contexto_{p.id}.pdf",
                            mime="application/pdf", icon=":material/picture_as_pdf:", use_container_width=True,
                            disabled=ocupado)
    cols[1].download_button("Ficha de contexto (HTML)", exportar.ficha_html(p), file_name=f"ficha_contexto_{p.id}.html",
                            mime="text/html", icon=":material/article:", use_container_width=True, disabled=ocupado)


def cabecera_reporte(titulo: str, cual: str, sub: str):
    """Título del reporte con el menú «Descargar ▾» a la derecha: los entregables de UNA versión ("v1" en el
    reporte inicial, "v2" en el actualizado; nunca se mezclan)."""
    inicial = cual == "v1"
    nombre = "inicial" if inicial else "final"
    v = p.v1 if inicial else p.v2
    c1, c2 = st.columns([5, 1.1], vertical_alignment="bottom")
    c1.html(panel.cabecera(titulo, cual, sub))
    with c2.popover("Descargar", icon=":material/download:", use_container_width=True, disabled=ocupado):
        st.download_button(f"Reporte {nombre} · PDF", reporte_pdf(p, cual), file_name=f"reporte_{nombre}_{p.id}.pdf",
                           mime="application/pdf", icon=":material/picture_as_pdf:", use_container_width=True,
                           key=f"pdf_{cual}")
        st.download_button(f"Reporte {nombre} · HTML", exportar.reporte_html(p, cual),
                           file_name=f"reporte_{nombre}_{p.id}.html", mime="text/html", icon=":material/article:",
                           use_container_width=True, key=f"html_{cual}")
        st.download_button(f"Excel completo {cual} · XLSX", exportar.excel(p, cual),
                           file_name=f"centinela_ig1_{cual}_{p.id}.xlsx", icon=":material/table_view:",
                           use_container_width=True, key=f"xlsx_{cual}")
        st.download_button(f"Matriz {cual} · CSV", exportar.csv_matriz(p, v), file_name=f"matriz_{cual}_{p.id}.csv",
                           mime="text/csv", icon=":material/csv:", use_container_width=True, key=f"csv_{cual}")


SUB_CONTROLES = "Cuántas salvaguardas de cada control hay en cada estado. Los cinco con mayores brechas van primero y explican por qué; abre cualquier control para ver sus salvaguardas."


def reporte_v1() -> list[tuple]:
    """Dashboard del reporte inicial (v1). Devuelve las secciones para el índice lateral."""
    v = p.v1
    rep = v.reporte
    res = rep.get("resumen_ejecutivo", {})
    ind = v.indicadores()
    riesgos = rep.get("riesgos", [])
    inis = rep.get("iniciativas", [])
    st.html(panel.resumen(ind))
    st.html(panel.seccion("postura", "Postura de ciberseguridad", "", panel.postura(res, v.matriz)))
    st.html(panel.seccion("controles", "Estado por control", SUB_CONTROLES,
                          panel.controles(v.matriz, res.get("controles_mayores_brechas", []))))
    st.html(panel.seccion("riesgos", "Cinco riesgos principales",
                          "La barra muestra el estado de las salvaguardas que sostienen cada riesgo. Pasa el cursor para "
                          "ver qué iniciativas lo reducen.", panel.riesgos(riesgos, v.matriz, "a")))
    st.html(panel.seccion("roadmap", "Roadmap de cinco iniciativas",
                          "Qué riesgos reduce cada una, cuánto esfuerzo pide y cuántas salvaguardas mueve.",
                          panel.roadmap(inis, riesgos, "a")))
    st.html(panel.matriz(v, p.documentos, "Matriz de las 56 salvaguardas",
                         "Estado, justificación, cita y página de cada salvaguarda (v1).", "matriz"))
    st.html(panel.seccion("pendientes", "Pendientes", "Lo que falta para dar el resultado por firme.",
                          panel.pendientes(res, ind)))
    return [("resumen", "Resumen", None), ("postura", "Postura", None), ("controles", "Controles", 15),
            ("riesgos", "Riesgos", len(riesgos)), ("roadmap", "Roadmap", len(inis)), ("matriz", "Matriz", ind["total"]),
            ("pendientes", "Pendientes", ind["no_verificado"])]


etapa = p.etapa

# --------------------------------------------------------------- navegación
# Siempre: Contexto, Reporte inicial y Reporte actualizado (estos dos cuando existen). La Evaluación 56 y la
# Validación del PDF 2 solo aparecen mientras son el paso en curso: al terminar, su contenido ya está en los
# reportes, y reabrirlas permitiría cambiar una v1 cerrada o decisiones ya aplicadas en la v2.
VISTAS = {"contexto": "Contexto", "evaluacion": "Evaluación 56 · en curso", "reporte": "Reporte inicial",
          "iniciativas": "Validación PDF 2 · en curso", "actualizado": "Reporte actualizado"}
opciones = {"contexto": ["contexto"], "evaluacion": ["contexto", "evaluacion"], "reporte": ["contexto", "reporte"],
            "iniciativas": ["contexto", "reporte", "iniciativas"], "actualizado": ["contexto", "reporte", "actualizado"]}[etapa]
if st.session_state.get("etapa_vista") != etapa or st.session_state.get("vista") not in opciones:
    st.session_state.vista = etapa        # al avanzar de etapa se muestra el paso nuevo
    st.session_state.etapa_vista = etapa
if len(opciones) > 1:
    st.segmented_control("Sección del análisis", opciones, format_func=VISTAS.get, key="vista", required=True,
                         disabled=ocupado, label_visibility="collapsed")
vista = st.session_state.vista or etapa
if st.session_state.get("vista_mostrada") not in (None, vista):
    st.html(ui.subir_al_inicio(), unsafe_allow_javascript=True)  # sección nueva: empezar desde arriba
st.session_state.vista_mostrada = vista
# La URL guarda la evaluación y la sección abiertas: al recargar (cambio de tema) se vuelve al mismo lugar.
if p.documentos:
    if st.query_params.get("evaluacion") != p.id or st.query_params.get("vista") != vista:
        st.query_params.update({"evaluacion": p.id, "vista": vista})
elif st.query_params:
    st.query_params.clear()

# --------------------------------------------------------- Etapa 1-2: contexto
if vista == "contexto" and etapa != "contexto":
    st.html(ui.titular("Ficha de contexto empresarial",
                       "Solo lectura: la ficha ya se validó y la evaluación se construyó sobre ella. Cada hallazgo indica si "
                       "su cita se encontró en el documento."))
    st.html(ui.ficha(p.ficha, p.documentos["pdf1"].etiqueta))
    descargas_ficha(st.columns([1, 1, 2]))
    if p.ajustes:
        st.html(ui.seccion(f"Ajustes registrados por el equipo · {len(p.ajustes)}"))
        for a in p.ajustes:
            st.markdown(f"- **{a['fecha']}** — {a['texto']}")

elif etapa == "contexto" and not p.ficha:
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

elif vista == "contexto":
    st.html(ui.titular("Ficha de contexto empresarial",
                       "Antes de evaluar, valida la interpretación del agente (R1). Cada hallazgo indica si su cita se "
                       "encontró en el documento."))
    st.html(ui.ficha(p.ficha, p.documentos["pdf1"].etiqueta))
    descargas_ficha(st.columns([1, 1, 2]))
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
elif vista == "evaluacion":
    ind = p.v1.indicadores()
    st.html(ui.titular("Evaluación inicial de las 56 salvaguardas",
                       "Cada estado se apoya en una cita verificada del documento. Lo que no está documentado queda como "
                       "«No verificado» (nunca como incumplimiento)."))
    st.html(panel.resumen(ind))
    st.html(ui.seccion("Cerrar la evaluación inicial",
                       "Genera el resumen ejecutivo, los cinco riesgos y el roadmap. La versión v1 queda fija como línea base."))
    lugar_progreso = st.empty()
    if st.button("Generar el reporte inicial (cierra la versión v1)", type="primary", icon=":material/description:",
                 disabled=ocupado):
        pedir("reporte")
    st.html(panel.matriz(p.v1, p.documentos, "Matriz de las 56 salvaguardas · v1",
                         "Incluye todas las salvaguardas, también las no verificadas.", "matriz", abierta=True))

# ------------------------------------------------- Etapas 3.5-4: reporte v1
elif vista == "reporte":
    cabecera_reporte("Reporte inicial", "v1", f"{p.nombre} · línea base cerrada el {p.v1.fecha}. Esta versión ya no se modifica.")
    secciones = reporte_v1()
    if etapa == "reporte":  # la carga del PDF 2 solo mientras es el paso en curso
        st.html(panel.seccion("pdf2", "Avance de iniciativas (PDF 2)",
                              "El agente parte de esta evaluación (no de cero) y propone cambios que tú validas como auditor.", ""))
        secciones.append(("pdf2", "Avance con PDF 2", None))
        archivo2 = st.file_uploader("PDF 2 — Avance de iniciativas", type=["pdf"], disabled=ocupado, label_visibility="collapsed")
        lugar_progreso = st.empty()
        if st.button("Analizar el avance de iniciativas", type="primary", icon=":material/upload_file:",
                     disabled=ocupado or not archivo2):
            datos = archivo2.getvalue()
            p.documentos["pdf2"] = Documento("pdf2", archivo2.name, "pdf", leer_pdf(datos), almacen.guardar_pdf(p, "pdf2", datos))
            guardar()
            pedir("pdf2")

# ------------------------------------------------ Etapa 5: validar cambios
elif vista == "iniciativas":
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
        if p.alertas:
            st.html(ui.seccion("Alertas del documento (requieren validación humana)",
                               "Contradicciones con el PDF 1, fechas incoherentes o evidencia que puede no estar vigente."))
            st.html(ui.avisos(p.alertas))
        st.html(ui.seccion("Propuesta de actualización",
                           "Cambios de estado (mejoras o empeoramientos) y actualizaciones de evidencia. "
                           "Los que no tienen cita verificable en el PDF 2 no se pueden aprobar."))
        if not p.cambios:
            st.info("El agente no propuso cambios: la evidencia del PDF 2 no fue suficiente.")
        for c in p.cambios:
            st.html(ui.cambio_fila(c))
            opciones = ["pendiente", "aprobado", "rechazado"] if c.aprobable else ["pendiente", "rechazado"]
            etiquetas = {"pendiente": "Pendiente", "aprobado": "Aprobar", "rechazado": "Rechazar"}
            decision = st.radio(f"Decisión {c.id}", opciones, index=opciones.index(c.decision) if c.decision in opciones else 0,
                                format_func=etiquetas.get, horizontal=True, key=f"dec_{c.id.replace('.', '_')}",
                                disabled=ocupado, label_visibility="collapsed")
            if decision != c.decision:
                p.decidir(c.id, decision); guardar()
        if p.sin_cambio:
            st.html(ui.seccion(f"Salvaguardas relacionadas sin cambio · {len(p.sin_cambio)}",
                               "Cada salvaguarda relacionada con una iniciativa recibe una decisión; aquí están las que quedan "
                               "igual y por qué. «El agente no decidió» requiere revisión manual."))
            st.html(ui.sin_cambio(p.sin_cambio))
        aprobados = sum(c.decision == "aprobado" for c in p.cambios)
        lugar_progreso = st.empty()
        if st.button(f"Aplicar {aprobados} cambio(s) aprobado(s) y actualizar el diagnóstico", type="primary",
                     icon=":material/published_with_changes:", disabled=ocupado):
            p.crear_v2(); guardar()
            pedir("v2")

# --------------------------------------------- Etapa 5.6: reporte actualizado
elif vista == "actualizado":
    v1, v2 = p.v1, p.v2
    rep = v2.reporte
    res = rep.get("resumen_ejecutivo", {})
    ind, ind1 = v2.indicadores(), v1.indicadores()
    riesgos_v1 = v1.reporte.get("riesgos", [])
    riesgos_v2 = rep.get("riesgos_v2") or riesgos_v1  # evaluaciones anteriores al cambio no tienen riesgos_v2
    aprobados = [c.id for c in p.cambios if c.decision == "aprobado"]
    cabecera_reporte("Reporte actualizado", "v2",
                     f"{p.nombre} · v2 del {v2.fecha}. Refleja solo las mejoras documentadas y aprobadas; la v1 se conserva.")
    st.html(panel.resumen(ind, ind1))
    filas = "".join(ui.cambio_fila(c) + f"<p class='aviso' style='margin:0 0 10px 14px'>Decisión del auditor: <b>{c.decision}</b></p>"
                    for c in p.cambios)
    st.html(panel.seccion("cambios", "Cambios derivados del PDF 2", "",
                          f"<div class='d-tarjeta' style='padding:16px 20px'><p class='d-largo d-abierto' style='margin:0 0 12px'>"
                          f"{ui.esc(rep.get('resumen_cambios'))}</p>{filas}</div>"))
    st.html(panel.seccion("postura", "Postura de ciberseguridad", "", panel.postura(res, v2.matriz)))
    st.html(panel.seccion("controles", "Estado por control", SUB_CONTROLES,
                          panel.controles(v2.matriz, res.get("controles_mayores_brechas", []), set(aprobados))))
    st.html(panel.seccion("riesgos-v1", "Riesgos originales tras las mejoras",
                          "Situación calculada por el sistema con el estado v2 de las salvaguardas de cada riesgo.",
                          panel.riesgos(riesgos_v1, v2.matriz, "a", rep.get("riesgos") or [])))
    st.html(panel.seccion("roadmap-v1", "Iniciativas del roadmap original",
                          "Completada si todas sus salvaguardas están implementadas en v2; en progreso si alguna mejoró.",
                          panel.roadmap(v1.reporte.get("iniciativas", []), riesgos_v1, "a", rep.get("iniciativas_estado") or [])))
    secciones = [("resumen", "Resumen", None), ("cambios", "Cambios PDF 2", len(p.cambios)), ("postura", "Postura", None),
                 ("controles", "Controles", 15), ("riesgos-v1", "Riesgos originales", len(riesgos_v1)),
                 ("roadmap-v1", "Iniciativas originales", len(v1.reporte.get("iniciativas", [])))]
    if rep.get("riesgos_v2"):
        st.html(panel.seccion("riesgos", "Cinco riesgos vigentes (v2)",
                              "Construidos sobre la matriz v2; el roadmap actualizado apunta a estos.",
                              panel.riesgos(riesgos_v2, v2.matriz, "b")))
        secciones.append(("riesgos", "Riesgos vigentes", len(riesgos_v2)))
    st.html(panel.seccion("roadmap", "Roadmap actualizado", "Qué riesgos vigentes reduce cada iniciativa y cuánto esfuerzo pide.",
                          panel.roadmap(rep.get("roadmap", []), riesgos_v2, "b")))
    st.html(panel.matriz(v2, p.documentos, "Matriz de las 56 salvaguardas · v2",
                         "Las modificadas en v2 aparecen resaltadas.", "matriz", set(aprobados)))
    st.html(panel.matriz(v1, p.documentos, "Matriz v1 · evaluación inicial", "Línea base, sin cambios.", "matriz-v1"))
    st.html(panel.seccion("pendientes", "Pendientes", "Lo que falta para dar el resultado por firme.", panel.pendientes(res, ind)))
    secciones += [("roadmap", "Roadmap", len(rep.get("roadmap", []))), ("matriz", "Matriz v2", ind["total"]),
                  ("matriz-v1", "Matriz v1", ind1["total"]), ("pendientes", "Pendientes", ind["no_verificado"])]

# --------------------------------------------------------------- barra lateral: índice o resumen
with lugar_lateral:
    if vista in ("reporte", "actualizado"):
        st.html(panel.indice(secciones))
    elif p.vigente:
        st.html(panel.estado_lateral(p.vigente.indicadores()))
    else:
        st.html('<p class="aviso" style="padding:0 8px">Agente consultor de CIS Controls v8.1 IG1. Carga el PDF de contexto '
                'para comenzar.</p>')

# ------------------------------------------------------- consultas al agente
mensajes = [m for m in p.chat if m["tipo"] == "texto"]
# El chat solo se ofrece cuando hay algo que explicar: la ficha del PDF 1 ya generada o un reporte.
# El historial se sigue mostrando en todas las etapas (incluye la prueba preliminar y los errores).
CHAT_ACTIVO = (vista == "contexto" and bool(p.ficha)) or vista in ("reporte", "actualizado")
if mensajes or CHAT_ACTIVO:
    st.html(ui.seccion("Conversación con el agente"))
    for m in mensajes:
        with st.chat_message(m["role"], avatar=AVATAR[m["role"]]):
            st.markdown(m["content"])
# El chat_input va DENTRO de un contenedor: en la raíz, Streamlit lo fija abajo y activa "pegarse al final",
# que arrastra la página hasta abajo cada vez que crece (al cambiar de sección o abrir una matriz).
pregunta_usuario = None
if CHAT_ACTIVO:
    with st.container(key="chat"):
        pregunta_usuario = st.chat_input(f"Pregunta a {NOMBRE_AGENTE} por qué tomó una decisión o qué falta…",
                                         disabled=ocupado)
if pregunta_usuario:
    decir(pregunta_usuario, "user")
    pedir("consulta", pregunta=pregunta_usuario)

st.html(ui.atribucion_html(atribucion()))

# ------------------------------------------- tareas lentas (al final del script)
if tarea:
    titulo, texto = TITULO_TAREA[tarea["tipo"]]
    if not p.modelo:  # la primera llamada fija el modelo de esta evaluación
        p.modelo = st.session_state.get("modelo_elegido", MODELO_POR_DEFECTO)
    motor.modelo = p.modelo
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
        p.consumo.extend(motor.consumo)  # tokens y costo de lo que se acaba de ejecutar
        motor.consumo.clear()
        st.session_state.tarea = None
        guardar()
    st.rerun()
