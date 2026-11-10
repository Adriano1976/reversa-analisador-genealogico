"""Testes da classificação da região contra os cartões (feature 056)."""
from __future__ import annotations

from core.regiao_no_cartao import (
    DESFECHO_CONVERGENTE,
    DESFECHO_DIVIDIDO,
    DESFECHO_PARCIAL,
    DESFECHO_SEM_ANCESTRAL,
    classificar,
)
from core.regioes import RegiaoCompartilhada, SegmentoDaRegiao


def _regiao(membros=(("A1", "Maria Silva"), ("B2", "João Souza"), ("C3", "Ana Lima"))):
    segmentos = tuple(
        SegmentoDaRegiao(kit=kit, nome=nome, cromossomo="7",
                         inicio=22000000, fim=38000000, cm=40.0)
        for kit, nome in membros
    )
    return RegiaoCompartilhada(
        cromossomo="7",
        inicio=22000000,
        fim=38000000,
        kits=tuple(sorted(kit for kit, _ in membros)),
        membros=tuple(membros),
        segmentos=segmentos,
        cm_minimo=35.0,
        cm_maximo=45.0,
    )


def _cartao(kit, nome, ancestral_id="I1", ancestral_nome="José Alves", cm=40.0):
    return {
        "kit": kit,
        "match_name": nome,
        "csv_name": nome,
        "cm": cm,
        "documentary": {
            "status": "found",
            "common_ancestor": {"id": ancestral_id, "name": ancestral_nome},
        },
    }


def test_convergente_quando_todos_apontam_o_mesmo_ancestral():
    cartoes = [
        _cartao("A1", "Maria Silva"),
        _cartao("B2", "João Souza"),
        _cartao("C3", "Ana Lima"),
    ]

    resultado = classificar(_regiao(), cartoes)

    assert resultado.desfecho == DESFECHO_CONVERGENTE
    assert "José Alves" in resultado.motivo
    assert "não prova o parentesco" in resultado.motivo


def test_dividido_quando_os_ancestrais_sao_distintos():
    cartoes = [
        _cartao("A1", "Maria Silva", "I1", "José Alves"),
        _cartao("B2", "João Souza", "I2", "Rita Maria"),
        _cartao("C3", "Ana Lima", "I2", "Rita Maria"),
    ]

    resultado = classificar(_regiao(), cartoes)

    assert resultado.desfecho == DESFECHO_DIVIDIDO
    assert "José Alves" in resultado.motivo and "Rita Maria" in resultado.motivo


def test_parcial_quando_parte_tem_caminho():
    cartoes = [
        _cartao("A1", "Maria Silva"),
        _cartao("B2", "João Souza"),
    ]

    resultado = classificar(_regiao(), cartoes)

    assert resultado.desfecho == DESFECHO_PARCIAL
    assert "2 de 3" in resultado.motivo


def test_sem_ancestral_quando_nenhum_cartao_tem_caminho():
    resultado = classificar(_regiao(), ())

    assert resultado.desfecho == DESFECHO_SEM_ANCESTRAL
    assert "ancestral que a árvore não tem" in resultado.motivo


def test_sem_cartoes_nenhum_desfecho_calculado():
    resultado = classificar(_regiao(), None)

    assert resultado.desfecho is None
    assert "depende da árvore" in resultado.motivo


def test_juncao_cai_para_o_nome_quando_o_kit_nao_esta_no_cartao():
    cartoes = [_cartao("ZZ9", "Maria Silva")]

    resultado = classificar(_regiao(), cartoes)

    membro = next(m for m in resultado.membros if m.kit == "A1")
    assert membro.tem_cartao is True
    assert membro.ancestral_id == "I1"
