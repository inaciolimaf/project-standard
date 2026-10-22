# Settings, errors, logging, LLM

## Settings (`api/core/config.py`)

- A single `Settings(BaseSettings)` with `env_file=".env"`, `extra="ignore"`, `frozen=True`.
  Access only through `settings()` (`@lru_cache`), cleared in tests.
- `environment: Literal["local", "production", "test"]` (in Crivo the variable is `AMBIENTE`
  with the values `local`, `producao`, `teste`).
- Secrets are `SecretStr` **with no default**. Model validator: in production, refuses a secret
  that is missing, shorter than 32 bytes, equal to a value in `EXAMPLE_VALUES` (the ones in
  `.env.example`) or two equal secrets — raises `SettingsError` before opening a port.
- Numbers with `Field(ge=...)`; paths as `Path` relative to `REPO_ROOT`.
- A `#:` comment above each non-obvious field (what it is, what happens if empty).
- Guarantee: a `Settings` test with production on and each secret missing/short/example.

### Environment variables are a contract with the server

**An environment variable configured by hand on the server is never renamed or removed.** The
server keeps the old name; a renamed variable makes the next deploy read nothing — with a
default, the system starts wrong without a single error; without one, it does not start and
nobody knows why.

- The **field** follows the code's language; the **variable** keeps its name, read by alias:

  ```python
  jwt_secret: SecretStr = Field(validation_alias="SEGREDO_JWT")
  migrate_on_start: bool = Field(default=False, validation_alias="MIGRAR_AO_SUBIR")
  ```

  (`AliasChoices("OLD", "NEW")` when a rename was agreed and both must work during the change.)
- A **new** variable enters with a safe default (the system keeps working as before without it)
  or, if it has none (a new secret), with an explicit notice to the server owner in the same
  delivery: the list of what to configure — name, value or how to generate it
  (`openssl rand -hex 32`), which service — and the docs' deploy page updated.
- Removing a variable the code no longer reads is harmless for the deploy, but it is the owner's
  call: say so, do not delete it from the server's panel yourself.
- A new project names its variables in English from the start (`ENVIRONMENT`,
  `MIGRATE_ON_START`); the rule protects what already exists.
- Test isolation lists every variable `Settings` reads (by their real names, aliases included).

## Unit of work and ownership (`api/core/db.py`)

- The session dependency (`DbSession`) is the **unit of work**: opens the transaction, commits
  at the end of the request if it succeeded, rolls back on error. Router and service do not call
  `commit()` (a service uses `flush()` when it needs the id). Background tasks and the CLI use
  `async with unit_of_work() as session:`.
- **FastAPI pitfall**: with the default scope, the code after a dependency's `yield` runs
  **after** the response has left — a commit that fails there reaches the client as 200 and
  nothing was saved. Use `DbSession = Annotated[AsyncSession, Depends(session, scope="function")]`
  (FastAPI ≥ 0.121): the dependency closes before the response and the failure becomes a 500.
- The session depends on a separate `factory()` (`Depends(factory)`): the test swaps only the
  factory for its own transaction's (`app.dependency_overrides[factory] = lambda: test_factory`)
  and the unit of work's commit/rollback logic stays the real one.
- **A write that must survive its own request's error** (recording the failed login attempt,
  counting a figure's failure): the route **returns** `error_response(request, error)` (the same
  `problem+json` as the single handler) instead of raising, and the unit of work commits
  normally. Raising would undo the write.
- **A background task that writes in stages** (and the cost of a model call that must stay even
  if the stage fails): receives the session **factory** as a parameter, does not call a fixed
  `unit_of_work()`. In production it is the real factory; in tests it is the test transaction's,
  where each session becomes its own savepoint — the cost's commit stays, the stage's rollback
  undoes only the stage. A fixed `unit_of_work()` opens another connection, which in a test sees
  nothing.
- `get_owned(session, Model, id, user, what=...)`: fetch + ownership check + the same 404 for
  nonexistent and another user's. It is the only way to load a user's record by id.
- Unit of work tests: a request that raises after writing leaves nothing in the database; a
  fake factory whose `commit()` raises proves the response is 500, not 200 (and the test fails if
  someone removes `scope="function"`).
- Guarantee of the rule: `tests/unit/test_architecture.py` walks the `ast` of `api/` and fails if
  `commit()` appears outside `core/db.py` (with a temporary list while the migration is ongoing).

## SQL: only through the query builder

- Every query is built with SQLAlchemy (ORM or Core): `select`, `insert`, `update`, `delete`,
  `func`, `literal_column`, `aliased`, `.cte(recursive=True)`, `insert(...).from_select(...)`,
  `postgresql.insert(...).on_conflict_do_update(...)`, trigram with `func.similarity`/`.op("%")`,
  `select(func.set_config(...))`. It also applies outside the session: with raw `asyncpg` (bulk
  load, in-memory index) the builder is compiled to the dialect and executed on the same
  connection; on a data file's SQLite, Core with a synchronous engine.
