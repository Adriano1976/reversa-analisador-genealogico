"""Achar o caminho entre duas pessoas, numa arvore recebida por parametro.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica: a
busca direta por ancestral comum (BFS bidirecional) e a busca indireta por
afinidade (`nx.shortest_path` com compressao de nos de familia), com os limites
que a alma fixa: profundidade 20 e 40 hops.

## A arvore entra por parametro (feature 005, T012)

Antes, `people` vinha de um import no topo e `graph` de um import DENTRO da
funcao, porque `graph` era reatribuido a cada parse e um import no topo ficaria
preso ao grafo antigo. A assimetria sumiu: os dois saem da arvore recebida.

## O que NAO pode mudar

`MAX_DEPTH` conta ITERACOES do BFS bidirecional, nao geracoes — a extracao
anterior descrevia como "20 niveis" e estava errada. E a ordem de insercao das
arestas do grafo decide qual caminho o `nx.shortest_path` devolve quando ha mais
de um de mesmo comprimento, entao ela e contrato de paridade (tag `@ordem`).
"""
from __future__ import annotations

from collections import deque

import networkx as nx

from .family_navigation import get_parents

Arvore = tuple


MAX_DEPTH = 20


MAX_HOPS = 40


def find_indirect_path(arvore: Arvore, start_id, end_id, max_hops=MAX_HOPS):
    """Procura QUALQUER caminho no grafo pessoa<->família.

    Retorna apenas os nós de pessoa, comprimindo os nós de família.
    """
    people, _families, graph, _child_to_family = arvore
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


def find_ancestral_path(arvore: Arvore, start_id, end_id, max_depth=MAX_DEPTH):
    """BFS bidirecional subindo por pais (profundidade maxima max_depth).

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
            for p_id in get_parents(arvore, curr_id):
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
            for p_id in get_parents(arvore, curr_id):
                if p_id not in visited2:
                    new_path = path + [p_id]
                    visited2[p_id] = new_path
                    q2.append((p_id, new_path))
    return (None, None)
