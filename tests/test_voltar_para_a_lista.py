"""T040 (feature `011-escolher-arquivo-da-lista`, regra `RN-19`): o caminho de volta.

## O buraco que esta acao fecha, medido

Depois de abrir uma arvore, a tela vira o formulario de busca — e **nao havia como voltar**.
Medido na tela no ar em 2026-10-10: `zero` elementos `<a href>` no estado de arvore escolhida,
nenhum botao de volta, e nenhuma indicacao de QUAL arquivo estava aberto.

A unica saida era recarregar a pagina (F5) ou digitar o endereco. Isso funciona — `GET /`
sempre entrega a tela inicial (`D-04`), e `test_o_get_volta_a_mesma_tela_inicial` abaixo
prende isso —, mas nao e um caminho que a tela OFERECE.

## Por que LINK, e nao um botao com `action`

1. volta por `GET /`, que e o caminho ja verificado e que nao depende de estado;
2. **nao passa pelo despacho de `action`**, entao nao corre o risco de cair no
   `render_template` do fim da rota e descartar o estado — que foi exatamente o defeito medido
   do `selecionar_arvore`, e o motivo de ele ter ganhado um ramo proprio;
3. nao reenvia formulario nenhum, entao nao mexe com o `loading` que o JavaScript liga no
   `submit`.

## O nome da arvore aberta sai sem a chave

`rotulo_do_arquivo` e o filtro que reusa `rotulo_de_referencia`, o mesmo das mensagens: o
operador le o nome que ele deu, nunca os 16 hexadecimais da chave (`D-09`).
"""
from __future__ import annotations

import os
import re
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

GEDCOM = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n0 TRLR\n"
)
CHAVE = "080e7943572d2652"
ARMAZENADO = f"{CHAVE}__Backup-Arvore-Sandro.ged"

TEXTO_DO_LINK = "escolher outra árvore"


def _guardar(pasta: str) -> None:
    with open(os.path.join(pasta, ARMAZENADO), "wb") as fh:
        fh.write(GEDCOM.encode("utf-8"))


def _visivel(corpo: str) -> str:
    """So o texto entre tags: e ali que a chave apareceria se vazasse."""
    return " ".join(re.findall(r">([^<]+)<", corpo))


def _escolher(cliente) -> str:
    """Abre a arvore e devolve o HTML do estado de arvore escolhida."""
    resposta = cliente.post("/", data={
        "action": "selecionar_arvore",
        "gedcom_filename": ARMAZENADO,
    })
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


class TestCaminhoDeVolta:
    """`RN-19`: a tela de busca oferece como voltar, e diz sobre o que vai rodar."""

    def test_a_tela_da_arvore_escolhida_tem_o_caminho_de_volta(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta)

        corpo = _escolher(cliente)

        assert 'href="/"' in corpo, "a tela de busca continua sem link nenhum de volta"
        assert TEXTO_DO_LINK in corpo, "o link de volta nao esta rotulado"

    def test_o_caminho_de_volta_e_um_link_e_nao_uma_acao(self, cliente_de_upload):
        """Se virar `action`, ele passa a depender do despacho da rota — e ja falhou uma vez assim."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta)

        corpo = _escolher(cliente)

        assert re.search(r'<a\s[^>]*href="/"', corpo), "o caminho de volta deixou de ser um link"
        assert 'value="voltar"' not in corpo, (
            "o caminho de volta virou uma `action`: era para ser link, que nao passa pelo "
            "despacho e nao corre o risco de cair no render final"
        )

    def test_a_tela_diz_qual_arvore_esta_aberta(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta)

        corpo = _escolher(cliente)
        visivel = _visivel(corpo)

        assert "Backup Arvore Sandro" in visivel, (
            "a tela de busca nao diz sobre qual arvore a busca vai rodar"
        )
        assert CHAVE not in visivel, (
            "a chave de conteudo apareceu como texto na tela da arvore aberta"
        )

    def test_a_tela_inicial_nao_tem_o_link_de_volta(self, cliente_de_upload):
        """Emparelhado: o link pertence ao estado de arvore escolhida, e nao a tela toda."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta)

        tela_inicial = cliente.get("/").get_data(as_text=True)
        tela_escolhida = _escolher(cliente)

        assert TEXTO_DO_LINK not in tela_inicial, (
            "o link de volta aparece na tela inicial, onde nao ha para onde voltar"
        )
        assert TEXTO_DO_LINK in tela_escolhida, "pre-condicao: ele tem de existir no outro estado"

    def test_o_get_volta_a_mesma_tela_inicial(self, cliente_de_upload):
        """O caminho que o link percorre: `GET /` entrega a tela inicial, sem residuo do estado.

        Esta e a medicao que sustenta a escolha do LINK: voltar por `GET /` nao depende de
        nenhum parametro e nao deixa a arvore escolhida para tras.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta)
        antes = cliente.get("/").get_data(as_text=True)
        _escolher(cliente)

        depois = cliente.get("/").get_data(as_text=True)

        assert depois == antes, (
            "o `GET /` depois de escolher uma arvore nao devolve a tela inicial identica"
        )
        assert TEXTO_DO_LINK not in depois
