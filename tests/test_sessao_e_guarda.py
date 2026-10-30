"""A guarda da borda e o cookie de sessao (feature 051).

O que se mede aqui e o contrato de `RN-03`, `RN-06` e `RF-06`: sem sessao, as
sete operacoes de dado nao rodam; as tres rotas de arte continuam publicas; o
cookie tem os atributos declarados; e a resposta autenticada nao pode ser
cacheada, para o "voltar" nao reexibir a tela depois do logout.
"""
from __future__ import annotations

import os

from tests.fixtures.autenticacao import CONTA_A


def test_sem_sessao_o_get_da_tela_vai_para_a_entrada(app_autenticado):
    resposta = app_autenticado.cliente.get("/")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")


def test_sem_sessao_o_post_nao_toca_dado(app_autenticado):
    resposta = app_autenticado.cliente.post("/", data={"action": "upload_gedcom"})

    assert resposta.status_code == 303, "POST sem sessao tem de ser 303, e nao 200"
    assert resposta.headers["Location"].endswith("/login")
    assert os.listdir(app_autenticado.pasta) == [], (
        "a acao sem sessao tocou a pasta de upload: a guarda nao rodou antes do handler"
    )


def test_as_tres_rotas_de_arte_continuam_publicas(app_autenticado):
    for caminho in ("/app.css", "/banner.png", "/apple-touch-icon.png"):
        resposta = app_autenticado.cliente.get(caminho)
        assert resposta.status_code != 302, (
            f"{caminho} foi redirecionado: a tela de entrada depende dela (P-08)"
        )


def test_a_tela_de_entrada_e_publica(app_autenticado):
    resposta = app_autenticado.cliente.get("/login")

    assert resposta.status_code == 200
    assert b"Entrar com Google" in resposta.data


def test_o_cookie_de_sessao_tem_os_atributos_do_contrato(app_autenticado):
    resposta = app_autenticado.entrar(CONTA_A)

    assert resposta.status_code == 302
    cookie = resposta.headers.get("Set-Cookie", "")
    assert "analisador_sessao=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Secure" not in cookie, (
        "o cookie saiu Secure com URL publica em http://: o uso local perde a sessao"
    )


def test_a_resposta_autenticada_nao_pode_ser_cacheada(app_autenticado):
    app_autenticado.entrar(CONTA_A)

    resposta = app_autenticado.cliente.get("/")

    assert resposta.status_code == 200
    assert resposta.headers.get("Cache-Control") == "no-store", (
        "sem no-store, o 'voltar' reexibe a tela depois do logout (RF-06)"
    )


def test_sair_encerra_a_sessao(app_autenticado):
    app_autenticado.entrar(CONTA_A)

    resposta = app_autenticado.cliente.post("/logout")

    assert resposta.status_code == 303
    assert app_autenticado.cliente.get("/").status_code == 302


def test_no_modo_de_teste_o_caminho_e_o_legado(cliente_de_upload):
    """Com o escape de teste ligado, o app e o de antes: sem guarda e sem Blueprint.

    O caminho aberto deixou de ser o padrao (auditoria de 2026-10-30): agora ele so
    existe com `ANALISADOR_MODO_TESTE=1`, que o `tests/conftest.py` declara. Quem
    garante que a aplicacao RECUSA subir sem modo declarado e
    `tests/test_modo_de_identidade.py`.
    """
    _app, cliente, _pasta = cliente_de_upload

    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert b"Sair" not in resposta.data
    assert cliente.get("/login").status_code == 404
