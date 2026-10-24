"""Medicao 2: quem usa o que, e as chaves dos dois dicionarios de cartao."""
from __future__ import annotations

import ast
import pathlib
import re
import subprocess

RAIZ = pathlib.Path(__file__).resolve().parents[3]
ALVO = RAIZ / "src" / "core" / "documentary_relationship.py"
fonte = ALVO.read_text(encoding="utf-8")
arvore = ast.parse(fonte)

exportados = []
for no in arvore.body:
    if isinstance(no, ast.Assign):
        for alvo in no.targets:
            if isinstance(alvo, ast.Name) and alvo.id == "__all__":
                exportados = [e.value for e in no.value.elts]
print("__all__:", len(exportados))

print()
print("=== quem importa cada nome exportado (import explicito) ===")
for nome in exportados:
    donos = []
    for caminho in sorted((RAIZ / "src").rglob("*.py")):
        if caminho == ALVO:
            continue
        texto = caminho.read_text(encoding="utf-8")
        for i, linha in enumerate(texto.splitlines(), 1):
            if "documentary_relationship" in linha and nome in linha:
                donos.append(f"{caminho.relative_to(RAIZ)}:{i}")
                break
        else:
            # uso qualificado: core.documentary_relationship.NOME
            if re.search(r"documentary_relationship\." + re.escape(nome) + r"\b", texto):
                donos.append(f"{caminho.relative_to(RAIZ)}:qualificado")
    for caminho in sorted((RAIZ / "tests").rglob("*.py")):
        texto = caminho.read_text(encoding="utf-8")
        if re.search(r"documentary_relationship\b", texto) and re.search(r"\b" + re.escape(nome) + r"\b", texto):
            donos.append(f"{caminho.relative_to(RAIZ)}:teste")
    print(f"  {nome:32} {len(donos):3}  {donos[:4]}")

print()
print("=== chaves devolvidas pelos dois construtores de cartao ===")


def chaves_de(nome_funcao):
    for no in ast.walk(arvore):
        if isinstance(no, ast.FunctionDef) and no.name == nome_funcao:
            for sub in ast.walk(no):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Dict):
                    return {k.value for k in sub.value.keys if isinstance(k, ast.Constant)}
    return set()


a = chaves_de("documentary_relationship")
b = chaves_de("documental_nao_encontrado")
print("documentary_relationship :", len(a), sorted(a))
print("documental_nao_encontrado:", len(b), sorted(b))
print("so no caminho encontrado  :", sorted(a - b))
print("so no nao encontrado      :", sorted(b - a))

print()
print("=== quem le as chaves de hop_evidence e homonym_dossier ===")
for funcao in ("hop_evidence", "homonym_dossier"):
    for no in ast.walk(arvore):
        if isinstance(no, ast.FunctionDef) and no.name == funcao:
            for sub in ast.walk(no):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Dict):
                    ks = [k.value for k in sub.value.keys if isinstance(k, ast.Constant)]
                    print(f"  {funcao}: {len(ks)} chaves -> {ks}")

print()
print("=== leituras de chave em quem consome (grep de item['x']) ===")
for chave in ("link_source", "family_husband", "family_wife", "identical_data",
              "similar_matches", "differences", "exact_matches", "ambiguous_identity",
              "additional_paths", "common_ancestors", "evidence", "homonyms"):
    total = 0
    for caminho in list((RAIZ / "src").rglob("*.py")) + list((RAIZ / "tests").rglob("*.py")):
        texto = caminho.read_text(encoding="utf-8")
        total += len(re.findall(r"\[[\"']" + re.escape(chave) + r"[\"']\]|\.get\([\"']" + re.escape(chave) + r"[\"']", texto))
    print(f"  {chave:22} {total:3}")
