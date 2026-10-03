"""Parsing de GEDCOM e construcao do grafo.

Responsabilidade unica: traduzir um arquivo GEDCOM em registros e no grafo
bidirecional pessoa para familia, substituindo o estado do processo.

Extraido de `upload.py` pela OPP-20261003-TWNT. A assimetria de substituicao do
estado (dicionarios mutados in place, grafo reatribuido) e deliberada e esta
documentada em `gedcom_state`.
"""
from __future__ import annotations

import networkx as nx
from ged4py.parser import GedcomReader

from core import gedcom_state
from core.gedcom_state import get_name, ref_id

def build_graph_from_parser(people_dict: dict, parser):
    """Constrói grafo bidirecional pessoa<->familia e índice filho->famílias."""
    g = nx.Graph()
    c2f = {}
    for pid, person in people_dict.items():
        g.add_node(pid, label=get_name(person), type="person")
    for fam in parser.records0("FAM"):
        fam_id = ref_id(fam.xref_id)
        if not fam_id:
            continue
        g.add_node(fam_id, label="Familia", type="family")
        husband_id = wife_id = None
        child_ids = []
        for sub_rec in fam.sub_records:
            if sub_rec.tag == "HUSB":
                husband_id = ref_id(sub_rec.value)
            elif sub_rec.tag == "WIFE":
                wife_id = ref_id(sub_rec.value)
            elif sub_rec.tag == "CHIL":
                cid = ref_id(sub_rec.value)
                child_ids.append(cid)
                c2f.setdefault(cid, []).append(fam_id)
        if husband_id and g.has_node(husband_id):
            g.add_edge(husband_id, fam_id)
        if wife_id and g.has_node(wife_id):
            g.add_edge(wife_id, fam_id)
        for cid in child_ids:
            if g.has_node(cid):
                g.add_edge(cid, fam_id)
    return g, c2f


def load_gedcom_and_build_graph(file_path: str) -> list[str]:
    """Parseia o GEDCOM e devolve a lista de nomes ordenada.

    Substitui o estado: dicionarios in place, grafo reatribuido. Ver `gedcom_state`.
    """
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
        # Mutação in-place (clear + update) mantém válidas as referências
        # importadas no topo pelos outros módulos. A reatribuição do grafo
        # é lida por quem o importa dentro da função (ver path_finding.py).
        gedcom_state.people.clear(); gedcom_state.people.update(new_people)
        gedcom_state.families.clear(); gedcom_state.families.update(new_families)
        gedcom_state.graph = new_graph
        gedcom_state.child_to_family.clear(); gedcom_state.child_to_family.update(new_child_to_family)
        all_names = sorted([get_name(p) for p in gedcom_state.people.values()])
        return all_names
