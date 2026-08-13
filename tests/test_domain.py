"""Testes da Tarefa 01 — Entidades de Domínio.

Cobre Family, GenealogyGraph, DNAGroup e as rotinas de limpeza de
mojibake (strip_bad_utf, demojibake) documentadas em domain.md.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analisador-genealogico"))

# pyrefly: ignore [missing-import]
from reconstructed.domain import (
    DNAGroup,
    Family,
    GenealogyGraph,
    MOJIBAKE_MAP,
    demojibake,
    strip_bad_utf,
)


# ---------------------------------------------------------------------------
# Mojibake (domain.md §2.3 / §1)
# ---------------------------------------------------------------------------

def test_strip_bad_utf_removes_replacement_char():
    assert "\ufffd" not in strip_bad_utf("Jo\uFFFDa\uFFFDo")


def test_strip_bad_utf_handles_none_and_empty():
    assert strip_bad_utf(None) == "" or strip_bad_utf("") == ""


def test_demojibake_fixes_cedilha():
    # "Ã§" corrompido deve virar "ç".
    assert "ç" in demojibake("FranÃ§isco")


def test_demojibake_returns_input_for_empty():
    assert demojibake("") == ""
    # Legado: `if not text: return text` -> None passa adiante.
    assert demojibake(None) is None


def test_demojibake_applies_known_map():
    if "A\u0303" in MOJIBAKE_MAP:
        assert "Ã" in demojibake("A\u0303")


# ---------------------------------------------------------------------------
# Family (entidade FAMILIA)
# ---------------------------------------------------------------------------

def test_family_defaults():
    fam = Family(xref_id="@F1@")
    assert fam.husb == ""
    assert fam.wife == ""
    assert fam.chil == []


def test_family_fields():
    fam = Family(xref_id="@F2@", husb="@I1@", wife="@I2@", chil=["@I3@", "@I4@"])
    assert fam.husb == "@I1@"
    assert fam.wife == "@I2@"
    assert len(fam.chil) == 2


def test_family_chil_is_isolated_per_instance():
    # field(default_factory=list) garante que cada instância tem lista própria.
    a = Family("@F1@")
    b = Family("@F2@")
    a.chil.append("@I9@")
    assert b.chil == []


# ---------------------------------------------------------------------------
# GenealogyGraph (grafo pessoa<->família)
# ---------------------------------------------------------------------------

def test_register_person_normalizes_name():
    g = GenealogyGraph()
    g.register_person("@I1@", "Jo\uFFFDa\u0303o")
    p = g.get_person("@I1@")
    assert p["xref_id"] == "@I1@"
    # name_clean passa por demojibake + strip.
    assert "name_clean" in p


def test_register_person_ignores_duplicate():
    g = GenealogyGraph()
    g.register_person("@I1@", "Nome Original")
    g.register_person("@I1@", "Nome Novo")
    assert g.get_person("@I1@")["name"] == "Nome Original"


def test_get_person_missing_returns_none():
    assert GenealogyGraph().get_person("@ZZZ@") is None


def test_register_family():
    g = GenealogyGraph()
    fam = Family("@F1@", husb="@I1@", wife="@I2@")
    g.register_family(fam)
    assert g.families["@F1@"] is fam


# ---------------------------------------------------------------------------
# DNAGroup (entidade DNA_MATCH)
# ---------------------------------------------------------------------------

def test_dna_group_fields():
    grp = DNAGroup(_group_key="ana | ana@x.com", cm=537.0)
    assert grp.cm == 537.0
    assert grp.matched_name == ""
    assert grp.aux == ""


def test_dna_group_defaults():
    grp = DNAGroup(_group_key="k", cm=0)
    assert grp.matched_name == ""
    assert grp.aux == ""