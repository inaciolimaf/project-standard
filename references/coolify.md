# Deploying on Coolify

What needs to change in a project that runs locally with `docker-compose.yml` to deploy on
Coolify. Reference: Crivo's `docker-compose-coolify.yml` and `docs/deploy-coolify.md`.

The variable names below are Crivo's (`AMBIENTE`, `MIGRAR_AO_SUBIR`, `COOKIES_SEGUROS`,
`CAMINHO_*`): they are configured on the server and stay as they are. A new project names its
variables in English from the start (`ENVIRONMENT`, `MIGRATE_ON_START`, `SECURE_COOKIES`,
`*_PATH`).

## Environment variables on the server: never rename

The **Environment Variables** tab is state that lives outside the repository. Whatever was typed
there is a contract:

- **Never rename or remove a variable that is configured on the server.** The next deploy reads
  the new name, finds nothing and either starts with a default (wrong, silently) or refuses to
  start. If the code's field changes name, it reads the old variable by alias
  (`Field(validation_alias="SEGREDO_JWT")`, see `runtime.md`), and the compose file keeps passing
  the old name.
- **A new variable** comes in with a safe default (`${NEW_VAR:-default}` in the compose and a
  default in `Settings`) or, if it has none, with an explicit notice to the server owner listing
  what to configure (name, how to generate it, which service) before the deploy, and the
  `docs/deploy-coolify.md` updated. A required variable (`:?`) added without notice makes the
  deploy fail.
- Commands typed in the container's terminal (CLI, seed) follow the same rule: change only by
  agreement.

## Why a separate compose file

The local compose publishes ports on the host, has dev passwords with defaults and mounts
relative `./folders`. On Coolify that would open the database to the internet, start with a weak
password and look for the data in a directory that does not exist. Instead of conditionals, there
is a dedicated `docker-compose-coolify.yml`, and its top lists the numbered differences.

## The changes, one by one

| # | Local (`docker-compose.yml`) | Coolify (`docker-compose-coolify.yml`) | Why |
|---|---|---|---|
| 1 | `ports: "${PORTA_DB:-5432}:5432"` on every service | `expose: ["5432"]` (and `"8000"`, `"80"`) | Coolify's proxy (Traefik) routes through the internal Docker network. `ports` publishes on the host interface: Postgres would be open to the internet |
| 2 | — | only `web` gets a domain (tab **Domains**), with `SERVICE_FQDN_WEB_80: ${SERVICE_FQDN_WEB_80:-}` in `environment` | `web`'s Caddy proxies `/api/*` and `/health` to `api:8000`. A single domain: no CORS, no cross-site cookie. The `SERVICE_FQDN_<SERVICE>_<PORT>` variable is how Coolify knows which service/port to expose |
| 3 | `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-crivo}` | `${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}` | No default: if the variable is missing, the deploy fails instead of starting with a dev password |
| 4 | `SEGREDO_X: ${SEGREDO_X:?set it in .env}` | `${SEGREDO_X:?set SEGREDO_X with 32+ bytes}` | The message states the requirement; the backend settings refuse short/example/repeated |
| 5 | `AMBIENTE: ${AMBIENTE:-local}` | `AMBIENTE: producao` fixed | Turns on the production validations (secrets, cookies) and JSON logs |
| 6 | `COOKIES_SEGUROS: ${COOKIES_SEGUROS:-false}` | `COOKIES_SEGUROS: "true"` | `Secure` cookie behind HTTPS; the settings refuse `false` in production |
| 7 | `make migrar` by hand | `MIGRAR_AO_SUBIR: "true"` | The entrypoint runs `alembic upgrade head` before uvicorn; on Coolify nobody runs migrations by hand |
| 8 | `./acervo:/app/acervo:ro` | `${CAMINHO_ACERVO:-/data/<app>/acervo}:/app/acervo:ro` | An absolute host path, overridable. Large data never goes in the image nor in git |
| 9 | — | `restart: unless-stopped` on every service | Comes back on its own after a crash or reboot |
| 10 | healthcheck without `start_period` | `start_period: 40s` on `api`, `15s` on `web` | The build/first start is slow; without it Coolify marks it as failed before it is up |
| 11 | `web` without a healthcheck | `wget -q --spider http://127.0.0.1:80/` | Coolify only considers the deploy ready when everything is healthy. `wget` already exists on alpine; do not install curl |
| 12 | fixed memory parameters in the Postgres `command` | `shared_buffers=${PG_SHARED_BUFFERS:-512MB}` and smaller `work_mem`/`maintenance_work_mem` | Adjustable to the server's RAM without editing the file |
| 13 | plain uvicorn | `--proxy-headers --forwarded-allow-ips "*"` in the `CMD` | Behind two proxies (Traefik → Caddy), the backend must read `X-Forwarded-*` to know it is HTTPS and the real IP |

