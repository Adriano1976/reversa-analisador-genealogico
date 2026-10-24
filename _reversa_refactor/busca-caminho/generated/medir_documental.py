"""Medicao da auditoria de 2026-10-24 de src/core/documentary_relationship.py.

Somente leitura: le o arquivo e o projeto, nao escreve nada.
"""
from __future__ import annotations

import ast
import collections
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parents[3]
ALVO = RAIZ / "src" / "core" / "documentary_relationship.py"

fonte = ALVO.read_text(encoding="utf-8")
arvore = ast.parse(fonte)

print("=== tamanho e blocos ===")
blocos = []
for no in arvore.body:
    if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
        blocos.append((no.name, no.lineno, no.end_lineno, no.end_lineno - no.lineno + 1))
    elif isinstance(no, ast.ClassDef):
        blocos.append((no.name, no.lineno, no.end_lineno, no.end_lineno - no.lineno + 1))
print(f"{'nome':38} {'ini':>4} {'fim':>4} {'linhas':>6}")
for nome, ini, fim, tam in blocos:
    print(f"{nome:38} {ini:4} {fim:4} {tam:6}")
print("total de linhas fisicas:", len(fonte.splitlines()))
print("total de defs:", len(blocos))
print("linhas em defs:", sum(b[3] for b in blocos))

print()
print("=== acesso posicional ao tuplo arvore ===")
contagem = collections.Counter()
for no in ast.walk(arvore):
    if isinstance(no, ast.Subscript) and isinstance(no.value, ast.Name) and no.value.id == "arvore":
        if isinstance(no.slice, ast.Constant):
            contagem[no.slice.value] += 1
print("arvore[N]:", dict(sorted(contagem.items())), "total", sum(contagem.values()))

print()
print("=== imports do modulo ===")
for no in ast.walk(arvore):
    if isinstance(no, ast.ImportFrom):
        print(" from", no.module, "->", [a.name for a in no.names])
    elif isinstance(no, ast.Import):
        print(" import", [a.name for a in no.names])

print()
print("=== quem consome o modulo ===")
padrao = re.compile(r"\bdocumentary_relationship\b")
for caminho in sorted((RAIZ / "src").rglob("*.py")):
    if caminho == ALVO:
        continue
    texto = caminho.read_text(encoding="utf-8")
    if padrao.search(texto):
        linhas = [i + 1 for i, l in enumerate(texto.splitlines()) if padrao.search(l)]
        print(f"  {caminho.relative_to(RAIZ)}: {linhas}")

print()
print("=== testes que citam o modulo ===")
for caminho in sorted((RAIZ / "tests").rglob("*.py")):
    texto = caminho.read_text(encoding="utf-8")
    if padrao.search(texto):
        print(f"  {caminho.relative_to(RAIZ)}")

print()
print("=== construcao do tuplo da arvore ===")
for no in ast.walk(arvore):
    pass
for caminho in sorted((RAIZ / "src").rglob("*.py")):
    texto = caminho.read_text(encoding="utf-8")
    for i, linha in enumerate(texto.splitlines(), 1):
        if "return (" in linha or ("people" in linha and "families" in linha and "graph" in linha):
            if "def " in linha:
                continue
            print(f"  {caminho.relative_to(RAIZ)}:{i}: {linha.strip()[:110]}")
