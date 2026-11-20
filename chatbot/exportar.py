"""Exportación de entregables: matriz (Excel/CSV), reporte técnico y ficha de contexto (HTML) y prompt maestro (Markdown).

Los valores salen de la misma matriz e indicadores que muestra la app: no hay cálculos aparte,
así que matriz, indicadores y reporte no pueden contradecirse.
"""

import csv
import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from . import prompts, ui
from .controls import atribucion, salvaguarda
from .state import ESTADOS, ETIQUETA, ETIQUETA_APLICABILIDAD, VALOR, Proyecto, Version, formato_pct

COLUMNAS_MATRIZ = ["ID CIS", "Salvaguarda", "Control CIS", "Aplicabilidad", "Estado", "Valor", "Justificación",
                   "Evidencia", "Cita", "Observaciones"]


def filas_matriz(p: Proyecto, v: Version) -> list[list]:
    filas = []
    for r in v.matriz.values():
        s = salvaguarda(r.id)
        filas.append([r.id, s.titulo, s.control_id, ETIQUETA_APLICABILIDAD[r.aplicabilidad], ETIQUETA[r.estado],
                      VALOR.get(r.estado, "—"), r.justificacion, r.evidencia(p.documentos), r.cita, r.observaciones])
    return filas


def csv_matriz(p: Proyecto, v: Version) -> bytes:
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(COLUMNAS_MATRIZ)
    w.writerows(filas_matriz(p, v))
    return salida.getvalue().encode("utf-8-sig")  # BOM para que Excel respete los acentos


