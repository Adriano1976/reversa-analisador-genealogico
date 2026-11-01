"""A folha de fontes derivada (feature 054, `D-05` e `D-14`).

## O que este arquivo prova, sem rede

O derivado commitado e o que a receita produz: os 11 `woff2` existem, com o tamanho e o
`sha256` declarados em `tests/fontes_da_tela.py`, e a folha tem 45 blocos `@font-face`
apontando so para caminhos locais. A suite nao pode depender de internet — a receita sim, e
por isso ela fica separada do teste.

## Por que a folha precisa ser ASCII

Ela nao declara `@charset`. Um comentario com acento faria o arquivo depender de o leitor
adivinhar a codificacao; em ASCII o problema nao existe, e o teste prende isso.

## O conjunto fechado da rota

`src/web/rotas_assets.py` guarda a lista dos nomes aceitos em `/fontes/<arquivo>.woff2`.
Ela e a **mesma** lista da receita: se a receita ganhar um subconjunto novo e a rota nao,
o arquivo existiria em disco e daria `404` — este teste compara as duas.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from tests.fontes_da_tela import (  # noqa: E402
    ARQUIVOS,
    BLOCOS_ESPERADOS,
    FOLHA,
    FONTES,
)

URL_LOCAL = re.compile(r"url\(/fontes/([^)]+)\)")


def test_os_arquivos_de_fonte_sao_exatamente_os_da_receita():
    em_disco = {nome for nome in os.listdir(FONTES) if nome.endswith(".woff2")}
    assert em_disco == set(ARQUIVOS), (
        f"sobrando: {sorted(em_disco - set(ARQUIVOS))}; faltando: {sorted(set(ARQUIVOS) - em_disco)}"
    )


def test_cada_fonte_tem_o_tamanho_e_o_hash_declarados():
    for nome, (tamanho, sha) in ARQUIVOS.items():
        with open(os.path.join(FONTES, nome), "rb") as arquivo:
            dados = arquivo.read()
        assert len(dados) == tamanho, f"{nome}: {len(dados)} bytes"
        assert hashlib.sha256(dados).hexdigest() == sha, f"{nome}: hash diferente do declarado"


def test_a_folha_e_ascii():
    with open(FOLHA, "rb") as arquivo:
        dados = arquivo.read()
    assert dados.isascii(), "fontes.css tem byte fora de ASCII"


def test_a_folha_mantem_os_blocos_e_nao_aponta_para_fora():
    with open(FOLHA, encoding="ascii") as arquivo:
        css = arquivo.read()
    assert css.count("@font-face") == BLOCOS_ESPERADOS
    assert "fonts.gstatic.com" not in css
    assert "url(http" not in css
    assert "url(//" not in css
    # O comentario de cabecalho CITA a origem (procedencia, `RN-07`); o que nao pode haver e
    # `url()` apontando para fora da aplicacao.
    alvos = re.findall(r"url\(([^)]+)\)", css)
    assert alvos, "a folha nao referencia fonte nenhuma"
    assert all(alvo.startswith("/fontes/") for alvo in alvos), sorted(set(alvos))[:3]


def test_todas_as_urls_da_folha_apontam_para_um_arquivo_do_conjunto():
    with open(FOLHA, encoding="ascii") as arquivo:
        css = arquivo.read()
    nomes = URL_LOCAL.findall(css)
    assert len(nomes) == BLOCOS_ESPERADOS
    assert set(nomes) == set(ARQUIVOS)
    assert css.count("/fontes/") == BLOCOS_ESPERADOS


def test_a_rota_aceita_exatamente_o_conjunto_da_receita():
    from web.rotas_assets import FONTES_DA_TELA

    assert set(FONTES_DA_TELA) == set(ARQUIVOS)
