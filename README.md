# padrao-de-projeto

Skill do [Claude Code](https://code.claude.com) com um padrão de engenharia para projetos
**Python (FastAPI + uv) com front React (Vite + TypeScript)**, extraído de um projeto real:

- estrutura em monólito modular (núcleo, infra, módulos com interface pública, eventos entre módulos);
- lint e tipos (ruff, mypy estrito, teto de 30 linhas por função e 300 por arquivo, eslint, prettier,
  tsc), fronteiras com `import-linter`, SQL só pelo query builder;
- pirâmide de testes (unidade, integração com Postgres real, dourados, Vitest com cobertura mínima,
  Playwright com fluxos de verdade);
- Docker, compose local e de produção (Coolify), Makefile e CI;
- documentação do sistema (`docs/sistema/` + `CLAUDE.md`) atualizada a cada mudança, com garantia.

O ponto de entrada é o [`SKILL.md`](SKILL.md); os detalhes estão em [`referencias/`](referencias/)
e os arquivos prontos para copiar em [`modelos/`](modelos/).

## Instalar

Para todos os seus projetos (skill pessoal):

```bash
git clone https://github.com/inaciolimaf/padrao-de-projeto.git ~/.claude/skills/padrao-de-projeto
```

Só para um projeto (vai junto no repositório dele):

```bash
mkdir -p .claude/skills
git clone https://github.com/inaciolimaf/padrao-de-projeto.git .claude/skills/padrao-de-projeto
rm -rf .claude/skills/padrao-de-projeto/.git
```

Atualizar a pessoal: `git -C ~/.claude/skills/padrao-de-projeto pull`.

## Usar

No Claude Code, peça algo como "aplica o padrão de projeto neste repositório" ou chame
`/padrao-de-projeto`. A skill começa auditando o projeto e mostra o que está, o que falta e o que
diverge antes de mudar qualquer coisa.
