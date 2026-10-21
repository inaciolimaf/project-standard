"""Escreve o OpenAPI do back em `openapi.json`: e dele que `web/src/api/tipos.ts` nasce (spec 06 §1)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main() -> int:
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    os.environ.setdefault("SEGREDO_JWT", "x")
    os.environ.setdefault("MIDIA_SEGREDO", "y")
    from api.main import criar_app

    destino = RAIZ / "openapi.json"
    destino.write_text(
        json.dumps(criar_app().openapi(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"{destino.relative_to(RAIZ)} escrito", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
