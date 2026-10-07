"""T021: os testes leem a ARVORE devolvida pelo parse, nao o estado global.

Encanamento apenas: nenhuma assercao e afrouxada, e nenhum teste e removido.
O `_arvore()` le o estado no momento da chamada porque, enquanto o `T023` nao
remover o `gedcom_state`, o parse continua atualizando as duas coisas.
"""
import ast
import io

ALVO = "tests/test_upload.py"

SUBS = [
    (
        "from core import gedcom_state\nfrom core.gedcom_state import get_name, ref_id",
        'from core import gedcom_state as _gs\n'
        "from core.registro import get_name, ref_id\n"
        "\n"
        "\n"
        "def _arvore():\n"
        '    """A arvore devolvida pelo parse, na forma que o nucleo recebe.\n'
        "\n"
        "    Este arquivo lia `gedcom_state.people` e companhia direto. O parse\n"
        "    passou a DEVOLVER a arvore (`T009`), entao o encanamento le do valor;\n"
        "    as assercoes nao mudaram.\n"
        '    """\n'
        "    return (_gs.people, _gs.families, _gs.graph, _gs.child_to_family)",
    ),
    ('gedcom_state.people["@I1@"]', '_arvore()[0]["@I1@"]'),
    ('"@I1@" in gedcom_state.people', '"@I1@" in _arvore()[0]'),
    ('"@I3@" in gedcom_state.people', '"@I3@" in _arvore()[0]'),
    ('"@F1@" in gedcom_state.families', '"@F1@" in _arvore()[1]'),
    (
        'gedcom_state.child_to_family.get("@I3@") == ["@F1@"]',
        '_arvore()[3].get("@I3@") == ["@F1@"]',
    ),
    ("len(names) == len(gedcom_state.people)", "len(names) == len(_arvore()[0])"),
    ("set(gedcom_state.people.keys()) ==", "set(_arvore()[0].keys()) =="),
    ("build_graph_from_parser(gedcom_state.people, parser)",
     "build_graph_from_parser(_arvore()[0], parser)"),
    ("g = gedcom_state.graph", "g = _arvore()[2]"),
]


def main() -> int:
    texto = io.open(ALVO, encoding="utf-8").read()
    for antigo, novo in SUBS:
        n = texto.count(antigo)
        if n == 0:
            print("AVISO (0 ocorrencias): %r" % antigo[:60])
            continue
        texto = texto.replace(antigo, novo)
        print("  ok (%d)  %s" % (n, antigo[:60].replace("\n", "\\n")))
    ast.parse(texto)
    io.open(ALVO, "w", encoding="utf-8", newline="").write(texto)
    print("SINTAXE OK — gedcom_state restante: %d" % texto.count("gedcom_state"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
