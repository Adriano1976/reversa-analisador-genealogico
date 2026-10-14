"""Balanco antes/depois da correcao da busca, nos cartoes da analise real.

Prova o que a correcao NAO fez: nenhum cartao que tinha caminho perdeu o caminho, e nenhum
cartao ganhou caminho onde nao havia ancestral comum.

O "antes" e reconstruido rodando a copia fiel do corpo anterior de `find_ancestral_path` sobre
os mesmos pares — o codigo de producao nao e tocado para isso.
"""
from __future__ import annotations

import os
import sys
from collections import Counter, deque

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.family_navigation import get_parents  # noqa: E402
from core.path_finding import find_ancestral_path  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

GED = os.path.join(RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")


def busca_antiga(arvore, start_id, end_id, max_depth=20):
    """Copia fiel do corpo anterior a correcao (teste contra o comportamento passado)."""
    q1, q2 = deque([(start_id, [start_id])]), deque([(end_id, [end_id])])
    v1, v2 = {start_id: [start_id]}, {end_id: [end_id]}
    if start_id == end_id:
        return ([start_id], start_id)
    for _ in range(max_depth):
        qs = len(q1)
        if not qs:
            break
        for _ in range(qs):
            cur, path = q1.popleft()
            if cur in v2:
                return (path + v2[cur][::-1][1:], cur)
            for p in get_parents(arvore, cur):
                if p not in v1:
                    v1[p] = path + [p]
                    q1.append((p, path + [p]))
        qs = len(q2)
        if not qs:
            break
        for _ in range(qs):
            cur, path = q2.popleft()
            if cur in v1:
                return (v1[cur] + path[::-1][1:], cur)
            for p in get_parents(arvore, cur):
                if p not in v2:
                    v2[p] = path + [p]
                    q2.append((p, path + [p]))
    return (None, None)


arvore = carregar_arvore(GED)
deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
resultados, _d, mensagem = dna_analysis(CSV, "Adriano Santos", deps, arvore)
raiz = "@I6f405a00@"
print(mensagem)

ganharam, perderam, iguais_com, iguais_sem = [], [], 0, 0
for r in resultados:
    alvo = (r["documentary"].get("person_b") or {}).get("id")
    if not alvo:
        continue
    antigo = busca_antiga(arvore, raiz, alvo)[0]
    novo = find_ancestral_path(arvore, raiz, alvo)[0]
    if antigo is None and novo is not None:
        ganharam.append((r, novo))
    elif antigo is not None and novo is None:
        perderam.append(r)
    elif novo is not None:
        iguais_com += 1
    else:
        iguais_sem += 1

print()
print("=" * 90)
print("BALANCO")
print("=" * 90)
print(f"   cartoes avaliados                      : {len(resultados)}")
print(f"   ja tinham caminho e continuam com ele  : {iguais_com}")
print(f"   nao tinham e continuam sem             : {iguais_sem}")
print(f"   GANHARAM caminho (o defeito)           : {len(ganharam)}")
print(f"   PERDERAM caminho (regressao)           : {len(perderam)}  <-- tem de ser ZERO")

for r, caminho in ganharam:
    print(f"      + {r['match_name']}  ({len(caminho)} nos)")

print()
print("   status dos cartoes, agora:")
for status, quantos in Counter(r["documentary"].get("status") for r in resultados).most_common():
    print(f"      {status:<12} {quantos}")

assert not perderam, f"REGRESSAO: {[r['match_name'] for r in perderam]}"
print()
print("   nenhum cartao perdeu caminho: OK")
