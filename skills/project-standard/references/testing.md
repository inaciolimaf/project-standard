# Test pyramid

Crivo's numbers (Oct/2026) to calibrate the proportion: ~200 unit, ~170 integration, Vitest with
60% coverage and whole screens tested, Playwright with real flows and a smoke of every route.

```
          ┌──────────────┐  e2e (Playwright, production build, real API)
          │ flows, routes │  — flows clicking (login, answer, mock exam, flashcard);
          │ mobile        │    smoke of ALL routes; 390×844 without overflow
        ┌─┴──────────────┴─┐  frontend (Vitest + Testing Library, jsdom) — coverage ≥ 60%
        │ screens, components│ — whole screens with the real router and a fake API, pure lib/,
        │ lib, client        │   error contract
      ┌─┴────────────────────┴┐  integration (pytest + real Postgres)
      │ HTTP routes, ingestion, │ — httpx ASGITransport, transaction with rollback
      │ migrations              │
    ┌─┴─────────────────────────┴┐  unit (pytest, no I/O)
    │ pure rules, parsers,         │ — fast, the majority
    │ contracts, golden            │
    └──────────────────────────────┘
```

## Backend coverage

`pytest-cov` measuring the application packages (`[tool.coverage.run] source = ["api", "pipeline"]`)
and a floor in `pyproject.toml`:

```toml
[tool.coverage.report]
# Floor, not target: below what the suite already covers, so it only fails when a change arrives
# without tests. Raise it when the real number rises.
fail_under = 80
skip_covered = true
show_missing = true
```

`fail_under` only acts when the run has `--cov`: CI runs `pytest -q --cov`, and the Makefile has a
coverage target that does the same. The plain test target stays without it (faster while
iterating). The floor is the measured number minus a margin (Crivo: 85% measured, 80% floor), never
a wish: a floor above reality makes the CI red on the day it is turned on.

## Unit — `tests/unit/test_<subject>.py`

- No database, no network, no disk outside `tmp_path`.
- Pure domain functions, parsers, sanitizing, scheduling, cost calculation, settings.
- An external service comes in through its fake implementation (`api/infra/llm/fake.py`: a
  script in order, an answer per stage, or a function of the request; with no match it returns
  something that breaks the contract, so the test fails loudly).

## Integration — `tests/integration/test_<domain>.py`

- Marker `integration`. Postgres from the test database URL variable (in Crivo
  `DATABASE_URL_TESTE`: the compose one, database `<app>_teste`, created by `make db-teste`) or,
  without it, `testcontainers`; with neither, `pytest.skip` with a reason — it never fails for
  lack of infrastructure.
- `migrated_schema` (session scope): `alembic upgrade head` once, `downgrade base` at the end —
  **migrations are tested in both directions** on every run.
- `db_context`: one transaction per test, `join_transaction_mode="create_savepoint"`, rollback
  at the end. The code may `commit` freely.
- `client`: `create_app()` with the session's `dependency_overrides` + `httpx.AsyncClient(
  transport=ASGITransport(app))`. Ready fixtures: `admin`, `student`, `admin_client`,
  `student_client`, and an ingested fake data set (`tests/fake_corpus.py`).
- Tests HTTP routes end to end: status, body, `problem+json` with a non-empty `detail`.

## Golden — `tests/golden/`

Real cases (files from the world: a notice, a corpus question, a caption) and real model answers
recorded by a CLI command (in Crivo `crivo <dominio> gravar-dourado`, it costs cents). The test
checks that the code and the contract accept the real case. A test that depends on a missing
golden file uses `skipif` with the command that generates it in the reason.

## Isolation (autouse fixture in `tests/conftest.py`)

- Removes from the environment every variable `Settings` reads (an explicit list, with the
  variables' real names).
- Test environment, `DATABASE_URL` unreachable (port 1) by default — a test that did not ask for
  a database does not find one by accident.
- Test secrets with 32+ bytes; `env_file=None` (the machine's `.env` never gets in).
- Clears every `lru_cache` singleton before and after.
- In the test environment the lifespan does not start background loops.

## pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
filterwarnings = ["error::DeprecationWarning:api.*", "error::DeprecationWarning:pipeline.*"]
markers = ["integration: needs Postgres (test database URL or testcontainers)"]
```

## Frontend — Vitest

- `web/tests/*.test.ts(x)`, `environment: "jsdom"`, `globals: false`, `css: false`,
  `setup.ts` with `jest-dom/vitest` and `cleanup()` in `afterEach`.
- **Minimum coverage of 60%** (lines, statements, functions and branches),
  `@vitest/coverage-v8` in `vite.config.ts`, a coverage npm script and Makefile target, in CI.
  Only what is generated (`src/api/types.ts`) and `main.tsx` stay out. Lower than the backend
  because screens have a lot of JSX without logic; higher than zero because seven out of ten
  frontend bugs that motivated the standard had no test.
