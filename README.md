# project-standard

[Claude Code](https://code.claude.com) skills with the engineering standards extracted from a real
project.

| Skill | Covers |
|---|---|
| [`project-standard`](skills/project-standard/SKILL.md) | Python (FastAPI + uv) with a React frontend: modular monolith, lint and types, test pyramid, Docker, Coolify, Makefile, CI, system documentation, language rule |
| [`frontend-standard`](skills/frontend-standard/SKILL.md) | React (Vite + TS + Tailwind v4 + TanStack) screens: visual identity, tokens, motion, accessibility, performance, CSS traps, and the lint and tests that guarantee them |
| [`test-speed`](skills/test-speed/SKILL.md) | Keeping the test suite and CI under 180 s: measure first, then cheap hashing in tests, pytest-xdist, Vitest threads, one e2e login, shards, parallel jobs, and the wall-clock gate |

Each skill works alone. They repeat the frontend basics on purpose; where they disagree on a frontend
subject, `frontend-standard` wins. `test-speed` owns how long the tests and CI take; `project-standard`
owns what they test.

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

Ask something like "apply the project standard to this repository", "aplica o padrão de front" or "reduz o
tempo dos testes", or call `/project-standard`, `/frontend-standard` or `/test-speed`. Each starts by auditing (or, for `test-speed`, measuring) and shows what is missing before
changing anything.
