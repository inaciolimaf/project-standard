# Backend (pytest)

## Cheap password hashing in tests

The hash is meant to be slow. In a suite where most integration tests create a user or log in, it
becomes most of the time.

The production cost is a named module constant (or a setting), so a fixture can replace it:

```python
# api/modules/auth/credentials/passwords.py
#: The stored hash carries its own cost, so raising this only reaches a password when it is next set.
BCRYPT_COST = 12


def password_hash_of(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(BCRYPT_COST)).decode("ascii")
```

```python
# tests/conftest.py, inside the autouse isolation fixture
# Three hashes per test at the production cost were the bulk of the suite's time.
monkeypatch.setattr(passwords, "BCRYPT_COST", 4)
```

With argon2 read from settings, the isolation fixture sets the minimum instead (Inkstave):
`ARGON2_TIME_COST=1`, `ARGON2_MEMORY_COST=8`, `ARGON2_PARALLELISM=1`. The verification of an
existing hash still works, since the hash carries its parameters.

Keep one test that checks the production default is the strong one, so a test value never leaks
into production.

## pytest-xdist with one database per worker

`uv add --dev pytest-xdist`. Each worker needs its own database: the integration fixtures migrate the
schema, downgrade it at the end and truncate tables, so two workers on one database break each
other.

```python
async def _recreate_database(url: URL, name: str) -> None:
    con = await asyncpg.connect(
        host=url.host, port=url.port, user=url.username, password=url.password, database="postgres"
    )
    try:
        await con.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await con.execute(f'CREATE DATABASE "{name}"')
    finally:
        await con.close()


def _own_database(url: str) -> str:
    """Under xdist each worker gets a database: a fixture truncates the index and downgrades the schema."""
    worker = os.getenv("PYTEST_XDIST_WORKER")
    if worker is None:
        return url
    parsed = make_url(url)
    name = f"{parsed.database}_{worker}"
    asyncio.run(_recreate_database(parsed, name))
    return parsed.set(database=name).render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def db_url() -> Iterator[str]:
    from_env = os.getenv(DB_VARIABLE)
    if from_env:
        yield _own_database(from_env)
        return
    for url in _container_url():
        yield _own_database(url)
```

- Each worker migrates its own database; a shared template database is not worth the coupling.
- The test database URL must point at a disposable database: the harness drops and recreates it.
  Say so in `CLAUDE.md`.
- **How many workers.** Locally `-n auto`. In CI a fixed number: most of an integration test is
  waiting for Postgres, so more workers than CPUs still pay off (Crivo: `-n 4` on a 2-CPU runner was
  faster than `auto`). Measure two or three values once.
- Tests that shared state by accident (module globals, `lru_cache` singletons, one session used by
  the test and by background tasks) show up now as flakiness. Fix the sharing; do not drop xdist.
  Example from Inkstave: a test harness handed one transactional session to the server's background
  tasks and to the test, and they raced; an `asyncio.Lock` around the shared session fixed it.

## Coverage

`COVERAGE_CORE=sysmon` makes coverage.py use `sys.monitoring` (Python ≥ 3.12), noticeably lighter
than the trace function. Set it in the CI job's `env` and in the coverage target. xdist and
`pytest-cov` work together with no extra setup; when stages run in separate jobs, each writes its
own data file and a final step combines them before the floor is checked.

## Per-test limit

The total budget does not tell which test grew. Keep `--durations=15` in `addopts` and, when the
suite is big, a gate on the JUnit XML durations (Inkstave's `check_test_budget.py`): warn above 3 s,
fail above 10 s for a test without the `slow` marker. A `slow` test is excluded from the default run
(`-m 'not slow'`) and runs in a separate, non-blocking target.

## Slow work never runs in the fast tiers

A real LLM call, a real LaTeX compile, a real browser render: a deterministic fake in the default run
(`project-standard` → `testing.md`), and the real thing in a `slow` or `live` tier.
