"""Genera el prompt maestro (Entregable 1) como archivo Markdown, fuera de la interfaz.

Uso:
    python scripts/exportar_prompt.py                      # → docs/prompt_maestro_centinela_ig1.md
    python scripts/exportar_prompt.py ruta/salida.md

No incluye el catálogo CIS (licencia CC BY-NC-ND 4.0), solo las instrucciones del agente.
Requiere el catálogo local (scripts/importar_cis.py) porque las instrucciones se arman con él.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chatbot import exportar  # noqa: E402

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "prompt_maestro_centinela_ig1.md"


def main(argv: list[str]) -> int:
    destino = Path(argv[1]) if len(argv) > 1 else DESTINO
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(exportar.prompt_maestro_md(), encoding="utf-8")
    print(f"Prompt maestro guardado en {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
