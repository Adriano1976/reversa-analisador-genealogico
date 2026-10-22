"""Achar o caminho entre duas pessoas, numa arvore recebida por parametro.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica: a
busca direta por ancestral comum (BFS bidirecional) e a busca indireta por
afinidade (`nx.shortest_path` com compressao de nos de familia), com os limites
que a alma fixa: profundidade 20 e 40 hops.

## A arvore entra por parametro (feature 005, T012)

Antes, `people` vinha de um import no topo e `graph` de um import DENTRO da
funcao, porque `graph` era reatribuido a cada parse e um import no topo ficaria
preso ao grafo antigo. Nenhum dos dois existe mais: o estado global saiu
(`T023`), e os dois saem da arvore recebida.

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

    ## O encontro e testado no DESCOBRIMENTO, e nao na saida da fila

    Ate 2026-10-13 este teste ficava so no `popleft`: o no era comparado com a fronteira
    oposta quando **saia** da fila deste lado. Isso produzia falso negativo, e o caso
    medido esta no GEDCOM real `Arvore_Unificada_Oficial_V1_2.ged`:

    - `Adriano Santos` (`@I6f405a00@`) e `Therezinha Carvalho do Nascimento Souza`
      (`@Ied60620a@`) tem **5 ancestrais comuns** (9 passos de um lado, 6 do outro);
    - a fronteira da Therezinha alcanca os 67 ancestrais dela e **esvazia** na oitava
      iteracao; a da raiz ainda expandia e so chegaria a regiao comum na nona;
    - o laco faz `break` quando uma das filas esvazia, entao o lado da raiz foi
      abandonado — e os **quatro** ancestrais comuns ja estavam nos dois conjuntos de
      visitados, sem que ninguem comparasse;
    - resultado: "Parentesco documental nao encontrado" para um par que tem caminho de
      **16 nos** e parentesco "Primos de 5º grau (três gerações de diferença)".

    Nao era o teto: subir `max_depth` para 40, 60, 80, 120 ou 200 nao muda o resultado,
    porque quem interrompe a busca e a fila vazia, e nao o limite de iteracoes. Por isso
    `MAX_DEPTH` continua **20** — o teto nao era o defeito, e mexe-lo so esconderia a causa.

    A correcao e a comparacao no instante em que o pai e descoberto. Ela e
    **puramente aditiva**: so encontra pares que ja tinham ancestral comum no arquivo, e
    nao pode criar falso positivo nem derrubar um "nao encontrado" que fosse correto.
    Medido nos 62 cartoes da analise real do operador: **5 cartoes** saiam de
    "nao encontrado" para "encontrado", todos com caminho verdadeiro.

    ## Enquanto houver fila de um lado, a busca continua

    O `if not q1: break` (e o irmao para `q2`) saiu: uma fronteira que esvazia so significa
    que aquele lado terminou de subir, e nao que a resposta nao exista. Quem encerra a
    busca e o teto de iteracoes, ou as duas filas vazias.

    ## O caminho concatenado

    O caminho sai como `caminho1 + [encontro] + caminho2`, com `caminho2` ja na ordem
    de subida a partir de `end_id` (herdada do `visited2`). O `visited` guarda o caminho
    na ordem de descoberta, entao o da fronteira invertida **nao** e girado aqui — o
    caminho que os testes de paridade congelaram ja saia assim, e girar mudaria a ordem
    exibida dos descendentes.
    """
    q1, q2 = deque([(start_id, [start_id])]), deque([(end_id, [end_id])])
    visited1, visited2 = {start_id: [start_id]}, {end_id: [end_id]}
    if start_id == end_id:
        return ([start_id], start_id)
    for _depth in range(max_depth):
        if q1:
            q_size = len(q1)
            for _ in range(q_size):
                curr_id, path = q1.popleft()
                for p_id in get_parents(arvore, curr_id):
                    if p_id in visited2:
                        return (path + [p_id] + visited2[p_id][::-1][1:], p_id)
                    if p_id not in visited1:
                        visited1[p_id] = path + [p_id]
                        q1.append((p_id, path + [p_id]))
        if q2:
            q_size = len(q2)
            for _ in range(q_size):
                curr_id, path = q2.popleft()
                for p_id in get_parents(arvore, curr_id):
                    if p_id in visited1:
                        return (visited1[p_id] + path[::-1], p_id)
                    if p_id not in visited2:
                        visited2[p_id] = path + [p_id]
                        q2.append((p_id, path + [p_id]))
        if not q1 and not q2:
            break
    return (None, None)
