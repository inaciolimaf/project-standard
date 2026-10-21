# Estrutura: monólito modular

Um processo, um deploy, um banco — mas dividido em **módulos de domínio com fronteira
garantida**. Cada módulo guarda as próprias rotas, DTOs, modelos e regra; módulo só conversa com
outro pela interface pública dele; efeito colateral em outro domínio vai por evento. Sem a
garantia (contratos de import no CI), em três meses volta a ser pasta trocada de lugar.

## Raiz

```
projeto/
├── api/            back FastAPI (pacote Python), ver abaixo
├── pipeline/       CLI do projeto (typer), `[project.scripts] nome = "pipeline.cli:app"`
├── ferramentas/    scripts de qualidade/geração: tamanho_de_funcao.py, cobertura_da_documentacao.py, openapi.py
├── migrations/     Alembic (versions/NNNN_nome_curto.py, numeração sequencial de 4 dígitos)
├── tests/          pytest: unidade/, integracao/, dourados/, fakes na raiz (*_falso.py)
├── web/            front (Vite) com package.json próprio, ver abaixo
├── docker/         *.Dockerfile, entrypoint-*.sh
├── specs/          NN-nome.md, o que foi pedido, na ordem de leitura
├── docs/           sistema/ (como funciona hoje) e deploy-<paas>.md
├── CLAUDE.md, README.md, Makefile
├── docker-compose.yml, docker-compose-<paas>.yml
├── pyproject.toml, uv.lock, alembic.ini
└── .env.example, .gitignore, .dockerignore
```

Dados grandes (acervo, cache, mídia) ficam **fora do git e fora da imagem**: diretório
gitignored na raiz, montado como volume.

## Back (`api/`)

```
api/
├── nucleo/         o que todo módulo usa e que não tem domínio
│   ├── config.py   Configuracao(BaseSettings) única, frozen, lida por configuracao() com lru_cache
│   ├── db.py       engine, fábrica de sessão, Base dos modelos, unidade de trabalho, obter_do_usuario
│   ├── deps.py     aliases Annotated sem domínio: SessaoBd, paginação (UsuarioAtual/Admin são do módulo auth)
│   ├── saude.py    /health com registrar_verificacao(nome, funcao): cada módulo registra a sua parte
│   ├── erros.py    ErroDeAplicacao + manipulador único de problem+json
│   ├── eventos.py  barramento de eventos de domínio (emitir / assinar / o_que_veio)
│   ├── tarefas.py  Agendador de tarefas em segundo plano (lança depois da resposta) e o evento ApiSubiu
│   ├── relogio.py  a hora do usuário (agora, hoje, dia_de): um lugar só para o teste trocar
│   ├── log.py      structlog
│   ├── modelos.py  agregador: importa o modelos.py de cada módulo (para o Alembic e o metadata)
│   └── main.py     criar_app(): lifespan, middleware, junta os routers dos módulos. Nada mais
├── infra/          técnico, sem regra de negócio (ex.: leitor de arquivo, índice, cliente de LLM, mídia)
└── modulos/
    └── <dominio>/
        ├── __init__.py   a INTERFACE PÚBLICA: o que outro módulo pode importar (`__all__`)
        ├── rotas.py      APIRouter, só HTTP
        ├── schemas.py    DTOs pydantic: XDto (saída), XEntrada (criação), XAlteracao (patch)
        ├── modelos.py    modelos SQLAlchemy do domínio
        ├── eventos.py    os eventos que o módulo EMITE (dataclasses, exportadas pela interface)
        ├── assinantes.py os eventos de outros módulos a que ele REAGE
        ├── deps.py       dependências do FastAPI que o módulo oferece (ex.: UsuarioAtual em auth)
        └── <subdominio>/ a regra de negócio, um pacote por subdomínio (ex.: em progresso, dia/,
                          missoes/, conquistas/, loja/; em questões, listagem/, filtro/, treino/)
```

