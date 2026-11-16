# CI job

```yaml
  mutation:
    # Mutation testing on the functions a push or pull request changed (backend/tools/mutation.py): red when
    # a tier scores below its minimum ([tool.mutation] in pyproject.toml) or the tests it runs pass 5 s,
    # report in the job summary. Outside the gate, so it does not count toward 180 s; a diff too big for
    # 270 s only warns.
    name: mutation (changed functions)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # the merge base must be in the clone
      - uses: astral-sh/setup-uv@v5
        with:
          prune-cache: false
      - run: uv sync --frozen
      - name: mutmut on the changed functions (make mutation)
        env:
          # pull request: since the base branch; push to main: since the previous tip of main.
          BASE: ${{ github.event_name == 'pull_request' && format('origin/{0}', github.base_ref) || github.event.before }}
        run: |
          rc=0; timeout 270 uv run python -m tools.mutation --base "$BASE" || rc=$?
          if [ "$rc" -eq 124 ]; then echo "::warning::mutation testing hit 270 s; run make mutation locally"; exit 0; fi
          exit "$rc"
```

- **Not in the gate's `needs`.** The `gate` of `test-speed` measures the run until it reaches it;
  the mutation job runs beside it and never adds to the 180 s.
- **Runs on push to main too.** Projects that commit straight to main have no pull requests; the
  diff is then against `github.event.before`.
- **A timeout warns, it does not fail.** A big refactor can have thousands of mutants; the job says
  so and the author runs `make mutation` locally. Every other failure (score, test budget, a broken
  test) stays red.
- The 5 s check runs on every push, even when no function in scope changed, so a slow test cannot
  slip in through a tests-only commit.
- GitHub's runners have 4 cores against a developer's 8–16: expect the mutant phase to take 2–3×
  longer than locally.
