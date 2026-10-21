# Lint, formatação e tipos

Oito verificações, todas bloqueiam o CI:

| # | Verificação | Lado | Comando local | O que pega |
|---|---|---|---|---|
| 1 | `ruff check` | Python | `make lint` | bugs prováveis, segurança, estilo, imports, anotações |
| 2 | `ruff format --check` | Python | `make formato` (corrige) | formatação |
| 3 | `tamanho_de_funcao` | Python | `make lint` | função com mais de 30 linhas úteis |
| 4 | `mypy --strict` | Python | `make tipos` | tipos |
| 5 | `eslint` | front | `make web-teste` | bugs de JS/TS, hooks, componente > 100 linhas, reuso (cor, número, folha, teclado), rotas |
| 6 | `prettier --check` | front | `make web-formato` (corrige) | formatação |
| 7 | `tsc -b` (strict) | front | `make web-teste` | tipos |
| 8 | `make docs` | docs | `make docs` | documentação cobre o código e não cita o que sumiu (`documentacao.md`) |
| 9 | `lint-imports` | Python | `make lint` | fronteira entre módulos e camadas (`estrutura.md`) |

Mais o contrato back × front (tipos do front gerados do OpenAPI, §8) e a cobertura mínima de
testes do front (60%, em `testes.md`).

**Regra de exceção (vale para as seis):** toda exceção tem o motivo escrito ao lado.
- Arquivo inteiro: `per-file-ignores` / `[[tool.mypy.overrides]]` / `ignorar` do tamanho de
  função, com comentário na linha de cima.
- Uma linha: `# noqa: S608 - nome de tabela fixo`, `# type: ignore[attr-defined]`,
  `// eslint-disable-next-line regra` com um comentário de uma linha acima explicando.
- Nunca `# noqa` sem código, `# type: ignore` sem código, nem `eslint-disable` de arquivo.

---

## 1. ruff check

```toml
[tool.ruff]
line-length = 110
target-version = "py312"
src = ["."]
exclude = ["web", "migrations/versions", <dados grandes: "acervo", "cache">]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "SIM", "RUF", "ANN", "S", "PLR0913"]
ignore = ["N818", "ANN401", "RUF001", "RUF002", "RUF003", "RUF012", "S101", "S311"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S", "ANN", "PLR0913", "E501"]

[tool.ruff.lint.pylint]
max-args = 7

[tool.ruff.lint.isort]
known-first-party = ["api", "pipeline", "tests", "ferramentas"]
```

`migrations/versions` fica de fora porque é gerado pelo Alembic e nunca mais editado; `web`
tem o próprio lint.

### Grupos ligados

| Código | Plugin | O que garante | Exemplos do que acusa |
|---|---|---|---|
| **E** | pycodestyle (erros) | estilo PEP 8 que o formatador não resolve | `E501` linha > 110, `E402` import fora do topo, `E711` `== None`, `E722` `except:` sem tipo, `E741` nome ambíguo (`l`, `O`) |
| **W** | pycodestyle (avisos) | espaço em branco | `W291` espaço no fim da linha, `W605` escape inválido em string |
| **F** | pyflakes | erros reais | `F401` import não usado, `F811` redefinição, `F821` nome indefinido, `F841` variável atribuída e não usada, `F541` f-string sem placeholder |
| **I** | isort | ordem de import estável (stdlib, terceiros, primeira parte, separados) | `I001` bloco fora de ordem — `ruff check --fix` resolve |
| **N** | pep8-naming | nomes | `N802` função não-snake_case, `N801` classe não-CapWords, `N806` variável maiúscula dentro de função |
| **UP** | pyupgrade | sintaxe da versão-alvo | `UP006` `List[int]` → `list[int]`, `UP007` `Optional[X]` → `X \| None`, `UP035` import de `typing` obsoleto |
| **B** | flake8-bugbear | armadilhas | `B006` default mutável (`def f(x=[])`), `B008` chamada em default de argumento, `B904` `raise` dentro de `except` sem `from`, `B007` variável de laço não usada, `B023` closure capturando variável de laço |
| **A** | flake8-builtins | não sombrear builtin | variável/argumento chamado `id`, `type`, `list`, `input`, `filter` |
| **C4** | flake8-comprehensions | comprehensions idiomáticas | `C400` `list(x for x in y)`, `C408` `dict()` em vez de `{}`, `C416` comprehension desnecessária |
| **SIM** | flake8-simplify | código mais simples | `SIM102` `if` aninhado que vira `and`, `SIM108` ternário, `SIM117` `with` aninhado, `SIM118` `key in d.keys()` |
| **RUF** | regras do ruff | diversas | `RUF005` concatenação de lista vira unpack, `RUF010` conversão explícita em f-string, `RUF100` `noqa` inútil |
| **ANN** | flake8-annotations | toda função com argumentos e retorno anotados (casa com o mypy estrito) | `ANN001` argumento sem tipo, `ANN201` retorno sem tipo |
| **S** | flake8-bandit | segurança | `S608` SQL montado com f-string, `S105/S106` senha literal, `S307` `eval`, `S603/S607` subprocess, `S113` request sem timeout, `S324` hash fraco |
| **PLR0913** | pylint | no máximo **7 argumentos** (`max-args = 7`) | função com 8+ parâmetros — agrupe num dataclass/DTO |

