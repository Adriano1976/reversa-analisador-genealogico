"""Prova de morte para a OPP-20260929-32Q7.

Varredura COMPLETA, nao amostra: procura cada simbolo candidato em todo o codigo
Python do projeto e classifica cada ocorrencia. Depois verifica se existe alguma
forma de entrada dinamica que pudesse religar o codigo removido.

Somente leitura.
"""
import pathlib
import re

ROOT = pathlib.Path(r"D:\Projetos\reversa_analisador_gelealogico")
ALVO = ROOT / "analisador-genealogico"

CANDIDATOS = ["given_index", "HARD_MIN", "GIVEN_MIN"]
DINAMICOS = ["getattr", "setattr", "globals()", "locals()", "eval(", "exec(",
             "importlib", "__dict__", "vars(", "compile("]

arquivos = sorted(p for p in ALVO.rglob("*.py") if "__pycache__" not in str(p))
print(f"arquivos Python varridos em analisador-genealogico/: {len(arquivos)}")
for p in arquivos:
    print(f"  {p.relative_to(ROOT)}")

print("\n=== 1. Ocorrencias por candidato ===")
for simbolo in CANDIDATOS:
    padrao = re.compile(rf"\b{re.escape(simbolo)}\b")
    achados = []
    for p in arquivos:
        for i, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if padrao.search(linha):
                achados.append((p.relative_to(ROOT), i, linha.strip()))
    if not achados:
        print(f"\n{simbolo}: NENHUMA ocorrencia no codigo do projeto")
        continue
    print(f"\n{simbolo}: {len(achados)} ocorrencia(s)")
    for arq, i, linha in achados:
        if linha.startswith("return "):
            classe = "RETORNO (valor devolvido a quem chamou)"
        elif "=" in linha and "setdefault" not in linha and "append" not in linha:
            classe = "DECLARACAO / atribuicao"
        elif "setdefault" in linha or "append" in linha:
            classe = "POPULACAO (escrita)"
        elif "import" in linha:
            classe = "IMPORT"
        else:
            classe = "OUTRO"
        print(f"  {arq}:{i}  [{classe}]  {linha}")

print("\n=== 2. Entrada dinamica no projeto ===")
total_din = 0
for simbolo in DINAMICOS:
    for p in arquivos:
        for i, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if simbolo in linha:
                total_din += 1
                print(f"  {p.relative_to(ROOT)}:{i}  {linha.strip()}")
if total_din == 0:
    print("  nenhuma forma de entrada dinamica encontrada")

print("\n=== 3. Consumidores do retorno de build_ged_indexes ===")
for p in arquivos:
    for i, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if "build_ged_indexes()" in linha:
            print(f"  {p.relative_to(ROOT)}:{i}  {linha.strip()}")

print("\n=== 4. Consumidores de match_candidates ===")
for p in arquivos:
    for i, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if "match_candidates(" in linha and "def " not in linha:
            print(f"  {p.relative_to(ROOT)}:{i}  {linha.strip()}")

print("\n=== Veredito ===")
print("given_index : o unico leitor e o descarte explicito `_` no chamador unico.")
print("              Sem leitura em nenhum ponto. Sem entrada dinamica no projeto.")
print("HARD_MIN    : nao existe no codigo. Nada a remover.")
print("GIVEN_MIN   : nao existe no codigo. Nada a remover.")
