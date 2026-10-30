# Structure: modular monolith

One process, one deploy, one database — but divided into **domain modules with a guaranteed
boundary**. Each module holds its own routes, DTOs, models and logic; a module only talks to
another through its public interface; a side effect in another domain goes through an event.
Without the guarantee (import contracts in CI), in three months it is back to being folders moved
around.

## Root

```
project/
├── api/            FastAPI backend (Python package), see below
├── pipeline/       the project's CLI (typer), `[project.scripts] name = "pipeline.cli:app"`
├── tools/          quality/generation scripts: function_size.py, docs_coverage.py, openapi.py
├── migrations/     Alembic (versions/NNNN_short_name.py, sequential 4-digit numbering)
├── tests/          pytest: unit/, integration/, golden/, fakes at the root (fake_*.py)
├── web/            frontend (Vite) with its own package.json, see below
├── docker/         *.Dockerfile, entrypoint-*.sh
├── specs/          NN-name.md, what was asked, in reading order
├── docs/           system/ (how it works today), glossary.md, deploy-<paas>.md
├── CLAUDE.md, README.md, Makefile
├── docker-compose.yml, docker-compose-<paas>.yml
├── pyproject.toml, uv.lock, alembic.ini
└── .env.example, .gitignore, .dockerignore
```

Large data (corpus, cache, media) stays **out of git and out of the image**: a gitignored
directory at the root, mounted as a volume.

## Backend (`api/`)

```
api/
├── core/           what every module uses and that has no domain
│   ├── config.py   a single Settings(BaseSettings), frozen, read by settings() with lru_cache
│   ├── db.py       engine, session factory, models' Base, unit_of_work, get_owned
│   ├── deps.py     domain-free Annotated aliases: DbSession, pagination (CurrentUser/Admin belong to auth)
│   ├── health.py   /health with register_check(name, fn): each module registers its own part
│   ├── errors.py   AppError + the single problem+json handler
│   ├── events.py   domain event bus (emit / subscribe / results_of)
│   ├── tasks.py    background task Scheduler (runs after the response) and the ApiStarted event
│   ├── clock.py    the user's time (now, today, day_of): one place for tests to swap
│   ├── log.py      structlog
│   ├── models.py   aggregator: imports each module's models.py (for Alembic and the metadata)
│   └── main.py     create_app(): lifespan, middleware, gathers the modules' routers. Nothing else
├── infra/          technical, no business logic (e.g. file reader, index, LLM client, media)
└── modules/
    └── <domain>/
        ├── __init__.py   the PUBLIC INTERFACE: what another module may import (`__all__`)
        ├── routes.py     APIRouter, HTTP only
        ├── schemas.py    pydantic DTOs: XDto (output), XCreate (creation), XUpdate (patch)
        ├── models.py     the domain's SQLAlchemy models
        ├── events.py     the events the module EMITS (dataclasses, exported by the interface)
        ├── subscribers.py the events from other modules it REACTS to
        ├── deps.py       FastAPI dependencies the module offers (e.g. CurrentUser in auth)
        └── <subdomain>/  the business logic, one package per subdomain (e.g. in progress, day/,
                          missions/, achievements/, shop/; in questions, listing/, filter/, practice/)
```

**Module root = contract; logic = subfolders per subdomain.** The root holds only the contract
files above (`routes.py` and `schemas.py` become `routes/`/`schemas/` packages when there are
several). Every folder has at most **8 `.py` files** (excluding `__init__.py`) — past that,
group them. A subfolder's name is the subdomain, never a generic technical layer (`services/`,
`utils/`, `helpers/`). The module's `__init__.py` re-exports what is public: reorganizing the
inside changes no other module, which is why one agent per module can work in parallel.
Guarantee: architecture test (`testing.md`).

Modules have a **layer order** from bottom to top (in Crivo: `corpus`, `rewards` → `auth` →
`notices` → `questions` → `review`, `lessons` → `flashcards`, `mock_exams` → `progress` →
`study` and the read-only ones, `admin` at the top). Lower modules do not import upper ones;
when they need to notify, they emit an event. Three kinds of module show up when untangling
cycles:
- **a data module below everyone** (e.g. `corpus`: the models and catalogs several domains
  read), so common reads do not pull in a whole domain;
