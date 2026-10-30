# Specs, language and commits

## Language

**The code is all in English.** That means identifiers, file and folder names, database tables
and columns, API routes and fields, error types (`domain/reason`), comments, docstrings,
documentation (`docs/`, specs, `CLAUDE.md`, README) and commit messages.

**Only what a person reads in the product stays in the product's language** (for Crivo,
Portuguese):

- the interface (labels, toasts, empty states), error messages (`detail` of the problem+json),
  PDFs, e-mails;
- the URLs of the screens (`/questoes`, `/simulados`): the user sees and shares them;
- prompts sent to the language model when they talk about documents in that language;
- external data formats (a third party's file layout and JSON keys, a scraped site).

Product text keeps its accents (`"Questão anulada"`, a product text example); code needs none
because it is in English.

### Glossary (`docs/glossary.md`)

The project keeps a **glossary**: domain term in the product's language → name in code, in
tables by area. **Every domain name comes from it**: a new term enters the glossary in the same
commit that introduces it. Without it, the same concept gets three English names in three
modules (`notice`, `edict`, `announcement`). The top of the glossary states the naming
conventions (Python `snake_case`/`PascalCase`, TypeScript `camelCase`/`PascalCase`, plural
`snake_case` tables, `kebab-case` plural routes) and lists what stays in the product's language
on purpose. Crivo's glossary is the example.

### What is never rewritten or renamed

- **Commits already made are not rewritten** (their messages stay in whatever language they
  were written in).
- **Environment variables configured on a server and commands people type** (CLI, Makefile
  targets) keep their names — see the operations rule in `SKILL.md`. In Crivo, `make teste`,
  `crivo ingestao rodar` and `SEGREDO_JWT` stay as they are.

### Migrating an existing project

The order is in `SKILL.md` → "How to apply it to a project", step 6. The rules:

1. **Glossary first**, reviewed by the user: it is the contract every agent follows.
2. **The database is renamed by migration, preserving data** (`op.rename_table`,
   `op.alter_column(new_column_name=...)`, indexes, sequences and constraints included); never
   drop and recreate. The migration's `downgrade` renames back, and the integration suite runs
   both ways.
3. **The API changes together with the frontend**, in the same deploy: routes, JSON fields and
   problem types renamed in the backend, the frontend types regenerated from the new OpenAPI,
   and the compiler shows every place to fix. Screen URLs do not change.
4. **What has an outside consumer does not change without agreement**: a public API, webhooks,
   files other systems read, values stored in users' browsers (`localStorage` keys), the
   variables on the server, the commands people type.
5. Structure and contract by a single agent (renaming in parallel while names are moving is a
   guaranteed conflict); after that, internal names, comments and tests in parallel by module.

### Comments and docstrings

- **A module docstring only when there is something the file path and the code do not say**: a
  decision, a pitfall, a why (e.g. "the kernel is a flat loop on purpose: calling a function with
  an array inside the loop is 6x slower"). What the module does belongs in `docs/system/`, not
  repeated at the top of each file.
- A comment explains **why** (the pitfall, the measured number), not what.
- These do not exist: separators (`# -------`, `// ===== Section =====`), a one-line header that
  only repeats the file path or name (`"""Flashcard routes."""` in `flashcards/routes.py`),
  `Revision:`/`Previous:` in a migration docstring (Alembic already keeps them in
  `revision`/`down_revision`). If the file needs a separator, it needs to be split.
- A docstring on a public function/class only when the name and the types are not enough (unit,
  side effect, invariant).

## Specs (`specs/NN-name.md`)

- Numbered in reading order; `00-vision-and-domain.md` is what the system is and the stack.
- Typical structure: a paragraph of what it is → a **Decisions** table (`Subject | Decision`) →
  numbered sections (`## 1. ...`) with flow, data, routes, screens → costs/limits.
- A spec that alters another says so explicitly: "this **alters spec 04**, which said ...".
- Code and comments cite the spec and the section: `(spec 06 §2)`.
- A lessons/defects spec uses the format **what happened → rule → guarantee**; a rule without a
  guarantee (test, lint, design constraint) does not get in.
- The README has the table `# | spec | what it decides`.

## Commits

Conventional commits in English, lowercase, no final period, describing the **behavior** (what
changes for whoever uses it), not the file:

```
feat(flashcards): suspend or delete the card also after the answer
fix(review): Good on a new card schedules in days instead of every day
perf(flashcards): lesson linking with up to 64 model calls in parallel
style(flashcards): prettier on the deck list
docs(specs): spec 15, AI-generated flashcards from the course
chore: ignore the local script.txt
```

- Types: `feat`, `fix`, `perf`, `style`, `docs`, `chore`, `test`, `ci`, `refactor`.
- Scope = domain (`flashcards`, `notices`, `llm`, `web`, `deploy`), not folder.
- A large feature cites the spec: `(spec 15)`.
- Work directly on `main`; one commit per coherent change.
- Before committing: lint/types + tests of the area you touched; the full suite is CI's job.
