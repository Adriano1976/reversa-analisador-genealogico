"""Testes das regras de DNA para mitigar endogamia.

Cobrem as tres regras do pedido — filtro rigido de 10 cM, recálculo do total e
sinal de evidência fraca abaixo de 15 cM —, a deteccao de endogamia estrutural
com `nx.all_shortest_paths` e o cruzamento difuso com `difflib` (barras do
GEDCOM limpas, cutoff 0.75).

## Por que os testes de integracao nao exigem mudar `result["cm"]`

O valor bruto e contrato congelado pela paridade (`tests/test_formatacao_cm.py`).
A mitigacao viaja em `result["endogamia"]`, e os testes abaixo verificam os DOIS
numeros: o bruto intacto e o recalculado ao lado. Assim a regra nova nao compra
sua passagem apagando a antiga.
"""
from __future__ import annotations

import os
import sys

import networkx as nx
import pandas as pd
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.endogamia import (  # noqa: E402
    CM_MINIMO_MAIOR_BLOCO,
    CM_MINIMO_SEGMENTO,
    CORTE_DIFLIB,
    MENSAGEM_ENDEROGAMIA,
    MENSAGEM_SEM_LIGACAO,
    DNAAnalyzer,
)
from core.dna_analysis import dna_analysis  # noqa: E402
from core.erros import DnaCsvSemColunas  # noqa: E402
from parsers.csv_ingest import normalizar_cm, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from parsers.segmentos_gedmatch import (  # noqa: E402
    ler_segmentos_gedmatch,
    segmentos_do_dataframe,
)
from tests.fixtures.helpers import deps as _deps  # noqa: E402
from tests.fixtures.sample_dna import DNA_GED  # noqa: E402


# ---------------------------------------------------------------------------
# Grafo sintetico: duas familias ligando as mesmas duas pessoas. Modela o
# colapso de pedigree (primos que se casam) sem depender de GEDCOM real.
# ---------------------------------------------------------------------------


def _grafo_com_dois_caminhos() -> nx.Graph:
    grafo = nx.Graph()
    for no, tipo in (("raiz", "person"), ("match", "person"),
                     ("F1", "family"), ("F2", "family")):
        grafo.add_node(no, type=tipo)
    grafo.add_edges_from([("raiz", "F1"), ("F1", "match"),
                          ("raiz", "F2"), ("F2", "match")])
    return grafo


def _grafo_com_um_caminho() -> nx.Graph:
    grafo = nx.Graph()
    grafo.add_node("raiz", type="person")
    grafo.add_node("match", type="person")
    grafo.add_node("F1", type="family")
    grafo.add_edges_from([("raiz", "F1"), ("F1", "match")])
    return grafo


# ---------------------------------------------------------------------------
# Regras 1 e 2 — filtro e recálculo
# ---------------------------------------------------------------------------


