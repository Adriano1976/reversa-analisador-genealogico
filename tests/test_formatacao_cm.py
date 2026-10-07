"""Formatacao do total de cM exibido no cartao de resultado.

Reproducao e regressao do BUG-20261004-EWSJ. O defeito nao e de calculo: o valor
somado esta correto, e o que faltava era formatar antes de escrever no HTML. Por
isso os testes cobrem duas frentes:

- o HTML emitido pelo template real nao pode carregar o residuo do ponto flutuante;
- o valor ARMAZENADO em result["cm"] nao pode mudar, porque a paridade contra o
  oraculo congelado exige igualdade exata, sem tolerancia e sem arredondamento
  (_reversa_sdd/migration/parity_specs.md:113).
"""
from __future__ import annotations

import os
import sys
import tempfile
from tests.fixtures.helpers import arvore_de as _arvore_de
from tests.fixtures.helpers import deps as _deps
from tests.fixtures.arvore_atual import atual, guardar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

# O valor exato do defeito: a soma de tres segmentos de 6,4 cM do mesmo match.
VALOR_DO_DEFEITO = 19.200000000000003


def _html_do_badge(cm):
    """HTML do badge, renderizado pelo template REAL, sem subir servidor.

    Passa pelo template de producao, e nao por uma copia da linha: se o filtro
    `cm_br` nao estiver registrado no aplicativo, o proprio Jinja levanta erro
    aqui, o que faz deste teste a cobertura do registro do filtro tambem.
    """
    from flask import render_template

    from app import app

    resultado = {
        "match_name": "Ana Silva Souza",
        "cm": cm,
        "text_path": "Carlos Silva Souza -> Ana Silva Souza",
        "mermaid_data": "graph LR",
    }
    with app.test_request_context("/"):
        return render_template("index.html", dna_results=[resultado])


def _resultados_do_fluxo_real():
    """Roda o fluxo real de analise com tres segmentos de 6,4 cM do mesmo match."""
    from core.dna_analysis import dna_analysis
    from parsers.gedcom_parser import carregar_arvore
    from tests.fixtures.sample_dna import DNA_GED

    fd, ged = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(DNA_GED)
    try:
        guardar(carregar_arvore(ged))
    finally:
        os.remove(ged)

    fd, csv = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("Name,cM\nAna Silva Souza,6.4\nAna Silva Souza,6.4\nAna Silva Souza,6.4\n")
    try:
        resultados, _descartados, _mensagem = dna_analysis(csv, "Carlos Silva Souza", _deps(), atual())
    finally:
        os.remove(csv)
    return resultados


# --- Reproducao: prova que o defeito relatado aparecia -----------------------


def test_badge_nao_exibe_ruido_de_ponto_flutuante():
    """O valor do print do relator nao pode aparecer cru no HTML."""
    html = _html_do_badge(VALOR_DO_DEFEITO)
    assert "19.200000000000003" not in html, (
        "o badge ainda exibe o residuo da soma em ponto flutuante"
    )
    assert "19,2 cM" in html, "o badge nao exibe o valor no formato decidido"


def test_badge_nunca_carrega_cauda_de_ponto_flutuante():
    """Varredura: nenhum total chega ao HTML na representacao crua do float."""
    for cm in (6.4 + 6.4 + 6.4, 0.1 + 0.2, 100 / 3):
        html = _html_do_badge(cm)
        assert repr(cm) not in html, "o badge carrega o valor cru %r" % (cm,)


# --- Regressao: protege o formato decidido e o contrato do valor --------------


def test_cm_com_duas_casas_preserva_as_duas():
    """A correcao nao pode truncar precisao que o dado realmente tem."""
    from utils.number_format import formatar_cm

    assert formatar_cm(19.25) == "19,25"


def test_cm_inteiro_nao_ganha_casa_decimal():
    from utils.number_format import formatar_cm

    assert formatar_cm(20.0) == "20"
    assert formatar_cm(6.4) == "6,4"


def test_formatador_aceita_bordas_numericas():
    """Bordas numericas nao levantam excecao, mesmo que o badge nunca as receba.

    Nome ajustado em relacao ao rascunho aprovado: o rascunho dizia "e_total", e o
    formatador nao e total para entrada nao numerica, por decisao. Ele aceita o que
    `float()` aceita, e levanta `TypeError`/`ValueError` fora disso, em vez de
    inventar um valor.
    """
    from utils.number_format import formatar_cm

    assert formatar_cm(0) == "0"
    assert formatar_cm(-1.5) == "-1,5"


def test_valor_armazenado_permanece_exato():
    """Contrato: formatar e transformar na saida, nunca arredondar o estado."""
    resultados = _resultados_do_fluxo_real()
    assert resultados, "o fluxo real nao produziu resultado"
    assert resultados[0]["cm"] == VALOR_DO_DEFEITO
