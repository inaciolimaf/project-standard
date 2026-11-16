---
name: mutation-testing
description: Inácio's playbook for mutation testing a Python (uv + pytest) backend with mutmut — measure how much behaviour the tests really pin down, mutate only the functions a change touched (on every core, in CI), hold each tier of code to a minimum score (domain rules 80%, bots/heuristics 65%), keep the tests mutation runs under 5 s in one process, skip log and error-message noise, and rewrite weak tests with cheap parallel agents working from the survivors list. Use when the user mentions mutation testing, mutmut, "teste de mutação", "testes mal feitos", "os testes não pegam nada", "qualidade dos testes", "mutation score", or when setting up CI for a project that follows project-standard.
---

# Mutation testing

Extracted from the card-games project (Exploding Kittens, Coup, BANG!, Saboteur), Nov/2026: the unit
suite had 85% line coverage, and still 36% of the mutants of one game survived. Six agents worked
from the survivors list and brought every game from 63–77% to 84–92%, found a real bug on the way,
and kept the tests mutation runs at 3.3 s. Works with `project-standard`, which owns the test
pyramid (`references/testing.md`), and `test-speed`, which owns how long CI takes.

**What it measures.** mutmut changes the code one small edit at a time (`>` into `>=`, `True` into
`False`, an argument into `None`) and runs the tests that cover the function. A mutant no test
notices ("survived") is behaviour nobody pins down. Coverage says a line *ran*; mutation says a test
would *fail* if the line were wrong.

## The rules and their guarantees

> 1. **Every change is mutated, only where it changed.** CI mutates the functions the diff touched,
>    on every core, and is red when a tier scores below its minimum.
> 2. **The tests mutation runs finish in 5 s in one process.** Every mutant pays for them.
> 3. **Tests pin behaviour, never sentences.** Log lines and error messages are not mutated.
> 4. **No database, no server, no browser.** Mutation runs the unit tests only: never the
>    integration tests (Postgres, Redis, migrations) and never the e2e (Playwright).
> 5. **A full run of everything in scope takes at most 40 minutes**, on every core. Past that, narrow
>    the paths or make the tests faster; never drop the parallelism.

| Rule | Guarantee |
|---|---|
| Changed functions reach the tier minimum | `tools/mutation.py` exits 1; CI job `mutation` (`references/ci.md`) |
| Tests for mutation ≤ 5 s | the same tool measures them before mutating and exits 1 past `max-test-seconds` |
| No text mutants | `do_not_mutate_patterns` in `[tool.mutmut]` (`references/setup.md`) |
| Unit tests only | `pytest_add_cli_args_test_selection` points at `tests/unit/` (or `-m "not integration"`); the tool measures exactly that selection |
| Full run ≤ 40 min | `make mutation-all` runs under `timeout 2400`; the baseline table records its time |
| Untested code is not "killed" | the tool counts mutmut's "no tests" (and mutants left "not checked" because no test runs them) as survivors |

The `mutation` job stays **outside** the 180 s gate of `test-speed`: it does not delay the merge
check, and a diff too large for its 270 s only warns. The project's `CLAUDE.md` states the three
rules in its "Tests" section.

### The minimum per tier

| Tier | Minimum | Why |
|---|---|---|
| Domain rules (engines, services, what each user may see) | **80%** | it is the product; a surviving mutant in a view can be data leaking to another user |
| Bots, heuristics, randomised policies | **65%** | random rolls and tie-breaks leave mutants that change nothing observable |

Never 100%: 5–10% of mutants are *equivalent* (the edit changes nothing observable). Chasing them
produces absurd tests. The reference used by Stryker is 80 "good", 60 "low".

## How to apply it

1. **Scope.** Mutate only the pure code: the domain and services, not the HTTP/WebSocket layer,
   repositories or stores. Their integration tests are too slow to run once per mutant. When the
   services take a database session (FastAPI + SQLAlchemy), list the files with no session in
   `[tool.mutation].paths` one by one; the services stay with the integration tests.
2. **Split the tests.** Mutation runs the unit tests only: `tests/unit/` in the standard layout, or
   every test minus the markers `integration` (drives a server, database, Redis) and a marker for
   whole simulated runs (`match` in the card games). Measure them in one process:
   `uv run pytest -p no:xdist -o addopts= tests/unit` → must say **under 5 s**. If not, apply
   `test-speed`, or move the slow ones behind a marker.
3. **Install.** `mutmut` pinned in the dev group, `[tool.mutmut]` and `[tool.mutation]` in
   `pyproject.toml`, `templates/tools/mutation.py` copied to `tools/`, `mutants/` in `.gitignore`,
   `make mutation` (`references/setup.md`).
