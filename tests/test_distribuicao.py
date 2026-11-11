"""Testes da distribuicao por cromossomo (feature 057).

A regiao e construida a mao: o que esta em teste aqui e a AGREGACAO, nao o
agrupamento (que tem testes proprios em `tests/test_regioes.py`).
"""
from __future__ import annotations

from core.distribuicao import distribuicao_por_cromossomo
from core.regioes import RegiaoCompartilhada, SegmentoDaRegiao
from reporting.ideograma import montar_ideograma


def _regiao(cromossomo, kits, cms):
    segmentos = tuple(
        SegmentoDaRegiao(
            kit=kit,
            nome=f"Nome {kit}",
            cromossomo=cromossomo,
            inicio=10_000_000 + indice * 1_000,
            fim=11_000_000 + indice * 1_000,
            cm=cm,
        )
        for indice, (kit, cm) in enumerate(zip(kits, cms))
    )
    return RegiaoCompartilhada(
        cromossomo=cromossomo,
        inicio=10_000_000,
        fim=11_000_000,
        kits=tuple(kits),
        membros=tuple((kit, f"Nome {kit}") for kit in kits),
        segmentos=segmentos,
        cm_minimo=min(cms),
        cm_maximo=max(cms),
    )


def test_uma_linha_por_cromossomo_em_ordem_natural():
    resumos = distribuicao_por_cromossomo([
        _regiao("10", ("A", "B", "C"), (10.0, 10.0, 10.0)),
        _regiao("2", ("D", "E", "F"), (10.0, 10.0, 10.0)),
    ])

    assert [resumo.cromossomo for resumo in resumos] == ["2", "10"]


def test_matches_conta_o_kit_uma_vez_mesmo_em_duas_regioes():
    """RN-02: o mesmo kit em duas regioes do cromossomo e UM match."""
    resumos = distribuicao_por_cromossomo([
        _regiao("7", ("A", "B", "C"), (20.0, 10.0, 10.0)),
        _regiao("7", ("A", "D", "E"), (30.0, 10.0, 10.0)),
    ])

    assert len(resumos) == 1
    assert resumos[0].kits == ("A", "B", "C", "D", "E")


def test_cm_medio_usa_o_segmento_mais_forte_de_cada_kit():
    """RN-03 + D-12: um segmento por kit, o de maior cM; media simples, sem soma."""
    resumos = distribuicao_por_cromossomo([
        _regiao("7", ("A", "B", "C"), (20.0, 10.0, 10.0)),
        _regiao("7", ("A", "D", "E"), (30.0, 10.0, 10.0)),
    ])

    # A entra com 30 (o maior dos dois segmentos dele), nao com 20 e 30.
    assert resumos[0].cm_medio == 14.0


def test_cromossomo_sem_regiao_nao_entra():
    assert distribuicao_por_cromossomo([]) == ()
    assert distribuicao_por_cromossomo(None) == ()


def test_ordem_bate_com_a_do_ideograma():
    """D-09: as duas implementacoes da ordem natural nao podem divergir."""
    cromossomos = ("X", "10", "2", "1", "MT")
    resumos = distribuicao_por_cromossomo([
        _regiao(cromossomo, ("A", "B", "C"), (10.0, 10.0, 10.0))
        for cromossomo in cromossomos
    ])
    linhas = montar_ideograma([
        {"cromossomo": cromossomo, "inicio": 10_000_000, "fim": 11_000_000}
        for cromossomo in cromossomos
    ])

    assert [resumo.cromossomo for resumo in resumos] == [
        linha["cromossomo"] for linha in linhas
    ]