### Ignorados de propósito

| Código | Por que fica desligado |
|---|---|
| `N818` | exige que exceção termine em `Error`; o código é em português (`ErroDeAplicacao`) |
| `ANN401` | proíbe `Any`; às vezes é a anotação honesta (structlog, JSON cru). O mypy estrito ainda cobra o resto |
| `RUF001/002/003` | caractere ambíguo em string/docstring/comentário; texto em português tem `–`, `—`, `×`, aspas tipográficas |
| `RUF012` | atributo de classe mutável sem `ClassVar`; choca com `model_config` do pydantic e `__table_args__` do SQLAlchemy |
| `S101` | proíbe `assert`; `assert` é usado para invariantes e para estreitar tipo |
| `S311` | `random` não-criptográfico; serve para sorteio de questões. Token/segredo usa `secrets` |

### Nos testes (`tests/**`)

Desligados: `S` (senha literal e `assert` são normais em teste), `ANN` (fixture e teste sem
anotação), `PLR0913` (teste recebe muitas fixtures), `E501` (dados longos inline).

### Exceções do Crivo (exemplos do formato certo)

```toml
# Reaproveita as fixtures de test_editais importando-as: o pytest injeta pelo nome do parametro.
"tests/integracao/test_indice.py" = ["F811"]
# O kernel numba recebe dezenas de arrays soltos de proposito (namedtuple no laco e 40x mais lento).
"api/indice/kernel.py" = ["ANN001", "ANN202", "PLR0913"]
"pipeline/ingestao/banco.py" = ["S608"]
```

Por linha: `# noqa: S608 - nome de tabela fixo` (SQL com nome de tabela de uma lista fechada —
o valor do usuário vai sempre por parâmetro `$1`/`?`).

### Padrões de código que o lint força

- **FastAPI**: dependências e parâmetros por `Annotated` (`SessaoBd = Annotated[AsyncSession,
  Depends(sessao)]` em `api/deps.py`), nunca `x = Depends(...)` no default — senão `B008`.
- **`raise ... from erro`** dentro de `except` (`B904`).
- **Muitos argumentos** viram dataclass ou DTO, não `noqa`.
- **SQL**: valor sempre por parâmetro; f-string só para identificador de lista fechada, com
  `noqa: S608` e motivo.

## 2. ruff format

Estilo do ruff (compatível com black) com `line-length = 110`. `make formato` aplica; CI roda
`ruff format --check .`. Não se discute formatação em revisão.

## 3. Teto de tamanho de função (`ferramentas/tamanho_de_funcao.py`)

O ruff não tem essa regra (`PLR0915` conta *statements*, não linhas). Modelo pronto em
`modelos/ferramentas/tamanho_de_funcao.py`.

- Máximo **30 linhas úteis**. Útil = entre o primeiro comando do corpo e o fim, sem linha em
  branco, comentário ou docstring — comentário e docstring são incentivados, não punidos.
- Assinatura e decorador não contam (o tamanho da assinatura já é cobrado pelo `PLR0913`).
- Função aninhada conta sozinha **e** dentro da externa (closure grande pesa na de fora).
- Saída: `api/x.py:42: FN001 \`nome\` tem 37 linhas uteis (maximo 30)`, ordenada da maior
  para a menor; sai com 1 se achar algo.

