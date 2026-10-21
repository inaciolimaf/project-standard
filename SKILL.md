---
name: padrao-de-projeto
description: Padrão de engenharia do Inácio para projetos Python (FastAPI + uv) com front React (Vite + TS) — estrutura de pastas, pirâmide de testes, lint (ruff, mypy estrito, teto de 30 linhas por função, eslint, tsc), Docker/compose, Coolify, Makefile, CI, documentação do sistema (docs/sistema + CLAUDE.md, atualizada a cada mudança), specs com regra+garantia e commits. Use ao criar um projeto novo, ao auditar ou alinhar um projeto existente a esse padrão ("aplica o padrão", "deixa igual ao crivo"), ou quando o usuário pedir para mudar o padrão em si.
---

# Padrão de projeto

Extraído do Crivo (sistema de questões de concurso do autor, a referência viva). Esta skill mora no
repositório `github.com/inaciolimaf/padrao-de-projeto`; o Crivo guarda uma cópia sincronizada em
`.claude/skills/padrao-de-projeto/`. Quando um detalhe não estiver aqui e você estiver no Crivo, o
arquivo correspondente dele é a fonte.

## Princípios (valem para tudo abaixo)

1. **Regra sem garantia não existe.** Toda regra do projeto tem um teste, um lint ou uma
   restrição de desenho que impede a repetição. Se não dá para garantir, não vira regra.
2. **Contrato entre duas partes tem um lado só de verdade.** Back × front: tipos do front
   gerados do OpenAPI do back. Back × pipeline: um teste que exercita os dois com o mesmo dado.
3. **Transformação de conteúdo não perde informação em silêncio.** Teste dourado com casos
   reais + contagem de problemas que precisa dar zero.
4. **Nenhum segredo tem valor padrão.** Em produção o processo recusa subir com segredo
   ausente, curto (< 32 bytes) ou igual ao do `.env.example`.
5. **Um comando por tarefa.** Tudo que se roda está no `Makefile`; `make` sem alvo lista.
6. **CI = o que o Makefile roda**, sem passo que só exista no CI.
7. **Mudou o sistema, mudou a documentação, no mesmo commit.** `docs/sistema/` explica o
   sistema como está, o `CLAUDE.md` explica como trabalhar nele, e os dois são mantidos
   arrumados a cada passagem. Garantia: `make docs`. Ver `referencias/documentacao.md`.

## Mapa das referências

| Assunto | Arquivo |
|---|---|
| Estrutura de pastas e camadas (back e front) | [referencias/estrutura.md](referencias/estrutura.md) |
| Lint, formatação e tipos — cada regra, cada exceção e o porquê; como corrigir | [referencias/lint-e-tipos.md](referencias/lint-e-tipos.md) |
| Pirâmide de testes | [referencias/testes.md](referencias/testes.md) |
| Docker e compose local | [referencias/docker-e-deploy.md](referencias/docker-e-deploy.md) |
| O que muda para subir no Coolify | [referencias/coolify.md](referencias/coolify.md) |
| Makefile e CI | [referencias/makefile-e-ci.md](referencias/makefile-e-ci.md) |
| Config, erros, log, LLM | [referencias/runtime.md](referencias/runtime.md) |
| Documentação do sistema, `CLAUDE.md`, regra de atualização | [referencias/documentacao.md](referencias/documentacao.md) |
| Specs, idioma, commits | [referencias/specs-e-commits.md](referencias/specs-e-commits.md) |
| Lacunas conhecidas (o que o padrão ainda não cobre) | [referencias/lacunas.md](referencias/lacunas.md) |

Arquivos prontos para copiar: `modelos/ferramentas/tamanho_de_funcao.py` (lint de tamanho de
função), `modelos/ferramentas/cobertura_da_documentacao.py` (`make docs`),
`modelos/ferramentas/openapi.py` (gera `openapi.json`; ajuste os imports do app) e
`modelos/CLAUDE.md` (esqueleto do `CLAUDE.md`).

## Como aplicar num projeto

1. **Auditar.** Leia `pyproject.toml`, `Makefile`, `.github/workflows/`, `docker*`,
   `package.json`, `eslint.config.*`, `tsconfig*.json`, a pasta de testes. Monte uma tabela
   *item do padrão → está / falta / diverge*, usando o checklist abaixo.
2. **Mostrar a tabela ao usuário** antes de mexer, com o que vai mudar e o que não se aplica
   (projeto sem front pula a parte web; sem banco pula Postgres/Alembic).
3. **Aplicar por área**, um commit por área (`chore(lint): ...`, `ci: ...`, `test: ...`).
   **Se a correção exigir mexer em muito código** (mais de ~15 arquivos ou ~50 ocorrências
   depois do `--fix`, ou mais de uma área), **trabalhe com multiagente**: o agente principal
   commita a configuração, divide o resto por arquivos disjuntos e lança subagentes em
   worktrees em paralelo, depois integra e roda todas as verificações. Detalhes em
   `lint-e-tipos.md` → "Quando usar multiagente".
4. **Ligar o lint novo sem quebrar tudo de uma vez:** se a regra acusar muita coisa, corrija o
   que for mecânico (`ruff check --fix`, `ruff format`) e liste o restante em
   `per-file-ignores`/`ignorar` **com o motivo em comentário** — nunca ignore sem motivo.
5. **Rodar só o que mexeu** (`make lint tipos`, o teste da área) e commitar; a suíte completa
   fica para o CI.

## Checklist

