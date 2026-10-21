---
name: project-standard
description: Inácio's engineering standard for Python (FastAPI + uv) projects with a React (Vite + TS) frontend — folder structure (modular monolith), test pyramid, lint (ruff, strict mypy, 30-line function cap, eslint, tsc), Docker/compose, Coolify, Makefile, CI, system documentation (docs/system + CLAUDE.md, updated with every change), specs with rule+guarantee, commits, and the language rule (code in English, product in its user's language, glossary between the two). Use when creating a new project, when auditing or aligning an existing project to this standard ("apply the standard", "aplica o padrão", "aplica o padrão de projeto", "deixa igual ao crivo"), or when the user asks to change the standard itself.
---

# Project standard

Extracted from Crivo (the author's exam-question system, the living reference). This skill lives
in the repository `github.com/inaciolimaf/project-standard`; Crivo keeps a synced copy in
`.claude/skills/project-standard/`. When a detail is missing here and you are in Crivo, its
corresponding file is the source.

Code examples use Crivo's English names (from its `docs/glossary.md`). Crivo's Makefile targets
(`make teste`, `make tipos`...), CLI commands and environment variables (`SEGREDO_JWT`,
`AMBIENTE`...) are in Portuguese on purpose — see the operations rule below.

## Principles (they apply to everything below)

1. **A rule without a guarantee does not exist.** Every project rule has a test, a lint or a
   design constraint that prevents it from happening again. If it cannot be guaranteed, it does
   not become a rule.
2. **A contract between two parts has a single source of truth.** Backend × frontend: frontend
   types generated from the backend's OpenAPI. Backend × pipeline: a test that exercises both
   with the same data.
3. **Content transformation never loses information silently.** Golden tests with real cases
   + a count of problems that must be zero.
4. **No secret has a default value.** In production the process refuses to start with a secret
   that is missing, short (< 32 bytes) or equal to the one in `.env.example`.
5. **One command per task.** Everything that is run lives in the `Makefile`; `make` with no
   target lists it.
6. **CI = what the Makefile runs**, with no step that exists only in CI.
7. **The system changed, the documentation changes, in the same commit.** `docs/system/`
   explains the system as it is, `CLAUDE.md` explains how to work on it, and both are kept tidy
   on every pass. Guarantee: `make docs`. See `references/documentation.md`.
8. **Code is in English; the product speaks its user's language.** Identifiers, files, tables,
   API, comments, docs and commits in English; only what a person reads in the product stays in
   the product's language. Every domain name comes from the project's glossary
   (`docs/glossary.md`). See `references/specs-and-commits.md` → "Language".

## Operations rule: never rename what someone configured or types by hand

> **An environment variable configured by hand on the server is never renamed or removed.**
> Renaming it breaks the next deploy silently: the server still has the old name, the code reads
> the new one and gets nothing (or a default).

- In code, the settings field may have another (English) name and read the existing variable by
  alias: `jwt_secret: SecretStr = Field(validation_alias="SEGREDO_JWT")`.
- A **new** variable only comes in with a safe default, or with an explicit notice to the server
  owner listing exactly what to configure (name, value or how to generate it, which service).
- The same goes for **commands and targets people type** (CLI commands, Makefile targets, npm
  scripts): change them only by agreement with the people who use them.

Details in `references/runtime.md`, `references/docker-and-deploy.md` and
`references/coolify.md`.

## Reference map

| Subject | File |
|---|---|
| Folder structure and layers (backend and frontend) | [references/structure.md](references/structure.md) |
| Lint, formatting and types — each rule, each exception and why; how to fix | [references/lint-and-types.md](references/lint-and-types.md) |
| Test pyramid | [references/testing.md](references/testing.md) |
| Docker and local compose | [references/docker-and-deploy.md](references/docker-and-deploy.md) |
| What changes to deploy on Coolify | [references/coolify.md](references/coolify.md) |
| Makefile and CI | [references/makefile-and-ci.md](references/makefile-and-ci.md) |
| Settings, errors, logging, LLM | [references/runtime.md](references/runtime.md) |
| System documentation, `CLAUDE.md`, update rule | [references/documentation.md](references/documentation.md) |
| Specs, language, glossary, commits | [references/specs-and-commits.md](references/specs-and-commits.md) |
| Known gaps (what the standard does not cover yet) | [references/gaps.md](references/gaps.md) |

Files ready to copy: `templates/tools/function_size.py` (function and file size lint),
`templates/tools/docs_coverage.py` (`make docs`), `templates/tools/openapi.py` (writes
`openapi.json`; adjust the app import) and `templates/CLAUDE.md` (skeleton of `CLAUDE.md`).

## How to apply it to a project

1. **Audit.** Read `pyproject.toml`, `Makefile`, `.github/workflows/`, `docker*`,
   `package.json`, `eslint.config.*`, `tsconfig*.json`, the tests folder. Build a table
   *standard item → present / missing / diverges*, using the checklist below. **The audit also
   checks the language of the code**: identifiers, file and folder names, database tables and
   columns, API routes and fields, comments, docs. If they are in another language, the
   conversion to English goes into the plan (step 6).
2. **Show the table to the user** before changing anything, with what will change and what does
   not apply (a project without frontend skips the web part; without a database skips
   Postgres/Alembic).
3. **Apply by area**, one commit per area (`chore(lint): ...`, `ci: ...`, `test: ...`).
   **If the fix requires touching a lot of code** (more than ~15 files or ~50 occurrences after
   `--fix`, or more than one area), **work with multiple agents**: the main agent commits the
   configuration, splits the rest by disjoint files and launches subagents in worktrees in
   parallel, then integrates and runs every check. Details in `lint-and-types.md` → "When to use
   multiple agents".
4. **Turn on a new lint without breaking everything at once:** if the rule flags a lot, fix what
   is mechanical (`ruff check --fix`, `ruff format`) and list the rest in
   `per-file-ignores`/`ignore` **with the reason in a comment** — never ignore without a reason.
5. **Run only what you touched** (`make lint`, the types check, the area's tests) and commit;
   the full suite is for CI.
6. **Converting the code to English**, in this order (details in `specs-and-commits.md` →
   "Migrating an existing project"):
   1. **glossary first** (`docs/glossary.md`), reviewed by the user;
   2. **structure and contract by a single agent**: folders, public interfaces, models + a
      renaming migration that preserves data, API routes and fields;
   3. **frontend afterwards**, from the new OpenAPI (regenerated types show every place to fix);
   4. **internal names, comments and tests in parallel**, one subagent per module (disjoint
      files);
   5. **docs last** (`docs/system/`, `CLAUDE.md`, README, specs' references to code).

   Never touched: environment variables on the server, CLI commands, Makefile targets (and
   anything else people type or outside systems consume), screen URLs, past commits.

## Checklist

**Language**
- [ ] code, database, API, comments, docs and new commits in English; only product text in the
      product's language
- [ ] `docs/glossary.md` maps domain terms to code names
- [ ] server environment variables, CLI commands and Makefile targets kept as they were (aliases
      in the settings when the field name changes)

**Python**
- [ ] `uv` + `pyproject.toml` with `[dependency-groups] dev`, `uv.lock` versioned, Python pinned
- [ ] ruff with the standard's rule set, `line-length = 110`
- [ ] `ruff format` (checked in CI with `--check`)
- [ ] mypy `strict = true` + `warn_unreachable`, pydantic plugin
- [ ] `tools/function_size.py` with a cap of 30 useful lines per function and 300 per file
- [ ] modular monolith: `api/core`, `api/infra`, `api/modules/<domain>` with a public interface
      in `__init__.py`, events between modules, models per module; `import-linter` in `make lint`
- [ ] unit of work (only the session dependency commits), `get_owned`, router without SQL
- [ ] SQL only through the query builder (no `text()` nor SQL strings; exceptions listed with a
      reason)
- [ ] module root holds only contract files; logic in subfolders per subdomain, at most 8 files
      per folder
- [ ] login with an attempt limit (429 + `Retry-After`)
- [ ] comments: module docstring only with a decision/pitfall; no separators nor a header that
      repeats the path
- [ ] pytest with `asyncio_mode = "auto"`, the project's own `DeprecationWarning` becomes an error
- [ ] `tests/unit/`, `tests/integration/` (marker `integration`), `tests/golden/`
- [ ] autouse fixture that isolates the environment (no test reads the machine's `.env`)
- [ ] test database: a test database URL variable or testcontainers, otherwise `skip` with a
      reason
- [ ] one transaction per test with rollback at the end
- [ ] LLM/external service with a deterministic fake implementation; the suite never calls the
      real one

**Frontend**
- [ ] Vite + React + TS `strict`, `noUnusedLocals/Parameters`, `noFallthroughCasesInSwitch`
- [ ] eslint flat config: `js.recommended` + `typescript-eslint` + `react-hooks` with
      `exhaustive-deps: error` + the project's `no-restricted-syntax` rules
- [ ] `web/src/modules/<domain>/` with a public `index.ts`; `routes/` only assembles screens
- [ ] `max-lines-per-function` 100 and `max-lines` 300 in `src/`, reuse rules (hex color,
      `toLocaleString`, `shadow-card`, `keydown`), each with a single allowed file
- [ ] prettier (`printWidth` 110) + `eslint-config-prettier`; format check in CI
- [ ] `<QueryView>`, `<Card>`, `Button` (`link`/`icon`), `formatting.ts`, `useShortcuts`,
      `palettes.ts`; tokens with light/dark and `@custom-variant dark`
- [ ] API types generated (`openapi-typescript`), generated file out of lint, CI checks the diff
- [ ] Vitest + Testing Library (jsdom), `tests/helpers/screen.tsx` (`renderScreen`/`fakeApi`),
      a test for every screen with logic, **coverage ≥ 60%** in CI
- [ ] Playwright: real flows with login (`e2e/flows/`), smoke of every route (list checked
      against the router), 390×844 without overflow; CI waits for `/health` in a loop
- [ ] `*.tsbuildinfo` and `coverage/` in `.gitignore` (build artifacts do not go into git)

**Infra**
- [ ] local `docker-compose.yml` (ports on the host) and production `docker-compose-coolify.yml`
      with the changes in `coolify.md` (`expose`, domain only on `web`, `restart`, secrets with
      `:?`, production environment fixed, migrate on start, `start_period`)
- [ ] backend Dockerfile with a separate dependency layer (`uv sync --no-install-project`)
- [ ] multi-stage frontend Dockerfile, served by Caddy with a proxy for `/api` and `/health`
- [ ] healthcheck on every service; `depends_on: condition: service_healthy`
- [ ] entrypoint that migrates when the migrate-on-start variable is `true`
- [ ] `.env.example` commented by section; `.env*` in `.gitignore` and `.dockerignore`
- [ ] `Makefile` with a self-documenting `help`; CI with jobs `back`, `web`, `e2e`

**Documentation** (`documentation.md`)
- [ ] complete `CLAUDE.md` (template in `templates/CLAUDE.md`) with the sections "Documentation —
      read first, update together" and "Language"
- [ ] `docs/system/README.md` (index + template) and one file per domain, describing the current
      code
- [ ] `tools/docs_coverage.py` + `make docs` + a CI step
- [ ] `README.md`: what it is, where things are (tree), how to run (command block), deploy
- [ ] numbered `specs/NN-name.md`; specs table in the README
- [ ] step-by-step `docs/deploy-<paas>.md`

## When the user asks to change the standard

Change it **in both places**: in the project's code where they asked and in this skill (the right
reference + the checklist, if it is a new item) — and, in the project, also the `CLAUDE.md` and
the affected `docs/system/` files. If the change is not applied in code yet, note it in
`references/gaps.md`. A large change across many files: subagents in worktrees, one per area,
and one commit per area.

**Where to edit and how to sync.** The skill's source is the repository clone in
`~/.claude/skills/project-standard/`: edit there, commit and push in that repository
(`git -C ~/.claude/skills/project-standard ...`). Then, in each project that keeps a copy (Crivo,
in `.claude/skills/project-standard/`), run `make skill` — it copies the clone's version into the
project — and commit it together with the code change. Never edit the project's copy directly:
it gets overwritten.
