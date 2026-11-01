"""Os recursos embutidos da tela (feature 054).

## O que este arquivo prova

O contrato de `interfaces/recursos-embutidos.md`: cada biblioteca de front-end que a tela usava
da CDN passou a ser servida pela propria aplicacao, **byte a byte** o arquivo oficial, com o
tipo de midia certo e publico (sem sessao). A folha de fontes e os 11 subconjuntos `woff2`
entram pela mesma porta.

## Por que o `sha256` mora aqui

E a prova de que o arquivo servido e o **oficial**, e nao uma copia editada a mao. O valor foi
medido no download (ver `_reversa_forward/054-.../evidence/procedencia.md`) e vira a ancora:
se alguem trocar o arquivo sem declarar, este teste cai antes do navegador perceber.

## O que este arquivo NAO prende

A ordem das tags no documento e a ausencia de origem externa: isso e
`tests/test_tela_sem_origem_externa.py`. A degradacao por arquivo ausente e
`tests/test_recursos_degradacao.py`.
"""
from __future__ import annotations

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from tests.fontes_da_tela import ARQUIVOS, BLOCOS_ESPERADOS  # noqa: E402

#: `rota -> (chave de config, tipo de midia, bytes, sha256)`.
BIBLIOTECAS = {
    "/bootstrap.css": (
        "BIBLIOTECA_CSS",
        "text/css",
        232803,
        "3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8",
    ),
    "/bootstrap.js": (
        "BIBLIOTECA_JS",
        "text/javascript",
        80721,
        "0833b2e9c3a26c258476c46266e6877fc75218625162e0460be9a3a098a61c6c",
    ),
    "/mermaid.js": (
        "MERMAID",
        "text/javascript",
        3337857,
        "8d607d7ef1d077a8aa202e18e62212bfa992c68bfeabc5cf45d51a128fe6675d",
    ),
}

FOLHA_DE_FONTES = "/fontes.css"
FONTE = "/fontes/" + sorted(ARQUIVOS)[0]


@pytest.fixture
def resolvido(cliente_de_upload):
    app, cliente, _pasta = cliente_de_upload
    return app, cliente


@pytest.mark.parametrize("rota", sorted(BIBLIOTECAS))
def test_a_biblioteca_responde_200(resolvido, rota):
    """`RF-03`, `RF-04`, `RF-05`. Antes da feature estas rotas davam 404."""
    _app, cliente = resolvido
    assert cliente.get(rota).status_code == 200


@pytest.mark.parametrize("rota", sorted(BIBLIOTECAS))
def test_o_tipo_de_midia_e_o_declarado(resolvido, rota):
    """Nunca `text/html`: um CSS servido como pagina quebra o navegador em silencio."""
    _app, cliente = resolvido
    _chave, tipo, _tamanho, _sha = BIBLIOTECAS[rota]
    recebido = cliente.get(rota).headers.get("Content-Type", "")
    assert recebido.split(";")[0].strip() == tipo, f"{rota}: Content-Type {recebido!r}"


@pytest.mark.parametrize("rota", sorted(BIBLIOTECAS))
def test_o_corpo_e_byte_a_byte_o_arquivo_em_disco(resolvido, rota):
    """`RF-03` a `RF-05`: o corpo servido e o arquivo, sem transformacao."""
    app, cliente = resolvido
    chave, _tipo, tamanho, _sha = BIBLIOTECAS[rota]
    corpo = cliente.get(rota).get_data()
    with open(app.config[chave], "rb") as arquivo:
        esperado = arquivo.read()
    assert corpo == esperado
    assert len(corpo) == tamanho


@pytest.mark.parametrize("rota", sorted(BIBLIOTECAS))
def test_o_arquivo_e_o_oficial_da_versao(resolvido, rota):
    """O `sha256` medido no download: o arquivo nao foi editado a mao."""
    _app, cliente = resolvido
    _chave, _tipo, _tamanho, sha = BIBLIOTECAS[rota]
    import hashlib

    assert hashlib.sha256(cliente.get(rota).get_data()).hexdigest() == sha


@pytest.mark.parametrize("rota", sorted(BIBLIOTECAS))
def test_o_recurso_nao_depende_de_sessao(resolvido, rota):
    """`RF-09` e `RN-06`: a tela de entrada, servida a quem nao tem sessao, depende deles."""
    _app, cliente = resolvido
    assert cliente.get(rota).status_code == 200


@pytest.mark.parametrize("rota", sorted(BIBLIOTECAS))
def test_o_recurso_recebe_o_cabecalho_de_enquadramento(resolvido, rota):
    """`RF-11`: o `after_request` da borda vale para os recursos novos, como para as artes."""
    _app, cliente = resolvido
    assert cliente.get(rota).headers.get("X-Frame-Options") == "DENY"


def test_a_folha_de_fontes_responde_200_como_css(resolvido):
    """`RF-14`: a folha derivada e servida pela aplicacao."""
    _app, cliente = resolvido
    resposta = cliente.get(FOLHA_DE_FONTES)
    assert resposta.status_code == 200
    assert resposta.headers.get("Content-Type", "").split(";")[0].strip() == "text/css"


def test_a_folha_de_fontes_tem_os_blocos_e_so_caminhos_locais(resolvido):
    """`RF-14`: 45 blocos `@font-face`, e nenhum `url()` apontando para fora."""
    import re

    _app, cliente = resolvido
    css = cliente.get(FOLHA_DE_FONTES).get_data(as_text=True)
    assert css.count("@font-face") == BLOCOS_ESPERADOS
    assert "fonts.gstatic.com" not in css
    nomes = re.findall(r"url\(/fontes/([^)]+)\)", css)
    assert len(nomes) == BLOCOS_ESPERADOS
    assert set(nomes) == set(ARQUIVOS)
    assert len(re.findall(r"url\(", css)) == BLOCOS_ESPERADOS


def test_cada_subconjunto_de_fonte_responde_200(resolvido):
    """`RF-14`: os 11 arquivos que a folha referencia existem e sao servidos."""
    app, cliente = resolvido
    for nome in sorted(ARQUIVOS):
        resposta = cliente.get("/fontes/" + nome)
        assert resposta.status_code == 200, nome
        assert resposta.headers.get("Content-Type", "").split(";")[0].strip() == "font/woff2"
        with open(os.path.join(app.config["PASTA_DE_FONTES"], nome), "rb") as arquivo:
            assert resposta.get_data() == arquivo.read()


def test_o_parametro_de_versao_nao_muda_o_corpo(resolvido):
    """`D-12`: `?v=` existe so para o navegador invalidar o cache."""
    _app, cliente = resolvido
    sem = cliente.get("/bootstrap.css").get_data()
    com = cliente.get("/bootstrap.css?v=5.3.3").get_data()
    assert sem == com