```toml
[tool.tamanho-de-funcao]
max-linhas = 30
caminhos = ["api", "pipeline", "ferramentas"]
# O kernel numba e um laco plano de proposito: cada chamada de funcao com array dentro do laco paga
# incremento e decremento da contagem de referencia (e disputa entre threads), 6x mais lento.
ignorar = ["api/indice/kernel.py"]
```

Como corrigir: extrair etapas com nome (`_validar`, `_montar`, `_gravar`), não comprimir linhas.
Testes não passam por essa regra.

### Teto de tamanho de arquivo: 300 linhas

A mesma ferramenta mede o **arquivo**: no máximo **300 linhas** (código FN002), contando como no
de função (sem linha em branco, comentário e docstring). Módulo que passa é dividido por
responsabilidade (`servico.py` → `servico/criar.py`, `servico/responder.py`; `modelos.py` de
1.200 linhas → um `modelos.py` por módulo). Config: `max-linhas-arquivo = 300` em
`[tool.tamanho-de-funcao]`; arquivos ainda por dividir em `ignorar-arquivo-temporario` (com
comentário e data), e `TAMANHO_ESTRITO=1` ignora essa lista para conferir o alvo. No front, `max-lines` 300 (`skipBlankLines`, `skipComments`) no eslint.

## 4. mypy

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["api", "pipeline", "ferramentas"]
plugins = ["pydantic.mypy"]
warn_unreachable = true

[[tool.mypy.overrides]]
module = ["fsrs.*", "jose.*", "testcontainers.*", ...]   # libs sem tipos
ignore_missing_imports = true
```

`strict` liga: `disallow_untyped_defs`, `disallow_incomplete_defs`,
`disallow_untyped_calls`, `disallow_untyped_decorators`, `disallow_any_generics`
(`list` sem parâmetro), `no_implicit_optional`, `warn_return_any`, `warn_unused_ignores`,
`warn_redundant_casts`, `strict_equality`, `check_untyped_defs`, `no_implicit_reexport`.
`warn_unreachable` acusa código morto depois de estreitamento de tipo.

- Plugin pydantic: o mypy entende os campos e o `__init__` dos modelos.
- Lib sem tipos: primeiro procure stub (`types-*`, `asyncpg-stubs`) no grupo dev; só se não
  houver, `ignore_missing_imports` no override.
- Módulo que não dá para tipar (ex.: kernel numba): override do módulo desligando só o
  necessário, com comentário.
- Testes **não** passam pelo mypy (decisão atual; ver lacunas).
- `# type: ignore[codigo]` sempre com código; `warn_unused_ignores` acusa os que sobraram.

## 5. eslint (front, flat config)

Modelo completo: `web/eslint.config.js` do Crivo. Estrutura:

```js
import prettier from "eslint-config-prettier";
const DE_ROTA = [/* useParams({from}), useSearch({from}) */];
const DE_REUSO = { cor: [...], numero: [...], folha: [...], teclado: [...] };   // tabela abaixo
/** As regras de sintaxe de `src/`, menos as do grupo que o arquivo implementa. */
function sintaxe(...liberados) { /* DE_ROTA + grupos de DE_REUSO fora de `liberados` */ }

export default tseslint.config(
  { ignores: ["dist", "node_modules", "src/api/tipos.ts", "capturas", "playwright-report", "test-results", "coverage"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  { files: ["**/*.{ts,tsx}"], plugins: { "react-hooks": reactHooks },
    rules: { ...reactHooks.configs.recommended.rules, "react-hooks/exhaustive-deps": "error",
             "no-restricted-syntax": ["error", ...DE_ROTA] } },
  { files: ["src/**/*.{ts,tsx}"],
    rules: { "max-lines-per-function": ["error", { max: 100, skipBlankLines: true, skipComments: true }],
             "no-restricted-syntax": sintaxe() } },
  // cada grupo de reuso tem UM arquivo liberado: o que implementa a coisa
  { files: ["src/lib/formatacao.ts"], rules: { "no-restricted-syntax": sintaxe("numero") } },
  { files: ["src/components/ui/Card.tsx"], rules: { "no-restricted-syntax": sintaxe("folha") } },
  { files: ["src/lib/atalhos.ts"], rules: { "no-restricted-syntax": sintaxe("teclado") } },
  { files: ["src/lib/paletas.ts"], rules: { "no-restricted-syntax": sintaxe("cor") } },
  prettier,   // por ultimo: desliga regra de estilo que conflita com o prettier
);
```

