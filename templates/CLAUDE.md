# CLAUDE.md — <Projeto>

<Duas ou três frases: o que o sistema é e o princípio de desenho principal.>

Este projeto segue a skill **`padrao-de-projeto`** (`~/.claude/skills/padrao-de-projeto/`).
Mudança de padrão (lint, testes, docker, CI, documentação) vale nos dois lugares: aqui e na skill.

## Documentação — leia antes, atualize junto

- **`docs/sistema/`** explica o sistema como ele está: um arquivo por domínio, índice em
  `docs/sistema/README.md`. Antes de mexer num domínio, leia o arquivo dele.
- **Toda mudança no sistema atualiza a documentação no mesmo commit**: rota, tabela, fluxo,
  regra, variável de ambiente, arquivo novo, removido ou renomeado → o arquivo do domínio.
  Domínio novo → arquivo novo + linha no índice.
- **Mantenha os `.md` arrumados**: ao passar por um arquivo de documentação (inclusive este
  `CLAUDE.md`, o `README.md` e as specs), corrija o que estiver desatualizado, duplicado ou
  confuso, mesmo que não seja da tarefa.
- **Este `CLAUDE.md` também se atualiza**: comando novo, convenção nova, armadilha descoberta,
  mudança de estrutura → entra aqui no mesmo commit.
- `specs/` é o que foi pedido e por quê; divergência do código fica registrada em `docs/sistema/`.
- Garantia: `make docs` (no CI).

## Onde as coisas estão

```
<árvore da raiz com uma linha por pasta>
```

## Comandos

`make` sem alvo lista tudo.

| Comando | Faz |
|---|---|
| `make lint` | ruff + teto de 30 linhas por função |
| `make formato` | ruff format |
| `make tipos` | mypy estrito |
| `make docs` | cobertura e caminhos vivos de `docs/sistema/` |
| `make teste` | pytest |
| `make web-teste` | eslint + vitest + tsc |
| <...> | <...> |

Teste de uma área: `<comando>`.

## Ambiente local

<Portas que são do usuário e não devem ser derrubadas, banco de dev, contas de teste, o que não
rodar sem pedir.>

## Regras do código

**Idioma**: <ex.: português; identificadores sem acento, prosa com acento>.

**Lint e tipos**: <resumo; detalhes em `~/.claude/skills/padrao-de-projeto/referencias/lint-e-tipos.md`>.

**Back**: <camadas, erros, config, SQL, ...>

**Front**: <cliente da API, tipos gerados, regras de hooks, 390 px, ...>

## Testes

<Pirâmide, fixtures principais, regra "bug vem com teste", testes conhecidamente quebrados.>

## Fluxo de trabalho

1. Leia o `docs/sistema/` do domínio.
2. Mudança + teste + documentação.
3. Rode só o que mexeu: `make lint tipos docs` + testes da área.
4. Commit <e push> em <branch>; conventional commit em português descrevendo o comportamento.

**Mudança grande** (mais de ~15 arquivos ou mais de uma área): subagentes em paralelo por
arquivos disjuntos (worktrees quando editam código existente); o principal integra e verifica.

## Deploy

<Onde e como; link para `docs/deploy-<paas>.md`.>
