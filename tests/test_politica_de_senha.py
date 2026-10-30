"""Politica de senha (`RN-02`).

A autoridade unica da regra: cada exigencia e testada isolada, para uma mudanca
acidental em uma delas nao passar escondida atras de uma senha que atende a todas.
"""
from __future__ import annotations

import pytest

from core.conta import (
    FALTA_ESPECIAL,
    FALTA_MAIUSCULA,
    FALTA_MINUSCULA,
    FALTA_NUMERO,
    FALTA_TAMANHO,
    SenhaForaDaPolitica,
    PoliticaDeSenha,
)

VALIDA = "Senha#2026"


@pytest.fixture
def politica() -> PoliticaDeSenha:
    return PoliticaDeSenha()


def test_aceita_senha_que_atende_a_todas_as_exigencias(politica):
    assert politica.avaliar(VALIDA).atendida
    assert politica.avaliar(VALIDA).faltas == ()


def test_recusa_senha_curta(politica):
    resultado = politica.avaliar("Ab#1")
    assert FALTA_TAMANHO in resultado.faltas


def test_recusa_senha_sem_minuscula(politica):
    assert FALTA_MINUSCULA in politica.avaliar("SENHA#2026").faltas


def test_recusa_senha_sem_maiuscula(politica):
    assert FALTA_MAIUSCULA in politica.avaliar("senha#2026").faltas


def test_recusa_senha_sem_numero(politica):
    assert FALTA_NUMERO in politica.avaliar("Senha#abc!").faltas


def test_recusa_senha_sem_especial(politica):
    assert FALTA_ESPECIAL in politica.avaliar("Senha2026x").faltas


def test_espaco_nao_conta_como_caractere_especial(politica):
    assert FALTA_ESPECIAL in politica.avaliar("Senha 2026x").faltas


def test_acento_e_letra_unicode_e_aceito_como_letra(politica):
    # `ç` e `ã` sao minusculas Unicode; a senha tem maiuscula, digito e especial.
    assert politica.avaliar("Senhã#2026").atendida


def test_teto_de_128_caracteres(politica):
    no_limite = "Aa1#" + "x" * 124
    assert len(no_limite) == 128
    assert politica.avaliar(no_limite).atendida
    assert FALTA_TAMANHO in politica.avaliar(no_limite + "x").faltas


def test_faltas_somam_quando_a_senha_falha_em_varias(politica):
    faltas = politica.avaliar("abc").faltas
    assert FALTA_TAMANHO in faltas
    assert FALTA_MAIUSCULA in faltas
    assert FALTA_NUMERO in faltas
    assert FALTA_ESPECIAL in faltas


def test_exigir_levanta_com_a_lista_do_que_falta(politica):
    with pytest.raises(SenhaForaDaPolitica) as erro:
        politica.exigir("abc")
    assert FALTA_TAMANHO in erro.value.faltas


def test_exigir_nao_levanta_para_senha_valida(politica):
    politica.exigir(VALIDA)


def test_a_mensagem_da_excecao_nao_repete_a_senha(politica):
    with pytest.raises(SenhaForaDaPolitica) as erro:
        politica.exigir("segredo-curto")
    assert "segredo-curto" not in str(erro.value)
