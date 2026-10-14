"""A busca decisiva: o Manoel de 1936 e a familia dele existem em ALGUMA das arvores?

A imagem do GEDmatch diz: Manoel Vieira da Silva, n. 25/01/1936, pais Antonio de Souza Vieira
(1873-1950) e Therezinha dos Santos (1893-1958). Procura:
  1. QUALQUER pessoa nascida entre 1930 e 1940, nas tres arvores (nao so sobrenome Vieira);
  2. os pais por janela de data (Antonio ~1873, Therezinha ~1890-1910);
  3. todos os "Therezinha" e "Terezinha" com data, nas tres arvores.

So LE os arquivos.
"""
from __future__ import annotations

import os
import sys
import unicodedata

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.documentary_relationship import birth_date, parse_year  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

ARQUIVOS = {
    "V1": os.path.join(RAIZ, "src", "uploads",
                       "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged"),
    "V2": (r"C:\Users\venda\.dsh\attachments\v1\files\34"
           r"\343924dd424b3fba0dd221814e2ad3a8c72e48ff7125de903aee3b4c3319332a"
           r"\Adriano_Santos_V2.ged"),
    "ANTIGO": os.path.join(RAIZ, "src", "uploads",
                           "b3211a52a933fdd0__Adriano_Santos.ged"),
}


def sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


arvores = {r: carregar_arvore(c) for r, c in ARQUIVOS.items() if os.path.isfile(c)}

print("=" * 110)
print("1. TODOS OS NASCIDOS ENTRE 1930 E 1940 (qualquer sobrenome)")
print("=" * 110)
for rotulo, arvore in arvores.items():
    people = arvore[0]
    achados = []
    for pid, p in people.items():
        ano = parse_year(birth_date(people, pid))
        if ano and 1930 <= ano <= 1940:
            achados.append((ano, pid, get_name(p), birth_date(people, pid)))
    achados.sort()
    print(f"--- {rotulo}: {len(achados)} pessoas ---")
    for ano, pid, nome, nasc in achados[:25]:
        print(f"    {pid:<12} {nome:<44} {nasc}")
    if len(achados) > 25:
        print(f"    ... e mais {len(achados) - 25}")

print()
print("=" * 110)
print("2. 'Antonio ... Vieira' NASCIDO ENTRE 1860 E 1885 (o pai da imagem)")
print("=" * 110)
for rotulo, arvore in arvores.items():
    people = arvore[0]
    achados = []
    for pid, p in people.items():
        nome = get_name(p)
        if "Vieira" in nome and sem_acento("antonio") in sem_acento(nome):
            ano = parse_year(birth_date(people, pid))
            if ano and 1860 <= ano <= 1885:
                achados.append((ano, pid, nome, birth_date(people, pid)))
    achados.sort()
    print(f"--- {rotulo}: {len(achados)} ---")
    for ano, pid, nome, nasc in achados[:15]:
        print(f"    {pid:<12} {nome:<44} {nasc}")

print()
print("=" * 110)
print("3. TODOS OS 'Therezinha' / 'Terezinha dos Santos' COM DATA")
print("=" * 110)
for rotulo, arvore in arvores.items():
    people = arvore[0]
    achados = []
    for pid, p in people.items():
        nome = get_name(p)
        chave = sem_acento(nome)
        if ("therezinha" in chave or "terezinha" in chave) and "santos" in chave:
            achados.append((pid, nome, birth_date(people, pid)))
    print(f"--- {rotulo}: {len(achados)} ---")
    for pid, nome, nasc in achados:
        print(f"    {pid:<12} {nome:<44} {nasc or '(sem data)'}")
