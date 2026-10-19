"""Testes de tela do bloco da árvore sugerida.

Renderizam o template real com um resultado sintético e olham o bloco do cartão — o
recorte importa, porque a legenda da lista também tem `.mermaid` em outros lugares.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures import resultado_para_cartao as fixo  # noqa: E402

MARCADOR_DO_CARTAO = '<details class="card cartao-do-resultado"'


def _pagina(resultado) -> str:
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        return render_template("index.html", dna_results=[resultado])


def _cartao(resultado) -> str:
    pagina = _pagina(resultado)
    partes = pagina.split(MARCADOR_DO_CARTAO)
    assert len(partes) == 2, "o cartão não foi renderizado"
    return partes[1]


# ---------------------------------------------------------------------------
# Com sugestão
# ---------------------------------------------------------------------------

def test_cartao_com_sugestao_mostra_o_bloco():
    cartao = _cartao(fixo.resultado_com_sugestao(3))

    assert 'class="arvore-sugerida"' in cartao
    assert "3 gerações sugeridas" in cartao
    assert 'class="mermaid"' in cartao


def test_o_resumo_fica_no_titulo_do_bloco():
    cartao = _cartao(fixo.resultado_com_sugestao(2))
    inicio = cartao.index('class="arvore-sugerida"')
    trecho = cartao[inicio:]
    resumo = trecho[:trecho.index("</summary>")]

    assert "2 gerações sugeridas" in resumo
    assert not resumo.count('class="mermaid"')


def test_o_bloco_vem_depois_do_diagrama_documentado():
    cartao = _cartao(fixo.resultado_com_sugestao())

    assert "grafo-do-registro" in cartao
    assert cartao.index("grafo-do-registro") < cartao.index("arvore-sugerida")


def test_o_diagrama_documentado_continua_igual():
    cartao = _cartao(fixo.resultado_com_sugestao())

    assert "Caminho genealógico no GEDCOM" in cartao
    assert "graph LR" in cartao


# ---------------------------------------------------------------------------
# Sem sugestão
# ---------------------------------------------------------------------------

def test_conflito_sem_geracoes_mostra_a_frase_e_nao_o_bloco():
    cartao = _cartao(fixo.resultado_sem_geracoes_em_conflito())

    assert "sem-sugestao" in cartao
    assert "as duas medidas concordam" in cartao
    assert "arvore-sugerida" not in cartao


def test_cartao_validado_nao_mostra_nem_bloco_nem_frase():
    cartao = _cartao(fixo.resultado("VALIDADO"))

    assert "arvore-sugerida" not in cartao
    assert "sem-sugestao" not in cartao