`npm run lint` = `eslint src tests e2e`. Ignora o build, o arquivo gerado (`tipos.ts`), os
artefatos do Playwright e o relatório de cobertura. Testes e e2e ficam fora do teto de linhas e
das regras de reuso (um `describe` é longo por natureza).

| Conjunto | O que traz (principais) |
|---|---|
| `js.configs.recommended` | `no-unused-vars`, `no-undef`, `no-unreachable`, `no-constant-condition`, `no-dupe-keys`, `no-empty`, `no-fallthrough`, `no-cond-assign`, `no-debugger`, `no-self-assign`, `no-case-declarations`, `no-useless-escape`, `no-prototype-builtins` |
| `tseslint.configs.recommended` | `@typescript-eslint/no-explicit-any`, `no-unused-vars` (versão TS), `ban-ts-comment` (`@ts-ignore` proibido, `@ts-expect-error` só com descrição), `no-non-null-asserted-optional-chain`, `no-empty-object-type`, `no-require-imports`, `no-namespace`, `prefer-as-const`, `no-unused-expressions`, `no-unsafe-function-type`, `no-wrapper-object-types`; desliga `no-undef` em TS (o `tsc` cobre) |
| `react-hooks` recommended | `rules-of-hooks` (hook só no topo de componente/hook, nunca em `if`/laço) |
| `react-hooks/exhaustive-deps: "error"` | todo valor usado em `useEffect`/`useMemo`/`useCallback` está no array de dependências. Subido de `warn` para `error` |

### Teto de tamanho: `max-lines-per-function` 100

Função (componente, hook) com mais de **100 linhas** em `src/`, sem contar linha em branco e
comentário, é erro — o equivalente do teto de 30 do back, mais alto porque JSX ocupa linha.
Corrige-se extraindo componentes e **hooks com nome** (`useCronometro`, `useRascunhoAutomatico`),
nunca espremendo JSX numa linha (o prettier desfaz isso de qualquer jeito).

### Regras do projeto (`no-restricted-syntax`)

De rota:

| Seletor | Mensagem | Por quê |
|---|---|---|
| `useParams({ ... })` | Use `Route.useParams()` do próprio arquivo de rota | `useParams({from})` digitado à mão lê a rota irmã e quebra só em produção com "Invariant failed" (spec 06 §2) |
| `useSearch({ ... })` | Use `Route.useSearch()` do próprio arquivo de rota | idem |

De reuso — o que já tem componente, helper ou token não é reescrito à mão. Cada grupo tem um
único arquivo liberado, o que implementa a coisa:

| Grupo | Seletor | Use em vez disso | Arquivo liberado | Por quê |
|---|---|---|---|---|
| `cor` | literal ou template com `#rgb`/`#rrggbb`/`#rrggbbaa` | token de `src/estilos.css` (`text-erro`, `bg-veu`) | `src/lib/paletas.ts` (cor de **conteúdo**: pele, cabelo, confete) | cor fixa não acompanha o tema escuro |
| `numero` | `x.toLocaleString(...)` | `formatarNumero`, `formatarPercentual`, `formatarDataHora` | `src/lib/formatacao.ts` | número/porcentagem formatados de vários jeitos ("52.0%", "52%", "52,0%") |
| `folha` | string com `shadow-card` | `<Card>` ou `CLASSE_DA_FOLHA` | `src/components/ui/Card.tsx` | a classe do cartão estava copiada em 27 arquivos |
| `teclado` | `addEventListener("keydown", ...)` | `useAtalhos(mapa, ativo)` | `src/lib/atalhos.ts` | atalho à mão não ignora campo de texto e pede `eslint-disable` de dependência |

Bug ou duplicação de front que se repete vira regra `no-restricted-syntax` com mensagem que diz
o que usar no lugar e, quando houver, cita a spec.

### Componentes e helpers que existem para não duplicar

