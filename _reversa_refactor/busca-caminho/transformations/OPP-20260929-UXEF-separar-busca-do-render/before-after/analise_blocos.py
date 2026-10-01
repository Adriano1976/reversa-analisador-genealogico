"""Analise o acoplamento entre os blocos de path_search.py, por AST.

Diferente da versao usada na ZV52, esta tambem rastreia QUAIS nomes importados
cada bloco referencia. Isso e o que decide a lista de imports de cada modulo
novo, e e o que permite prever o custo de import por fronteira.

Blocos definidos pelos banners que o proprio autor do modulo escreveu.

Uso:
    python <este script>
"""

from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
ALVO = os.path.join(ROOT, "analisador-genealogico", "reconstructed", "path_search.py")

BLOCOS = [
    ("head",            "docstring, imports e constantes",   1,  27),
    ("resolucao",       "resolucao de pessoa por nome",     28,  41),
    ("navegacao",       "navegacao familiar",               42, 125),
    ("busca",           "busca de caminho",                126, 186),
    ("render",          "renderizacao Mermaid",            187, 464),
    ("handler",         "handler do fluxo",                465, 508),
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

    # --- simbolos definidos no nivel de modulo ------------------------------
    definidos, linhagem, fim_de = {}, {}, {}
    for no in arvore.body:
        alvos = []
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            alvos = [no.name]
        elif isinstance(no, ast.Assign):
            alvos = [t.id for t in no.targets if isinstance(t, ast.Name)]
        else:
            continue
        for a in alvos:
            definidos[a] = bloco_de(no.lineno)
            linhagem[a] = no.lineno
            fim_de[a] = no.end_lineno

    # --- nomes importados, por onde sao importados --------------------------
    importados = {}     # nome local -> modulo de origem
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for a in no.names:
                importados[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(no, ast.ImportFrom):
            mod = ("." * (no.level or 0)) + (no.module or "")
            for a in no.names:
                importados[a.asname or a.name] = mod

    # --- imports que NAO estao no topo (o caso de `graph` dentro da funcao) --
    fora_do_topo = []
    for no in ast.walk(arvore):
        if isinstance(no, (ast.Import, ast.ImportFrom)) and no.col_offset != 0:
            nomes = [a.asname or a.name for a in no.names]
            fora_do_topo.append((no.lineno, bloco_de(no.lineno), nomes))

    # --- uso por bloco ------------------------------------------------------
    usos_def, usos_imp = {n: set() for n, _, _, _ in BLOCOS}, {n: set() for n, _, _, _ in BLOCOS}
    for no in ast.walk(arvore):
        if isinstance(no, ast.Name) and isinstance(no.ctx, ast.Load):
            onde = bloco_de(no.lineno)
            if not onde:
                continue
            if no.id in definidos and definidos[no.id] != onde:
                usos_def[onde].add(no.id)
            elif no.id in importados:
                usos_imp[onde].add(no.id)

    print("ACOPLAMENTO ENTRE OS BLOCOS DE path_search.py")
    print("arquivo: %s" % os.path.relpath(ALVO, ROOT))
    print("linhas : %d" % total)
    print("=" * 78)

    defs_por_bloco = {}
    for nome, bloco in definidos.items():
        defs_por_bloco.setdefault(bloco, []).append(nome)

    for nome, rotulo, ini, fim in BLOCOS:
        d = sorted(defs_por_bloco.get(nome, []))
        print("\n%-12s linhas %3d-%-3d (%3d linhas) %s" % (nome, ini, fim, fim - ini + 1, rotulo))
        if d:
            for s in d:
                print("   define %-42s linha %3d-%3d (%3d linhas)"
                      % (s, linhagem[s], fim_de[s], fim_de[s] - linhagem[s] + 1))
        else:
            print("   define: -")
        if usos_def[nome]:
            print("   usa de outro bloco : %s" % ", ".join(sorted(usos_def[nome])))
        if usos_imp[nome]:
            print("   usa importado      : %s"
                  % ", ".join("%s(%s)" % (n, importados[n]) for n in sorted(usos_imp[nome])))

    print("\n" + "=" * 78)
    print("IMPORTS FORA DO TOPO")
    for linha, bloco, nomes in fora_do_topo:
        print("   linha %3d no bloco %-10s %s" % (linha, bloco, nomes))
    if not fora_do_topo:
        print("   nenhum")

    print("\n" + "=" * 78)
    print("GRAFO ENTRE BLOCOS (quem depende de quem)")
    arestas = set()
    for nome, _, _, _ in BLOCOS:
        for usado in usos_def[nome]:
            arestas.add((nome, definidos[usado]))
    for a, b in sorted(arestas):
        print("   %-12s -> %s" % (a, b))
    if not arestas:
        print("   nenhuma")

    print("\n" + "=" * 78)
    print("DEPENDENCIAS EXTERNAS POR BLOCO (para prever o custo de import)")
    for nome, _, _, _ in BLOCOS:
        if usos_imp[nome]:
            mods = sorted(set(importados[n] for n in usos_imp[nome]))
            print("   %-12s %s" % (nome, ", ".join(mods)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
