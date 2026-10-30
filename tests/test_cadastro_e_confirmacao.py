"""Cadastro e confirmacao pela rota (`RN-01`, `RN-07`, `RN-19`).

O teste atravessa a borda HTTP inteira: formulario, caso de uso, arquivo em
memoria e e-mail em memoria. A regra que mais importa aqui e a da resposta
identica — conta nova e conta existente precisam produzir o MESMO corpo.
"""
from __future__ import annotations

from tests.fixtures.identidade import (
    cadastrar_e_confirmar,
    entrar_com_senha,
    token_do_corpo,
)
from web.textos_de_conta import (
    CADASTRO_GENERICO,
    CONFIRMACAO_INVALIDA,
    EMAIL_CONFIRMADO,
    ENVIO_INDISPONIVEL,
    SENHAS_DIFERENTES,
)

SENHA = "Senha#2026"


def _postar_cadastro(app, email="teste@example.test", senha=SENHA, repeticao=None):
    return app.cliente.post(
        "/cadastro",
        data={"email": email, "senha": senha, "repeticao": senha if repeticao is None else repeticao},
    )


def test_cadastro_valido_cria_conta_nao_confirmada(app_com_contas):
    resposta = _postar_cadastro(app_com_contas, email="teste@example.test")

    assert resposta.status_code == 200
    assert CADASTRO_GENERICO in resposta.get_data(as_text=True)
    conta = app_com_contas.contas.por_email("teste@example.test")
    assert conta is not None
    assert not conta.confirmada
    assert len(app_com_contas.email.mensagens) == 1
    assert "confirmar?token=" in app_com_contas.email.ultimo_corpo()


def test_cadastro_nao_abre_sessao(app_com_contas):
    _postar_cadastro(app_com_contas)

    assert app_com_contas.cliente.get("/").status_code == 302


def test_senha_fraca_nao_cria_conta_e_nomeia_o_que_falta(app_com_contas):
    resposta = _postar_cadastro(app_com_contas, senha="abc")
    corpo = resposta.get_data(as_text=True)

    assert app_com_contas.contas.quantidade() == 0
    assert "Falta:" in corpo
    assert "maiúscula" in corpo
    assert "número" in corpo
    assert "caractere especial" in corpo


def test_repeticao_diferente_nao_cria_conta(app_com_contas):
    resposta = _postar_cadastro(app_com_contas, repeticao="Outra#2026")

    assert SENHAS_DIFERENTES in resposta.get_data(as_text=True)
    assert app_com_contas.contas.quantidade() == 0


def test_email_duplicado_responde_igual_e_avisa_o_dono(app_com_contas):
    _postar_cadastro(app_com_contas, email="teste@example.test")
    quantidade = app_com_contas.contas.quantidade()
    mensagens = len(app_com_contas.email.mensagens)

    reposta_duplicada = _postar_cadastro(app_com_contas, email="teste@example.test")

    assert reposta_duplicada.status_code == 200
    assert CADASTRO_GENERICO in reposta_duplicada.get_data(as_text=True)
    assert app_com_contas.contas.quantidade() == quantidade
    assert len(app_com_contas.email.mensagens) == mensagens + 1
    assert "já tem conta" in app_com_contas.email.ultimo_corpo() or (
        "Alguém tentou" in app_com_contas.email.ultimo_corpo()
    )


def test_confirmacao_pelo_link_habilita_a_entrada(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    conta = app_com_contas.contas.por_email("teste@example.test")
    assert conta.confirmada

    resposta = entrar_com_senha(app_com_contas, "teste@example.test", SENHA)

    assert resposta.status_code == 303
    assert resposta.headers["Location"].endswith("/")


def test_token_invalido_mostra_a_mensagem_de_link_vencido(app_com_contas):
    resposta = app_com_contas.cliente.get("/confirmar?token=nao-existe")

    assert CONFIRMACAO_INVALIDA in resposta.get_data(as_text=True)


def test_confirmacao_consome_o_token(app_com_contas):
    dados = cadastrar_e_confirmar(app_com_contas)

    segunda = app_com_contas.cliente.get(f"/confirmar?token={dados['token']}")

    assert CONFIRMACAO_INVALIDA in segunda.get_data(as_text=True)
    assert EMAIL_CONFIRMADO not in segunda.get_data(as_text=True)


def test_reenvio_invalida_o_token_anterior(app_com_contas):
    _postar_cadastro(app_com_contas, email="teste@example.test")
    primeiro = token_do_corpo(app_com_contas.email.ultimo_corpo())

    app_com_contas.cliente.post(
        "/reenviar-confirmacao", data={"email": "teste@example.test"}
    )
    segundo = token_do_corpo(app_com_contas.email.ultimo_corpo())

    assert primeiro != segundo
    antigo = app_com_contas.cliente.get(f"/confirmar?token={primeiro}")
    assert CONFIRMACAO_INVALIDA in antigo.get_data(as_text=True)


def test_limite_de_cadastros_por_origem(app_com_contas):
    for indice in range(5):
        resposta = _postar_cadastro(app_com_contas, email=f"pessoa{indice}@example.test")
        assert resposta.status_code == 200

    sexta = _postar_cadastro(app_com_contas, email="sexta@example.test")

    assert CADASTRO_GENERICO in sexta.get_data(as_text=True)
    assert app_com_contas.contas.por_email("sexta@example.test") is None


def test_sem_transporte_o_cadastro_avisa_e_nao_cria_conta(app_com_contas):
    from application.cadastro import ServicoDeCadastro
    from tests.fixtures.identidade import EmailDesligado

    borda = app_com_contas.app.extensions["analisador"]
    borda["cadastro"] = ServicoDeCadastro(
        borda["contas"],
        EmailDesligado(),
        borda["relogio"],
        borda["limitador"],
        url_publica="http://127.0.0.1:5000",
    )

    resposta = _postar_cadastro(app_com_contas, email="sem-smtp@example.test")

    assert ENVIO_INDISPONIVEL in resposta.get_data(as_text=True)
    assert app_com_contas.contas.por_email("sem-smtp@example.test") is None