Todo projeto com front tem, em `src/components/ui/` e `src/components/Estados.tsx`:
`<Card>`/`CardCabecalho`/`CardCorpo`/`Secao`, `<Botao>` (variantes de ação + `link` para botão de
texto + tamanho `icone` para botão só com ícone, que exige `aria-label`), `<Consulta query={q}>
{(dados) => ...}</Consulta>` (carregando, erro com "Tentar de novo" e dados — nada de ternário
`isPending ? ... : isError ? ...` repetido), `<Carregando>`, `<Vazio>`, `<Erro>`, `<Modal>`,
`<Gaveta>`, painel lateral e nó de árvore genéricos quando houver mais de uma tela usando. Em
`src/lib/`: `formatacao.ts` (todo número, porcentagem e data), `atalhos.ts` (`useAtalhos`),
`paletas.ts` (cores de conteúdo). Botão cru (`<button>`) só para controle especial (alternativa,
seletor, célula).

### Padrões que o lint força

- Callback usado dentro de `useEffect` entra por `ref` (ou `useEvent`), não pelo array de
  dependências — senão o efeito reinicia a cada render (debounce que nunca dispara).
- `eslint-disable-next-line react-hooks/exhaustive-deps` só com comentário acima dizendo por
  que a dependência omitida é estável (o Crivo tem dois casos assim).
- Consulta com filtro na chave **não** usa `placeholderData`; "manter o anterior enquanto
  carrega" é `isFetching` + lista antiga escurecida.

## 6. TypeScript (`tsc -b`)

