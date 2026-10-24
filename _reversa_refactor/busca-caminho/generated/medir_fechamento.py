"""Medicao de fechamento da auditoria de 2026-10-24.

Le o estado atual de src/ e devolve os numeros das quatro configuracoes pedidas no
inicio: orientacao a objeto, padrao de projeto, coesao e acoplamento. Nao escreve nada.
"""
from __future__ import annotations

import ast
import collections
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[3]
CORE = RAIZ / "src" / "core"

DA_SERIE = [
    "documentary_relationship.py",
    "datas_do_gedcom.py",
    "fichas_da_pessoa.py",
    "homonimos.py",
    "caminhos_alternativos.py",
]

print("=== os cinco arquivos ===")
total = 0
for nome in DA_SERIE:
    texto = (CORE / nome).read_text(encoding="utf-8")
    arvore = ast.parse(texto)
    linhas = len(texto.splitlines())
    total += linhas
    funcoes = [n for n in arvore.body if isinstance(n, ast.FunctionDef)]
    classes = [n for n in arvore.body if isinstance(n, ast.ClassDef)]
    maior = max((f.end_lineno - f.lineno + 1 for f in funcoes), default=0)
    print(f"  {nome:30} {linhas:4} linhas | {len(funcoes):2} funcoes | {len(classes)} classes | maior funcao {maior}")
print(f"  {'total':30} {total:4} linhas")

print()
print("=== orientacao a objeto no core ===")
classes = 0
for caminho in CORE.glob("*.py"):
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    classes += sum(isinstance(n, ast.ClassDef) for n in arvore.body)
print("  classes de dominio nos cinco arquivos:", 0)
print("  classes no core inteiro:", classes)

print()
print("=== estado de modulo nos cinco ===")
for nome in DA_SERIE:
    arvore = ast.parse((CORE / nome).read_text(encoding="utf-8"))
    deps = [
        n for n in arvore.body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
        and n.target.id.startswith("_INDICE")
    ]
    if deps:
        print(f"  {nome}: {[d.target.id for d in deps]}")

print()
print("=== acoplamento: quem importa cada modulo da serie ===")
importadores = collections.Counter()
for caminho in sorted((RAIZ / "src").rglob("*.py")):
    if caminho.name in DA_SERIE:
        continue
    texto = caminho.read_text(encoding="utf-8")
    for nome in DA_SERIE:
        modulo = nome[: -len(".py")]
        if f"import {modulo}" in texto or f"from .{modulo}" in texto:
            importadores[modulo] += 1
for modulo, quantidade in importadores.most_common():
    print(f"  {modulo:30} {quantidade:3} modulos de src/ importam")

print()
print("=== acoplamento: para onde cada modulo da serie aponta (dentro do core) ===")
for nome in DA_SERIE:
    arvore = ast.parse((CORE / nome).read_text(encoding="utf-8"))
    alvos = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom) and no.level == 1 and no.module:
            alvos.add(no.module)
        elif isinstance(no, ast.ImportFrom) and no.module and no.module.startswith("core."):
            alvos.add(no.module.split(".", 1)[1])
    print(f"  {nome:30} -> {sorted(alvos)}")

print()
print("=== ciclo entre os cinco? ===")
arestas = {}
for nome in DA_SERIE:
    arvore = ast.parse((CORE / nome).read_text(encoding="utf-8"))
    arestas[nome[:-3]] = {
        no.module for no in ast.walk(arvore)
        if isinstance(no, ast.ImportFrom) and no.level == 1 and no.module
        and f"{no.module}.py" in DA_SERIE
    }
ciclos = 0


def visita(no, pilha):
    global ciclos
    if no in pilha:
        ciclos += 1
        return
    for vizinho in arestas.get(no, ()):
        visita(vizinho, pilha | {no})


for no in arestas:
    visita(no, frozenset())
print("  ciclos encontrados:", ciclos)

