# project-standard

[Claude Code](https://code.claude.com) skills with the engineering standards extracted from a real
project.

| Skill | Covers |
|---|---|
| [`project-standard`](skills/project-standard/SKILL.md) | Python (FastAPI + uv) with a React frontend: modular monolith, lint and types, test pyramid, Docker, Coolify, Makefile, CI, system documentation, language rule |
| [`frontend-standard`](skills/frontend-standard/SKILL.md) | React (Vite + TS + Tailwind v4 + TanStack) screens: visual identity, tokens, motion, accessibility, performance, CSS traps, and the lint and tests that guarantee them |

Each skill works alone. They repeat the frontend basics on purpose; where they disagree on a frontend
subject, `frontend-standard` wins.

## Install

Clone it anywhere and link each skill. Claude Code reads `~/.claude/skills/<name>/SKILL.md` and follows
symlinks:

```bash
git clone https://github.com/inaciolimaf/project-standard.git ~/code/project-standard
for s in ~/code/project-standard/skills/*/; do ln -s "$s" ~/.claude/skills/"$(basename "$s")"; done
```

Update with `git -C ~/code/project-standard pull`. A new skill needs its own link.

For a single project, copy the folders you want from `skills/` into its `.claude/skills/`.

**Moving from the old layout.** If `~/.claude/skills/project-standard` is the clone itself, move it out
and link it as above: the skill no longer sits at the root of the repository.

## Use

Ask something like "apply the project standard to this repository" or "aplica o padrão de front", or call
`/project-standard` or `/frontend-standard`. Both start by auditing and show what is missing before
changing anything.