What does **not** change: Dockerfiles, `depends_on: condition: service_healthy`, the Postgres
named volume, the project name (`name:`), and the names of the variables already on the server.

## Prerequisites in the code (without them the compose is not enough)

- **Settings that refuse to start in production** with a secret that is missing, < 32 bytes,
  equal to `.env.example` or repeated, and with insecure cookies (see `runtime.md`).
- **`/health`** at the API root that answers fast and states the database and data status
  (missing optional data shows as `missing`, it does not bring health down).
- **Entrypoint** `docker/entrypoint-api.sh` with the migrate-on-start variable and `exec "$@"`.
- **Caddyfile** in `web` with `handle /api/*` and `handle /health` → `reverse_proxy api:8000`
  and the SPA fallback (`try_files {path} /index.html`).
- **Frontend with a relative URL** (`BASE = "/api/v1"`), never `http://localhost:8000` in code.
- **JSON logs** in production (Coolify shows stdout).
- **CLI inside the image** (`[project.scripts]`) for seed and admin from the terminal.

## Step by step in the panel (goes in each project's `docs/deploy-coolify.md`)

1. **Secrets** on the local machine: `openssl rand -hex 32` for each secret (all different),
   `openssl rand -hex 16` for `POSTGRES_PASSWORD`.
2. **Large data** (if any): pack it (`tar -I 'zstd -T0 -3'`), `sha256sum`, serve with
   `python3 -m http.server` + `cloudflared tunnel --url`, and on the host (Coolify → Servers →
   Terminal) `curl -L -C -` to `/data/<app>/...`, `sha256sum -c`, extract.
3. **New Resource → Docker Compose**, repository and branch `main`, **Compose file** =
   `/docker-compose-coolify.yml`.
4. **Environment Variables**: `POSTGRES_PASSWORD`, the secrets, the data path variables if they
   differ from the default, `PG_SHARED_BUFFERS`, external API keys. Keep this list in the doc: it
   is what the server owner checks when a deploy brings a new variable.
5. **Domains** only on the `web` service.
6. **Deploy**. Migrations run on their own; `api` only becomes healthy with database and data.
7. **Seed** from the `api` container terminal: data load and the CLI's admin creation command
   with `--email ...` (password typed, never through a variable).
8. **Operate**: `https://domain/health`, logs in the panel, backup only of the Postgres volume,
   update = push to `main` (Coolify rebuilds and migrates).

## Checklist to take a project to Coolify

- [ ] `docker-compose-coolify.yml` with the 13 changes above and the top comment
- [ ] `.env.example` with a `# --- Coolify / production ---` section (data path and `PG_*`
      variables)
- [ ] settings refuse insecure production + a test for it
- [ ] `/health`, entrypoint with migration, Caddyfile with proxy
- [ ] `docs/deploy-coolify.md` with the step by step, the variable list and the expected sizes
      (disk/RAM)
- [ ] no variable already on the server renamed or removed; new ones with a default or announced
- [ ] the README points to the deploy doc

## Large change

If taking the project to Coolify requires touching a lot of code (secret settings, `/health`,
absolute URLs scattered in the frontend, a missing CLI), split it by area between subagents in
worktrees, as described in `lint-and-types.md` → "When to use multiple agents": the main agent
writes the compose and the doc; subagents take care of the backend (settings + health +
entrypoint) and the frontend (relative URLs + Caddyfile) in parallel.
