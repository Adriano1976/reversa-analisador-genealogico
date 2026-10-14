"""Onde esta o Manoel "Vieira" de 1936? Varredura de TODOS os .ged do projeto.

O operador diz que outro arquivo .ged traz esse Manoel com nascimento em 1936 e que o kit
TG8027863 e dele. Esta sonda procura em toda a arvore do repositorio, inclusive aposentados e
snapshots, para localizar o registro e comparar com os quatro da arvore ativa.
"""
from __future__ import annotations

import os
import re

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
PULAR = {"node_modules", ".git", ".venv", "__pycache__"}


def todos_os_ged():
    for base, pastas, arquivos in os.walk(RAIZ):
        pastas[:] = [p for p in pastas if p not in PULAR]
        for nome in arquivos:
            if nome.endswith(".ged"):
                yield os.path.join(base, nome)


print("=== REGISTROS 'Vieira' NASCIDOS EM 1936, EM TODO O PROJETO ===")
achou_algo = False
for caminho in todos_os_ged():
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            texto = f.read()
    except OSError:
        continue
    achados = []
    for m in re.finditer(r"(?s)^0 (@[^@]+@) INDI\n(.*?)(?=^0 )", texto, re.M):
        bloco = m.group(0)
        nome = re.search(r"^1 NAME (.*)$", bloco, re.M)
        nasc = re.search(r"^2 DATE (.*)$", bloco, re.M)
        if not nome or not nasc:
            continue
        if "Vieira" in nome.group(1) and "1936" in nasc.group(1):
            achados.append((m.group(1), nome.group(1).strip(), nasc.group(1).strip()))
    if achados:
        achou_algo = True
        rel = os.path.relpath(caminho, RAIZ)
        print(f"--- {rel} ({len(texto):,} bytes) ---")
        for xref, nome, nasc in achados:
            print(f"    {xref}  {nome}  nascimento {nasc}")
if not achou_algo:
    print("    NENHUM registro 'Vieira' com 1936 em nenhum .ged do projeto")

print()
print("=== REGISTROS COM 'Manoel' E 'Vieira' NO NOME, POR ARQUIVO ===")
for caminho in todos_os_ged():
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            texto = f.read()
    except OSError:
        continue
    achados = []
    for m in re.finditer(r"(?s)^0 (@[^@]+@) INDI\n(.*?)(?=^0 )", texto, re.M):
        bloco = m.group(0)
        nome = re.search(r"^1 NAME (.*)$", bloco, re.M)
        nasc = re.search(r"^2 DATE (.*)$", bloco, re.M)
        if not nome:
            continue
        n = nome.group(1)
        if "Manoel" in n and "Vieira" in n:
            achados.append((m.group(1), n.strip(), nasc.group(1).strip() if nasc else "(sem data)"))
    if achados:
        rel = os.path.relpath(caminho, RAIZ)
        print(f"--- {rel} ---")
        for xref, nome, nasc in achados:
            print(f"    {xref}  {nome}  nascimento {nasc}")
