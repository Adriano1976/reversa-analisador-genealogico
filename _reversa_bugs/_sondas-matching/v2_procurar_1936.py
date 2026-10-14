"""Procura no GEDCOM novo (Adriano_Santos_V2.ged) as pessoas da imagem do GEDmatch.

Alvos: Manoel Vieira da Silva (n. 25/01/1936), os pais Antonio de Souza Vieira e Therezinha dos
Santos, a conjuge Cecilia de Aguiar Figueiredo, o filho Manoel Vieira da Silva e o irmao
Agenor Prokopek da Silva.

So LE o arquivo enviado; nao escreve nele.
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.family_navigation import get_parents, get_spouses  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from core.documentary_relationship import birth_date, parse_year  # noqa: E402

CAMINHO = (r"C:\Users\venda\.dsh\attachments\v1\files\34"
           r"\343924dd424b3fba0dd221814e2ad3a8c72e48ff7125de903aee3b4c3319332a"
           r"\Adriano_Santos_V2.ged")

print(f"arquivo: {CAMINHO}")
print(f"existe: {os.path.isfile(CAMINHO)}  bytes: {os.path.getsize(CAMINHO):,}")
print()
arvore = carregar_arvore(CAMINHO)
people = arvore[0]
print(f"pessoas carregadas: {len(people):,}")
print()


def sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def buscar(termo: str, limite: int = 10):
    alvo = sem_acento(termo)
    saida = []
    for pid, p in people.items():
        nome = get_name(p)
        if alvo in sem_acento(nome):
            saida.append((pid, nome, birth_date(people, pid)))
        if len(saida) >= limite:
            break
    return saida


print("=" * 100)
print("1. AS PESSOAS DA IMAGEM")
print("=" * 100)
for termo in ("Manoel Vieira da Silva", "Manoel da Silva Vieira", "Antonio de Souza Vieira",
              "Therezinha dos Santos", "Cecilia de Aguiar", "Agenor Prokopek"):
    achados = buscar(termo)
    print(f"   {termo!r}: {len(achados)}")
    for pid, nome, nasc in achados:
        pais = [get_name(people[x]) for x in get_parents(arvore, pid) if x in people]
        conj = [get_name(people[x]) for x in get_spouses(arvore, pid) if x in people]
        print(f"      {pid:<14} {nome:<40} {str(nasc):<18}")
        print(f"                     pais={pais}")
        print(f"                     conjuge={conj}")

print()
print("=" * 100)
print("2. TODOS OS 'Vieira' NASCIDOS ENTRE 1930 E 1940")
print("=" * 100)
for pid, p in people.items():
    nome = get_name(p)
    if "Vieira" not in nome:
        continue
    ano = parse_year(birth_date(people, pid))
    if ano and 1930 <= ano <= 1940:
        pais = [get_name(people[x]) for x in get_parents(arvore, pid) if x in people]
        print(f"   {pid:<14} {nome:<40} {str(birth_date(people, pid)):<18} pais={pais}")
