# System documentation

Every project has three layers of text, each with a role:

| Where | Role | When it changes |
|---|---|---|
| `CLAUDE.md` (root) | instructions for whoever touches the code (person or agent): commands, structure, rules, workflow, environment pitfalls | a new command, convention, structure or pitfall |
| `docs/system/` | **how the system works today**, one file per domain | **every** change of behavior, route, table, flow, rule, variable or file |
| `specs/NN-name.md` | what was asked and why, before building | a new spec; the old one is not rewritten, the new one says "this alters spec NN" |

Plus `docs/glossary.md` (domain term in the product's language → name in code, see
`specs-and-commits.md`), `README.md` (what it is, how to run, specs table, link to
`docs/system/`) and `docs/deploy-<paas>.md`. All of it in English.

## Rules

1. **The system changed, the documentation changes, in the same commit.** Route, table, flow,
   rule, environment variable, new/removed/renamed file → the domain's file in `docs/system/`.
   New domain → new file + a line in the index. New domain term → a line in the glossary.
2. **Read before touching.** Before changing a domain, read its file in `docs/system/`.
3. **Always tidy the `.md`.** When passing through any documentation file (including
   `CLAUDE.md` and `README.md`), fix what is outdated, duplicated or confusing, even outside the
   task. Wrong documentation is worse than none.
4. **`CLAUDE.md` updates too**: a Makefile target, a new convention, a discovered pitfall → it
   goes in the same commit.
5. **Code diverges from the spec → `docs/system/` records it** under "Points of attention" (the
   spec stays as history).
6. Identifiers and paths exactly as in the code, between backticks, relative to the root.
   Product text quoted in the docs (a button label, an error `detail`) stays in the product's
   language.

## Guarantee: `make docs`

`tools/docs_coverage.py` (template in `templates/tools/`), in `make docs` and in CI, right after
the function size check:

- **DOC001 — undocumented**: every path matched by `require` must appear between backticks in
  some `.md` of `docs/system/` (a directory counts if it or something inside it appears);
- **DOC002 — dead path**: every repository path cited between backticks exists, and every
  `tests/x.py::name` points to a real `def name`. Globs, `<placeholder>` and `...` are ignored.

```toml
[tool.docs-coverage]
docs = "docs/system"
roots = ["api", "pipeline", "web", "tests", "tools", "migrations", "docker", "docs", "specs"]
require = [
    "api/modules/*/",
    "api/infra/*/",
    "api/core/*.py",
    "pipeline/*.py",
    "web/src/routes/*.tsx",
]
```

Adjust `require` to each project's folders: modules, infra packages, pipeline, frontend routes.

## Structure of `docs/system/`

```
docs/system/
├── README.md        index (File | Domain | Spec) + the template below + the update rule
├── overview.md      architecture, lifecycle, settings, errors, logging, database, migrations, CLI, domain map
├── <domain>.md      one per domain (group small domains)
└── frontend.md      stack, routes, API client, hooks, components, visual identity, tests
```

Template for each domain file (a section that does not apply is dropped):

```markdown
# <Domain>
One paragraph: what it is for whoever uses it and the spec it came from.
## Where it is         table File | Role (backend, pipeline, frontend, tests)
## Data                tables and the migration that created them; files on disk; cache
## Routes              table Method and path | What it does | Errors (problem+json type)
## How it works        main flows, in order, with function names
## Rules and guarantees each invariant and the test that guarantees it (`tests/x.py::name`)
## Settings            the domain's environment variables
## Points of attention pitfalls, non-obvious decisions, divergences from the spec
```

Size: 100–300 lines per file, dense. It describes what the **code** does.

## Creating the documentation in a project that has none

1. Write `docs/system/README.md` (index with the partition into domains + template) first.
2. Write `overview.md` and one file per domain. With more than ~4 domains, **one subagent per
   group of domains in parallel** (new, disjoint files, no worktree): each one gets the exact
   list of code files it covers, reads the code (not just the specs), follows the template and
   edits nothing besides its own `.md` files.
3. Wire `make docs` + CI, run it, fix DOC001/DOC002.
4. Write the glossary (`docs/glossary.md`) from the domain terms that appeared.
5. Write or update `CLAUDE.md` (template in `templates/CLAUDE.md`) with the Documentation and
   Language sections, and `README.md` with the link to `docs/system/`.
6. One commit `docs(system): ...`.
