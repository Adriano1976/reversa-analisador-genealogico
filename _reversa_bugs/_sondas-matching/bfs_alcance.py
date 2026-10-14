"""Mede o alcance do defeito da BFS bidirecional nos cartoes da analise real.

Cruza os pares (raiz, match aceito) da analise de DNA e conta quantos cartoes dizem
"Parentesco documental nao encontrado" **tendo** ancestral comum alcancavel — ou seja,
quantos resultados a correcao da busca mudaria.

Nao altera nada: le a arvore ativa e o CSV, e roda as duas buscas em paralelo (a do codigo e
uma copia corrigida).
"""
from __future__ import annotations

import os
import sys
from collections import deque

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

import core.path_finding as pf  # noqa: E402
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
RAIZ_DA_ARVORE = "Adriano Santos"


def busca_corrigida(arvore, start_id, end_id, max_depth=20):
    """A mesma busca, checando o encontro no DESCOBRIMENTO (copia de prova, nao de producao)."""
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


arvore = carregar_arvore(GED)
people = arvore[0]
deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
resultados, _descartados, mensagem = dna_analysis(CSV, RAIZ_DA_ARVORE, deps, arvore)
print(mensagem)
print()

# A raiz resolvida, igual ao nucleo: o primeiro id cujo nome contem o texto informado.
raiz_id = next(pid for pid, p in people.items() if RAIZ_DA_ARVORE.lower() in get_name(p).lower())
print(f"raiz resolvida: {raiz_id} {get_name(people[raiz_id])}")
print()

mudam = []
for r in resultados:
    alvo = (r["documentary"].get("person_b") or {}).get("id")
    if not alvo:
        continue
    status_atual = r["documentary"].get("status")
    tem_caminho = bool((r["documentary"].get("path") or {}).get("ids"))
    corrigido, comum = busca_corrigida(arvore, raiz_id, alvo)
    if not tem_caminho and corrigido:
        mudam.append((r, comum, corrigido))

print("=" * 100)
print(f"CARTOES QUE MUDAM DE 'NAO ENCONTRADO' PARA 'ENCONTRADO': {len(mudam)} de {len(resultados)}")
print("=" * 100)
for r, comum, caminho in mudam:
    print(f"   CSV  : {r['csv_name']}")
    print(f"   GED  : {r['match_name']}   ({r['cm']} cM)")
    print(f"   ancestral comum : {comum} {get_name(people[comum])}")
    print(f"   caminho ({len(caminho)} nos): {' -> '.join(get_name(people[x]) for x in caminho)}")
    print()
