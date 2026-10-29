"""A busca nao muda o resultado da analise (feature 052, `RF-11`).

## O que este arquivo prende

O caminho e o de PRODUCAO nas duas pontas: a analise roda pela rota, com o GEDCOM
parseado de verdade, e a busca roda pela rota nova. O que se compara e o que o
operador ve — a mensagem de conexoes e a quantidade de cartoes —, antes e depois de
uma busca no meio.

## Por que isso e um portao, e nao uma formalidade

A tentacao de "reaproveitar" o ranking da busca dentro do `matching` existe, e ela
mudaria quem e aceito e quem e descartado. A `RN-06` proibe; este teste e o que faz a
proibicao valer alguma coisa.
"""
from __future__ import annotations

import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.sample_gedcom import SAMPLE_GED  # noqa: E402

CHAVE = "080e7943572d2652"
ARVORE = f"{CHAVE}__arvore.ged"
RELATORIO = f"{CHAVE}__relatorio.csv"

ARVORE_DE_TESTE = SAMPLE_GED

#: Relatorio sintetico com um nome que existe na arvore de `SAMPLE_GED`.
RELATORIO_DE_TESTE = "Name,Total cM,Kit\nCarlos Silva,120.0,AB123\n"

RAIZ_DA_ARVORE = "Carlos Silva"

_MENSAGEM = re.compile(r"(\d+) conexões encontradas")
_CARTAO = re.compile(r'id="resultado-\d+"')


def _guardar(pasta: str, nome: str, conteudo: str) -> None:
    with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)


def analisar(cliente) -> str:
    resposta = cliente.post(
        "/",
        data={
            "action": "dna_analysis",
            "gedcom_filename": ARVORE,
            "matches_csv_filename": RELATORIO,
            "root_name": RAIZ_DA_ARVORE,
        },
    )
    assert resposta.status_code == 200, (
        f"o POST de analise devolveu {resposta.status_code}; sem resultado nao ha o que comparar"
    )
    return resposta.get_data(as_text=True)


def _resumo(pagina: str) -> tuple[str | None, int]:
    achado = _MENSAGEM.search(pagina)
    return (achado.group(1) if achado else None, len(_CARTAO.findall(pagina)))


class TestABuscaNaoMudaAAnalise:
    def test_o_veredito_e_os_cartoes_sao_os_mesmos(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARVORE, ARVORE_DE_TESTE)
        _guardar(pasta, RELATORIO, RELATORIO_DE_TESTE)

        antes = _resumo(analisar(cliente))

        busca = cliente.post(
            "/busca", data={"termo": "Silva", "gedcom_filename": ARVORE}
        )
        assert busca.status_code == 200

        depois = _resumo(analisar(cliente))

        assert antes == depois
        assert antes[0] is not None, "a pagina de analise nao trouxe a mensagem de conexoes"

    def test_a_pagina_de_busca_nao_produz_resultado_de_analise(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARVORE, ARVORE_DE_TESTE)

        resposta = cliente.post(
            "/busca", data={"termo": "Silva", "gedcom_filename": ARVORE}
        )
        corpo = resposta.get_data(as_text=True)

        assert _MENSAGEM.search(corpo) is None
        assert _CARTAO.findall(corpo) == []

    def test_a_busca_nao_grava_nada_na_pasta(self, cliente_de_upload):
        """`RN-01`: a busca e leitura. A pasta nao ganha nem perde arquivo."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, ARVORE, ARVORE_DE_TESTE)

        antes = sorted(os.listdir(pasta))
        cliente.post("/busca", data={"termo": "Silva", "gedcom_filename": ARVORE})
        depois = sorted(os.listdir(pasta))

        assert antes == depois
