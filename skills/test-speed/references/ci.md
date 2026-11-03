# CI (GitHub Actions)

## Job layout: side by side, then the gate

```
check ─┐
back  ─┤
web   ─┼─> gate (fails on any failure, or past 180 s)
e2e×N ─┘
```

- **No `needs` between the work jobs.** Chaining `e2e` after `back` and `web` adds their times; side
  by side the run lasts as long as the slowest job.
- **`check`** holds everything that is not a test: ruff, format check, function size, import
  contracts, docs coverage, mypy, the OpenAPI ↔ frontend types diff, eslint, prettier, `tsc -b`, and
  the production build with the bundle budget. The test jobs then only test.
- **`back`** runs pytest with coverage; **`web`** runs Vitest with coverage; **`e2e`** is the shard
  matrix (`e2e.md`).
- Every job has `timeout-minutes` above the budget (Crivo: 6). It guards against a hang; a per-job
  limit at the budget cancels useful work without saying anything about the total.

## The gate

```yaml
gate:
  runs-on: ubuntu-latest
  needs: [check, back, web, e2e]
  if: always()
  permissions:
    actions: read
  steps:
    - name: all green
      if: contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled')
      run: exit 1
    - name: at most 180 s from the start of the run until here
      env:
        GH_TOKEN: ${{ github.token }}
      run: |
        start=$(gh api "repos/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID/attempts/$GITHUB_RUN_ATTEMPT" --jq .run_started_at)
        total=$(( $(date +%s) - $(date -d "$start" +%s) ))
        echo "run took ${total}s"
        if [ "$total" -gt 180 ]; then echo "::error::CI took ${total}s; the limit is 180s"; exit 1; fi
```

- It measures the run's real wall clock, queue time included: what a person waits for.
- Make `gate` the only required check in branch protection; it already depends on every job.
- **Alternative used by Inkstave**: each test stage publishes its own duration
  (`scripts/measure_stage.sh` writes `seconds=` to `$GITHUB_OUTPUT`) and a `budget` job gates the
  **slowest** stage, never the sum, since the stages run in parallel. It also feeds the per-test
  limit from the JUnit files. Keep the coverage floor step with `if: ${{ !cancelled() }}` so a red
  budget does not hide a red coverage.

## Caches and setup

```yaml
- uses: astral-sh/setup-uv@v5
  with:
    prune-cache: false # took up to 108 s after the job had finished
- uses: actions/setup-node@v4
  with:
    node-version: 22
    cache: npm
    cache-dependency-path: web/package-lock.json
```

- `uv sync --frozen` and `npm ci --no-audit --no-fund`.
- A job installs only what it uses: `back` needs no Node, `web` needs no uv.

## Postgres service

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    options: >-
      --tmpfs /var/lib/postgresql/data
      --health-cmd "pg_isready -U app" --health-interval 2s --health-timeout 3s --health-retries 30
```

`--tmpfs` keeps the data in memory (no fsync to disk); a 2 s health interval starts the steps sooner.
The CI database is thrown away anyway.

## Where the minutes hide

Read the step durations of a slow run before touching tests. In Crivo, besides the tests: the uv
cache post-step (108 s), `playwright install --with-deps` in every e2e job, and the production build
done inside a test job. None of them show up in `pytest --durations`.
