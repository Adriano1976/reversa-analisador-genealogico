"""Ancestrais comuns, cadeias ate eles e caminhos alternativos.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). Ele responde pela enumeracao
que existe alem do caminho principal: quantos ancestrais comuns ha, quantas cadeias levam a
cada um e por onde passa o caminho alternativo.
"""
from __future__ import annotations

from collections import deque

from .datas_do_gedcom import birth_date
from .family_navigation import get_parents
from .registro import get_name

# Teto de expansao da busca por TODOS os ancestrais comuns. O caminho principal
# continua vindo de `find_ancestral_path` (contrato congelado); a enumeracao
# completa existe para contar caminhos alternativos e detectar colapso.
MAX_DEPTH_ALTERNATIVOS = 12
LIMITE_DE_CADEIAS = 8


def _ancestor_depths(arvore, start_id, max_depth: int) -> dict:
    """Menor numero de saltos de `start_id` ate cada ancestral (BFS por pais)."""
    profundidades = {}
    fronteira = [start_id]
    for nivel in range(1, max_depth + 1):
        proxima = []
        for pid in fronteira:
            for pai in get_parents(arvore, pid):
                if pai == start_id or pai in profundidades:
                    continue
                profundidades[pai] = nivel
                proxima.append(pai)
        if not proxima:
            break
        fronteira = proxima
    return profundidades


def _cadeias_ate(arvore, start_id, alvo, max_depth: int, limite=LIMITE_DE_CADEIAS) -> int:
    """Quantas cadeias distintas de pais levam de `start_id` ate `alvo`.

    Mais de uma cadeia ate o MESMO ancestral e a assinatura de colapso de
    pedigree (primos que se casam, endogamia). A contagem para no `limite`.
    """
    if start_id == alvo:
        return 1
    total = 0
    pilha = deque([(start_id, 0)])
    while pilha:
        pid, nivel = pilha.popleft()
        if nivel >= max_depth:
            continue
        for pai in get_parents(arvore, pid):
            if pai == alvo:
                total += 1
                if total >= limite:
                    return total
            else:
                pilha.append((pai, nivel + 1))
    return total


def _cadeia_curta(arvore, start_id, alvo, max_depth):
    """Caminho mais curto de `start_id` ate `alvo` subindo por pais."""
    anterior = {start_id: None}
    fila = deque([(start_id, 0)])
    while fila:
        pid, nivel = fila.popleft()
        if pid == alvo:
            break
        if nivel >= max_depth:
            continue
        for pai in get_parents(arvore, pid):
            if pai not in anterior:
                anterior[pai] = pid
                fila.append((pai, nivel + 1))
    if alvo not in anterior:
        return None
    cadeia, atual = [], alvo
    while atual is not None:
        cadeia.append(atual)
        atual = anterior[atual]
    return cadeia[::-1]


def find_all_common_ancestors(arvore, a_id, b_id, max_depth=MAX_DEPTH_ALTERNATIVOS, limit=12) -> list:
    """Todos os ancestrais comuns dentro do teto, ordenados por distancia total."""
    de_a = _ancestor_depths(arvore, a_id, max_depth)
    de_b = _ancestor_depths(arvore, b_id, max_depth)
    comuns = []
    for pid in set(de_a) & set(de_b):
        da, db = de_a[pid], de_b[pid]
        comuns.append({
            "id": pid,
            "name": get_name(arvore[0].get(pid)),
            "distance_a": da,
            "distance_b": db,
            "total_meioses": da + db,
            "birth": birth_date(arvore[0], pid),
        })
    comuns.sort(key=lambda c: (c["total_meioses"], max(c["distance_a"], c["distance_b"]), c["name"] or "")) # type: ignore
    return comuns[:limit]


def _caminho_alternativo(arvore, a_id, b_id, ancestral_id):
    subida = _cadeia_curta(arvore, a_id, ancestral_id, MAX_DEPTH_ALTERNATIVOS)
    descida = _cadeia_curta(arvore, b_id, ancestral_id, MAX_DEPTH_ALTERNATIVOS)
    if not subida or not descida:
        return None
    ids = subida + descida[::-1][1:]
    return {"ids": ids, "names": [get_name(arvore[0].get(i)) for i in ids], "via": ancestral_id}

__all__ = ["find_all_common_ancestors"]
