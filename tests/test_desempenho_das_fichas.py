"""Desempenho das fichas: uma varredura de familias por arvore, nao por ficha.

BUG-20261021-7O7V. O contador de varreduras existe porque tempo nao serve como
assercao (mesmo criterio de tests/test_carga_da_arvore.py): o que se prende e a
QUANTIDADE de trabalho, nao o relogio.

Antes da correcao, os dois primeiros testes FALHAM: `person_summary` varre as
familias uma vez por ficha, e o dossie monta as mesmas fichas duas vezes. Os dois
ultimos passam hoje e depois, e sao a rede de paridade.
"""
from __future__ import annotations

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core import documentary_relationship as dr  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

CABECALHO = (
    "0 HEAD\n1 SOUR teste-desempenho-fichas\n1 GEDC\n2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n"
)

NUCLEO = (
    "0 @I1@ INDI\n1 NAME Joao /Silva Souza/\n1 SEX M\n1 FAMS @F1@\n1 FAMS @F2@\n"
    "0 @I2@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n1 FAMS @F1@\n"
    "0 @I3@ INDI\n1 NAME Ana /Lima/\n1 SEX F\n1 FAMS @F2@\n"
    "0 @I4@ INDI\n1 NAME Filho /Silva/\n1 SEX M\n1 FAMC @F1@\n"
    "0 @I5@ INDI\n1 NAME Filha /Silva/\n1 SEX F\n1 FAMC @F1@\n"
    "0 @I6@ INDI\n1 NAME Outro /Silva/\n1 SEX M\n1 FAMC @F2@\n"
    "0 @I7@ INDI\n1 NAME Sem /Fams/\n1 SEX M\n"
    "0 @I8@ INDI\n1 NAME Crianca /Fams/\n1 SEX U\n1 FAMC @F3@\n"
    "0 @I9@ INDI\n1 NAME Joao /Silva/\n1 SEX M\n1 BIRT\n2 DATE 1900\n"
    "0 @I10@ INDI\n1 NAME Joao /Silva/\n1 SEX M\n1 BIRT\n2 DATE 1950\n"
    "0 @F1@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n1 CHIL @I4@\n1 CHIL @I5@\n"
    "0 @F2@ FAM\n1 HUSB @I1@\n1 WIFE @I3@\n1 CHIL @I6@\n1 CHIL @I6@\n"
    "0 @F3@ FAM\n1 HUSB @I7@\n1 CHIL @I8@\n"
)


def _gedcom() -> str:
    partes = [CABECALHO, NUCLEO]
    for k in range(50):
        partes.append(f"0 @I{100 + k}@ INDI\n1 NAME Pessoa{k} /Teste/\n1 SEX U\n")
    partes.append("0 TRLR\n")
    return "".join(partes)


class FamiliasContadoras(dict):
    """Dicionario de familias que conta quantas vezes alguem pediu `.values()`."""

    def __init__(self, base):
        super().__init__(base)
        self.leituras = 0

    def values(self):
        self.leituras += 1
        return super().values()


def _limpar(arvore):
    limpar = getattr(dr, "limpar_indice_de_filhos", None)
    if limpar is not None:
        limpar(arvore)


def _get_children_referencia(arvore, person_id):
    """A varredura de hoje, copiada como oraculo de paridade."""
    filhos = []
    people, families = arvore[0], arvore[1]
    for fam in families.values():
        husb = next((dr.ref_id(r.value) for r in fam.sub_records if r.tag == "HUSB"), None)
        wife = next((dr.ref_id(r.value) for r in fam.sub_records if r.tag == "WIFE"), None)
        if person_id in (husb, wife):
            for rec in fam.sub_records:
                if rec.tag == "CHIL":
                    cid = dr.ref_id(rec.value)
                    if cid not in filhos:
                        filhos.append(cid)
    return filhos


@pytest.fixture()
def arvore(tmp_path):
    caminho = tmp_path / "fichas.ged"
    caminho.write_text(_gedcom(), encoding="utf-8")
    arvore = carregar_arvore(str(caminho))
    yield arvore
    _limpar(arvore)


def test_person_summary_nao_varre_as_familias_por_ficha(arvore):
    contador = FamiliasContadoras(arvore[1])
    arvore_contada = (arvore[0], contador, arvore[2], arvore[3])
    _limpar(arvore_contada)

    for pid in list(arvore_contada[0])[:50]:
        dr.person_summary(arvore_contada, pid)

    assert contador.leituras <= 1, (
        "person_summary varreu as familias "
        f"{contador.leituras} vezes para 50 fichas; o indice por arvore deve fazer "
        "uma varredura so"
    )


def test_dossie_calcula_as_diferencas_uma_vez(arvore, monkeypatch):
    chamadas = []
    original = dr.person_summary

    def contando(arv, pid):
        chamadas.append(pid)
        return original(arv, pid)

    monkeypatch.setattr(dr, "person_summary", contando)
    dossie = dr.homonym_dossier(arvore, "Joao Silva")

    assert dossie["exact_count"] == 2
    assert dossie["identical_data"] is False
    assert [d["campo"] for d in dossie["differences"]] == ["birth"]
    assert len(chamadas) <= 3, (
        f"o dossie montou {len(chamadas)} fichas para 2 homonimos; "
        "as mesmas fichas estao sendo remontadas"
    )


def test_get_children_mesma_ordem_e_deduplicacao(arvore):
    for pid in arvore[0]:
        assert dr.get_children(arvore, pid) == _get_children_referencia(arvore, pid), (
            f"filhos divergentes para {pid}"
        )


def test_dossie_preserva_os_campos(arvore):
    dossie = dr.homonym_dossier(arvore, "Joao Silva")
    assert [f["id"] for f in dossie["exact_matches"]] == ["@I9@", "@I10@"]
    assert dossie["ambiguous"] is True
    assert dossie["differences"] == [
        {"campo": "birth", "rotulo": "data de nascimento"}
    ]
    assert dossie["identical_data"] is False
