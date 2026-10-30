"""Definir a primeira senha estando autenticado (`RF-24`, `RN-20`)."""
from __future__ import annotations

from tests.fixtures.autenticacao import CONTA_A
from tests.fixtures.identidade import entrar_com_senha

SENHA = "Senha#2026"


def test_conta_google_define_a_primeira_senha(app_com_contas):
    app_com_contas.entrar(CONTA_A)
    corpo = app_com_contas.cliente.get("/").get_data(as_text=True)
    assert "Definir senha" in corpo

    formulario = app_com_contas.cliente.get("/definir-senha")
    assert "Defina uma senha para entrar sem depender do Google." in formulario.get_data(as_text=True)

    resposta = app_com_contas.cliente.post(
        "/definir-senha", data={"senha": SENHA, "repeticao": SENHA}
    )

    assert resposta.status_code == 303
    conta = app_com_contas.contas.por_sub(CONTA_A.sub)
    assert conta is not None
    assert conta.tem_senha
    assert conta.email_normalizado == CONTA_A.email


def test_depois_de_definir_a_entrada_por_senha_cai_no_mesmo_dono(app_com_contas):
    app_com_contas.entrar(CONTA_A)
    app_com_contas.cliente.post("/definir-senha", data={"senha": SENHA, "repeticao": SENHA})
    app_com_contas.cliente.post("/logout")

    resposta = entrar_com_senha(app_com_contas, CONTA_A.email, SENHA)

    assert resposta.status_code == 303
    conta = app_com_contas.contas.por_email(CONTA_A.email)
    assert conta.sub == CONTA_A.sub, "o dono nao pode mudar ao definir a senha"


def test_conta_que_ja_tem_senha_nao_abre_a_tela(app_com_contas):
    app_com_contas.entrar(CONTA_A)
    app_com_contas.cliente.post("/definir-senha", data={"senha": SENHA, "repeticao": SENHA})

    resposta = app_com_contas.cliente.get("/definir-senha", follow_redirects=False)

    assert resposta.status_code == 302


def test_senha_fraca_nao_define_nada(app_com_contas):
    app_com_contas.entrar(CONTA_A)

    resposta = app_com_contas.cliente.post(
        "/definir-senha", data={"senha": "abc", "repeticao": "abc"}
    )

    assert "Falta:" in resposta.get_data(as_text=True)
    assert not app_com_contas.contas.por_sub(CONTA_A.sub).tem_senha


def test_sem_sessao_a_rota_de_definir_vai_para_a_entrada(app_com_contas):
    resposta = app_com_contas.cliente.get("/definir-senha")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")
