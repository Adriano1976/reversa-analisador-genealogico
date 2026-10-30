"""Falha de armazenamento nao vira 500 (`RNF-09`).

Cenario real, medido em 2026-10-30: a pasta `src/dados/` sem permissao de escrita
fazia o `POST /recuperar-senha` responder `500`. Condicao operacional que o
operador resolve nao e erro de programacao: a tela pede para tentar de novo e o
log guarda a causa com traceback.
"""
from __future__ import annotations

from tests.fixtures.autenticacao import CONTA_A
from tests.fixtures.identidade import cadastrar_e_confirmar, entrar_com_senha
from web.textos_de_conta import ARMAZENAMENTO_INDISPONIVEL

SENHA = "Senha#2026"


def _quebrar(app_com_contas):
    app_com_contas.contas.falhar = True
    return app_com_contas


def test_cadastro_nao_retorna_500(app_com_contas):
    _quebrar(app_com_contas)

    resposta = app_com_contas.cliente.post(
        "/cadastro",
        data={"email": "teste@example.test", "senha": SENHA, "repeticao": SENHA},
    )

    assert resposta.status_code == 200
    assert ARMAZENAMENTO_INDISPONIVEL in resposta.get_data(as_text=True)


def test_entrada_nao_retorna_500(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    _quebrar(app_com_contas)

    resposta = entrar_com_senha(app_com_contas, "teste@example.test", SENHA)

    assert resposta.status_code == 200
    assert ARMAZENAMENTO_INDISPONIVEL in resposta.get_data(as_text=True)


def test_confirmacao_nao_retorna_500(app_com_contas):
    _quebrar(app_com_contas)

    resposta = app_com_contas.cliente.get("/confirmar?token=qualquer")

    assert resposta.status_code == 200
    assert ARMAZENAMENTO_INDISPONIVEL in resposta.get_data(as_text=True)


def test_recuperacao_nao_retorna_500(app_com_contas):
    _quebrar(app_com_contas)

    resposta = app_com_contas.cliente.post(
        "/recuperar-senha", data={"email": "teste@example.test"}
    )

    assert resposta.status_code == 200
    assert ARMAZENAMENTO_INDISPONIVEL in resposta.get_data(as_text=True)


def test_tela_de_redefinicao_nao_retorna_500(app_com_contas):
    _quebrar(app_com_contas)

    resposta = app_com_contas.cliente.get("/redefinir-senha?token=qualquer")

    assert resposta.status_code == 200
    assert ARMAZENAMENTO_INDISPONIVEL in resposta.get_data(as_text=True)


def test_definir_senha_nao_retorna_500(app_com_contas):
    app_com_contas.entrar(CONTA_A)
    _quebrar(app_com_contas)

    resposta = app_com_contas.cliente.get("/definir-senha")

    assert resposta.status_code == 200
    assert ARMAZENAMENTO_INDISPONIVEL in resposta.get_data(as_text=True)


def test_a_causa_entra_no_log(app_com_contas, caplog):
    import logging

    _quebrar(app_com_contas)

    with caplog.at_level(logging.ERROR):
        app_com_contas.cliente.post(
            "/recuperar-senha", data={"email": "teste@example.test"}
        )

    assert "falha de armazenamento na identidade local" in caplog.text
