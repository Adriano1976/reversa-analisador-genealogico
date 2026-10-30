"""Rotas de identidade: publico, cabecalhos e origem (`RN-07`, `RN-13`, `RN-16`)."""
from __future__ import annotations


def test_rotas_publicas_abrem_sem_sessao(app_com_contas):
    for caminho in ("/login", "/cadastro", "/recuperar-senha", "/confirmar?token=x",
                    "/redefinir-senha?token=x"):
        assert app_com_contas.cliente.get(caminho).status_code == 200, caminho


def test_rota_autenticada_exige_sessao(app_com_contas):
    resposta = app_com_contas.cliente.get("/definir-senha")

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_respostas_de_identidade_nao_sao_cacheaveis(app_com_contas):
    for caminho in ("/login", "/cadastro", "/recuperar-senha"):
        resposta = app_com_contas.cliente.get(caminho)
        assert resposta.headers["Cache-Control"] == "no-store", caminho


def test_pagina_com_token_nao_entrega_referer(app_com_contas):
    resposta = app_com_contas.cliente.get("/confirmar?token=qualquer")

    assert resposta.headers["Referrer-Policy"] == "no-referrer"


def test_post_de_outra_origem_e_recusado(app_com_contas):
    resposta = app_com_contas.cliente.post(
        "/cadastro",
        data={"email": "teste@example.test", "senha": "Senha#2026", "repeticao": "Senha#2026"},
        headers={"Origin": "https://malicioso.example"},
    )

    assert resposta.status_code == 400
    assert app_com_contas.contas.quantidade() == 0


def test_tela_de_entrada_tem_os_controles_do_contrato(app_com_contas):
    corpo = app_com_contas.cliente.get("/login").get_data(as_text=True)

    assert "Entre na sua conta" in corpo
    assert "Entrar com Google" in corpo
    assert 'action="/login"' in corpo
    assert 'name="email"' in corpo
    assert 'name="senha"' in corpo
    assert "Esqueci minha senha" in corpo
    assert "Criar conta" in corpo


def test_icone_da_aba_aponta_para_a_arte_publica(app_com_contas):
    corpo = app_com_contas.cliente.get("/login").get_data(as_text=True)

    assert '<link rel="icon" type="image/png" sizes="128x128" href="/favicon.png">' in corpo
    assert '<link rel="apple-touch-icon" href="/apple-touch-icon.png">' in corpo


def test_a_tela_de_cadastro_mostra_a_politica(app_com_contas):
    corpo = app_com_contas.cliente.get("/cadastro").get_data(as_text=True)

    assert "A senha precisa ter ao menos 8 caracteres" in corpo
    assert 'name="repeticao"' in corpo


def test_a_tela_de_recuperacao_mostra_o_caminho_do_google(app_com_contas):
    corpo = app_com_contas.cliente.get("/recuperar-senha").get_data(as_text=True)

    assert "Se você entra apenas com Google" in corpo
    assert "Solicitar instruções" in corpo
