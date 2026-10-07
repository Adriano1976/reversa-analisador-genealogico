"""T023 (b): os testes leem a arvore DEVOLVIDA pelo parse, nao o estado global.

## O que muda, e por que assim

O `(a)` parou de mutar as globais: `carregar_arvore` devolve dicionarios e grafo
NOVOS. Todo teste que lia `_gs.people` depois do parse quebrou — 70 deles.

A correcao e guardar o RETORNO do parse num modulo de fixtura unico
(`tests/fixtures/arvore_atual.py`) e apontar os helpers para ele. Deste jeito:

- o teste continua dizendo o que sempre disse (o parse acontece, e le-se a
  arvore resultante);
- a leitura passa a ser a do VALOR, e nao a de um global mutado de lado;
- quando `gedcom_state` for removido, nao ha mais nada a mudar nos testes.

Nenhuma assercao e alterada.
"""
import ast
import io
import os
import re

# ---- o modulo de fixtura que guarda a arvore da ultima carga -----------------
FIxtura = '''"""A arvore carregada pelo ULTIMO parse (feature 005, T023).

## Por que isto existe

Ate a feature 005, `load_gedcom_and_build_graph` mutava as globais de
`core.gedcom_state`, e os testes liam `_gs.people` depois. O parse passou a
DEVOLVER a arvore e a nao escrever estado, entao a leitura passou a ser do valor.

Este modulo guarda o resultado da ultima carga para os testes que precisam da
arvore depois de chama-la. Nao e estado de dominio: e o retorno do parse, que o
teste guardou porque o perdeu de vista — o parse acontece antes da assercao.

Enquanto houver uma carga por teste, e equivalente a ler o global; a diferenca e
que o valor e o que o parse DEVOLVEU, e nao um efeito colateral dele.
"""
from __future__ import annotations

ATUAL = None


def guardar(arvore):
    """Guarda a arvore devolvida pelo parse. Devolve a propria arvore."""
    global ATUAL
    ATUAL = arvore
    return arvore


def atual():
    """A arvore do ultimo parse. Levanta se nenhum parse aconteceu."""
    if ATUAL is None:
        raise AssertionError(
            "nenhuma arvore carregada: chame o parse (ou `carregar`) antes"
        )
    return ATUAL
'''

# ---- por arquivo: como o parse e chamado, e como a arvore e lida ------------
# (arquivo, antigo, novo)
TROCAS = [
    # garda o retorno nos helpers de carga
    ("tests/test_confrontacao_gedcom_dna.py",
     "        gedcom_parser.load_gedcom_and_build_graph(caminho)",
     "        guardar(gedcom_parser.carregar_arvore(caminho))"),
    ("tests/test_upload.py",
     "        gedcom_parser.load_gedcom_and_build_graph(path)",
     "        guardar(gedcom_parser.carregar_arvore(path))"),
    ("tests/test_dna_analysis.py",
     "        gedcom_parser.load_gedcom_and_build_graph(ged_path)",
     "        guardar(gedcom_parser.carregar_arvore(ged_path))"),
    ("tests/test_characterization_matching.py",
     "        gedcom_parser.load_gedcom_and_build_graph(path)",
     "        guardar(gedcom_parser.carregar_arvore(path))"),
    ("tests/test_path_search.py",
     "        gedcom_parser.load_gedcom_and_build_graph(path)",
     "        guardar(gedcom_parser.carregar_arvore(path))"),
    ("tests/test_characterization_mermaid.py",
     "        gedcom_parser.load_gedcom_and_build_graph(path)",
     "        guardar(gedcom_parser.carregar_arvore(path))"),
    ("tests/test_formatacao_cm.py",
     "        load_gedcom_and_build_graph(ged)",
     "        guardar(carregar_arvore(ged))"),
]

# leitura da arvore: `_arvore_de(_gs)` e `_arvore()` viram `atual()`
LEITURA = [
    ("_arvore_de(_gs)", "atual()"),
    ("_arvore()", "atual()"),
    ("_gs.people", "atual()[0]"),
    ("_gs.families", "atual()[1]"),
    ("_gs.graph", "atual()[2]"),
    ("_gs.child_to_family", "atual()[3]"),
]

IMPORT = "from tests.fixtures.arvore_atual import atual, guardar\n"


def main() -> int:
    cam = os.path.join("tests", "fixtures", "arvore_atual.py")
    if not os.path.exists(cam):
        io.open(cam, "w", encoding="utf-8", newline="").write(FIxtura)
        print("criado %s" % cam)

    arquivos = sorted({a for a, _, _ in TROCAS})
    for caminho in arquivos:
        texto = io.open(caminho, encoding="utf-8").read()
        for alvo, antigo, novo in TROCAS:
            if alvo != caminho:
                continue
            n = texto.count(antigo)
            if n == 0:
                print("  AVISO carga (0): %s" % caminho)
                continue
            texto = texto.replace(antigo, novo)
            print("  carga (%d)  %s" % (n, caminho))
        for antigo, novo in LEITURA:
            if antigo in texto:
                texto = texto.replace(antigo, novo)
        if re.search(r"(?<![\w.])atual\(\)", texto) and IMPORT not in texto:
            linhas = texto.splitlines(keepends=True)
            alvo_i = 0
            for i, l in enumerate(linhas):
                if l.startswith("import ") or l.startswith("from "):
                    alvo_i = i
            linhas.insert(alvo_i + 1, IMPORT)
            texto = "".join(linhas)
        ast.parse(texto)
        io.open(caminho, "w", encoding="utf-8", newline="").write(texto)
    print("APLICADO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
