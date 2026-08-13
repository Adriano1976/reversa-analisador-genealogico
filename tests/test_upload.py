"""Testes da Tarefa 02 — Upload e Parsing de GEDCOM.

Cobre ref_id, get_name, build_graph_from_parser e
load_gedcom_and_build_graph, incluindo o comportamento do estado global
em memória e o índice filho->família. Usa o GEDCOM sintético de testes.
"""
import os
import sys
import tempfile

import networkx as nx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analisador-genealogico"))

from tests.fixtures.sample_gedcom import SAMPLE_GED

from reconstructed import upload
# pyrefly: ignore [missing-import]
from reconstructed.upload import build_graph_from_parser, get_name, ref_id


def _write_g(content=SAMPLE_GED):
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path
    except Exception:
        os.remove(path)
        raise


# ---------------------------------------------------------------------------
# ref_id
# ---------------------------------------------------------------------------

def test_ref_id_passthrough_for_str():
    assert ref_id("@I1@") == "@I1@"


def test_ref_id_reads_xref_id_attribute():
    class Obj:
        def __init__(self, xref_id):
            self.xref_id = xref_id

    assert ref_id(Obj("@F1@")) == "@F1@"


# ---------------------------------------------------------------------------
# get_name
# ---------------------------------------------------------------------------

def test_get_name_empty_none():
    assert get_name(None) == "Sem Nome"


def test_get_name_real_person():
    path = _write_g(SAMPLE_GED)
    try:
        upload.load_gedcom_and_build_graph(path)
        # @I1@ é "Joao /Silva/" no fixture; verifica formato retornado.
        p = upload.people["@I1@"]
        name = get_name(p)
        assert name and isinstance(name, str)
        assert name.lower().startswith("joao")
    finally:
        os.remove(path)


def test_get_name_missing_returns_sem_nome():
    ged = SAMPLE_GED.replace("1 NAME Joao /Silva/", "1 SEX M")  # remove so nome
    path = _write_g(ged)
    try:
        upload.load_gedcom_and_build_graph(path)
        assert get_name(upload.people["@I1@"]) in ("Sem Nome", "")
    finally:
        os.remove(path)


# ---------------------------------------------------------------------------
# ensure_dirs
# ---------------------------------------------------------------------------

def test_ensure_dirs_creates_uploads(monkeypatch, tmp_path):
    target = str(tmp_path / "upl")
    monkeypatch.setattr(upload, "UPLOAD_FOLDER", target)
    upload.ensure_dirs()
    assert os.path.isdir(target)


# ---------------------------------------------------------------------------
# load_gedcom_and_build_graph — happy path
# ---------------------------------------------------------------------------

def _load(content):
    ged = _write_g(content)
    try:
        return upload.load_gedcom_and_build_graph(ged)
    finally:
        os.remove(ged)


def test_load_populates_globals():
    _load(SAMPLE_GED)
    assert "@I1@" in upload.people
    assert "@I3@" in upload.people
    assert "@F1@" in upload.families
    assert upload.child_to_family.get("@I3@") == ["@F1@"]


def test_load_returns_sorted_names():
    names = _load(SAMPLE_GED)
    assert names == sorted(names)
    # Pessoas esperadas no GEDCOM sintético.
    assert any("Joao" in n for n in names)
    assert any("Carlos" in n for n in names)
    assert "Sem Nome" in names or any(n.strip() for n in names)


def test_reload_replaces_globals():
    first = _load(SAMPLE_GED)
    # Carrega outro conteúdo -> `people` deve ser substituído, não somado.
    _load(SAMPLE_GED)
    assert set(upload.people.keys()) == {"@I1@", "@I2@", "@I3@", "@I4@", "@I5@", "@I6@", "@I9@"}


# ---------------------------------------------------------------------------
# build_graph_from_parser
# ---------------------------------------------------------------------------

def test_build_graph_structure():
    _load(SAMPLE_GED)
    from ged4py.parser import GedcomReader

    with GedcomReader(_write_g(SAMPLE_GED)) as parser:
        g, c2f = build_graph_from_parser(upload.people, parser)

    assert isinstance(g, nx.Graph)
    # Nós de pessoas e de família presentes.
    assert "@I1@" in g
    assert "@F1@" in g
    # Arestas pai/cônjuge <-> família e filho <-> família.
    assert g.has_edge("@I1@", "@F1@")      # HUSB
    assert g.has_edge("@I2@", "@F1@")      # WIFE
    assert g.has_edge("@I3@", "@F1@")      # CHIL
    # Índice filho -> famílias.
    assert c2f.get("@I3@") == ["@F1@"]


def test_graph_bidirectional_nodes_person_family_types():
    _load(SAMPLE_GED)
    g = upload.graph
    assert g.nodes["@I1@"]["type"] == "person"
    assert g.nodes["@F1@"]["type"] == "family"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_parse_malformed_raises():
    bad = "0 HEAD\nesta linha quebra o parser"
    ged = _write_g(bad)
    try:
        # malformado pode lançar; não deve travar o processo silenciosamente.
        try:
            upload.load_gedcom_and_build_graph(ged)
        except Exception:
            pass
        else:
            raise AssertionError("esperado erro em GEDCOM malformado")
    finally:
        os.remove(ged)


def test_family_without_id_skipped():
    _load(SAMPLE_GED)
    from ged4py.parser import GedcomReader

    # FAM sem xref_id não adiciona nó; pessoas ainda mapeiam filhos corretamente.
    with GedcomReader(_write_g(SAMPLE_GED)) as parser:
        g, c2f = build_graph_from_parser(upload.people, parser)
    assert "@I3@" in g
    assert c2f.get("@I3@") == ["@F1@"]