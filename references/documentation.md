# Documentação do sistema

Todo projeto tem três camadas de texto, cada uma com um papel:

| Onde | Papel | Quando muda |
|---|---|---|
| `CLAUDE.md` (raiz) | instruções para quem mexe no código (pessoa ou agente): comandos, estrutura, regras, fluxo de trabalho, armadilhas do ambiente | comando, convenção, estrutura ou armadilha nova |
| `docs/sistema/` | **como o sistema funciona hoje**, um arquivo por domínio | **toda** mudança de comportamento, rota, tabela, fluxo, regra, variável ou arquivo |
| `specs/NN-nome.md` | o que foi pedido e por quê, antes de construir | spec nova; a antiga não é reescrita, a nova diz "isto altera a spec NN" |

Mais `README.md` (o que é, como rodar, tabela de specs, link para `docs/sistema/`) e
`docs/deploy-<paas>.md`.

## Regras

1. **Mudou o sistema, mudou a documentação, no mesmo commit.** Rota, tabela, fluxo, regra,
   variável de ambiente, arquivo novo/removido/renomeado → o arquivo do domínio em
   `docs/sistema/`. Domínio novo → arquivo novo + linha no índice.
2. **Ler antes de mexer.** Antes de alterar um domínio, ler o arquivo dele em `docs/sistema/`.
3. **Sempre arrumar o `.md`.** Ao passar por qualquer arquivo de documentação (inclusive
   `CLAUDE.md` e `README.md`), corrigir o que estiver desatualizado, duplicado ou confuso,
   mesmo fora da tarefa. Documentação errada é pior que ausente.
4. **O `CLAUDE.md` se atualiza também**: Makefile com alvo novo, convenção nova, armadilha
   descoberta → entra no mesmo commit.
5. **Código diverge da spec → `docs/sistema/` registra** em "Pontos de atenção" (a spec fica
   como histórico).
6. Prosa com acento; identificadores e caminhos exatamente como no código, entre crases,
   relativos à raiz.

## Garantia: `make docs`

`ferramentas/cobertura_da_documentacao.py` (modelo em `modelos/ferramentas/`), no `make docs`
e no CI, logo depois do tamanho de função:

- **DOC001 — sem documentação**: todo caminho casado por `exigir` precisa aparecer entre
  crases em algum `.md` de `docs/sistema/` (diretório conta se ele ou algo dentro aparece);
- **DOC002 — caminho morto**: todo caminho do repo citado entre crases existe, e todo
  `tests/x.py::nome` aponta para um `def nome` real. Glob, `<placeholder>` e `...` são
  ignorados.

```toml
[tool.cobertura-da-documentacao]
documentacao = "docs/sistema"
raizes = ["api", "pipeline", "web", "tests", "ferramentas", "migrations", "docker", "docs", "specs"]
exigir = [
    "api/routers/*.py",
    "api/services/*",
    "api/*/",
    "pipeline/*.py",
    "web/src/rotas/*.tsx",
]
```

Ajuste `exigir` às pastas de cada projeto: routers, services, pacotes, rotas do front.

## Estrutura de `docs/sistema/`

```
docs/sistema/
├── README.md        índice (Arquivo | Domínio | Spec) + o modelo abaixo + a regra de atualização
├── visao-geral.md   arquitetura, ciclo de vida, config, erros, log, banco, migrations, CLI, mapa dos domínios
├── <dominio>.md     um por domínio (agrupe domínios pequenos)
└── front.md         stack, rotas, cliente da API, hooks, componentes, identidade visual, testes
```

Modelo de cada arquivo de domínio (seção que não se aplica sai):

```markdown
# <Domínio>
Um parágrafo: o que é para quem usa e a spec de origem.
## Onde está          tabela Arquivo | Papel (back, pipeline, front, testes)
## Dados              tabelas e a migration que as criou; arquivos em disco; cache
## Rotas              tabela Método e caminho | O que faz | Erros (tipo do problem+json)
## Como funciona      fluxos principais, em ordem, com nome de função
## Regras e garantias cada invariante e o teste que a garante (`tests/x.py::nome`)
## Configuração       variáveis de ambiente do domínio
## Pontos de atenção  armadilhas, decisões não óbvias, divergências da spec
```

Tamanho: 100–300 linhas por arquivo, denso. Descreve o que o **código** faz.

## Criar a documentação num projeto que não tem

1. Escrever `docs/sistema/README.md` (índice com a partição em domínios + modelo) primeiro.
2. Escrever `visao-geral.md` e um arquivo por domínio. Com mais de ~4 domínios, **um
   subagente por grupo de domínios em paralelo** (arquivos novos e disjuntos, sem worktree):
   cada um recebe a lista exata de arquivos de código que cobre, lê o código (não só as
   specs), segue o modelo e não edita nada além dos seus `.md`.
3. Ligar `make docs` + CI, rodar, corrigir DOC001/DOC002.
4. Escrever ou atualizar o `CLAUDE.md` (modelo em `modelos/CLAUDE.md`) com a seção
   Documentação, e o `README.md` com o link para `docs/sistema/`.
5. Um commit `docs(sistema): ...`.
