"""Verifica, antes de gerar o diff, que a guarda estrutural reprova o codigo de hoje
e aprova o codigo proposto. Nao escreve em arquivo nenhum.
"""
from __future__ import annotations

import ast
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[4]
ALVO = RAIZ / "src" / "core" / "documentary_relationship.py"
ESTAGIO = pathlib.Path(__file__).resolve().parent / "CHG-001-novo-teste.py"

atual = ALVO.read_text(encoding="utf-8")

print("linhas do arquivo de teste estagiado:", len(ESTAGIO.read_text(encoding="utf-8").splitlines()))

# --- o mesmo codigo das guardas do teste -----------------------------------
def funcao(texto, nome="_indice_por_nome"):
    for no in ast.walk(ast.parse(texto)):
        if isinstance(no, ast.FunctionDef) and no.name == nome:
            return no
    raise AssertionError(nome)


def subscritos(fn):
    linhas = []
    for no in ast.walk(fn):
        if isinstance(no, ast.Subscript) and isinstance(no.value, ast.Name):
            if no.value.id == "_INDICE_DE_NOMES":
                linhas.append(no.lineno)
    return sorted(linhas)


def valor_inicial(texto):
    for no in ast.parse(texto).body:
        if isinstance(no, ast.AnnAssign):
            if isinstance(no.target, ast.Name) and no.target.id == "_INDICE_DE_NOMES":
                return no.value
        elif isinstance(no, ast.Assign):
            for alvo in no.targets:
                if isinstance(alvo, ast.Name) and alvo.id == "_INDICE_DE_NOMES":
                    return no.value
    raise AssertionError("sem atribuicao")


ANTES_CLASSE = '''class _CacheDeNomes(TypedDict):
    """A chave do GEDCOM e o indice que ela valida, no mesmo estado de modulo.

    Tipado por causa do retorno: com o literal `{"chave": None, "mapa": None}` o
    verificador inferia um dicionario de `None`, e `_indice_por_nome` parecia
    devolver `None` onde declara `dict`. Os valores iniciais vazios dizem a mesma
    coisa que o `None` dizia, porque a primeira consulta sempre invalida a chave.
    """

    chave: tuple
    mapa: dict


_INDICE_DE_NOMES: _CacheDeNomes = {"chave": (), "mapa": {}}
'''

DEPOIS_CLASSE = """#: O par (chave, mapa) num valor so. A troca e uma atribuicao de nome, que em
#: CPython e atomica: quem le ve o par inteiro ou o par anterior, nunca a chave de
#: um GEDCOM junto do mapa de outro. Enquanto eram dois campos de um dicionario, a
#: publicacao acontecia em dois tempos e o `return` relia o global, de modo que
#: duas requisicoes simultaneas podiam devolver o indice uma da outra. Medido em
#: 2026-10-24 com duas arvores e duas threads: ver `_reversa_refactor/busca-caminho/`.
_INDICE_DE_NOMES: tuple[tuple, dict] = ((), {})
"""

ANTES_CORPO = """    people = arvore[0]
    chave = _chave_de(people)
    if _INDICE_DE_NOMES["chave"] != chave:
        mapa: dict = {}
        for pid, pessoa in people.items():
            mapa.setdefault(normalizar(get_name(pessoa)), []).append(pid)
        _INDICE_DE_NOMES["mapa"] = mapa
        _INDICE_DE_NOMES["chave"] = chave
    return _INDICE_DE_NOMES["mapa"]
"""

DEPOIS_CORPO = """    global _INDICE_DE_NOMES

    people = arvore[0]
    chave = _chave_de(people)
    publicado = _INDICE_DE_NOMES
    if publicado[0] != chave:
        mapa: dict = {}
        for pid, pessoa in people.items():
            mapa.setdefault(normalizar(get_name(pessoa)), []).append(pid)
        publicado = (chave, mapa)
        _INDICE_DE_NOMES = publicado
    return publicado[1]
"""

assert ANTES_CLASSE in atual, "o bloco da classe mudou de forma"
assert ANTES_CORPO in atual, "o corpo de _indice_por_nome mudou de forma"

depois = atual.replace(ANTES_CLASSE, DEPOIS_CLASSE).replace(ANTES_CORPO, DEPOIS_CORPO)
depois = depois.replace("from typing import TypedDict\n", "")

print()
print("=== guarda 1: subscritos no indice dentro de _indice_por_nome ===")
print("  hoje   :", subscritos(funcao(atual)), "-> a guarda REPROVA" if subscritos(funcao(atual)) else "-> PASSA")
print("  proposto:", subscritos(funcao(depois)), "-> a guarda APROVA" if not subscritos(funcao(depois)) else "-> REPROVA")

print()
print("=== guarda 2: valor inicial e uma tupla de dois ===")
for rotulo, texto in (("hoje", atual), ("proposto", depois)):
    valor = valor_inicial(texto)
    ok = isinstance(valor, ast.Tuple) and len(valor.elts) == 2
    print(f"  {rotulo:9}: {type(valor).__name__} -> {'APROVA' if ok else 'REPROVA'}")

print()
print("=== o texto proposto ainda compila e nao importa TypedDict ===")
ast.parse(depois)
print("  compila: sim | 'from typing import TypedDict' presente:", "from typing import TypedDict" in depois)
print("  ocorrencias de _INDICE_DE_NOMES:", depois.count("_INDICE_DE_NOMES"))
print("  linhas totais hoje:", len(atual.splitlines()), "| proposto:", len(depois.splitlines()))

if "-" in sys.argv:
    pathlib.Path(__file__).resolve().parent.joinpath("depois.py").write_text(depois, encoding="utf-8")
