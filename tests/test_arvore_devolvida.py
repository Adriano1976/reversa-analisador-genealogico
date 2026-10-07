"""A arvore devolvida pelo parse como valor (RF-13, feature 005 T009).

A feature `005-nucleo-puro-src` move a arvore de estado global para parametro. O
primeiro passo (`T009`) fez o parse DEVOLVER a arvore; `T023` removeu a escrita
das globais, que existiu so durante a transicao (`D-11`). Nao ha mais estado.

O que se verifica aqui e que o valor devolvido esta **completo e na mesma forma**
que o estado sempre teve: os quatro componentes preenchidos, as chaves de pessoa e
de familia iguais as do arquivo, e o grafo com os mesmos nos e arestas. Se o valor
devolvido vier vazio ou parcial, a migracao de cada consumidor (`T011` a `T014`)
construiria sobre uma base errada — e o harness acusaria divergencia so mais tarde,
longe da causa.
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from parsers import gedcom_parser  # noqa: E402

GEDCOM = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Joao /Silva/
1 SEX M
1 FAMS @F1@
0 @I2@ INDI
1 NAME Maria /Souza/
1 SEX F
1 FAMS @F1@
0 @I3@ INDI
1 NAME Carlos /Silva/
1 SEX M
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
0 TRLR
"""


@pytest.fixture()
def gedcom_temporario():
    fd, caminho = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(GEDCOM)
    yield caminho
    try:
        os.unlink(caminho)
    except OSError:
        pass


def test_carregar_arvore_devolve_os_quatro_componentes(gedcom_temporario):
    people, families, graph, child_to_family = gedcom_parser.carregar_arvore(gedcom_temporario)

    assert set(people) == {"@I1@", "@I2@", "@I3@"}, "pessoas do arquivo ausentes do valor devolvido"
    assert set(families) == {"@F1@"}, "familias do arquivo ausentes do valor devolvido"
    assert graph is not None and graph.number_of_nodes() > 0, "grafo devolvido vazio"
    assert child_to_family.get("@I3@") == ["@F1@"], "indice filho->familia incorreto"


def test_carregar_arvore_mantem_a_forma_do_estado(gedcom_temporario):
    """A forma nao muda: `dict`, `dict`, `nx.Graph`, `dict` com listas.

    A paridade depende disso. Trocar a forma — por um `set`, por um objeto novo —
    mudaria o valor comparado e quebraria o harness sem necessidade.
    """
    people, families, graph, child_to_family = gedcom_parser.carregar_arvore(gedcom_temporario)

    assert isinstance(people, dict) and isinstance(families, dict)
    assert isinstance(child_to_family, dict)
    assert all(isinstance(v, list) for v in child_to_family.values())
    assert hasattr(graph, "edges") and not graph.is_directed(), "o grafo deve seguir nao direcionado"


def test_grafo_da_arvore_liga_pessoa_a_familia_nos_dois_sentidos(gedcom_temporario):
    """O grafo e bidirecional pessoa<->familia, e o no de familia existe."""
    _people, _families, graph, _c2f = gedcom_parser.carregar_arvore(gedcom_temporario)

    assert graph.has_node("@F1@")
    for pessoa in ("@I1@", "@I2@", "@I3@"):
        assert graph.has_node(pessoa)
        assert graph.has_edge(pessoa, "@F1@"), "aresta %s <-> @F1@ ausente" % pessoa


def test_contrato_antigo_devolve_a_lista_de_nomes(gedcom_temporario):
    """`load_gedcom_and_build_graph` mantem o retorno antigo durante a migracao.

    Os dois consumidores de hoje dependem desta forma (`src/app.py` para o campo
    de sugestao; o coletor do harness para o probe `names`). Trocá-la agora
    quebraria os dois no mesmo passo em que o parse muda.
    """
    nomes = gedcom_parser.load_gedcom_and_build_graph(gedcom_temporario)

    assert isinstance(nomes, list)
    assert nomes == sorted(nomes), "a lista de nomes deve vir ordenada"
    assert set(nomes) == {"Joao Silva", "Maria Souza", "Carlos Silva"}
