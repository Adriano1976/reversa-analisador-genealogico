"""As telas da entrada: login com dois caminhos e masthead com a conta.

Contrato do login mudou por decisao declarada na feature 053 (`RN-17`): o cartao
passou a ter campos de e-mail e senha, os links de recuperacao e cadastro e o
icone da aba. As frases da 051 continuam byte a byte — elas sao os literais que o
harness e os testes daquela entrega congelaram.
"""
from __future__ import annotations

from tests.fixtures.autenticacao import CONTA_A


def test_a_tela_de_entrada_tem_os_literais_do_contrato(app_autenticado):
    corpo = app_autenticado.cliente.get("/login").get_data(as_text=True)

    assert "Entrar com Google" in corpo
    assert "Entre com a sua conta Google para continuar." in corpo
    assert "Entre na sua conta" in corpo
    assert "Esqueci minha senha" in corpo
    assert "Criar conta" in corpo


def test_a_tela_de_entrada_tem_o_formulario_de_senha(app_autenticado):
    corpo = app_autenticado.cliente.get("/login").get_data(as_text=True)

    assert 'action="/login"' in corpo
    assert 'name="email"' in corpo
    assert 'name="senha"' in corpo
    assert ">Entrar</button>" in corpo


def test_a_tela_de_entrada_tem_o_icone_da_aba(app_autenticado):
    corpo = app_autenticado.cliente.get("/login").get_data(as_text=True)

    assert '<link rel="icon" type="image/png" sizes="128x128" href="/favicon.png">' in corpo
    assert '<link rel="apple-touch-icon" href="/apple-touch-icon.png">' in corpo


def test_a_falha_aparece_na_tela_de_entrada(app_autenticado):
    corpo = app_autenticado.cliente.get("/callback?error=access_denied").get_data(
        as_text=True
    )

    assert "A entrada foi cancelada." in corpo
    assert "Entrar com Google" in corpo, "a tela de entrada sumiu da resposta de falha"


def test_a_masthead_mostra_a_conta_e_o_comando_de_sair(app_autenticado):
    app_autenticado.entrar(CONTA_A)

    corpo = app_autenticado.cliente.get("/").get_data(as_text=True)

    assert "Conta A" in corpo
    assert "Sair" in corpo
    assert 'action="/logout"' in corpo, "o comando de sair nao e um formulario POST"


def test_a_masthead_oferece_definir_senha_a_quem_nao_tem(app_autenticado):
    app_autenticado.entrar(CONTA_A)

    corpo = app_autenticado.cliente.get("/").get_data(as_text=True)

    assert "Definir senha" in corpo


def test_sem_sessao_nao_ha_comando_de_sair(app_autenticado):
    corpo = app_autenticado.cliente.get("/login").get_data(as_text=True)

    assert "Sair" not in corpo


def test_a_tela_de_entrada_mostra_a_arte_do_topo(app_autenticado):
    """O banner da masthead tambem aparece na entrada (2026-10-27)."""
    corpo = app_autenticado.cliente.get("/login").get_data(as_text=True)

    assert 'src="/banner.png"' in corpo
    assert "árvore genealógica" in corpo, "o alt da ilustração sumiu da entrada"
