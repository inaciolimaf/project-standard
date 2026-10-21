# Lint, formatting and types

Nine checks, all blocking CI:

| # | Check | Side | Local command (Crivo) | What it catches |
|---|---|---|---|---|
| 1 | `ruff check` | Python | `make lint` | probable bugs, security, style, imports, annotations |
| 2 | `ruff format --check` | Python | `make formato` (fixes) | formatting |
| 3 | `function_size` | Python | `make lint` | a function with more than 30 useful lines, a file with more than 300 |
| 4 | `mypy --strict` | Python | `make tipos` | types |
| 5 | `eslint` | frontend | `make web-teste` | JS/TS bugs, hooks, component > 100 lines, reuse (color, number, sheet, keyboard), routes |
| 6 | `prettier --check` | frontend | `make web-formato` (fixes) | formatting |
| 7 | `tsc -b` (strict) | frontend | `make web-teste` | types |
| 8 | `make docs` | docs | `make docs` | documentation covers the code and does not cite what vanished (`documentation.md`) |
| 9 | `lint-imports` | Python | `make lint` | boundaries between modules and layers (`structure.md`) |

Plus the backend × frontend contract (frontend types generated from the OpenAPI, §8) and the
frontend's minimum test coverage (60%, in `testing.md`). The Makefile targets above are Crivo's
(Portuguese, kept because people type them); a new project uses the English names in
`makefile-and-ci.md`.

**Exception rule (applies to all of them):** every exception has its reason written next to it.
- A whole file: `per-file-ignores` / `[[tool.mypy.overrides]]` / the function size `ignore`,
  with a comment on the line above.
- One line: `# noqa: S608 - fixed table name`, `# type: ignore[attr-defined]`,
  `// eslint-disable-next-line rule` with a one-line comment above explaining it.
- Never `# noqa` without a code, `# type: ignore` without a code, nor a file-level
  `eslint-disable`.

---

## 1. ruff check

```toml
[tool.ruff]
line-length = 110
target-version = "py312"
src = ["."]
exclude = ["web", "migrations/versions", <large data: "corpus", "cache">]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "SIM", "RUF", "ANN", "S", "PLR0913"]
ignore = ["ANN401", "RUF001", "RUF002", "RUF003", "RUF012", "S101", "S311"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S", "ANN", "PLR0913", "E501"]

[tool.ruff.lint.pylint]
max-args = 7

[tool.ruff.lint.isort]
known-first-party = ["api", "pipeline", "tests", "tools"]
```

`migrations/versions` stays out because Alembic generates it and it is never edited again; `web`
has its own lint.

### Enabled groups

| Code | Plugin | What it guarantees | Examples of what it flags |
|---|---|---|---|
| **E** | pycodestyle (errors) | PEP 8 style the formatter does not solve | `E501` line > 110, `E402` import not at top, `E711` `== None`, `E722` bare `except:`, `E741` ambiguous name (`l`, `O`) |
| **W** | pycodestyle (warnings) | whitespace | `W291` trailing whitespace, `W605` invalid escape in a string |
| **F** | pyflakes | real errors | `F401` unused import, `F811` redefinition, `F821` undefined name, `F841` variable assigned and unused, `F541` f-string without placeholder |
| **I** | isort | stable import order (stdlib, third party, first party, separated) | `I001` unsorted block — `ruff check --fix` solves it |
| **N** | pep8-naming | names | `N802` non-snake_case function, `N801` non-CapWords class, `N806` uppercase variable inside a function, `N818` exception not ending in `Error` |
| **UP** | pyupgrade | the target version's syntax | `UP006` `List[int]` → `list[int]`, `UP007` `Optional[X]` → `X \| None`, `UP035` obsolete `typing` import |
| **B** | flake8-bugbear | pitfalls | `B006` mutable default (`def f(x=[])`), `B008` call in an argument default, `B904` `raise` inside `except` without `from`, `B007` unused loop variable, `B023` closure capturing a loop variable |
| **A** | flake8-builtins | do not shadow builtins | a variable/argument called `id`, `type`, `list`, `input`, `filter` |
| **C4** | flake8-comprehensions | idiomatic comprehensions | `C400` `list(x for x in y)`, `C408` `dict()` instead of `{}`, `C416` unnecessary comprehension |
| **SIM** | flake8-simplify | simpler code | `SIM102` nested `if` that becomes `and`, `SIM108` ternary, `SIM117` nested `with`, `SIM118` `key in d.keys()` |
| **RUF** | ruff's own rules | assorted | `RUF005` list concatenation becomes unpacking, `RUF010` explicit conversion in an f-string, `RUF100` useless `noqa` |
| **ANN** | flake8-annotations | every function with annotated arguments and return (matches strict mypy) | `ANN001` argument without type, `ANN201` return without type |
| **S** | flake8-bandit | security | `S608` SQL built with an f-string, `S105/S106` literal password, `S307` `eval`, `S603/S607` subprocess, `S113` request without timeout, `S324` weak hash |
| **PLR0913** | pylint | at most **7 arguments** (`max-args = 7`) | a function with 8+ parameters — group them in a dataclass/DTO |