def _hoja(libro: Workbook, titulo: str, encabezado: list[str], filas: list[list]) -> None:
    hoja = libro.create_sheet(titulo[:31])
    hoja.append(encabezado)
    for celda in hoja[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1F2A30")
    for f in filas:
        hoja.append(f)
    for i, _ in enumerate(encabezado, 1):
        letra = hoja.cell(1, i).column_letter
        hoja.column_dimensions[letra].width = 14 if i <= 2 else 38
        for celda in hoja[letra][1:]:
            celda.alignment = Alignment(wrap_text=True, vertical="top")
    hoja.freeze_panes = "A2"


def _indicadores(v: Version) -> list:
    i = v.indicadores()
    return [i["total"]] + [i[e] for e in ESTADOS] + [formato_pct(i["implementacion"]), formato_pct(i["cobertura"])]


def _version(p: Proyecto, cual: str) -> Version:
    v = p.v1 if cual == "v1" else p.v2 if cual == "v2" else None
    if v is None:
        raise ValueError(f"La versión {cual} no existe todavía.")
    return v


def excel(p: Proyecto, cual: str) -> bytes:
    """Excel completo de UNA versión. "v1": evaluación inicial (contexto, matriz v1, indicadores, riesgos y roadmap).
    "v2": evaluación actualizada (contexto, matriz v2, indicadores v1 frente a v2, situación de los riesgos,
    estado de las iniciativas, roadmap actualizado y cambios del PDF 2). La matriz v1 no se repite en el de v2."""
    v = _version(p, cual)
    rep = v.reporte or {}
    libro = Workbook()
    libro.remove(libro.active)
    if p.ficha:
        filas = []
        for clave, nombre, _ in prompts.DIMENSIONES:
            d = p.ficha.get("dimensiones", {}).get(clave, {})
            for h in d.get("hallazgos", []) or [{}]:
                filas.append([nombre, d.get("resumen", ""), h.get("dato", ""), h.get("pagina", ""), h.get("seccion", ""),
                              h.get("cita", ""), "Sí" if h.get("verificada") else ("No" if h else ""), d.get("faltante", "")])
        _hoja(libro, "Contexto", ["Dimensión", "Resumen", "Hallazgo", "Página", "Sección", "Cita", "Cita verificada", "Falta"], filas)
    _hoja(libro, f"Matriz {cual}", COLUMNAS_MATRIZ, filas_matriz(p, v))
    enc = ["Versión", "Total", *[ETIQUETA[e] for e in ESTADOS], "Implementación IG1", "Cobertura IG1"]
    comparadas = [p.v1, p.v2] if cual == "v2" else [p.v1]
    _hoja(libro, "Indicadores", enc, [[x.nombre, *_indicadores(x)] for x in comparadas])
    riesgos_v1 = (p.v1.reporte or {}).get("riesgos", [])
    if cual == "v1" and riesgos_v1:
        _hoja(libro, "Riesgos v1", ["#", "Riesgo", "Descripción", "Activo o proceso", "Deficiencia", "Consecuencia",
                                    "Severidad", "Justificación", "Salvaguardas"],
              [[i, r["titulo"], r["descripcion"], r["activo_proceso"], r["deficiencia"], r["consecuencia"], r["severidad"],
                r["justificacion"], ", ".join(r["salvaguardas"])] for i, r in enumerate(riesgos_v1, 1)])
    if cual == "v2" and rep.get("riesgos"):
        _hoja(libro, "Riesgos v1 situación", ["#", "Riesgo original", "Severidad inicial", "Salvaguardas", "Situación",
                                              "Severidad residual", "Mejoraron", "Siguen con brecha", "Explicación"],
              [[i, r.get("titulo", ""), (riesgos_v1[i - 1].get("severidad", "") if i <= len(riesgos_v1) else ""),
                ", ".join(riesgos_v1[i - 1].get("salvaguardas", [])) if i <= len(riesgos_v1) else "",
                r.get("situacion", ""), r.get("severidad_residual", ""), ", ".join(r.get("mejoradas", [])),
                ", ".join(r.get("pendientes", [])), r.get("explicacion", "")] for i, r in enumerate(rep["riesgos"], 1)])
    if cual == "v2" and rep.get("riesgos_v2"):
        _hoja(libro, "Riesgos v2", ["#", "Riesgo", "Descripción", "Activo o proceso", "Deficiencia", "Consecuencia",
                                    "Severidad", "Justificación", "Salvaguardas"],
              [[i, r["titulo"], r["descripcion"], r["activo_proceso"], r["deficiencia"], r["consecuencia"], r["severidad"],
                r["justificacion"], ", ".join(r["salvaguardas"])] for i, r in enumerate(rep["riesgos_v2"], 1)])
    if cual == "v2" and rep.get("iniciativas_estado"):
        _hoja(libro, "Iniciativas v1 estado", ["#", "Iniciativa", "Estado", "Explicación"],
              [[i, e.get("titulo", ""), e.get("estado", ""), e.get("explicacion", "")]
               for i, e in enumerate(rep["iniciativas_estado"], 1)])
    roadmap = rep.get("iniciativas") or rep.get("roadmap") or []
    if roadmap:
        _hoja(libro, f"Roadmap {cual}", ["Prioridad", "Iniciativa", "Descripción", "Riesgos", "Salvaguardas", "Beneficio",
                                         "Esfuerzo", "Clasificación"],
              [[x["prioridad"], x["titulo"], x["descripcion"], ", ".join(map(str, x["riesgos"])), ", ".join(x["salvaguardas"]),
                x["beneficio"], x["esfuerzo"], "Quick win" if x["tipo"] == "quick_win" else "Inversión o proyecto"]
               for x in roadmap])
    if cual == "v2" and p.cambios:
        _hoja(libro, "Cambios PDF 2", ["ID CIS", "Tipo", "Estado inicial", "Estado propuesto", "Justificación", "Iniciativa",
                                       "Página", "Cita", "Cita verificada", "Decisión del auditor"],
              [[c.id, "Evidencia" if c.tipo == "evidencia" else "Estado", ETIQUETA[c.estado_inicial],
                ETIQUETA[c.estado_propuesto], c.justificacion, c.iniciativa, c.pagina or "",
                c.cita, "Sí" if c.cita_verificada else "No", c.decision] for c in p.cambios])
    if cual == "v2" and p.sin_cambio:
        _hoja(libro, "Sin cambio PDF 2", ["ID CIS", "Motivo", "Detalle", "Iniciativa"],
              [[x.get("id"), x.get("motivo"), x.get("detalle"), x.get("iniciativa")] for x in p.sin_cambio])
    if p.ajustes:
        _hoja(libro, "Ajustes al agente", ["Fecha", "Ajuste"], [[a["fecha"], a["texto"]] for a in p.ajustes])
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def reporte_html(p: Proyecto, cual: str) -> str:
    """Reporte técnico de UNA versión en HTML: "v1" (inicial) o "v2" (final, con la comparación frente a v1)."""
    v = _version(p, cual)
    rep = v.reporte or {}
    nombre = "Reporte técnico inicial" if cual == "v1" else "Reporte técnico final"
    partes = [f"<h1 class='titular'>{nombre} · {ui.esc(p.nombre)}</h1>",
              f"<p class='lead'>{ui.esc(prompts.NOMBRE_AGENTE)} · CIS Controls v8.1 IG1 · 56 salvaguardas · "
              f"{ui.esc(v.nombre)} del {ui.esc(v.fecha)}</p>"]
    if p.ficha:
        partes += [ui.seccion("Contexto de la empresa"), f"<p class='ficha-resumen'>{ui.esc(p.ficha.get('resumen_contexto') or p.ficha.get('resumen_ejecutivo'))}</p>"]
    riesgos_v1 = (p.v1.reporte or {}).get("riesgos", [])
    titulos = [r["titulo"] for r in riesgos_v1]
    riesgos_v2 = rep.get("riesgos_v2") or []
    titulos_v2 = [r["titulo"] for r in riesgos_v2] or titulos  # evaluaciones anteriores: sin riesgos_v2
    roadmap = rep.get("iniciativas") or rep.get("roadmap") or []
    if cual == "v1":
        partes += [ui.seccion(f"Dashboard · {v.nombre}"), ui.tablero(v.indicadores(), len(riesgos_v1), len(roadmap)),
                   ui.seccion("Resumen ejecutivo"), ui.resumen_ejecutivo(rep.get("resumen_ejecutivo", {})),
                   ui.seccion("Cinco riesgos principales"), ui.riesgos(riesgos_v1),
                   ui.seccion("Roadmap de cinco iniciativas"), ui.roadmap(roadmap, titulos)]
    else:
        aprobados = [c.id for c in p.cambios if c.decision == "aprobado"]
        partes += [ui.seccion(f"Dashboard · {v.nombre} frente a v1"),
                   ui.tablero(v.indicadores(), len(riesgos_v2 or rep.get("riesgos", [])), len(roadmap), p.v1.indicadores()),
                   ui.seccion("Cambios derivados del PDF 2"), f"<p class='ficha-resumen'>{ui.esc(rep.get('resumen_cambios'))}</p>",
                   ui.comparacion(p.v1.indicadores(), v.indicadores(), aprobados),
                   ui.seccion("Resumen ejecutivo actualizado"), ui.resumen_ejecutivo(rep.get("resumen_ejecutivo", {})),
                   ui.seccion("Riesgos originales: mitigados, reducidos o que permanecen"), ui.riesgos(riesgos_v1, rep.get("riesgos")),
                   ui.seccion("Iniciativas del roadmap original: completadas o en progreso"),
                   ui.roadmap(p.v1.reporte.get("iniciativas", []), titulos, rep.get("iniciativas_estado"))]
        if riesgos_v2:
            partes += [ui.seccion("Cinco riesgos vigentes (v2)"), ui.riesgos(riesgos_v2)]
        partes += [ui.seccion("Roadmap actualizado"), ui.roadmap(roadmap, titulos_v2)]
    return _pagina_html(f"{nombre} {p.nombre}", partes)


def ficha_html(p: Proyecto) -> str:
    """Ficha de contexto (Etapa 2) autocontenida: dimensiones con evidencia, faltantes, ambigüedades,
    perfil de riesgo y los ajustes registrados por el equipo (Etapa 2.5)."""
    doc = p.documentos.get("pdf1")
    estado = "Validada por el equipo" if p.ficha_validada else "Pendiente de validación por el equipo"
    partes = [f"<h1 class='titular'>Ficha de contexto · {ui.esc(p.nombre)}</h1>",
              f"<p class='lead'>{ui.esc(prompts.NOMBRE_AGENTE)} · Fuente: {ui.esc(doc.etiqueta + ' · ' + doc.nombre if doc else '—')}"
              f" · {estado}</p>",
              ui.ficha(p.ficha or {}, doc.etiqueta if doc else "PDF 1")]
    if p.ajustes:
        partes += [ui.seccion("Ajustes registrados por el equipo (Etapa 2.5)"),
                   "<ul class='ficha-resumen'>" + "".join(f"<li><b>{ui.esc(a['fecha'])}</b> — {ui.esc(a['texto'])}</li>"
                                                          for a in p.ajustes) + "</ul>"]
    return _pagina_html(f"Ficha de contexto {p.nombre}", partes)


def _pagina_html(titulo: str, partes: list[str]) -> str:
    """Documento HTML autocontenido con el mismo diseño que la app."""
    partes = partes + [ui.atribucion_html(atribucion())]
    estilos = ui.CSS.replace("<style>", "<style>body{margin:0;padding:40px;background:#0a0c0f;color:#f0f2f4;"
                                          "font-family:Geist,system-ui,sans-serif}")
    return (f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>{ui.esc(titulo)}</title>"
            f"<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono&display=swap'>"
            f"{estilos}</head><body><main style='max-width:1100px;margin:0 auto'>{''.join(partes)}</main></body></html>")


def prompt_maestro_md() -> str:
    """Entregable 1: prompt maestro con identidad, alcance, reglas y escala, más las tareas por etapa."""
    tareas = [("Prueba preliminar (Etapa 1.5)", prompts.sistema_explicacion), ("Ficha de contexto (Etapa 2)", prompts.sistema_ficha),
              ("Evaluación de las 56 salvaguardas (Etapa 3)", prompts.sistema_evaluacion),
              ("Resumen ejecutivo, riesgos y roadmap (Etapas 3.5 y 4)", prompts.sistema_reporte),
              ("Procesamiento del PDF 2 (Etapa 5)", prompts.sistema_iniciativas),
              ("Diagnóstico actualizado (Etapa 5.6)", prompts.sistema_reporte_actualizado)]
    maestro = prompts.prompt_maestro()
    secciones = []
    for nombre, f in tareas:
        texto = f()
        tarea = texto[texto.index("# Tarea"):] if "# Tarea" in texto else texto
        secciones.append(f"## {nombre}\n\n{tarea}")
    return (f"# Prompt maestro — {prompts.NOMBRE_AGENTE}\n\n{maestro}\n\n"
            "# Fuente normativa\nEl catálogo oficial CIS Controls v8.1 IG1 (56 salvaguardas: ID, título, descripción y control) "
            "se carga desde el Excel oficial de CIS y se incluye sin modificar en cada evaluación. "
            "No se reproduce aquí por su licencia (CC BY-NC-ND 4.0).\n\n"
            "# Configuración técnica\n- Plataforma: API de Claude (Anthropic), modelo Claude Sonnet 5.5, razonamiento adaptativo con esfuerzo fijo.\n- Consistencia: instrucciones fijas, salida estructurada y reglas deterministas en el código (estados, indicadores y situación de riesgos e iniciativas).\n"
            "- Salida estructurada con JSON Schema en cada etapa.\n- Validaciones automáticas: 56 salvaguardas siempre presentes, "
            "verificación de cada cita contra el documento, indicadores calculados por el sistema y cambios del PDF 2 sujetos a aprobación.\n\n"
            "# Instrucciones por etapa\n\n" + "\n\n".join(secciones))
