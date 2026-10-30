# CLAUDE.md — <Project>

<Two or three sentences: what the system is and the main design principle.>

This project follows the **`project-standard`** skill (`~/.claude/skills/project-standard/`).
A change to the standard (lint, tests, docker, CI, documentation) applies in both places: here and
in the skill.

## Documentation — read first, update together

- **`docs/system/`** explains the system as it is: one file per domain, index in
  `docs/system/README.md`. Before touching a domain, read its file.
- **Every change to the system updates the documentation in the same commit**: route, table,
  flow, rule, environment variable, new, removed or renamed file → the domain's file. New domain
  → new file + a line in the index.
- **Keep the `.md` files tidy**: when passing through a documentation file (including this
  `CLAUDE.md`, the `README.md` and the specs), fix what is outdated, duplicated or confusing,
  even if it is not part of the task.
- **This `CLAUDE.md` updates too**: new command, new convention, discovered pitfall, structure
  change → it goes here in the same commit.
- `specs/` is what was asked and why; divergence from the code is recorded in `docs/system/`.
- Guarantee: `make docs` (in CI).

## Language

- **The code is all in English**: identifiers, file and folder names, database tables and
  columns, API routes and fields, error types, comments, docstrings, documentation (`docs/`,
  specs, this file, README) and commit messages.
- **Only what a person reads in the product stays in <product language>**: interface text,
  error messages (`detail`), PDFs, e-mails; also the screen URLs, prompts to the language model
  that talk about documents in that language, and external data formats.
- **Every domain name comes from `docs/glossary.md`** (domain term in <product language> → name in
  code). A new term enters the glossary in the same commit that introduces it.
- **Never renamed**: environment variables configured on the server (the settings field may have
  another name and read the variable by alias, `Field(validation_alias="<VAR>")`; a new variable
  comes with a safe default or with a notice to the server owner listing what to configure), CLI
  commands and Makefile targets (only by agreement), past commits.
- <If the project is still being migrated: what is already in English, what is not, and the
  order of the migration.>

## Where things are

```
<root tree with one line per folder>
```

## Commands

`make` with no target lists everything.

| Command | Does |
|---|---|
| `make lint` | ruff + function size cap + import boundaries |
| `make format` | ruff format |
| `make types` | strict mypy |
| `make docs` | coverage and live paths of `docs/system/` |
| `make test` | pytest |
| `make web-test` | eslint + prettier check + tsc + vitest |
| <...> | <...> |

Tests for one area: `<command>`.

## Local environment

<Ports that belong to the user and must not be taken down, dev database, test accounts, what not
to run without asking.>

## Code rules

**Lint and types**: <summary; details in
`~/.claude/skills/project-standard/references/lint-and-types.md`>.

**Backend**: <layers, errors, settings, SQL, ...>

**Frontend**: <API client, generated types, hook rules, 390 px, ...>

## Tests

<Pyramid, main fixtures, the "a bug comes with a test" rule, known broken tests.>

## Workflow

1. Read the domain's `docs/system/` file.
2. Change + test + documentation (+ glossary if there is a new term).
3. Run only what you touched: `make lint types docs` + the area's tests.
4. Commit <and push> on <branch>; conventional commit in English describing the behavior.

**Large change** (more than ~15 files or more than one area): subagents in parallel by disjoint
files (worktrees when they edit existing code); the main agent integrates and verifies.

## Deploy

<Where and how; link to `docs/deploy-<paas>.md`, and the list of environment variables the
server must have.>