| Opção | Efeito |
|---|---|
| `strict` | `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `useUnknownInCatchVariables`, `alwaysStrict` |
| `noUnusedLocals` / `noUnusedParameters` | variável/parâmetro sem uso é erro (prefixe `_` se for proposital) |
| `noFallthroughCasesInSwitch` | `case` sem `break`/`return` é erro |
| `isolatedModules` | cada arquivo compila sozinho (exigência do Vite/esbuild) |
| `noEmit` | o `tsc` só checa; quem gera o JS é o Vite |
| `moduleResolution: "bundler"`, `allowImportingTsExtensions`, `resolveJsonModule` | resolução como o Vite faz |
| `skipLibCheck` | não checa `.d.ts` de dependências |
| `types` | `vite/client`, `node`, `vitest/globals`, `@testing-library/jest-dom` |
| `include` | `src`, `tests`, `e2e` e os configs (`vite.config.ts`, `playwright.config.ts`, `eslint.config.js`) — teste e config também são checados |

`npm run build` = `tsc -b && vite build`: build não sai com erro de tipo.

## 7. Prettier (front)

`web/.prettierrc.json`:

```json
{ "printWidth": 110, "semi": true, "singleQuote": false, "trailingComma": "all", "arrowParens": "always", "endOfLine": "lf" }
```

`printWidth` 110, o mesmo `line-length` do ruff. `.prettierignore`: `src/api/tipos.ts` (gerado),
`dist`, `node_modules`, `capturas`, `playwright-report`, `test-results`, `coverage`,
`package-lock.json`. Scripts: `formato` (`prettier --write .`) e `formato:checar`
(`prettier --check .`); `make web-formato` corrige, `make web-teste` e o CI conferem.
`eslint-config-prettier` é o último item do eslint, para o eslint não brigar com o prettier.

## 8. Contrato back × front

`make tipos-web`: `ferramentas/openapi.py` escreve `openapi.json` (gitignored) de
`criar_app().openapi()`; `openapi-typescript` gera `web/src/api/tipos.ts` (versionado, fora do
lint). O CI regenera e falha em `git diff --exit-code -- src/api/tipos.ts`. Campo renomeado no
back quebra a compilação do front.

---

## Como aplicar o lint num projeto (e corrigir o que ele acusar)

1. **Configurar primeiro, sozinho**: `pyproject.toml`, `eslint.config.js`, `tsconfig.json`,
   ferramenta de tamanho de função, alvos do Makefile e CI. Um commit só de configuração.
2. **Correção mecânica**: `ruff check --fix .`, `ruff format .`, `eslint --fix`. Commit.
3. **Medir o que sobrou**, por verificação e por pasta:
   ```bash
   uv run ruff check . --statistics
   uv run ruff check . --output-format=concise | cut -d: -f1 | sort | uniq -c | sort -rn
   uv run python -m ferramentas.tamanho_de_funcao | wc -l
   uv run mypy | tail -1
   cd web && npx eslint src tests e2e -f json | python3 -c 'import json,sys,collections; c=collections.Counter(f["filePath"] for f in json.load(sys.stdin) for m in f["messages"]); [print(n,f) for f,n in c.most_common()]'
   ```
4. **Decidir o modo de correção** (abaixo).
5. Cada correção é **refatoração sem mudar comportamento**; os testes da área têm que passar
   antes e depois.

### Ligar regra nova sem quebrar a `main`: a lista `PENDENTES`

Regra nova que acusa muitos arquivos entra já como erro, com os arquivos que ainda não cumprem
numa lista temporária que desliga só as regras novas para eles:

```js
// TEMPORARIO (refatoracao de AAAA-MM-DD): arquivos que ainda nao cumprem as regras novas.
// Para conferir um arquivo como ficara: `ESLINT_ESTRITO=1 npx eslint <arquivo>`.
const PENDENTES = process.env.ESLINT_ESTRITO === "1" ? [] : ["src/rotas/x.tsx", ...];
...(PENDENTES.length ? [{ files: PENDENTES, rules: { "max-lines-per-function": "off", "no-restricted-syntax": ["error", ...DE_ROTA] } }] : []),
```

Arquivo novo já nasce cumprindo; os subagentes conferem os seus com `ESLINT_ESTRITO=1` e **não
editam** a lista (seria conflito entre todos); o agente principal apaga a lista inteira na
integração. A mesma ideia vale para o Python (`per-file-ignores` temporário com comentário).

### Quando usar multiagente

Se a correção for grande — **mais de ~15 arquivos ou mais de ~50 ocorrências** que o `--fix`
não resolveu, ou se pegar mais de uma área (back e front, ou vários pacotes) — **não corrija
sozinho em sequência: divida entre subagentes em worktrees**.

- O agente principal faz os passos 1–3 (configuração e `--fix` já commitados na `main`), e
  só então divide o restante. Antes de dividir, ele também cria e commita **o que todos vão
  usar**: componentes e helpers base (`<Consulta>`, variantes do `Botao`, `formatarPercentual`),
  tokens novos, o helper de teste de tela (`tests/auxiliar/tela.tsx`). Senão cada subagente
  inventa o seu e a integração vira conflito.
- Escreva **um arquivo de contexto comum** (regras, como preparar a worktree, como testar,
  formato do relatório) e dê a cada subagente esse arquivo + a lista exata dos seus arquivos.
  Arquivo compartilhado que alguém precisa mudar (`ui/index.ts`, `estilos.css`) tem **um dono
  nomeado**; os outros anotam o pedido no relatório.
- **Cada subagente com o próprio banco de teste** (`CREATE DATABASE <app>_teste_<agente>` e
  `DATABASE_URL_TESTE` apontando para ele, apagado no fim): o fixture que migra faz `downgrade
  base` no fim da sessão, e com dois agentes no mesmo banco um derruba o esquema do outro no
  meio da suíte — falhas aleatórias que parecem bug e não são.
- Worktree não tem `node_modules` nem `.venv`: `ln -s "$MAIN/web/node_modules" web/node_modules`
  e `uv sync`. Arquivos gitignored que o teste precisa (`.env`) são copiados da principal.
- **Partição por arquivo, nunca por regra**: cada subagente recebe um conjunto disjunto de
  pastas/arquivos (ex.: `api/services/editais/`, `api/services/cartoes/`, `api/routers/` +
  `api/schemas/`, `pipeline/`, `web/src/rotas/`, `web/src/components/`). Dois agentes nunca
  editam o mesmo arquivo. Mudança em arquivo compartilhado (`pyproject.toml`, `conftest.py`,
  `deps.py`, `client.ts`) fica com o agente principal.
- Cada subagente (`Agent` com `isolation: "worktree"`): recebe a lista exata de ocorrências
  da sua fatia, corrige sem mudar comportamento, roda o lint **só da sua fatia** + os testes da
  área, e commita na branch da worktree com `refactor(<area>): ...` ou `chore(lint): ...`.
- Lance todos os subagentes na mesma mensagem (rodam em paralelo). Até ~7 por rodada.
- O agente principal integra as branches uma a uma (merge ou cherry-pick), roda **todas** as
  verificações na `main`, corrige conflitos ou sobras, apaga a lista `PENDENTES` e atualiza
  `docs/sistema/` e o `CLAUDE.md` a partir dos relatórios (subagentes de front não editam docs
  compartilhados; o do back edita o arquivo do próprio domínio).
- Mudança pequena (abaixo do limiar) é feita direto, sem subagente.

Isso vale para qualquer mudança do padrão aplicada a um projeto, não só lint.
