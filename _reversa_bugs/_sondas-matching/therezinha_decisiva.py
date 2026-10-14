"""A pergunta decisiva: Soraia ganha por ser a pessoa certa, ou so por ter um sobrenome a mais?

Monta a arvore MINIMA (so as duas pessoas envolvidas) e roda o matching de producao.
Nenhum arquivo do projeto e tocado.
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

ALVO = "Therezinha Carvalho do Nascimento Souza"
CM = 31.9
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_sonda.ged")

CABECALHO = """0 HEAD
1 SOUR teste
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
"""

CENARIOS = {
    "1. Como esta hoje (Soraia com 'Souza', Therezinha sem)": [
        ("@I1@", "Soraia Carvalho do Nascimento /Souza/"),
        ("@I2@", "Therezinha Carvalho do /Nascimento/"),
    ],
    "2. Soraia perde o 'Souza' (os dois empatam em 2 sobrenomes)": [
        ("@I1@", "Soraia Carvalho do /Nascimento/"),
        ("@I2@", "Therezinha Carvalho do /Nascimento/"),
    ],
    "3. So a Therezinha existe na arvore": [
        ("@I2@", "Therezinha Carvalho do /Nascimento/"),
    ],
}

for rotulo, pessoas in CENARIOS.items():
    linhas = [CABECALHO]
    for xref, nome in pessoas:
        linhas.append(f"0 {xref} INDI\n1 NAME {nome}\n")
    linhas.append("0 TRLR\n")
    with open(TMP, "w", encoding="utf-8") as f:
        f.write("".join(linhas))

    arvore = carregar_arvore(TMP)
    ged_index, surname_index, features = build_ged_indexes(arvore)
    cands, motivo = match_candidates(arvore, ALVO, CM, ged_index, surname_index, features)
    escolhido = get_name(arvore[0][cands[0]]) if cands else "(descartado)"
    print(rotulo)
    print(f"   escolhida: {escolhido}")
    print(f"   motivo   : {motivo}")
    print()

os.remove(TMP)
