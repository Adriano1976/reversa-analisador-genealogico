"""Contraprova: com o nome exato na arvore, o matching acerta; sem ele, cai na Soraia.

A arvore de teste e minima e montada AQUI (nenhum arquivo do projeto e tocado): o que se
mede e a decisao do motor de matching diante dos dois dados possiveis.
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.name_normalization import norm_name  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

ALVO = "Therezinha Carvalho do Nascimento Souza"
CM = 31.9

GED_SEM_SOUZA = """0 HEAD
1 SOUR teste
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Soraia Carvalho do Nascimento /Souza/
0 @I2@ INDI
1 NAME Therezinha Carvalho do /Nascimento/
0 TRLR
"""

GED_COM_SOUZA = """0 HEAD
1 SOUR teste
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Soraia Carvalho do Nascimento /Souza/
0 @I2@ INDI
1 NAME Therezinha Carvalho do Nascimento /Souza/
0 TRLR
"""

import tempfile  # noqa: E402

for rotulo, conteudo in (("SEM 'Souza' no registro da Therezinha", GED_SEM_SOUZA),
                         ("COM 'Souza' no registro da Therezinha", GED_COM_SOUZA)):
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_sonda.ged")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    arvore = carregar_arvore(caminho)
    ged_index, surname_index, features = build_ged_indexes(arvore)
    cands, motivo = match_candidates(arvore, ALVO, CM, ged_index, surname_index, features)
    escolhido = get_name(arvore[0][cands[0]]) if cands else "(descartado)"
    print(f"{rotulo}")
    print(f"   chave exata no indice? {norm_name(ALVO) in ged_index}")
    print(f"   nome do CSV          : {ALVO}")
    print(f"   pessoa escolhida     : {escolhido}")
    print()
os.remove(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_sonda.ged"))
