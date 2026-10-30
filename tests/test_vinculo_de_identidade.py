"""Vinculo de identidade por e-mail verificado (`RN-20`, `RF-22`).

O cenario que este arquivo existe para impedir e o pre-sequestro: alguem cadastra
o e-mail de outra pessoa com a propria senha, e a vitima confirma o endereco sem
saber que esta confirmando a credencial do atacante.
"""
from __future__ import annotations

from tests.fixtures.autenticacao import CONTA_A
from tests.fixtures.identidade import cadastrar_e_confirmar, entrar_com_senha

SENHA = "Senha#2026"


def test_entrada_google_cria_o_registro_da_conta_confirmado(app_com_contas):
    app_com_contas.entrar(CONTA_A)

    conta = app_com_contas.contas.por_sub(CONTA_A.sub)

    assert conta is not None
    assert conta.confirmada
    assert conta.google_sub == CONTA_A.sub
    assert not conta.tem_senha


def test_google_anexa_a_conta_local_e_mantem_o_dono(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email=CONTA_A.email, senha=SENHA)
    local = app_com_contas.contas.por_email(CONTA_A.email)

    app_com_contas.entrar(CONTA_A)

    conta = app_com_contas.contas.por_email(CONTA_A.email)
    assert conta.sub == local.sub, "a conta local continua sendo a dona"
    assert conta.google_sub == CONTA_A.sub
    assert app_com_contas.contas.por_sub(CONTA_A.sub) is None, "nao pode nascer uma segunda conta"

    # A entrada por senha continua funcionando e cai no mesmo dono.
    app_com_contas.cliente.post("/logout")
    entrar_com_senha(app_com_contas, CONTA_A.email, SENHA)
    assert app_com_contas.contas.quantidade() == 1


def test_cadastro_deslogado_com_email_existente_nao_altera_a_conta(app_com_contas):
    app_com_contas.entrar(CONTA_A)
    app_com_contas.cliente.post("/logout")
    antes = app_com_contas.contas.por_email(CONTA_A.email)

    resposta = app_com_contas.cliente.post(
        "/cadastro",
        data={"email": CONTA_A.email, "senha": "Ataque#2026", "repeticao": "Ataque#2026"},
    )

    depois = app_com_contas.contas.por_email(CONTA_A.email)
    assert "Se este e-mail puder ser usado" in resposta.get_data(as_text=True)
    assert depois == antes, "o cadastro deslogado nao pode tocar a conta existente"
    assert not depois.tem_senha
    assert "Alguém tentou" in app_com_contas.email.ultimo_corpo()


def test_falha_do_repositorio_nao_derruba_a_entrada_google(app_com_contas):
    app_com_contas.contas.falhar = True

    resposta = app_com_contas.entrar(CONTA_A)

    assert resposta.status_code == 302
    assert app_com_contas.cliente.get("/").status_code == 200
