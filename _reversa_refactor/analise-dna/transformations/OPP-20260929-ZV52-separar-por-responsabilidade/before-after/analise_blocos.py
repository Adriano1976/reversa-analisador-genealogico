"""Analise o acoplamento entre os blocos de dna_analysis.py, por AST.

Nao estima nada: le o arquivo, agrupa as instrucoes de nivel de modulo pelos
banners que o proprio autor ja escreveu, e calcula para cada bloco:

  - quais nomes de nivel de modulo ele DEFINE
  - quais nomes definidos em OUTRO bloco ele REFERENCIA

Isso da o grafo de dependencia real entre as responsabilidades, que e o que
decide se a divisao proposta cria ou nao um ciclo de import.

Uso:
    python <este script>
"""

from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
ALVO = os.path.join(ROOT, "analisador-genealogico", "reconstructed", "dna_analysis.py")

# Fronteiras declaradas pelo proprio autor do modulo, pelos banners de secao.
BLOCOS = [
    ("head",                "docstring e imports",              1,  25),
    ("cm_e_vocabulario",    "faixas de cM e vocabulario",      26,  67),
    ("normalizacao",        "normalizacao e nomes",            69, 145),
    ("csv_ingest",          "leitura e agregacao do CSV",     147, 199),
    ("matching",            "indices e matching difuso",      201, 341),
    ("fluxo",               "fluxo principal",                343, 402),
]


def bloco_de(linha):
    for nome, _, ini, fim in BLOCOS:
        if ini <= linha <= fim:
            return nome
    return None


def main() -> int:
    src = open(ALVO, encoding="utf-8").read()
    arvore = ast.parse(src)
    total = src.count("\n") + (0 if src.endswith("\n") else 1)

    definidos = {}      # nome -> bloco
    linhagem = {}       # nome -> linha da definicao
    for no in arvore.body:
        alvos = []
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            alvos = [no.name]
        elif isinstance(no, ast.Assign):
            alvos = [t.id for t in no.targets if isinstance(t, ast.Name)]
        elif isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
            alvos = [no.target.id]
        for a in alvos:
            definidos[a] = bloco_de(no.lineno)
            linhagem[a] = no.lineno

    defs_por_bloco = {}
    for nome, bloco in definidos.items():
        defs_por_bloco.setdefault(bloco, []).append(nome)

    usos = {nome: set() for nome, _, _, _ in BLOCOS}
    for no in ast.walk(arvore):
        if isinstance(no, ast.Name) and isinstance(no.ctx, ast.Load):
            dono = definidos.get(no.id)
            if dono is None:
                continue
            onde = bloco_de(no.lineno)
            if onde and onde != dono:
                usos[onde].add(no.id)

    print("ACOPLAMENTO ENTRE OS BLOCOS DE dna_analysis.py")
    print("arquivo: %s" % os.path.relpath(ALVO, ROOT))
    print("linhas : %d" % total)
    print("=" * 78)
    for nome, rotulo, ini, fim in BLOCOS:
        d = sorted(defs_por_bloco.get(nome, []))
        print("\n%-18s linhas %3d-%-3d  (%3d linhas)  %s" % (nome, ini, fim, fim - ini + 1, rotulo))
        print("  define     (%2d): %s" % (len(d), ", ".join(d) if d else "-"))
        u = sorted(usos[nome])
        if u:
            for nome_usado in u:
                print("  usa de %-16s: %s (definido na linha %d)"
                      % (definidos[nome_usado], nome_usado, linhagem[nome_usado]))
        else:
            print("  usa de outro bloco: nenhum")

    print("\n" + "=" * 78)
    print("GRAFO ENTRE BLOCOS (quem depende de quem)")
    arestas = set()
    for nome, _, _, _ in BLOCOS:
        for usado in usos[nome]:
            arestas.add((nome, definidos[usado]))
    for a, b in sorted(arestas):
        print("  %-18s -> %s" % (a, b))
    if not arestas:
        print("  nenhuma")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
