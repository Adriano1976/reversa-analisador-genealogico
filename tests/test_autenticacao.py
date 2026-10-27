"""O fluxo de entrada: configuracao, `state`, troca de codigo e perfil (feature 051).

Nenhum teste aqui fala com a rede: o provedor real recebe um transporte falso, e o
servico da borda recebe um provedor falso. O que se prende e o contrato de `RN-09`
e do `interfaces/provedor-de-identidade.md`.
"""
from __future__ import annotations

import pytest

from tests.fixtures.autenticacao import CONTA_A, ProvedorFalso, servico_de_teste
from web.autenticacao import (
    ConfiguracaoDeEntrada,
    ErroDeEntrada,
    ProvedorGoogle,
    servico_do_ambiente,
)

AMBIENTE = {
    "GOOGLE_CLIENT_ID": "cliente",
    "GOOGLE_CLIENT_SECRET": "segredo",
    "ANALISADOR_SECRET_KEY": "chave",
    "ANALISADOR_URL_PUBLICA": "https://exemplo.test",
    "ANALISADOR_DONO_INICIAL": "a@example.test",
}


def test_sem_as_variaveis_a_entrada_nao_e_montada():
    servico, faltantes = servico_do_ambiente({})

    assert servico is None
    assert faltantes == [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "ANALISADOR_SECRET_KEY",
        "ANALISADOR_URL_PUBLICA",
        "ANALISADOR_DONO_INICIAL",
    ], "a mensagem da subida tem de nomear todas as ausentes, e na ordem do contrato"


def test_com_as_variaveis_a_entrada_e_montada():
    servico, faltantes = servico_do_ambiente(AMBIENTE)

    assert faltantes == []
    assert servico.configuracao.url_de_retorno == "https://exemplo.test/callback"
    assert servico.configuracao.usa_https is True


def test_a_url_de_autorizacao_leva_o_contrato():
    provedor = ProvedorGoogle(
        ConfiguracaoDeEntrada(
            "cliente-de-teste", "segredo", "chave",
            "http://127.0.0.1:5000", "a@example.test",
        )
    )

    url = provedor.url_de_autorizacao("estado-abc")

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=cliente-de-teste" in url
    assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fcallback" in url
    assert "response_type=code" in url
    assert "state=estado-abc" in url
    assert "scope=openid%20email%20profile" in url


def test_o_perfil_sem_email_verificado_e_recusado():
    def pedir(metodo, url, **kwargs):
        if url.endswith("/token"):
            return 200, {"access_token": "token"}
        return 200, {"sub": "1", "email": "a@example.test", "email_verified": False}

    provedor = ProvedorGoogle(
        ConfiguracaoDeEntrada("id", "segredo", "chave", "http://127.0.0.1:5000", "a@example.test"),
        pedir,
    )

    with pytest.raises(ErroDeEntrada) as capturado:
        provedor.ler_perfil("token")

    assert capturado.value.motivo == "email_nao_verificado"


def test_a_troca_recusada_pelo_provedor_vira_erro_de_entrada():
    def pedir(metodo, url, **kwargs):
        return 400, {"error": "invalid_grant"}

    provedor = ProvedorGoogle(
        ConfiguracaoDeEntrada("id", "segredo", "chave", "http://127.0.0.1:5000", "a@example.test"),
        pedir,
    )

    with pytest.raises(ErroDeEntrada) as capturado:
        provedor.trocar_codigo("codigo")

    assert capturado.value.motivo == "token_http_400"


def test_o_callback_com_state_divergente_nao_cria_sessao(app_autenticado):
    cliente = app_autenticado.cliente
    with cliente.session_transaction() as sessao:
        sessao["oauth_state"] = "estado-certo"

    resposta = cliente.get("/callback?state=estado-errado&code=x")

    assert resposta.status_code == 200
    assert "A entrada expirou. Tente de novo." in resposta.get_data(as_text=True)
    assert cliente.get("/").status_code == 302, "uma sessao nasceu de um state invalido"


def test_o_state_e_de_uso_unico(app_autenticado):
    cliente = app_autenticado.cliente
    codigo = "codigo-1001"
    app_autenticado.provedor.contas[codigo] = CONTA_A
    with cliente.session_transaction() as sessao:
        sessao["oauth_state"] = "estado-um"

    assert cliente.get(f"/callback?state=estado-um&code={codigo}").status_code == 302

    cliente.get("/logout")
    repetido = cliente.get(f"/callback?state=estado-um&code={codigo}")

    assert "A entrada expirou. Tente de novo." in repetido.get_data(as_text=True)


def test_o_cancelamento_mostra_a_frase_e_nao_cria_sessao(app_autenticado):
    resposta = app_autenticado.cliente.get("/callback?error=access_denied")

    assert "A entrada foi cancelada." in resposta.get_data(as_text=True)
    assert app_autenticado.cliente.get("/").status_code == 302


def test_falha_na_troca_nao_cria_sessao(app_autenticado):
    app_autenticado.provedor.falhar_na_troca = True
    cliente = app_autenticado.cliente
    with cliente.session_transaction() as sessao:
        sessao["oauth_state"] = "estado-um"

    resposta = cliente.get("/callback?state=estado-um&code=qualquer")

    assert "Não foi possível concluir a entrada agora." in resposta.get_data(as_text=True)
    assert cliente.get("/").status_code == 302
