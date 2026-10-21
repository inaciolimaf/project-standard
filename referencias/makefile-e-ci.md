# Makefile e CI

## Makefile

Primeira linha: `# <App> — comandos principais. \`make\` sem alvo lista os comandos.`
Todo alvo tem `## descrição`; `help` é o primeiro alvo (padrão) e lista com cor:

```make
help: ## Lista os comandos disponiveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
```

Seções com comentário-régua (`# --- Docker ----...`). Alvos em português, curtos:

| Seção | Alvo | Faz |
|---|---|---|
| Docker | `docker-up` / `docker-down` / `docker-logs` | `docker compose up -d` / `down` / `logs -f` |
| | `db-teste` | `CREATE DATABASE <app>_teste` no Postgres do compose (`\|\| true`) |
| Banco | `migrar` | `uv run alembic upgrade head` |
| | `<carga>` | `migrar` como dependência; `ARGS=` repassa flags |
| Qualidade | `teste` | `DATABASE_URL_TESTE=$(DB_TESTE_URL) uv run pytest` |
| | `lint` | `ruff check .` + `ruff format --check .` + `python -m ferramentas.tamanho_de_funcao` + `lint-imports` (o mesmo que o CI: o local não passa onde o CI quebra) |
| | `fronteiras` | só `lint-imports` (camadas, interface pública, sem ciclos) |
| | `formato` | `ruff format .` |
| | `tipos` | `mypy` |
| | `docs` | `python -m ferramentas.cobertura_da_documentacao` (ver `documentacao.md`) |
| Front | `tipos-web` | `python -m ferramentas.openapi` + `npm run tipos` |
| | `web-dev` | `npm run dev` |
| | `web-teste` | `npm run lint && npm run formato:checar && npx tsc -b && npm test` (mesma ordem do CI) |
| | `web-formato` | `npm run formato` (prettier, corrige) |
| | `web-cobertura` | `npm run cobertura` (Vitest com cobertura; falha abaixo de 60%) |
| | `web-build` | `npm run build` |
| | `e2e` | depende de `web-build`; `npm run e2e -- --project=rotas` |
| | `celular` | depende de `web-build`; `npm run celular` |
| | `e2e-fluxos` | depende de `web-build`; projeto `fluxos` do Playwright |

Variáveis no topo com padrão sobrescrevível: `API_URL ?= http://localhost:8000`,
`DB_TESTE_URL := ...:$(or $(PORTA_DB),5432)/<app>_teste`. Todos os alvos em `.PHONY`.

Scripts do `web/package.json`: `dev`, `build` (`tsc -b && vite build`), `preview` (porta fixa
4173 `--strictPort`), `tipos`, `lint`, `formato` (`prettier --write .`), `formato:checar`
(`prettier --check .`), `test` (`vitest run`), `cobertura` (`vitest run --coverage`), `e2e`,
`celular`.

## CI (`.github/workflows/ci.yml`)

Primeira linha: comentário de uma linha dizendo o que roda. `on: push: [main]` + `pull_request`.

**`back`** (service Postgres com healthcheck, banco `<app>_teste`):
1. `astral-sh/setup-uv` → `uv sync --frozen`
2. `ruff check . && ruff format --check .`
3. `python -m ferramentas.tamanho_de_funcao`
4. `lint-imports`
5. `python -m ferramentas.cobertura_da_documentacao`
6. `mypy`
7. `pytest -q` com `DATABASE_URL_TESTE`
8. contrato: gera `openapi.json`, `npm ci`, `npm run tipos`, `git diff --exit-code -- src/api/tipos.ts`

**`web`** (`working-directory: web`, Node 22 com cache npm pelo `package-lock.json`):
`npm ci --no-audit --no-fund` → `npm run lint` → `npm run formato:checar` → `npx tsc -b` →
`npm run cobertura` (testes + piso de 60%) → `npm run build`

**`e2e`** (`needs: [back, web]`, Postgres + env de produção falsa com segredos de 32+ bytes):
dados falsos (mesma fábrica dos testes de integração) → `alembic upgrade head` → carga →
cria conta e2e pela CLI → sobe uvicorn em background e espera `/health` num laço de `curl` com
tempo limite (nunca `sleep N`; se não subir, imprime o log da API e falha) → `playwright
install --with-deps chrome` → build → projetos `rotas`, `celular` e `fluxos` → `upload-artifact`
das capturas com `if: always()`.

Regra: todo passo do CI tem alvo equivalente no Makefile.
