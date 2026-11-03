---
name: test-speed
description: Inácio's playbook for making a test suite and its CI run fast — measure where the time goes, then apply the fixes in order of payoff (cheap password hashing in tests, pytest-xdist with one database per worker, Postgres on tmpfs, Vitest threads and worker count, one Playwright login shared by read-only projects, shards, parallel CI jobs, setup-uv prune-cache, lighter coverage) and guard the result with a wall-clock gate of 180 s. Use when tests or CI are slow, when a run passes the budget, when the user says "testes lentos", "reduz o tempo dos testes", "CI lento", "acelera o CI", "passou de 3 minutos", or when setting up CI for a project that follows project-standard.
---

# Test speed

Extracted from Crivo, whose CI went from **17m31s to under 180 s** in three commits (Nov/2026), and
from Inkstave, which gates its stages the same way. Works with `project-standard`, which owns the
test pyramid (`references/testing.md`) and the Makefile and CI (`references/makefile-and-ci.md`);
this skill owns how long they take.

## The rule and its guarantee

> **CI lasts at most 180 s, from the start of the run to the end.** The jobs run side by side, so
> only the slowest one counts. When the gate fails, make the tests faster; do not raise the limit.

- **Guarantee:** a `gate` job that reads the run's real wall clock and fails past 180 s
  (`references/ci.md` → "The gate"). Per-job `timeout-minutes` only guard against a hang; they
  never measure the total.
- Locally, run the suite under `timeout 180` too.
- The project's `CLAUDE.md` states the rule in its "Tests" section.

## How to apply it

1. **Measure before changing anything.** Without numbers the work goes to the wrong place.
   - Backend: `pytest --durations=25` (keep `--durations=15` in `addopts`, it costs nothing).
   - Frontend: `vitest run --reporter=verbose` and the total of each file.
   - E2E: the Playwright `list` reporter's per-test times.
   - CI: the duration of every **step** of every job in the Actions UI or with
     `gh run view <id> --json jobs`. Look for steps that are not tests at all (installs, cache
     post-steps, builds repeated in several jobs).
2. **Show the user a table** *where the time goes → fix → expected gain*, ordered by gain.
3. **Apply in that order**, one commit per fix or per area (`ci: ...`, `test: ...`, `perf(test): ...`),
   each one measured: the commit message carries the before and after when it is known
   (`110 s against 151 s`).
4. **Re-run the CI and read the gate.** Stop when it passes with margin; do not keep optimising a job
   that is no longer the slowest.
5. Update the project's `CLAUDE.md` (the rule, new commands such as `-n auto`) and
   `docs/system/` in the same commit, as `project-standard` requires.

## Where the time usually goes (Crivo's order of payoff)

| # | Cause | Fix | Reference |
|---|---|---|---|
| 1 | Password hashing at production cost in every test that creates or logs in a user | bcrypt cost 4 / minimal argon2 in tests only | `backend.md` |
| 2 | Backend tests in one process | `pytest-xdist`, one database per worker | `backend.md` |
| 3 | Every e2e test signs in through the API (one hash each, hundreds per run) | one login in `globalSetup`, `storageState` for the read-only projects | `e2e.md` |
| 4 | Jobs chained with `needs`, lint and types inside the test job | independent jobs side by side; lint and types in their own `check` job | `ci.md` |
| 5 | Read-only e2e projects with `workers: 1` | `fullyParallel` + workers, then shards in a matrix | `e2e.md` |
| 6 | `setup-uv` pruning its cache after the job (up to 108 s) | `prune-cache: false` | `ci.md` |
| 7 | Vitest with the default `forks` pool and CPUs − 1 workers (one on a 2-CPU runner) | `pool: "threads"`, `--maxWorkers=3` in CI | `frontend.md` |
| 8 | Postgres writing to disk, health-check every 5 s | `--tmpfs /var/lib/postgresql/data`, health every 2 s | `ci.md` |
| 9 | Coverage tracing with `sys.settrace` | `COVERAGE_CORE=sysmon` (Python ≥ 3.12) | `backend.md` |
| 10 | `playwright install --with-deps chrome` in every e2e job | `channel: "chrome"` uses the Chrome already in the runner image | `e2e.md` |
| 11 | The production build inside the test job | build and bundle budget in `check` (e2e still builds what it serves) | `ci.md` |

Always check #1 first: in Crivo three hashes per test at cost 12 were the bulk of the backend suite,
and the same hash, done by the API on every e2e login, was most of the e2e time.

## What never makes the suite faster

- **Raising the limit** or moving slow tests out of CI without a marker. A genuinely slow test is
  marked (`@slow`) and stays out of the default run; a slow test that is not marked fails the
  per-test gate (`backend.md` → "Per-test limit").
- **Lowering the cost in production.** The cheap hash lives only in the test fixtures; the stored
  hash carries its own cost, so production keeps its own.
- **`sleep N` and fixed waits.** They are slow on a fast machine and flaky on a loaded one. Poll the
  condition with a deadline (the API's `/health`, a Redis `pubsub_numsub`, a row count).
- **More parallelism than the shared resource takes.** A single backend, worker or database behind
  many browser contexts slows everything and makes tests flaky. Tests that change data run one at a
  time or each on its own data.
- **Retries to hide flakiness.** `retries: 0`; a flaky test is a bug with a test to fix.

## Checklist

**Backend**
- [ ] password hash cost lowered in the autouse test fixture (bcrypt 4, or argon2 `time_cost=1`,
      `memory_cost=8`, `parallelism=1`); the production cost is a named constant or setting
- [ ] `pytest-xdist` in the dev group; `-n auto` locally (in `addopts` or the test target), a fixed
      `-n` in CI tuned to the runner
- [ ] one database per xdist worker (`<db>_<worker>`), created by the session fixture
- [ ] `COVERAGE_CORE=sysmon` where coverage runs
- [ ] `--durations` in `addopts`; a per-test limit with an `@slow` marker kept out of the default run

**Frontend**
- [ ] Vitest `pool: "threads"`; `--maxWorkers` set in CI
- [ ] fake timers instead of real waits (`project-standard` → `testing.md`)

**E2E**
- [ ] one login in `globalSetup` writing `storageState` for read-only projects
- [ ] read-only projects `fullyParallel` with several workers; projects that write data with one
- [ ] shards in the CI matrix for the big projects
- [ ] system Chrome (`channel: "chrome"`), no `playwright install` in CI

**CI**
- [ ] jobs `check`, `back`, `web`, `e2e` with no `needs` between them, and a `gate` that needs all
- [ ] `gate` fails if any job failed or was cancelled, and if the run passed 180 s
- [ ] `timeout-minutes` on every job (a hang guard, above the budget)
- [ ] `prune-cache: false` on `setup-uv`; npm cache by `package-lock.json`
- [ ] Postgres services on `--tmpfs`, health-check every 2 s
- [ ] the rule in `CLAUDE.md` → "Tests"

## Reference map

| Subject | File |
|---|---|
| pytest: hashing, xdist and a database per worker, coverage, per-test limit | [references/backend.md](references/backend.md) |
| Vitest: pool and workers | [references/frontend.md](references/frontend.md) |
| Playwright: shared login, parallel projects, shards, browser | [references/e2e.md](references/e2e.md) |
| GitHub Actions: job layout, the 180 s gate, caches, services | [references/ci.md](references/ci.md) |
