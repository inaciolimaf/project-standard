# Known gaps

What the standard does not cover yet, or covers inconsistently, as seen in Crivo on 2026-10-20.
When one is resolved, move the decision into the right reference and delete it from here.

| # | Gap | Where | Suggestion |
|---|---|---|---|
| 3 | No pre-commit hook | root | `pre-commit` (or `lefthook`) with ruff, function size, eslint |
| 7 | `ghcr.io/astral-sh/uv:latest` without a pinned version | `docker/api.Dockerfile` | pin the uv version |
| 8 | Python tests outside mypy | `pyproject.toml` | decide: include `tests` with overrides or keep them out on purpose |
| 9 | The `integration` marker exists but there is no target to run only unit tests | `Makefile` | a unit-only target: `pytest -m "not integration"` |
| 12 | Crivo does not have the event loop and deadline rules yet (ruff `ASYNC`, the architecture test against the synchronous `Session`, the database timeouts and their test) | `pyproject.toml`, `api/core/db.py`, `tests/` | apply as in `runtime.md`; delete this row when done |
| 11 | No dependency audit (`pip-audit`, `npm audit`) nor Dependabot | CI | weekly job |
