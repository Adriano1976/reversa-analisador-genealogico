"""Restaura `carregar_arvore` no parser, MANTENDO a mutacao das globais.

O revert do `T023(a)` levou junto o `carregar_arvore`, que era trabalho nao
commitado e do qual `app.py`, os fluxos e os testes dependem. Aqui ele volta com
a semantica de TRANSICAO: devolve a arvore E atualiza as globais.

E o estado correto para esta altura: o nucleo ja recebe a arvore por parametro
(`T011` a `T021`), e a escrita das globais sai depois que os FIXTURES dos testes
passarem a ler o retorno do parse — em dois movimentos separados, e nao num so.
"""
import ast
import io

ALVO = "src/parsers/gedcom_parser.py"

ANTIGO = '''def load_gedcom_and_build_graph(file_path: str) -> list[str]:
    """Parseia o GEDCOM e devolve a lista de nomes ordenada.

    Substitui o estado: dicionarios in place, grafo reatribuido. Ver `gedcom_state`.
    """
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
'''

NOVO = '''Tree = tuple[dict, dict, "nx.Graph", dict]


def carregar_arvore(file_path: str) -> Tree:
    """Parseia o GEDCOM e devolve a ARVORE como valor (RF-13, D-02).

    A arvore e `(people, families, graph, child_to_family)`, na mesma forma que o
    estado global sempre teve — nenhum campo muda, e a ordem de insercao de cada
    estrutura e preservada, porque ela e contrato de paridade
    (`_reversa_sdd/migration/parity_specs.md` secao 4, tag `@ordem`).

    ## Transicao (D-11)

    Enquanto houver consumidor lendo `core.gedcom_state`, esta funcao **tambem**
    atualiza as globais, e e o unico lugar do projeto que ainda faz isso.

    A escrita das globais sai em `T023`, e a ordem importa: primeiro os FIXTURES
    dos testes passam a ler o retorno do parse, com o parser ainda mutando (suite
    verde o tempo todo); depois a mutacao sai. Fazer as duas no mesmo passo deixa
    a suite vermelha de uma vez — medido em 2026-10-06, 49 falhas.
    """
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
        new_graph, new_child_to_family = build_graph_from_parser(new_people, parser)
'''

ANTIGO_FIM = '''        gedcom_state.versao += 1
        all_names = sorted([get_name(p) for p in gedcom_state.people.values()])
        return all_names
'''

NOVO_FIM = '''        gedcom_state.versao += 1
        return new_people, new_families, new_graph, new_child_to_family


def load_gedcom_and_build_graph(file_path: str) -> list[str]:
    """Parseia o GEDCOM e devolve a lista de nomes ordenada.

    Contrato antigo mantido durante a transicao: `src/app.py` e o coletor do
    harness dependem da lista. Delega para `carregar_arvore`, para haver um so
    lugar que faz o parse.
    """
    people, _families, _graph, _child_to_family = carregar_arvore(file_path)
    return sorted([get_name(p) for p in people.values()])
'''


def main() -> int:
    texto = io.open(ALVO, encoding="utf-8").read()
    for antigo, novo in ((ANTIGO, NOVO), (ANTIGO_FIM, NOVO_FIM)):
        n = texto.count(antigo)
        if n != 1:
            print("ABORTADO: %d ocorrencias de %r" % (n, antigo[:50]))
            return 1
        texto = texto.replace(antigo, novo)
    ast.parse(texto)
    io.open(ALVO, "w", encoding="utf-8", newline="").write(texto)
    print("OK — carregar_arvore restaurado com a mutacao de transicao")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
