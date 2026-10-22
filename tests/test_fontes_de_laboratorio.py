"""Testes do catálogo de fontes (feature 040).

Três camadas:

1. `rotulo` — o que é laboratório, o que é `não declarada` e o que é `outro`, com o texto
   original preservado nos três casos.
2. `escolher` — a escolha dentro do kit (primeira linha COM laboratório, caindo para a
   primeira não vazia) e a detecção de divergência.
3. o payload — `build_genetic_evidence` põe `source` canônico, `source_raw`,
   `source_motivo` e emite `fontes_divergentes`.

Nenhum valor vem do arquivo real do operador: os casos são sintéticos e reproduzem as
formas medidas em 2026-10-22 (`GENERA`, `-`, `Minha herança`, `L1b1a`, …).
"""
from __future__ import annotations

import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from core.fontes_de_laboratorio import (  # noqa: E402
    EMPRESA_NAO_CONFIRMADA,
    HAPLOGRUPO,
    LABORATORIOS,
    NAO_DECLARADA,
    NAO_RECONHECIDA,
    NOME_DE_PROJETO,
    OUTRO,
    SEM_VALOR_UTIL,
    TEXTO_DE_FORMULARIO,
    escolher,
    explicacao,
    rotulo,
)
from core.genetic_evidence import build_genetic_evidence  # noqa: E402


def _evidencias(texto):
    return build_genetic_evidence(pd.read_csv(io.StringIO(texto)))


class TestRotulo:
    @pytest.mark.parametrize("entrada, esperado", [
        ("Genera", "Genera"),
        ("GENERA", "Genera"),
        ("genera", "Genera"),
        ("gENERA", "Genera"),
        ("Genera Brasil", "Genera"),
        ("Outros (Genera)", "Genera"),
        ("GEN", "Genera"),
        ("Meu DNA", "meuDNA"),
        ("MEUDNA", "meuDNA"),
        ("Meudna", "meuDNA"),
        ("MeuDNA-Mandelics", "meuDNA"),
        ("23andMe", "23andMe"),
        ("23andme", "23andMe"),
        ("23eEu", "23andMe"),
        ("MyHeritage", "MyHeritage"),
        ("My Heritage", "MyHeritage"),
        ("my heritage", "MyHeritage"),
        ("FTDNA", "FTDNA"),
        ("ftdna", "FTDNA"),
        ("FamilyTree", "FamilyTreeDNA"),
        ("Ancestry", "Ancestry"),
        ("Living DNA", "Living DNA"),
        ("Genos", "Genos"),
        ("DNA Land", "DNA Land"),
        ("mundodna", "MundoDNA"),
    ])
    def test_alias_vira_laboratorio_canonico(self, entrada, esperado):
        assert rotulo(entrada).canonico == esperado
        assert rotulo(entrada).texto == esperado
        assert rotulo(entrada).motivo is None

    @pytest.mark.parametrize("entrada", [
        "-", "", "   ", "Selecione uma empresa ou fonte",
        "Select a Company or Source", "Outro (insira o nome abaixo)",
        "Other (enter name below)", "Outros",
    ])
    def test_texto_de_formulario_nao_e_laboratorio(self, entrada):
        resultado = rotulo(entrada)

        assert resultado.canonico is None
        assert resultado.texto == NAO_DECLARADA
        assert resultado.motivo == TEXTO_DE_FORMULARIO

    @pytest.mark.parametrize("entrada", [
        "Minha herança", "Minha Herança", "Minha heran", "Meu Patrimônio",
    ])
    def test_empresa_nao_confirmada_nao_e_presumida(self, entrada):
        resultado = rotulo(entrada)

        assert resultado.canonico is None
        assert resultado.texto == NAO_DECLARADA
        assert resultado.motivo == EMPRESA_NAO_CONFIRMADA

    @pytest.mark.parametrize("entrada", ["Migration - F2 - A", "Migration - F2 - T", "Ancestralidade"])
    def test_nome_de_projeto_nao_e_laboratorio(self, entrada):
        assert rotulo(entrada).motivo == NOME_DE_PROJETO

    def test_haplogrupo_na_coluna_errada(self):
        assert rotulo("L1b1a").motivo == HAPLOGRUPO

    def test_valor_desconhecido_vira_outro_e_nao_laboratorio(self):
        resultado = rotulo("Empresa Inventada")

        assert resultado.canonico is None
        assert resultado.texto == OUTRO
        assert resultado.motivo == NAO_RECONHECIDA

    def test_o_texto_original_sobrevive_a_normalizacao(self):
        assert rotulo("Minha Herança").bruto == "Minha Herança"
        assert rotulo("GENERA").bruto == "GENERA"

    def test_o_catalogo_declara_onze_laboratorios(self):
        assert len(LABORATORIOS) == 11


