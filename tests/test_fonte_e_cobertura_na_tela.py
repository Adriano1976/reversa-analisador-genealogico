"""Testes de tela da fonte e da cobertura (feature 040).

Renderiza a página de resultados de verdade (Jinja + template do app) sobre a árvore
sintética, e prende quatro coisas:

1. o painel existe com evidência, nasce aberto e fica **fora** da guarda dos cartões;
2. sem cobertura, o painel não aparece (é o que preserva a tela de entrada);
3. a linha `Fonte:` mostra o rótulo canônico e o texto original em etiqueta;
4. a linha da medida traz o estado, os números e a ressalva de escopo.

Nenhum dado real do operador entra aqui: o CSV é sintético.
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
from tests.fixtures.sample_dna import (  # noqa: E402
    DNA_CSV_FONTE_NOME_DE_PROJETO,
    DNA_CSV_FONTE_SUJA,
    DNA_CSV_FONTE_VAZIA,
    DNA_CSV_MEDIDA_PARCIAL,
    DNA_GED,
)

# Um cartão de 200 cM, robusto, com texto de formulário na fonte.
CSV_ROBUSTO = DNA_CSV_FONTE_SUJA
# Dois blocos de 8 cM: total 16 (passa de 15) e maior bloco 8 (não passa) -> parcial.
CSV_PARCIAL = DNA_CSV_MEDIDA_PARCIAL


def _analisar(texto_csv):
    """Roda o núcleo e devolve `(cartões, descartes, cobertura)`."""
    fd, caminho_ged = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_GED)
    fd, caminho_csv = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(texto_csv)
    try:
        arvore = arvore_de(gedcom_parser.carregar_arvore(caminho_ged))
        cobertura: dict = {}
        resultados, descartados, _mensagem = dna_analysis(
            caminho_csv, "Carlos Silva Souza", deps(), arvore, cobertura=cobertura)
        return resultados, descartados, cobertura
    finally:
        os.remove(caminho_ged)
        os.remove(caminho_csv)


def _render(resultados, descartados, cobertura=None):
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        return render_template(
            "index.html",
            dna_results=list(resultados),
            skipped_matches=list(descartados),
            cobertura=cobertura,
            gedcom_filename="arvore.ged",
            root_name_usado="carlos",
            csv_filename_usado="matches.csv",
        )


class TestPainel:
    def test_o_painel_existe_aberto_e_fora_da_guarda_dos_cartoes(self):
        resultados, descartados, cobertura = _analisar(CSV_ROBUSTO)
        pagina = _render(resultados, descartados, cobertura)

        assert "Cobertura do arquivo" in pagina
        assert 'class="card cobertura-do-arquivo' in pagina
        assert 'id="cobertura"' in pagina
        assert "linhas no CSV" in pagina
        assert pagina.index("Cobertura do arquivo") < pagina.index("Resultados das Análises de Conexão")

    def test_sem_cartao_o_painel_ainda_renderiza(self):
        _resultados, descartados, cobertura = _analisar(CSV_ROBUSTO)

        pagina = _render([], descartados, cobertura)

        assert "Cobertura do arquivo" in pagina
        assert "Resultados das Análises de Conexão" not in pagina

    def test_sem_cobertura_o_painel_nao_aparece(self):
        resultados, descartados, _cobertura = _analisar(CSV_ROBUSTO)

        pagina = _render(resultados, descartados, None)

        assert "Cobertura do arquivo" not in pagina
        assert 'id="cobertura"' not in pagina

    def test_o_painel_nao_afirma_parentesco(self):
        resultados, descartados, cobertura = _analisar(CSV_ROBUSTO)
        pagina = _render(resultados, descartados, cobertura)
        trecho = pagina[pagina.index("Cobertura do arquivo"):pagina.index("Resultados das Análises de Conexão")]

        assert "não é ausência de parentesco" in trecho
        assert "Parentesco" not in trecho
        assert "<form" not in trecho


class TestFonteNoCartao:
    def test_texto_de_formulario_vira_nao_declarada_com_etiqueta(self):
        resultados, descartados, cobertura = _analisar(CSV_ROBUSTO)
        pagina = _render(resultados, descartados, cobertura)

        assert "Fonte: não declarada" in pagina
        assert "Outro (insira o nome abaixo)" in pagina
        assert "Fonte: Outro (insira o nome abaixo)" not in pagina

    def test_laboratorio_reconhecido_nao_ganha_etiqueta_redundante(self):
        resultados, descartados, cobertura = _analisar(CSV_PARCIAL)
        pagina = _render(resultados, descartados, cobertura)

        assert "Fonte: Genera" in pagina
        assert '<span class="etiqueta-da-fonte">Genera</span>' not in pagina

    def test_nome_de_projeto_vem_com_a_explicacao_do_que_e(self):
        resultados, descartados, cobertura = _analisar(DNA_CSV_FONTE_NOME_DE_PROJETO)
        pagina = _render(resultados, descartados, cobertura)

        assert "Fonte: não declarada" in pagina
        assert '<span class="etiqueta-da-fonte">Migration - F2 - T</span>' in pagina
        assert "nome de projeto de pesquisa, não de laboratório" in pagina

    def test_celula_vazia_explica_sem_exibir_a_etiqueta_traco(self):
        resultados, descartados, cobertura = _analisar(DNA_CSV_FONTE_VAZIA)
        pagina = _render(resultados, descartados, cobertura)

        assert "Fonte: não declarada" in pagina
        assert "o arquivo não traz uma fonte utilizável nesta coluna" in pagina
        assert '<span class="etiqueta-da-fonte">-</span>' not in pagina


class TestMedidaNoCartao:
    def test_medida_robusta_aparece_com_a_ressalva(self):
        resultados, descartados, cobertura = _analisar(CSV_ROBUSTO)
        pagina = _render(resultados, descartados, cobertura)

        assert "Medida robusta" in pagina
        assert "200 cM" in pagina
        assert "Qualidade da medida, não do parentesco." in pagina

    def test_medida_parcial_nomeia_o_bloco_pequeno(self):
        resultados, descartados, cobertura = _analisar(CSV_PARCIAL)
        pagina = _render(resultados, descartados, cobertura)

        assert "Medida parcial" in pagina
        assert "menor bloco abaixo de 15,0 cM" in pagina
        assert "Qualidade da medida, não do parentesco." in pagina
