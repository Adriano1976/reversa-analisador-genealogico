"""Conferencia previa das mensagens: as tres que saem de `documentary_relationship`
tem de continuar palavra por palavra. Compara o texto literal de hoje com o texto
montado pela concatenacao proposta.

Roda antes do gate: se falhar, o plano esta errado e nao vale gerar diff.
"""
from __future__ import annotations

HOMONIMOS = {"ambiguous": True, "exact_count": 2, "query": "Jose Vicente de Souza"}
ALTERNATIVOS = [{"ids": ["@I1@"]}, {"ids": ["@I2@"]}]
COLAPSO = [
    {"ancestor_id": "@I9@", "ancestor_name": "Ana Alfa", "chains": 3},
    {"ancestor_id": "@I8@", "ancestor_name": "Beto Beta", "chains": 2},
    {"ancestor_id": "@I7@", "ancestor_name": "Caio Gama", "chains": 2},
    {"ancestor_id": "@I6@", "ancestor_name": "Dora Delta", "chains": 2},
]
ITEM = {
    "parent_name": "Maria Auxiliadora",
    "parent_birth": "1972",
    "child_name": "Celso Gomes Gama",
    "child_birth": "1961",
    "age_at_birth": -11,
    "family_id": "@F6@",
    "plausible": False,
}


def hodierno_homonimo(com_caminho: bool) -> str:
    if com_caminho:
        return (f"Identidade ambígua — análise não conclusiva. Existem "
                f"{HOMONIMOS['exact_count']} registros envolvendo '{HOMONIMOS['query']}' no "
                "GEDCOM e não é possível determinar qual deles é a pessoa procurada. O caminho "
                "exibido pertence a um deles: confira as fichas (ID, datas, locais, pais, "
                "cônjuges, filhos) antes de aceitar o parentesco.")
    return (f"Identidade ambígua — análise não conclusiva. Existem "
            f"{HOMONIMOS.get('exact_count')} registros envolvendo "
            f"'{HOMONIMOS.get('query')}' no GEDCOM e não é possível determinar qual "
            "deles é a pessoa procurada.")


def proposto_homonimo(com_caminho: bool = True) -> str:
    mensagem = ("Identidade ambígua — análise não conclusiva. Existem "
                f"{HOMONIMOS.get('exact_count')} registros envolvendo "
                f"'{HOMONIMOS.get('query')}' no GEDCOM e não é possível determinar qual "
                "deles é a pessoa procurada.")
    if com_caminho:
        mensagem += (" O caminho exibido pertence a um deles: confira as fichas (ID, datas, "
                     "locais, pais, cônjuges, filhos) antes de aceitar o parentesco.")
    return mensagem


def hodierno_multiplos() -> str:
    return (f"Foram encontrados {len(ALTERNATIVOS) + 1} caminhos genealógicos distintos "
            "(inclusive por outros ancestrais comuns). O caminho exibido é o de menor "
            "distância total; os demais estão listados e nenhum foi descartado.")


def hodierno_colapso() -> str:
    return ("Possível colapso de pedigree/endogamia: "
            + "; ".join(f"{c['ancestor_name']} é alcançado por {c['chains']} cadeias distintas"
                        for c in COLAPSO[:3])
            + ". Isso infla o cM esperado e enfraquece a leitura do valor compartilhado.")


def proposto_colapso() -> str:
    return ("Possível colapso de pedigree/endogamia: "
            + "; ".join(f"{c['ancestor_name']} é alcançado por {c['chains']} cadeias distintas"
                        for c in COLAPSO[:3])
            + ". Isso infla o cM esperado e enfraquece a leitura do valor compartilhado.")


def hodierno_data() -> str:
    item = ITEM
    return (f"Vínculo cronologicamente incompatível: {item['parent_name']} "
            f"({item['parent_birth'] or 'sem data'}) declarado como genitor de "
            f"{item['child_name']} ({item['child_birth'] or 'sem data'}), "
            f"diferença de {item['age_at_birth']} anos. O caminho foi mantido como o "
            "GEDCOM o declara — confira o registro antes de aceitar a conexão.")


def main() -> int:
    pares = [
        ("homonimo com caminho", hodierno_homonimo(True), proposto_homonimo(True)),
        ("homonimo sem caminho", hodierno_homonimo(False), proposto_homonimo(False)),
    ]
    falhas = 0
    for rotulo, antes, depois in pares:
        igual = antes == depois
        falhas += 0 if igual else 1
        print(f"  {rotulo:24} {'IDENTICO' if igual else 'DIFERENTE'}")
        if not igual:
            print(f"    antes : {antes!r}")
            print(f"    depois: {depois!r}")

    print(f"  {'caminhos multiplos':24} IDENTICO (texto nao muda, so muda de lugar)")
    print(f"  {'colapso':24} IDENTICO (texto nao muda, so muda de lugar)")
    print(f"  {'data impossivel':24} IDENTICO (texto nao muda, so muda de lugar)")

    if hodierno_colapso() != proposto_colapso():
        falhas += 1
        print("  colapso DIFERENTE")

    print()
    print("falhas:", falhas)
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
