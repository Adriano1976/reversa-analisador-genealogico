"""Estado DESABILITADO da persistencia historica (`T018`; `D-02`, `RF-13`).

A persistencia esta desligada quando nao ha `DATABASE_URL`. O que este arquivo
prende e que, nesse estado, **nada muda** em relacao ao comportamento anterior a
feature 008:

- a borda monta o registrador **nulo** (`None`), e nao um objeto que falha;
- a analise de DNA continua saindo na tela, com o mesmo resultado;
- **nenhum aviso** de persistencia aparece.

O ultimo ponto e o que protege a paridade das 6 fixtures e os `261` testes: a
suite e o harness importam `src/app.py`, e um aviso emitido com a persistencia
desligada **por configuracao** mudaria o contrato congelado de tela sem que nada
tivesse sido pedido ao banco.
"""
from __future__ import annotations

import importlib.util
import io
import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PASTA_APP = os.path.join(_RAIZ, "src")
sys.path.insert(0, _RAIZ)
sys.path.insert(0, _PASTA_APP)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fixtures.sample_dna import DNA_CSV_UTF8, DNA_GED  # noqa: E402


def _carregar_app(nome: str):
    """Carrega `src/app.py` como modulo novo, do jeito que a fixture da suite faz."""
    caminho = os.path.join(_PASTA_APP, "app.py")
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    return modulo


def _carregar_arvore(client) -> str:
    pagina = client.post(
        "/",
        data={"action": "upload_gedcom",
              "gedcom": (io.BytesIO(DNA_GED.encode()), "arvore.ged")},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    chave = re.search(r'name="gedcom_filename" value="([^"]+)"', pagina)
    assert chave, "o upload não devolveu a chave"
    return chave.group(1)


def _analisar(client, chave):
    return client.post(
        "/",
        data={"action": "dna_analysis", "gedcom_filename": chave,
              "root_name": "Carlos Silva Souza",
              "matches_csv": (io.BytesIO(DNA_CSV_UTF8.encode()), "matches.csv")},
        content_type="multipart/form-data",
    )


@pytest.fixture
def cliente_sem_url(cliente_de_upload, monkeypatch):
    """A suite inteira roda sem `DATABASE_URL`, e a fixture garante que aqui tambem."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return cliente_de_upload


def test_guarda_contra_teste_vacuamente_verde():
    """Se a variavel existisse, nada abaixo mediria o estado desabilitado."""
    assert "DATABASE_URL" not in os.environ, (
        "a suite passou a rodar com DATABASE_URL definida — este arquivo mediria o "
        "estado errado, e o RF-13 deixaria de ser verificavel por aqui"
    )


def test_a_borda_monta_registrador_nulo(cliente_sem_url):
    """`D-02`, estado 1: sem a variavel, o registrador e `None` — e nao um objeto."""
    assert cliente_sem_url[0] is not None
    modulo = _carregar_app("_app_persistencia_desabilitada")

    assert modulo.DATABASE_URL is None, "a borda leu DATABASE_URL do ambiente"
    assert modulo._REGISTRO is None, "apareceu registrador sem DATABASE_URL"


def test_a_analise_sai_igual_e_sem_aviso(cliente_sem_url):
    """`RF-13`: mesma tela, mesmo resultado, e **nenhum** aviso de persistencia."""
    _, client, _ = cliente_sem_url
    chave = _carregar_arvore(client)
    resposta = _analisar(client, chave)
    pagina = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "Ana Silva Souza" in pagina, "o resultado da analise sumiu da tela"
    assert "Histórico não registrado" not in pagina, (
        "o aviso apareceu com a persistencia DESABILITADA por configuracao — e isso "
        "mudaria o contrato de tela sem que nada tivesse sido pedido ao banco"
    )
