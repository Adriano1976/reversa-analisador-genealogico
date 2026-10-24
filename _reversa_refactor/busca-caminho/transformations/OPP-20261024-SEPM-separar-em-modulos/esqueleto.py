"""Lista o esqueleto do modulo: cada sentenca de topo com a faixa de linhas."""
from __future__ import annotations

import ast
import pathlib

ALVO = pathlib.Path(__file__).resolve().parents[4] / "src" / "core" / "documentary_relationship.py"
texto = ALVO.read_text(encoding="utf-8")
arvore = ast.parse(texto)

for no in arvore.body:
    tipo = type(no).__name__
    nome = getattr(no, "name", "")
    alvo = ""
    if tipo in {"FunctionDef", "ClassDef"}:
        alvo = nome
    elif tipo == "Assign":
        alvo = ", ".join(t.id for t in no.targets if isinstance(t, ast.Name))
    elif tipo == "AnnAssign":
        alvo = getattr(no.target, "id", "")
    print(f"{tipo:12} {alvo:38} {no.lineno:4}-{no.end_lineno:4}  ({no.end_lineno - no.lineno + 1})")

print()
print("total de linhas:", len(texto.splitlines()))
