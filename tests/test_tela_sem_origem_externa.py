"""A tela nao referencia nenhum host externo (feature 054).

## O que este arquivo prova

`RF-01` e `RF-02`: nem a tela principal nem as telas de identidade declaram `link` de folha,
`link` de fonte, `preconnect` ou `script` apontando para uma origem externa. E `RF-12`: a
folha do Bootstrap continua **antes** da folha propria, que redefine as variaveis `--bs-*`.

## Por que a prova e sobre o HTML servido, e nao sobre o template

O template tem comentarios Jinja e ramos condicionais; o que o navegador ve e o documento
servido. Medir o servido pega inclusive uma tag esquecida dentro de um `{% if %}`.

## As telas de identidade

As seis herdam de `src/templates/_entrada_base.html`. Tres delas (login, cadastro e
recuperacao) sao publicas e renderizam sem sessao, entao sao verificadas pelo documento
servido; a base e conferida na fonte, porque as outras tres exigem token ou sessao. A base
**nao** pode referenciar a folha de fontes: essas telas nao carregam a webfont hoje, e a
tipografia delas tem de continuar a de hoje (`L-02`).
"""
from __future__ import annotations

import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

TAG_DE_RECURSO = re.compile(r"<(?:link|script)\b[^>]*>", re.IGNORECASE)
TAG_COM_SRC = re.compile(r"<script\b[^>]*\bsrc=\"([^\"]+)\"", re.IGNORECASE)

HOSTS_EXTERNOS = ("cdn.jsdelivr.net", "fonts.googleapis.com", "fonts.gstatic.com", "unpkg.com", "cdnjs.")

IDENTIDADES_PUBLICAS = ("/login", "/cadastro", "/recuperar-senha")

BASE_DAS_IDENTIDADES = os.path.join(RAIZ, "src", "templates", "_entrada_base.html")


def _tags(html: str) -> list[str]:
    return TAG_DE_RECURSO.findall(html)


def test_a_tela_principal_nao_declara_origem_externa(cliente_de_upload):
    """`RF-01`."""
    _app, cliente, _pasta = cliente_de_upload
    html = cliente.get("/").get_data(as_text=True)
    for tag in _tags(html):
        assert "https://" not in tag, f"tag com origem externa: {tag}"
        assert "//cdn" not in tag, f"tag com origem externa: {tag}"
    for host in HOSTS_EXTERNOS:
        assert host not in html, f"a tela ainda menciona {host}"


def test_a_tela_principal_nao_tem_preconnect(cliente_de_upload):
    """Os dois `preconnect` existiam so para as fontes do Google."""
    _app, cliente, _pasta = cliente_de_upload
    html = cliente.get("/").get_data(as_text=True).lower()
    assert "preconnect" not in html


def test_o_bootstrap_vem_antes_da_folha_propria(cliente_de_upload):
    """`RF-12`: a folha propria redefine `--bs-*` e precisa vencer."""
    _app, cliente, _pasta = cliente_de_upload
    html = cliente.get("/").get_data(as_text=True)
    assert html.index("/bootstrap.css") < html.index("/app.css")
    assert html.index("/fontes.css") < html.index("/app.css")


def test_o_mermaid_fica_no_head_e_o_bootstrap_no_fim_do_corpo(cliente_de_upload):
    """`RF-08` e `D-08`: trocar de lugar mudaria o comportamento, nao so a origem."""
    _app, cliente, _pasta = cliente_de_upload
    html = cliente.get("/").get_data(as_text=True)
    fontes = TAG_COM_SRC.findall(html)
    assert fontes, "a tela nao tem nenhum script com src"
    assert "/mermaid.js" in fontes[0], f"o primeiro script com src e {fontes[0]!r}"
    assert html.index("/mermaid.js") < html.index("<body")
    assert fontes[-1].startswith("/bootstrap.js"), f"o ultimo script com src e {fontes[-1]!r}"


def test_a_versao_aparece_nas_tags(cliente_de_upload):
    """`D-12`: sem `?v=` a atualizacao de uma biblioteca pode ficar presa no cache."""
    _app, cliente, _pasta = cliente_de_upload
    html = cliente.get("/").get_data(as_text=True)
    assert "/bootstrap.css?v=" in html
    assert "/bootstrap.js?v=" in html
    assert "/mermaid.js?v=" in html
    assert "/fontes.css?v=" in html


def test_as_telas_de_identidade_publicas_nao_declaram_origem_externa(app_autenticado):
    """`RF-02`: login, cadastro e recuperacao, no documento servido."""
    for rota in IDENTIDADES_PUBLICAS:
        html = app_autenticado.cliente.get(rota).get_data(as_text=True)
        for tag in _tags(html):
            assert "https://" not in tag, f"{rota}: tag com origem externa: {tag}"
        for host in HOSTS_EXTERNOS:
            assert host not in html, f"{rota} ainda menciona {host}"


def test_as_telas_de_identidade_nao_carregam_a_webfont(app_autenticado):
    """`L-02`: a tipografia delas continua a de hoje; a folha de fontes nao as alcanca."""
    for rota in IDENTIDADES_PUBLICAS:
        html = app_autenticado.cliente.get(rota).get_data(as_text=True)
        assert "/fontes.css" not in html, f"{rota} passou a carregar a webfont"
    with open(BASE_DAS_IDENTIDADES, encoding="utf-8") as arquivo:
        base = arquivo.read()
    assert "/fontes.css" not in base
    for tag in _tags(base):
        assert "https://" not in tag, f"a base das identidades tem origem externa: {tag}"