class TestEscolher:
    def test_primeira_linha_vazia_nao_esconde_laboratorio_adiante(self):
        escolhido, divergentes = escolher(["-", "", "Genera"])

        assert escolhido.texto == "Genera"
        assert divergentes == ()

    def test_sem_laboratorio_reconhecido_cai_para_o_primeiro_valor_nao_vazio(self):
        escolhido, divergentes = escolher(["Minha herança", "Empresa Inventada"])

        assert escolhido.texto == NAO_DECLARADA
        assert escolhido.bruto == "Minha herança"
        assert divergentes == ()

    def test_kit_sem_fonte_nenhuma_fica_nao_declarada(self):
        escolhido, divergentes = escolher([])

        assert escolhido.texto == NAO_DECLARADA
        assert escolhido.motivo == TEXTO_DE_FORMULARIO
        assert divergentes == ()

    def test_dois_laboratorios_devolvem_o_segundo_como_divergente(self):
        escolhido, divergentes = escolher(["Genera", "MyHeritage"])

        assert escolhido.texto == "Genera"
        assert divergentes == ("MyHeritage",)

    def test_a_mesma_empresa_em_grafias_diferentes_nao_e_divergencia(self):
        _escolhido, divergentes = escolher(["Genera", "GENERA", "genera"])

        assert divergentes == ()


class TestExplicacao:
    """A frase que o cartão mostra ao lado do texto original (feature 042)."""

    def test_laboratorio_nao_tem_explicacao(self):
        assert explicacao(None) is None

    def test_nome_de_projeto_diz_o_que_e(self):
        frase = explicacao(NOME_DE_PROJETO, "Migration - F2 - T")

        assert "nome de projeto de pesquisa" in frase
        assert "não de laboratório" in frase

    def test_celula_vazia_ou_traco_vira_ausencia_de_valor(self):
        assert explicacao(TEXTO_DE_FORMULARIO, "-") == SEM_VALOR_UTIL
        assert explicacao(TEXTO_DE_FORMULARIO, "") == SEM_VALOR_UTIL
        assert explicacao(TEXTO_DE_FORMULARIO, None) == SEM_VALOR_UTIL

    def test_texto_de_formulario_com_conteudo_explica_a_origem(self):
        frase = explicacao(TEXTO_DE_FORMULARIO, "Selecione uma empresa ou fonte")

        assert "texto de formulário" in frase

    def test_empresa_nao_confirmada_explica_que_o_projeto_nao_presume(self):
        assert "não presume" in explicacao(EMPRESA_NAO_CONFIRMADA, "Minha herança")

    def test_haplogrupo_e_desconhecido_tem_frase_propria(self):
        assert "haplogrupo" in explicacao(HAPLOGRUPO, "L1b1a")
        assert "não reconhecido" in explicacao(NAO_RECONHECIDA, "Empresa Inventada")


class TestPayload:
    def test_a_evidencia_carrega_rotulo_original_e_motivo(self):
        evidencias, _avisos = _evidencias(
            "Name,cM,Source\nAna Silva Souza,200,Outro (insira o nome abaixo)\n")
        kit = next(iter(next(iter(evidencias.values())).values()))

        assert kit["source"] == NAO_DECLARADA
        assert kit["source_raw"] == "Outro (insira o nome abaixo)"
        assert kit["source_motivo"] == TEXTO_DE_FORMULARIO

    def test_laboratorio_fica_sem_motivo(self):
        evidencias, _avisos = _evidencias("Name,cM,Source\nAna Silva Souza,200,GENERA\n")
        kit = next(iter(next(iter(evidencias.values())).values()))

        assert kit["source"] == "Genera"
        assert kit["source_raw"] == "GENERA"
        assert kit["source_motivo"] is None

    def test_csv_sem_coluna_de_fonte_deixa_source_vazio(self):
        evidencias, _avisos = _evidencias("Name,cM\nAna Silva Souza,200\n")
        kit = next(iter(next(iter(evidencias.values())).values()))

        assert kit["source"] is None
        assert kit["source_raw"] is None
        assert kit["source_motivo"] is None

    def test_dois_laboratorios_no_mesmo_kit_geram_aviso_de_cartao(self):
        evidencias, avisos = _evidencias(
            "Name,cM,Kit,Source\n"
            "Ana Silva Souza,100,AB1234567,Genera\n"
            "Ana Silva Souza,100,AB1234567,MyHeritage\n")
        kit = next(iter(next(iter(evidencias.values())).values()))
        codigos = [a["code"] for a in avisos]

        assert kit["source"] == "Genera"
        assert "fontes_divergentes" in codigos
        aviso = next(a for a in avisos if a["code"] == "fontes_divergentes")
        assert aviso["nivel"] == "cartao"
        assert "MyHeritage" in aviso["message"]
