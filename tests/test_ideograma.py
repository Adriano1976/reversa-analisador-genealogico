"""Testes do ideograma por cromossomo (feature 056)."""
from __future__ import annotations

from reporting.ideograma import LARGURA_MINIMA, montar_ideograma


def _item(cromossomo, inicio, fim, desfecho="Parcial", kits=3, acumulo=False):
    return {
        "cromossomo": cromossomo,
        "inicio": inicio,
        "fim": fim,
        "extensao_mb": round((fim - inicio) / 1_000_000, 2),
        "kits": kits,
        "cm_minimo": 10.0,
        "cm_maximo": 20.0,
        "desfecho": desfecho,
        "desfecho_chave": desfecho.lower(),
        "acumulo": acumulo,
        "membros_lista": [{"nome": "Maria", "kit": "A1"}, {"nome": "João", "kit": "B2"}],
    }


def test_agrupa_por_cromossomo_em_ordem_natural():
    linhas = montar_ideograma([
        _item("10", 1_000_000, 2_000_000),
        _item("2", 1_000_000, 2_000_000),
        _item("1", 1_000_000, 2_000_000),
    ])

    assert [linha["cromossomo"] for linha in linhas] == ["1", "2", "10"]


def test_posicao_e_largura_em_porcentagem_do_cromossomo():
    linhas = montar_ideograma([_item("1", 0, 100_000_000)])

    faixa = linhas[0]["faixas"][0]
    assert faixa["esquerda"] == 0.0
    # 100 Mb de 249,25 Mb = 40,12%
    assert 40.0 <= faixa["largura"] <= 40.3


def test_faixa_minuscula_nao_desaparece():
    linhas = montar_ideograma([_item("1", 1_000_000, 1_500_000)])

    assert linhas[0]["faixas"][0]["largura"] == LARGURA_MINIMA


def test_posicao_alem_do_comprimento_e_presa_na_borda():
    linhas = montar_ideograma([_item("21", 48_000_000, 60_000_000)])

    faixa = linhas[0]["faixas"][0]
    assert faixa["esquerda"] <= 100.0
    assert faixa["esquerda"] + faixa["largura"] <= 100.0


def test_cromossomo_desconhecido_usa_a_regua_do_arquivo():
    linhas = montar_ideograma([_item("99", 0, 10_000_000)])

    assert linhas[0]["regua_oficial"] is False
    assert linhas[0]["faixas"][0]["largura"] == 100.0


def test_faixa_perto_da_borda_abre_o_cartao_para_a_esquerda():
    linhas = montar_ideograma([_item("1", 240_000_000, 245_000_000)])

    assert linhas[0]["faixas"][0]["lado"] == "esquerda"


def test_faixa_perto_do_inicio_abre_o_cartao_para_a_direita():
    """Colada na borda esquerda, a dica centrada sairia para fora do cartão."""
    linhas = montar_ideograma([_item("1", 2_000_000, 5_000_000)])

    assert linhas[0]["faixas"][0]["lado"] == "direita"


def test_faixa_no_meio_abre_o_cartao_centrado():
    linhas = montar_ideograma([_item("1", 120_000_000, 125_000_000)])

    assert linhas[0]["faixas"][0]["lado"] == "centro"


def test_ordem_das_faixas_e_por_posicao():
    linhas = montar_ideograma([
        _item("7", 80_000_000, 90_000_000),
        _item("7", 10_000_000, 20_000_000),
    ])

    inicios = [faixa["inicio"] for faixa in linhas[0]["faixas"]]
    assert inicios == sorted(inicios)
