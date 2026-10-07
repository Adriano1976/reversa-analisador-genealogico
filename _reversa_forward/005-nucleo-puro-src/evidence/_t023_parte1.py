"""T023, parte 1: tirar de `gedcom_state` quem so precisava de `get_name`.

`get_name` e `ref_id` sao funcoes de REGISTRO e vivem em `core/registro.py`
desde o `T008`. Os modulos abaixo ainda as importavam do modulo de estado, o que
os mantinha dependentes dele sem precisar. Aqui a dependencia cai para o modulo
canonico, e a guarda de estado fica mais perto de poder passar.

Encanamento apenas: nenhuma assercao, nenhum comportamento.
"""
import ast
import io

TROCAS = [
    # dna_analysis: o unico uso real era `get_name`; `gedcom_state` so servia ao
    # `_arvore_global`, que o T020 ja deixou sem uso.
    (
        "src/core/dna_analysis.py",
        [
            ("from .gedcom_state import get_name, people\nfrom . import gedcom_state\n",
             "from .registro import get_name\n"),
        ],
    ),
    # path_search: idem.
    (
        "src/core/path_search.py",
        [
            ("from .gedcom_state import get_name, people\nfrom . import gedcom_state\n",
             "from .registro import get_name\n"),
        ],
    ),
    # documentary_relationship: consome os quatro + ref_id. `people` e `families`
    # ainda aparecem nos auxiliares `_data_de`/`_local_de`/`_ids`, que recebem
    # `people` por parametro — o import do topo so serve ao `_arvore_global`.
    (
        "src/core/documentary_relationship.py",
        [
            ("from . import gedcom_state\n", ""),
            ("from .gedcom_state import child_to_family, families, get_name, people, ref_id\n",
             "from .registro import get_name, ref_id\n"),
        ],
    ),
]


def main() -> int:
    for caminho, subs in TROCAS:
        texto = io.open(caminho, encoding="utf-8").read()
        for antigo, novo in subs:
            n = texto.count(antigo)
            if n != 1:
                print("ABORTADO %s: %d ocorrencias de %r" % (caminho, n, antigo[:50]))
                return 1
            texto = texto.replace(antigo, novo)
        ast.parse(texto)
        io.open(caminho, "w", encoding="utf-8", newline="").write(texto)
        print("  ok  %s  (gedcom_state: %d)" % (caminho, texto.count("gedcom_state")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
