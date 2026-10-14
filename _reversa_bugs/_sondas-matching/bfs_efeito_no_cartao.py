"""O cartao da Therezinha com a busca de caminho corrigida: o que ele MOSTRARIA.

A correcao e aplicada por monkeypatch, so neste processo: `src/core/` nao e alterado. Serve
para medir o efeito antes de decidir se a correcao entra no codigo.
"""
from __future__ import annotations

import os
import sys
from collections import deque

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

import core.documentary_relationship as dr  # noqa: E402
from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.family_navigation import get_parents  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

GED = os.path.join(RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")
ALVO = "Therezinha Carvalho do Nascimento Souza"


def busca_corrigida(arvore, start_id, end_id, max_depth=20):
    if start_id == end_id:
        return ([start_id], start_id)
    q1, q2 = deque([(start_id, [start_id])]), deque([(end_id, [end_id])])
    v1, v2 = {start_id: [start_id]}, {end_id: [end_id]}
    for _ in range(max_depth):
        if q1:
            for _ in range(len(q1)):
                cur, path = q1.popleft()
                for p in get_parents(arvore, cur):
                    if p in v2:
                        return (path + [p] + v2[p][::-1][1:], p)
                    if p not in v1:
                        v1[p] = path + [p]
                        q1.append((p, path + [p]))
        if q2:
            for _ in range(len(q2)):
                cur, path = q2.popleft()
                for p in get_parents(arvore, cur):
                    if p in v1:
                        return (v1[p] + path[::-1], p)
                    if p not in v2:
                        v2[p] = path + [p]
                        q2.append((p, path + [p]))
        if not q1 and not q2:
            break
    return (None, None)


deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
arvore = carregar_arvore(GED)


def retrato(r):
    doc = r["documentary"]
    return (f"      status      : {doc.get('status')}\n"
            f"      parentesco  : {doc.get('label')}\n"
            f"      meioses     : {doc.get('meioses')}\n"
            f"      ancestral   : {(doc.get('common_ancestor') or {}).get('name')}\n"
            f"      caminho     : {r['text_path'] or '(nenhum)'}\n"
            f"      grafo       : {'sim' if r['mermaid_data'] else 'nao'}\n"
            f"      confronto   : {(r['comparison'] or {}).get('label')}\n"
            f"      observacoes : {(r['observations'] or ['(nenhuma)'])[0][:110]}")


print("=" * 100)
print("ANTES (busca de producao)")
print("=" * 100)
res, _d, _m = dna_analysis(CSV, "Adriano Santos", deps, arvore)
r = next(x for x in res if x["csv_name"] == ALVO)
print(f"   cartao: {r['match_name']}  ({r['cm']} cM)")
print(retrato(r))

print()
print("=" * 100)
print("DEPOIS (mesma analise, com a busca corrigida por monkeypatch)")
print("=" * 100)
dr.find_ancestral_path = busca_corrigida
res2, _d2, _m2 = dna_analysis(CSV, "Adriano Santos", deps, arvore)
r2 = next(x for x in res2 if x["csv_name"] == ALVO)
print(f"   cartao: {r2['match_name']}  ({r2['cm']} cM)")
print(retrato(r2))

if r2["mermaid_data"]:
    print()
    print("   --- Mermaid gerado (primeiras linhas) ---")
    for linha in r2["mermaid_data"].splitlines()[:14]:
        print(f"      {linha}")
