"""Testes da tabela de segmentos (feature 058).

A regiao e' construida a mao: o que esta em teste e' o achatamento em linhas e a ordem da
tabela, nao o agrupamento (que tem testes proprios em `tests/test_regioes.py`).
"""
from __future__ import annotations

from application.segmentos import cromossomos_das_linhas, projetar_segmentos
from core.regioes import RegiaoCompartilhada, SegmentoDaRegiao
from core.segmentos import SegmentoDeRegiao, segmentos_das_regioes


class _Classificada:
    """A forma que o nucleo entrega: a regiao mais o desfecho documental dela."""

    def __init__(self, regiao, desfecho=None, rotulo=""):
        self.regiao = regiao
        self.desfecho = desfecho
        self.rotulo = rotulo


def _regiao(cromossomo, participantes, inicio=10_000_000):
    """`participantes` e' uma lista de (kit, nome, cm)."""
    segmentos = tuple(
        SegmentoDaRegiao(
            kit=kit,
            nome=nome,
            cromossomo=cromossomo,
            inicio=inicio + indice * 1_000,
            fim=inicio + 2_000_000 + indice * 1_000,
            cm=cm,
        )
        for indice, (kit, nome, cm) in enumerate(participantes)
    )
    cms = [cm for _, _, cm in participantes]
    return RegiaoCompartilhada(
        cromossomo=cromossomo,
        inicio=inicio,
        fim=inicio + 2_000_000,
        kits=tuple(kit for kit, _, _ in participantes),
        membros=tuple((kit, nome) for kit, nome, _ in participantes),
        segmentos=segmentos,
        cm_minimo=min(cms),
        cm_maximo=max(cms),
    )


def _linha(**campos):
    base = {
        "regiao_indice": 1,
        "cromossomo": "7",
        "inicio": 23_000_000,
        "fim": 37_000_000,
        "cm": 45.0,
        "kit": "A111111",
        "nome": "Ana Silva Souza",
        "desfecho": "Convergente",
        "desfecho_chave": "convergente",
    }
    base.update(campos)
    return SegmentoDeRegiao(**base)


def test_uma_linha_por_par_regiao_kit():
    regioes = [_Classificada(_regiao("7", [
        ("A", "Ana", 45.0), ("B", "Bento", 40.0), ("C", "Clara", 35.0),
    ]))]

    linhas = segmentos_das_regioes(regioes)

    assert [linha.kit for linha in linhas] == ["A", "B", "C"]
    assert all(linha.cromossomo == "7" for linha in linhas)


def test_ordem_por_cromossomo_natural_e_depois_inicio():
    regioes = [
        _Classificada(_regiao("10", [("A", "Ana", 10.0)], inicio=10_000_000)),
        _Classificada(_regiao("2", [("B", "Bento", 10.0)], inicio=50_000_000)),
        _Classificada(_regiao("2", [("C", "Clara", 10.0)], inicio=5_000_000)),
    ]

    linhas = segmentos_das_regioes(regioes)

    assert [(linha.cromossomo, linha.inicio) for linha in linhas] == [
        ("2", 5_000_000),
        ("2", 50_000_000),
        ("10", 10_000_000),
    ]


def test_indice_da_regiao_sobrevive_a_ordenacao():
    """D-02: o vinculo com a faixa e' o indice da regiao, nao a posicao da linha."""
    regioes = [
        _Classificada(_regiao("10", [("A", "Ana", 10.0)])),
        _Classificada(_regiao("2", [("B", "Bento", 10.0)])),
    ]

    linhas = segmentos_das_regioes(regioes)

    # A regiao do cromossomo 2 e' a SEGUNDA da lista, mas a primeira da tabela.
    assert linhas[0].cromossomo == "2"
    assert linhas[0].regiao_indice == 2
    assert linhas[1].regiao_indice == 1


def test_desfecho_da_regiao_vai_para_a_linha():
    regioes = [_Classificada(
        _regiao("7", [("A", "Ana", 45.0)]),
        desfecho="convergente",
        rotulo="Convergente",
    )]

    linha = segmentos_das_regioes(regioes)[0]

    assert linha.desfecho == "Convergente"
    assert linha.desfecho_chave == "convergente"


def test_regiao_sem_desfecho_nao_inventa_rotulo():
    linha = segmentos_das_regioes([_Classificada(_regiao("7", [("A", "Ana", 45.0)]))])[0]

    assert linha.desfecho == ""
    assert linha.desfecho_chave == ""


def test_lista_vazia_devolve_tupla_vazia():
    assert segmentos_das_regioes([]) == ()
    assert segmentos_das_regioes(None) == ()


def test_projecao_deriva_extensao_e_preserva_o_cm():
    linhas = projetar_segmentos([_linha(inicio=23_000_000, fim=31_210_000, cm=14.2)])

    assert linhas[0]["extensao_mb"] == 8.21
    assert linhas[0]["cm"] == 14.2
    assert linhas[0]["regiao"] == 1


def test_projecao_monta_a_chave_de_busca_sem_acento():
    linhas = projetar_segmentos([_linha(nome="José Ávila", kit="KZ6071981", cromossomo="7")])

    assert linhas[0]["chave_de_busca"] == "7 kz6071981 jose avila"


def test_projecao_nao_muta_o_segmento():
    segmento = _linha()
    [linha] = projetar_segmentos([segmento])

    linha["cm"] = 0.0

    assert segmento.cm == 45.0


def test_cromossomos_das_linhas_respeita_a_ordem_da_tabela():
    linhas = projetar_segmentos([
        _linha(cromossomo="1"), _linha(cromossomo="7"), _linha(cromossomo="1"),
    ])

    assert cromossomos_das_linhas(linhas) == ["1", "7"]
