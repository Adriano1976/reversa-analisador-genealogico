"""Achar o caminho entre duas pessoas.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica: a
busca direta por ancestral comum (BFS bidirecional) e a busca indireta por
afinidade (`nx.shortest_path` com compressao de nos de familia), com os limites
que a alma fixa: profundidade 20 e 40 hops.

## Contrato de import com `.upload`

`people` e mutado in place, entao vem do topo. `graph` e a excecao: e
reatribuido a cada parse (`graph = new_graph`), entao um import no topo ficaria
preso ao grafo antigo, e ele continua sendo importado dentro de
`find_indirect_path`.
"""
from __future__ import annotations

from collections import deque

import networkx as nx

from .family_navigation import get_parents
from .upload import people


MAX_DEPTH = 20


MAX_HOPS = 40


def find_indirect_path(start_id, end_id, max_hops=MAX_HOPS):
    """Procura QUALQUER caminho no grafo pessoa<->família.

    Retorna apenas os nós de pessoa, comprimindo os nós de família.
    """
    # `graph` é reatribuído por `load_gedcom_and_build_graph` (graph = new_graph),
    # então um import no topo ficaria preso ao grafo antigo. Ver o contrato no topo.
    from .upload import graph
    if graph is None or start_id not in graph or end_id not in graph:
        return None
    try:
        path = nx.shortest_path(graph, source=start_id, target=end_id)  # BFS não ponderado
        if len(path) - 1 > max_hops:
            return None
        person_path = [n for n in path if n in people]
        return person_path if len(person_path) >= 2 else None
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def find_ancestral_path(start_id, end_id, max_depth=MAX_DEPTH):
    """BFS bidirecional subindo por pais (profundidade máx. max_depth).

    Retorna `(path, common_ancestor)` ou `(None, None)`.
    """
    q1, q2 = deque([(start_id, [start_id])]), deque([(end_id, [end_id])])
    visited1, visited2 = {start_id: [start_id]}, {end_id: [end_id]}
    if start_id == end_id:
        return ([start_id], start_id)
    for _depth in range(max_depth):
        q_size = len(q1)
        if not q_size:
            break
        for _ in range(q_size):
            curr_id, path = q1.popleft()
            if curr_id in visited2:
                return (path + visited2[curr_id][::-1][1:], curr_id)
            for p_id in get_parents(curr_id):
                if p_id not in visited1:
                    new_path = path + [p_id]
                    visited1[p_id] = new_path
                    q1.append((p_id, new_path))
        q_size = len(q2)
        if not q_size:
            break
        for _ in range(q_size):
            curr_id, path = q2.popleft()
            if curr_id in visited1:
                return (visited1[curr_id] + path[::-1][1:], curr_id)
            for p_id in get_parents(curr_id):
                if p_id not in visited2:
                    new_path = path + [p_id]
                    visited2[p_id] = new_path
                    q2.append((p_id, new_path))
    return (None, None)
