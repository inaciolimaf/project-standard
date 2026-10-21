# Deploy no Coolify

O que precisa mudar num projeto que roda local com `docker-compose.yml` para subir no Coolify.
Referência: `docker-compose-coolify.yml` e `docs/deploy-coolify.md` do Crivo.

## Por que um compose separado

O compose local publica portas no host, tem senhas de dev com padrão e monta `./pastas`
relativas. No Coolify isso abriria o banco para a internet, subiria com senha fraca e
procuraria os dados num diretório que não existe. Em vez de condicionais, existe um
`docker-compose-coolify.yml` próprio, e o topo dele lista as diferenças numeradas.

## As mudanças, uma a uma

| # | Local (`docker-compose.yml`) | Coolify (`docker-compose-coolify.yml`) | Por quê |
|---|---|---|---|
| 1 | `ports: "${PORTA_DB:-5432}:5432"` em todo serviço | `expose: ["5432"]` (e `"8000"`, `"80"`) | O proxy do Coolify (Traefik) roteia pela rede interna do Docker. `ports` publica na interface do host: o Postgres ficaria aberto para a internet |
| 2 | — | só o `web` recebe domínio (aba **Domains**), com `SERVICE_FQDN_WEB_80: ${SERVICE_FQDN_WEB_80:-}` no `environment` | O Caddy do `web` faz proxy de `/api/*` e `/health` para `api:8000`. Um domínio só: sem CORS, sem cookie cross-site. A variável `SERVICE_FQDN_<SERVICO>_<PORTA>` é como o Coolify sabe qual serviço/porta expor |
| 3 | `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-crivo}` | `${POSTGRES_PASSWORD:?defina POSTGRES_PASSWORD}` | Sem padrão: falta a variável, o deploy falha em vez de subir com senha de dev |
| 4 | `SEGREDO_X: ${SEGREDO_X:?defina no .env}` | `${SEGREDO_X:?defina SEGREDO_X com 32+ bytes}` | A mensagem diz o requisito; a config do back recusa curto/de exemplo/repetido |
| 5 | `AMBIENTE: ${AMBIENTE:-local}` | `AMBIENTE: producao` fixo | Liga as validações de produção (segredos, cookies) e o log em JSON |
| 6 | `COOKIES_SEGUROS: ${COOKIES_SEGUROS:-false}` | `COOKIES_SEGUROS: "true"` | Cookie `Secure` atrás de HTTPS; a config recusa `false` em produção |
| 7 | `make migrar` na mão | `MIGRAR_AO_SUBIR: "true"` | O entrypoint roda `alembic upgrade head` antes do uvicorn; no Coolify ninguém roda migração na mão |
| 8 | `./acervo:/app/acervo:ro` | `${CAMINHO_ACERVO:-/data/<app>/acervo}:/app/acervo:ro` | Caminho absoluto no host, sobrescrevível. Dados grandes nunca vão na imagem nem no git |
| 9 | — | `restart: unless-stopped` em todo serviço | Volta sozinho depois de queda ou reboot |
| 10 | healthcheck sem `start_period` | `start_period: 40s` na `api`, `15s` no `web` | O build/primeira subida é lento; sem isso o Coolify marca como falho antes de subir |
| 11 | `web` sem healthcheck | `wget -q --spider http://127.0.0.1:80/` | O Coolify só considera o deploy pronto com todos saudáveis. `wget` já existe no alpine; não instale curl |
| 12 | parâmetros de memória fixos no `command` do Postgres | `shared_buffers=${PG_SHARED_BUFFERS:-512MB}` e `work_mem`/`maintenance_work_mem` menores | Ajustável pela RAM do servidor sem editar o arquivo |
| 13 | uvicorn simples | `--proxy-headers --forwarded-allow-ips "*"` no `CMD` | Atrás de dois proxies (Traefik → Caddy), o back precisa ler `X-Forwarded-*` para saber que é HTTPS e o IP real |

O que **não** muda: Dockerfiles, `depends_on: condition: service_healthy`, volume nomeado do
Postgres, nome do projeto (`name:`).

## Pré-requisitos no código (sem eles o compose não basta)

- **Config que recusa subir em produção** com segredo ausente, < 32 bytes, igual ao
  `.env.example` ou repetido, e com `COOKIES_SEGUROS=false` (ver `runtime.md`).
- **`/health`** na raiz da API que responde rápido e diz o estado de banco e dados (dado
  opcional ausente aparece como `ausente`, não derruba o health).
- **Entrypoint** `docker/entrypoint-api.sh` com `MIGRAR_AO_SUBIR` e `exec "$@"`.
- **Caddyfile** no `web` com `handle /api/*` e `handle /health` → `reverse_proxy api:8000` e
  fallback SPA (`try_files {path} /index.html`).
- **Front com URL relativa** (`BASE = "/api/v1"`), nunca `http://localhost:8000` no código.
- **Log JSON** em produção (o Coolify mostra stdout).
- **CLI dentro da imagem** (`[project.scripts]`) para seed e admin pelo terminal do contêiner.

## Passo a passo no painel (vai em `docs/deploy-coolify.md` de cada projeto)

1. **Segredos** na máquina local: `openssl rand -hex 32` para cada segredo (diferentes),
   `openssl rand -hex 16` para `POSTGRES_PASSWORD`.
2. **Dados grandes** (se houver): empacotar (`tar -I 'zstd -T0 -3'`), `sha256sum`, servir com
   `python3 -m http.server` + `cloudflared tunnel --url`, e no host (Coolify → Servers →
   Terminal) `curl -L -C -` para `/data/<app>/...`, `sha256sum -c`, extrair.
3. **New Resource → Docker Compose**, repositório e branch `main`, **Compose file** =
   `/docker-compose-coolify.yml`.
4. **Environment Variables**: `POSTGRES_PASSWORD`, os segredos, `CAMINHO_*` se fugir do
   padrão, `PG_SHARED_BUFFERS`, chaves de API externas.
5. **Domains** só no serviço `web`.
6. **Deploy**. Migrations rodam sozinhas; a `api` só fica saudável com banco e dados.
7. **Seed** pelo terminal do contêiner `api`: carga de dados e
   `<cli> admin criar --email ...` (senha digitada, nunca por variável).
8. **Operar**: `https://dominio/health`, logs no painel, backup só do volume do Postgres,
   atualizar = push na `main` (o Coolify reconstrói e migra).

## Checklist para levar um projeto ao Coolify

- [ ] `docker-compose-coolify.yml` com as 13 mudanças acima e o comentário de topo
- [ ] `.env.example` com seção `# --- Coolify / producao ---` (variáveis `CAMINHO_*`, `PG_*`)
- [ ] config recusa produção insegura + teste disso
- [ ] `/health`, entrypoint com migração, Caddyfile com proxy
- [ ] `docs/deploy-coolify.md` com o passo a passo e tamanhos (disco/RAM) esperados
- [ ] README aponta para o doc de deploy

## Mudança grande

Se levar o projeto ao Coolify exigir mexer em muito código (config de segredos, `/health`,
URLs absolutas no front espalhadas, CLI inexistente), divida por área entre subagentes em
worktrees, como descrito em `lint-e-tipos.md` → "Quando usar multiagente": o agente principal
escreve o compose e o doc; subagentes cuidam de back (config + health + entrypoint) e front
(URLs relativas + Caddyfile) em paralelo.
