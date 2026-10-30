"""Writes the backend OpenAPI to `openapi.json`: `web/src/api/types.ts` is generated from it (spec 06 §1)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    # Placeholder values only so the settings load; the variable names are the ones the server has.
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    os.environ.setdefault("SEGREDO_JWT", "x")
    os.environ.setdefault("MIDIA_SEGREDO", "y")
    from api.core.main import create_app

    target = ROOT / "openapi.json"
    target.write_text(
        json.dumps(create_app().openapi(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"{target.relative_to(ROOT)} written", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
