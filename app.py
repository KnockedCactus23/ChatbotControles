"""Interfaz de chat (Streamlit) del diagnóstico de controles de ciberseguridad."""

import streamlit as st
from dotenv import load_dotenv

from chatbot import ui
from chatbot.controls import CONTROLES_POR_ID
from chatbot.engine import ErrorChatbot, Motor
from chatbot.state import Evaluacion

load_dotenv()
st.set_page_config(page_title="Diagnóstico de controles", page_icon=":material/shield:", layout="wide")
st.html(ui.CSS)

AVATAR = {"assistant": ":material/shield:", "user": ":material/person:"}

EJEMPLO = (
    "Somos Ferretería Andina (empresa ficticia), una cadena de 8 tiendas con 140 empleados y una tienda en línea. "
    "Usamos Microsoft 365 para correo y documentos, un ERP en un servidor propio en la oficina central y la tienda "
    "en línea está en Shopify. Todos los equipos tienen el antivirus de Windows (Defender), sin consola central. "
    "Hacemos respaldos del ERP cada noche a un NAS en la misma oficina. Tenemos un firewall Fortinet, pero la red "
    "de las tiendas no está segmentada y el wifi de clientes comparte red con las cajas. No tenemos un responsable "
    "de seguridad formal: TI son 3 personas. Manejamos datos personales de clientes y pagos con tarjeta mediante "
    "una pasarela externa. Nunca hemos hecho una prueba de penetración."
)


def iniciar():
    st.session_state.evaluacion = Evaluacion()
    st.session_state.chat = []
    st.session_state.reporte = None
    st.session_state.iniciado = False
    st.session_state.respondidas = 0
    st.session_state.estados_previos = {}
    st.session_state.cobertura_previa = 0.0
    st.session_state.generando = False  # True entre la última respuesta y la llegada del reporte
    try:
        st.session_state.motor = Motor()
    except ErrorChatbot as e:  # sin GEMINI_API_KEY
        st.session_state.motor = None
        st.session_state.error_inicio = str(e)


if "evaluacion" not in st.session_state:
    iniciar()
st.session_state.setdefault("generando", False)  # sesiones abiertas antes de este cambio

ev: Evaluacion = st.session_state.evaluacion
motor: Motor | None = st.session_state.motor


def decir(texto: str):
    st.session_state.chat.append({"tipo": "texto", "role": "assistant", "content": texto})


def generar_reporte():
    """Se llama solo al final del script, cuando la tarjeta de check ya está en pantalla."""
    try:
        st.session_state.reporte = motor.report(ev)
    except ErrorChatbot as e:
        decir(f"No pude generar el reporte: {e}")
    finally:
        st.session_state.generando = False


def fase() -> str:
    if st.session_state.reporte:
        return "reporte"
    return "verificacion" if st.session_state.iniciado else "contexto"


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    estados = {cid: ec.estado for cid, ec in ev.controles.items()}
    previos = st.session_state.estados_previos
    cambiados = {cid for cid, e in estados.items() if previos and previos.get(cid) != e}
    st.html(ui.postura(ev.resumen(), st.session_state.cobertura_previa, ev.porcentaje_cobertura()))
    st.html(ui.matriz(estados, cambiados))
    st.session_state.estados_previos = estados
    st.session_state.cobertura_previa = ev.porcentaje_cobertura()

    for estado in ui.ORDEN_ESTADOS:
        grupo = [(cid, ec) for cid, ec in ev.controles.items() if ec.estado == estado]
        if grupo and st.session_state.iniciado:
            with st.expander(f"{ui.ETIQUETA[estado]} · {len(grupo)}"):
                st.html(ui.detalle(grupo))

    # Durante la generación los botones se muestran deshabilitados (no se ocultan) para que
    # Streamlit no deje visibles los de la ejecución anterior mientras espera a la API.
    if st.session_state.iniciado and not st.session_state.reporte:
        if st.button("Generar reporte ahora", icon=":material/description:", use_container_width=True,
                     type="primary", disabled=st.session_state.generando):
            st.session_state.generando = True; st.rerun()
    if st.session_state.iniciado:
        if st.button("Nueva evaluación", icon=":material/restart_alt:", use_container_width=True,
                     disabled=st.session_state.generando):
            iniciar(); st.rerun()

# ------------------------------------------------------------------ encabezado
st.html(ui.encabezado(fase()))

if motor is None:
    st.error(f"{st.session_state.get('error_inicio')}. Copia `.env.example` como `.env` y pon tu `GEMINI_API_KEY` "
             "(gratis en aistudio.google.com/apikey).", icon=":material/key:")
    st.stop()

