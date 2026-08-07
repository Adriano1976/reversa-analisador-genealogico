"""Tarefa 03 — Busca de Caminho.

Resolução de pessoa por nome (1º ID em homônimos), conexão direta por
ancestral comum (BFS bidirecional, prof. máx. 20) e fallback de conexão
indireta por afinidade (shortest_path, máx. 40 hops) com compressão de
nós de família. Renderiza caminho textual + diagrama Mermaid.

Comportamento idêntico ao legado (inclui as decisões documentadas:
homônimos usam o 1º ID; famílias adotivas/complexas assumem caminho
por pais).
"""
from __future__ import annotations

import re
import unicodedata
from collections import deque

import networkx as nx

from .upload import child_to_family, families, get_name, people

MAX_DEPTH = 20
MAX_HOPS = 40


# ---------------------------------------------------------------------------
# Resolução de pessoas
# ---------------------------------------------------------------------------

def find_person_by_name(name_query):
    """Exact match (case-insensitive) primeiro; depois substring."""
    exact = [pid for pid, p in people.items() if name_query.lower() == get_name(p).lower()]
    if exact:
        return exact
    return [pid for pid, p in people.items() if name_query.lower() in get_name(p).lower()]


# ---------------------------------------------------------------------------
# Navegação familiar
# ---------------------------------------------------------------------------

def get_parents(person_id):
    """Pais de uma pessoa via FAMC ou índice filho->famílias."""
    person = people.get(person_id)
    if not person:
        return []
    famc_ref = next((ref_id(rec.value) for rec in person.sub_records if rec.tag == "FAMC"), None)
    fam_ids = [famc_ref] if famc_ref else child_to_family.get(person_id, [])
    if not fam_ids:
        return []
    parent_ids = []
    for fam_id in fam_ids:
        family = families.get(fam_id)
        if not family:
            continue
        for sub_rec in family.sub_records:
            if sub_rec.tag in ("HUSB", "WIFE"):
                pid = ref_id(sub_rec.value)
                if pid and pid not in parent_ids:
                    parent_ids.append(pid)
    return parent_ids


def get_spouses(person_id):
    """Cônjuges de uma pessoa via registros FAMS; fallback por varredura."""
    person = people.get(person_id)
    spouse_ids = []
    if person:
        fams_refs = [ref_id(rec.value) for rec in person.sub_records if rec.tag == "FAMS"]
        for fam_ref in fams_refs:
            family = families.get(fam_ref)
            if not family:
                continue
            is_husband = any(ref_id(rec.value) == person_id for rec in family.sub_records if rec.tag == "HUSB")
            partner_tag = "WIFE" if is_husband else "HUSB"
            for rec in family.sub_records:
                if rec.tag == partner_tag:
                    spouse_ids.append(ref_id(rec.value))
    if spouse_ids:
        return spouse_ids
    for fam in families.values():
        husb = next((ref_id(r.value) for r in fam.sub_records if r.tag == "HUSB"), None)
        wife = next((ref_id(r.value) for r in fam.sub_records if r.tag == "WIFE"), None)
        if husb == person_id and wife:
            spouse_ids.append(wife)
        elif wife == person_id and husb:
            spouse_ids.append(husb)
    return spouse_ids


def are_spouses(a_id, b_id) -> bool:
    return b_id in set(get_spouses(a_id))


def split_path_by_marriage(person_path):
    """Encontra o 1º par de cônjuges adjacentes no caminho indireto."""
    for i in range(len(person_path) - 1):
        a, b = person_path[i], person_path[i + 1]
        if are_spouses(a, b):
            left = person_path[:i + 1]      # ... → A
            right = person_path[i + 1:]     # B → ...
            return left, right, (a, b)
    return None, None, None


def pick_spouse_for_couple(person_id, candidate_path=None):
    """Escolhe um cônjuge para formar o 'casal' no topo do ramo."""
    spouses = get_spouses(person_id) or []
    if candidate_path:
        seen = set(candidate_path)
        for s in spouses:
            if s in seen:
                return s
    return spouses[0] if spouses else None


def exclude_tail(seq, n=1):
    """Retorna seq sem os últimos n elementos (evita duplicar o ancestral na ponta)."""
    return seq[:-n] if len(seq) > n else []


# ---------------------------------------------------------------------------
# Busca de caminho
# ---------------------------------------------------------------------------