**Raiz do módulo = contrato; regra = subpastas por subdomínio.** Na raiz ficam só os arquivos de
contrato acima (`rotas.py` e `schemas.py` viram pacotes `rotas/`/`schemas/` quando são vários).
Toda pasta tem no máximo **8 arquivos `.py`** (fora o `__init__.py`) — passou, agrupe. Nome de
subpasta é o subdomínio, nunca camada técnica genérica (`services/`, `utils/`, `helpers/`). O
`__init__.py` do módulo reexporta o que é público: reorganizar por dentro não muda nenhum outro
módulo, por isso dá para fazer um agente por módulo em paralelo. Garantia: teste de arquitetura
(`testes.md`).

Os módulos têm uma **ordem de camadas** de baixo para cima (no Crivo: `acervo`, `recompensas` →
`auth` → `editais` → `questoes` → `revisao`, `aulas` → `cartoes`, `simulados` → `progresso` →
`estudar` e os de leitura, `admin` no topo). Quem está embaixo não importa quem está em cima;
quando precisa avisar, emite evento. Três tipos de módulo que aparecem ao desfazer ciclos:
- **módulo de dados embaixo de todos** (ex.: `acervo`: os modelos e catálogos que vários domínios
  leem), para leitura comum não puxar um domínio inteiro;
- **módulo só de DTOs e enums** (ex.: `recompensas`: o `MudancasDto` que o progresso devolve e que
  aparece na resposta de quem emite) — fica embaixo dos emissores e acima de nada; sem regra;
- **módulo de leitura no topo** (ex.: `admin`, `estatisticas`): pode ler de todos, ninguém o importa.

### Fronteiras (garantidas por `import-linter` no `make lint` e no CI)

```toml
[tool.importlinter]
root_packages = ["api"]

[[tool.importlinter.contracts]]
name = "camadas: modulos -> infra -> nucleo"
type = "layers"
layers = ["api.modulos", "api.infra", "api.nucleo"]

[[tool.importlinter.contracts]]
name = "modulo so importa a interface publica de outro modulo"
type = "independence"        # ou "forbidden" por par, com allow_indirect_imports
modules = ["api.modulos.questoes", "api.modulos.cartoes", "..."]
# importacoes de interface publica liberadas em ignore_imports, com comentario do porque
```

Regras:
1. **Interface pública no `__init__.py`.** `from api.modulos.editais import recorte_do_edital`
   pode; `from api.modulos.editais.processamento import _algo` não. O `__init__` reexporta só o
   que outros módulos precisam, com `__all__`. Dentro do `__init__`, modelos e schemas primeiro e
   services depois (com `I001` desligado só nesses arquivos): enquanto existe ciclo, é essa ordem
   que deixa a importação funcionar. Teste mexe no nome da interface
   (`monkeypatch.setattr("api.modulos.progresso.agora", ...)`), que é o que os outros módulos leem.
2. **Dependência do usuário logado é do módulo `auth`** (`api/modulos/auth/deps.py`:
   `UsuarioAtual`, `Admin`...), exportada pela interface dele; o núcleo não conhece usuário.
   Rota que precisa da sessão do usuário (ex.: servir mídia por token) é HTTP de domínio e mora
   num módulo, não em `infra`. Infra que precisa avisar um domínio (ex.: "figura indisponível"
   marca a questão) emite evento.
3. **Camadas:** `modulos` importa `infra` e `nucleo`; `infra` importa só `nucleo`; `nucleo` não
   importa ninguém de dentro do `api`. O `nucleo/main.py` é a exceção natural (junta os routers)
   e fica fora do contrato de camadas.
