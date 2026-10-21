# Docker, compose e deploy

## Dois compose

Resumo abaixo; a lista completa do que muda para produção, com o porquê de cada item, está em
[coolify.md](coolify.md).

| | `docker-compose.yml` (local) | `docker-compose-<paas>.yml` (produção, ex.: Coolify) |
|---|---|---|
| Rede | `ports: "${PORTA_X:-padrao}:porta"` | `expose` — só o proxy do PaaS fala com os serviços; `ports` deixaria o Postgres na internet |
| Domínio | — | só o `web`; o Caddy dele faz proxy de `/api` e `/health` (um domínio, sem CORS nem cookie cross-site) |
| Segredos | `${SEGREDO:?defina SEGREDO no .env}`; senha do banco com padrão de dev | todos com `:?`, inclusive `POSTGRES_PASSWORD` |
| `AMBIENTE` | `${AMBIENTE:-local}` | `producao` fixo, `COOKIES_SEGUROS: "true"` |
| Migração | `make migrar` | `MIGRAR_AO_SUBIR: "true"` no entrypoint |
| Volumes de dados | `./dados:/app/dados:ro` | `${CAMINHO_DADOS:-/data/<app>/dados}:/app/dados:ro` |
| Reinício | — | `restart: unless-stopped`, `start_period` no healthcheck |

O compose de produção começa com um comentário numerado listando as diferenças para o local.

Comuns:
- `name: <app>` no topo.
- Todo serviço com `healthcheck`; dependentes com `depends_on: condition: service_healthy`.
  API: `python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"`
  (sem instalar curl). Postgres: `pg_isready -U ... -d ...`.
- Variáveis com padrão `${VAR:-padrao}`; `TZ` em todo serviço.
- Postgres com parâmetros de memória no `command` e `shm_size` quando há carga grande.
- Dados grandes (GBs) **sempre volume**, nunca camada da imagem.

## Dockerfile do back (`docker/api.Dockerfile`)

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/usr/local
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
# Camada de dependencias, invalidada so quando o lock muda.
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
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
```

- `COPY` explícito por pasta (nada de `COPY . .`).
- `--frozen --no-dev`: imagem reproduzível, sem ferramentas de teste.

## Entrypoint (`docker/entrypoint-api.sh`)

```sh
#!/bin/sh
# Migra antes de servir, se pedido: em PaaS com deploy automatico ninguem roda `alembic` na mao.
set -e
if [ "${MIGRAR_AO_SUBIR:-false}" = "true" ]; then
	alembic upgrade head
fi
exec "$@"
```

## Dockerfile do front (`docker/web.Dockerfile`)

Multi-stage: `node:22-alpine` com `npm ci --no-audit --no-fund` (camada só com
`package*.json`) e `npm run build`; depois `caddy:2-alpine` com `/srv` + `Caddyfile`. Contexto
= raiz do repo quando o front importa arquivo do back.

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

## Banco

- Imagem do Postgres **não muda de base libc** num volume existente (alpine/musl ↔
  debian/glibc muda a ordenação de texto e corrompe índices em silêncio). Extensão nova
  (pgvector) é compilada na mesma base (`docker/db.Dockerfile`).
- Testes e CI usam a mesma versão maior do Postgres que produção.

## `.dockerignore` / `.gitignore`

`.dockerignore`: `.git`, `.venv`, dados grandes, `web/node_modules`, `web/dist`,
`**/__pycache__`, `.env`, `.env.*`, arquivos de credencial.

`.gitignore`: dados grandes (com comentário do tamanho), caches Python
(`.venv .mypy_cache .ruff_cache .pytest_cache __pycache__`), `node_modules`, `web/dist`,
`.env`, `.env.*`, `!.env.example`, artefatos gerados (`openapi.json`).

## `.env.example`

Seções com cabeçalho `# --- nome (spec NN) ---`, cada variável com comentário do que é, unidade
e o que acontece se vazia. Segredos com valor `troque-...` (que a config recusa em produção). No
topo: "Copie para `.env` (que NAO vai para o git). Nenhum segredo tem valor padrão no código".

## Deploy

`docs/deploy-<paas>.md` passo a passo numerado: gerar segredos (`openssl rand -hex 32`),
levar dados grandes ao host, configurar o PaaS, seed pelo terminal do contêiner, conferir.
