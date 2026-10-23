"""Prova de morte da OPP-20261023-DOCF.

Roda da raiz do projeto. Confere, por AST, os dois candidatos a poda em
`src/core/dna_analysis.py`:

1. a expressao de string solta nas linhas 558-571, que nao e docstring;
2. o nome `DNAAnalyzer` declarado em `__all__`, sem consumidor.

Nao importa o modulo (o import custa pandas); trabalha sobre o texto.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[5]
ALVO = RAIZ / "src" / "core" / "dna_analysis.py"


def cargoes_texto_soltas(arvore: ast.AST) -> list[tuple[str, int, int]]:
    """Statements de expressao cujo valor e uma constante string, fora do docstring."""
    achados = []
    for no in ast.walk(arvore):
        if not isinstance(
            no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
        ):
            continue
        corpo = no.body
        if (
            corpo
            and isinstance(corpo[0], ast.Expr)
            and isinstance(corpo[0].value, ast.Constant)
            and isinstance(corpo[0].value.value, str)
        ):
            corpo = corpo[1:]
        for stmt in corpo:
            if (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                achados.append(
                    (getattr(no, "name", "<modulo>"), stmt.lineno, stmt.end_lineno)
                )
    return achados


def main() -> int:
    fonte = ALVO.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    print(f"alvo: {ALVO.relative_to(RAIZ)}")
    print(f"linhas: {len(fonte.splitlines())}")
    print()

    print("== candidato 1: string solta ==")
    soltas = cargoes_texto_soltas(arvore)
    if not soltas:
        print("  nenhuma encontrada")
        return 1
    for dono, ini, fim in soltas:
        print(f"  dentro de {dono}: linhas {ini}-{fim} ({fim - ini + 1} linhas)")
        no = next(
            n
            for n in ast.walk(arvore)
            if isinstance(n, ast.Expr) and n.lineno == ini
        )
        print(f"  tipo do no: {type(no).__name__}({type(no.value).__name__})")
        print("  efeito colateral possivel: nao (constante string)")
    print()

    print("== docstring real ==")
    sys.path.insert(0, str(RAIZ / "src"))
    from core.dna_analysis import dna_analysis  # noqa: PLC0415

    doc = inspect.getdoc(dna_analysis) or ""
    print(f"  inspect.getdoc(dna_analysis) comeca com: {doc.splitlines()[0]!r}")
    print(f"  tamanho: {len(doc)} caracteres")
    print()

    print("== candidato 2: __all__ ==")
    import core.dna_analysis as modulo  # noqa: PLC0415

    declarados = list(getattr(modulo, "__all__", []))
    print(f"  __all__ tem {len(declarados)} nomes")
    print(f"  'DNAAnalyzer' em __all__: {'DNAAnalyzer' in declarados}")
    consumidores = []
    for arquivo in RAIZ.rglob("*.py"):
        if any(
            parte in {".git", ".venv", "__pycache__"}
            for parte in arquivo.parts
        ):
            continue
        try:
            texto = arquivo.read_text(encoding="utf-8")
            outra = ast.parse(texto)
        except (UnicodeDecodeError, SyntaxError):
            continue
        for no in ast.walk(outra):
            if isinstance(no, ast.ImportFrom) and no.module == "core.dna_analysis":
                for alias in no.names:
                    if alias.name == "DNAAnalyzer":
                        consumidores.append(str(arquivo.relative_to(RAIZ)))
            if isinstance(no, ast.ImportFrom) and no.module in (None, "core"):
                for alias in no.names:
                    if alias.name == "dna_analysis":
                        apelido = alias.asname or "dna_analysis"
                        for uso in ast.walk(outra):
                            if (
                                isinstance(uso, ast.Attribute)
                                and isinstance(uso.value, ast.Name)
                                and uso.value.id == apelido
                                and uso.attr == "DNAAnalyzer"
                            ):
                                consumidores.append(
                                    str(arquivo.relative_to(RAIZ))
                                )
    estrela = []
    for arquivo in RAIZ.rglob("*.py"):
        if any(
            parte in {".git", ".venv", "__pycache__"} for parte in arquivo.parts
        ):
            continue
        try:
            outra = ast.parse(arquivo.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, SyntaxError):
            continue
        for no in ast.walk(outra):
            if isinstance(no, ast.ImportFrom) and no.module == "core.dna_analysis":
                if any(alias.name == "*" for alias in no.names):
                    estrela.append(str(arquivo.relative_to(RAIZ)))
    print(f"  consumidores de DNAAnalyzer por este modulo: {len(consumidores)}")
    for caminho in sorted(set(consumidores)):
        print(f"    {caminho}")
    print(f"  'import *' do modulo no projeto: {len(estrela)}")
    for caminho in estrela:
        print(f"    {caminho}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
