# Setup

## `pyproject.toml`

```toml
[dependency-groups]
dev = [
    # ...
    "mutmut==3.8.1",
]

[tool.pytest.ini_options]
markers = [
    "integration: drives the server, a database or Redis; left out of mutation testing (too slow)",
]

# --- mutation testing (tools/mutation.py) -------------------------------------------

[tool.mutmut]
# tools/mutation.py narrows what is mutated (the functions a change touched) and adds the test
# selection of [tool.mutation]; run mutation testing through it, not through `mutmut` directly.
source_paths = ["app/"]
pytest_add_cli_args_test_selection = ["tests/"]
pytest_add_cli_args = ["-p", "no:cacheprovider", "-p", "no:randomly", "-o", "addopts="]
# Log lines and error messages are text for people: mutating them makes tests compare sentences.
# The whole statement is skipped; the conditions around it are still mutated.
do_not_mutate_patterns = ['\.add_log\(', 'logger\.', 'raise GameError\(']

[tool.mutation]
# Only the pure code is mutated; the I/O layer is covered by integration tests, too slow to run
# once per mutant.
paths = ["app/modules/*/domain/*", "app/modules/*/services/*"]
# The tests mutmut runs. They must finish in `max-test-seconds` in one process.
test-selection = "not integration"
max-test-seconds = 5
# The first tier whose paths match a file wins.
tiers = [
    { name = "heuristics", min-score = 65, paths = ["app/*/bot.py"] },
    { name = "domain rules", min-score = 80, paths = ["app/*"] },
]
```

- `do_not_mutate_patterns` are regexes matched per line; the whole statement that starts on a
  matching line is skipped. Use the project's own log call and error class.
- With the standard's folders (`tests/unit/`, `tests/integration/`), select by folder instead of by
  marker: `pytest_add_cli_args_test_selection = ["tests/unit/"]` and `test-selection = ""`. The
  tool measures and runs exactly that selection (folder plus `-m` when the expression is set).
- `tests_dir` is deprecated in mutmut 3.8; use `pytest_add_cli_args_test_selection`.
- Pin the exact version: the tool touches mutmut internals (`_run`, `config()`,
  `SourceFileMutationData`, `get_diff_for_mutant`), which may move between releases.

## The markers

```python
pytestmark = pytest.mark.integration  # hub, Redis or SQLite: too slow for mutation testing
```

One line under the imports of each file. The default `make test` still runs everything; only
mutation leaves them out. A test that is slow but pure (a whole simulated match) gets its own
marker (`match`), so its reason stays clear.

## The tool: `templates/tools/mutation.py`

Copy it to `backend/tools/`. Commands:

```
uv run python -m tools.mutation                       # functions changed since origin/main
uv run python -m tools.mutation --base HEAD~3         # ... since another ref
uv run python -m tools.mutation app/x/y.py            # every function of these files
uv run python -m tools.mutation --survivors s.md app/x/*.py   # + every survivor's diff
uv run python -m tools.mutation --check-speed          # only the 5 s budget of the tests
```

What it does, in order:

1. Measures the selected tests in one process (`-p no:xdist`, pytest's own clock) and stops with
   exit 1 past `max-test-seconds`.
2. Maps the diff since the merge base (working tree included) to the module functions and methods
   it touched, keeping only files under `[tool.mutation].paths`. mutmut names them
   `<module>.x_<function>__mutmut_N` and `<module>.xǁ<Class>ǁ<method>__mutmut_N`.
3. Deletes `mutants/`, narrows mutmut's `only_mutate` to those files, adds `-m <selection>` and runs
   `_run(globs, max_children=os.cpu_count())`.
4. Reads the results from `mutants/*.meta`, scores each tier, prints Markdown (and appends it to
   `$GITHUB_STEP_SUMMARY`), and exits 1 when a tier is below its minimum.

## Makefile

```make
mutation: ## Mutation testing on the functions changed since origin/main; fails below the tier minimum or past 5 s of tests
	$(BACK) timeout 600 uv run python -m tools.mutation
```

## Where the time goes

Measured on the card games (12 cores):

| Phase | Time | Note |
|---|---|---|
| Generate mutants | 0.3 s per file | 11 s if `only_mutate` is not narrowed (every file) |
| Map tests to functions (stats) | ~30 s | the whole selection once, with tracing |
| Clean run | the selection once | |
| Mutants | 4–20 per second | each runs only the tests that cover its function; survivors run all of them |

A mutant costs the time of the tests that cover its function, and a survivor runs all of them. That
is why the 5 s budget matters more than any flag, and why good tests make the run faster: a killed
mutant stops at the first failing test (the full baseline took 39 min, the run after the rewrite
17 min).
