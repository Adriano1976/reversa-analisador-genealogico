"""Testes de integração da fachada `application.correcao`.

Escreve GEDCOM e CSV sintéticos no `tmp_path` da suíte e exercita o caminho completo:
parse da árvore, validação da `028`, cirurgia do grafo e sugestão por comparação.
Nenhum dado real.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from application.correcao import sugerir_correcao  # noqa: E402
from core.cirurgia_do_grafo import (  # noqa: E402
    NATUREZA,
    SEM_CAMINHO_DOCUMENTAL,
    SUGESTAO_INDISPONIVEL,
)
from core.validator import ERRO_CRONICO  # noqa: E402
from tests.fixtures.arvore_para_cirurgia import (  # noqa: E402
    CSV_DOIS_KITS,
    CSV_SALTO,
    CSV_SEM_MATCH,
    CSV_VALIDO,
    GED_LINHA_VALIDA,
    GED_SALTO_IMPOSSIVEL,
)


def _arquivo(tmp_path: Path, nome: str, conteudo: str) -> str:
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return str(caminho)


def _codigos(sugestao):
    return [item["codigo"] for item in sugestao["avisos"]]


def test_salto_impossivel_gera_sugestao(tmp_path):
    ged = _arquivo(tmp_path, "salto.ged", GED_SALTO_IMPOSSIVEL)
    csv = _arquivo(tmp_path, "salto.csv", CSV_SALTO)

    resultado = sugerir_correcao(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert resultado["resumo"]["comparacoes"] == 1
    sugestao = resultado["sugestoes"][0]
    assert sugestao["natureza"] == NATUREZA
    assert sugestao["status_origem"] == ERRO_CRONICO
    assert sugestao["grafo"] is not None
    assert sugestao["ramo_base"]["intacto"] is True
    assert sugestao["doador"]["id"] == "@I1@"
    assert resultado["resumo"]["com_sugestao"] == 1
    assert resultado["resumo"]["geracoes_virtuais"] == len(sugestao["geracoes_virtuais"])


def test_linha_valida_nao_gera_sugestao(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_LINHA_VALIDA)
    csv = _arquivo(tmp_path, "valido.csv", CSV_VALIDO)

    resultado = sugerir_correcao(ged, csv, "Doador Sintetico", ano_referencia=2026)

    sugestao = resultado["sugestoes"][0]
    assert sugestao["grafo"] is None
    assert _codigos(sugestao) == [SUGESTAO_INDISPONIVEL]
    assert resultado["resumo"]["com_sugestao"] == 0


def test_multiplos_kits_so_o_quebrado_recebe_sugestao(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_LINHA_VALIDA)
    csv = _arquivo(tmp_path, "dois_kits.csv", CSV_DOIS_KITS)

    resultado = sugerir_correcao(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert resultado["resumo"]["comparacoes"] == 2
    com_sugestao = [item for item in resultado["sugestoes"] if item["grafo"] is not None]
    assert len(com_sugestao) == 1
    assert resultado["resumo"]["com_sugestao"] == 1


def test_kit_sem_match_nao_gera_sugestao(tmp_path):
    ged = _arquivo(tmp_path, "salto.ged", GED_SALTO_IMPOSSIVEL)
    csv = _arquivo(tmp_path, "sem_match.csv", CSV_SEM_MATCH)

    resultado = sugerir_correcao(ged, csv, "Doador Sintetico", ano_referencia=2026)

    sugestao = resultado["sugestoes"][0]
    assert sugestao["grafo"] is None
    assert SUGESTAO_INDISPONIVEL in _codigos(sugestao)


def test_sem_caminho_documental_quando_o_match_nao_tem_familia(tmp_path):
    from tests.fixtures.arvore_para_cirurgia import CSV_VALIDO as _CSV, GED_MATCH_SEM_FAMILIA

    ged = _arquivo(tmp_path, "sem_familia.ged", GED_MATCH_SEM_FAMILIA)
    csv = _arquivo(tmp_path, "um_kit.csv", _CSV)

    resultado = sugerir_correcao(ged, csv, "Doador Sintetico", ano_referencia=2026)

    sugestao = resultado["sugestoes"][0]
    assert sugestao["grafo"] is None
    codigos = _codigos(sugestao)
    assert SUGESTAO_INDISPONIVEL in codigos or SEM_CAMINHO_DOCUMENTAL in codigos
