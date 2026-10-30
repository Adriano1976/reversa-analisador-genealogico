"""Recuperacao e redefinicao de senha (`RN-08`, `RN-09`, `RN-10`)."""
from __future__ import annotations

from tests.fixtures.identidade import (
    cadastrar_e_confirmar,
    entrar_com_senha,
    token_do_corpo,
)
from web.textos_de_conta import (
    ENVIO_INDISPONIVEL,
    RECUPERACAO_GENERICA,
    REDEFINICAO_INVALIDA,
    SENHA_ALTERADA,
)

SENHA = "Senha#2026"
NOVA = "NovaSenha#2027"


def _pedir_link(app, email="teste@example.test"):
    return app.cliente.post("/recuperar-senha", data={"email": email})


def test_recuperacao_responde_igual_com_e_sem_conta(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    mensagens = len(app_com_contas.email.mensagens)

    _pedir_link(app_com_contas, "teste@example.test")
    com_conta = _pedir_link(app_com_contas, "ninguem@example.test")

    assert RECUPERACAO_GENERICA in com_conta.get_data(as_text=True)
    # Um envio para a conta existente; nenhum para a inexistente.
    assert len(app_com_contas.email.mensagens) == mensagens + 1


def test_link_valido_mostra_o_formulario_e_nao_consome(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    _pedir_link(app_com_contas)
    token = token_do_corpo(app_com_contas.email.ultimo_corpo())

    primeira = app_com_contas.cliente.get(f"/redefinir-senha?token={token}")
    segunda = app_com_contas.cliente.get(f"/redefinir-senha?token={token}")

    assert "Defina uma nova senha" in primeira.get_data(as_text=True)
    assert "Defina uma nova senha" in segunda.get_data(as_text=True)


def test_link_invalido_mostra_a_mensagem_de_vencido(app_com_contas):
    resposta = app_com_contas.cliente.get("/redefinir-senha?token=nao-existe")

    assert REDEFINICAO_INVALIDA in resposta.get_data(as_text=True)


def test_redefinicao_troca_a_senha_e_consome_o_token(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    _pedir_link(app_com_contas)
    token = token_do_corpo(app_com_contas.email.ultimo_corpo())

    resposta = app_com_contas.cliente.post(
        "/redefinir-senha",
        data={"token": token, "senha": NOVA, "repeticao": NOVA},
    )

    assert resposta.status_code == 303
    assert resposta.headers["Location"].endswith("/login")
    assert entrar_com_senha(app_com_contas, "teste@example.test", SENHA).status_code == 200
    assert entrar_com_senha(app_com_contas, "teste@example.test", NOVA).status_code == 303

    segundo_uso = app_com_contas.cliente.post(
        "/redefinir-senha",
        data={"token": token, "senha": "Outra#2028", "repeticao": "Outra#2028"},
    )
    assert REDEFINICAO_INVALIDA in segundo_uso.get_data(as_text=True)


def test_senha_fraca_nao_consome_o_token(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    _pedir_link(app_com_contas)
    token = token_do_corpo(app_com_contas.email.ultimo_corpo())

    recusada = app_com_contas.cliente.post(
        "/redefinir-senha", data={"token": token, "senha": "abc", "repeticao": "abc"}
    )
    valida = app_com_contas.cliente.get(f"/redefinir-senha?token={token}")

    assert "Falta:" in recusada.get_data(as_text=True)
    assert "Defina uma nova senha" in valida.get_data(as_text=True)


def test_sessao_anterior_cai_depois_da_redefinicao(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    entrar_com_senha(app_com_contas, "teste@example.test", SENHA)
    assert app_com_contas.cliente.get("/").status_code == 200

    _pedir_link(app_com_contas)
    token = token_do_corpo(app_com_contas.email.ultimo_corpo())
    app_com_contas.cliente.post(
        "/redefinir-senha", data={"token": token, "senha": NOVA, "repeticao": NOVA}
    )

    assert app_com_contas.cliente.get("/").status_code == 302


def test_token_expirado_e_recusado(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    _pedir_link(app_com_contas)
    token = token_do_corpo(app_com_contas.email.ultimo_corpo())
    app_com_contas.relogio.avancar(minutes=61)

    resposta = app_com_contas.cliente.post(
        "/redefinir-senha", data={"token": token, "senha": NOVA, "repeticao": NOVA}
    )

    assert REDEFINICAO_INVALIDA in resposta.get_data(as_text=True)


def test_sem_transporte_a_recuperacao_avisa(app_com_contas):
    from application.recuperacao import ServicoDeRecuperacao
    from tests.fixtures.identidade import EmailDesligado

    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    borda = app_com_contas.app.extensions["analisador"]
    borda["recuperacao"] = ServicoDeRecuperacao(
        borda["contas"], EmailDesligado(), borda["relogio"], borda["limitador"],
        url_publica="http://127.0.0.1:5000",
    )

    resposta = _pedir_link(app_com_contas)

    assert ENVIO_INDISPONIVEL in resposta.get_data(as_text=True)


def test_apos_redefinir_a_tela_de_entrada_mostra_a_frase(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    _pedir_link(app_com_contas)
    token = token_do_corpo(app_com_contas.email.ultimo_corpo())
    app_com_contas.cliente.post(
        "/redefinir-senha", data={"token": token, "senha": NOVA, "repeticao": NOVA}
    )

    tela = app_com_contas.cliente.get("/login")

    assert SENHA_ALTERADA in tela.get_data(as_text=True)
