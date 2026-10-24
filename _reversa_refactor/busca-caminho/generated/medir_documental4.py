"""Medicao 4: alcance do acesso posicional ao tuplo da arvore em src/."""
from __future__ import annotations

import ast
import collections
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[3]

total = collections.Counter()
por_arquivo: dict[str, int] = {}
for caminho in sorted((RAIZ / "src").rglob("*.py")):
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    n = 0
    for no in ast.walk(arvore):
        if isinstance(no, ast.Subscript) and isinstance(no.value, ast.Name) and no.value.id in {"arvore", "tree"}:
            if isinstance(no.slice, ast.Constant) and isinstance(no.slice.value, int):
                n += 1
                total[no.slice.value] += 1
    if n:
        por_arquivo[str(caminho.relative_to(RAIZ))] = n

for arquivo, n in sorted(por_arquivo.items(), key=lambda x: -x[1]):
    print(f"{n:4}  {arquivo}")
print()
print("total:", sum(por_arquivo.values()), "| por indice:", dict(sorted(total.items())))

desempacotados = 0
for caminho in sorted((RAIZ / "src").rglob("*.py")):
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    for no in ast.walk(arvore):
        if isinstance(no, ast.Assign) and isinstance(no.value, ast.Name) and no.value.id == "arvore":
            if isinstance(no.targets[0], ast.Tuple):
                desempacotados += 1
                print(f"desempacotamento: {caminho.relative_to(RAIZ)}:{no.lineno}")
print("desempacotamentos de `arvore`:", desempacotados)
