"""Procura um Manoel "Vieira" nascido em 1936 nos GEDCOMs ativos.

O operador afirma que outro arquivo .ged tem esse Manoel com nascimento em 1936, e que o kit
TG8027863 (do cartao de 25,4 cM) e dele. Esta sonda localiza o registro, para medir se a idade
resolveria o homonimo.
"""
from __future__ import annotations

import os
import re

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
UPLOADS = os.path.join(RAIZ, "src", "uploads")


def registros(texto: str):
    for m in re.finditer(r"(?s)^0 (@[^@]+@) INDI\n(.*?)(?=^0 )", texto, re.M):
        yield m.group(1), m.group(0)


def dados(bloco: str):
    nome = re.search(r"^1 NAME (.*)$", bloco, re.M)
    nasc = re.search(r"^2 DATE (.*)$", bloco, re.M)
    return (nome.group(1).strip() if nome else "?"), (nasc.group(1).strip() if nasc else "")


print("=== TODOS OS GEDCOMs: registros 'Vieira' nascidos em 1936 ===")
for nome_arq in sorted(os.listdir(UPLOADS)):
    if not nome_arq.endswith(".ged"):
        continue
    caminho = os.path.join(UPLOADS, nome_arq)
    with open(caminho, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    achados = []
    for xref, bloco in registros(texto):
        nome_p, nasc = dados(bloco)
        if "Vieira" in nome_p and "1936" in nasc:
            achados.append((xref, nome_p, nasc))
    print(f"--- {nome_arq} ({len(texto):,} bytes) ---")
    for xref, nome_p, nasc in achados:
        print(f"    {xref}  {nome_p}  nascimento {nasc}")
    if not achados:
        print("    nenhum")

print()
print("=== 'Manoel' nascidos entre 1900 e 1950, em cada arquivo ===")
for nome_arq in sorted(os.listdir(UPLOADS)):
    if not nome_arq.endswith(".ged"):
        continue
    caminho = os.path.join(UPLOADS, nome_arq)
    with open(caminho, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    achados = []
    for xref, bloco in registros(texto):
        nome_p, nasc = dados(bloco)
        if "Manoel" not in nome_p:
            continue
        if re.search(r"(19[0-4]\d|1950)", nasc):
            achados.append((xref, nome_p, nasc))
    if achados:
        print(f"--- {nome_arq} ---")
        for xref, nome_p, nasc in achados[:20]:
            print(f"    {xref}  {nome_p}  nascimento {nasc}")
