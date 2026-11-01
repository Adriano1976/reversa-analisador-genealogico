"""Degradacao dos recursos embutidos (feature 054).

## O que este arquivo prova

Arquivo ausente **nao derruba a aplicacao**: a mesma regra das artes e da folha, em que o
recurso responde `404` e a tela continua em `200`. E nome de arquivo de fonte fora do
conjunto fechado responde `404` — inclusive quando o cliente tenta sair da pasta com
separador de caminho.

## Por que os testes monkeypatcham a config

O caminho ausente e simulado por `app.config`, e nao por arquivo apagado, para o teste nao
depender de mexer no repositorio. E o mesmo ponto que as artes usam.
"""
from __future__ import annotations

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from tests.fontes_da_tela import ARQUIVOS  # noqa: E402

FONTE_VALIDA = sorted(ARQUIVOS)[0]


@pytest.fixture
def resolvido(cliente_de_upload):
    app, cliente, _pasta = cliente_de_upload
    return app, cliente


@pytest.mark.parametrize(
    "rota, chave",
    [
        ("/bootstrap.css", "BIBLIOTECA_CSS"),
        ("/bootstrap.js", "BIBLIOTECA_JS"),
        ("/mermaid.js", "MERMAID"),
        ("/fontes.css", "FOLHA_DE_FONTES"),
    ],
)
def test_recurso_ausente_da_404_e_a_tela_continua(resolvido, monkeypatch, rota, chave):
    """`RNF` de disponibilidade: 404 no recurso, 200 na tela, nunca 500."""
    app, cliente = resolvido
    monkeypatch.setitem(app.config, chave, os.path.join("caminho", "que", "nao", "existe"))
    resposta = cliente.get(rota)
    assert resposta.status_code == 404
    assert resposta.get_data() == b""
    assert cliente.get("/").status_code == 200


def test_pasta_de_fontes_ausente_da_404(resolvido, monkeypatch):
    app, cliente = resolvido
    monkeypatch.setitem(app.config, "PASTA_DE_FONTES", os.path.join("pasta", "inexistente"))
    assert cliente.get("/fontes/" + FONTE_VALIDA).status_code == 404


def test_arquivo_de_fonte_ausente_da_404(resolvido, monkeypatch, tmp_path):
    """A pasta existe, o arquivo nao: mesmo desfecho das artes."""
    app, cliente = resolvido
    monkeypatch.setitem(app.config, "PASTA_DE_FONTES", str(tmp_path))
    assert cliente.get("/fontes/" + FONTE_VALIDA).status_code == 404


@pytest.mark.parametrize(
    "rota",
    [
        "/fontes/qualquer.woff2",
        "/fontes/nao-existe.woff2",
        "/fontes/..%5C..%5Capp.css.woff2",
        "/fontes/....woff2",
    ],
)
def test_nome_fora_do_conjunto_da_404(resolvido, rota):
    """`D-04`: o conjunto e fechado, e o 404 da rota e vazio.

    Separador de caminho nao encontra arquivo nenhum: o nome so vira caminho depois de passar
    pelo conjunto.
    """
    _app, cliente = resolvido
    resposta = cliente.get(rota)
    assert resposta.status_code == 404, f"{rota} respondeu {resposta.status_code}"
    assert resposta.get_data() == b""


@pytest.mark.parametrize(
    "rota",
    [
        "/fontes/%2e%2e%2fapp.css.woff2",
        "/fontes/%2Fetc%2Fpasswd.woff2",
    ],
)
def test_caminho_codificado_nao_serve_arquivo(resolvido, rota):
    """O `404` aqui e do roteador, nao da rota — o que importa e nao servir nada."""
    _app, cliente = resolvido
    assert cliente.get(rota).status_code == 404


def test_o_404_nao_revela_caminho_absoluto(resolvido):
    _app, cliente = resolvido
    corpo = cliente.get("/fontes/qualquer.woff2").get_data(as_text=True)
    assert "assets" not in corpo
    assert ":\\" not in corpo
