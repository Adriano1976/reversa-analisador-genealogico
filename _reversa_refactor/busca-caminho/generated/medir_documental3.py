"""Medicao 3: importacao real por AST, em src, tests e instrumentos congelados."""
from __future__ import annotations

import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[3]
ALVO = RAIZ / "src" / "core" / "documentary_relationship.py"
MODULO = "documentary_relationship"

usos: dict[str, list[str]] = {}
qualificados: list[str] = []


def visitar(caminho: pathlib.Path, rotulo: str) -> None:
    try:
        texto = caminho.read_text(encoding="utf-8")
        arvore = ast.parse(texto)
    except (UnicodeDecodeError, SyntaxError):
        return
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            mod = no.module or ""
            if mod.endswith(MODULO) or (no.level and MODULO in mod):
                for a in no.names:
                    usos.setdefault(a.name, []).append(f"{rotulo}:{no.lineno}")
        elif isinstance(no, ast.Attribute) and isinstance(no.value, ast.Name) and no.value.id == MODULO:
            pass
        elif isinstance(no, ast.Attribute):
            # core.documentary_relationship.funcao
            base = no.value
            if isinstance(base, ast.Attribute) and base.attr == MODULO:
                qualificados.append(f"{rotulo}:{no.lineno}:{no.attr}")


for pasta in ("src", "tests"):
    for caminho in sorted((RAIZ / pasta).rglob("*.py")):
        if caminho == ALVO:
            continue
        visitar(caminho, str(caminho.relative_to(RAIZ)))

for caminho in sorted((RAIZ / "_reversa_bugs").rglob("*.py")):
    visitar(caminho, str(caminho.relative_to(RAIZ)))
for caminho in sorted((RAIZ / "_reversa_sdd").rglob("*.py")):
    visitar(caminho, str(caminho.relative_to(RAIZ)))

fonte = ALVO.read_text(encoding="utf-8")
arvore = ast.parse(fonte)
exportados = []
for no in arvore.body:
    if isinstance(no, ast.Assign):
        for alvo in no.targets:
            if isinstance(alvo, ast.Name) and alvo.id == "__all__":
                exportados = [e.value for e in no.value.elts]

print("=== nomes exportados e quem os importa de fora ===")
for nome in exportados:
    alvos = usos.get(nome, [])
    print(f"  {nome:32} {len(alvos):3}  {alvos[:5]}")

print()
print("=== nomes publicos NAO exportados que alguem importa ===")
for nome, alvos in sorted(usos.items()):
    if nome not in exportados:
        print(f"  {nome:32} {len(alvos):3}  {alvos[:5]}")

print()
print("=== uso qualificado (modulo.funcao) ===")
print(" ", qualificados[:20] or "nenhum")

print()
print("=== chamadas internas por nome (dentro do proprio arquivo) ===")
chamadas: dict[str, int] = {}
for no in ast.walk(arvore):
    if isinstance(no, ast.Call) and isinstance(no.func, ast.Name):
        chamadas[no.func.id] = chamadas.get(no.func.id, 0) + 1
for nome in exportados:
    if nome in chamadas:
        print(f"  interno {nome:32} {chamadas[nome]}")