4. **Sem ciclos entre módulos.** Se A precisa avisar B do que aconteceu, A **emite um evento**
   e B assina — A não importa B. Ex.: questões emite `RespostaRegistrada`, cartões
   `CartaoRevisado`, simulados `SimuladoFinalizado`, auth `UsuarioCriado`; revisão e progresso
   assinam e decidem cartão de revisão, moedas, missões e ofensiva. Convenção:
   - os assinantes rodam **na mesma sessão** (o que gravam comita ou desfaz junto) e na ordem de
     `MODULOS_COM_ASSINANTES` (ex.: revisão antes de progresso), carregados no primeiro `emitir`
     — o núcleo não importa módulo, e teste/CLI veem os mesmos assinantes que a API;
   - o que os assinantes devolvem volta ao emissor (`eventos.o_que_veio(resultados, Tipo)`): é
     assim que a resposta da API continua trazendo "o que mudou" sem o emissor conhecer o progresso;
   - `tests/unidade/test_eventos.py` confere quem assina cada evento;
   - evento é aviso. Usá-lo como pergunta (ex.: "conte isto pelo índice em memória") funciona,
     mas é exceção a justificar — normalmente a função muda de módulo;
   - infraestrutura transversal que gerava ciclo (agendador de tarefas, relógio, recuperação na
     subida) vai para o núcleo; cada módulo registra a própria recuperação assinando `ApiSubiu`.
5. **Modelos por módulo.** Cada módulo tem o próprio `modelos.py`; `nucleo/modelos.py` importa
   todos para o Alembic enxergar o metadata inteiro. FK entre módulos é por nome de tabela
   (`ForeignKey("usuarios.id")`), sem importar a classe do outro módulo; `relationship` entre
   módulos só com string e só quando necessário.
6. **Exceções às fronteiras** ficam em `ignore_imports` com comentário e entram como lacuna a
   resolver — nunca silenciosas.

### Camada HTTP, transação e posse

- **Router só faz HTTP**: valida entrada, chama o service, devolve DTO. Nada de `select(...)`
  nem regra no router.
- **A transação tem um dono só: a unidade de trabalho da requisição.** A dependência da sessão
  abre a transação, comita no fim se a requisição deu certo e desfaz se deu erro. Service e
  router **não** chamam `commit()`; service usa `flush()` quando precisa do id gerado. Assim
  duas operações de services diferentes compõem uma transação só. Tarefa em segundo plano e
  comando da CLI abrem a própria unidade de trabalho (`async with unidade_de_trabalho() as s:`).
- **"O registro do usuário ou 404" é um helper**:
  `await obter_do_usuario(sessao, Edital, id, usuario, o_que="Edital")` — busca, confere a posse
  (`usuario_id`), e levanta `nao_encontrado` igual para "não existe" e "é de outro usuário"
  (não vaza que o id existe). Nunca `sessao.get` + `if x.usuario_id != usuario.id` à mão.
- Service não conhece `Request`/`Response`.

### Tamanho

Função até 30 linhas úteis, **arquivo até 300 linhas** (`ferramentas/tamanho_de_funcao.py`
mede os dois). Arquivo que passa é dividido por responsabilidade dentro do módulo
(`servico.py` vira `servico/criar.py`, `servico/responder.py`...), não por número de linhas.

Um arquivo de dados lido pelos dois lados (ex.: `sanitizacao.json`) mora no back e o front
importa por caminho relativo — uma fonte só.

## Front (`web/`)

A mesma ideia: módulos por domínio, e as rotas só montam telas.

```
web/src/
├── main.tsx, router.tsx, estilos.css
├── api/            client.ts (fetch único, lerProblema), tipos.ts (gerado), modelos.ts (aliases)
├── rotas/          um arquivo por rota TanStack Router: lê params (Route.useParams), monta a tela
│                   com componentes do módulo. Fino.
├── modulos/
│   └── <dominio>/
│       ├── componentes/   componentes do domínio
│       ├── hooks.ts       hooks TanStack Query do domínio (chaves, consultas, mutações)
│       ├── lib.ts         funções puras do domínio
│       └── index.ts       interface pública do módulo
├── components/     só o que é compartilhado por vários módulos
│   └── ui/         primitivos: Card, Botao, Modal, Gaveta, Input, Abas, PainelLateral, NoDeArvore...
└── lib/            transversal: formatacao.ts (único lugar que formata número/data), atalhos.ts
                    (único que escuta teclado), paletas.ts (único com cor fixa de conteúdo),
                    storage, tema, filtro-url
```

