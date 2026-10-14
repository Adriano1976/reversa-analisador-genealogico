"""O que a imagem do GEDmatch acrescenta: 1936, os pais, e o kit de origem.

A imagem traz, para o kit TG8027863:
  - "Manoel Vieira da Silva", nascimento "25 de janeiro de 1936";
  - pais: Antonio de Souza Vieira e Therezinha dos Santos;
  - irmao: Agenor Prokopek da Silva; conjuge: Cecília de Aguiar Figueiredo;
  - filhos: Manoel Vieira da Silva;
  - arvore de origem: "Familia Sergipana" (ancestral project), 5.097 membros;
  - cM total 25,4 (7,9 + 17,5) e "MRCA = 4.6" no proprio GEDmatch.

Esta sonda cruza esses nomes com a arvore ATIVA e com o outro GEDCOM, para medir:
  1. alguem nascido em 1936 com esses pais existe no dado carregado?
  2. os pais (Antonio de Souza Vieira / Therezinha dos Santos) existem?
  3. qual dos registros "Manoel ... Vieira" tem janela de vida compativel com 1936?
"""
from __future__ import annotations

import os
import re
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.family_navigation import get_parents  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from core.documentary_relationship import birth_date, parse_year  # noqa: E402

UPLOADS = os.path.join(RAIZ, "src", "uploads")
GED_ATIVO = os.path.join(UPLOADS, "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
GED_ADRIANO = os.path.join(UPLOADS, "b3211a52a933fdd0__Adriano_Santos.ged")

arvore = carregar_arvore(GED_ATIVO)
people = arvore[0]


def buscar(termo: str, limite: int = 12):
    """Pessoas cujo nome contem o termo (comparacao sem acento e sem caixa)."""
    import unicodedata
    alvo = unicodedata.normalize("NFKD", termo).encode("ascii", "ignore").decode().lower()
    saida = []
    for pid, p in people.items():
        nome = get_name(p)
        chave = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
        if alvo in chave:
            saida.append((pid, nome, birth_date(people, pid)))
        if len(saida) >= limite:
            break
    return saida


print("=" * 100)
print("1. OS PAIS DO MANOEL DE 1936 EXISTEM NA ARVORE ATIVA?")
print("=" * 100)
for termo in ("Antonio de Souza Vieira", "Therezinha dos Santos", "Cecilia de Aguiar",
              "Agenor Prokopek"):
    achados = buscar(termo)
    print(f"   {termo!r}: {len(achados)} ocorrencia(s)")
    for pid, nome, nasc in achados[:6]:
        print(f"      {pid:<14} {nome:<44} {nasc or '(sem data)'}")

print()
print("=" * 100)
print("2. QUEM NA ARVORE TEM NASCIMENTO EM 1936 E SOBRENOME VIEIRA?")
print("=" * 100)
for pid, p in people.items():
    nome = get_name(p)
    if "Vieira" not in nome:
        continue
    ano = parse_year(birth_date(people, pid))
    if ano and 1930 <= ano <= 1940:
        pais = [get_name(people[x]) for x in get_parents(arvore, pid) if x in people]
        print(f"   {pid:<14} {nome:<40} {birth_date(people, pid):<18} pais={pais}")

print()
print("=" * 100)
print("3. OS 4 'Manoel da Silva Vieira': janela de vida contra 1936")
print("=" * 100)
for pid in ("@I8bf4f5b7@", "@I55271618@", "@I3052bc4c@", "@I02fa7bd1@"):
    nome = get_name(people[pid])
    nasc = birth_date(people, pid)
    ano = parse_year(nasc)
    pais = [f"{get_name(people[x])}" for x in get_parents(arvore, pid) if x in people]
    idade_hoje = (2026 - ano) if ano else None
    veredito = ""
    if idade_hoje is not None:
        veredito = "vivo hoje" if idade_hoje <= 115 else f"morto ha {idade_hoje - 115} anos"
    print(f"   {pid:<14} nasceu {nasc:<14} -> {idade_hoje} anos em 2026  [{veredito}]")
    print(f"                  pais no GEDCOM: {pais}")

print()
print("=" * 100)
print("4. O OUTRO GEDCOM (Adriano_Santos.ged) TEM ESSE MANOEL?")
print("=" * 100)
try:
    outra = carregar_arvore(GED_ADRIANO)
    op = outra[0]
    for pid, p in op.items():
        nome = get_name(p)
        if "Manoel" in nome and "Vieira" in nome:
            print(f"   {pid:<14} {nome:<40} {birth_date(op, pid) or '(sem data)'}")
except Exception as erro:
    print(f"   falhou: {type(erro).__name__}: {erro}")