**Python**
- [ ] `uv` + `pyproject.toml` com `[dependency-groups] dev`, `uv.lock` versionado, Python fixado
- [ ] ruff com o conjunto de regras do padrão, `line-length = 110`
- [ ] `ruff format` (checado no CI com `--check`)
- [ ] mypy `strict = true` + `warn_unreachable`, plugin do pydantic
- [ ] `ferramentas/tamanho_de_funcao.py` com teto de 30 linhas úteis por função e 300 por arquivo
- [ ] monólito modular: `api/nucleo`, `api/infra`, `api/modulos/<dominio>` com interface pública
      no `__init__.py`, eventos entre módulos, modelos por módulo; `import-linter` no `make lint`
- [ ] unidade de trabalho (só a dependência da sessão comita), `obter_do_usuario`, router sem SQL
- [ ] SQL só pelo query builder (sem `text()` nem string SQL; exceções listadas com motivo)
- [ ] raiz do módulo só com arquivos de contrato; regra em subpastas por subdomínio, no máximo 8
      arquivos por pasta
- [ ] login com limite de tentativas (429 + `Retry-After`)
- [ ] comentários: docstring de módulo só com decisão/armadilha; sem separadores nem cabeçalho
      que repete o caminho
- [ ] pytest com `asyncio_mode = "auto"`, `DeprecationWarning` do próprio código vira erro
- [ ] `tests/unidade/`, `tests/integracao/` (marker `integracao`), `tests/dourados/`
- [ ] fixture autouse que isola o ambiente (nenhum teste lê o `.env` da máquina)
- [ ] banco de teste: `DATABASE_URL_TESTE` ou testcontainers, senão `skip` com motivo
- [ ] uma transação por teste com rollback no fim
- [ ] LLM/serviço externo com implementação falsa determinística; a suíte nunca chama o real

**Front**
- [ ] Vite + React + TS `strict`, `noUnusedLocals/Parameters`, `noFallthroughCasesInSwitch`
- [ ] eslint flat config: `js.recommended` + `typescript-eslint` + `react-hooks` com
      `exhaustive-deps: error` + regras `no-restricted-syntax` do projeto
- [ ] `web/src/modulos/<dominio>/` com `index.ts` público; `rotas/` só monta telas
- [ ] `max-lines-per-function` 100 e `max-lines` 300 em `src/`, regras de reuso (cor hex, `toLocaleString`,
      `shadow-card`, `keydown`), cada uma com um único arquivo liberado
- [ ] prettier (`printWidth` 110) + `eslint-config-prettier`; `formato:checar` no CI
- [ ] `<Consulta>`, `<Card>`, `Botao` (`link`/`icone`), `formatacao.ts`, `useAtalhos`,
      `paletas.ts`; tokens com claro/escuro e `@custom-variant dark`
- [ ] tipos da API gerados (`openapi-typescript`), arquivo gerado fora do lint, CI confere diff
- [ ] Vitest + Testing Library (jsdom), `tests/auxiliar/tela.tsx` (`renderizarTela`/`apiFalsa`),
      teste de toda tela com lógica, **cobertura ≥ 60%** no CI
- [ ] Playwright: fluxos de verdade com login (`e2e/fluxos/`), smoke de todas as rotas (lista
      conferida contra o router), 390×844 sem overflow; CI espera `/health` em laço
- [ ] `*.tsbuildinfo` e `coverage/` no `.gitignore` (artefato de build não vai para o git)

**Infra**
- [ ] `docker-compose.yml` local (portas no host) e `docker-compose-coolify.yml` de produção
      com as mudanças de `coolify.md` (`expose`, domínio só no `web`, `restart`, segredos com
      `:?`, `AMBIENTE=producao`, `MIGRAR_AO_SUBIR`, `start_period`)
- [ ] Dockerfile do back com camada de deps separada (`uv sync --no-install-project`)
- [ ] Dockerfile do front multi-stage, servido por Caddy com proxy de `/api` e `/health`
- [ ] healthcheck em todo serviço; `depends_on: condition: service_healthy`
- [ ] entrypoint que migra se `MIGRAR_AO_SUBIR=true`
- [ ] `.env.example` comentado por seção; `.env*` no `.gitignore` e no `.dockerignore`
- [ ] `Makefile` com `help` autodocumentado; CI com jobs `back`, `web`, `e2e`

**Documentação** (`documentacao.md`)
- [ ] `CLAUDE.md` completo (modelo em `modelos/CLAUDE.md`) com a seção "Documentação — leia
      antes, atualize junto"
- [ ] `docs/sistema/README.md` (índice + modelo) e um arquivo por domínio, descrevendo o código atual
- [ ] `ferramentas/cobertura_da_documentacao.py` + `make docs` + passo no CI
- [ ] `README.md`: o que é, onde as coisas estão (árvore), como rodar (bloco de comandos), deploy
- [ ] `specs/NN-nome.md` numeradas; tabela de specs no README
- [ ] `docs/deploy-<paas>.md` passo a passo

## Quando o usuário pedir para mudar o padrão

Mude **nos dois lugares**: no código do projeto onde ele pediu e nesta skill (a referência
certa + o checklist, se for um item novo) — e, no projeto, também o `CLAUDE.md` e o
`docs/sistema/` afetados. Se a mudança não for aplicada no código ainda, anote
em `referencias/lacunas.md`. Mudança grande em vários arquivos: subagentes em worktrees, um
por área, e um commit por área.

**Onde editar e como sincronizar.** A fonte da skill é o clone do repositório em
`~/.claude/skills/padrao-de-projeto/`: edite ali, faça commit e push nesse repositório
(`git -C ~/.claude/skills/padrao-de-projeto ...`). Depois, em cada projeto que guarda uma cópia
(o Crivo, em `.claude/skills/padrao-de-projeto/`), rode `make skill` — copia a versão do clone
para o projeto — e commite junto com a mudança de código. Nunca edite a cópia do projeto
direto: ela é sobrescrita.
