"""Testes da geometria do grafico de distribuicao (feature 057).

Nada aqui olha a tela: o que esta em teste e a conta de desenho (topo do eixo,
marcas, altura em porcentagem) e o lado em que o cartao do hover abre.
"""
from __future__ import annotations

from reporting.distribuicao import INTERVALOS_POR_EIXO, montar_distribuicao


def _item(cromossomo="7", kits=4, cm=37.5):
    return {"cromossomo": cromossomo, "kits": kits, "cm_medio": cm}


def test_eixo_parte_do_zero():
    """RN-08: base deslocada exagera diferenca; as duas series partem de zero."""
    grafico = montar_distribuicao([_item()])

    for eixo in (grafico["eixo_matches"], grafico["eixo_cm"]):
        assert eixo["marcas"][0] == {"valor": 0, "posicao": 0.0}


def test_topo_redondo_cobre_o_maior_valor():
    grafico = montar_distribuicao([_item(kits=7, cm=37.5)])

    # 7 / 4 = 1,75 -> passo 2 -> topo 8;  37,5 / 4 = 9,375 -> passo 10 -> topo 40
    assert grafico["eixo_matches"] == {
        "topo": 8, "passo": 2,
        "marcas": [
            {"valor": 0, "posicao": 0.0},
            {"valor": 2, "posicao": 25.0},
            {"valor": 4, "posicao": 50.0},
            {"valor": 6, "posicao": 75.0},
            {"valor": 8, "posicao": 100.0},
        ],
    }
    assert grafico["eixo_cm"]["topo"] == 40.0
    assert grafico["eixo_cm"]["passo"] == 10.0


def test_altura_e_proporcional_ao_topo():
    grafico = montar_distribuicao([_item("7", 7, 37.5), _item("1", 4, 10.0)])
    primeira, segunda = grafico["colunas"]

    assert primeira["altura_cm"] == 93.75
    assert segunda["altura_matches"] == 50.0
    assert segunda["altura_cm"] == 25.0


def test_marcas_vao_de_zero_ao_topo():
    eixo = montar_distribuicao([_item(kits=7)])["eixo_matches"]

    assert len(eixo["marcas"]) == INTERVALOS_POR_EIXO + 1
    assert eixo["marcas"][-1]["valor"] == eixo["topo"]
    assert eixo["marcas"][-1]["posicao"] == 100.0


def test_lado_do_cartao_nas_bordas():
    grafico = montar_distribuicao([
        _item("1", 1, 10.0),
        _item("2", 1, 10.0),
        _item("3", 1, 10.0),
    ])

    assert [coluna["lado"] for coluna in grafico["colunas"]] == [
        "direita", "centro", "esquerda",
    ]


def test_sem_itens_devolve_estrutura_vazia():
    grafico = montar_distribuicao([])

    assert grafico["colunas"] == []
    assert grafico["eixo_matches"] == {}
    assert grafico["eixo_cm"] == {}
