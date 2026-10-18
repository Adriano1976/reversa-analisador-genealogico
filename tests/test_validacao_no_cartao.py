"""Testes de tela do selo de validação.

Renderizam o template REAL com um resultado sintético — sem subir servidor — e olham só o
bloco do cartão. O recorte importa: a legenda do topo da lista contém as duas classes de
propósito, e uma asserção na página inteira passaria mesmo sem o selo no cartão.
"""
from __future__ import annotations

import os
import re
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
    """Só o bloco do cartão: o que vem depois do marcador dele."""
    pagina = _pagina(resultado)
    partes = pagina.split(MARCADOR_DO_CARTAO)
    assert len(partes) == 2, "o cartão não foi renderizado"
    return partes[1]


# ---------------------------------------------------------------------------
# Presença do selo
# ---------------------------------------------------------------------------

def test_cartao_em_conflito_mostra_o_selo():
    cartao = _cartao(fixo.resultado())

    assert "badge validacao-conflito" in cartao
    assert "Linha em conflito" in cartao
    assert "veredito de validação temporal" in cartao


def test_cartao_validado_mostra_o_selo():
    cartao = _cartao(fixo.resultado("VALIDADO"))

    assert "badge validacao-valido" in cartao
    assert "Validado" in cartao


def test_o_title_do_selo_carrega_o_codigo_da_anomalia():
    cartao = _cartao(fixo.resultado())
    trecho = cartao[cartao.index("validacao-conflito"):]
    selo = trecho[:trecho.index(">")]

    assert "title=" in selo
    assert "PROFUNDIDADE_TEMPORAL_INCOMPATIVEL" in selo


# ---------------------------------------------------------------------------
# Ausência
# ---------------------------------------------------------------------------

def test_cartao_inconclusivo_nao_ganha_selo():
    cartao = _cartao(fixo.resultado_inconclusivo())

    assert "validacao-" not in cartao
    assert "Linha em conflito" not in cartao


def test_sem_veredito_nenhum_selo_aparece():
    resultado = fixo.resultado()
    resultado.update({"validacao_status": None, "validacao_rotulo": None,
                      "validacao_classe": None, "validacao_aviso": None})
    cartao = _cartao(resultado)

    assert "validacao-" not in cartao


# ---------------------------------------------------------------------------
# Contrato da classe e dos quatro estados
# ---------------------------------------------------------------------------

def test_a_classe_do_selo_nao_usa_o_prefixo_dos_estados():
    cartao = _cartao(fixo.resultado())
    classes = re.findall(r'class="badge ([^"]*validacao[^"]*)"', cartao)

    assert classes, "o selo não tem classe de validação"
    for classe in classes:
        assert "estado-" not in classe


def test_o_selo_do_confronto_continua_intacto():
    cartao = _cartao(fixo.resultado())

    assert re.search(r'class="badge estado-CONFLITANTE"', cartao)


def test_o_literal_de_maquina_fica_no_title_e_nunca_no_texto():
    cartao = _cartao(fixo.resultado())
    selo = re.search(r'<span class="badge validacao-conflito" title="([^"]*)">([^<]*)<', cartao)

    assert selo, "o selo não foi encontrado no cartão"
    assert "ERRO CRONICO / QUEBRA DE LINHA" in selo.group(1)
    assert "ERRO CRONICO / QUEBRA DE LINHA" not in selo.group(2)
    assert selo.group(2).strip() == "Linha em conflito"


# ---------------------------------------------------------------------------
# Legenda da lista
# ---------------------------------------------------------------------------

def test_a_legenda_declara_o_que_e_ausencia_de_selo():
    pagina = _pagina(fixo.resultado_inconclusivo())

    assert "legenda-da-validacao" in pagina
    assert "sem selo = não concluído" in pagina
