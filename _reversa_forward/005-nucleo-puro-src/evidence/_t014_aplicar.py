"""Aplica a migracao do T014 (feature 005) com substituicoes exatas.

Script de uso unico. Aborta se qualquer padrao nao casar, e informa a contagem
de cada substituicao, para que nenhuma alteracao passe silenciosamente.
"""
import io
import sys

ALVO = r"src/core/documentary_relationship.py"

SUBS = [
    # --- helpers que leem so `people` -------------------------------------
    ("def _data_de(pid, tag):", "def _data_de(people, pid, tag):"),
    ("def birth_date(pid):\n    return _data_de(pid, \"BIRT\")",
     "def birth_date(people, pid):\n    return _data_de(people, pid, \"BIRT\")"),
    ("def death_date(pid):\n    return _data_de(pid, \"DEAT\")",
     "def death_date(people, pid):\n    return _data_de(people, pid, \"DEAT\")"),
    ("def _local_de(pid, tag):", "def _local_de(people, pid, tag):"),
    ("def _ids(sub_tag, pid):", "def _ids(people, sub_tag, pid):"),

    # --- fichas -----------------------------------------------------------
    ("def get_children(person_id):", "def get_children(arvore, person_id):"),
    ("def person_summary(person_id) -> dict:", "def person_summary(arvore, person_id) -> dict:"),
    ('"name": get_name(people.get(person_id))', '"name": get_name(arvore[0].get(person_id))'),
    ('"sex": next((r.value for r in people[person_id].sub_records if r.tag == "SEX"), None) if person_id in people else None',
     '"sex": next((r.value for r in arvore[0][person_id].sub_records if r.tag == "SEX"), None) if person_id in arvore[0] else None'),
    ('"birth": birth_date(person_id)', '"birth": birth_date(arvore[0], person_id)'),
    ('"birth_year": parse_year(birth_date(person_id))', '"birth_year": parse_year(birth_date(arvore[0], person_id))'),
    ('"death": death_date(person_id)', '"death": death_date(arvore[0], person_id)'),
    ('"death_year": parse_year(death_date(person_id))', '"death_year": parse_year(death_date(arvore[0], person_id))'),
    ('"parents": get_parents(_arvore_global(), person_id)', '"parents": get_parents(arvore, person_id)'),
    ('"parent_names": [get_name(people.get(p)) for p in get_parents(_arvore_global(), person_id)]',
     '"parent_names": [get_name(arvore[0].get(p)) for p in get_parents(arvore, person_id)]'),
    ('"children": get_children(person_id)', '"children": get_children(arvore, person_id)'),

    # --- indice de nomes e dossie -----------------------------------------
    ("def _indice_por_nome() -> dict:", "def _indice_por_nome(arvore) -> dict:"),
    ("def homonym_dossier(name_query: str, similar_ids=None) -> dict:",
     "def homonym_dossier(arvore, name_query: str, similar_ids=None) -> dict:"),
    ("fichas = [person_summary(i) for i in ids]", "fichas = [person_summary(arvore, i) for i in ids]"),
    ("fichas = [person_summary(pid) for pid in exatos]", "fichas = [person_summary(arvore, pid) for pid in exatos]"),
    ('"similar_matches": [person_summary(pid) for pid in parecidos[:5]],',
     '"similar_matches": [person_summary(arvore, pid) for pid in parecidos[:5]],'),

    # --- evidencia de salto -----------------------------------------------
    ("def hop_evidence(child_id, parent_id) -> dict:", "def hop_evidence(arvore, child_id, parent_id) -> dict:"),
]

def main() -> int:
    texto = io.open(ALVO, encoding="utf-8").read()
    for antigo, novo in SUBS:
        n = texto.count(antigo)
        if n != 1:
            print("ABORTADO: padrao com %d ocorrencias (esperado 1): %r" % (n, antigo[:70]))
            return 1
        texto = texto.replace(antigo, novo)
        print("  ok  %s" % antigo[:70].replace("\n", "\\n"))
    io.open(ALVO, "w", encoding="utf-8", newline="").write(texto)
    print("APLICADO: %d substituicoes" % len(SUBS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
