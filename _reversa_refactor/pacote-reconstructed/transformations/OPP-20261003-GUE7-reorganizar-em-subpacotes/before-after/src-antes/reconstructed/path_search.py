"""Tarefa 03 — Busca de Caminho.

Resolução de pessoa por nome (1º ID em homônimos), conexão direta por
ancestral comum (BFS bidirecional, prof. máx. 20) e fallback de conexão
indireta por afinidade (shortest_path, máx. 40 hops) com compressão de
nós de família. Renderiza caminho textual + diagrama Mermaid.

Comportamento idêntico ao legado (inclui as decisões documentadas:
homônimos usam o 1º ID; famílias adotivas/complexas assumem caminho
por pais).


## Layout (OPP-20260929-UXEF)

Este modulo passou a compor o fluxo. As responsabilidades foram separadas em
`family_navigation` (parentesco), `path_finding` (os dois algoritmos de busca) e
`mermaid_render` (o diagrama e o escape do rotulo). A direcao das dependencias e
estritamente descendente, sem ciclo e sem import tardio novo.

## Superficie de compatibilidade

O bloco de reexportacao no fim do arquivo existe porque consumidores externos
importam nomes daqui: `app.py`, `reconstructed/dna_analysis.py`,
`tests/test_path_search.py`, `tests/test_mermaid_escape.py`,
`tests/test_characterization_mermaid.py`, `_reversa_sdd/parity/harness.py` e as
sondas do BUG-20260929-J6PQ. Enquanto eles nao forem migrados, o bloco fica.
"""

from __future__ import annotations

from .family_navigation import (
    are_spouses,
    exclude_tail,
    find_person_by_name,
    get_parents,
    get_spouses,
    pick_spouse_for_couple,
    split_path_by_marriage,
)
from .mermaid_render import (
    _LABEL_SEGURO,
    _mermaid_label,
    _mermaid_sid,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from .path_finding import MAX_DEPTH, MAX_HOPS, find_ancestral_path, find_indirect_path
from .gedcom_state import get_name, people, ref_id

# `are_spouses`, `get_parents`, `get_spouses`, `pick_spouse_for_couple`,
# `split_path_by_marriage`, `exclude_tail`, `MAX_DEPTH`, `_mermaid_sid`,
# `_LABEL_SEGURO`, `_mermaid_label` e `ref_id` nao sao usados por `path_search`.
# Eles estao aqui pela superficie de compatibilidade declarada em `__all__`.


def path_search(person1_name: str, person2_name: str):
    """Executa o fluxo completo de busca de caminho.

    Retorna `(path_result, msg, success)`. `path_result` é dict com
    `person1_name`, `person2_name`, `text_path` e `mermaid_data`.
    """
    person1_name = person1_name.strip()
    person2_name = person2_name.strip()

    p1_ids = find_person_by_name(person1_name)
    p2_ids = find_person_by_name(person2_name)
    if not p1_ids:
        return None, f"Pessoa 1 '{person1_name}' não encontrada.", False
    if not p2_ids:
        return None, f"Pessoa 2 '{person2_name}' não encontrada.", False

    p1_id, p2_id = p1_ids[0], p2_ids[0]

    path, common_ancestor = find_ancestral_path(p1_id, p2_id)
    if path:
        nomes = [get_name(people[n]) for n in path]
        mermaid_data = generate_mermaid_graph(path, p1_id, p2_id, common_ancestor)
        msg = "Conexão direta encontrada (ancestral comum)."
    else:
        person_path = find_indirect_path(p1_id, p2_id, max_hops=MAX_HOPS)
        if not person_path:
            return (None,
                    f"Nenhuma conexão encontrada entre '{person1_name}' e '{person2_name}'.",
                    True)
        nomes = [get_name(people[n]) for n in person_path]
        mermaid_data = generate_mermaid_graph_indirect_bridge(p1_id, p2_id, person_path)
        msg = "Conexão indireta encontrada (via casamento/afinidade)."

    path_result = {
        "person1_name": person1_name,
        "person2_name": person2_name,
        "text_path": " → ".join(nomes),
        "mermaid_data": mermaid_data,
    }
    return path_result, msg, True


# ---------------------------------------------------------------------------
# Superficie de compatibilidade (ver a nota no docstring do modulo).
# Reexporta o que era definido aqui antes da OPP-20260929-UXEF. Os nomes
# privados do render entram porque `tests/test_mermaid_escape.py` e as sondas do
# BUG-20260929-J6PQ os importam deste modulo.
# ---------------------------------------------------------------------------
__all__ = [
    "path_search",
    "find_person_by_name", "get_parents", "get_spouses", "are_spouses",
    "split_path_by_marriage", "pick_spouse_for_couple", "exclude_tail",
    "MAX_DEPTH", "MAX_HOPS", "find_indirect_path", "find_ancestral_path",
    "_mermaid_sid", "_LABEL_SEGURO", "_mermaid_label",
    "generate_mermaid_graph", "generate_mermaid_graph_indirect_bridge",
    "ref_id",
]
