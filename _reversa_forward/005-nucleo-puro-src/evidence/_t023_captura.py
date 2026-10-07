"""T023 (b2): captura automatica da arvore devolvida pelo parse.

## Por que a captura no chamador nao bastou

O `(b)` fez cada helper de carga guardar o retorno. Metade dos testes continuou
falhando com `[] != ['@I10@']`, que e o sintoma de `atual()` lido antes de
qualquer `guardar` — varios testes chamam o parse direto, sem passar pelo helper
do arquivo, e eu teria de acertar todos os pontos um a um.

A captura no MODULO DO PARSER resolve na raiz: toda chamada de `carregar_arvore`
guarda o resultado, venha de onde vier. E o mesmo comportamento que as globais
mutadas davam — "depois de carregar, a ultima arvore esta disponivel" — sem
estado de dominio, porque o que se guarda e o VALOR que a funcao devolveu.

O `gedcom_parser` continua puro: ele nao le a arvore guardada. Quem le e o teste.
"""
import ast
import io

ALVO = "src/parsers/gedcom_parser.py"

ANTIGO = '''    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
        return new_people, new_families, new_graph, new_child_to_family
'''

NOVO = '''    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
        arvore = (new_people, new_families, new_graph, new_child_to_family)
        # Observabilidade da ULTIMA carga, para quem precisa da arvore depois de
        # chama-la (os testes). Nao e estado de dominio: e o registro do valor
        # que esta chamada acabou de devolver — o equivalente ao que a mutacao
        # in-place das globais oferecia, sem manter estrutura viva.
        global ULTIMA_ARVORE
        ULTIMA_ARVORE = arvore
        return arvore
'''

CABECA = '''Tree = tuple[dict, dict, "nx.Graph", dict]

# A arvore da ultima chamada de `carregar_arvore`. Ver a nota no corpo: e
# observabilidade do retorno, nao estado de dominio.
ULTIMA_ARVORE = None
'''


def main() -> int:
    texto = io.open(ALVO, encoding="utf-8").read()
    for antigo, novo in ((ANTIGO, NOVO),
                         ('Tree = tuple[dict, dict, "nx.Graph", dict]\n', CABECA)):
        n = texto.count(antigo)
        if n != 1:
            print("ABORTADO: %d ocorrencias de %r" % (n, antigo[:50]))
            return 1
        texto = texto.replace(antigo, novo)
    ast.parse(texto)
    io.open(ALVO, "w", encoding="utf-8", newline="").write(texto)
    print("OK — parser guarda a ultima arvore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
