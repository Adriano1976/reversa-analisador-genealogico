"""Testes da Tarefa 03 — Busca de Caminho (TT-01 a TT-05).

Carrega um GEDCOM sintético em memória e exercita o fluxo de busca
direta (ancestral comum), fallback indireto (afinidade), pessoa
inexistente, sem conexão e pessoas idênticas.
"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.fixtures.sample_gedcom import SAMPLE_GED

from reconstructed import upload
from reconstructed.path_search import (
    find_ancestral_path,
    find_indirect_path,
    find_person_by_name,
    path_search,
)


@pytest.fixture(scope="module")
def loaded_tree():
    """Carrega o GEDCOM sintético uma única vez para toda a suíte."""
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(SAMPLE_GED)
        upload.load_gedcom_and_build_graph(path)
    finally:
        os.remove(path)
    return upload


def test_person_lookup(loaded_tree):
    assert find_person_by_name("Carlos Silva") == ["@I3@"]
    assert "@I4@" in find_person_by_name("Ana Silva")
    assert find_person_by_name("Zzz Ninguém") == []


def test_direct_connection_trivial(loaded_tree):
    path, common = find_ancestral_path("@I3@", "@I3@")
    assert path == ["@I3@"]
    assert common == "@I3@"


def test_direct_connection_common_ancestor(loaded_tree):
    # TT-01: Carlos (I3) e Ana (I4) compartilham I1/I2.
    path, common = find_ancestral_path("@I3@", "@I4@")
    assert path is not None
    assert common in ("@I1@", "@I2@")


def test_path_search_direct(loaded_tree):
    result, msg, success = path_search("Carlos Silva", "Ana Silva")
    assert success is True
    assert msg == "Conexão direta encontrada (ancestral comum)."
    assert "Carlos Silva" in result["text_path"]
    assert "Ana Silva" in result["text_path"]
    assert result["mermaid_data"].startswith("flowchart BT")


def test_indirect_connection_via_marriage(loaded_tree):
    # TT-02: Carlos (I3) e Bia (I5) são casados (F2).
    result, msg, success = path_search("Carlos Silva", "Bia Oliveira")
    assert success is True
    assert msg == "Conexão indireta encontrada (via casamento/afinidade)."
    assert "Bia Oliveira" in result["text_path"]


def test_indirect_path_function(loaded_tree):
    person_path = find_indirect_path("@I3@", "@I5@", max_hops=40)
    assert person_path is not None
    assert "@I3@" in person_path
    assert "@I5@" in person_path


def test_person_not_found(loaded_tree):
    # TT-03: mensagem específica por pessoa.
    result, msg, success = path_search("Zzz Ninguém", "Carlos Silva")
    assert success is False
    assert "Pessoa 1 'Zzz Ninguém' não encontrada." == msg

    result, msg, success = path_search("Carlos Silva", "Zzz Ninguém")
    assert success is False
    assert "Pessoa 2 'Zzz Ninguém' não encontrada." == msg


def test_no_connection(loaded_tree):
    # TT-04: Lone Ranger não tem famílias; sem conexão com ninguém.
    result, msg, success = path_search("Carlos Silva", "Lone Ranger")
    assert success is True
    assert "Nenhuma conexão encontrada" in msg
    assert result is None


def test_identical_persons(loaded_tree):
    # TT-05: pessoas idênticas -> caminho trivial.
    result, msg, success = path_search("Carlos Silva", "Carlos Silva")
    assert success is True
    assert msg == "Conexão direta encontrada (ancestral comum)."
    assert result["text_path"] == "Carlos Silva"
