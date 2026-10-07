"""`T020`: varredura de que `index()` nao orquestra mais nada de dominio.

## A pergunta

`RF-01` cobra que `index()` nao contenha sequencia de passos de dominio â€”
"nenhuma chamada a parser, agregador de CSV ou resolvedor de diagrama permanece no
`app.py`". Ler o arquivo a olho nao prova isso; esta varredura prova por AST, que
e o mesmo metodo das guardas de `tests/test_dependencias_nucleo.py`.

## A distincao que a varredura precisa fazer

`read_csv_with_fallback`, `detectar_colunas`, `aggregate_matches` e as duas
funcoes de diagrama **continuam importadas** no `app.py` â€” e devem continuar: a
`RF-09`/`D-05` manda a BORDA monta-las no pacote `Dependencias` e injeta-lo. O que
nao pode existir e CHAMADA de dominio. Entao a varredura procura chamadas, e
verifica que a unica ocorrencia de cada uma dessas funcoes e dentro da expressao
`Dependencias(...)`, que e montagem de dependencia, nao passo de dominio.

## O que ela NAO prova

Nao prova que o comportamento esta certo â€” para isso existe a sonda diferencial de
mensagens e a paridade. Prova FORMA, que e a pergunta do `T020`.
"""
from __future__ import annotations

import ast
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
CAMINHO = os.path.join(RAIZ, "src", "app.py")

# Simbolos que a rota NAO pode chamar. Cada um foi, antes da extracao, um passo de
# dominio dentro de `index()`.
DOMINIO_PROIBIDO = {
    "carregar_arvore": "parse do GEDCOM",
    "load_gedcom_and_build_graph": "casca removida em T015",
    "resolvedor_de_diagrama": "resolucao do dominio de diagrama",
    "documentary_relationship": "parentesco documental",
    "match_candidates": "matching",
    "build_ged_indexes": "indices do GEDCOM",
}

# Simbolos que so podem aparecer na MONTAGEM do pacote de dependencias.
SO_NA_MONTAGEM = {
    "read_csv_with_fallback", "detectar_colunas", "aggregate_matches",
    "generate_mermaid_graph", "generate_mermaid_graph_indirect_bridge",
}


def _nome(no):
    """Nome simples de um no de expressao: `f` em `f(...)` e em `f` solto."""
    if isinstance(no, ast.Name):
        return no.id
    if isinstance(no, ast.Call):
        return _nome(no.func)
    if isinstance(no, ast.Attribute):
        return no.attr
    return None


def _index(arvore):
    for no in ast.walk(arvore):
        if isinstance(no, ast.FunctionDef) and no.name == "index":
            return no
    raise AssertionError("funcao index() nao encontrada em src/app.py")


def _montagem_das_dependencias(arvore):
    """A expressao `Dependencias(...)` do nivel do modulo, e os nomes que ela cita."""
    for no in ast.walk(arvore):
        if isinstance(no, ast.Call) and _nome(no) == "Dependencias":
            return {_nome(arg) for arg in no.args if isinstance(arg, ast.Name)}
    return set()


def main():
    with open(CAMINHO, encoding="utf-8") as fh:
        fonte = fh.read()
    arvore = ast.parse(fonte, filename=CAMINHO)
    corpo = _index(arvore)

    problemas = []

    chamadas = [_nome(no) for no in ast.walk(corpo)
                if isinstance(no, ast.Call)]
    for simbolo, papel in DOMINIO_PROIBIDO.items():
        if simbolo in chamadas:
            problemas.append("index() chama %s() â€” %s" % (simbolo, papel))

    for simbolo in sorted(SO_NA_MONTAGEM):
        if simbolo in chamadas:
            problemas.append(
                "index() chama %s() diretamente; ela so pode ser montada no pacote "
                "de dependencias da borda (RF-09, D-05)" % simbolo)

    montados = _montagem_das_dependencias(arvore)
    faltando = SO_NA_MONTAGEM - montados
    if faltando:
        problemas.append(
            "o pacote `Dependencias` da borda nao cita: %s" % ", ".join(sorted(faltando)))

    # A montagem tem de ser UNICA (RF-14): uma no modulo, nenhuma dentro da rota.
    montagens_no_modulo = sum(
        1 for no in arvore.body
        if isinstance(no, ast.Assign) and any(
            isinstance(valor, ast.Call) and _nome(valor) == "Dependencias"
            for valor in [no.value]))
    if montagens_no_modulo != 1:
        problemas.append(
            "esperado UM ponto de montagem de `Dependencias` no modulo; encontrados %d "
            "(RF-14)" % montagens_no_modulo)
    if "Dependencias" in chamadas:
        problemas.append("index() monta `Dependencias` por requisicao (RF-14)")

    print("arquivo varrido: %s" % CAMINHO)
    print("funcao varrida : index()")
    print("chamadas em index(): %d" % len(chamadas))
    print("simbolos proibidos encontrados: %d" % sum(
        1 for s in DOMINIO_PROIBIDO if s in chamadas))
    print("funcoes de dependencia citadas na montagem da borda: %s"
          % ", ".join(sorted(montados)))
    print("pontos de montagem de `Dependencias` no modulo: %d" % montagens_no_modulo)

    if problemas:
        print("\nRESULTADO: REPROVADO")
        for problema in problemas:
            print("  - " + problema)
        return 1
    print("\nRESULTADO: APROVADO â€” nenhum passo de dominio em index()")
    return 0


if __name__ == "__main__":
    sys.exit(main())