class TestFiltroDeSegmentos:
    """`CM_MINIMO_SEGMENTO` e `CM_MINIMO_MAIOR_BLOCO` sao regra, nao sugestao."""

    def test_descarta_abaixo_de_10_e_recalcula_o_total(self):
        evidencia = DNAAnalyzer().avaliar_segmentos([6.4, 6.4, 6.4, 20.0])

        assert evidencia.segmentos_descartados == 3
        assert evidencia.segmentos_mantidos == 1
        assert evidencia.total_cm == pytest.approx(20.0), (
            "o total tem de sair so dos segmentos que sobreviveram"
        )
        assert evidencia.cm_bruto == pytest.approx(39.2)
        assert evidencia.cm_descartado == pytest.approx(19.2)
        assert evidencia.maior_segmento_cm == pytest.approx(20.0)
        assert evidencia.evidencia_fraca is False

    def test_exatamente_10_cm_sobrevive(self):
        """O limiar e `< 10`, e nao `<= 10`: 10 cM entra na conta."""
        evidencia = DNAAnalyzer().avaliar_segmentos([10.0])
        assert evidencia.segmentos_descartados == 0
        assert evidencia.total_cm == pytest.approx(10.0)

    def test_maior_bloco_abaixo_de_15_vira_evidencia_fraca(self):
        evidencia = DNAAnalyzer().avaliar_segmentos([12.5, 11.0])

        assert evidencia.maior_segmento_cm == pytest.approx(12.5)
        assert evidencia.evidencia_fraca is True
        assert "evidência fraca" in evidencia.mensagem
        assert "parentesco distante inflado" in evidencia.mensagem
        assert "15" in evidencia.mensagem, "o limiar citado tem de ser o real"

    def test_maior_bloco_de_15_ou_mais_nao_e_fraco(self):
        evidencia = DNAAnalyzer().avaliar_segmentos([15.0])
        assert evidencia.evidencia_fraca is False
        assert "evidência fraca" not in evidencia.mensagem

    def test_todos_descartados_nao_inventa_base_genetica(self):
        evidencia = DNAAnalyzer().avaliar_segmentos([6.4, 6.4, 6.4])

        assert evidencia.total_cm == 0.0
        assert evidencia.maior_segmento_cm is None
        assert evidencia.evidencia_fraca is True
        assert "evidência fraca" in evidencia.mensagem
        assert "parentesco distante inflado" in evidencia.mensagem

    def test_segmento_sem_valor_nao_vira_zero(self):
        """`None`/texto invalido e ausencia de dado, e nao um segmento de 0 cM."""
        evidencia = DNAAnalyzer().avaliar_segmentos(
            [{"cm": 20.0}, {"cm": None}, {"cm": "n/d"}, {"cm": 5.0}]
        )

        assert evidencia.segmentos_sem_valor == 2
        assert evidencia.segmentos_descartados == 1
        assert evidencia.segmentos_mantidos == 1
        assert evidencia.total_cm == pytest.approx(20.0)
        assert "sem cM numérico" in evidencia.mensagem

    def test_aceita_as_formas_de_entrada_do_fluxo(self):
        """O dict de `genetic_evidence` e um numero solto chegam ao mesmo total."""
        analisador = DNAAnalyzer()
        por_dict = analisador.avaliar_segmentos([{"cm": 20.0}, {"cm": 30.0}])
        por_numero = analisador.avaliar_segmentos([20.0, 30.0])
        assert por_dict.total_cm == por_numero.total_cm == pytest.approx(50.0)

    def test_sem_ruido_a_mensagem_e_vazia(self):
        """Cartao limpo nao ganha aviso: repetir "nada aconteceu" seria ruido."""
        assert DNAAnalyzer().avaliar_segmentos([20.0, 30.0]).mensagem == ""

    def test_limiares_sao_configuraveis(self):
        analisador = DNAAnalyzer(cm_minimo_segmento=5.0, cm_minimo_maior_bloco=40.0)
        evidencia = analisador.avaliar_segmentos([6.0])
        assert evidencia.segmentos_descartados == 0
        assert evidencia.evidencia_fraca is True

    def test_limiares_invalidos_sao_recusados(self):
        with pytest.raises(ValueError):
            DNAAnalyzer(cm_minimo_segmento=-1)
        with pytest.raises(ValueError):
            DNAAnalyzer(corte_difflib=1.5)
        with pytest.raises(ValueError):
            DNAAnalyzer(limite_de_caminhos=1)

    def test_constantes_publicas_sao_as_do_pedido(self):
        assert CM_MINIMO_SEGMENTO == 10.0
        assert CM_MINIMO_MAIOR_BLOCO == 15.0
        assert CORTE_DIFLIB == 0.75


# ---------------------------------------------------------------------------
# Regra 3 — endogamia estrutural no grafo
# ---------------------------------------------------------------------------


