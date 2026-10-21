# Lacunas conhecidas

O que o padrão ainda não cobre ou cobre de forma inconsistente, visto no Crivo em 2026-10-20.
Quando uma for resolvida, mova a decisão para a referência certa e apague daqui.

| # | Lacuna | Onde | Sugestão |
|---|---|---|---|
| 3 | Sem hook de pre-commit | raiz | `pre-commit` (ou `lefthook`) com ruff, tamanho de função, eslint |
| 5 | Sem cobertura mínima (`pytest-cov` instalado, sem `fail_under`) | `pyproject.toml` | `--cov` no CI com `fail_under` |
| 7 | `ghcr.io/astral-sh/uv:latest` sem versão fixa | `docker/api.Dockerfile` | fixar a versão do uv |
| 8 | Testes Python fora do mypy | `pyproject.toml` | decidir: incluir `tests` com overrides ou manter fora de propósito |
| 9 | Marker `integracao` existe mas não há alvo para rodar só unidade | `Makefile` | `teste-unidade: pytest -m "not integracao"` |
| 11 | Sem auditoria de dependências (`pip-audit`, `npm audit`) nem Dependabot | CI | job semanal |
