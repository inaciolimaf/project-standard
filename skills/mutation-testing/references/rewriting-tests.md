# Rewriting weak tests from the survivors

## 1. Baseline

With the tool's `--all`, one run covers every file in scope (`make mutation-all`, at most 40 min). Or
run every area in the background, one after the other (they share the CPU), each under `timeout`:

```bash
for a in area1 area2 area3; do
  timeout 1800 uv run python -m tools.mutation --survivors "$OUT/$a.md" app/<path>/$a/*.py > "$OUT/$a.log"
done
```

`--survivors` keeps every survivor's diff; each run deletes `mutants/`, so without it the next area
erases the previous list. Then count survivors per module for the briefs:

```bash
grep -oE '^## `app\.[a-z_.]+\.x' "$OUT/$a.md" | sed -E 's/^## `//; s/\.x$//' | sort | uniq -c | sort -nr
```

Show the user: area → score per tier → survivors → biggest modules. An area above its minimum
needs no agent.

## 2. Agents

- **One agent per area**, each in its own worktree (`isolation: "worktree"`), new test files with an
  area prefix (`tests/test_<area>_mut_<topic>.py`), so merges never conflict. Split an area with more
  than ~1,500 survivors in two by module.
- **A cheap model**: the work is many small, well-specified tests. The card games used Haiku; Crivo
  used Sonnet, for domain rules written in Portuguese. Ask the user.
- **"no tests" survivors** (marked `(no tests)` in the file) mean no unit test runs the function at
  all: the agent writes the first tests of that module, starting from its public functions.
- **They never run mutation testing.** They read the survivors file and run only pytest. **Target
  90%** in the brief so the one real measurement lands above 80%.
- **They never change application code.** A correct test that exposes a bug stays, marked
  `@pytest.mark.xfail(strict=True, reason="BUG: ...")`, and goes in the report. The main agent fixes
  it afterwards with that test as the reproduction.
- A first pass usually stops at the biggest modules. Read the report and send a second round
  (`SendMessage` to the same agent) listing the modules left out, the tier still below its minimum
  first.

## 3. The brief (adapt the paths)

```markdown
# Brief: kill surviving mutants with behaviour tests

A mutation-testing run changed the code one small edit at a time and ran the tests. Every mutant in
your survivors file is an edit that **no test noticed**. Write tests that would fail on those edits.

## Hard rules
1. **Never run mutation testing** (`mutmut`, `make mutation`, `tools.mutation`). Work from the file.
   Run only the unit tests (`tests/unit`): no database, no migrations, no e2e.
2. **Do not change anything under `backend/app/`.** If a correct test exposes a real bug, keep it,
   mark it `@pytest.mark.xfail(strict=True, reason="BUG: <one line>")` and list it in your report.
3. Test **behaviour**: state, returned events, what each user's view contains and must NOT contain,
   counts, `Error.code` (never the message). Never assert log or message text.
4. **Target: kill 90% of your survivors.** Skip equivalent mutants; no absurd tests to chase them.
5. New files `tests/test_<prefix>_mut_<topic>.py`; helpers in `tests/_helpers_<prefix>.py`. Do not
   touch `tests/conftest.py` or other areas' files.
6. Fast tests: in memory, no sleeps, no network; under ~2 s added to the suite.
7. The rules documents are the source of truth; the code may be wrong.

## Reading the survivors file
    ## `app.game.coup._challenge.xǁChallengeMixinǁblock__mutmut_12`
    -    if o.get("stage") == C.STAGE_BLOCKED:
    +    if o.get(None) == C.STAGE_BLOCKED:
Nobody blocks an action twice: a test that does and expects code `cannot_block` kills it.
Work module by module, biggest first (`grep -n '^## \`<module>' FILE`, then read around).

## Loop
- After each file: `timeout 120 uv run pytest -q -x tests/<file>`, ruff check and format.
- At the end the whole suite passes. Every command under `timeout`. Commit in the worktree; no push.

## Report
Branch and commits; per module, survivors targeted and skipped as equivalent; BUGs (xfail); suite
time before and after.
```

## 4. Integrate and measure once

The loop is: measure → agents → integrate → measure. Only the main agent measures, and only after
every branch is merged; an area still below its tier gets a second round from the **new** survivors
file (`SendMessage` to the same agent), then one more measurement.

1. Merge each branch (`git diff --name-only main...<branch>` must list only test files).
2. Fix the bugs the xfail tests describe, each with its test turned green.
3. `make test`, lint, and `tools.mutation --check-speed`: the new tests must fit the 5 s.
4. **One** full measurement per area. Every tier above its minimum, or another round for the area
   below.

The card games, after this: Coup 73 → 91%, Exploding Kittens 65 → 92%, BANG! 63 → 84%,
Saboteur 77 → 92%, core 76 → 99%, bots 47–71 → 92–100%; +1,579 tests (0.4 s each area); one bug
found (a steal choice that lost the player's prompt).
