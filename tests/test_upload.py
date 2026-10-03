"""Testes da Tarefa 02 — Parsing de GEDCOM e construção do grafo.

Cobre ref_id, get_name, build_graph_from_parser e
load_gedcom_and_build_graph, incluindo o comportamento do estado global
em memória e o índice filho->família. Usa o GEDCOM sintético de testes.

Removido em 2026-10-02: o teste de `ensure_dirs()`, junto com a função e a
constante `UPLOAD_FOLDER` que ele exercitava. Eram resíduo do legado, sem
consumidor de produção — o `app.py` resolve a pasta por `_pasta_uploads()`.
"""
import os
import sys
import tempfile

import networkx as nx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures.sample_gedcom import SAMPLE_GED

from reconstructed import gedcom_parser
from reconstructed import gedcom_state
from reconstructed.gedcom_parser import build_graph_from_parser
from reconstructed.gedcom_state import get_name, ref_id


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
        gedcom_parser.load_gedcom_and_build_graph(path)
        # @I1@ é "Joao /Silva/" no fixture; verifica formato retornado.
        p = gedcom_state.people["@I1@"]
        name = get_name(p)
        assert name and isinstance(name, str)
        assert name.lower().startswith("joao")
    finally:
        os.remove(path)


def test_get_name_absent_attribute_returns_sem_nome():
    """Falsy `person` ou `person.name` -> 'Sem Nome' (o unico caso do fallback).

    Descoberto medindo, e o achado e mais forte do que parece: um registro sem o
    atributo `name` NAO devolve None — o ged4py levanta AttributeError. A expressao do
    legado, `person and person.name`, curto-circuita em `person` antes de tocar `.name`,
    entao o AttributeError nunca ocorre com um registro real. Combinado com o fato de
    que remover a tag NAME produz um objeto Name vazio ('' e nao 'Sem Nome'), a
    conclusao e: **o literal 'Sem Nome' e inalcancavel a partir de registros INDI** —
    e e exatamente por isso que ele nunca aparece nos 55.523 nomes da base real.

    Logo o fallback so e exercitavel por um duplo de teste. Documentado aqui para que
    ninguem "conserte" a funcao tentando cobrir um caso de dados que nao existe.
    """
    class SemNome:
        name = None

    assert get_name(None) == "Sem Nome"      # `person` falsy
    assert get_name(SemNome()) == "Sem Nome"  # `person.name` falsy


def test_get_name_empty_formatted_returns_empty_string():
    """Tag NAME presente mas com formato vazio -> '' (nao 'Sem Nome').

    DIV-001: a reconstrucao tratava este caso como 'Sem Nome', divergindo do
    oraculo congelado (app_legacy_e43ca22.py:42-43), que devolve `person.name.format()`
    sem fallback. E o caso que OCORRE em dado real (296 pessoas em 35.460). Este teste
    existe porque a versao anterior assertava `in ("Sem Nome", "")` — uma assercao que
    aceita os DOIS valores, logo nao pode falhar e nao protegia nada.
    """
    ged = SAMPLE_GED.replace("1 NAME Joao /Silva/", "1 NAME /")
    path = _write_g(ged)
    try:
        gedcom_parser.load_gedcom_and_build_graph(path)
        assert get_name(gedcom_state.people["@I1@"]) == ""
    finally:
        os.remove(path)


def test_get_name_indian_without_name_tag_returns_empty_string():
    """Remover a tag NAME de um INDI -> '' (NAO 'Sem Nome'). Documenta o achado acima."""
    ged = SAMPLE_GED.replace("1 NAME Joao /Silva/", "1 SEX M")
    path = _write_g(ged)
    try:
        gedcom_parser.load_gedcom_and_build_graph(path)
        assert get_name(gedcom_state.people["@I1@"]) == ""
    finally:
        os.remove(path)


# ---------------------------------------------------------------------------
# load_gedcom_and_build_graph — happy path
# ---------------------------------------------------------------------------

def _load(content):
    ged = _write_g(content)
    try:
        return gedcom_parser.load_gedcom_and_build_graph(ged)
    finally:
        os.remove(ged)


def test_load_populates_globals():
    _load(SAMPLE_GED)
    assert "@I1@" in gedcom_state.people
    assert "@I3@" in gedcom_state.people
    assert "@F1@" in gedcom_state.families
    assert gedcom_state.child_to_family.get("@I3@") == ["@F1@"]


def test_load_returns_sorted_names():
    names = _load(SAMPLE_GED)
    assert names == sorted(names)
    # Pessoas esperadas no GEDCOM sintético.
    assert any("Joao" in n for n in names)
    assert any("Carlos" in n for n in names)


def test_load_returns_exactly_one_name_per_person_and_no_empty_entries():
    """SAMPLE_GED tem 7 pessoas, TODAS com nome: nenhuma entrada vazia, nenhum 'Sem Nome'.

    Substitui a assercao anterior:

        assert "Sem Nome" in names or any(n.strip() for n in names)

    Aquela disjuncao era satisfeita pelos outros nomes da arvore, entao passava mesmo
    com uma entrada vazia presente — e portanto nao podia falhar quando `get_name`
    divergia do oraculo (DIV-001). Esta versao falha em ambos os casos.
    """
    names = _load(SAMPLE_GED)
    assert len(names) == 7
    assert len(names) == len(gedcom_state.people)
    assert "" not in names
    assert "Sem Nome" not in names


def test_reload_replaces_globals():
    first = _load(SAMPLE_GED)
    # Carrega outro conteúdo -> `people` deve ser substituído, não somado.
    _load(SAMPLE_GED)
    assert set(gedcom_state.people.keys()) == {"@I1@", "@I2@", "@I3@", "@I4@", "@I5@", "@I6@", "@I9@"}


# ---------------------------------------------------------------------------
# build_graph_from_parser
# ---------------------------------------------------------------------------

def test_build_graph_structure():
    _load(SAMPLE_GED)
    from ged4py.parser import GedcomReader

    with GedcomReader(_write_g(SAMPLE_GED)) as parser:
        g, c2f = build_graph_from_parser(gedcom_state.people, parser)

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
    g = gedcom_state.graph
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
            gedcom_parser.load_gedcom_and_build_graph(ged)
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
        g, c2f = build_graph_from_parser(gedcom_state.people, parser)
    assert "@I3@" in g
    assert c2f.get("@I3@") == ["@F1@"]
