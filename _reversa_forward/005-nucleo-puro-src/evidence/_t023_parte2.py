"""T023, parte 2: remover `_arvore_global` e as ultimas referencias a `people`.

Depois do `T020`, ninguem chama `_arvore_global`: os fluxos recebem `arvore` por
parametro. A funcao sobreviveu porque o `T018` consolidou tres copias em uma — e
uma copia orfa ainda e um ponto de esquecimento. Aqui ela sai, junto com
`_chave_da_arvore`, que so existia para servi-la.

Tambem conserta as referencias a `people` que sobraram em `path_search` e
`dna_analysis`: os dois recebem `arvore`, entao leem `arvore[0]`.
"""
import ast
import io

# Bloco exato a remover de documentary_relationship (do comentario ate o fim da
# segunda funcao). Mantemos o dicionario do indice.
BLOCO = '''_ARVORE_CACHE = {"chave": None, "arvore": None}


def _chave_da_arvore():
    pessoas = gedcom_state.people
    if not pessoas:
        return (0, 0, 0, None, None)
    chaves = sorted(pessoas)
    return (len(pessoas), len(gedcom_state.families),
            len(gedcom_state.child_to_family), chaves[0], chaves[-1])


def _arvore_global():
    """A arvore, enquanto ela ainda vive em `gedcom_state`. Ver `T023`.

    Memoizada pela chave derivada do conteudo: uma mesma analise monta a tupla
    uma vez, e nao a cada chamada.
    """
    chave = _chave_da_arvore()
    if _ARVORE_CACHE["chave"] != chave:
        _ARVORE_CACHE["arvore"] = (
            gedcom_state.people,
            gedcom_state.families,
            gedcom_state.graph,
            gedcom_state.child_to_family,
        )
        _ARVORE_CACHE["chave"] = chave
    return _ARVORE_CACHE["arvore"]


'''

TROCAS = [
    ("src/core/documentary_relationship.py", [
        (BLOCO, ""),
        # a chave do indice passa a ser derivada do proprio dicionario recebido
        ("    chave = _chave_da_arvore()\n", "    chave = _chave_de(people)\n"),
    ]),
    ("src/core/path_search.py", [
        ("        nomes = [get_name(people[n]) for n in person_path]",
         "        nomes = [get_name(arvore[0][n]) for n in person_path]"),
    ]),
    ("src/core/dna_analysis.py", [
        ("    root_person_ids = [pid for pid, p in people.items() if root_name.lower() in get_name(p).lower()]",
         "    root_person_ids = [pid for pid, p in arvore[0].items()\n                       if root_name.lower() in get_name(p).lower()]"),
        ('                "match_name": get_name(people[pid]),',
         '                "match_name": get_name(arvore[0][pid]),'),
    ]),
]

# A funcao de chave que substitui a antiga, derivada do valor recebido.
CHAVE = '''

def _chave_de(people) -> tuple:
    """Chave de invalidacao do indice, derivada do CONTEUDO recebido.

    A identidade do dicionario NAO serve: o parse muta `people` in place, entao o
    `id()` e o mesmo durante todo o processo e o cache nunca invalidaria (medido
    em 2026-10-06, e cobrado por `test_6d`). A chave usa contagem, primeira e
    ultima chave — barato e suficiente para distinguir dois GEDCOMs carregados.
    """
    if not people:
        return (0, None, None)
    chaves = sorted(people)
    return (len(people), chaves[0], chaves[-1])

'''


def main() -> int:
    for caminho, subs in TROCAS:
        texto = io.open(caminho, encoding="utf-8").read()
        for antigo, novo in subs:
            n = texto.count(antigo)
            if n == 0:
                print("AVISO (0): %s :: %r" % (caminho, antigo[:60].replace("\n", "\\n")))
                continue
            texto = texto.replace(antigo, novo)
            print("  ok (%d)  %s" % (n, caminho))
        if caminho.endswith("documentary_relationship.py") and "_chave_de" not in texto:
            texto = texto.replace("\n_INDICE_DE_NOMES = ", CHAVE + "\n_INDICE_DE_NOMES = ", 1)
        ast.parse(texto)
        io.open(caminho, "w", encoding="utf-8", newline="").write(texto)
    for caminho in ("src/core/documentary_relationship.py", "src/core/path_search.py",
                    "src/core/dna_analysis.py"):
        t = io.open(caminho, encoding="utf-8").read()
        print("%-45s gedcom_state=%d _arvore_global=%d"
              % (caminho, t.count("gedcom_state"), t.count("_arvore_global")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