class TestEndogamiaEstrutural:

    def test_dois_caminhos_mais_curtos_confirmam_endogamia(self):
        diagnostico = DNAAnalyzer().diagnosticar_endogamia(
            _grafo_com_dois_caminhos(), "raiz", "match")

        assert diagnostico.endogamia_estrutural is True
        assert diagnostico.quantidade_de_caminhos == 2
        assert diagnostico.mensagem == MENSAGEM_ENDEROGAMIA, (
            "a frase do diagnostico e contrato de texto"
        )

    def test_um_caminho_nao_confirma_endogamia(self):
        diagnostico = DNAAnalyzer().diagnosticar_endogamia(
            _grafo_com_um_caminho(), "raiz", "match")
        assert diagnostico.endogamia_estrutural is False
        assert diagnostico.quantidade_de_caminhos == 1
        assert diagnostico.mensagem != MENSAGEM_ENDEROGAMIA

    def test_sem_caminho_nao_levanta_networkx_no_path(self):
        """O match sem ligacao documental e caso previsto, e nao excecao."""
        grafo = _grafo_com_um_caminho()
        grafo.add_node("sozinho", type="person")

        diagnostico = DNAAnalyzer().diagnosticar_endogamia(grafo, "raiz", "sozinho")

        assert diagnostico.caminhos == ()
        assert diagnostico.endogamia_estrutural is False
        assert diagnostico.mensagem == MENSAGEM_SEM_LIGACAO

    def test_no_inexistente_nao_levanta(self):
        diagnostico = DNAAnalyzer().diagnosticar_endogamia(
            _grafo_com_um_caminho(), "raiz", "nao-existe")
        assert diagnostico.caminhos == ()

    def test_grafo_direcionado_e_convertido_para_nao_direcionado(self):
        """A travessia colateral exige subir por um ramo e descer pelo outro."""
        direcionado = nx.DiGraph()
        direcionado.add_edges_from([("raiz", "F1"), ("match", "F1")])

        # No grafo direcionado nao ha caminho raiz -> match; no nao-direcionado ha.
        assert not nx.has_path(direcionado, "raiz", "match")
        diagnostico = DNAAnalyzer().diagnosticar_endogamia(direcionado, "raiz", "match")
        assert diagnostico.quantidade_de_caminhos == 1

    def test_mrca_informado_pelo_documental_vence(self):
        diagnostico = DNAAnalyzer().diagnosticar_endogamia(
            _grafo_com_dois_caminhos(), "raiz", "match", mrca_id="F1")
        assert diagnostico.mrca_ids == ("F1",)

    def test_sem_mrca_informado_a_intersecao_dos_caminhos_e_usada(self):
        diagnostico = DNAAnalyzer().diagnosticar_endogamia(
            _grafo_com_dois_caminhos(), "raiz", "match")
        # A interseccao dos dois caminhos tem so as pontas, que sao removidas.
        assert diagnostico.mrca_ids == ()

    def test_enumeracao_para_no_limite_e_marca_truncado(self):
        grafo = nx.Graph()
        grafo.add_node("raiz", type="person")
        grafo.add_node("match", type="person")
        for numero in range(12):
            familia = f"F{numero}"
            grafo.add_node(familia, type="family")
            grafo.add_edges_from([("raiz", familia), (familia, "match")])

        analisador = DNAAnalyzer(limite_de_caminhos=8)
        diagnostico = analisador.diagnosticar_endogamia(grafo, "raiz", "match")

        assert diagnostico.quantidade_de_caminhos == 8
        assert diagnostico.truncado is True


# ---------------------------------------------------------------------------
# Cruzamento difuso de nomes
# ---------------------------------------------------------------------------


class TestCruzamentoDifuso:

    PESSOAS = {
        "@I1@": "Adriano /Santos/",
        "@I2@": "Adriano Santos",
        "@I3@": "Joana /Silva/",
    }

    def test_barras_do_gedcom_sao_limpas(self):
        assert DNAAnalyzer.limpar_nome_gedcom("Adriano /Santos/") == "Adriano Santos"
        assert DNAAnalyzer.limpar_nome_gedcom("  Adriano   /Santos/ ") == "Adriano Santos"
        assert DNAAnalyzer.limpar_nome_gedcom(None) == ""

    def test_encontra_todos_os_homonimos_da_grafia(self):
        correspondencias = DNAAnalyzer().casar_nome("adriano santos", self.PESSOAS)
        ids = {item.id for item in correspondencias}
        assert ids == {"@I1@", "@I2@"}, (
            "a resolucao nao pode escolher um homonimo em silencio"
        )
        assert all(item.similaridade == pytest.approx(1.0) for item in correspondencias)

    def test_cutoff_075_aceita_erro_pequeno_e_recusa_nome_distante(self):
        analisador = DNAAnalyzer()
        assert analisador.casar_nome("Adriano Santtos", self.PESSOAS), (
            "um erro de digitacao dentro do cutoff tem de ser encontrado"
        )
        assert analisador.casar_nome("Zzz Ninguem", self.PESSOAS) == ()

    def test_indice_preserva_o_nome_limpo(self):
        indice = DNAAnalyzer().indice_de_nomes(self.PESSOAS)
        assert ("@I1@", "Adriano Santos") in indice["adriano santos"]

    def test_analisar_sem_match_id_resolve_pelo_difflib(self):
        analise = DNAAnalyzer().analisar(
            nome_csv="Adriano Santos",
            nomes_por_id=self.PESSOAS,
            segmentos=[20.0],
            grafo=None,
            origem_id="@I9@",
        )
        assert analise.match_id in {"@I1@", "@I2@"}
        assert analise.correspondencias
        assert analise.diagnostico is None, (
            "sem grafo entregue nao ha diagnostico de caminho a afirmar"
        )

    def test_analisar_com_match_id_nao_roda_difflib(self):
        analise = DNAAnalyzer().analisar(
            nome_csv="nome que nao existe",
            nomes_por_id=self.PESSOAS,
            segmentos=[20.0],
            grafo=None,
            origem_id="@I9@",
            match_id="@I3@",
        )
        assert analise.match_id == "@I3@"
        assert analise.correspondencias == ()


