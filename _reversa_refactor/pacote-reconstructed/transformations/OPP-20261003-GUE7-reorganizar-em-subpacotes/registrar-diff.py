"""Registra os CHG-*.diff da OPP-20261003-GUE7, um por lote.

Estado "antes":

- para os sete modulos movidos, a copia congelada em `before-after/src-antes/`,
  que e autoritativa;
- para os demais arquivos de `src/`, tambem a copia congelada, e a conferencia
  abaixo exige que ela seja igual ao inverso das edicoes desta transformacao;
- para `tests/`, `_reversa_sdd/parity/` e `README.md`, o inverso exato de cada
  edicao, com assercao de que cada trecho aparece exatamente uma vez.

As tabelas de movimentacao e de edicao vem de `reorganizar.py`, para nao existirem
duas versoes da verdade.
"""
from __future__ import annotations

import difflib
import os

from reorganizar import EDITS, MOVES, PRE, ROOT, le

HERE = os.path.dirname(os.path.abspath(__file__))
ANTES = os.path.join(HERE, "before-after", "src-antes")

LOTES = [
    ("CHG-001-subpacotes.diff", [
        "src/reconstructed/parsers/__init__.py",
        "src/reconstructed/reporting/__init__.py",
    ]),
    ("CHG-002-movimentacao.diff", ["src/reconstructed/" + d for _, d in MOVES]),
    ("CHG-003-fachadas-e-app.diff", [
        "src/reconstructed/dna_analysis.py",
        "src/reconstructed/path_search.py",
        "src/app.py",
    ]),
    ("CHG-004-testes.diff", [
        "tests/test_characterization_matching.py",
        "tests/test_dna_analysis.py",
        "tests/test_upload.py",
        "tests/test_mermaid_escape.py",
        "tests/test_path_search.py",
        "tests/test_characterization_mermaid.py",
    ]),
    ("CHG-005-paridade.diff", [
        "_reversa_sdd/parity/harness.py",
        "_reversa_sdd/parity/_check_split_types.py",
    ]),
    ("CHG-006-readme.diff", ["README.md"]),
]

MOVED = {"src/reconstructed/" + destino: "src/reconstructed/" + origem for origem, destino in MOVES}
EDICAO = {rel: pares for rel, pares in EDITS}


def inverso(rel):
    """Estado anterior pelo inverso das edicoes desta transformacao."""
    texto = le(os.path.join(ROOT, rel))
    for antes, depois in EDICAO[rel]:
        n = texto.count(depois)
        if n != 1:
            raise SystemExit("%s: %r aparece %d vezes" % (rel, depois[:50], n))
        texto = texto.replace(depois, antes)
    return texto


def antes_de(rel):
    """Devolve (texto_antes, texto_depois, e_novo)."""
    atual = le(os.path.join(ROOT, rel))
    if rel in MOVED:
        # a copia congelada tem a raiz `src/` ja removida: src-antes/reconstructed/...
        congelado = os.path.join(ANTES, MOVED[rel].replace("src/", "", 1))
        return le(congelado), atual, False
    if rel in EDICAO:
        reconstruido = inverso(rel)
        congelado = os.path.join(ANTES, rel.replace("src/", "", 1)) if rel.startswith("src/") else None
        if congelado and os.path.exists(congelado):
            if le(congelado) != reconstruido:
                raise SystemExit("%s: o inverso nao bate com a copia congelada" % rel)
        return reconstruido, atual, False
    return "", atual, True


def diff(antes, depois, nome_antes, nome_depois):
    return "".join(difflib.unified_diff(
        antes.splitlines(keepends=True), depois.splitlines(keepends=True),
        fromfile=nome_antes, tofile=nome_depois, n=3))


def main() -> int:
    print("=" * 78)
    print("REGISTRO DOS DIFFS DA OPP-20261003-GUE7")
    print("=" * 78)
    total = 0
    for arquivo, alvos in LOTES:
        corpo = []
        for rel in alvos:
            antes, depois, novo = antes_de(rel)
            if rel in MOVED:
                origem = MOVED[rel]
                corpo.append("rename from %s\nrename to %s\n" % (origem, rel))
                corpo.append(diff(antes, depois, "a/" + origem, "b/" + rel))
            elif novo:
                corpo.append(diff("", depois, "/dev/null", "b/" + rel))
            else:
                corpo.append(diff(antes, depois, "a/" + rel, "b/" + rel))
        texto = "".join(corpo)
        with open(os.path.join(HERE, arquivo), "w", encoding="utf-8", newline="") as fh:
            fh.write(texto)
        print("  %-34s %2d arquivo(s)  %6d bytes" % (arquivo, len(alvos), len(texto.encode("utf-8"))))
        total += len(alvos)
    print()
    print("=" * 78)
    print("RESULTADO: 6 LOTES, %d ARQUIVOS TOCADOS" % total)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