def find_indirect_path(start_id, end_id, max_hops=MAX_HOPS):
    """Procura QUALQUER caminho no grafo pessoa<->família.

    Retorna apenas os nós de pessoa, comprimindo os nós de família.
    """
    from .upload import graph
    if graph is None or start_id not in graph or end_id not in graph:
        return None
    try:
        path = nx.shortest_path(graph, source=start_id, target=end_id)  # BFS não ponderado
        if len(path) - 1 > max_hops:
            return None
        person_path = [n for n in path if n in people]
        return person_path if len(person_path) >= 2 else None
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def find_ancestral_path(start_id, end_id, max_depth=MAX_DEPTH):
    """BFS bidirecional subindo por pais (profundidade máx. max_depth).

    Retorna `(path, common_ancestor)` ou `(None, None)`.
    """
    q1, q2 = deque([(start_id, [start_id])]), deque([(end_id, [end_id])])
    visited1, visited2 = {start_id: [start_id]}, {end_id: [end_id]}
    if start_id == end_id:
        return ([start_id], start_id)
    for _depth in range(max_depth):
        q_size = len(q1)
        if not q_size:
            break
        for _ in range(q_size):
            curr_id, path = q1.popleft()
            if curr_id in visited2:
                return (path + visited2[curr_id][::-1][1:], curr_id)
            for p_id in get_parents(curr_id):
                if p_id not in visited1:
                    new_path = path + [p_id]
                    visited1[p_id] = new_path
                    q1.append((p_id, new_path))
        q_size = len(q2)
        if not q_size:
            break
        for _ in range(q_size):
            curr_id, path = q2.popleft()
            if curr_id in visited1:
                return (visited1[curr_id] + path[::-1][1:], curr_id)
            for p_id in get_parents(curr_id):
                if p_id not in visited2:
                    new_path = path + [p_id]
                    visited2[p_id] = new_path
                    q2.append((p_id, new_path))
    return (None, None)


# ---------------------------------------------------------------------------
# Renderização Mermaid
# ---------------------------------------------------------------------------

