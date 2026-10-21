# Pirâmide de testes

Números do Crivo (out/2026) para calibrar a proporção: ~200 de unidade, ~170 de integração,
Vitest com cobertura de 60% e telas inteiras testadas, Playwright com fluxos de verdade e
smoke de todas as rotas.

```
          ┌──────────────┐  e2e (Playwright, build de produção, API real)
          │ fluxos, rotas │  — fluxos clicando (login, responder, simulado, cartão);
          │ celular       │    smoke de TODAS as rotas; 390×844 sem overflow
        ┌─┴──────────────┴─┐  front (Vitest + Testing Library, jsdom) — cobertura ≥ 60%
        │ telas, componentes│ — telas inteiras com router real e API falsa, lib/ pura,
        │ lib, client       │   contrato de erro
      ┌─┴───────────────────┴─┐  integração (pytest + Postgres real)
      │ rotas HTTP, ingestão,  │ — httpx ASGITransport, transação com rollback
      │ migrations             │
    ┌─┴───────────────────────┴─┐  unidade (pytest, sem I/O)
    │ regras puras, parsers,      │ — rápidos, maioria
    │ contratos, dourados         │
    └─────────────────────────────┘
```

## Unidade — `tests/unidade/test_<assunto>.py`

- Sem banco, sem rede, sem disco fora de `tmp_path`.
- Funções puras de domínio, parsers, sanitização, agenda, cálculo de custo, config.
- Serviço externo entra pela implementação falsa (`api/llm/falso.py`: roteiro em ordem,
  resposta por etapa, ou função do pedido; sem correspondência devolve algo que quebra o
  contrato, para o teste falhar alto).

## Integração — `tests/integracao/test_<dominio>.py`

- Marker `integracao`. Postgres de `DATABASE_URL_TESTE` (o do compose, banco `<app>_teste`,
  criado por `make db-teste`) ou, sem ela, `testcontainers`; sem nenhum dos dois, `pytest.skip`
  com motivo — nunca falha por falta de infraestrutura.
- `esquema_migrado` (escopo de sessão): `alembic upgrade head` uma vez, `downgrade base` no
  fim — **as migrations são testadas nos dois sentidos** a cada rodada.
- `contexto_de_banco`: uma transação por teste, `join_transaction_mode="create_savepoint"`,
  rollback no fim. O código pode dar `commit` à vontade.
- `cliente`: `criar_app()` com `dependency_overrides` da sessão + `httpx.AsyncClient(
  transport=ASGITransport(app))`. Fixtures prontas: `admin`, `aluno`, `cliente_admin`,
  `cliente_aluno`, e um conjunto de dados falso ingerido (`tests/acervo_falso.py`).
- Testa rota HTTP de ponta a ponta: status, corpo, `problem+json` com `detail` não vazio.

## Dourados — `tests/dourados/`

Casos reais (arquivos do mundo: edital, questão do acervo, legenda) e respostas reais do modelo
gravadas por um comando da CLI (`crivo <dominio> gravar-dourado`, gasta centavos). O teste
confere que o código e o contrato aceitam o caso real. Teste que depende de dourado ausente faz
`skipif` com o comando que o gera na razão.

## Isolamento (fixture autouse em `tests/conftest.py`)

- Apaga do ambiente toda variável que a `Configuracao` lê (lista explícita).
- `AMBIENTE=teste`, `DATABASE_URL` inalcançável (porta 1) por padrão — teste que não pediu
  banco não acha um sem querer.
- Segredos de teste com 32+ bytes; `env_file=None` (o `.env` da máquina nunca entra).
- Limpa todos os singletons `lru_cache` antes e depois.
- Em `AMBIENTE=teste` o lifespan não sobe laços de fundo.

## pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
filterwarnings = ["error::DeprecationWarning:api.*", "error::DeprecationWarning:pipeline.*"]
markers = ["integracao: precisa de Postgres (DATABASE_URL_TESTE ou testcontainers)"]
```

## Front — Vitest

- `web/tests/*.test.ts(x)`, `environment: "jsdom"`, `globals: false`, `css: false`,
  `setup.ts` com `jest-dom/vitest` e `cleanup()` no `afterEach`.
- **Cobertura mínima de 60%** (linhas, statements, funções e branches), `@vitest/coverage-v8`
  no `vite.config.ts`, `npm run cobertura` / `make web-cobertura`, no CI. Fica fora só o que é
  gerado (`src/api/tipos.ts`) e o `main.tsx`. Mais baixo que o back porque tela tem muito JSX
  sem lógica; mais alto que zero porque sete de dez bugs do front que motivaram o padrão não
  tinham teste.
- Três tipos de teste, do mais barato ao mais caro:
  1. **`lib/` pura** (formatação, filtro na URL, storage, atalhos, tema): todas, com os casos de
     borda. São os testes mais baratos que existem.
  2. **Componente isolado**: `render(<X .../>)` + `userEvent`; para componente que usa
     `Link`/`useNavigate`, `vi.mock("@tanstack/react-router")`.
  3. **Tela inteira**: `tests/auxiliar/tela.tsx` com o router de verdade, memória como
     histórico e a API falsa:
     ```ts
     const api = apiFalsa({ "GET /questoes": { itens: [], total: 0 } });   // METODO /caminho sem /api/v1
     const { usuario } = await renderizarTela("/marcadas");
     expect(api.chamadas("GET /questoes")[0]?.query.get("marcadas")).toBe("true");
     ```
     `apiFalsa` troca o `fetch`, já responde o que o shell pede (usuário logado, saldo...) e
     devolve 404 em `problem+json` com o caminho no `detail` para rota não declarada — o teste
     falha dizendo o que faltou. `renderizarTela` completa o que o jsdom não tem (`matchMedia`,
     `scrollTo`). Dados falsos comuns em `tests/auxiliar/dados.ts`; os de uma área em
     `tests/auxiliar/dados-<area>.ts`. `vi.unstubAllGlobals()` no `afterEach`.
- Animação e tempo (`requestAnimationFrame`, debounce, cronômetro) com relógio falso
  (`vi.useFakeTimers({ toFake: ["requestAnimationFrame", "cancelAnimationFrame", "performance"] })`
  + `vi.advanceTimersByTime`), nunca `waitFor` esperando o tempo real: com a máquina carregada
  (CI, agentes em paralelo) o teste falha sem bug.
- O tempo de espera dos testes de tela fica num lugar só: `configure({ asyncUtilTimeout: 4000 })`
  no `setup.ts` e `testTimeout` no `vite.config.ts` — não em cada arquivo.
- **Toda tela com lógica tem teste de tela**: cronômetro (`vi.useFakeTimers`), autosave,
  confirmação, atalhos de teclado, formulário com erro da API. Teste o que o usuário vê e faz,
  não detalhe de implementação.
- Obrigatório também: `client.ts` (erro 409 falso vira exceção com `title`/`detail` e a tela
  mostra o `detail`; refresh no 401), componentes de filtro, renderização de HTML.
- **Correção no front sem teste que a reproduza não é aceita.** Tela nova nasce com teste.

## E2E — Playwright

- Roda no **build de produção** (`vite preview` na 4173) contra a API real (`API_URL`), login
  pela API com `E2E_EMAIL`/`E2E_SENHA`. Chrome do sistema (`channel: "chrome"`).
- Projeto `rotas`: abre cada rota (lista em `e2e/auxiliar.ts`) com ids falsos; falha em
  `pageerror` com "Invariant" ou na tela de erro genérica; `#root` não vazio.
- Projeto `celular`: mesmas rotas a 390×844 com toque, captura em `capturas/<rota>.png`,
  falha se `scrollWidth > innerWidth`. No CI as capturas viram artefato.
- **A lista de rotas não pode ficar para trás**: um teste compara as rotas do router com a
  lista do e2e e falha dizendo qual falta (ou a lista é gerada do router). Lista mantida só à
  mão ficou sem as telas mais novas.
- Projeto `fluxos`: **fluxos de verdade, clicando como o usuário**, um arquivo por fluxo em
  `e2e/fluxos/`. O mínimo: login pelo formulário (e senha errada mostra a mensagem da API) e
  logout; o caminho principal de cada área (no Crivo: abrir e responder uma questão, treino,
  simulado do início ao resultado, revisar cartão pelo teclado). Independentes dos dados exatos:
  pegam o primeiro item disponível, criam pela API o que precisam e apagam no fim. Rodam
  contra a API local e no CI contra dados falsos.
- **Funcionalidade nova entra no e2e no mesmo commit**: a rota na lista (o teste acima cobra)
  e, se tem fluxo principal novo, um arquivo em `e2e/fluxos/`.
- No CI, a API é esperada com laço de `curl` em `/health` com tempo limite (nunca `sleep N`),
  imprimindo o log da API se não subir.

## Teste de arquitetura

`tests/unidade/test_arquitetura.py` guarda as regras de desenho que nenhum lint de terceiro
cobre, lendo o `ast` do código: "só a unidade de trabalho chama `commit()`", "SQL só pelo query
builder" (acusa `sqlalchemy.text` e string que começa com palavra-chave SQL, fora as docstrings;
exceções em `SQL_LIBERADO` com motivo) e "pasta de módulo com no máximo 8 arquivos". Regra nova
desse tipo entra aqui, com lista temporária e `ARQUITETURA_ESTRITA=1` para conferir o alvo.

## No dia a dia

Rode o teste da área mexida, não a suíte toda; o CI roda tudo. Se o CI quebrar, corrija em
seguida.