4. **Baseline.** First run the selection **twice in one process** (`pytest.main(...)` twice, see
   `references/setup.md`): mutmut runs it more than once per worker, and a test that leaks global
   state (a registry, a cache, a monkeypatched module) fails the clean run. Then one full run
   (`--all`) or one per area in the background (`--survivors <area>.md` keeps every
   survivor's diff). A 3–8k-mutant area takes 2–13 min on 12 cores. **Show the user a table** area →
   score → survivors → biggest modules.
5. **Rewrite the weak tests** with agents in parallel, one per area, working from the survivors files
   and never running mutation themselves (`references/rewriting-tests.md`). Integrate, run the suite,
   then **one** measurement. Areas still below their tier get another round from the new survivors
   file, and another measurement: measure → agents → measure, until every tier passes.
6. **CI.** The `mutation` job (`references/ci.md`). From then on every touched function must reach
   its tier: the old code never blocks anyone, and the score only rises.
7. Update `CLAUDE.md`, `docs/system/` and the Makefile help in the same commit, as
   `project-standard` requires.

## Pitfalls (each one cost time)

- **Mutating everything every time.** The card games had 25k mutants (one hour). Diff mode: a few
  dozen to a few hundred mutants, 25–120 s.
- **Idle CPU.** Pass `max_children=os.cpu_count()`. A script reading results one `mutmut show` per
  mutant is serial and slow: read `mutants/*.meta` in-process instead (the tool does).
- **Stale `mutants/`.** mutmut treats a file it copied unmutated on an earlier run as "unmodified"
  and skips it when it comes into scope. The tool deletes `mutants/` before each run.
- **`only_mutate` has no CLI flag**, and `[tool.mutmut]` in `pyproject.toml` wins over `setup.cfg`.
  The tool sets it on mutmut's config object before calling `_run`.
- **Text mutants.** Without the pattern filter, half the survivors were log lines and error
  messages, and agents started asserting sentences. Filter `add_log(`/`logger.`/`raise <Error>(`.
- **Agents running mutation.** Each run costs minutes of CPU, and six in parallel saturate the
  machine. They get the survivors file and a 90% target instead; one measurement after the merge.
- **"no tests" counted as killed.** The first version of the tool read only "survived" as a
  survivor; mutmut reports a function no selected test runs as "no tests", so untested code scored
  100%. And when *no* function in scope is covered, mutmut stops before testing and leaves every
  mutant "not checked". Both are survivors now.
- **Tests that read the source tree.** Architecture, naming and size tests read `api/**.py`; under
  mutmut that is the trampolined copy in `mutants/`, and the clean run fails. `--ignore` them in
  `pytest_add_cli_args`.
- **Files the tests need outside `source_paths`.** mutmut runs the tests inside `mutants/` and copies
  only the source paths, `tests/` and the lock files: a package the code imports (`downloader/`) or a
  file a test reads (`.env.example`) goes in `also_copy`.
- **A leaking test fails the clean run.** mutmut calls pytest more than once in the same process: a
  test that subscribes to a global registry and never undoes it finds its old subscribers the second
  time. Fix the test (`monkeypatch.setitem` on the registry), not the tool.
- **Whole-match or end-to-end tests in the mutation selection.** They kill few extra mutants and
  multiply the time of every mutant.

## Checklist

- [ ] `mutmut` pinned in the dev group (`uv add --dev mutmut==<x.y.z>`)
- [ ] `[tool.mutmut]`: `source_paths`, `pytest_add_cli_args_test_selection`,
      `pytest_add_cli_args` (no cache, `-o addopts=`), `do_not_mutate_patterns`
- [ ] `[tool.mutation]`: `paths` (pure code only), `test-selection`, `max-test-seconds = 5`, `tiers`
- [ ] markers registered in `[tool.pytest.ini_options].markers` with their reason
- [ ] `tools/mutation.py` (template), passing ruff, mypy strict and the size lint
- [ ] `mutants/` in `.gitignore`; `make mutation` under `timeout`
- [ ] CI job `mutation`: `fetch-depth: 0`, base from the event, `timeout-minutes`, outside the gate
- [ ] the selection passes twice in one process (no leaking global state)
- [ ] baseline table shown, with the run's time (≤ 40 min); weak areas rewritten by parallel agents;
      one measurement after the merge, another round for an area still below its tier
- [ ] rules in `CLAUDE.md` → "Tests"; tool in `docs/system/` (tooling section)

## Reference map

| Subject | File |
|---|---|
| `pyproject.toml`, markers, the tool, Makefile, how mutmut spends its time | [references/setup.md](references/setup.md) |
| The CI job | [references/ci.md](references/ci.md) |
| Baseline, agents rewriting tests, the brief, merging | [references/rewriting-tests.md](references/rewriting-tests.md) |
| The tool to copy | [templates/tools/mutation.py](templates/tools/mutation.py) |
