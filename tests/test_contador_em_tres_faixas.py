"""Testes da contagem em três faixas (feature 033).

A frase do topo da lista dizia "N com caminho no GEDCOM e M apenas com evidência
genética". Ela chamava de "sem caminho" o que a árvore tem: quando a janela de vida é
impossível, o parentesco apresentado vira "não encontrado" (adendo 016), mas o caminho
continua em `documentary_do_registro`.

Estes testes olham a FRASE, não o cartão: o que se mede aqui é a conta que o operador lê
antes de decidir o que abrir.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures import resultado_para_cartao as fixo  # noqa: E402

ABERTURA = 'class="text-center text-muted contagem-das-conexoes"'


def _frase(resultados) -> str:
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        pagina = render_template("index.html", dna_results=list(resultados))
    inicio = pagina.index(ABERTURA)
    return pagina[inicio:pagina.index("</p>", inicio)]


# ---------------------------------------------------------------------------
# As três faixas fecham a conta
# ---------------------------------------------------------------------------

def test_as_tres_faixas_somam_o_total():
    frase = _frase([
        fixo.resultado(),
        fixo.resultado(),
        fixo.resultado_recusado_pela_idade(),
        fixo.resultado_sem_caminho(),
    ])

    assert "4 conexões analisadas" in frase
    assert "<strong>2</strong> com caminho genealógico no GEDCOM" in frase
    assert "<strong>1</strong> com caminho documental recusado pela idade do match" in frase
    assert "<strong>1</strong> apenas com evidência genética" in frase


def test_o_recusado_nao_e_contado_como_caminho():
    frase = _frase([fixo.resultado_recusado_pela_idade()])

    assert "<strong>0</strong> com caminho genealógico" in frase
    assert "<strong>1</strong> com caminho documental recusado" in frase


def test_sem_recusados_a_faixa_nao_aparece():
    frase = _frase([fixo.resultado(), fixo.resultado_sem_caminho()])

    assert "recusado" not in frase
    assert "<strong>1</strong> com caminho genealógico" in frase
    assert "<strong>1</strong> apenas com evidência genética" in frase


def test_o_total_continua_sendo_o_numero_de_cartoes():
    frase = _frase([fixo.resultado_sem_caminho() for _ in range(5)])

    assert "5 conexões analisadas" in frase
    assert "<strong>0</strong> com caminho" in frase
    assert "<strong>5</strong> apenas com evidência genética" in frase


# ---------------------------------------------------------------------------
# A árvore sugerida é atributo, não faixa
# ---------------------------------------------------------------------------

def test_a_sugestao_sai_em_frase_propria_e_nao_infla_o_caminho():
    frase = _frase([fixo.resultado_com_sugestao(3), fixo.resultado_sem_caminho()])

    assert "<strong>1</strong> com caminho genealógico" in frase
    assert "<strong>1</strong> conexão mostra" in frase


def test_a_frase_da_sugestao_diz_que_as_geracoes_nao_estao_no_gedcom():
    frase = _frase([fixo.resultado_com_sugestao()])

    assert "árvore sugerida" in frase
    assert "não estão no GEDCOM" in frase


def test_plural_da_sugestao_no_plural():
    frase = _frase([fixo.resultado_com_sugestao(), fixo.resultado_com_sugestao()])

    assert "<strong>2</strong> conexões mostram" in frase


def test_sugestao_sem_desenho_nao_e_contada():
    """`sugestao_geracoes` sozinho contaria cartão cujo bloco não aparece na página."""
    sem_desenho = fixo.resultado_com_sugestao()
    sem_desenho["sugestao_mermaid"] = None

    frase = _frase([sem_desenho])

    assert "árvore sugerida" not in frase


def test_sem_sugestao_nenhuma_a_frase_nao_aparece():
    frase = _frase([fixo.resultado(), fixo.resultado_sem_caminho()])

    assert "árvore sugerida" not in frase


# ---------------------------------------------------------------------------
# O cartão recusado continua dizendo "não encontrado"
# ---------------------------------------------------------------------------

def test_o_cartao_recusado_nao_muda_de_texto():
    """A contagem conta o que a árvore tem; o cartão continua com a regra do adendo 016."""
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        pagina = render_template("index.html", dna_results=[fixo.resultado_recusado_pela_idade()])

    cartao = pagina.split('<details class="card cartao-do-resultado"')[1]
    assert "Parentesco documental não encontrado" in cartao
