# Specs, idioma e commits

## Idioma

- **Tudo em português**: nomes de módulo, função, variável, fixture, alvo do Makefile, teste,
  mensagem de commit, spec. Termos técnicos sem tradução boa ficam em inglês (`router`,
  `schema`, `hook`, `token`).
- **Código sem acento** (identificadores, comentários e docstrings em `.py`/`.ts`:
  `nao`, `funcao`, `configuracao`). **Prosa com acento** (specs, README, docs, textos de UI).
- **Docstring de módulo só quando há algo que o caminho do arquivo e o código não dizem**: uma
  decisão, uma armadilha, um porquê (ex.: "o kernel e um laco plano de proposito: chamar funcao
  com array dentro do laco e 6x mais lento"). O que o módulo faz fica em `docs/sistema/`, não
  repetido no topo de cada arquivo.
- Comentário explica **por quê** (a armadilha, o número medido), não o quê.
- Não existem: separadores (`# -------`, `// ===== Secao =====`), cabeçalho de uma linha que só
  repete o caminho ou o nome do arquivo (`"""Rotas de cartoes."""` em `routers/cartoes.py`),
  `Revisao:`/`Anterior:` na docstring de migration (o Alembic já guarda em
  `revision`/`down_revision`). Se o arquivo precisa de separador, precisa ser dividido.
- Docstring de função/classe pública só quando o nome e os tipos não bastam (unidade, efeito
  colateral, invariante).

## Specs (`specs/NN-nome.md`)

- Numeradas na ordem de leitura; `00-visao-e-dominio.md` é o que o sistema é e a stack.
- Estrutura típica: parágrafo do que é → tabela **Decisões** (`Assunto | Decisão`) → seções
  numeradas (`## 1. ...`) com fluxo, dados, rotas, telas → custos/limites.
- Spec que altera outra diz explicitamente: "isto **altera a spec 04**, que dizia ...".
- Código e comentários citam a spec e a seção: `(spec 06 §2)`.
- Spec de lições/defeitos usa o formato **o que aconteceu → regra → garantia**; regra sem
  garantia (teste, lint, restrição de desenho) não entra.
- README tem a tabela `# | spec | o que decide`.

## Commits

Conventional commits em português, minúsculas, sem ponto final, descrevendo o
**comportamento** (o que muda para quem usa), não o arquivo:

```
feat(cartoes): suspender ou excluir o cartao tambem depois da resposta
fix(revisao): Bom num cartao novo agenda em dias, nao volta todo dia
perf(cartoes): ligacao das aulas com ate 64 chamadas ao modelo em paralelo
style(cartoes): prettier na lista de baralhos
docs(specs): spec 15, cartoes gerados por IA a partir do curso
chore: ignora o script.txt local
```

- Tipos: `feat`, `fix`, `perf`, `style`, `docs`, `chore`, `test`, `ci`, `refactor`.
- Escopo = domínio (`cartoes`, `editais`, `llm`, `web`, `deploy`), não pasta.
- Feature grande cita a spec: `(spec 15)`.
- Trabalho direto na `main`; um commit por mudança coerente.
- Antes de commitar: lint/tipos + testes da área mexida; a suíte completa é do CI.