# ---------------------------------------------------------------------------
# Adapter: leitura e normalizacao numerica
# ---------------------------------------------------------------------------


CSV_COM_TIPOS = (
    "Name,cM,Kit number\n"
    "Ana Silva Souza,12.5,A1111111\n"
    "Ana Silva Souza,n/d,A1111111\n"
    "Ana Silva Souza,,A1111111\n"
    'Ana Silva Souza,"7,5",A1111111\n'
)


class TestNormalizacaoDoCsv:

    def _ler(self, tmp_path, texto=CSV_COM_TIPOS):
        caminho = tmp_path / "segmentos.csv"
        caminho.write_text(texto, encoding="utf-8")
        return read_csv_with_fallback(str(caminho))

    def test_to_numeric_coerce_strings_e_nulos(self, tmp_path):
        df = self._ler(tmp_path)
        assert df["cM"].dtype == "float64"
        assert df.loc[0, "cM"] == pytest.approx(12.5)
        assert pd.isna(df.loc[1, "cM"]), "texto invalido tem de virar NaN, e nao 0"
        assert pd.isna(df.loc[2, "cM"]), "celula vazia tem de virar NaN"
        assert df.loc[3, "cM"] == pytest.approx(7.5), (
            "virgula decimal de planilha regional tem de ser lida"
        )
        assert df.attrs["cm_nao_numericos"] == 2

    def test_normalizar_cm_e_idempotente(self, tmp_path):
        df = self._ler(tmp_path)
        antes = df["cM"].fillna(-1).tolist()
        normalizar_cm(df)
        assert df["cM"].fillna(-1).tolist() == antes

    def test_sem_coluna_de_cm_nao_levanta(self):
        df = pd.DataFrame({"X": [1], "Y": [2]})
        assert normalizar_cm(df) is df


class TestAdapterDeSegmentos:

    def _csv(self, tmp_path, texto=CSV_COM_TIPOS):
        caminho = tmp_path / "segmentos.csv"
        caminho.write_text(texto, encoding="utf-8")
        return str(caminho)

    def test_segmentos_saem_tipados_e_sem_as_linhas_invalidas(self, tmp_path):
        leitura = ler_segmentos_gedmatch(self._csv(tmp_path))

        assert [segmento.centimorgans for segmento in leitura.segmentos] == [12.5, 7.5]
        assert leitura.linhas == 4
        assert leitura.linhas_sem_cm == (2, 3)
        assert leitura.segmentos[0].pessoa == "Ana Silva Souza"
        assert leitura.segmentos[0].kit == "A1111111"
        assert any("sem cM numérico" in aviso for aviso in leitura.avisos)

    def test_csv_sem_colunas_levanta_erro_de_dominio(self):
        with pytest.raises(DnaCsvSemColunas):
            segmentos_do_dataframe(pd.DataFrame({"X": [1], "Y": [2]}))

    def test_leitura_sem_segmento_avisa(self, tmp_path):
        leitura = ler_segmentos_gedmatch(
            self._csv(tmp_path, "Name,cM\nAna Silva Souza,n/d\n"))
        assert leitura.segmentos == ()
        assert any("Nenhum segmento" in aviso for aviso in leitura.avisos)

    def test_os_segmentos_do_adapter_alimentam_o_analisador(self, tmp_path):
        """A fronteira parser -> core e o ponto do modulo: o dado tem de fluir.

        `SegmentoDeGedmatch` nao e `Mapping`; a leitura pelo atributo
        `centimorgans` e o que impede o adapter de virar codigo decorativo.
        """
        leitura = ler_segmentos_gedmatch(self._csv(tmp_path))
        evidencia = DNAAnalyzer().avaliar_segmentos(leitura.segmentos)

        assert evidencia.total_cm == pytest.approx(12.5)
        assert evidencia.segmentos_descartados == 1
        assert evidencia.segmentos_sem_valor == 0
        assert evidencia.segmentos_mantidos == 1


# ---------------------------------------------------------------------------
# Integracao com o fluxo real
# ---------------------------------------------------------------------------


