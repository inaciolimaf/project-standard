# project-standard

A [Claude Code](https://code.claude.com) skill with an engineering standard for
**Python (FastAPI + uv) projects with a React (Vite + TypeScript) frontend**, extracted from a real
project:

- modular monolith structure (core, infra, modules with a public interface, events between
  modules);
- lint and types (ruff, strict mypy, cap of 30 lines per function and 300 per file, eslint,
  prettier, tsc), boundaries with `import-linter`, SQL only through the query builder;
- test pyramid (unit, integration with a real Postgres, golden, Vitest with minimum coverage,
  Playwright with real flows);
- Docker, local and production compose (Coolify), Makefile and CI;
- system documentation (`docs/system/` + `CLAUDE.md`) updated with every change, with a
  guarantee;
- code in English, product in its user's language, with a glossary between the two.

The entry point is [`SKILL.md`](SKILL.md); the details are in [`references/`](references/) and the
files ready to copy in [`templates/`](templates/).

## Install

For all your projects (personal skill):

```bash
git clone https://github.com/inaciolimaf/project-standard.git ~/.claude/skills/project-standard
```

For a single project (it goes along in that project's repository):

```bash
mkdir -p .claude/skills
git clone https://github.com/inaciolimaf/project-standard.git .claude/skills/project-standard
rm -rf .claude/skills/project-standard/.git
```

Update the personal one: `git -C ~/.claude/skills/project-standard pull`.

The repository used to be called `padrao-de-projeto`; GitHub redirects the old URL. If you cloned
it under the old name, move the folder so the skill is found by its new name:
`mv ~/.claude/skills/padrao-de-projeto ~/.claude/skills/project-standard`.

## Use

In Claude Code, ask something like "apply the project standard to this repository" (or, in
Portuguese, "aplica o padrão") or call `/project-standard`. The skill starts by auditing the
project and shows what is present, what is missing and what diverges before changing anything.