pendientes = len(ev.preguntas_pendientes)
if fase() == "contexto":
    st.html(ui.titular("Cuéntame cómo opera tu empresa.",
                       "Con tu descripción hago un primer diagnóstico frente a ISO/IEC 27002 y CIS Controls v8. "
                       "Después confirmo contigo, con preguntas de sí o no, lo que no haya quedado claro."))
    st.html(ui.guia_inicial())
    if st.button("Probar con una empresa ficticia", icon=":material/storefront:"):
        st.session_state.pendiente = EJEMPLO
    st.html('<p class="nota">Usa empresas ficticias: en el plan gratuito, Google puede usar el contenido para mejorar sus productos.</p>')
elif st.session_state.generando:
    st.html(ui.titular("Verificación completa." if not pendientes else "Preparando el reporte.",
                       "Estoy redactando el diagnóstico con todo lo que conversamos. Tarda unos segundos."))
elif fase() == "verificacion":
    st.html(ui.titular("Confirmemos lo que falta.",
                       f"Quedan {pendientes} controles por confirmar. Responde sí o no; si necesitas matizar algo, "
                       "escríbelo abajo y ajusto el análisis."))
else:
    st.html(ui.titular("Diagnóstico listo.",
                       "Este es el estado de tus controles con base en lo que conversamos, junto con las acciones "
                       "que más reducen tu riesgo."))

# ------------------------------------------------------------------ conversación
for m in st.session_state.chat:
    if m["tipo"] == "verificacion":
        st.html(ui.fila_respuesta(m["control_id"], m["respuesta"]))
    else:
        with st.chat_message(m["role"], avatar=AVATAR[m["role"]]):
            st.markdown(m["content"])

# Tarjeta de la pregunta cerrada en curso (o check mientras se genera el reporte)
generando = st.session_state.generando
pregunta = ev.pregunta_actual() if fase() == "verificacion" and not generando else None
if generando:
    # Mismo contenedor y mismo número de hijos que la tarjeta de pregunta, para que cada
    # posición se sobrescriba y no queden botones viejos visibles durante la llamada a la API.
    with st.container(key="verificacion"):
        st.html(ui.tarjeta_completada(st.session_state.respondidas, completa=not pendientes))
        st.empty()
        st.empty()
elif pregunta:
    with st.container(key="verificacion"):
        total = st.session_state.respondidas + pendientes
        st.html(ui.cabecera_pregunta(pregunta.control_id, pregunta.pregunta, st.session_state.respondidas, total))
        col_si, col_no, _ = st.columns([1.1, 1.1, 2])
        respuesta = None
        if col_si.button("Sí, lo tenemos", key=f"si_{pregunta.control_id}", type="primary",
                         icon=":material/check:", use_container_width=True):
            respuesta = True
        if col_no.button("No lo tenemos", key=f"no_{pregunta.control_id}",
                         icon=":material/close:", use_container_width=True):
            respuesta = False
        st.html('<p class="verif-ayuda">Tu respuesta se toma como declaración; no necesitas subir evidencia.</p>')
    if respuesta is not None:
        ev.responder(respuesta)
        st.session_state.respondidas += 1
        st.session_state.chat.append({"tipo": "verificacion", "control_id": pregunta.control_id, "respuesta": respuesta})
        if not ev.pregunta_actual():
            st.session_state.generando = True  # el reporte se pide en la siguiente ejecución
        st.rerun()

# Texto libre: contexto inicial o aclaraciones en cualquier momento
placeholder = ("Describe tu empresa: sector, tamaño, infraestructura y medidas actuales…" if fase() == "contexto"
               else "Aclara o añade información…")
if generando:
    st.chat_input("Generando el diagnóstico…", disabled=True)  # deshabilitado, no oculto (ver arriba)
    texto = None
else:
    texto = (st.chat_input(placeholder) if fase() != "reporte" else None) or st.session_state.pop("pendiente", None)
if texto:
    st.session_state.chat.append({"tipo": "texto", "role": "user", "content": texto})
    with st.spinner("Analizando el contexto con Gemini…"):
        try:
            if not st.session_state.iniciado:
                datos = motor.analyze(texto, ev)
                st.session_state.iniciado = True
            else:
                datos = motor.follow_up(texto, ev)
            decir(datos["mensaje"])
            if not ev.pregunta_actual():
                st.session_state.generando = True
        except ErrorChatbot as e:
            decir(f"No pude procesar el mensaje: {e}")
    st.rerun()

# Llamada al reporte al final: todo lo de arriba (incluido el check) ya se dibujó.
if generando:
    generar_reporte()
    st.rerun()

# ------------------------------------------------------------------ reporte
if st.session_state.reporte:
    st.html(ui.reporte(st.session_state.reporte, ev))
    if st.button("Iniciar una nueva evaluación", icon=":material/restart_alt:"):
        iniciar(); st.rerun()
