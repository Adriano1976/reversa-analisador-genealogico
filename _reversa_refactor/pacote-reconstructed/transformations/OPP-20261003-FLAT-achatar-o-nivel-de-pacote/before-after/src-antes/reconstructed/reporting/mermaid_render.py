"""Emissao do diagrama Mermaid e o contrato de escape do rotulo.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica:
transformar um caminho de parentesco no texto do diagrama.

Este e o modulo onde o contrato de escape vive. `_LABEL_SEGURO` e a lista branca
que substituiu a lista negra furada pela crase, e o comentario que a documenta
veio junto com ela. Ver BUG-20260929-J6PQ.
"""
from __future__ import annotations

import re
import unicodedata
from contextlib import contextmanager

from ..core.family_navigation import (
    exclude_tail,
    get_spouses,
    pick_spouse_for_couple,
    split_path_by_marriage,
)
from ..core.path_finding import find_ancestral_path
from ..core.gedcom_state import get_name, people


def _mermaid_sid(raw) -> str:
    """Identificador de no Mermaid: apenas [A-Za-z0-9_], prefixado com N_."""
    if isinstance(raw, (list, tuple, set)):
        raw = next(iter(raw), "")
    safe_str = str(raw).replace('@', '').replace('+', '_')
    return 'N_' + re.sub(r'[^a-zA-Z0-9_]', '', safe_str)


# Caracteres que podem sobreviver num rotulo entre aspas do Mermaid. A gramatica
# do flowchart prova que, dentro do estado `string`, o lexer consome tudo com
# `<string>[^"]+`, entao colchete, dois pontos, barra e palavra-chave sao inertes.
# O que nao pode passar e a aspa dupla, que encerra o rotulo, e a crase, que logo
# apos a aspa de abertura desvia o lexer para markdown-string e faz o
# fecha-colchete nunca virar o token que a gramatica exige.
# Lista branca, e nao negra: a negra anterior foi furada justamente pela crase.
#
# A amplitude segue o criterio de INERTE, e nao o de "seguro": tudo que a
# gramatica tolera dentro das aspas e que o legado preservava continua passando.
# A versao anterior desta lista era estreita demais e descartava 14 caracteres
# sem que isso fosse pretendido. Ver BUG-20261002-T4ZM.
#
_LABEL_SEGURO = re.compile(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ .,'()&<>:;/\[\]!?@#$%*+=^_{|}~\\-]")


def _mermaid_label(txt) -> str:
    """Rotulo de no Mermaid: NFC, lista branca de caracteres seguros, com &, < e > em entidade."""
    s = unicodedata.normalize("NFC", str(txt))
    s = (s.replace('\u00A0', ' ')
           .replace('\u2013', '-')
           .replace('\u2014', '-')
           .replace('\u201c', "'").replace('\u201d', "'").replace('\u2019', "'"))
    s = s.replace('"', "'")
    s = re.sub(r'[\r\n]+', ' ', s)
    s = _LABEL_SEGURO.sub('', s)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def generate_mermaid_graph(path, p1_id, p2_id, common_ancestor_id):
    sid, lab = _mermaid_sid, _mermaid_label

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
    sid, lab = _mermaid_sid, _mermaid_label

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
    couple1_label = None
    if spouse_ca1:
        couple1_id = sid("+".join(sorted([str(ca1), str(spouse_ca1)])))
        couple1_label = f'{lab(get_name(people.get(ca1)))} &amp; {lab(get_name(people.get(spouse_ca1)))}'

    lines = ["flowchart BT"]
    seen = set()

    @contextmanager
    def subgrafo(header):
        """Abre o subgrafo, escreve a direcao e o fecha ao fim do bloco.

        O fechamento deixa de ser uma linha que alguem precisa posicionar no meio
        do fluxo: ele e o fim do `with`. Um `end` a mais ou a menos muda a arvore
        do diagrama sem levantar erro nenhum, e era exatamente esse o risco
        registrado na OPP-20260929-H2YY.

        Sem try/finally de proposito: `end` so e escrito se o corpo terminar, que
        e o comportamento da sequencia de append que este helper substitui.
        """
        lines.append("subgraph %s" % header)
        lines.append("direction BT")
        yield
        lines.append("end")

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

    def emit_couple_or_ancestor(couple_id, couple_label, ca, left_col, right_col):
        """Emite o par de conjuge, ou o ancestral quando nao ha par, e liga as colunas.

        O destino das setas difere entre os dois casos: o par ja chega como id de
        no, e o ancestral ainda precisa passar por `sid`. Assumir que o mesmo id
        serve para os dois muda a saida nos casos com conjuge.
        """
        if couple_id:
            lines.append(f'{couple_id}["{couple_label}"]')
            alvo = couple_id
        else:
            add_node(ca)
            alvo = sid(ca)
        if left_col:
            lines.append(f'{sid(left_col[-1])} --> {alvo}')
        if right_col:
            lines.append(f'{sid(right_col[-1])} --> {alvo}')

    with subgrafo("COLUMNS"):
        with subgrafo("ESQ[Ramo 1]"):
            with subgrafo("ESQ_COLS"):
                left_col_r1 = exclude_tail(r1_down, n=1)
                right_col_r1 = exclude_tail(r1_up_from_A, n=1)

                if left_col_r1:
                    with subgrafo("ESQ_L[ ]"):
                        add_chain(left_col_r1)
                if right_col_r1:
                    with subgrafo("ESQ_R[ ]"):
                        add_chain(right_col_r1)

            emit_couple_or_ancestor(couple1_id, couple1_label, ca1, left_col_r1, right_col_r1)

        if is_direct_connection_to_p2:
            with subgrafo("DIR[Ramo 2]"):
                add_node(p2_id)
            right_col_r2 = []
            couple2_id, ca2 = None, None
        else:
            path_p2_B, ca2 = find_ancestral_path(p2_id, B)
            if not path_p2_B:
                return generate_mermaid_graph(person_path, p1_id, p2_id, None)

            spouse_ca2 = pick_spouse_for_couple(ca2, candidate_path=path_p2_B)
            r2_down, r2_up_from_B = split_at(path_p2_B, ca2)

            couple2_id = None
            couple2_label = None
            if spouse_ca2:
                couple2_id = sid("+".join(sorted([str(ca2), str(spouse_ca2)])))
                couple2_label = f'{lab(get_name(people.get(ca2)))} &amp; {lab(get_name(people.get(spouse_ca2)))}'

            with subgrafo("DIR[Ramo 2]"):
                with subgrafo("DIR_COLS"):
                    left_col_r2 = exclude_tail(r2_up_from_B, n=1)
                    right_col_r2 = exclude_tail(r2_down, n=1)

                    if left_col_r2:
                        with subgrafo("DIR_L[ ]"):
                            add_chain(left_col_r2)
                    if right_col_r2:
                        with subgrafo("DIR_R[ ]"):
                            add_chain(right_col_r2)

                emit_couple_or_ancestor(couple2_id, couple2_label, ca2, left_col_r2, right_col_r2)

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
