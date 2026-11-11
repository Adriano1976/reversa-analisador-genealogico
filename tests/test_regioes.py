"""Testes do agrupamento por região compartilhada (feature 056)."""
from __future__ import annotations

from core.regioes import PISO_DE_CM, SegmentoDaRegiao, agrupar


def _segmento(kit, inicio, fim, cm, cromossomo="7", nome=None, snps=None) -> SegmentoDaRegiao:
    return SegmentoDaRegiao(
        kit=kit,
        nome=nome or f"Pessoa {kit}",
        cromossomo=cromossomo,
        inicio=inicio,
        fim=fim,
        cm=cm,
        snps=snps,
    )


def test_tres_matches_sobrepostos_viram_regiao():
    agrupamento = agrupar([
        _segmento("A111111", 21000000, 39000000, 45.0),
        _segmento("B222222", 21500000, 38500000, 40.0),
        _segmento("C333333", 22000000, 38000000, 35.0),
    ])

    assert agrupamento.total == 1
    regiao = agrupamento.regioes[0]
    assert len(regiao.kits) == 3
    assert regiao.cromossomo == "7"
    assert regiao.inicio == 22000000
    assert regiao.fim == 38000000
    assert regiao.cm_minimo == 35.0
    assert regiao.cm_maximo == 45.0


def test_segmento_abaixo_do_piso_nao_entra():
    agrupamento = agrupar([
        _segmento("A111111", 21000000, 39000000, 45.0),
        _segmento("B222222", 21500000, 38500000, 40.0),
        _segmento("C333333", 22000000, 38000000, PISO_DE_CM - 1),
    ])

    assert agrupamento.total == 0


def test_dois_segmentos_do_mesmo_match_contam_uma_vez():
    agrupamento = agrupar([
        _segmento("A111111", 21000000, 39000000, 45.0),
        _segmento("A111111", 60000000, 70000000, 25.0),
        _segmento("B222222", 21500000, 38500000, 40.0),
        _segmento("C333333", 22000000, 38000000, 35.0),
    ])

    assert agrupamento.total == 1
    regiao = agrupamento.regioes[0]
    assert len(regiao.kits) == 3
    # A região usa o segmento que está na janela, não o distante.
    assert regiao.inicio == 22000000
    assert regiao.fim == 38000000


def test_regiao_fechada_em_faixa_curta_recebe_alerta_de_acumulo():
    segmentos = [
        _segmento(f"K{i:06d}", 58000000, 58400000, 10.5, cromossomo="20")
        for i in range(1, 10)
    ]

    agrupamento = agrupar(segmentos)

    assert agrupamento.total == 1
    assert agrupamento.regioes[0].acumulo is True


def test_snps_da_regiao_sao_o_minimo_e_o_maximo_dos_segmentos():
    agrupamento = agrupar([
        _segmento("A111111", 21000000, 39000000, 45.0, snps=9000),
        _segmento("B222222", 21500000, 38500000, 40.0, snps=7000),
        _segmento("C333333", 22000000, 38000000, 35.0, snps=8000),
    ])

    regiao = agrupamento.regioes[0]
    assert regiao.snps_minimo == 7000
    assert regiao.snps_maximo == 9000


def test_ordem_e_deterministica():
    segmentos = [
        _segmento("A111111", 21000000, 39000000, 45.0),
        _segmento("B222222", 21500000, 38500000, 40.0),
        _segmento("C333333", 22000000, 38000000, 35.0),
        _segmento("D444444", 22000000, 38000000, 30.0, cromossomo="20"),
        _segmento("E555555", 22500000, 37500000, 30.0, cromossomo="20"),
        _segmento("F666666", 23000000, 37000000, 30.0, cromossomo="20"),
    ]

    primeira = agrupar(segmentos)
    segunda = agrupar(list(reversed(segmentos)))

    assert [(r.cromossomo, r.inicio, r.kits) for r in primeira.regioes] == \
           [(r.cromossomo, r.inicio, r.kits) for r in segunda.regioes]


def test_limite_trunca_e_declara():
    segmentos = [
        _segmento("A111111", 21000000, 39000000, 45.0),
        _segmento("B222222", 21500000, 38500000, 40.0),
        _segmento("C333333", 22000000, 38000000, 35.0),
        _segmento("D444444", 22000000, 38000000, 30.0, cromossomo="20"),
        _segmento("E555555", 22500000, 37500000, 30.0, cromossomo="20"),
        _segmento("F666666", 23000000, 37000000, 30.0, cromossomo="20"),
    ]

    agrupamento = agrupar(segmentos, limite=1)

    assert agrupamento.total == 2
    assert len(agrupamento.regioes) == 1
    assert agrupamento.truncado is True
