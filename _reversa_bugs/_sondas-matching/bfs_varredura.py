"""Varredura global: quantas pessoas da arvore o defeito escondia, nao so nos 62 cartoes.

Os cartoes da analise de DNA passam por matching por nome e cobrem apenas parte das pessoas da
arvore. Aqui a pergunta e outra: para uma amostra grande de pessoas do GEDCOM, quantas ganham
caminho com a correcao? E a medida de alcance do defeito, sem o funil do matching.

A amostra e deterministica (passo fixo sobre a lista de pessoas), para o numero ser
reproduzivel.
"""
from __future__ import annotations

import os
import sys
from collections import Counter, deque

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.family_navigation import get_parents  # noqa: E402
from core.path_finding import find_ancestral_path  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

GED = os.path.join(RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
RAIZ_ID = "@I6f405a00@"
PASSO = 40   # 1 pessoa a cada 40, deterministicamente


def busca_antiga(arvore, start_id, end_id, max_depth=20):
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
ids = list(arvore[0])
amostra = [pid for i, pid in enumerate(ids) if i % PASSO == 0 and pid != RAIZ_ID]
print(f"pessoas na arvore: {len(ids)} | amostra: {len(amostra)} (1 a cada {PASSO})")

balanco = Counter()
ganharam = []
for pid in amostra:
    antigo = busca_antiga(arvore, RAIZ_ID, pid)[0]
    novo = find_ancestral_path(arvore, RAIZ_ID, pid)[0]
    if antigo is None and novo is not None:
        balanco["ganharam"] += 1
        ganharam.append((pid, len(novo)))
    elif antigo is not None and novo is None:
        balanco["PERDERAM"] += 1
    elif novo is not None:
        balanco["ja tinham"] += 1
    else:
        balanco["sem caminho nos dois"] += 1

print()
print("=" * 80)
print("RESULTADO DA AMOSTRA")
print("=" * 80)
for chave in ("ja tinham", "ganharam", "sem caminho nos dois", "PERDERAM"):
    print(f"   {chave:<22} {balanco[chave]}")
total = sum(balanco.values())
if total:
    print(f"   taxa de ganho: {100 * balanco['ganharam'] / total:.1f}% da amostra")

print()
print("   os que ganharam (id, nos do caminho):")
for pid, nos in ganharam[:25]:
    print(f"      {pid}  {nos} nos")
if len(ganharam) > 25:
    print(f"      ... e mais {len(ganharam) - 25}")
