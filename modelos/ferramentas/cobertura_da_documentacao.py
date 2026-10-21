"""Confere que `docs/sistema/` acompanha o codigo: nada sem documentar, nada citado que nao existe.

Duas verificacoes:

- **cobertura**: todo caminho casado por `exigir` (routers, services, pacotes, rotas do front) e
  citado entre crases em algum arquivo da documentacao. Diretorio conta como citado se ele ou
  qualquer arquivo dentro dele aparece;
- **caminhos vivos**: todo caminho do repositorio citado entre crases existe, e todo
  `tests/x.py::nome` aponta para um `def nome` no arquivo. Documentacao que fala de arquivo
  apagado ou teste renomeado falha aqui.

Uso:

    uv run python -m ferramentas.cobertura_da_documentacao

Configuracao em `[tool.cobertura-da-documentacao]` do `pyproject.toml`. Sai com 1 se achar algo.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CODIGO_SEM_DOC = "DOC001"
CODIGO_CAMINHO_MORTO = "DOC002"
RAIZ = Path(__file__).resolve().parent.parent
TRECHO_ENTRE_CRASES = re.compile(r"`([^`\n]+)`")
#: Nomes que nao sao codigo do projeto, mesmo casando com `exigir`.
IGNORADOS = frozenset({"__init__.py", "__pycache__", "__main__.py"})


@dataclass(frozen=True)
class Config:
    documentacao: Path
    exigir: tuple[str, ...]
    raizes: tuple[str, ...]


@dataclass(frozen=True)
class Citacao:
    arquivo: Path
    linha: int
    caminho: str
    teste: str | None


def ler_config() -> Config:
    with (RAIZ / "pyproject.toml").open("rb") as arquivo:
        dados: dict[str, Any] = tomllib.load(arquivo)
    bruto = dados.get("tool", {}).get("cobertura-da-documentacao", {})
    return Config(
        documentacao=RAIZ / bruto.get("documentacao", "docs/sistema"),
        exigir=tuple(bruto.get("exigir", [])),
        raizes=tuple(bruto.get("raizes", [])),
    )


def _citacao(trecho: str, raizes: tuple[str, ...]) -> tuple[str, str | None] | None:
    """`api/x.py::teste` -> (`api/x.py`, `teste`); o que nao e caminho do repo -> None."""
    eh_do_repo = trecho.startswith(tuple(f"{r}/" for r in raizes))
    # Glob, placeholder (`<nome>`, `...`) e trecho com espaco sao exemplo, nao caminho.
    if not eh_do_repo or any(c in trecho for c in "*{<> ") or "..." in trecho:
        return None
    caminho, _, teste = trecho.partition("::")
    caminho = re.sub(r":\d+$", "", caminho)
    return caminho, (teste.split("[")[0] or None)


def citacoes(config: Config) -> Iterator[Citacao]:
    for arquivo in sorted(config.documentacao.rglob("*.md")):
        for numero, texto in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), start=1):
            for trecho in TRECHO_ENTRE_CRASES.findall(texto):
                achado = _citacao(trecho.strip(), config.raizes)
                if achado:
                    yield Citacao(arquivo, numero, achado[0], achado[1])


def exigidos(config: Config) -> Iterator[str]:
    for padrao in config.exigir:
        for caminho in sorted(RAIZ.glob(padrao.rstrip("/"))):
            if caminho.name in IGNORADOS or (padrao.endswith("/") and not caminho.is_dir()):
                continue
            yield caminho.relative_to(RAIZ).as_posix()


def _citado(caminho: str, citados: set[str]) -> bool:
    prefixo = caminho.rstrip("/") + "/"
    return caminho in citados or prefixo in citados or any(c.startswith(prefixo) for c in citados)


def _ignorado_pelo_git(caminho: str) -> bool:
    """Arquivo que so existe na maquina (cache, captura, cookie): nao some no CI por estar errado."""
    resultado = subprocess.run(  # noqa: S603 - argumentos fixos, sem shell
        ["git", "check-ignore", "-q", caminho],  # noqa: S607 - git do PATH, como no Makefile
        cwd=RAIZ,
        check=False,
    )
    return resultado.returncode == 0


def _problema_da_citacao(citacao: Citacao) -> str | None:
    alvo = RAIZ / citacao.caminho
    if not alvo.exists() and not _ignorado_pelo_git(citacao.caminho):
        return f"cita `{citacao.caminho}`, que nao existe"
    if citacao.teste and alvo.is_file():
        definicao = re.compile(rf"^\s*(async\s+)?def {re.escape(citacao.teste)}\b", re.MULTILINE)
        if not definicao.search(alvo.read_text(encoding="utf-8")):
            return f"cita o teste `{citacao.teste}`, que nao existe em `{citacao.caminho}`"
    return None


def verificar(config: Config) -> list[str]:
    todas = list(citacoes(config))
    citados = {c.caminho.rstrip("/") for c in todas} | {c.caminho for c in todas}
    erros = [
        f"{caminho}: {CODIGO_SEM_DOC} nao aparece em nenhum arquivo de "
        f"{config.documentacao.relative_to(RAIZ)}/"
        for caminho in exigidos(config)
        if not _citado(caminho, citados)
    ]
    for citacao in todas:
        problema = _problema_da_citacao(citacao)
        if problema:
            local = f"{citacao.arquivo.relative_to(RAIZ)}:{citacao.linha}"
            erros.append(f"{local}: {CODIGO_CAMINHO_MORTO} {problema}")
    return erros


def main() -> int:
    erros = verificar(ler_config())
    for erro in erros:
        print(erro)
    if erros:
        print(f"Encontrados {len(erros)} erros. Atualize a documentacao (CLAUDE.md, secao Documentacao).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
