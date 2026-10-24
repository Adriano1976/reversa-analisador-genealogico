"""Contagem fisica dos modulos que a SEPM criou e da fachada."""
from __future__ import annotations

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[4]
NOMES = [
    "documentary_relationship.py",
    "datas_do_gedcom.py",
    "fichas_da_pessoa.py",
    "homonimos.py",
    "caminhos_alternativos.py",
]
total = 0
for nome in NOMES:
    linhas = (RAIZ / "src" / "core" / nome).read_text(encoding="utf-8").splitlines()
    total += len(linhas)
    print(f"{nome:32} {len(linhas):4} linhas")
print(f"{'total dos cinco':32} {total:4}")
print()
print("core antes da divisao:", 22, "modulos")
print("core depois:", len(list((RAIZ / "src" / "core").glob("*.py"))), "modulos")
