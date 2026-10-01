"""Gera a divisao de path_search.py em 4 modulos, por AST. NAO toca na arvore legada.

Opcao A aprovada no gate do plano: `family_navigation` -> `path_finding` ->
`mermaid_render` -> `path_search`, sem ciclo e sem import tardio novo.

Extrai o texto EXATO de cada simbolo de nivel de modulo pelo ast, distribui pelo
modulo de destino e monta os arquivos. O docstring do modulo original e preservado
LITERALMENTE, extraido do proprio arquivo, e nao redigitado.

Escreve em `.pytest-tmp/uxef-proposta/` e o diff na raiz desta transformacao.

Uso:
    python <este script>
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
REL = "analisador-genealogico/reconstructed/path_search.py"
ORIG = os.path.join(ROOT, REL)
ESPELHO = os.path.join(ROOT, ".pytest-tmp", "uxef-proposta")
SAIDA_DIFF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "CHG-001.diff")
BASE = "analisador-genealogico/reconstructed/"

DESTINO = {
    # quem e parente de quem
    "find_person_by_name": "family_navigation",
    "get_parents": "family_navigation",
    "get_spouses": "family_navigation",
    "are_spouses": "family_navigation",
    "split_path_by_marriage": "family_navigation",
    "pick_spouse_for_couple": "family_navigation",
    "exclude_tail": "family_navigation",
    # achar o caminho
    "MAX_DEPTH": "path_finding",
    "MAX_HOPS": "path_finding",
    "find_indirect_path": "path_finding",
    "find_ancestral_path": "path_finding",
    # emitir o diagrama
    "_mermaid_sid": "mermaid_render",
    "_LABEL_SEGURO": "mermaid_render",
    "_mermaid_label": "mermaid_render",
    "generate_mermaid_graph": "mermaid_render",
    "generate_mermaid_graph_indirect_bridge": "mermaid_render",
    # o handler fica
    "path_search": "path_search",
}

CABECALHOS = {
    "family_navigation": '''"""Quem e parente de quem, na arvore carregada.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica:
resolver uma pessoa pelo nome e navegar as ligacoes de familia (pais, conjuge,
casamento, afinidade). Nao conhece caminho, nao conhece diagrama.

## Contrato de import com `.upload`

`people`, `families` e `child_to_family` sao mutados in place por
`load_gedcom_and_build_graph`, entao o binding do topo continua apontando para o
objeto vivo. `ref_id` e funcao, nunca reatribuida. Por isso os cinco vem do topo.

`graph` e a excecao e nao aparece aqui: ele e reatribuido a cada parse, e quem
precisa dele e `path_finding`, que o importa dentro da funcao.
"""
from __future__ import annotations

from .upload import child_to_family, families, get_name, people, ref_id
''',
    "path_finding": '''"""Achar o caminho entre duas pessoas.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica: a
busca direta por ancestral comum (BFS bidirecional) e a busca indireta por
afinidade (`nx.shortest_path` com compressao de nos de familia), com os limites
que a alma fixa: profundidade 20 e 40 hops.

## Contrato de import com `.upload`

`people` e mutado in place, entao vem do topo. `graph` e a excecao: e
reatribuido a cada parse (`graph = new_graph`), entao um import no topo ficaria
preso ao grafo antigo, e ele continua sendo importado dentro de
`find_indirect_path`.
"""
from __future__ import annotations

from collections import deque

import networkx as nx

from .family_navigation import get_parents
from .upload import people
''',
    "mermaid_render": '''"""Emissao do diagrama Mermaid e o contrato de escape do rotulo.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica:
transformar um caminho de parentesco no texto do diagrama.

