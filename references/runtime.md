# Config, erros, log, LLM

## Configuração (`api/config.py`)

- Uma `Configuracao(BaseSettings)` com `env_file=".env"`, `extra="ignore"`, `frozen=True`.
  Acesso só por `configuracao()` (`@lru_cache`), limpo nos testes.
- `ambiente: Literal["local", "producao", "teste"]`.
- Segredos são `SecretStr` **sem padrão**. Validador de modelo: em `producao`, recusa segredo
  ausente, com menos de 32 bytes, igual a um valor de `VALORES_DE_EXEMPLO` (os do
  `.env.example`) ou dois segredos iguais — levanta `ErroDeConfiguracao` antes de abrir porta.
- Números com `Field(ge=...)`; caminhos como `Path` relativos a `RAIZ_DO_REPO`.
- Comentário `#:` acima de cada campo não óbvio (o que é, o que acontece se vazio).
- Garantia: teste de `Configuracao` com `AMBIENTE=producao` e cada segredo faltando/curto/de
  exemplo.

## Unidade de trabalho e posse (`api/nucleo/db.py`)

- A dependência da sessão (`SessaoBd`) é a **unidade de trabalho**: abre a transação, comita no
  fim da requisição se deu certo, desfaz se deu erro. Router e service não chamam `commit()`
  (service usa `flush()` quando precisa do id). Tarefa de fundo e CLI usam
  `async with unidade_de_trabalho() as sessao:`.
- **Armadilha do FastAPI**: com o escopo padrão, o código depois do `yield` de uma dependência
  roda **depois** que a resposta já saiu — um commit que falha ali chega ao cliente como 200 e
  nada foi gravado. Use `SessaoBd = Annotated[AsyncSession, Depends(sessao, scope="function")]`
  (FastAPI ≥ 0.121): a dependência fecha antes da resposta e a falha vira 500.
- A sessão depende de uma `fabrica()` separada (`Depends(fabrica)`): o teste troca só a fábrica
  pela da transação dele (`app.dependency_overrides[fabrica] = lambda: fabrica_do_teste`) e a
  lógica de commit/rollback da unidade de trabalho continua sendo a real.
- **Gravação que precisa sobreviver ao erro da própria requisição** (registrar a tentativa de
  login que falhou, contar a falha de uma figura): a rota **devolve**
  `resposta_de_erro(request, erro)` (o mesmo `problem+json` do manipulador único) em vez de
  levantar, e a unidade de trabalho comita normalmente. Levantar desfaria a gravação.
- **Tarefa de fundo que grava em etapas** (e o custo de uma chamada de modelo que precisa ficar
  mesmo se a etapa falhar): recebe a **fábrica** de sessão como parâmetro, não chama
  `unidade_de_trabalho()` fixo. Em produção é a fábrica real; no teste é a da transação do teste,
  onde cada sessão vira um savepoint próprio — o commit do custo fica, o rollback da etapa desfaz
  só a etapa. Uma `unidade_de_trabalho()` fixa abre outra conexão, que no teste não enxerga nada.
- `obter_do_usuario(sessao, Modelo, id, usuario, o_que=...)`: busca + confere a posse + 404 igual
  para inexistente e de outro usuário. É o único jeito de carregar registro do usuário pelo id.
- Testes da unidade de trabalho: requisição que levanta erro depois de gravar não deixa nada no
  banco; uma fábrica falsa cujo `commit()` levanta prova que a resposta é 500, não 200 (e o teste
  falha se alguém tirar o `scope="function"`).
- Garantia da regra: `tests/unidade/test_arquitetura.py` percorre o `ast` de `api/` e falha se
  `commit()` aparecer fora de `nucleo/db.py` (com lista temporária enquanto a migração anda).

## SQL: só pelo query builder

