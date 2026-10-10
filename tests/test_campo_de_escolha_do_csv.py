"""`T021` (`OBS-01` da feature 011): o campo de escolha do CSV na TELA.

## A lacuna que este arquivo fecha, e como ela foi MEDIDA

O `OBS-01` do `regression-watch.md` registrou que a `T021` foi verificada **sem teste de tela**. A
conferência de 2026-10-10 confirmou a lacuna, e com precisão cirúrgica:

- o **contrato da ROTA** está coberto por `tests/test_dna_analysis.py` — três testes que mandam
  `matches_csv_filename` no `data={...}` do cliente de teste;
- **nada** asserta que o campo exista no **template**. A busca que provou isso:
  `name="matches_csv_filename"` não aparecia em teste nenhum.

A consequência é concreta: **se o `<select>` sumisse da tela, os três testes de rota continuariam
verdes.** Eles enviam o campo por conta própria e nunca o leem da tela — então a rota estaria certa e
o operador não teria como escolher relatório nenhum.

## O que a `T021` exige, e o que está preso aqui

> "A aba de DNA ganha o campo de escolha que preenche `matches_csv_filename`, **mantendo o envio de
> arquivo como a outra via de entrada**"

São duas metades, e as duas têm teste: o campo de escolha **existe** e carrega a referência do
relatório; e o envio de arquivo **continua** sendo a outra via. Sem a segunda, "ganha o campo" poderia
ter custado o caminho antigo.
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
CHAVE_ARVORE = "080e7943572d2652"
CHAVE_CSV = "94e2402671702cac"
ARVORE = f"{CHAVE_ARVORE}__arvore.ged"
RELATORIO = f"{CHAVE_CSV}__relatorio.csv"


def _guardar(pasta: str, nome: str, conteudo: bytes) -> None:
    with open(os.path.join(pasta, nome), "wb") as fh:
        fh.write(conteudo)


def _estado_de_arvore_escolhida(cliente, pasta) -> str:
    """O HTML do estado em que os formularios de busca e analise aparecem.

    O campo de escolha do CSV vive AQUI, e nao na tela de entrada: ele pertence ao formulario da
    analise, que so existe depois de uma arvore estar carregada. Escolher a arvore e obrigatorio
    para chegar ao estado — e e por isso que a `T021` so podia ser medida neste estado.
    """
    _guardar(pasta, ARVORE, GEDCOM.encode("utf-8"))
    _guardar(pasta, RELATORIO, b"nome,cm\nMaria,100\n")
    resposta = cliente.post("/", data={"action": "selecionar_arvore",
                                      "gedcom_filename": ARVORE})
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


class TestCampoDeEscolhaDoCsv:
    """`T021`: o campo existe na tela, carrega a referencia, e nao custou o envio de arquivo."""

    def test_a_aba_de_dna_oferece_o_campo_de_escolha(self, cliente_de_upload):
        """A lacuna exata do `OBS-01`: o campo ser ASSERTADO no template, e nao so na rota."""
        _app, cliente, pasta = cliente_de_upload

        corpo = _estado_de_arvore_escolhida(cliente, pasta)

        assert 'name="matches_csv_filename"' in corpo, (
            "a tela nao oferece o campo de escolha do CSV: a rota sabe receber "
            "`matches_csv_filename`, e o operador nao tem como manda-lo"
        )

    def test_o_campo_carrega_a_referencia_do_relatorio_armazenado(self, cliente_de_upload):
        """Um `<select>` vazio nao e escolha. A opcao tem de carregar o nome ARMAZENADO."""
        _app, cliente, pasta = cliente_de_upload

        corpo = _estado_de_arvore_escolhida(cliente, pasta)

        assert f'value="{RELATORIO}"' in corpo, (
            "o campo de escolha nao carrega a referencia do relatorio: escolher nao teria efeito"
        )

    def test_o_envio_de_arquivo_continua_como_a_outra_via(self, cliente_de_upload):
        """A segunda metade da `T021`: ganhar o campo nao pode ter custado o caminho antigo."""
        _app, cliente, pasta = cliente_de_upload

        corpo = _estado_de_arvore_escolhida(cliente, pasta)

        assert 'name="matches_csv"' in corpo, (
            "o envio de arquivo sumiu da tela: a `T021` exige as DUAS vias de entrada"
        )
