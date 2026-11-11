"""Contrato da tabela de segmentos na tela (feature 058).

Roda a analise de verdade com a fixture sintetica de 11 segmentos em 3 cromossomos e
confere a posicao da secao, as colunas, o contador e o par linha<->faixa do ideograma.
"""
from __future__ import annotations

import os
import re

from tests.fixtures.sample_dna import DNA_CSV_SEGMENTOS_DISTRIBUICAO, DNA_GED


def _analisar(cliente, pasta, conteudo=DNA_CSV_SEGMENTOS_DISTRIBUICAO):
    arvore = "080e7943572d2652__arvore.ged"
    relatorio = "94e2402671702cac__matches.csv"
    with open(os.path.join(pasta, arvore), "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_GED)
    with open(os.path.join(pasta, relatorio), "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
    return cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": arvore,
        "matches_csv_filename": relatorio,
        "root_name": "Carlos Silva Souza",
    })


def test_a_tabela_entra_depois_da_distribuicao_e_antes_da_lista(cliente_de_upload):
    _app, cliente, pasta = cliente_de_upload

    html = _analisar(cliente, pasta).get_data(as_text=True)

    assert "Detalhamento dos segmentos compartilhados" in html
    assert (
        html.index("Cada série tem a sua escala")
        < html.index("Detalhamento dos segmentos compartilhados")
        < html.index('<article class="regiao"')
    ), "a tabela saiu da posição fixada entre a distribuição e a lista"


def test_uma_linha_por_segmento_e_o_contador_conta_todas(cliente_de_upload):
    _app, cliente, pasta = cliente_de_upload

    html = _analisar(cliente, pasta).get_data(as_text=True)

    # A fixture tem 11 segmentos: 4 no cromossomo 1, 4 no 7 e 3 no 16.
    assert html.count("<tr data-busca=") == 11
    assert "11 segmentos" in html


def test_as_sete_colunas_estao_no_cabecalho(cliente_de_upload):
    _app, cliente, pasta = cliente_de_upload

    html = _analisar(cliente, pasta).get_data(as_text=True)

    for rotulo in ("Cromossomo", "Posição", "Tamanho", "cM", "Kit", "Nome", "Desfecho"):
        assert f">{rotulo}<" in html, f"a coluna {rotulo!r} sumiu do cabeçalho"


def test_cada_linha_aponta_para_uma_faixa_que_existe(cliente_de_upload):
    _app, cliente, pasta = cliente_de_upload

    html = _analisar(cliente, pasta).get_data(as_text=True)
    destinos = set(re.findall(r'href="#(regiao-\d+)"', html))
    ancoras = set(re.findall(r'id="(regiao-\d+)"', html))

    assert destinos, "nenhuma linha aponta para a faixa do ideograma"
    assert destinos <= ancoras, "há linha apontando para faixa que não existe no HTML"


def test_a_toolbar_tem_busca_e_filtro(cliente_de_upload):
    _app, cliente, pasta = cliente_de_upload

    html = _analisar(cliente, pasta).get_data(as_text=True)

    assert 'id="busca-dos-segmentos"' in html
    assert 'id="filtro-do-cromossomo"' in html
    assert "<option value=\"\">Todos</option>" in html
    # Os tres cromossomos da fixture aparecem no filtro.
    for cromossomo in ("1", "7", "16"):
        assert f'<option value="{cromossomo}">{cromossomo}</option>' in html


def test_sem_regiao_nao_existe_tabela(cliente_de_upload):
    _app, cliente, pasta = cliente_de_upload
    csv_sem_regiao = (
        "Name,cM,Kit,Chromosome,Start,End\n"
        "Ana Silva Souza,45,A111111,7,21000000,39000000\n"
        "Zzz Um,40,B222222,8,21500000,38500000\n"
    )

    html = _analisar(cliente, pasta, csv_sem_regiao).get_data(as_text=True)

    assert "Detalhamento dos segmentos compartilhados" not in html
    assert 'class="segmentos"' not in html
