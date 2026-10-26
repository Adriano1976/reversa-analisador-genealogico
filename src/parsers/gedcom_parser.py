"""Parsing de GEDCOM e construcao do grafo.

Responsabilidade unica: traduzir um arquivo GEDCOM em registros e no grafo
bidirecional pessoa para familia, devolvendo a arvore como valor.

Extraido de `upload.py` pela OPP-20261003-TWNT. Ate `T023` da feature 005 esta
funcao TAMBEM substituia o estado global do processo; a escrita saiu, e a
assimetria de substituicao que ela exigia (dicionarios mutados in place, grafo
reatribuido) deixou de existir junto com o estado.

## A casca `load_gedcom_and_build_graph` saiu em `T015` da feature 006

Ela devolvia a lista de nomes ordenada, no contrato antigo. A varredura de
consumidores de producao deu **zero** — `app.py` e o coletor de paridade ja
liam `carregar_arvore`. Os consumidores reais eram tres, todos de teste, e
migraram para a arvore no mesmo passo. Quem ainda precisar da lista a deriva da
arvore, como `application/upload_gedcom.py` faz.
"""
from __future__ import annotations

import networkx as nx
from ged4py.parser import GedcomReader

from core.registro import get_name, ref_id

def build_graph_from_parser(people_dict: dict, familias):
    """Constrói grafo bidirecional pessoa<->familia e índice filho->famílias.

    Recebe as famílias **já materializadas** na ordem do arquivo, e não o
    `GedcomReader`: quem lê o arquivo é `carregar_arvore`, e a construção do grafo
    só transforma dado (`RN-03` da feature 025).

    ## Por que a lista, e não o dicionário `families`

    `families` é chaveado por `ref_id`, e `ref_id(None)` devolve `None`
    (`core.registro`). Duas famílias sem `xref_id` cairiam na mesma chave, e o
    dicionário teria menos entradas do que o arquivo tem. A lista preserva a
    **sequência exata** que a segunda passada percorria antes desta feature.

    ## Invariante: os registros só são LIDOS

    A lista é compartilhada com o dicionário `families` da árvore devolvida. Isso é
    seguro porque esta função lê apenas `fam.xref_id` e `fam.sub_records`, e nunca
    muta o registro. Se algum dia precisar mutar, a lista tem de ser copiada antes.
    """
    g = nx.Graph()
    c2f = {}
    for pid, person in people_dict.items():
        g.add_node(pid, label=get_name(person), type="person")
    for fam in familias:
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


Tree = tuple[dict, dict, "nx.Graph", dict]


def carregar_arvore(file_path: str) -> Tree:
    """Parseia o GEDCOM e devolve a ARVORE como valor (RF-13, D-02).

    A arvore e `(people, families, graph, child_to_family)`, na mesma forma que o
    estado global sempre teve — nenhum campo muda, e a ordem de insercao de cada
    estrutura e preservada, porque ela e contrato de paridade
    (`_reversa_sdd/migration/parity_specs.md` secao 4, tag `@ordem`).

    Sem estado: nao ha escrita de modulo, e a mesma funcao pode ser chamada duas
    vezes com arquivos diferentes sem que uma carga interfira na outra (`T023`).
    """
    # `GedcomReader.__exit__` do ged4py 0.5.5 e' tipado sem `None` em `exc_type`,
    # mas o `with` passa `None` quando nao ha excecao — o stub e' que esta errado.
    # Sem `close()` publico, o `with` e' o unico encerramento disponivel.
    # pyrefly: ignore[bad-context-manager]
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        # UMA materializacao por registro de nivel 0 (`RN-02`): a lista e lida
        # aqui e entregue ao grafo, em vez de o grafo percorrer `records0("FAM")`
        # de novo. Medido na arvore real de 35.460 pessoas: `read_record` caiu de
        # 49.321 (1 HEAD + 35.460 INDI + 2 x 6.930 FAM) para 42.391.
        #
        # E a LISTA, e nao `new_families.values()`: o dicionario e chaveado por
        # `ref_id`, e familia sem `xref_id` colapsa na chave `None`. A lista
        # preserva a sequencia exata que a segunda passada percorria.
        familias = list(parser.records0("FAM"))
        new_families = {ref_id(f.xref_id): f for f in familias}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, familias)
        return new_people, new_families, new_graph, new_child_to_family
