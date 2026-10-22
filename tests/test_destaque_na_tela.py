"""A caixa de destaque do bloco 3 na tela (feature 044).

Renderiza a página de resultados de verdade e prende o que o destaque precisa fazer
para não virar veredito:

1. o rótulo muda com a quantidade (uma, duas, três) e diz o critério;
2. cada item traz a distância da média e **onde procurar**;
3. a ressalva traz o tamanho do conjunto e a negativa;
4. a linha destacada é a mesma linha da tabela — a lista continua inteira;
5. a palavra `Probabilidade` continua ausente.

Nenhum dado real do operador entra aqui: os CSVs são sintéticos.
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
    DNA_CSV_FONTE_SUJA,
    DNA_CSV_HIPOTESE_TRES_DESTAQUES,
    DNA_CSV_HIPOTESE_DOIS_DESTAQUES,
    DNA_CSV_MEDIDA_INSUFICIENTE,
    DNA_GED,
)


def _pagina(texto_csv):
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
    finally:
        os.remove(caminho_ged)
        os.remove(caminho_csv)

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


class TestARotuloMudaComAQuantidade:
    def test_uma_hipotese_destacada(self):
        pagina = _pagina(DNA_CSV_MEDIDA_INSUFICIENTE)  # 9 cM
        assert "Hipótese mais próxima da média publicada" in pagina
        assert "Primos de 8º grau" in pagina
        assert "esta é a mais próxima" in pagina

    def test_duas_hipoteses_destacadas(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_DOIS_DESTAQUES)  # 42,6 cM
        assert "Duas relações praticamente empatadas pela distância da média" in pagina
        assert "Primos de 3º grau (1× removido)" in pagina
        assert "Primos de 4º grau" in pagina
        assert "estas são as mais próximas" in pagina

    def test_tres_hipoteses_destacadas(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)  # 154,5 cM
        assert "Três relações praticamente empatadas pela distância da média" in pagina
        assert "Meio-primos de 2º grau" in pagina
        assert "Entre as 9 relações compatíveis" in pagina


class TestODestaqueDizOndeProcurar:
    def test_cada_item_traz_a_distancia_e_o_antepassado(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)
        assert "32,5 cM da média publicada" in pagina
        assert "(122 cM)" in pagina
        assert "onde procurar:" in pagina
        assert "bisavós e trisavós" in pagina

    def test_a_ressalva_aparece(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)
        assert "não é confirmação" in pagina
        assert "o parentesco documental continua vindo do GEDCOM" in pagina

    def test_a_tabela_mostra_a_distancia_de_todas_as_linhas(self):
        """A ordem da lista precisa ser auditável linha a linha, não só no destaque.

        Conta com o espaço à direita porque o rótulo da caixa também diz "distância da
        média": sem o espaço, o teste contava o próprio rótulo.
        """
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)
        assert pagina.count("distância da média ") == 9


class TestAListaContinuaInteira:
    def test_o_destaque_nao_remove_linhas(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)
        assert pagina.count("<tr") >= 9
        assert "Primos de 1º grau (1× removido)" in pagina, (
            "a relação mais distante da média sumiu da tabela"
        )

    def test_as_linhas_destacadas_estao_marcadas(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)
        assert pagina.count("linha-destacada") == 3

    def test_a_caixa_de_destaque_aparece_uma_vez_por_kit(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)
        assert pagina.count("destaque-da-hipotese") == 1

    def test_a_palavra_probabilidade_continua_fora(self):
        pagina = _pagina(DNA_CSV_HIPOTESE_TRES_DESTAQUES)
        assert "Probabilidade" not in pagina

    def test_sem_candidata_nao_ha_caixa(self):
        pagina = _pagina("Name,cM,Kit,Source\nAna Silva Souza,5000,AB1234567,Genera\n")
        assert "destaque-da-hipotese" not in pagina
        assert "Nenhuma relação publicada cobre exatamente este valor." in pagina
