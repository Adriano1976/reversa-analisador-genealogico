"""A tabela do bloco 3 na tela (feature 043).

Renderiza a pagina de resultados de verdade sobre a arvore sintetica e prende o que
a tabela trocou de lugar com a lista antiga:

1. os quatro cabecalhos das colunas existem;
2. a primeira linha traz a relacao, a posicao do valor na faixa e o antepassado
   comum — inclusive a frase que diz que o antepassado **nao** vem da fonte;
3. a barra da faixa desenha o percentual da posicao;
4. a lista antiga (`cM na fonte; media ...`) nao voltou;
5. a palavra `Probabilidade` nao aparece: a coluna foi recusada de proposito;
6. valor sem cobertura publicada nao renderiza tabela nenhuma.

Nenhum dado real do operador entra aqui: o CSV e sintetico.
"""
from __future__ import annotations

import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import dna_analysis  # noqa: E402
from parsers import gedcom_parser  # noqa: E402
from tests.fixtures.helpers import arvore_de, deps  # noqa: E402
from tests.fixtures.sample_dna import DNA_CSV_FONTE_SUJA, DNA_GED  # noqa: E402

# 200 cM: a primeira linha e "Primos de 1º grau (duas gerações de diferença)", cuja faixa e 33–471.
CSV_200 = DNA_CSV_FONTE_SUJA
# Acima do maximo publicado (3.720 cM): nenhuma relacao cobre o valor.
CSV_SEM_COBERTURA = "Name,cM,Kit,Source\nAna Silva Souza,5000,AB1234567,Genera\n"


def _analisar(texto_csv):
    fd, caminho_ged = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_GED)
    fd, caminho_csv = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(texto_csv)
    try:
        arvore = arvore_de(gedcom_parser.carregar_arvore(caminho_ged))
        resultados, descartados, _mensagem = dna_analysis(
            caminho_csv, "Carlos Silva Souza", deps(), arvore)
        return resultados, descartados
    finally:
        os.remove(caminho_ged)
        os.remove(caminho_csv)


def _render(resultados, descartados):
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        return render_template(
            "index.html",
            dna_results=list(resultados),
            skipped_matches=list(descartados),
            gedcom_filename="arvore.ged",
            root_name_usado="carlos",
            csv_filename_usado="matches.csv",
        )


def _com_tabela():
    resultados, descartados = _analisar(CSV_200)
    return _render(resultados, descartados)


class TestATabela:
    def test_os_quatro_cabecalhos_estao_na_tela(self):
        pagina = _com_tabela()
        for cabecalho in ("Relação", "Faixa na fonte", "Onde o valor cai",
                          "Antepassado comum mais recente"):
            assert cabecalho in pagina, f"a tabela perdeu a coluna {cabecalho!r}"

    def test_a_primeira_linha_traz_relacao_posicao_e_antepassado(self):
        pagina = _com_tabela()
        assert "Primos de 1º grau (duas gerações de diferença)" in pagina
        assert "avós e trisavós" in pagina, (
            "o antepassado comum de um 1C2R tem dois lados (2 e 4 geracoes), "
            "e os dois precisam aparecer"
        )
        assert "2 e 4 gerações acima" in pagina
        assert "abaixo do centro" in pagina, "a posicao do valor na faixa nao chegou a tela"

    def test_a_barra_desenha_o_percentual_da_posicao(self):
        """33–471 com 200 cM: (200-33)/438 = 38%."""
        pagina = _com_tabela()
        assert "barra-da-faixa" in pagina
        assert 'marca-da-faixa" style="left: 38%' in pagina, (
            "a marca da barra precisa cair na posicao calculada pelo nucleo"
        )

    def test_a_tela_diz_que_o_antepassado_nao_vem_da_fonte(self):
        """A coluna e definicao, e nao estatistica — e o operador precisa saber."""
        pagina = _com_tabela()
        assert "Ordenado da relação mais próxima da média da faixa" in pagina
        assert "vem da fonte" in pagina
        assert "por definição" in pagina

    def test_a_lista_antiga_nao_voltou(self):
        pagina = _com_tabela()
        assert "na fonte; média" not in pagina, (
            "o formato antigo (`(33–471 cM na fonte; média 221 cM)`) reapareceu"
        )

    def test_a_palavra_probabilidade_nao_aparece(self):
        """A coluna `Probabilidade` foi recusada em 2026-10-22.

        Ver `tests/test_mrca_e_posicao_na_faixa.py` para a razao: a fonte nao publica
        probabilidade por relacao, e percentuais somando 100% fechariam o mundo.
        """
        pagina = _com_tabela()
        assert "Probabilidade" not in pagina
        assert "probabilidade de parentesco" not in pagina.lower()

    def test_o_titulo_da_secao_continua_o_mesmo(self):
        pagina = _com_tabela()
        assert "Possibilidades de parentesco pelo DNA" in pagina


class TestSemCoberturaPublicada:
    def test_valor_sem_faixa_nao_renderiza_tabela(self):
        resultados, descartados = _analisar(CSV_SEM_COBERTURA)
        pagina = _render(resultados, descartados)
        assert "tabela-das-hipoteses" not in pagina, (
            "sem relacao publicada nao ha o que tabelar: o cartao cairia numa tabela vazia"
        )
        assert "Nenhuma relação publicada cobre exatamente este valor." in pagina