- Forbidden: `text("...")` and strings that start with `SELECT/INSERT/UPDATE/DELETE/WITH/...`.
  Exceptions only where the builder cannot reach — `EXPLAIN` around a query already built by the
  builder, bulk `COPY` (`copy_records_to_table`) — and each one is listed, with the reason, in
  the architecture test's `ALLOWED_SQL`. DDL belongs to migrations (`op.*`).
- Hot path (millions of rows, one query per opened question): compile the builder once and reuse
  the generated SQL; measure before and after. The SQL still comes from the builder.
- Values always by parameter; the builder already guarantees it.

## Login

- **Attempt limit**: per e-mail and per IP, with a window (e.g. 5 failures in 15 min → `429`
  with `problem+json`, `Retry-After` and a `detail` saying when to try again). Success resets
  the e-mail's counter. The counter lives in the database (or a shared cache), not in process
  memory, so it holds with more than one worker.
- The same message for a nonexistent e-mail and a wrong password (it does not reveal who has an
  account).
- Test: the sixth wrong attempt gets 429 even with the right password; after the window, it gets
  in.

## Sessions and logout

A JWT is valid until it expires: deleting the cookie only forgets it in that browser, and a copy
(stolen, or left in another tab) keeps working. So ending a session is a server decision:

- **Session version** on the user (`session_version`, claim `sv`): changing the password or
  deactivating the account bumps it, and every token of the account dies, refresh included. The
  password-change route reissues the pair so whoever changed it stays signed in.
- **Session id** (claim `sid`): a new UUID on login, the same for the access/refresh pair and kept
  across refreshes. Logout writes the `sid` in a `revoked_sessions` table with `expires_at` = now +
  refresh lifetime (after that the token dies on its own; the expired rows are deleted on each
  logout). Only that device leaves; the others stay in.
- **One check** (`is_alive(session, user, claims)`): exists, active, same version, `sid` not
  revoked. The current-user dependency and the refresh route use the same function; it costs one
  primary-key lookup per request, next to the user's.
- Logout reads the refresh cookie first (the access may have expired while the refresh would bring
  it back) and answers 204 even without a valid token. A token from before `sid` existed cannot
  be revoked alone: its logout bumps the version (every device, once).
- Do not bump the version on logout to save the table: it signs out every device of the account,
  and the e2e that clicks "log out" signs out the other tests that use the same account.
- Tests: a copy of the tokens taken before logout gets 401 (access and refresh), a second client
  of the same account stays in, logout after a refresh still revokes.

## Errors (`api/core/errors.py`)

- A single format: `application/problem+json` (RFC 9457: `type`, `title`, `status`, `detail`).
- `AppError(status_code, title, detail, type, extras)` refuses an empty `detail`
  (`ValueError`) — every 409/422 explains to the user what to do. `title` and `detail` are
  product text (in the product's language); `type` is code (English).
- `type` as a `domain/reason` slug (e.g. `notice/no-model`).
- One handler registers everything: `AppError`, `HTTPException`, `RequestValidationError`.
- Frontend: a single `readProblem()` in `client.ts`, `ApiError` with `title`/`detail`.

## Logging (`api/core/log.py`)

- structlog: `JSONRenderer` in production, `ConsoleRenderer` elsewhere, ISO timestamp.
- A middleware generates/propagates `x-request-id` and binds `request_id`, `route`, `method` to
  the context.
- Events named `domain.action` (`api.starting`, `notices.recovery_failed`) with named fields;
  error text truncated (`str(error)[:300]`).

## App (`api/core/main.py`)

- `create_app()` is a factory (tests and `openapi.py` use it).
- Domain routes under `/api/v1`, `/health` at the root; docs at `/api/docs`.
- Background loops in the lifespan only outside the test environment; a task left halfway when
  the process died is recovered on startup (it becomes an error state, it does not stay
  "running" forever).

## LLM / paid external service

- An `LLMClient` interface in `api/infra/llm/base.py`; a real implementation and a deterministic
  `fake.py`.
- Without a configured key, the routes that depend on it answer `503` with `problem+json`; the
  rest works.
- Structured output validated by a pydantic contract (`contracts.py`); prompts in `prompts.py`
  (in the language of the documents they talk about).
- The cost of each call recorded in the database; a daily cap (in Crivo
  `LIMITE_CUSTO_DIARIO_USD`, zero turns it off) cuts before calling.
- Model per variable (in Crivo `MODELO_<DOMINIO>`), empty falls back to the code's default.
- Nothing that spends money starts on its own: each stage is born from a user action.