### Ignored on purpose

| Code | Why it stays off |
|---|---|
| `ANN401` | forbids `Any`; sometimes it is the honest annotation (structlog, raw JSON). Strict mypy still enforces the rest |
| `RUF001/002/003` | ambiguous character in a string/docstring/comment; product text (in the product's language) has `–`, `—`, `×`, typographic quotes |
| `RUF012` | mutable class attribute without `ClassVar`; clashes with pydantic's `model_config` and SQLAlchemy's `__table_args__` |
| `S101` | forbids `assert`; `assert` is used for invariants and to narrow types |
| `S311` | non-cryptographic `random`; it is fine for drawing questions. Tokens/secrets use `secrets` |

`N818` (exception names end in `Error`) is on: with the code in English it costs nothing
(`AppError`, `SettingsError`). A project still being migrated from another language ignores it
until its exceptions are renamed, with that reason in the comment.

### In tests (`tests/**`)

Off: `S` (literal passwords and `assert` are normal in tests), `ANN` (fixtures and tests without
annotations), `PLR0913` (a test receives many fixtures), `E501` (long inline data).

### Crivo's exceptions (examples of the right format)

```toml
# Reuses test_notices' fixtures by importing them: pytest injects them by parameter name.
"tests/integration/test_index.py" = ["F811"]
# The numba kernel takes dozens of loose arrays on purpose (a namedtuple in the loop is 40x slower).
"api/modules/questions/index/kernel.py" = ["ANN001", "ANN202", "PLR0913"]
"pipeline/ingestion/db.py" = ["S608"]
```

Per line: `# noqa: S608 - fixed table name` (SQL with a table name from a closed list — the
user's value always goes by parameter `$1`/`?`).

### Code patterns the lint enforces

- **FastAPI**: dependencies and parameters through `Annotated` (`DbSession = Annotated[
  AsyncSession, Depends(session)]` in `api/core/deps.py`), never `x = Depends(...)` as a default
  — otherwise `B008`.
- **`raise ... from error`** inside `except` (`B904`).
- **Too many arguments** become a dataclass or DTO, not a `noqa`.
- **SQL**: values always by parameter; f-strings only for an identifier from a closed list, with
  `noqa: S608` and a reason.

## 2. ruff format

ruff's style (black-compatible) with `line-length = 110`. The format target applies it; CI runs
`ruff format --check .`. Formatting is not discussed in review.

## 3. Function size cap (`tools/function_size.py`)

ruff does not have this rule (`PLR0915` counts *statements*, not lines). A ready template in
`templates/tools/function_size.py`.

- At most **30 useful lines**. Useful = between the body's first statement and the end, without
  blank lines, comments or docstrings — comments and docstrings are encouraged, not punished.
- Signature and decorators do not count (the signature's size is already enforced by
  `PLR0913`).
- A nested function counts on its own **and** inside the outer one (a large closure weighs on the
  outer function).
- Output: `api/x.py:42: FN001 \`name\` has 37 useful lines (max 30)`, sorted from largest to
  smallest; exits with 1 if it finds anything.

```toml
[tool.function-size]
max-lines = 30
paths = ["api", "pipeline", "tools"]
# The numba kernel is a flat loop on purpose: each function call with an array inside the loop pays
# a reference count increment and decrement (and contention between threads), 6x slower.
ignore = ["api/modules/questions/index/kernel.py"]
```

How to fix: extract named steps (`_validate`, `_build`, `_save`), do not compress lines. Tests do
not go through this rule.

### File size cap: 300 lines

The same tool measures the **file**: at most **300 lines** (code FN002), counting as for
functions (no blank lines, comments or docstrings). A module that goes over is split by
responsibility (`service.py` → `service/create.py`, `service/answer.py`; a 1,200-line
`models.py` → one `models.py` per module). Settings: `max-file-lines = 300` in
`[tool.function-size]`; files still to be split in `ignore-file-temporarily` (with a comment and
a date), and `SIZE_STRICT=1` ignores that list to check the target. On the frontend, `max-lines`
300 (`skipBlankLines`, `skipComments`) in eslint.

## 4. mypy

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["api", "pipeline", "tools"]
plugins = ["pydantic.mypy"]
warn_unreachable = true

[[tool.mypy.overrides]]
module = ["fsrs.*", "jose.*", "testcontainers.*", ...]   # untyped libs
ignore_missing_imports = true
```

`strict` turns on: `disallow_untyped_defs`, `disallow_incomplete_defs`,
`disallow_untyped_calls`, `disallow_untyped_decorators`, `disallow_any_generics` (`list` without
a parameter), `no_implicit_optional`, `warn_return_any`, `warn_unused_ignores`,
`warn_redundant_casts`, `strict_equality`, `check_untyped_defs`, `no_implicit_reexport`.
`warn_unreachable` flags dead code after type narrowing.

- pydantic plugin: mypy understands the models' fields and `__init__`.
- An untyped lib: first look for a stub (`types-*`, `asyncpg-stubs`) in the dev group; only if
  there is none, `ignore_missing_imports` in the override.
- A module that cannot be typed (e.g. the numba kernel): a module override turning off only what
  is needed, with a comment.
- Tests do **not** go through mypy (current decision; see gaps).
- `# type: ignore[code]` always with a code; `warn_unused_ignores` flags the leftovers.

## 5. eslint (frontend, flat config)

Complete template: Crivo's `web/eslint.config.js`. Structure:

```js
import prettier from "eslint-config-prettier";
const ROUTE_RULES = [/* useParams({from}), useSearch({from}) */];
const REUSE_RULES = { color: [...], number: [...], sheet: [...], keyboard: [...] };   // table below
/** The syntax rules for `src/`, minus those of the group the file implements. */
function syntax(...allowed) { /* ROUTE_RULES + REUSE_RULES groups not in `allowed` */ }

export default tseslint.config(
  { ignores: ["dist", "node_modules", "src/api/types.ts", "captures", "playwright-report", "test-results", "coverage"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  { files: ["**/*.{ts,tsx}"], plugins: { "react-hooks": reactHooks },
    rules: { ...reactHooks.configs.recommended.rules, "react-hooks/exhaustive-deps": "error",
             "no-restricted-syntax": ["error", ...ROUTE_RULES] } },
  { files: ["src/**/*.{ts,tsx}"],
    rules: { "max-lines-per-function": ["error", { max: 100, skipBlankLines: true, skipComments: true }],
             "no-restricted-syntax": syntax() } },
  // each reuse group has ONE allowed file: the one that implements the thing
  { files: ["src/lib/formatting.ts"], rules: { "no-restricted-syntax": syntax("number") } },
  { files: ["src/components/ui/Card.tsx"], rules: { "no-restricted-syntax": syntax("sheet") } },
  { files: ["src/lib/shortcuts.ts"], rules: { "no-restricted-syntax": syntax("keyboard") } },
  { files: ["src/lib/palettes.ts"], rules: { "no-restricted-syntax": syntax("color") } },
  prettier,   // last: turns off style rules that conflict with prettier
);
```

`npm run lint` = `eslint src tests e2e`. It ignores the build, the generated file (`types.ts`),
Playwright's artifacts and the coverage report. Tests and e2e stay out of the line cap and the
reuse rules (a `describe` is long by nature).

| Set | What it brings (main ones) |
|---|---|
| `js.configs.recommended` | `no-unused-vars`, `no-undef`, `no-unreachable`, `no-constant-condition`, `no-dupe-keys`, `no-empty`, `no-fallthrough`, `no-cond-assign`, `no-debugger`, `no-self-assign`, `no-case-declarations`, `no-useless-escape`, `no-prototype-builtins` |
| `tseslint.configs.recommended` | `@typescript-eslint/no-explicit-any`, `no-unused-vars` (TS version), `ban-ts-comment` (`@ts-ignore` forbidden, `@ts-expect-error` only with a description), `no-non-null-asserted-optional-chain`, `no-empty-object-type`, `no-require-imports`, `no-namespace`, `prefer-as-const`, `no-unused-expressions`, `no-unsafe-function-type`, `no-wrapper-object-types`; turns off `no-undef` in TS (`tsc` covers it) |
| `react-hooks` recommended | `rules-of-hooks` (hooks only at the top of a component/hook, never in an `if`/loop) |
| `react-hooks/exhaustive-deps: "error"` | every value used in `useEffect`/`useMemo`/`useCallback` is in the dependency array. Raised from `warn` to `error` |

### Size cap: `max-lines-per-function` 100

A function (component, hook) with more than **100 lines** in `src/`, not counting blank lines and
comments, is an error — the equivalent of the backend's 30, higher because JSX takes lines. It is
fixed by extracting components and **named hooks** (`useTimer`, `useAutosave`), never by
squeezing JSX into one line (prettier undoes that anyway).

### The project's rules (`no-restricted-syntax`)

Route rules:

| Selector | Message | Why |
|---|---|---|
| `useParams({ ... })` | Use the route file's own `Route.useParams()` | a hand-typed `useParams({from})` reads the sibling route and breaks only in production with "Invariant failed" (spec 06 §2) |
| `useSearch({ ... })` | Use the route file's own `Route.useSearch()` | same |

Reuse rules — what already has a component, helper or token is not rewritten by hand. Each group
has a single allowed file, the one that implements the thing:

| Group | Selector | Use instead | Allowed file | Why |
|---|---|---|---|---|
| `color` | a literal or template with `#rgb`/`#rrggbb`/`#rrggbbaa` | a token from `src/styles.css` (`text-error`, `bg-veil`) | `src/lib/palettes.ts` (**content** colors: skin, hair, confetti) | a fixed color does not follow the dark theme |
| `number` | `x.toLocaleString(...)` | `formatNumber`, `formatPercent`, `formatDateTime` | `src/lib/formatting.ts` | numbers/percentages formatted in several ways ("52.0%", "52%", "52,0%") |
| `sheet` | a string with `shadow-card` | `<Card>` or `SHEET_CLASS` | `src/components/ui/Card.tsx` | the card's class was copied in 27 files |
| `keyboard` | `addEventListener("keydown", ...)` | `useShortcuts(map, active)` | `src/lib/shortcuts.ts` | a hand-made shortcut does not ignore text fields and asks for a dependency `eslint-disable` |

A frontend bug or duplication that repeats becomes a `no-restricted-syntax` rule with a message
that says what to use instead and, when there is one, cites the spec.

### Components and helpers that exist so nothing is duplicated

Every project with a frontend has, in `src/components/ui/` and `src/components/States.tsx`:
`<Card>`/`CardHeader`/`CardBody`/`Section`, `<Button>` (action variants + `link` for a text
button + size `icon` for an icon-only button, which requires `aria-label`), `<QueryView
query={q}>{(data) => ...}</QueryView>` (loading, error with "try again" and data — no repeated
`isPending ? ... : isError ? ...` ternary), `<Loading>`, `<Empty>`, `<ErrorState>`, `<Modal>`,
`<Drawer>`, generic side panel and tree node when more than one screen uses them. In `src/lib/`:
`formatting.ts` (every number, percentage and date), `shortcuts.ts` (`useShortcuts`),
`palettes.ts` (content colors). A raw `<button>` only for a special control (option, selector,
cell).

### Patterns the lint enforces

- A callback used inside `useEffect` comes in through a `ref` (or `useEvent`), not the dependency
  array — otherwise the effect restarts on every render (a debounce that never fires).
- `eslint-disable-next-line react-hooks/exhaustive-deps` only with a comment above saying why the
  omitted dependency is stable (Crivo has two such cases).
- A query with a filter in its key does **not** use `placeholderData`; "keep the previous one
  while loading" is `isFetching` + the old list dimmed.

## 6. TypeScript (`tsc -b`)

| Option | Effect |
|---|---|
| `strict` | `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `useUnknownInCatchVariables`, `alwaysStrict` |
| `noUnusedLocals` / `noUnusedParameters` | an unused variable/parameter is an error (prefix `_` if intentional) |
| `noFallthroughCasesInSwitch` | a `case` without `break`/`return` is an error |
| `isolatedModules` | each file compiles alone (required by Vite/esbuild) |
| `noEmit` | `tsc` only checks; Vite generates the JS |
| `moduleResolution: "bundler"`, `allowImportingTsExtensions`, `resolveJsonModule` | resolution the way Vite does it |
| `skipLibCheck` | does not check dependencies' `.d.ts` |
| `types` | `vite/client`, `node`, `vitest/globals`, `@testing-library/jest-dom` |
| `include` | `src`, `tests`, `e2e` and the configs (`vite.config.ts`, `playwright.config.ts`, `eslint.config.js`) — tests and configs are checked too |

`npm run build` = `tsc -b && vite build`: no build comes out with a type error.

## 7. Prettier (frontend)

`web/.prettierrc.json`:

```json
{ "printWidth": 110, "semi": true, "singleQuote": false, "trailingComma": "all", "arrowParens": "always", "endOfLine": "lf" }
```

`printWidth` 110, the same as ruff's `line-length`. `.prettierignore`: `src/api/types.ts`
(generated), `dist`, `node_modules`, `captures`, `playwright-report`, `test-results`,
`coverage`, `package-lock.json`. Scripts: a format script (`prettier --write .`) and a format
check script (`prettier --check .`); the web format target fixes, the web test target and CI
check.
`eslint-config-prettier` is eslint's last item, so eslint does not fight prettier.

## 8. Backend × frontend contract

The web types target (in Crivo `make tipos-web`): `tools/openapi.py` writes `openapi.json`
(gitignored) from `create_app().openapi()`; `openapi-typescript` generates `web/src/api/types.ts`
(versioned, out of lint). CI regenerates it and fails on
`git diff --exit-code -- src/api/types.ts`. A field renamed in the backend breaks the frontend's
compilation.

---

## How to apply the lint to a project (and fix what it flags)

1. **Configure first, alone**: `pyproject.toml`, `eslint.config.js`, `tsconfig.json`, the
   function size tool, Makefile targets and CI. A configuration-only commit.
2. **Mechanical fix**: `ruff check --fix .`, `ruff format .`, `eslint --fix`. Commit.
3. **Measure what is left**, per check and per folder:
   ```bash
   uv run ruff check . --statistics
   uv run ruff check . --output-format=concise | cut -d: -f1 | sort | uniq -c | sort -rn
   uv run python -m tools.function_size | wc -l
   uv run mypy | tail -1
   cd web && npx eslint src tests e2e -f json | python3 -c 'import json,sys,collections; c=collections.Counter(f["filePath"] for f in json.load(sys.stdin) for m in f["messages"]); [print(n,f) for f,n in c.most_common()]'
   ```
4. **Decide the fixing mode** (below).
5. Each fix is a **refactoring without behavior change**; the area's tests must pass before and
   after.

### Turning on a new rule without breaking `main`: the `PENDING` list

A new rule that flags many files comes in already as an error, with the files that do not comply
yet in a temporary list that turns off only the new rules for them:

```js
// TEMPORARY (refactoring of YYYY-MM-DD): files that do not comply with the new rules yet.
// To check how a file will end up: `ESLINT_STRICT=1 npx eslint <file>`.
const PENDING = process.env.ESLINT_STRICT === "1" ? [] : ["src/routes/x.tsx", ...];
...(PENDING.length ? [{ files: PENDING, rules: { "max-lines-per-function": "off", "no-restricted-syntax": ["error", ...ROUTE_RULES] } }] : []),
```

A new file is born compliant; subagents check theirs with `ESLINT_STRICT=1` and **do not edit**
the list (it would be a conflict between all of them); the main agent deletes the whole list at
integration. The same idea applies to Python (temporary `per-file-ignores` with a comment).

### When to use multiple agents

If the fix is large — **more than ~15 files or more than ~50 occurrences** that `--fix` did not
solve, or if it spans more than one area (backend and frontend, or several packages) — **do not
fix it alone in sequence: split it between subagents in worktrees**.

- The main agent does steps 1–3 (configuration and `--fix` already committed on `main`), and
  only then splits the rest. Before splitting, it also creates and commits **what everyone will
  use**: base components and helpers (`<QueryView>`, `Button` variants, `formatPercent`), new
  tokens, the screen test helper (`tests/helpers/screen.tsx`). Otherwise each subagent invents
  its own and integration becomes a conflict.
- Write **one common context file** (rules, how to prepare the worktree, how to test, the report
  format) and give each subagent that file + the exact list of its files. A shared file someone
  needs to change (`ui/index.ts`, `styles.css`) has **one named owner**; the others note the
  request in their report.
- **Each subagent with its own test database** (`CREATE DATABASE <app>_test_<agent>` and the
  test database URL pointing to it, dropped at the end): the fixture that migrates runs
  `downgrade base` at the end of the session, and with two agents on the same database one drops
  the other's schema mid-suite — random failures that look like bugs and are not.
- A worktree has no `node_modules` nor `.venv`: `ln -s "$MAIN/web/node_modules" web/node_modules`
  and `uv sync`. Gitignored files the tests need (`.env`) are copied from the main checkout.
- **Partition by file, never by rule**: each subagent gets a disjoint set of folders/files (e.g.
  `api/modules/notices/`, `api/modules/flashcards/`, `pipeline/`, `web/src/routes/`,
  `web/src/components/`). Two agents never edit the same file. Changes to shared files
  (`pyproject.toml`, `conftest.py`, `deps.py`, `client.ts`) stay with the main agent.
- Each subagent (`Agent` with `isolation: "worktree"`): gets the exact list of occurrences in its
  slice, fixes without changing behavior, runs the lint **only for its slice** + the area's
  tests, and commits on the worktree branch with `refactor(<area>): ...` or `chore(lint): ...`.
- Launch all subagents in the same message (they run in parallel). Up to ~7 per round.
- The main agent integrates the branches one by one (merge or cherry-pick), runs **every** check
  on `main`, fixes conflicts or leftovers, deletes the `PENDING` list and updates `docs/system/`
  and `CLAUDE.md` from the reports (frontend subagents do not edit shared docs; the backend one
  edits its own domain's file).
- A small change (below the threshold) is done directly, without subagents.

This applies to any change of the standard applied to a project, not only lint.
