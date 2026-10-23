"""Gera a imagem DEPOIS da OPP-20261023-DOCF, sem tocar no projeto.

Le `src/core/dna_analysis.py`, confere os dois trechos por linha e escreve uma
copia sem eles. O diff entre a copia ANTES e a copia DEPOIS e o CHG-001.

Roda da raiz do projeto:  python _reversa_refactor/.../gerar-depois.py
"""
from __future__ import annotations

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[4]
ALVO = RAIZ / "src" / "core" / "dna_analysis.py"

SAIDA_ANTES = pathlib.Path(__file__).resolve().parent / "before-after" / "antes.py"
SAIDA_DEPOIS = pathlib.Path(__file__).resolve().parent / "before-after" / "depois.py"

LINHA_INICIAL_DOCSTRING = 558
LINHA_FINAL_DOCSTRING = 571
NOME_MORTO = '"dna_analysis", "Dependencias", "DNAAnalyzer",'
NOME_NOVO = '"dna_analysis", "Dependencias",'


def main() -> int:
    original = ALVO.read_text(encoding="utf-8")
    linhas = original.splitlines(keepends=True)

    primeira = linhas[LINHA_INICIAL_DOCSTRING - 1].strip()
    ultima = linhas[LINHA_FINAL_DOCSTRING - 1].strip()
    if not primeira.startswith('"""Executa o fluxo completo'):
        print(f"ABORTA: linha {LINHA_INICIAL_DOCSTRING} nao e o inicio esperado: {primeira!r}")
        return 1
    if ultima != '"""':
        print(f"ABORTA: linha {LINHA_FINAL_DOCSTRING} nao e o fecho esperado: {ultima!r}")
        return 1

    removidas = linhas[LINHA_INICIAL_DOCSTRING - 1 : LINHA_FINAL_DOCSTRING]
    print(f"removendo {len(removidas)} linhas ({LINHA_INICIAL_DOCSTRING}-{LINHA_FINAL_DOCSTRING})")

    restantes = linhas[: LINHA_INICIAL_DOCSTRING - 1] + linhas[LINHA_FINAL_DOCSTRING :]
    depois = "".join(restantes)

    if depois.count(NOME_MORTO) != 1:
        print(f"ABORTA: {NOME_MORTO!r} nao aparece exatamente uma vez")
        return 1
    depois = depois.replace(NOME_MORTO, NOME_NOVO)
    print("removido 1 nome de __all__")

    SAIDA_ANTES.write_bytes(original.encode("utf-8"))
    SAIDA_DEPOIS.write_bytes(depois.encode("utf-8"))
    print(f"antes:  {SAIDA_ANTES}  ({len(original.splitlines())} linhas)")
    print(f"depois: {SAIDA_DEPOIS}  ({len(depois.splitlines())} linhas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