GED_COM_COLAPSO = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Carlos /Silva/ Souza
1 SEX M
1 FAMC @F1@
1 FAMC @F2@
0 @I2@ INDI
1 NAME Ana /Silva/ Souza
1 SEX F
1 FAMC @F1@
1 FAMC @F2@
0 @I3@ INDI
1 NAME Joaquim /Silva/
1 SEX M
0 @I4@ INDI
1 NAME Marta /Souza/
1 SEX F
0 @I5@ INDI
1 NAME Pedro /Silva/
1 SEX M
0 @I6@ INDI
1 NAME Rita /Souza/
1 SEX F
0 @F1@ FAM
1 HUSB @I3@
1 WIFE @I4@
1 CHIL @I1@
1 CHIL @I2@
0 @F2@ FAM
1 HUSB @I5@
1 WIFE @I6@
1 CHIL @I1@
1 CHIL @I2@
0 TRLR
"""


def _arvore_de(texto: str, tmp_path):
    caminho = tmp_path / "arvore.ged"
    caminho.write_text(texto, encoding="utf-8")
    return carregar_arvore(str(caminho))


def _analisar(tmp_path, gedcom: str, csv: str, raiz: str):
    arvore = _arvore_de(gedcom, tmp_path)
    caminho = tmp_path / "matches.csv"
    caminho.write_text(csv, encoding="utf-8")
    return dna_analysis(str(caminho), raiz, _deps(), arvore)


class TestIntegracaoNoFluxo:

    def test_total_bruto_continua_e_o_mitigado_viaja_ao_lado(self, tmp_path):
        resultados, _descartados, _msg = _analisar(
            tmp_path, DNA_GED,
            "Name,cM\nAna Silva Souza,6.4\nAna Silva Souza,6.4\nAna Silva Souza,6.4\n",
            "Carlos Silva Souza")

        cartao = resultados[0]
        assert cartao["cm"] == pytest.approx(19.2), (
            "o valor bruto e contrato de paridade e nao pode ser reescrito"
        )
        assert cartao["endogamia"]["cm_bruto"] == pytest.approx(19.2)
        assert cartao["endogamia"]["total_cm"] == 0.0
        assert cartao["endogamia"]["segmentos_descartados"] == 3
        assert cartao["endogamia"]["evidencia_fraca"] is True
        assert any("evidência fraca" in observacao
                   for observacao in cartao["observations"])

    def test_filtro_mantem_o_segmento_bom_e_recalcula(self, tmp_path):
        resultados, _descartados, _msg = _analisar(
            tmp_path, DNA_GED,
            "Name,cM\nAna Silva Souza,20\nAna Silva Souza,5\n",
            "Carlos Silva Souza")

        cartao = resultados[0]
        assert cartao["cm"] == pytest.approx(25.0)
        assert cartao["endogamia"]["total_cm"] == pytest.approx(20.0)
        assert cartao["endogamia"]["maior_segmento_cm"] == pytest.approx(20.0)
        assert cartao["endogamia"]["segmentos_descartados"] == 1
        assert cartao["endogamia"]["evidencia_fraca"] is False
        assert any("Total recalculado" in observacao
                   for observacao in cartao["observations"])

    def test_colapso_de_pedigree_aponta_endogamia_estrutural(self, tmp_path):
        resultados, _descartados, _msg = _analisar(
            tmp_path, GED_COM_COLAPSO, "Name,cM\nAna Silva Souza,120\n",
            "Carlos Silva Souza")

        cartao = resultados[0]
        assert cartao["endogamia"]["arvore"]["quantidade_de_caminhos"] == 2
        assert cartao["endogamia"]["arvore"]["endogamia_estrutural"] is True
        assert any(MENSAGEM_ENDEROGAMIA in observacao
                   for observacao in cartao["observations"]), (
            "a frase exata do diagnostico precisa chegar ao cartao"
        )

    def test_match_sem_ligacao_nao_derruba_a_analise(self, tmp_path):
        resultados, _descartados, _msg = _analisar(
            tmp_path, DNA_GED, "Name,cM\nLone Ranger,120\n", "Carlos Silva Souza")

        cartao = resultados[0]
        assert cartao["endogamia"]["arvore"]["quantidade_de_caminhos"] == 0
        assert cartao["endogamia"]["arvore"]["endogamia_estrutural"] is False
        assert not any(MENSAGEM_ENDEROGAMIA in observacao
                       for observacao in cartao["observations"])
