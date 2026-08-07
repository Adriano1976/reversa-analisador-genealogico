"""Tarefa 02 — Upload e Parsing de GEDCOM.

Salva o .ged em uploads/, faz o parsing de registros INDI/FAM via ged4py,
constrói o grafo bidirecional pessoa<->família (networkx) e retorna a lista
ordenada de nomes. Comportamento idêntico ao legado (inclui as limitações
documentadas: sem validação de extensão/tamanho, colisão sobrescreve).
"""
from __future__ import annotations

import os

import networkx as nx
from ged4py.parser import GedcomReader

# Estado global em memória (singleton por processo) — não persistente.
people = {}
families = {}
graph = None
child_to_family: dict[str, list[str]] = {}

UPLOAD_FOLDER = "uploads"


def ensure_dirs() -> None:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def ref_id(val):
    """Extrai o xref_id de um objeto ged4py; retorna o valor se já for str."""
    return getattr(val, "xref_id", val)


def get_name(person) -> str:
    """Nome formatado do registro; 'Sem Nome' se ausente ou vazio."""
    if not person or not person.name:
        return "Sem Nome"
    formatted = person.name.format()
    return formatted if formatted and formatted.strip() else "Sem Nome"


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

    Sobrescreve as globais people, families, graph e child_to_family.
    """
    global people, families, graph, child_to_family
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
        # Mutação in-place (clear + update) mantém válidas referências
        # importadas por outros módulos (ex.: path_search), preservando o
        # design de estado global do legado.
        people.clear(); people.update(new_people)
        families.clear(); families.update(new_families)
        graph = new_graph
        child_to_family.clear(); child_to_family.update(new_child_to_family)
        all_names = sorted([get_name(p) for p in people.values()])
        return all_names