| Arquivo | Papel |
|---|---|
| `src/api/client.ts` | `fetch` único, `lerProblema()` único para erros, `BASE = "/api/v1"` |
| `src/api/tipos.ts` | **gerado** do `openapi.json` (não editar, fora do lint) |
| `src/estilos.css` | tokens de cor com valor claro e escuro (`:root[data-theme=...]`) + `@theme inline`; `@custom-variant dark` para o `dark:` seguir o tema do app, não o do sistema |
| `tests/` | Vitest (`*.test.ts(x)`), `setup.ts`, `auxiliar/` (`tela.tsx` com `renderizarTela`/`apiFalsa`, `dados*.ts`) |
| `e2e/` | Playwright (`rotas.spec.ts`, `celular.spec.ts`, `fluxos/*.spec.ts`, `auxiliar.ts`) |
| `Caddyfile` | serve o build e faz proxy de `/api/*` e `/health` |

Fronteira no front: módulo importa outro só pelo `index.ts` dele (regra
`no-restricted-imports` com padrão `**/modulos/*/!(index)`), e `components/`/`lib/` não
importam `modulos/`.

Stack: React 19, Vite 6, TypeScript 5 strict, Tailwind v4 (`@tailwindcss/vite`), TanStack
Router + Query, Radix para diálogo/abas. Dev server com proxy de `/api` e `/health` para
`API_URL` (padrão `http://localhost:8000`) — mesmo domínio em dev e em produção, sem CORS.

## Levar um projeto em camadas (`routers/`, `schemas/`, `services/`) para módulos

1. **Medir o acoplamento** antes: quem importa quem entre domínios
   (`grep -rn "from api.services.X" api | grep -v "api/services/X"`). O número diz quanto vai
   virar evento ou interface pública.
2. **Mover é um passo só, mecânico, de um agente só** (back e front podem ser dois agentes, em
   paralelo, porque não se tocam): `git mv` para a estrutura nova, imports reescritos, testes
   verdes, nenhuma mudança de comportamento. Mover em paralelo com outras mudanças é conflito
   garantido; nada mais roda enquanto isso.
3. **Ligar os contratos** do import-linter com as violações atuais em `ignore_imports`
   (comentadas, como a lista `PENDENTES` do eslint).
4. **Base comum, pelo agente principal**: unidade de trabalho, `obter_do_usuario`, barramento de
   eventos, teto de 300 linhas por arquivo, teste de arquitetura e os contratos do
   import-linter (ainda fora do `make lint`, em `make fronteiras`). Tudo com listas temporárias e
   variável de ambiente "estrita" para conferir o alvo.
5. **Interfaces públicas e camadas: um agente só.** Parece paralelizável por módulo, mas não é:
   enquanto há ciclos entre módulos, reexportar nomes nos `__init__.py` quebra na importação
   conforme a ordem em que os módulos carregam, e isso só aparece com tudo junto. Antes, o
   principal mede quem importa o quê de quem e escreve um **contrato de nomes** (o que cada
   `__init__` exporta, privados `_x` renomeados, colisões resolvidas) — sem ele dois lados
   escolhem nomes diferentes.
6. **Depois, em paralelo, um agente por módulo** (arquivos disjuntos): tirar `commit()`, usar
   `obter_do_usuario`, dividir arquivos acima de 300 linhas, limpar comentários, as correções do
   domínio.
7. **Por último, um agente só para os ciclos**: chamadas diretas entre módulos viram eventos;
   `sem-ciclos` passa e os contratos entram no `make lint`.
8. `docs/sistema/` com os caminhos novos a cada passo (`make docs` acusa todo caminho que sumiu).

No front, a mudança de lugar foi um agente só e trouxe junto: módulo `shell` (navegação, toasts,
404, que dependem de auth e progresso e por isso não podem ficar em `components/`); a parte de
`lib/toasts` que conhece progresso foi para o módulo de progresso; e a regra de fronteira por
caminho relativo (`../outro-modulo/...`) é uma regex montada da lista de pastas de `modulos/`,
porque o padrão `**/modulos/**` não pega import relativo.
