"""Auditoria da identidade local (`RN-14`).

A linha identifica a conta pelo `sub` e nunca carrega e-mail, senha ou token. O
conjunto de acoes e fechado: acao escrita a mao em cada chamada faria a mesma
coisa aparecer com dois nomes.
"""
from __future__ import annotations

import logging

from utils.auditoria import ACOES, registrar
from utils.logs import LOGGER_DE_AUDITORIA

ACOES_DA_IDENTIDADE = {
    "cadastrar",
    "confirmar",
    "definir_senha",
    "pedir_senha",
    "redefinir_senha",
}


def test_as_cinco_acoes_entraram_no_conjunto_fechado():
    assert ACOES_DA_IDENTIDADE <= ACOES


def test_a_linha_de_cadastro_sai_com_a_acao_e_sem_email(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_DE_AUDITORIA)

    registrar("cadastrar", "sucesso", ip="127.0.0.1", origem="POST /cadastro")

    texto = caplog.text
    assert "acao=cadastrar" in texto
    assert "desfecho=sucesso" in texto
    assert "@" not in texto, "a linha nao pode carregar e-mail"


def test_a_linha_de_definir_senha_identifica_pelo_sub(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_DE_AUDITORIA)

    registrar("definir_senha", "sucesso", conta="local-abc", ip="127.0.0.1")

    assert "conta=local-abc" in caplog.text


def test_a_linha_de_redefinicao_nao_carrega_token(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_DE_AUDITORIA)

    registrar("redefinir_senha", "sucesso", conta="local-abc", ip="127.0.0.1")

    assert "token" not in caplog.text.lower()
