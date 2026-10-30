"""Token de uso unico (`RN-08`, `RN-19`)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.token_de_uso_unico import (
    TIPO_CONFIRMACAO,
    TIPO_REDEFINICAO,
    TipoDeTokenInvalido,
    conferir,
    derivar,
    emitir,
    valido,
)

AGORA = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)


def test_emite_texto_aleatorio_com_entropia_de_32_bytes():
    token = emitir(TIPO_CONFIRMACAO, AGORA)
    assert token.texto
    assert len(token.texto) >= 40
    assert token.hash == derivar(token.texto)


def test_dois_tokens_nunca_sao_iguais():
    um = emitir(TIPO_CONFIRMACAO, AGORA)
    outro = emitir(TIPO_CONFIRMACAO, AGORA)
    assert um.texto != outro.texto
    assert um.hash != outro.hash


def test_validade_da_confirmacao_e_de_24_horas():
    token = emitir(TIPO_CONFIRMACAO, AGORA)
    assert token.expira_em == AGORA + timedelta(hours=24)


def test_validade_da_redefinicao_e_de_60_minutos():
    token = emitir(TIPO_REDEFINICAO, AGORA)
    assert token.expira_em == AGORA + timedelta(minutes=60)


def test_valido_ate_o_instante_do_vencimento_e_nao_depois():
    token = emitir(TIPO_REDEFINICAO, AGORA)
    assert valido(token, AGORA + timedelta(minutes=59, seconds=59))
    assert not valido(token, token.expira_em)
    assert not valido(token, token.expira_em + timedelta(seconds=1))


def test_conferir_aceita_o_texto_e_recusa_o_resto():
    token = emitir(TIPO_CONFIRMACAO, AGORA)
    assert conferir(token.texto or "", token.hash)
    assert not conferir("outro-texto", token.hash)
    assert not conferir(token.texto or "", None)


def test_registro_persistido_nao_tem_o_texto():
    token = emitir(TIPO_CONFIRMACAO, AGORA)
    registro = token.para_registro()
    assert "texto" not in registro
    assert registro["tipo"] == TIPO_CONFIRMACAO
    assert registro["expira_em"] == token.expira_em.isoformat()


def test_tipo_desconhecido_e_recusado():
    with pytest.raises(TipoDeTokenInvalido):
        emitir("redefinicao_de_outra_coisa", AGORA)


def test_texto_pedido_serve_para_o_teste_ser_deterministico():
    token = emitir(TIPO_REDEFINICAO, AGORA, texto="fixo")
    assert token.texto == "fixo"
    assert token.hash == derivar("fixo")
