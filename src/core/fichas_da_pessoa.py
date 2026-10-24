"""A ficha comparavel de uma pessoa da arvore, e o indice pai para filhos.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). A ficha serve para
desambiguar homonimos; o indice pai para filhos evita varrer todas as familias a cada ficha.
Nenhuma das duas sabe o que e parentesco documental.
"""
from __future__ import annotations

from .datas_do_gedcom import birth_date, birth_place, death_date, parse_year
from .family_navigation import get_parents
from .registro import get_name, ref_id

# ---------------------------------------------------------------------------
# Ficha comparavel da pessoa
# ---------------------------------------------------------------------------

def ids_com_tag(people, sub_tag, pid):
    return [ref_id(r.value) for r in people[pid].sub_records if r.tag == sub_tag] if pid in people else []


#: Nome do atributo privado onde o indice pai -> filhos fica preso ao GRAFO da
#: arvore. Nao e estado de modulo: o indice nasce e morre com a arvore daquela
#: requisicao, entao nao ha retencao entre requisicoes nem chave de conteudo
#: para colidir (o problema do L-24). Duas threads que compartilhem a mesma
#: arvore montam o mesmo mapa; a atribuicao e atomica e o mapa e somente leitura.
_ATRIBUTO_DE_FILHOS = "_indice_de_filhos_do_documental"


def _construir_indice_de_filhos(families) -> dict:
    """Pai -> filhos, na ordem em que a varredura de familias os encontra.

    Reproduz `get_children` de antes: percorre as familias na ordem do dicionario,
    acrescenta os filhos de cada familia ao pai e a mae e deduplica por pessoa. A
    ordem e contrato observavel, por isso a construcao nao reordena nada.
    """
    mapa = {}
    for fam in families.values():
        husb = wife = None
        filhos = []
        for rec in fam.sub_records:
            tag = rec.tag
            if tag == "HUSB":
                husb = ref_id(rec.value)
            elif tag == "WIFE":
                wife = ref_id(rec.value)
            elif tag == "CHIL":
                filhos.append(rec.value)
        for pai in (husb, wife):
            if not pai:
                continue
            destino = mapa.setdefault(pai, [])
            for valor in filhos:
                cid = ref_id(valor)
                if cid not in destino:
                    destino.append(cid)
    return mapa


def _indice_de_filhos(arvore) -> dict:
    """O indice da arvore, montado uma vez e preso ao grafo dela."""
    grafo = arvore[2]
    mapa = getattr(grafo, _ATRIBUTO_DE_FILHOS, None)
    if mapa is None:
        mapa = _construir_indice_de_filhos(arvore[1])
        setattr(grafo, _ATRIBUTO_DE_FILHOS, mapa)
    return mapa


def get_children(arvore, person_id):
    """Filhos declarados em qualquer familia em que a pessoa seja HUSB ou WIFE."""
    return list(_indice_de_filhos(arvore).get(person_id, []))


def person_summary(arvore, person_id) -> dict:
    """Ficha comparavel de uma pessoa, para desambiguar homonimos."""
    people = arvore[0]
    birth = birth_date(people, person_id)
    death = death_date(people, person_id)
    parents = get_parents(arvore, person_id)
    return {
        "id": person_id,
        "name": get_name(people.get(person_id)),
        "sex": next((r.value for r in people[person_id].sub_records if r.tag == "SEX"), None) if person_id in people else None,
        "birth": birth,
        "birth_year": parse_year(birth),
        "birth_place": birth_place(people, person_id),
        "death": death,
        "death_year": parse_year(death),
        "parents": parents,
        "parent_names": [get_name(people.get(p)) for p in parents],
        "spouses": ids_com_tag(people, "FAMS", person_id),
        "children": get_children(arvore, person_id),
        "family_as_child": arvore[3].get(person_id, []),
    }

__all__ = ["get_children", "person_summary", "ids_com_tag"]
