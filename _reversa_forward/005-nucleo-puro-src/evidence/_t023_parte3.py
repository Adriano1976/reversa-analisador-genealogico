"""T023 (a): o parse devolve a arvore sem tocar em estado global.

Remove a mutacao in-place e o contador `versao` de `carregar_arvore`, e o import
de `core.gedcom_state` do parser. A partir daqui o parse e uma funcao pura sobre
bytes: le o arquivo e devolve a arvore.

A casca `load_gedcom_and_build_graph` CONTINUA existindo nesta rodada, porque o
coletor do harness ainda a usa; ela passa a ser pura tambem, e sai quando o
coletor migrar (o `T010`, absorvido pelo `T023`).
"""
import ast
import io

ALVO = "src/parsers/gedcom_parser.py"

ANTIGO_IMPORTS = (
    "from core import gedcom_state\n"
    "from core.gedcom_state import get_name, ref_id\n"
)
NOVO_IMPORTS = "from core.registro import get_name, ref_id\n"

ANTIGO_CORPO = '''    ## Transicao (D-11)

    Enquanto houver consumidor lendo `core.gedcom_state`, esta funcao **tambem**
    atualiza as globais, e e o unico lugar do projeto que ainda faz isso. Quando o
    ultimo consumidor migrar (`T011` a `T014`), a escrita das globais sai daqui e
    o modulo de estado e removido (`T023`).
    """
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
        # Mutacao in-place (clear + update) mantem validas as referencias
        # importadas no topo pelos modulos ainda nao migrados. A reatribuicao do
        # grafo e lida por quem o importa dentro da funcao (ver path_finding.py).
        gedcom_state.people.clear(); gedcom_state.people.update(new_people)
        gedcom_state.families.clear(); gedcom_state.families.update(new_families)
        gedcom_state.graph = new_graph
        gedcom_state.child_to_family.clear(); gedcom_state.child_to_family.update(new_child_to_family)
        # Sinal de invalidacao para indices derivados (ver `gedcom_state.versao`).
        gedcom_state.versao += 1
        return new_people, new_families, new_graph, new_child_to_family
'''

NOVO_CORPO = '''    A funcao e PURA sobre o arquivo: nao escreve estado de modulo, e devolve
    dicionarios e grafo NOVOS a cada chamada. Antes ela mutava as globais in place
    para que os consumidores ja importados enxergassem a carga; a feature 005
    tirou os consumidores do estado, e a mutacao saiu com eles.
    """
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
        return new_people, new_families, new_graph, new_child_to_family
'''


def main() -> int:
    texto = io.open(ALVO, encoding="utf-8").read()
    for antigo, novo in ((ANTIGO_IMPORTS, NOVO_IMPORTS), (ANTIGO_CORPO, NOVO_CORPO)):
        n = texto.count(antigo)
        if n != 1:
            print("ABORTADO: %d ocorrencias de %r" % (n, antigo[:60]))
            return 1
        texto = texto.replace(antigo, novo)
    ast.parse(texto)
    io.open(ALVO, "w", encoding="utf-8", newline="").write(texto)
    print("OK — gedcom_state no parser: %d" % texto.count("gedcom_state"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
