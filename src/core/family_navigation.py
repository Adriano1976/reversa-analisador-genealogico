"""Quem e parente de quem, numa arvore recebida por parametro.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica:
resolver uma pessoa pelo nome e navegar as ligacoes de familia (pais, conjuge,
casamento, afinidade). Nao conhece caminho, nao conhece diagrama.

## A arvore entra por parametro (feature 005, T011)

Ate a feature 005 este modulo lia `people`, `families` e `child_to_family` de
`core.gedcom_state`, que eram mutados in place pelo parse para que o binding do
topo continuasse apontando para o objeto vivo. Agora a arvore chega como
`Arvore = (people, families, graph, child_to_family)`, do mesmo jeito que o parse
a devolve (`parsers.gedcom_parser.carregar_arvore`).

O parametro se chama `arvore` e vem PRIMEIRO em toda funcao que precisa dele.
As funcoes que nao precisam — `split_path_by_marriage` e `exclude_tail`, que
operam sobre uma lista de ids — nao o recebem: passar o que nao se usa e ruido, e
o objetivo aqui e dependencia explicita, nao assinatura uniforme.

## Assimetria historica que deixou de existir

`graph` era a excecao do estado: reatribuido a cada parse, e por isso quem o
consumia precisava importa-lo dentro da funcao. Com a arvore como valor, a
assimetria sumiu — quem precisa do grafo o pega da arvore recebida.
"""
from __future__ import annotations

from .registro import get_name, ref_id

# Forma da arvore, identica a devolvida por `carregar_arvore`: `dict`, `dict`,
# `nx.Graph`, `dict` de listas. A ordem de insercao de cada estrutura e contrato
# de paridade (tag `@ordem` de `parity_specs.md` secao 4) e nao pode mudar.
Arvore = tuple


def _partes(arvore: Arvore):
    people, families, _graph, child_to_family = arvore
    return people, families, child_to_family


def find_person_by_name(arvore: Arvore, name_query):
    """Exact match (case-insensitive) primeiro; depois substring."""
    people = arvore[0]
    exact = [pid for pid, p in people.items() if name_query.lower() == get_name(p).lower()]
    if exact:
        return exact
    return [pid for pid, p in people.items() if name_query.lower() in get_name(p).lower()]


def get_parents(arvore: Arvore, person_id):
    """Pais de uma pessoa via FAMC ou índice filho->famílias."""
    people, families, child_to_family = _partes(arvore)
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


def get_spouses(arvore: Arvore, person_id):
    """Cônjuges de uma pessoa via registros FAMS; fallback por varredura.

    A varredura por TODAS as familias so roda quando a via FAMS nao devolve nada.
    E contrato aceito desde 2026-09-30 e nao deve ser "complementado": tornar a
    varredura sempre ativa muda o resultado (o conjuge de uma segunda familia
    passa a aparecer). Ver `_reversa_sdd/busca-caminho/design.md`.
    """
    people, families, _child_to_family = _partes(arvore)
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


def are_spouses(arvore: Arvore, a_id, b_id) -> bool:
    return b_id in set(get_spouses(arvore, a_id))


def split_path_by_marriage(arvore: Arvore, person_path):
    """Encontra o 1º par de cônjuges adjacentes no caminho indireto.

    Recebe a arvore porque a pergunta "estes dois sao conjuges?" e do dominio, e
    `are_spouses` a responde. O RISK-011 existe exatamente aqui: nenhum cenario
    de matching falharia se esta decomposicao desaparecesse, porque o matching
    continuaria correto. Por isso ela tem probe diferencial dedicado.
    """
    for i in range(len(person_path) - 1):
        a, b = person_path[i], person_path[i + 1]
        if are_spouses(arvore, a, b):
            left = person_path[:i + 1]      # ... → A
            right = person_path[i + 1:]     # B → ...
            return left, right, (a, b)
    return None, None, None


def pick_spouse_for_couple(arvore: Arvore, person_id, candidate_path=None):
    """Escolhe um cônjuge para formar o 'casal' no topo do ramo."""
    spouses = get_spouses(arvore, person_id) or []
    if candidate_path:
        seen = set(candidate_path)
        for s in spouses:
            if s in seen:
                return s
    return spouses[0] if spouses else None


def exclude_tail(seq, n=1):
    """Retorna seq sem os últimos n elementos (evita duplicar o ancestral na ponta).

    Nao recebe a arvore: opera sobre uma sequencia de ids e nada mais.
    """
    return seq[:-n] if len(seq) > n else []