Este e o modulo onde o contrato de escape vive. `_LABEL_SEGURO` e a lista branca
que substituiu a lista negra furada pela crase, e o comentario que a documenta
veio junto com ela. Ver BUG-20260929-J6PQ.
"""
from __future__ import annotations

import re
import unicodedata

from .family_navigation import (
    exclude_tail,
    get_spouses,
    pick_spouse_for_couple,
    split_path_by_marriage,
)
from .path_finding import find_ancestral_path
from .upload import get_name, people
''',
    "path_search": '''# ---------------------------------------------------------------------------
# Superficie de compatibilidade (ver a nota no docstring do modulo).
# Reexporta o que era definido aqui antes da OPP-20260929-UXEF. Os nomes
# privados do render entram porque `tests/test_mermaid_escape.py` e as sondas do
# BUG-20260929-J6PQ os importam deste modulo.
# ---------------------------------------------------------------------------
__all__ = [
    "path_search",
    "find_person_by_name", "get_parents", "get_spouses", "are_spouses",
    "split_path_by_marriage", "pick_spouse_for_couple", "exclude_tail",
    "MAX_DEPTH", "MAX_HOPS", "find_indirect_path", "find_ancestral_path",
    "_mermaid_sid", "_LABEL_SEGURO", "_mermaid_label",
    "generate_mermaid_graph", "generate_mermaid_graph_indirect_bridge",
    "ref_id",
]
''',
}

ORDEM = {
    "family_navigation": [
        "find_person_by_name", "get_parents", "get_spouses", "are_spouses",
        "split_path_by_marriage", "pick_spouse_for_couple", "exclude_tail",
    ],
    "path_finding": ["MAX_DEPTH", "MAX_HOPS", "find_indirect_path", "find_ancestral_path"],
    "mermaid_render": [
        "_mermaid_sid", "_LABEL_SEGURO", "_mermaid_label",
        "generate_mermaid_graph", "generate_mermaid_graph_indirect_bridge",
    ],
    "path_search": ["path_search"],
}

# Imports do modulo que fica. Inclui os nomes que so existem para a
# compatibilidade, agrupados e comentados para nao parecerem esquecimento.
IMPORTS_FINAL = '''
from .family_navigation import (
    are_spouses,
    exclude_tail,
    find_person_by_name,
    get_parents,
    get_spouses,
    pick_spouse_for_couple,
    split_path_by_marriage,
)
from .mermaid_render import (
    _LABEL_SEGURO,
    _mermaid_label,
    _mermaid_sid,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from .path_finding import MAX_DEPTH, MAX_HOPS, find_ancestral_path, find_indirect_path
from .upload import get_name, people, ref_id

# `are_spouses`, `get_parents`, `get_spouses`, `pick_spouse_for_couple`,
# `split_path_by_marriage`, `exclude_tail`, `MAX_DEPTH`, `_mermaid_sid`,
# `_LABEL_SEGURO`, `_mermaid_label` e `ref_id` nao sao usados por `path_search`.
# Eles estao aqui pela superficie de compatibilidade declarada em `__all__`.
'''

NOTA_LAYOUT = '''

## Layout (OPP-20260929-UXEF)

Este modulo passou a compor o fluxo. As responsabilidades foram separadas em
`family_navigation` (parentesco), `path_finding` (os dois algoritmos de busca) e
`mermaid_render` (o diagrama e o escape do rotulo). A direcao das dependencias e
estritamente descendente, sem ciclo e sem import tardio novo.

## Superficie de compatibilidade

O bloco de reexportacao no fim do arquivo existe porque consumidores externos
importam nomes daqui: `app.py`, `reconstructed/dna_analysis.py`,
`tests/test_path_search.py`, `tests/test_mermaid_escape.py`,
`tests/test_characterization_mermaid.py`, `_reversa_sdd/parity/harness.py` e as
sondas do BUG-20260929-J6PQ. Enquanto eles nao forem migrados, o bloco fica.
'''


def texto_de(src_linhas, no):
    """Devolve `(linha_inicial, texto)` do simbolo, com os comentarios acima.

    Devolve tambem a linha inicial, e nao so o texto, porque a conferencia de
    linhas contabilizadas precisa dela: um simbolo precedido por bloco de
    comentario comeca antes de `no.lineno`. Guardar `no.lineno` fazia a
    conferencia acusar como nao movido um comentario que viajou junto.

    `no.lineno` e 1-based, entao o texto comeca em `src_linhas[no.lineno - 1]`, e
    a linha acima de uma linha `k` (1-based) e `src_linhas[k - 2]`.
    """
    inicio = no.lineno
    while inicio - 1 >= 1 and src_linhas[inicio - 2].lstrip().startswith("#"):
        inicio -= 1
    return inicio, "".join(src_linhas[inicio - 1:no.end_lineno])


def main() -> int:
    src = open(ORIG, encoding="utf-8", newline="").read()
    linhas = src.splitlines(keepends=True)
    arvore = ast.parse(src)

    _, docstring = texto_de(linhas, arvore.body[0])

    simbolos = []
    for no in arvore.body:
        nomes = []
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nomes = [no.name]
        elif isinstance(no, ast.Assign):
            nomes = [t.id for t in no.targets if isinstance(t, ast.Name)]
        for n in nomes:
            if n in DESTINO:
                ini, texto = texto_de(linhas, no)
                simbolos.append((n, texto, ini, no.end_lineno))

    faltando = [n for n in DESTINO if n not in [s[0] for s in simbolos]]
    assert not faltando, "simbolos nao encontrados: %s" % faltando

    por_modulo = {}
    for nome, texto, _, _ in simbolos:
        por_modulo.setdefault(DESTINO[nome], {})[nome] = texto

    arquivos = {}
    for modulo, cab in CABECALHOS.items():
        if modulo == "path_search":
            # Insere as secoes novas ANTES do fecha-aspas do docstring. A primeira
            # ocorrencia de '"""\n' neste texto e o fechamento, porque a abertura e
            # seguida de texto na mesma linha.
            corpo = docstring.replace('"""\n', NOTA_LAYOUT + '"""\n', 1)
            corpo = corpo + "\nfrom __future__ import annotations\n" + IMPORTS_FINAL
            for nome in ORDEM[modulo]:
                corpo += "\n\n" + por_modulo[modulo][nome].rstrip("\n") + "\n"
            corpo += "\n\n" + cab
        else:
            corpo = cab
            for nome in ORDEM[modulo]:
                corpo += "\n\n" + por_modulo[modulo][nome].rstrip("\n") + "\n"
        arquivos[modulo + ".py"] = corpo

    # --- conferencia 1: o texto de cada simbolo comeca pelo proprio nome -----
    problemas = []
    for nome, texto, _, _ in simbolos:
        primeira = next((l.strip() for l in texto.splitlines()
                         if l.strip() and not l.strip().startswith("#")), "")
        ok = (primeira.startswith(nome + " ") or primeira.startswith(nome + "=")
              or primeira.startswith(nome + ":") or primeira.startswith(nome + "[")
              or primeira.startswith("def " + nome + "("))
        if not ok:
            problemas.append("simbolo %s comeca por %r" % (nome, primeira[:60]))

    # --- conferencia 2: escrito uma vez so, no modulo certo ------------------
    for nome, texto, _, _ in simbolos:
        alvo = arquivos[DESTINO[nome] + ".py"]
        t = texto.rstrip("\n")
        if t not in alvo:
            problemas.append("simbolo %s nao aparece em %s" % (nome, DESTINO[nome]))
        elif alvo.count(t) != 1:
            problemas.append("simbolo %s aparece %d vezes em %s"
                             % (nome, alvo.count(t), DESTINO[nome]))

    # --- conferencia 3: o docstring original foi preservado como prefixo -----
    # Nao da para comparar por igualdade: o docstring final tem as secoes novas
    # de layout e compatibilidade acrescentadas no fim.
    original_doc = ast.get_docstring(arvore)
    final_doc = ast.get_docstring(ast.parse(arquivos["path_search.py"]))
    if not final_doc.startswith(original_doc):
        problemas.append("o docstring original nao foi preservado como prefixo")

    # --- conferencia 4: linhas de codigo do original nao contabilizadas ------
    usadas = set()
    for _, _, ini, fim in simbolos:
        usadas.update(range(ini, fim + 1))
    orfas = []
    for i, linha in enumerate(linhas, start=1):
        if i in usadas or i <= 27 or not linha.strip():
            continue
        orfas.append("%4d: %s" % (i, linha.rstrip()))

    print("simbolos movidos     : %d" % len(simbolos))
    print("banners nao movidos  : %d (esperado: 15, os 5 banners)" % len(orfas))
    for o in orfas:
        print("   " + o)
    print("problemas            : %d" % len(problemas))
    for p in problemas:
        print("   " + p)

    destino_dir = os.path.join(ESPELHO, "analisador-genealogico", "reconstructed")
    os.makedirs(destino_dir, exist_ok=True)
    for nome_arq, conteudo in arquivos.items():
        with open(os.path.join(destino_dir, nome_arq), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(conteudo)
        compile(conteudo, nome_arq, "exec")

    def blob(t):
        d = t.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(d)).encode() + b"\0" + d).hexdigest()

    blocos = []
    for nome_arq in ["family_navigation.py", "path_finding.py", "mermaid_render.py",
                     "path_search.py"]:
        novo = arquivos[nome_arq]
        caminho = BASE + nome_arq
        if nome_arq == "path_search.py":
            blocos.append("".join([
                "diff --git a/%s b/%s\n" % (caminho, caminho),
                "index %s..%s 100644\n" % (blob(src)[:7], blob(novo)[:7]),
                "--- a/%s\n" % caminho, "+++ b/%s\n" % caminho,
            ] + list(difflib.unified_diff(linhas, novo.splitlines(keepends=True),
                                          fromfile="a/" + caminho, tofile="b/" + caminho, n=3))))
        else:
            blocos.append("".join([
                "diff --git a/%s b/%s\n" % (caminho, caminho),
                "new file mode 100644\n",
                "index 0000000..%s\n" % blob(novo)[:7],
                "--- /dev/null\n", "+++ b/%s\n" % caminho,
            ] + list(difflib.unified_diff([], novo.splitlines(keepends=True),
                                          fromfile="/dev/null", tofile="b/" + caminho, n=3))))
    conteudo_diff = "".join(blocos)
    with open(SAIDA_DIFF, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(conteudo_diff)
    print("diff escrito         : %s (%d bytes)"
          % (os.path.relpath(SAIDA_DIFF, ROOT), len(conteudo_diff.encode("utf-8"))))
    for nome_arq, conteudo in sorted(arquivos.items()):
        print("  %-24s %4d linhas" % (nome_arq, conteudo.count("\n")))
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
