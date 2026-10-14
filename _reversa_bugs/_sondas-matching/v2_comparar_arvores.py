"""Compara os GEDCOMs do projeto: quem tem quem, e se o Manoel de 1936 existe em algum.

Arquivos:
  - V1 (arvore ativa da analise): 46733fab...__Arvore_Unificada_Oficial_V1_2.ged
  - V2 (enviado agora):           Adriano_Santos_V2.ged  (nos anexos da sessao)
  - Adriano_Santos.ged (antigo):  b3211a52...__Adriano_Santos.ged

So LE. Nao escreve em nenhum dado.
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
    "V1 (arvore ativa da analise)":
        os.path.join(RAIZ, "src", "uploads",
                     "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged"),
    "V2 (enviado agora)":
        (r"C:\Users\venda\.dsh\attachments\v1\files\34"
         r"\343924dd424b3fba0dd221814e2ad3a8c72e48ff7125de903aee3b4c3319332a"
         r"\Adriano_Santos_V2.ged"),
    "Adriano_Santos.ged (antigo)":
        os.path.join(RAIZ, "src", "uploads", "b3211a52a933fdd0__Adriano_Santos.ged"),
}

ALVOS = [
    "Adriano Santos",
    "Manoel Vieira da Silva",
    "Manoel da Silva Vieira",
    "Antonio de Souza Vieira",
    "Therezinha dos Santos",
    "Cecilia de Aguiar",
    "Agenor Prokopek",
    "Therezinha Carvalho do Nascimento",
    "Soraia Carvalho do Nascimento",
]


def sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


arvores = {}
for rotulo, caminho in ARQUIVOS.items():
    if not os.path.isfile(caminho):
        print(f"!! {rotulo}: arquivo ausente")
        continue
    arvores[rotulo] = carregar_arvore(caminho)
    print(f"{rotulo}: {len(arvores[rotulo][0]):,} pessoas  ({os.path.getsize(caminho):,} bytes)")

print()
print("=" * 110)
print("PRESENCA DE CADA ALVO EM CADA ARQUIVO")
print("=" * 110)
largura = 26
print(f"{'alvo':<38}" + "".join(f"{r[:largura]:<{largura}}" for r in arvores))
for alvo in ALVOS:
    linha = f"{alvo:<38}"
    for rotulo, arvore in arvores.items():
        people = arvore[0]
        achados = []
        for pid, p in people.items():
            nome = get_name(p)
            if sem_acento(alvo) in sem_acento(nome):
                achados.append((pid, birth_date(people, pid)))
        if achados:
            resumo = ", ".join(f"{birth_date(people, px) or '?'}" for px, _ in achados[:2])
            if len(achados) > 2:
                resumo += f" (+{len(achados) - 2})"
            linha += f"{str(len(achados)) + ': ' + resumo:<{largura}}"
        else:
            linha += f"{'-':<{largura}}"
    print(linha)

print()
print("=" * 110)
print("QUEM TEM O ADRIANO SANTOS, E QUANDO NASCEU")
print("=" * 110)
for rotulo, arvore in arvores.items():
    people = arvore[0]
    for pid, p in people.items():
        nome = get_name(p)
        if sem_acento("Adriano") in sem_acento(nome) and sem_acento("Santos") in sem_acento(nome):
            print(f"   {rotulo:<32} {pid:<12} {nome:<30} {birth_date(people, pid)}")
