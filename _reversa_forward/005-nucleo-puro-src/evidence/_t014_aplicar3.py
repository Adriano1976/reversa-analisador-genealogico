"""Terceira parte do T014: os ultimos leitores de estado."""
import io

ALVO = r"src/core/documentary_relationship.py"

SUBS = [
    # get_children: navega familias
    ("def get_children(arvore, person_id):", "def get_children(arvore, person_id):"),
    ("    for fam in families.values():", "    people, families = arvore[0], arvore[1]\n    for fam in families.values():"),
    ('"family_as_child": child_to_family.get(person_id, []),', '"family_as_child": arvore[3].get(person_id, []),'),

    # _dossie: le people para separar o id do rotulo
    ("def _ids(people, sub_tag, pid):", "def _ids(people, sub_tag, pid):"),

    # hop_evidence: recebe people
    ("def hop_evidence(arvore, child_id, parent_id) -> dict:",
     "def hop_evidence(arvore, child_id, parent_id) -> dict:"),
    ("        candidata = families.get(famc)", "        families = arvore[1]\n        candidata = families.get(famc)"),
    ("        for fam_id in child_to_family.get(child_id, []):",
     "        for fam_id in arvore[3].get(child_id, []):"),
    ("            fam = families.get(fam_id)", "            fam = families.get(fam_id)"),
    ("        fam = families.get(familia_id)", "        fam = arvore[1].get(familia_id)"),
    ('"child_name": get_name(people.get(child_id)),', '"child_name": get_name(arvore[0].get(child_id)),'),
    ('"parent_name": get_name(people.get(parent_id)),', '"parent_name": get_name(arvore[0].get(parent_id)),'),
    ('"family_husband": {"id": husb, "name": get_name(people.get(husb))} if husb else None,',
     '"family_husband": {"id": husb, "name": get_name(arvore[0].get(husb))} if husb else None,'),
    ('"family_wife": {"id": wife, "name": get_name(people.get(wife))} if wife else None,',
     '"family_wife": {"id": wife, "name": get_name(arvore[0].get(wife))} if wife else None,'),

    # documentary_relationship: guarda de presenca
    ("    if a_id not in people or b_id not in people:", "    if a_id not in arvore[0] or b_id not in arvore[0]:"),

    # docstring do indice
    ("    `gedcom_state.versao`, e nao o tamanho de `people`: dois GEDCOMs diferentes\n    podem ter a mesma contagem.",
     "    a IDENTIDADE do dicionario de pessoas recebido, e nao um contador\n    (`gedcom_state.versao`, removido pela feature 005): dois GEDCOMs diferentes\n    podem ter a mesma contagem, e um contador exigiria estado."),
]


def main() -> int:
    texto = io.open(ALVO, encoding="utf-8").read()
    for antigo, novo in SUBS:
        if antigo == novo:
            continue
        n = texto.count(antigo)
        if n == 0:
            print("AVISO (0): %r" % antigo[:70])
            continue
        texto = texto.replace(antigo, novo)
        print("  ok (%d)  %s" % (n, antigo[:70]))
    io.open(ALVO, "w", encoding="utf-8", newline="").write(texto)
    restos = [l for l in texto.splitlines()
              if ("people" in l or "families" in l or "child_to_family" in l)
              and "arvore" not in l and "def " not in l and "from " not in l
              and "#" not in l and "gedcom_state" not in l]
    print("--- linhas suspeitas de ainda ler o global ---")
    print("\n".join(restos) or "(nenhuma)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