def generate_mermaid_graph(path, p1_id, p2_id, common_ancestor_id):
    def sid(raw: str) -> str:
        safe_str = str(raw).replace('@', '').replace('+', '_')
        return 'N_' + re.sub(r'[^a-zA-Z0-9_]', '', safe_str)

    def lab(txt: str) -> str:
        s = unicodedata.normalize("NFC", str(txt))
        s = (s.replace('\u00A0', ' ')
               .replace('\u2013', '-')
               .replace('\u2014', '-')
               .replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'"))
        s = (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        s = s.replace('"', "'")
        s = re.sub(r'[\r\n]+', ' ', s)
        return s

    lines = ["flowchart BT"]
    seen_nodes = set()
    ac_idx = -1
    if common_ancestor_id and common_ancestor_id in path:
        try:
            ac_idx = path.index(common_ancestor_id)
        except ValueError:
            pass
    is_direct_ancestry = (ac_idx == -1 or ac_idx == 0 or ac_idx == len(path) - 1)
    couple_members_to_skip = set()
    ancestor_id_for_arrows = sid(common_ancestor_id)
    if not is_direct_ancestry:
        spouses = get_spouses(common_ancestor_id)
        if spouses:
            couple_members_to_skip.update({common_ancestor_id, spouses[0]})
            couple_id_str = "+".join(sorted(list(couple_members_to_skip)))
            ancestor_id_for_arrows = sid(couple_id_str)
            ac_name1 = lab(get_name(people[common_ancestor_id]))
            ac_name2 = lab(get_name(people[spouses[0]]))
            lines.append(f'{ancestor_id_for_arrows}["{ac_name1} &amp; {ac_name2}"]')
            seen_nodes.add(ancestor_id_for_arrows)
    for node_id in path:
        if node_id in couple_members_to_skip:
            continue
        node_sid = sid(node_id)
        if node_sid not in seen_nodes:
            node_name = lab(get_name(people.get(node_id)))
            lines.append(f'{node_sid}["{node_name}"]')
            seen_nodes.add(node_sid)
    if is_direct_ancestry:
        for i in range(len(path) - 1):
            lines.append(f'{sid(path[i])} --> {sid(path[i + 1])}')
    elif ac_idx > 0:
        for i in range(ac_idx - 1):
            lines.append(f'{sid(path[i])} --> {sid(path[i + 1])}')
        lines.append(f'{sid(path[ac_idx - 1])} --> {ancestor_id_for_arrows}')
        for i in range(len(path) - 1, ac_idx + 1, -1):
            lines.append(f'{sid(path[i])} --> {sid(path[i - 1])}')
        lines.append(f'{sid(path[ac_idx + 1])} --> {ancestor_id_for_arrows}')
    lines.append(f'style {sid(p1_id)} fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px')
    lines.append(f'style {sid(p2_id)} fill:#ffebee,stroke:#ef5350,stroke-width:2px')
    if common_ancestor_id:
        lines.append(f'style {ancestor_id_for_arrows} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    return "\n".join(lines)


def generate_mermaid_graph_indirect_bridge(p1_id, p2_id, person_path):
    def sid(raw: str) -> str:
        if isinstance(raw, (list, tuple, set)):
            raw = next(iter(raw), "")
        safe_str = str(raw).replace('@', '').replace('+', '_')
        return 'N_' + re.sub(r'[^a-zA-Z0-9_]', '', safe_str)

    def lab(txt: str) -> str:
        s = unicodedata.normalize("NFC", str(txt))
        s = (s.replace('\u00A0', ' ')
               .replace('\u2013', '-').replace('\u2014', '-')
               .replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'"))
        s = (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        s = s.replace('"', "'")
        s = re.sub(r'[\r\n]+', ' ', s)
        return s

    def norm_ids(seq):
        out = []
        if not seq:
            return out
        for x in seq:
            if isinstance(x, (list, tuple, set)):
                out.extend([str(y) for y in x])
            else:
                out.append(str(x))
        return out

    left, right, spouses = split_path_by_marriage(person_path)
    if not spouses:
        return generate_mermaid_graph(person_path, p1_id, p2_id, None)

    A, B = map(str, spouses)
    p1_id, p2_id = str(p1_id), str(p2_id)

    is_direct_connection_to_p2 = (p2_id == B)

    path_p1_A, ca1 = find_ancestral_path(p1_id, A)
    if not path_p1_A:
        return generate_mermaid_graph(person_path, p1_id, p2_id, None)

    spouse_ca1 = pick_spouse_for_couple(ca1, candidate_path=path_p1_A)

    def split_at(path, mid):
        path = norm_ids(path)
        mid = str(mid)
        i = path.index(mid)
        down = path[:i + 1]
        up_rev = list(reversed(path[i:]))
        return down, up_rev

    r1_down, r1_up_from_A = split_at(path_p1_A, ca1)

    couple1_id = None
    if spouse_ca1:
        couple1_id = sid("+".join(sorted([str(ca1), str(spouse_ca1)])))
        couple1_label = f'{lab(get_name(people.get(ca1)))} &amp; {lab(get_name(people.get(spouse_ca1)))}'

    lines = ["flowchart BT"]
    seen = set()

    def add_node(pid, label=None):
        pid = str(pid)
        node = sid(pid)
        if node not in seen:
            lines.append(f'{node}["{lab(get_name(people.get(pid))) if label is None else label}"]')
            seen.add(node)
        return node

    def add_chain(seq):
        seq = norm_ids(seq)
        for i in range(len(seq)):
            add_node(seq[i])
            if i < len(seq) - 1:
                lines.append(f'{sid(seq[i])} --> {sid(seq[i + 1])}')

    lines.append("subgraph COLUMNS")
    lines.append("direction BT")
    lines.append("subgraph ESQ[Ramo 1]")
    lines.append("direction BT")
    lines.append("subgraph ESQ_COLS")
    lines.append("direction BT")

    left_col_r1 = exclude_tail(r1_down, n=1)
    right_col_r1 = exclude_tail(r1_up_from_A, n=1)

    if left_col_r1:
        lines.append("subgraph ESQ_L[ ]")
        lines.append("direction BT")
        add_chain(left_col_r1)
        lines.append("end")

    if right_col_r1:
        lines.append("subgraph ESQ_R[ ]")
        lines.append("direction BT")
        add_chain(right_col_r1)
        lines.append("end")

    lines.append("end")  # ESQ_COLS

    if couple1_id:
        lines.append(f'{couple1_id}["{couple1_label}"]')
        if left_col_r1:
            lines.append(f'{sid(left_col_r1[-1])} --> {couple1_id}')
        if right_col_r1:
            lines.append(f'{sid(right_col_r1[-1])} --> {couple1_id}')
    else:
        add_node(ca1)
        if left_col_r1:
            lines.append(f'{sid(left_col_r1[-1])} --> {sid(ca1)}')
        if right_col_r1:
            lines.append(f'{sid(right_col_r1[-1])} --> {sid(ca1)}')

    lines.append("end")  # ESQ

    if is_direct_connection_to_p2:
        lines.append("subgraph DIR[Ramo 2]")
        lines.append("direction BT")
        add_node(p2_id)
        lines.append("end")
        right_col_r2 = []
        couple2_id, ca2 = None, None
    else:
        path_p2_B, ca2 = find_ancestral_path(p2_id, B)
        if not path_p2_B:
            return generate_mermaid_graph(person_path, p1_id, p2_id, None)

        spouse_ca2 = pick_spouse_for_couple(ca2, candidate_path=path_p2_B)
        r2_down, r2_up_from_B = split_at(path_p2_B, ca2)

        couple2_id = None
        if spouse_ca2:
            couple2_id = sid("+".join(sorted([str(ca2), str(spouse_ca2)])))
            couple2_label = f'{lab(get_name(people.get(ca2)))} &amp; {lab(get_name(people.get(spouse_ca2)))}'

        lines.append("subgraph DIR[Ramo 2]")
        lines.append("direction BT")
        lines.append("subgraph DIR_COLS")
        lines.append("direction BT")

        left_col_r2 = exclude_tail(r2_up_from_B, n=1)
        right_col_r2 = exclude_tail(r2_down, n=1)

        if left_col_r2:
            lines.append("subgraph DIR_L[ ]")
            lines.append("direction BT")
            add_chain(left_col_r2)
            lines.append("end")

        if right_col_r2:
            lines.append("subgraph DIR_R[ ]")
            lines.append("direction BT")
            add_chain(right_col_r2)
            lines.append("end")

        lines.append("end")  # DIR_COLS

        if couple2_id:
            lines.append(f'{couple2_id}["{couple2_label}"]')
            if left_col_r2:
                lines.append(f'{sid(left_col_r2[-1])} --> {couple2_id}')
            if right_col_r2:
                lines.append(f'{sid(right_col_r2[-1])} --> {couple2_id}')
        else:
            add_node(ca2)
            if left_col_r2:
                lines.append(f'{sid(left_col_r2[-1])} --> {sid(ca2)}')
            if right_col_r2:
                lines.append(f'{sid(right_col_r2[-1])} --> {sid(ca2)}')

        lines.append("end")  # DIR

    A_anchor = sid(f"{A}_anc")
    B_anchor = sid(f"{B}_anc")
    lines += [
        f'{A_anchor}[" "]',
        f'{B_anchor}[" "]',
        f'style {A_anchor} fill:transparent,stroke:transparent,stroke-width:0',
        f'style {B_anchor} fill:transparent,stroke:transparent,stroke-width:0',
        f'{sid(A)} --- {A_anchor}',
        f'{B_anchor} --- {sid(B)}',
        f'{A_anchor} --- |Casamento| {B_anchor}',
    ]
    lines.append("end")  # COLUMNS

    if left_col_r1:
        lines.append(f'style {sid(p1_id)} fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px')

    if is_direct_connection_to_p2 or right_col_r2:
        lines.append(f'style {sid(p2_id)} fill:#ffebee,stroke:#ef5350,stroke-width:2px')

    if couple1_id:
        lines.append(f'style {couple1_id} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    elif ca1:
        lines.append(f'style {sid(ca1)} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    if couple2_id:
        lines.append(f'style {couple2_id} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    elif ca2:
        lines.append(f'style {sid(ca2)} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    lines.append(f'style {sid(A)} fill:#fff8e1,stroke:#f6a821,stroke-width:2px')
    lines.append(f'style {sid(B)} fill:#fff8e1,stroke:#f6a821,stroke-width:2px')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handler do fluxo (equivalente ao bloco path_search do legado)
# ---------------------------------------------------------------------------

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


# Re-exporta ref_id usado internamente (herdado de upload).
from .upload import ref_id  # noqa: E402