- **a DTO-and-enum-only module** (e.g. `rewards`: the `ChangesDto` that progress returns and that
  appears in the emitter's response) — it sits below the emitters and above nothing; no logic;
- **a read-only module at the top** (e.g. `admin`, `stats`): it may read from everyone, nobody
  imports it.

### Boundaries (guaranteed by `import-linter` in `make lint` and in CI)

```toml
[tool.importlinter]
root_packages = ["api"]

[[tool.importlinter.contracts]]
name = "layers: modules -> infra -> core"
type = "layers"
layers = ["api.modules", "api.infra", "api.core"]

[[tool.importlinter.contracts]]
name = "a module only imports another module's public interface"
type = "independence"        # or "forbidden" per pair, with allow_indirect_imports
modules = ["api.modules.questions", "api.modules.flashcards", "..."]
# public interface imports allowed in ignore_imports, with a comment saying why
```

Rules:
1. **Public interface in `__init__.py`.** `from api.modules.notices import notice_scope` is
   fine; `from api.modules.notices.processing import _something` is not. The `__init__`
   re-exports only what other modules need, with `__all__`. Inside the `__init__`, models and
   schemas first and services after (with `I001` turned off only in those files): while a cycle
   exists, that order is what makes the import work. Tests patch the interface's name
   (`monkeypatch.setattr("api.modules.progress.now", ...)`), which is what other modules read.
2. **The logged-in user dependency belongs to the `auth` module** (`api/modules/auth/deps.py`:
   `CurrentUser`, `Admin`...), exported by its interface; core does not know about users. A
   route that needs the user's session (e.g. serving media by token) is domain HTTP and lives in
   a module, not in `infra`. Infra that needs to notify a domain (e.g. "figure unavailable"
   flags the question) emits an event.
3. **Layers:** `modules` imports `infra` and `core`; `infra` imports only `core`; `core` imports
   nothing from inside `api`. `core/main.py` is the natural exception (it gathers the routers)
   and stays out of the layers contract.
4. **No cycles between modules.** If A needs to tell B what happened, A **emits an event** and B
   subscribes — A does not import B. E.g.: questions emits `AnswerRecorded`, flashcards
   `FlashcardReviewed`, mock exams `MockExamFinished`, auth `UserCreated`; review and progress
   subscribe and decide review card, coins, missions and streak. Convention:
   - subscribers run **in the same session** (what they write commits or rolls back together)
     and in the order of `MODULES_WITH_SUBSCRIBERS` (e.g. review before progress), loaded on the
     first `emit` — core does not import modules, and tests/CLI see the same subscribers as the
     API;
   - what subscribers return goes back to the emitter (`events.results_of(results, Type)`): this
     is how the API response keeps bringing "what changed" without the emitter knowing about
     progress;
   - `tests/unit/test_events.py` checks who subscribes to each event;
   - an event is a notice. Using it as a question (e.g. "count this through the in-memory
     index") works, but it is an exception to justify — usually the function changes modules;
   - cross-cutting infrastructure that created cycles (task scheduler, clock, recovery on
     startup) goes to core; each module registers its own recovery by subscribing to
     `ApiStarted`.
5. **Models per module.** Each module has its own `models.py`; `core/models.py` imports all of
   them so Alembic sees the whole metadata. FKs between modules are by table name
   (`ForeignKey("users.id")`), without importing the other module's class; `relationship`
   between modules only with a string and only when necessary.
6. **Exceptions to the boundaries** go in `ignore_imports` with a comment and are logged as a gap
   to resolve — never silent.

### HTTP layer, transaction and ownership

- **The router only does HTTP**: validates input, calls the service, returns a DTO. No
  `select(...)` nor logic in the router.
- **The transaction has a single owner: the request's unit of work.** The session dependency
  opens the transaction, commits at the end if the request succeeded and rolls back on error.
  Service and router **do not** call `commit()`; a service uses `flush()` when it needs the
  generated id. That way two operations from different services compose a single transaction.
  A background task and a CLI command open their own unit of work
  (`async with unit_of_work() as session:`).
- **"The user's record or 404" is a helper**:
  `await get_owned(session, Notice, id, user, what="Edital")` — fetches, checks ownership
  (`user_id`), and raises `not_found` identically for "does not exist" and "belongs to another
  user" (it does not leak that the id exists). `what` is product text (it ends up in the
  `detail`). Never `session.get` + `if x.user_id != user.id` by hand.
- A service does not know `Request`/`Response`.

### Size

Function up to 30 useful lines, **file up to 300 lines** (`tools/function_size.py` measures
both). A file that goes over is split by responsibility inside the module (`service.py` becomes
`service/create.py`, `service/answer.py`...), not by line count.

A data file read by both sides (e.g. `sanitize.json`) lives in the backend and the frontend
imports it by relative path — a single source.

## Frontend (`web/`)

The same idea: modules by domain, and routes only assemble screens.

```
web/src/
├── main.tsx, router.tsx, styles.css
├── api/            client.ts (single fetch, readProblem), types.ts (generated), models.ts (aliases)
├── routes/         one file per TanStack Router route: reads params (Route.useParams), assembles the
│                   screen with the module's components. Thin.
├── modules/
│   └── <domain>/
│       ├── components/   the domain's components
│       ├── hooks.ts      the domain's TanStack Query hooks (keys, queries, mutations)
│       ├── lib.ts        the domain's pure functions
│       └── index.ts      the module's public interface
├── components/     only what several modules share
│   └── ui/         primitives: Card, Button, Modal, Drawer, Input, Tabs, SidePanel, TreeNode...
└── lib/            cross-cutting: formatting.ts (the only place that formats numbers/dates),
                    shortcuts.ts (the only one that listens to the keyboard), palettes.ts (the only
                    one with fixed content colors), storage, theme, url-filter
```

| File | Role |
|---|---|
| `src/router.tsx` | the route list and `createAppRouter(queryClient, history?)`: 404 at the root, `defaultErrorComponent` and `defaultPendingComponent` (see `lint-and-types.md`, "The router's error and loading screens") |
| `src/api/client.ts` | single `fetch`, single `readProblem()` for errors, `BASE = "/api/v1"` |
| `src/api/types.ts` | **generated** from `openapi.json` (do not edit, out of lint) |
| `src/styles.css` | color tokens with light and dark values (`:root[data-theme=...]`) + `@theme inline`; `@custom-variant dark` so `dark:` follows the app's theme, not the system's |
| `tests/` | Vitest (`*.test.ts(x)`), `setup.ts`, `helpers/` (`screen.tsx` with `renderScreen`/`fakeApi`, `data*.ts`) |
| `e2e/` | Playwright (`routes.spec.ts`, `mobile.spec.ts`, `flows/*.spec.ts`, `helpers.ts`) |
| `Caddyfile` | serves the build and proxies `/api/*` and `/health` |

Frontend boundary: a module imports another only through its `index.ts` (rule
`no-restricted-imports` with the pattern `**/modules/*/!(index)`), and `components/`/`lib/` do
not import `modules/`.

Stack: React 19, Vite 6, TypeScript 5 strict, Tailwind v4 (`@tailwindcss/vite`), TanStack
Router + Query, Radix for dialog/tabs. Dev server with a proxy for `/api` and `/health` to
`API_URL` (default `http://localhost:8000`) — same domain in dev and production, no CORS.

## Moving a layered project (`routers/`, `schemas/`, `services/`) to modules

1. **Measure the coupling** first: who imports whom across domains
   (`grep -rn "from api.services.X" api | grep -v "api/services/X"`). The number says how much
   will become events or public interface.
2. **Moving is a single mechanical step by a single agent** (backend and frontend can be two
   agents in parallel, since they do not touch each other): `git mv` to the new structure,
   imports rewritten, tests green, no behavior change. Moving in parallel with other changes is
   a guaranteed conflict; nothing else runs meanwhile.
3. **Turn on the import-linter contracts** with the current violations in `ignore_imports`
   (commented, like eslint's `PENDING` list).
4. **Common base, by the main agent**: unit of work, `get_owned`, event bus, 300-line file cap,
   architecture test and the import-linter contracts (still outside `make lint`, in a separate
   boundaries target). All with temporary lists and a "strict" environment variable to check
   the target.
5. **Public interfaces and layers: a single agent.** It looks parallelizable per module, but it
   is not: while there are cycles between modules, re-exporting names in the `__init__.py`
   files breaks at import time depending on the order modules load, and that only shows up with
   everything together. Beforehand, the main agent measures who imports what from whom and
   writes a **names contract** (what each `__init__` exports, private `_x` renamed, collisions
   resolved) — without it two sides pick different names.
6. **Then, in parallel, one agent per module** (disjoint files): remove `commit()`, use
   `get_owned`, split files above 300 lines, clean up comments, the domain's fixes.
7. **Last, a single agent for the cycles**: direct calls between modules become events; the
   no-cycles contract passes and the contracts enter `make lint`.
8. `docs/system/` with the new paths at each step (`make docs` flags every path that vanished).

On the frontend, the move was a single agent and brought along: a `shell` module (navigation,
toasts, 404, which depend on auth and progress and therefore cannot live in `components/`); the
part of `lib/toasts` that knows about progress moved to the progress module; and the boundary
rule for relative paths (`../other-module/...`) is a regex built from the list of folders in
`modules/`, because the pattern `**/modules/**` does not catch relative imports.
