"""Registra os CHG-*.diff da OPP-20261003-RGKA.

Compara a copia pristina guardada em before-after/dna_analysis.antes.py com o
arquivo atual e grava o diff unificado. Os dois arquivos novos sao registrados
como diff contra /dev/null. Escreve apenas nesta pasta de transformacao.
"""
from __future__ import annotations

import difflib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

ANTES = os.path.join(HERE, "before-after", "dna_analysis.antes.py")
ATUAL = os.path.join(ROOT, "src", "reconstructed", "dna_analysis.py")
NOVOS = [
    ("CHG-001-core-init.diff", "src/reconstructed/core/__init__.py"),
    ("CHG-002-core-cm-estimator.diff", "src/reconstructed/core/cm_estimator.py"),
]


def linhas(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.readlines()


def grava(nome, texto):
    destino = os.path.join(HERE, nome)
    with open(destino, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)
    print("%-34s %5d bytes" % (nome, len(texto.encode("utf-8"))))


def main() -> int:
    for nome, rel in NOVOS:
        caminho = os.path.join(ROOT, rel)
        d = difflib.unified_diff([], linhas(caminho),
                                 fromfile="/dev/null", tofile="b/" + rel, n=3)
        grava(nome, "".join(d))

    d = difflib.unified_diff(linhas(ANTES), linhas(ATUAL),
                             fromfile="a/src/reconstructed/dna_analysis.py",
                             tofile="b/src/reconstructed/dna_analysis.py", n=3)
    grava("CHG-003-dna-analysis.diff", "".join(d))

    antes = open(ANTES, encoding="utf-8").read()
    atual = open(ATUAL, encoding="utf-8").read()
    print()
    print("linhas dna_analysis.py: antes %d, depois %d" % (len(antes.splitlines()), len(atual.splitlines())))
    print("tabela de cM ainda no dna_analysis.py? %s" % ("SIM" if "SHARED_CM_DATA = [" in atual else "nao"))
    print("tabela de cM preservada byte a byte no modulo novo? %s" % (
        "sim" if atual_bloco(antes) in open(os.path.join(ROOT, "src", "reconstructed", "core", "cm_estimator.py"), encoding="utf-8").read() else "NAO"))
    return 0


def atual_bloco(texto):
    """Extrai a lista original, do 'SHARED_CM_DATA = [' ate o ']' de fechamento."""
    inicio = texto.index("SHARED_CM_DATA = [")
    fim = texto.index("\n]", inicio) + 2
    return texto[inicio:fim]


if __name__ == "__main__":
    raise SystemExit(main())
