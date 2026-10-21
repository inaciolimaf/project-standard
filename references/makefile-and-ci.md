# Makefile and CI

## Makefile

First line: `# <App> — main commands. \`make\` with no target lists the commands.`
Every target has a `## description`; `help` is the first (default) target and lists with color:

```make
help: ## List the available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
```

Sections with a ruler comment (`# --- Docker ----...`). Targets are short. **A new project names
them in English; an existing project keeps the names people already type** (operations rule in
`SKILL.md`). The table gives both: the standard's name and Crivo's.

| Section | Target (new project) | Crivo | Does |
|---|---|---|---|
| Docker | `docker-up` / `docker-down` / `docker-logs` | same | `docker compose up -d` / `down` / `logs -f` |
| | `db-test` | `db-teste` | `CREATE DATABASE <app>_test` on the compose Postgres (`\|\| true`) |
| Database | `migrate` | `migrar` | `uv run alembic upgrade head` |
| | `<load>` | `<carga>` | `migrate` as a dependency; `ARGS=` passes flags through |
| Quality | `test` | `teste` | `<TEST_DB_VAR>=$(TEST_DB_URL) uv run pytest` |
| | `lint` | `lint` | `ruff check .` + `ruff format --check .` + `python -m tools.function_size` + `lint-imports` (the same as CI: local does not pass where CI breaks) |
| | `boundaries` | `fronteiras` | only `lint-imports` (layers, public interface, no cycles) |
| | `format` | `formato` | `ruff format .` |
| | `types` | `tipos` | `mypy` |
| | `docs` | `docs` | `python -m tools.docs_coverage` (see `documentation.md`) |
| Frontend | `web-types` | `tipos-web` | `python -m tools.openapi` + the npm types script |
| | `web-dev` | `web-dev` | `npm run dev` |
| | `web-test` | `web-teste` | lint, format check, `npx tsc -b`, `npm test` (same order as CI) |
| | `web-format` | `web-formato` | prettier, fixing |
| | `web-coverage` | `web-cobertura` | Vitest with coverage; fails below 60% |
| | `web-build` | `web-build` | `npm run build` |
| | `e2e` | `e2e` | depends on `web-build`; Playwright project `routes` |
| | `mobile` | `celular` | depends on `web-build`; Playwright project `mobile` |
| | `e2e-flows` | `e2e-fluxos` | depends on `web-build`; Playwright project `flows` |

Variables at the top with overridable defaults: `API_URL ?= http://localhost:8000`,
`TEST_DB_URL := ...:$(or $(DB_PORT),5432)/<app>_test`. Every target in `.PHONY`.

Scripts in `web/package.json` (new project): `dev`, `build` (`tsc -b && vite build`), `preview`
(fixed port 4173 `--strictPort`), `types`, `lint`, `format` (`prettier --write .`),
`format:check` (`prettier --check .`), `test` (`vitest run`), `coverage`
(`vitest run --coverage`), `e2e`, `mobile`. Crivo keeps its Portuguese script names
(`tipos`, `formato`, `formato:checar`, `cobertura`, `celular`).

## CI (`.github/workflows/ci.yml`)

First line: a one-line comment saying what runs. `on: push: [main]` + `pull_request`.

**`back`** (Postgres service with a healthcheck, database `<app>_test`):
1. `astral-sh/setup-uv` → `uv sync --frozen`
2. `ruff check . && ruff format --check .`
3. `python -m tools.function_size`
4. `lint-imports`
5. `python -m tools.docs_coverage`
6. `mypy`
7. `pytest -q` with the test database URL
8. contract: generate `openapi.json`, `npm ci`, the types script,
   `git diff --exit-code -- src/api/types.ts`

**`web`** (`working-directory: web`, Node 22 with npm cache by `package-lock.json`):
`npm ci --no-audit --no-fund` → lint → format check → `npx tsc -b` → coverage (tests + the 60%
floor) → `npm run build`

**`e2e`** (`needs: [back, web]`, Postgres + a fake production env with 32+ byte secrets):
fake data (the same factory as the integration tests) → `alembic upgrade head` → load → create
the e2e account through the CLI → start uvicorn in the background and wait for `/health` in a
`curl` loop with a timeout (never `sleep N`; if it does not come up, print the API log and fail)
→ `playwright install --with-deps chrome` → build → projects `routes`, `mobile` and `flows` →
`upload-artifact` of the captures with `if: always()`.

Rule: every CI step has an equivalent Makefile target.