- Toda consulta é montada com o SQLAlchemy (ORM ou Core): `select`, `insert`, `update`, `delete`,
  `func`, `literal_column`, `aliased`, `.cte(recursive=True)`, `insert(...).from_select(...)`,
  `postgresql.insert(...).on_conflict_do_update(...)`, trigrama com `func.similarity`/`.op("%")`,
  `select(func.set_config(...))`. Vale também fora da sessão: com `asyncpg` cru (carga em massa,
  índice em memória) o builder é compilado para o dialeto e executado pela mesma conexão; no SQLite
  de um arquivo de dados, Core com engine síncrona.
- Proibido: `text("...")` e string que começa com `SELECT/INSERT/UPDATE/DELETE/WITH/...`.
  Exceção só onde o builder não alcança — `EXPLAIN` em volta de uma consulta já montada pelo
  builder, `COPY` em massa (`copy_records_to_table`) — e cada uma fica listada, com o motivo, em
  `SQL_LIBERADO` do teste de arquitetura. DDL é das migrations (`op.*`).
- Caminho quente (milhões de linhas, uma consulta por questão aberta): compile o builder uma vez e
  reaproveite o SQL gerado; meça antes e depois. O SQL continua vindo do builder.
- Valor sempre por parâmetro; o builder já garante.

## Login

- **Limite de tentativas**: por e-mail e por IP, com janela (ex.: 5 falhas em 15 min → `429`
  com `problem+json`, `Retry-After` e `detail` dizendo quando tentar de novo). Sucesso zera o
  contador do e-mail. O contador mora no banco (ou num cache compartilhado), não na memória do
  processo, para valer com mais de um worker.
- A mesma mensagem para e-mail inexistente e senha errada (não revela quem tem conta).
- Teste: a sexta tentativa errada recebe 429 mesmo com a senha certa; depois da janela, entra.

## Erros (`api/erros.py`)

- Formato único: `application/problem+json` (RFC 9457: `type`, `title`, `status`, `detail`).
- `ErroDeAplicacao(status_code, titulo, detalhe, tipo, extras)` recusa `detalhe` vazio
  (`ValueError`) — todo 409/422 explica para o usuário o que fazer.
- `tipo` como slug `dominio/motivo` (ex.: `edital/sem-modelo`).
- Um manipulador registra tudo: `ErroDeAplicacao`, `HTTPException`, `RequestValidationError`.
- Front: `lerProblema()` único em `client.ts`, `ErroApi` com `title`/`detail`.

## Log (`api/log.py`)

- structlog: `JSONRenderer` em produção, `ConsoleRenderer` fora dela, timestamp ISO.
- Middleware gera/propaga `x-request-id` e vincula `request_id`, `rota`, `metodo` ao contexto.
- Evento com nome `dominio.acao` (`api.iniciando`, `editais.recuperacao_falhou`) e campos
  nomeados; texto de erro truncado (`str(erro)[:300]`).

## App (`api/main.py`)

- `criar_app()` é fábrica (testes e `openapi.py` usam).
- Rotas de domínio sob `/api/v1`, `/health` na raiz; docs em `/api/docs`.
- Laços de fundo no lifespan só fora de `AMBIENTE=teste`; tarefa que ficou no meio quando o
  processo caiu é recuperada na subida (vira estado de erro, não fica "rodando" para sempre).

## LLM / serviço externo pago

- Interface `ClienteLLM` em `api/llm/base.py`; implementação real e `falso.py` determinístico.
- Sem chave configurada, as rotas que dependem respondem `503` com `problem+json`; o resto
  funciona.
- Saída estruturada validada por contrato pydantic (`contratos.py`); prompts em `prompts.py`.
- Custo de cada chamada registrado no banco; teto diário (`LIMITE_CUSTO_DIARIO_USD`, zero
  desliga) corta antes de chamar.
- Modelo por variável (`MODELO_<DOMINIO>`), vazio cai no padrão do código.
- Nada que gaste dinheiro começa sozinho: cada etapa nasce de uma ação do usuário.
