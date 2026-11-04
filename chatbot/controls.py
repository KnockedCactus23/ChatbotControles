"""Catálogo de dominios de control.

Cada dominio agrupa controles de ISO/IEC 27002:2022 y CIS Controls v8 que
cubren el mismo objetivo, para que el diagnóstico sea manejable en una
conversación. El chatbot solo puede usar los ``id`` definidos aquí.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Control:
    id: str
    nombre: str
    descripcion: str
    iso27002: tuple[str, ...]
    cis_v8: tuple[str, ...]
    pregunta_base: str  # pregunta cerrada por defecto si Gemini no propone una


CONTROLES: tuple[Control, ...] = (
    Control(
        "GOB-01", "Políticas de seguridad de la información",
        "Políticas aprobadas por la dirección, comunicadas y revisadas periódicamente.",
        ("5.1 Políticas de seguridad de la información",),
        (),
        "¿Cuentan con una política de seguridad de la información aprobada por la dirección y revisada al menos una vez al año?",
    ),
    Control(
        "GOB-02", "Roles y responsabilidades de seguridad",
        "Responsables de seguridad definidos, segregación de funciones.",
        ("5.2 Roles y responsabilidades", "5.3 Segregación de funciones"),
        (),
        "¿Están formalmente definidos y documentados los roles y responsabilidades de seguridad (por ejemplo, un CISO o responsable designado)?",
    ),
    Control(
        "GOB-03", "Gestión de riesgos y cumplimiento",
        "Identificación y tratamiento de riesgos, requisitos legales y revisiones independientes.",
        ("5.31 Requisitos legales y contractuales", "5.35 Revisión independiente", "5.36 Cumplimiento de políticas"),
        (),
        "¿Realizan un análisis de riesgos de seguridad documentado al menos una vez al año?",
    ),
    Control(
        "ACT-01", "Inventario de activos de hardware",
        "Inventario actualizado de equipos, servidores y dispositivos con responsable asignado.",
        ("5.9 Inventario de información y otros activos", "5.11 Devolución de activos"),
        ("CIS 1 Inventario y control de activos empresariales",),
        "¿Tienen un inventario actualizado de todos los equipos (servidores, laptops, dispositivos de red, móviles) con un responsable asignado?",
    ),
    Control(
        "ACT-02", "Inventario de software",
        "Inventario de software autorizado y control de software no autorizado.",
        ("5.9 Inventario de información y otros activos", "8.19 Instalación de software en sistemas operativos"),
        ("CIS 2 Inventario y control de activos de software",),
        "¿Tienen un inventario del software autorizado y bloquean o detectan la instalación de software no autorizado?",
    ),
    Control(
        "DAT-01", "Clasificación y protección de datos",
        "Clasificación de la información, cifrado en reposo y en tránsito, prevención de fuga de datos.",
        ("5.12 Clasificación de la información", "5.13 Etiquetado", "8.12 Prevención de fuga de datos", "8.24 Uso de criptografía"),
        ("CIS 3 Protección de datos",),
        "¿Clasifican la información (p. ej. pública, interna, confidencial) y cifran los datos sensibles en reposo y en tránsito?",
    ),
    Control(
        "CFG-01", "Configuración segura",
        "Líneas base de configuración (hardening) para equipos, servidores y nube.",
        ("8.9 Gestión de la configuración",),
        ("CIS 4 Configuración segura de activos y software",),
        "¿Aplican configuraciones seguras estándar (hardening / benchmarks) en equipos, servidores y servicios en la nube?",
    ),
    Control(
        "IAM-01", "Gestión de identidades y cuentas",
        "Altas, bajas y revisiones periódicas de cuentas; cuentas compartidas controladas.",
        ("5.16 Gestión de identidades", "5.18 Derechos de acceso"),
        ("CIS 5 Gestión de cuentas",),
        "¿Tienen un proceso para dar de alta, modificar y dar de baja cuentas, y revisan periódicamente las cuentas activas?",
    ),
    Control(
        "IAM-02", "Control de accesos y mínimo privilegio",
        "Accesos basados en rol, cuentas privilegiadas separadas y controladas.",
        ("5.15 Control de acceso", "8.2 Derechos de acceso privilegiado", "8.3 Restricción de acceso a la información"),
        ("CIS 6 Gestión del control de accesos",),
        "¿Los accesos se otorgan por rol con mínimo privilegio y las cuentas de administrador están separadas de las de uso diario?",
    ),
    Control(
        "IAM-03", "Autenticación multifactor (MFA)",
        "MFA en accesos remotos, correo, nube y cuentas privilegiadas.",
        ("5.17 Información de autenticación", "8.5 Autenticación segura"),
        ("CIS 6.3 MFA para aplicaciones expuestas", "CIS 6.4 MFA para acceso remoto", "CIS 6.5 MFA para cuentas administrativas"),
        "¿Tienen MFA habilitado en correo, VPN/acceso remoto, servicios en la nube y cuentas de administrador?",
    ),
    Control(
        "VUL-01", "Gestión de vulnerabilidades y parches",
        "Escaneos periódicos y aplicación de parches con tiempos definidos.",
        ("8.8 Gestión de vulnerabilidades técnicas",),
        ("CIS 7 Gestión continua de vulnerabilidades",),
        "¿Realizan escaneos de vulnerabilidades periódicos y aplican parches de seguridad con plazos definidos?",
    ),
    Control(
        "LOG-01", "Registro y monitoreo de eventos",
        "Recolección centralizada de logs, retención y revisión/alertas (SIEM).",
        ("8.15 Registro de eventos", "8.16 Actividades de monitoreo", "8.17 Sincronización de relojes"),
        ("CIS 8 Gestión de registros de auditoría",),
        "¿Centralizan los logs de sistemas críticos y alguien los revisa o recibe alertas (por ejemplo con un SIEM)?",
    ),
    Control(
        "MAIL-01", "Protección de correo y navegación",
        "Filtrado de correo (SPF/DKIM/DMARC, antiphishing) y filtrado web.",
        ("8.23 Filtrado web",),
        ("CIS 9 Protecciones de correo y navegador web",),
        "¿Tienen filtrado antiphishing/antispam en el correo, SPF/DKIM/DMARC configurados y filtrado de navegación web?",
    ),
    Control(
        "MAL-01", "Protección contra malware (antivirus/EDR)",
        "Antimalware o EDR gestionado centralmente en todos los equipos.",
        ("8.7 Protección contra malware",),
        ("CIS 10 Defensas contra malware",),
        "¿Todos los equipos y servidores tienen antivirus o EDR gestionado de forma centralizada y actualizado?",
    ),
    Control(
        "BCK-01", "Copias de seguridad y recuperación",
        "Respaldos automáticos, copia aislada/offline y pruebas de restauración.",
        ("8.13 Respaldo de la información",),
        ("CIS 11 Recuperación de datos",),
        "¿Hacen respaldos automáticos de la información crítica, guardan una copia aislada (offline/inmutable) y prueban la restauración?",
    ),
    Control(
        "NET-01", "Seguridad de red",
        "Firewalls, segmentación de red, gestión segura de la infraestructura de red y acceso remoto seguro.",
        ("8.20 Seguridad de redes", "8.21 Seguridad de servicios de red", "8.22 Segregación de redes"),
        ("CIS 12 Gestión de la infraestructura de red", "CIS 13 Monitoreo y defensa de la red"),
        "¿Tienen firewall perimetral gestionado y la red segmentada (por ejemplo, separando servidores, usuarios e invitados)?",
    ),
    Control(
        "PER-01", "Concientización y capacitación",
        "Capacitación periódica en seguridad y simulaciones de phishing.",
        ("6.3 Concientización, educación y formación",),
        ("CIS 14 Concientización y capacitación en seguridad",),
        "¿Capacitan al personal en ciberseguridad al menos una vez al año (incluyendo simulaciones de phishing)?",
    ),
    Control(
        "PROV-01", "Gestión de proveedores",
        "Requisitos de seguridad en contratos y evaluación de proveedores de TI / nube.",
        ("5.19 Seguridad en relaciones con proveedores", "5.20 Seguridad en acuerdos con proveedores", "5.23 Seguridad en servicios en la nube"),
        ("CIS 15 Gestión de proveedores de servicios",),
        "¿Evalúan la seguridad de sus proveedores críticos e incluyen cláusulas de seguridad en los contratos?",
    ),
    Control(
        "DEV-01", "Desarrollo seguro de aplicaciones",
        "Ciclo de desarrollo seguro, revisión de código y pruebas de seguridad.",
        ("8.25 Ciclo de desarrollo seguro", "8.28 Codificación segura", "8.29 Pruebas de seguridad"),
        ("CIS 16 Seguridad del software de aplicación",),
        "Si desarrollan software, ¿siguen prácticas de desarrollo seguro (revisión de código, análisis de vulnerabilidades, separación de ambientes)?",
    ),
    Control(
        "INC-01", "Gestión de incidentes",
        "Plan de respuesta a incidentes, roles, canales de reporte y lecciones aprendidas.",
        ("5.24 Planificación de la gestión de incidentes", "5.25 Evaluación de eventos", "5.26 Respuesta a incidentes", "5.27 Lecciones aprendidas", "6.8 Reporte de eventos"),
        ("CIS 17 Gestión de respuesta a incidentes",),
        "¿Tienen un plan de respuesta a incidentes documentado, con responsables y que se haya probado o usado?",
    ),
    Control(
        "BCP-01", "Continuidad del negocio",
        "Plan de continuidad y recuperación ante desastres (DRP) probado.",
        ("5.29 Seguridad durante una interrupción", "5.30 Preparación TIC para la continuidad", "8.14 Redundancia"),
        (),
        "¿Tienen un plan de continuidad / recuperación ante desastres con tiempos de recuperación definidos y probado?",
    ),
    Control(
        "PEN-01", "Pruebas de penetración",
        "Pentests internos/externos periódicos y corrección de hallazgos.",
        ("8.8 Gestión de vulnerabilidades técnicas", "5.35 Revisión independiente"),
        ("CIS 18 Pruebas de penetración",),
        "¿Realizan pruebas de penetración (internas o por un tercero) al menos una vez al año?",
    ),
    Control(
        "FIS-01", "Seguridad física",
        "Control de acceso físico a oficinas y centros de datos, protección de equipos.",
        ("7.1 Perímetros de seguridad física", "7.2 Entrada física", "7.4 Monitoreo de seguridad física", "7.8 Ubicación y protección de equipos"),
        (),
        "¿El acceso físico a las áreas con servidores o equipos de red está restringido y registrado?",
    ),
)

CONTROLES_POR_ID: dict[str, Control] = {c.id: c for c in CONTROLES}
IDS_CONTROLES: list[str] = [c.id for c in CONTROLES]
ESTADOS = ("cubierto", "parcial", "no_cubierto", "desconocido")


def catalogo_para_prompt() -> str:
    """Catálogo en texto plano para incluir en el system prompt (estable → cacheable)."""
    lineas = []
    for c in CONTROLES:
        iso = "; ".join(c.iso27002) or "—"
        cis = "; ".join(c.cis_v8) or "—"
        lineas.append(f"- {c.id} | {c.nombre}: {c.descripcion}\n  ISO 27002: {iso}\n  CIS v8: {cis}")
    return "\n".join(lineas)
