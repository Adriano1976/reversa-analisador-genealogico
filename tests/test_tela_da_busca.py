"""A tela da busca: onde o campo aparece e o que ele mostra (feature 052).

## O que este arquivo prende

- sem arvore aberta o bloco **nao existe** — e a mesma condicao dos campos de nome, e
  e o que mantem `SHA_DA_TELA` valendo;
- com arvore aberta o campo aparece, com rotulo, e aponta para a rota propria `/busca`;
- o termo digitado volta para o campo depois da busca (`RF-09`);
- cada secao declara o proprio total (`RN-07`);
- a secao da arvore e a do relatorio sao identificaveis separadamente (`RN-05`).

As assercoes sao sobre o **HTML entregue**, e nao sobre o contexto do template: e o que
o operador ve.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.busca_arvores import GED_DA_BUSCA  # noqa: E402

CHAVE = "080e7943572d2652"
ARVORE = f"{CHAVE}__arvore.ged"


def _guardar(pasta: str, nome: str, conteudo: str) -> None:
    with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)


def abrir_arvore(cliente_de_upload) -> str:
    _app, cliente, pasta = cliente_de_upload
    _guardar(pasta, ARVORE, GED_DA_BUSCA)
    resposta = cliente.post(
        "/", data={"action": "selecionar_arvore", "gedcom_filename": ARVORE}
    )
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


class TestSemArvore:
    def test_o_bloco_nao_aparece(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.get("/").get_data(as_text=True)

        assert 'id="busca-termo"' not in corpo
        assert "resultado-da-busca" not in corpo


class TestComArvore:
    def test_o_campo_aparece_com_rotulo(self, cliente_de_upload):
        corpo = abrir_arvore(cliente_de_upload)

        assert 'id="busca-termo"' in corpo
        assert "Nome ou sobrenome" in corpo
        assert 'action="/busca"' in corpo

    def test_o_campo_nao_depende_de_script(self, cliente_de_upload):
        """A busca e servida pelo servidor: sem JS, o formulario continua funcionando."""
        corpo = abrir_arvore(cliente_de_upload)

        assert '<form method="POST" action="/busca"' in corpo
        assert 'name="gedcom_filename"' in corpo


class TestResultadoNaTela:
    def test_o_termo_volta_para_o_campo(self, cliente_de_upload):
        abrir_arvore(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.post(
            "/busca", data={"termo": "Silva", "gedcom_filename": ARVORE}
        ).get_data(as_text=True)

        assert 'value="Silva"' in corpo

    def test_a_secao_da_arvore_declara_o_total(self, cliente_de_upload):
        abrir_arvore(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.post(
            "/busca", data={"termo": "Silva", "gedcom_filename": ARVORE}
        ).get_data(as_text=True)

        assert 'id="secao-da-busca-arvore"' in corpo
        assert 'class="contagem-da-secao"' in corpo

    def test_sem_acerto_a_tela_diz_e_preserva_o_termo(self, cliente_de_upload):
        abrir_arvore(cliente_de_upload)
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.post(
            "/busca", data={"termo": "Zzzz", "gedcom_filename": ARVORE}
        ).get_data(as_text=True)

        assert "Nenhum nome encontrado" in corpo
        assert 'value="Zzzz"' in corpo


class TestNenhumFormularioDependeDaUrl:
    def test_todo_formulario_declara_action(self, cliente_de_upload):
        """A tela e servida em `/` e, depois de uma busca, em `/busca`.

        Formulario sem `action` posta na URL CORRENTE. Enquanto a unica URL era `/`,
        isso passava; com `POST /busca` no ar, o formulario da analise de DNA passou a
        cair na rota da busca e a tela respondia "Digite um nome ou sobrenome para
        buscar." — o defeito medido em 2026-10-28. Este teste e o guarda dele: se alguem
        acrescentar um formulario sem `action`, a busca quebra de novo em silencio.
        """
        import re

        corpo = abrir_arvore(cliente_de_upload)

        formularios = re.findall(r"<form[^>]*>", corpo)
        sem_action = [tag for tag in formularios if "action=" not in tag]

        assert formularios, "a tela nao tem formulario nenhum"
        assert sem_action == [], f"formulario sem action posta na URL corrente: {sem_action}"
