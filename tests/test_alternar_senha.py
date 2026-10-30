"""Alternancia de visibilidade das senhas, no tipo do `bootstrap-show-password-toggle`.

O contrato tem tres metades:

1. o HTML entrega o campo com um botao **vazio** e `d-none` — sem JavaScript nao ha
   controle inerte, e o formulario funciona igual (`RF-18`);
2. o olho e o `background-image` do proprio campo, e o botao so cobre a area dele;
3. o script revela o botao no primeiro foco/entrada e troca `type` e `aria-label`.

O clique nao e testado aqui (a suite nao executa JavaScript); a conferencia manual
esta no `onboarding.md`.
"""
from __future__ import annotations

from tests.fixtures.autenticacao import CONTA_A
from tests.fixtures.identidade import cadastrar_e_confirmar, token_do_corpo

SENHA = "Senha#2026"


def _corpo(app, caminho: str) -> str:
    return app.cliente.get(caminho).get_data(as_text=True)


def _quantidade_de_botoes(corpo: str) -> int:
    return corpo.count('data-alternar-senha="')


def test_login_tem_alternancia_no_campo_de_senha(app_com_contas):
    corpo = _corpo(app_com_contas, "/login")

    assert _quantidade_de_botoes(corpo) == 1
    assert 'data-alternar-senha="senha"' in corpo
    assert 'name="senha"' in corpo
    assert 'type="password"' in corpo


def test_o_botao_e_vazio_e_nasce_oculto(app_com_contas):
    """O tipo do projeto de origem: sem texto e com `d-none` ate o primeiro foco."""
    corpo = _corpo(app_com_contas, "/login")

    assert 'class="botao-de-senha d-none"' in corpo
    assert 'aria-label="Mostrar senha"></button>' in corpo
    assert ">Mostrar<" not in corpo, "o botao voltou a ter texto; o tipo e icone no campo"


def test_o_campo_desliga_correcao_e_capitalizacao(app_com_contas):
    """Recomendacao do projeto de origem: em texto visivel o navegador nao corrige."""
    corpo = _corpo(app_com_contas, "/login")

    assert 'spellcheck="false"' in corpo
    assert 'autocorrect="off"' in corpo
    assert 'autocapitalize="off"' in corpo


def test_o_botao_declara_estado_e_nao_submete(app_com_contas):
    corpo = _corpo(app_com_contas, "/login")

    assert 'type="button"' in corpo
    assert 'aria-pressed="false"' in corpo


def test_o_icone_ja_vem_visivel_no_html(app_com_contas):
    """O olho nao pode depender de foco nem de `:valid` para aparecer."""
    corpo = _corpo(app_com_contas, "/login")

    assert 'class="form-control input-password"' in corpo


def test_o_script_habilita_o_botao_e_troca_o_rotulo(app_com_contas):
    corpo = _corpo(app_com_contas, "/login")

    assert 'classList.remove("d-none")' in corpo
    assert 'aria-label", escondida ? "Esconder senha" : "Mostrar senha"' in corpo


def test_o_campo_arredonda_os_dois_lados(app_com_contas):
    """O `input-group` zera o raio do lado direito; a regra devolve o raio do tema."""
    css = app_com_contas.cliente.get("/app.css").get_data(as_text=True)

    assert ".campo-com-senha .form-control{border-radius:var(--r-2)!important}" in css


def test_o_icone_e_o_fundo_do_campo_e_nao_um_botao_com_texto(app_com_contas):
    """A folha e servida por `/app.css`; o olho vive nas regras de `input-password`."""
    css = app_com_contas.cliente.get("/app.css").get_data(as_text=True)

    assert '.input-password[type="text"]' in css
    assert '.input-password[type="password"]' in css
    assert "data:image/svg+xml" in css
    assert '.input-password[type="password"]:valid' not in css, (
        "o icone voltou a depender de `:valid`: com o campo vazio nao aparece"
    )


def test_cadastro_tem_alternancia_nos_dois_campos(app_com_contas):
    corpo = _corpo(app_com_contas, "/cadastro")

    assert _quantidade_de_botoes(corpo) == 2
    assert 'data-alternar-senha="senha"' in corpo
    assert 'data-alternar-senha="repeticao"' in corpo


def test_redefinicao_tem_alternancia_nos_dois_campos(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    app_com_contas.cliente.post("/recuperar-senha", data={"email": "teste@example.test"})
    token = token_do_corpo(app_com_contas.email.ultimo_corpo())

    corpo = _corpo(app_com_contas, f"/redefinir-senha?token={token}")

    assert _quantidade_de_botoes(corpo) == 2
    assert 'name="token"' in corpo


def test_definir_senha_tem_alternancia_nos_dois_campos(app_com_contas):
    app_com_contas.entrar(CONTA_A)

    corpo = _corpo(app_com_contas, "/definir-senha")

    assert _quantidade_de_botoes(corpo) == 2


def test_o_campo_de_email_nao_ganha_alternancia(app_com_contas):
    corpo = _corpo(app_com_contas, "/login")

    assert 'data-alternar-senha="email"' not in corpo
