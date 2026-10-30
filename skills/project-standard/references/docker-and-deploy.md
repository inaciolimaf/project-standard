# Docker, compose and deploy

## Two compose files

Summary below; the complete list of what changes for production, with the reason for each item,
is in [coolify.md](coolify.md). Variable names are Crivo's (Portuguese, set on the server, never
renamed); a new project names them in English.

| | `docker-compose.yml` (local) | `docker-compose-<paas>.yml` (production, e.g. Coolify) |
|---|---|---|
| Network | `ports: "${PORT_X:-default}:port"` | `expose` — only the PaaS proxy talks to the services; `ports` would put Postgres on the internet |
| Domain | — | only `web`; its Caddy proxies `/api` and `/health` (one domain, no CORS nor cross-site cookie) |
| Secrets | `${SECRET:?set SECRET in .env}`; database password with a dev default | all with `:?`, including `POSTGRES_PASSWORD` |
| Environment | `${AMBIENTE:-local}` | production fixed (`AMBIENTE: producao`), `COOKIES_SEGUROS: "true"` |
| Migration | the Makefile's migrate target | `MIGRAR_AO_SUBIR: "true"` in the entrypoint |
| Data volumes | `./data:/app/data:ro` | `${DATA_PATH:-/data/<app>/data}:/app/data:ro` |
| Restart | — | `restart: unless-stopped`, `start_period` in the healthcheck |

The production compose starts with a numbered comment listing the differences from the local one.

Common:
- `name: <app>` at the top.
- Every service with a `healthcheck`; dependents with `depends_on: condition: service_healthy`.
  API: `python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"`
  (without installing curl). Postgres: `pg_isready -U ... -d ...`.
- Variables with a default `${VAR:-default}`; `TZ` on every service.
- Postgres with memory parameters in `command` and `shm_size` when there is a large load.
- Large data (GBs) **always a volume**, never an image layer.

## Environment variables: a contract with whoever runs it

**An environment variable configured by hand on the server is never renamed or removed** —
renaming breaks the next deploy silently. The compose files keep passing the existing names;
when the code's settings field has another name, it reads the variable by alias (`runtime.md`).
A new variable enters with a safe default (`${VAR:-default}`) or with an explicit notice to the
server owner and the list of what to configure; `.env.example` and `docs/deploy-<paas>.md`
change in the same commit.

## Backend Dockerfile (`docker/api.Dockerfile`)

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/usr/local
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
# Dependency layer, invalidated only when the lock changes.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY api/ ./api/
COPY pipeline/ ./pipeline/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY docker/entrypoint-api.sh /usr/local/bin/entrypoint-api
RUN uv sync --frozen --no-dev
EXPOSE 8000
ENTRYPOINT ["entrypoint-api"]
CMD ["uvicorn", "api.core.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
```

- Explicit `COPY` per folder (no `COPY . .`).
- `--frozen --no-dev`: a reproducible image, without test tools.

## Entrypoint (`docker/entrypoint-api.sh`)

```sh
#!/bin/sh
# Migrate before serving, if asked: on a PaaS with automatic deploys nobody runs `alembic` by hand.
set -e
if [ "${MIGRAR_AO_SUBIR:-false}" = "true" ]; then
	alembic upgrade head
fi
exec "$@"
```

## Frontend Dockerfile (`docker/web.Dockerfile`)

Multi-stage: `node:22-alpine` with `npm ci --no-audit --no-fund` (a layer with only
`package*.json`) and `npm run build`; then `caddy:2-alpine` with `/srv` + `Caddyfile`. Context =
the repository root when the frontend imports a file from the backend.

```
:80 {
	root * /srv
	encode gzip
	handle /api/* { reverse_proxy api:8000 }
	handle /health { reverse_proxy api:8000 }
	handle { try_files {path} /index.html
	         file_server }
}
```

## Database

- The Postgres image **does not change its libc base** on an existing volume (alpine/musl ↔
  debian/glibc changes text collation and corrupts indexes silently). A new extension
  (pgvector) is compiled on the same base (`docker/db.Dockerfile`).
- Tests and CI use the same Postgres major version as production.

## `.dockerignore` / `.gitignore`

`.dockerignore`: `.git`, `.venv`, large data, `web/node_modules`, `web/dist`,
`**/__pycache__`, `.env`, `.env.*`, credential files.

`.gitignore`: large data (with a comment of its size), Python caches
(`.venv .mypy_cache .ruff_cache .pytest_cache __pycache__`), `node_modules`, `web/dist`,
`.env`, `.env.*`, `!.env.example`, generated artifacts (`openapi.json`).

## `.env.example`

Sections with a `# --- name (spec NN) ---` header, each variable with a comment of what it is,
its unit and what happens if empty. Secrets with a `change-me-...` value (which the settings
refuse in production). At the top: "Copy to `.env` (which does NOT go to git). No secret has a
default value in the code".

## Deploy

A numbered step-by-step `docs/deploy-<paas>.md`: generate secrets (`openssl rand -hex 32`), take
large data to the host, configure the PaaS (with the list of environment variables), seed from
the container terminal, check.
