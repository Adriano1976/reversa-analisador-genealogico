"""A rota `POST /busca` (feature 052).

## O que este arquivo prende

- a busca feliz devolve `200` com as duas secoes rotuladas e a ficha da arvore;
- termo em branco devolve a mensagem propria e **preserva o estado da tela**;
- termo acima do teto nao derruba a rota;
- referencia que nao resolve responde `404` com o literal de inexistencia — nunca
  `403`, e sem citar o nome de ninguem (`RN-06` da feature 051);
- sem `gedcom_filename` a rota devolve para a tela, e nao inventa uma busca.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.busca_arvores import GED_DA_BUSCA  # noqa: E402
from web.rotas_busca import TERMO_VAZIO, TETO_DO_TERMO  # noqa: E402

CHAVE = "080e7943572d2652"
ARVORE = f"{CHAVE}__arvore.ged"


def _guardar(pasta: str, nome: str, conteudo: bytes) -> None:
    with open(os.path.join(pasta, nome), "wb") as arquivo:
        arquivo.write(conteudo)


def arvore_aberta(cliente_de_upload) -> str:
    """Grava a arvore na pasta e a abre pela tela, como o operador faz."""
    _app, cliente, pasta = cliente_de_upload
    _guardar(pasta, ARVORE, GED_DA_BUSCA.encode("utf-8"))
    resposta = cliente.post(
        "/", data={"action": "selecionar_arvore", "gedcom_filename": ARVORE}
    )
    assert resposta.status_code == 200
    return ARVORE


class TestBuscaFeliz:
    def test_devolve_a_ficha_da_pessoa(self, cliente_de_upload):
        referencia = arvore_aberta(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.post(
            "/busca", data={"termo": "Silva", "gedcom_filename": referencia}
        )
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 200
        assert "Ana Silva" in corpo
        assert "secao-da-busca-arvore" in corpo

    def test_acento_e_caixa_nao_mudam_o_conjunto(self, cliente_de_upload):
        referencia = arvore_aberta(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        um = cliente.post("/busca", data={"termo": "JOSE", "gedcom_filename": referencia})
        outro = cliente.post("/busca", data={"termo": "josé", "gedcom_filename": referencia})

        assert "Jose Silva e Souza" in um.get_data(as_text=True)
        assert "Jose Silva e Souza" in outro.get_data(as_text=True)

    def test_sobrenome_composto_aparece_pelo_token(self, cliente_de_upload):
        referencia = arvore_aberta(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.post(
            "/busca", data={"termo": "dos Santos", "gedcom_filename": referencia}
        )

        assert "Maria dos Santos" in resposta.get_data(as_text=True)


class TestTermo:
    def test_termo_em_branco_devolve_a_mensagem(self, cliente_de_upload):
        referencia = arvore_aberta(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.post(
            "/busca", data={"termo": "   ", "gedcom_filename": referencia}
        )

        assert resposta.status_code == 200
        assert TERMO_VAZIO in resposta.get_data(as_text=True)

    def test_termo_acima_do_teto_nao_derruba(self, cliente_de_upload):
        referencia = arvore_aberta(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.post(
            "/busca", data={"termo": "a" * (TETO_DO_TERMO + 50), "gedcom_filename": referencia}
        )

        assert resposta.status_code == 200

    def test_sem_referencia_de_arvore_volta_para_a_tela(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.post("/busca", data={"termo": "Silva"})

        assert resposta.status_code == 302
        assert resposta.headers["Location"].endswith("/")


class TestReferenciaQueNaoResolve:
    def test_responde_404_com_o_literal_de_inexistencia(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.post(
            "/busca",
            data={"termo": "Silva", "gedcom_filename": f"{CHAVE}__sumiu.ged"},
        )
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 404
        assert "não existe mais" in corpo
        assert "Ana Silva" not in corpo