- Three kinds of test, from cheapest to most expensive:
  1. **Pure `lib/`** (formatting, URL filter, storage, shortcuts, theme): all of it, with the
     edge cases. These are the cheapest tests there are.
  2. **Isolated component**: `render(<X .../>)` + `userEvent`; for a component that uses
     `Link`/`useNavigate`, `vi.mock("@tanstack/react-router")`.
  3. **Whole screen**: `tests/helpers/screen.tsx` with the real router (built by the app's own
     `createAppRouter(queryClient, history)`, so the tests run the production defaults: error and
     loading screens, 404), memory history and the fake API:
     ```ts
     const api = fakeApi({ "GET /questions": { items: [], total: 0 } });   // METHOD /path without /api/v1
     const { user } = await renderScreen("/marcadas");                      // the screen URL stays in Portuguese
     expect(api.calls("GET /questions")[0]?.query.get("bookmarked")).toBe("true");
     ```
     `fakeApi` swaps `fetch`, already answers what the shell asks for (logged-in user,
     balance...) and returns a 404 in `problem+json` with the path in the `detail` for an
     undeclared route — the test fails saying what was missing. `renderScreen` fills in what
     jsdom lacks (`matchMedia`, `scrollTo`). Common fake data in `tests/helpers/data.ts`; an
     area's in `tests/helpers/data-<area>.ts`. `vi.unstubAllGlobals()` in `afterEach`.
- Animation and time (`requestAnimationFrame`, debounce, timer) with a fake clock
  (`vi.useFakeTimers({ toFake: ["requestAnimationFrame", "cancelAnimationFrame", "performance"] })`
  + `vi.advanceTimersByTime`), never `waitFor` waiting for real time: with a loaded machine (CI,
  agents in parallel) the test fails without a bug.
- The screen tests' wait time lives in one place: `configure({ asyncUtilTimeout: 4000 })` in
  `setup.ts` and `testTimeout` in `vite.config.ts` — not in each file.
- **Every screen with logic has a screen test**: timer (`vi.useFakeTimers`), autosave,
  confirmation, keyboard shortcuts, a form with an API error. Test what the user sees and does,
  not implementation details.
- Also mandatory: `client.ts` (a fake 409 becomes an exception with `title`/`detail` and the
  screen shows the `detail`; refresh on 401), filter components, HTML rendering.
- **A frontend fix without a test that reproduces it is not accepted.** A new screen is born with
  a test.

## E2E — Playwright

- Runs on the **production build** (`vite preview` on 4173) against the real API (`API_URL`),
  logging in through the API with credentials from variables (in Crivo `E2E_EMAIL`/`E2E_SENHA`).
  System Chrome (`channel: "chrome"`).
- Project `routes`: opens each route (list in `e2e/helpers.ts`) with fake ids; fails on a
  `pageerror` with "Invariant" or on the generic error screen; `#root` not empty.
- Project `mobile`: the same routes at 390×844 with touch, a capture in `captures/<route>.png`,
  fails if `scrollWidth > innerWidth`. In CI the captures become an artifact.
- **The route list cannot fall behind**: a test compares the router's routes with the e2e list
  and fails saying which one is missing (or the list is generated from the router). A list kept
  only by hand was missing the newest screens.
- Project `flows`: **real flows, clicking like the user**, one file per flow in `e2e/flows/`. The
  minimum: login through the form (and a wrong password shows the API's message) and logout; the
  main path of each area (in Crivo: open and answer a question, practice, a mock exam from start
  to result, review a flashcard with the keyboard). Independent of exact data: they take the
  first available item, create through the API what they need and delete it at the end. They run
  against the local API and, in CI, against fake data.
- **A new feature enters the e2e in the same commit**: the route in the list (the test above
  enforces it) and, if it has a new main flow, a file in `e2e/flows/`.
- In CI, the API is awaited with a `curl` loop on `/health` with a timeout (never `sleep N`),
  printing the API log if it does not come up.

(Crivo keeps its Playwright project names and the Makefile targets that call them — `make e2e`,
`make celular`, `make e2e-fluxos` — because people type them.)

## Architecture test

`tests/unit/test_architecture.py` guards the design rules no third-party lint covers, reading the
code's `ast`: "only the unit of work calls `commit()`", "SQL only through the query builder"
(flags `sqlalchemy.text` and strings that start with an SQL keyword, docstrings excluded;
exceptions in `ALLOWED_SQL` with a reason) and "a module folder has at most 8 files". A new rule
of this kind goes here, with a temporary list and `ARCHITECTURE_STRICT=1` to check the target.

## Day to day

Run the tests of the area you touched, not the whole suite; CI runs everything. If CI breaks, fix
it right after.
