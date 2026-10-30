"""Entrada com e-mail e senha (`RN-05`, `RN-10`, `RN-15`).

O que estes testes prendem: a resposta indistinguivel entre senha errada e e-mail
inexistente, a conta nao confirmada que so se revela depois da senha correta, e o
limite que conta a falha — nao a tentativa.
"""
from __future__ import annotations

from tests.fixtures.identidade import cadastrar_e_confirmar, entrar_com_senha
from web.textos_de_conta import ENTRADA_INVALIDA, ENTRADA_NAO_CONFIRMADA

SENHA = "Senha#2026"
OUTRA = "Outra#2026"


def test_entrada_correta_abre_a_sessao(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)

    resposta = entrar_com_senha(app_com_contas, "teste@example.test", SENHA)

    assert resposta.status_code == 303
    assert app_com_contas.cliente.get("/").status_code == 200


def test_senha_errada_e_email_inexistente_produzem_o_mesmo_corpo(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)

    errada = entrar_com_senha(app_com_contas, "teste@example.test", OUTRA)
    inexistente = entrar_com_senha(app_com_contas, "ninguem@example.test", SENHA)

    assert errada.status_code == inexistente.status_code == 200
    assert errada.get_data(as_text=True) == inexistente.get_data(as_text=True)
    assert ENTRADA_INVALIDA in errada.get_data(as_text=True)
    assert app_com_contas.cliente.get("/").status_code == 302


def test_conta_nao_confirmada_so_se_revela_depois_da_senha(app_com_contas):
    app_com_contas.cliente.post(
        "/cadastro",
        data={"email": "teste@example.test", "senha": SENHA, "repeticao": SENHA},
    )

    com_senha_errada = entrar_com_senha(app_com_contas, "teste@example.test", OUTRA)
    com_senha_certa = entrar_com_senha(app_com_contas, "teste@example.test", SENHA)

    assert ENTRADA_INVALIDA in com_senha_errada.get_data(as_text=True)
    assert ENTRADA_INVALIDA not in com_senha_certa.get_data(as_text=True)
    assert ENTRADA_NAO_CONFIRMADA in com_senha_certa.get_data(as_text=True)
    assert "Reenviar o link de confirmação" in com_senha_certa.get_data(as_text=True)


def test_limite_conta_a_falha_e_nao_a_tentativa(app_com_contas):
    cadastrar_e_confirmar(app_com_contas, email="teste@example.test", senha=SENHA)
    for _ in range(5):
        entrar_com_senha(app_com_contas, "teste@example.test", OUTRA)

    bloqueada = entrar_com_senha(app_com_contas, "teste@example.test", SENHA)

    assert bloqueada.status_code == 200
    assert ENTRADA_INVALIDA in bloqueada.get_data(as_text=True)

    app_com_contas.relogio.avancar(minutes=16)
    liberada = entrar_com_senha(app_com_contas, "teste@example.test", SENHA)

    assert liberada.status_code == 303


def test_google_continua_sem_senha_e_nao_quebra(app_com_contas):
    from tests.fixtures.autenticacao import CONTA_A

    resposta = app_com_contas.entrar(CONTA_A)

    assert resposta.status_code == 302
    assert app_com_contas.cliente.get("/").status_code == 200
