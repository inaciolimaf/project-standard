"""Lint de tamanho: nenhuma funcao passa do teto de linhas uteis, nenhum arquivo do teto dele.

O ruff nao tem essas regras (o `PLR0915` conta *statements*, nao linhas), entao elas moram aqui.

Conta como linha util toda linha que nao e branca, nem so de comentario, nem de docstring.
Comentario e docstring sao o que se quer incentivar; puni-los faria a regra pedir codigo pior. Na
funcao, a contagem vai do primeiro comando do corpo ao fim: assinatura e decorador ficam de fora,
o custo deles ja e cobrado pelo `PLR0913`.

Funcao aninhada e medida por conta propria *e* dentro da que a contem: uma closure grande e
peso da funcao externa tanto quanto qualquer outro bloco.

Uso:

    uv run python -m ferramentas.tamanho_de_funcao [caminho ...]

Sem argumento, usa `[tool.tamanho-de-funcao]` do `pyproject.toml`. Sai com 1 se achar algo.
`ignorar-arquivo-temporario` lista arquivos grandes ainda por dividir; `TAMANHO_ESTRITO=1` ignora a
lista, para conferir como o arquivo vai ficar.
"""

from __future__ import annotations

import ast
import os
import sys
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CODIGO = "FN001"
CODIGO_ARQUIVO = "FN002"
RAIZ = Path(__file__).resolve().parent.parent
MAX_PADRAO = 30
MAX_ARQUIVO_PADRAO = 300


@dataclass(frozen=True)
class Config:
    max_linhas: int
    caminhos: tuple[Path, ...]
    #: Arquivos fora das duas regras, com o motivo no `pyproject.toml` (ex.: kernel numba, que nao pode
    #: chamar funcao dentro do laco sem pagar contagem de referencia por chamada).
    ignorar: frozenset[Path] = frozenset()
    max_linhas_arquivo: int = MAX_ARQUIVO_PADRAO
    ignorar_arquivo: frozenset[Path] = frozenset()


@dataclass(frozen=True)
class Achado:
    arquivo: Path
    linha: int
    codigo: str
    o_que: str
    linhas_uteis: int
    maximo: int

    def formatar(self) -> str:
        rel = self.arquivo.relative_to(RAIZ) if self.arquivo.is_relative_to(RAIZ) else self.arquivo
        return (
            f"{rel}:{self.linha}: {self.codigo} {self.o_que} tem "
            f"{self.linhas_uteis} linhas uteis (maximo {self.maximo})"
        )


def ler_config(argv: list[str]) -> Config:
    """Le `[tool.tamanho-de-funcao]`; caminhos na linha de comando tem precedencia."""
    bruto: dict[str, Any] = {}
    pyproject = RAIZ / "pyproject.toml"
    if pyproject.exists():
        with pyproject.open("rb") as arquivo:
            dados: dict[str, Any] = tomllib.load(arquivo)
        bruto = dict(dados.get("tool", {}).get("tamanho-de-funcao", {}))

    nomes = argv or [str(c) for c in bruto.get("caminhos", [])] or ["."]
    estrito = os.environ.get("TAMANHO_ESTRITO") == "1"
    temporarios = [] if estrito else bruto.get("ignorar-arquivo-temporario", [])
    return Config(
        max_linhas=int(bruto.get("max-linhas", MAX_PADRAO)),
        caminhos=tuple(RAIZ / n for n in nomes),
        ignorar=frozenset(RAIZ / n for n in bruto.get("ignorar", [])),
        max_linhas_arquivo=int(bruto.get("max-linhas-arquivo", MAX_ARQUIVO_PADRAO)),
        ignorar_arquivo=frozenset(RAIZ / n for n in temporarios),
    )


def arquivos_python(caminhos: tuple[Path, ...]) -> Iterator[Path]:
    for caminho in caminhos:
        if caminho.is_file():
            yield caminho
        else:
            yield from sorted(caminho.rglob("*.py"))


def _linhas_da_docstring(corpo: list[ast.stmt]) -> set[int]:
    if not corpo:
        return set()
    primeiro = corpo[0]
    if (
        isinstance(primeiro, ast.Expr)
        and isinstance(primeiro.value, ast.Constant)
        and isinstance(primeiro.value.value, str)
        and primeiro.end_lineno is not None
    ):
        return set(range(primeiro.lineno, primeiro.end_lineno + 1))
    return set()


def _contar(faixa: range, fonte: list[str], fora: set[int]) -> int:
    return sum(
        1
        for numero in faixa
        if numero not in fora and (texto := fonte[numero - 1].strip()) and not texto.startswith("#")
    )


def medir(no: ast.FunctionDef | ast.AsyncFunctionDef, fonte: list[str]) -> int:
    """Quantas linhas uteis o corpo de `no` ocupa."""
    docstring = _linhas_da_docstring(no.body)
    corpo = [c for c in no.body if c.lineno not in docstring]
    if not corpo or no.end_lineno is None:
        return 0
    return _contar(range(corpo[0].lineno, no.end_lineno + 1), fonte, docstring)


def medir_arquivo(arvore: ast.Module, fonte: list[str]) -> int:
    """Linhas uteis do arquivo inteiro, sem as docstrings de modulo, classe e funcao."""
    docstrings = _linhas_da_docstring(arvore.body)
    for no in ast.walk(arvore):
        if isinstance(no, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            docstrings |= _linhas_da_docstring(no.body)
    return _contar(range(1, len(fonte) + 1), fonte, docstrings)


def analisar(arquivo: Path, config: Config) -> Iterator[Achado]:
    fonte = arquivo.read_text(encoding="utf-8")
    try:
        arvore = ast.parse(fonte, filename=str(arquivo))
    except SyntaxError as erro:  # arquivo quebrado e problema do ruff, nao daqui
        print(f"{arquivo}: {CODIGO} nao foi possivel analisar ({erro})", file=sys.stderr)
        return
    linhas = fonte.splitlines()
    if arquivo not in config.ignorar_arquivo:
        total = medir_arquivo(arvore, linhas)
        if total > config.max_linhas_arquivo:
            yield Achado(arquivo, 1, CODIGO_ARQUIVO, "o arquivo", total, config.max_linhas_arquivo)
    for no in ast.walk(arvore):
        if isinstance(no, ast.FunctionDef | ast.AsyncFunctionDef):
            uteis = medir(no, linhas)
            if uteis > config.max_linhas:
                yield Achado(arquivo, no.lineno, CODIGO, f"`{no.name}`", uteis, config.max_linhas)


def main(argv: list[str] | None = None) -> int:
    config = ler_config(list(argv if argv is not None else sys.argv[1:]))
    achados = [
        achado
        for arquivo in arquivos_python(config.caminhos)
        if arquivo not in config.ignorar
        for achado in analisar(arquivo, config)
    ]
    for achado in sorted(achados, key=lambda a: (a.codigo, -a.linhas_uteis, str(a.arquivo))):
        print(achado.formatar())
    if achados:
        print(f"Encontrados {len(achados)} erros.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
