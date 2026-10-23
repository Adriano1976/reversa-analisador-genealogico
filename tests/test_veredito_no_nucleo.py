"""Testes do veredito de validação dentro do fluxo de DNA.

Cobrem as quatro chaves que o cartão consome, o mapeamento status → rótulo/classe e o
custo: uma chamada ao validador por resultado, nunca duas.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from application.validacao import (  # noqa: E402
    intervalo_de_geracao_mediano as intervalo_da_fachada,
)
from core import dna_analysis as nucleo  # noqa: E402
from core import validacao_no_cartao  # noqa: E402
from core.dna_analysis import dna_analysis  # noqa: E402
from core.documentary_relationship import (  # noqa: E402
    intervalo_de_geracao_mediano as intervalo_do_nucleo,
)
from core.validator import ERRO_CRONICO, INCONCLUSIVO, VALIDADO  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from tests.fixtures.arvore_para_cirurgia import (  # noqa: E402
    CSV_SALTO,
    CSV_VALIDO,
    GED_LINHA_VALIDA,
    GED_MATCH_SEM_FAMILIA,
    GED_SALTO_IMPOSSIVEL,
)
from tests.fixtures.helpers import deps  # noqa: E402


def _arquivo(tmp_path: Path, nome: str, conteudo: str) -> str:
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return str(caminho)


def _analisar(tmp_path, ged_texto, csv_texto, nome="Doador Sintetico"):
    ged = _arquivo(tmp_path, "arvore.ged", ged_texto)
    csv = _arquivo(tmp_path, "matches.csv", csv_texto)
    arvore = carregar_arvore(ged)
    resultados, _descartados, _mensagem = dna_analysis(csv, nome, deps(), arvore)
    return arvore, resultados


# ---------------------------------------------------------------------------
# As quatro chaves
# ---------------------------------------------------------------------------

def test_linha_em_conflito_traz_os_quatro_campos(tmp_path):
    _arvore, resultados = _analisar(tmp_path, GED_SALTO_IMPOSSIVEL, CSV_SALTO)

    assert len(resultados) == 1
    cartao = resultados[0]
    assert cartao["validacao_status"] == ERRO_CRONICO
    assert cartao["validacao_rotulo"] == "Linha em conflito"
    assert cartao["validacao_classe"] == "validacao-conflito"
    # O aviso cita o motivo e o primeiro código crítico, na ordem do validador
    # (severidade e depois código). Neste par o confronto já era CONFLITANTE.
    assert "CONFLITO_CM_DOCUMENTAL" in cartao["validacao_aviso"]
    assert cartao["validacao_aviso"].startswith(ERRO_CRONICO + ": ")


def test_linha_valida_traz_os_quatro_campos(tmp_path):
    _arvore, resultados = _analisar(tmp_path, GED_LINHA_VALIDA, CSV_VALIDO)

    cartao = resultados[0]
    assert cartao["validacao_status"] == VALIDADO
    assert cartao["validacao_rotulo"] == "Validado"
    assert cartao["validacao_classe"] == "validacao-valido"
    assert cartao["validacao_aviso"]


def test_inconclusivo_tem_status_e_nao_tem_rotulo(tmp_path):
    # Match sem registro de família: há resultado, não há caminho documental.
    _arvore, resultados = _analisar(tmp_path, GED_MATCH_SEM_FAMILIA, CSV_VALIDO)

    cartao = resultados[0]
    assert cartao["validacao_status"] == INCONCLUSIVO
    assert cartao["validacao_rotulo"] is None
    assert cartao["validacao_classe"] is None
    assert cartao["validacao_aviso"] is None


def test_a_classe_nunca_contem_estado(tmp_path):
    for ged, csv in ((GED_SALTO_IMPOSSIVEL, CSV_SALTO), (GED_LINHA_VALIDA, CSV_VALIDO)):
        _arvore, resultados = _analisar(tmp_path, ged, csv)
        for cartao in resultados:
            classe = cartao["validacao_classe"]
            if classe:
                assert classe.startswith("validacao-")
                assert "estado-" not in classe


# ---------------------------------------------------------------------------
# Custo
# ---------------------------------------------------------------------------

def test_uma_chamada_ao_validador_por_resultado(tmp_path, monkeypatch):
    """O espiao mora no modulo que CHAMA o validador, e nao no que monta o cartao.

    Depois da OPP-20261023-CTAO a chamada saiu de `core.dna_analysis` para
    `core.validacao_no_cartao`. Patchar a origem (`core.validator`) nao serviria:
    o nome ja foi importado, e o espiao precisa estar no ponto de uso.
    """
    chamadas = {"total": 0}
    original = validacao_no_cartao.validar_comparacao

    def espiao(comparacao):
        chamadas["total"] += 1
        return original(comparacao)

    monkeypatch.setattr(validacao_no_cartao, "validar_comparacao", espiao)
    _arvore, resultados = _analisar(tmp_path, GED_SALTO_IMPOSSIVEL, CSV_SALTO)

    assert len(resultados) == 1
    assert chamadas["total"] == 1


# ---------------------------------------------------------------------------
# Fonte única do intervalo de geração
# ---------------------------------------------------------------------------

def test_fachada_e_nucleo_dao_o_mesmo_intervalo(tmp_path):
    arvore, _resultados = _analisar(tmp_path, GED_LINHA_VALIDA, CSV_VALIDO)

    assert intervalo_da_fachada(arvore) == intervalo_do_nucleo(arvore)
    assert intervalo_do_nucleo(arvore) == 25.0
