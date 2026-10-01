"""Gera a divisao de dna_analysis.py em 4 modulos, por AST. NAO toca na arvore legada.

Le o arquivo original, extrai o texto EXATO de cada simbolo de nivel de modulo (via
`lineno`/`end_lineno` do ast), distribui os simbolos pelo modulo de destino e
monta os arquivos novos. Ao final confere que o texto de cada simbolo aparece
VERBATIM no arquivo construido, e reporta qualquer linha do original que nao
tenha sido contabilizada.

Escreve o resultado em `.pytest-tmp/zv52-proposta/` e o diff em CHG-001.diff.

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
REL = "analisador-genealogico/reconstructed/dna_analysis.py"
ORIG = os.path.join(ROOT, REL)
ESPELHO = os.path.join(ROOT, ".pytest-tmp", "zv52-proposta")
SAIDA_DIFF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "CHG-001.diff")
BASE = "analisador-genealogico/reconstructed/"

# Simbolo -> modulo de destino. O fluxo decide isso, nao a estetica.
DESTINO = {
    # vocabulario de nomes: usado por normalizacao E por matching, um dono so
    "STOP_WORDS": "name_normalization",
    "GENERIC_GIVENS": "name_normalization",
    "SURNAME_SUFFIXES": "name_normalization",
    "COMMON_SURNAMES": "name_normalization",
    "SURNAME_EQUIV": "name_normalization",
    "SHORT_KEEP": "name_normalization",
    # funcoes de nome
    "norm_name": "name_normalization",
    "drop_short_tokens": "name_normalization",
    "surname_core_tokens": "name_normalization",
    "split_name_pt": "name_normalization",
    "surnames_set": "name_normalization",
    "top_given_tokens": "name_normalization",
    "token_prefixes": "name_normalization",
    "soft_prefix_jaccard": "name_normalization",
    # ingestao de CSV
    "read_csv_with_fallback": "csv_ingest",
    "detect_columns": "csv_ingest",
    "aggregate_matches": "csv_ingest",
    # matching
    "build_ged_indexes": "matching",
    "match_candidates": "matching",
    # regra de cM e fluxo ficam
    "SHARED_CM_DATA": "dna_analysis",
    "get_relationships_by_cm": "dna_analysis",
    "dna_analysis": "dna_analysis",
}

CABECALHOS = {
    "name_normalization": '''"""Normalizacao e decomposicao de nomes, e o vocabulario que isso usa.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52. Responsabilidade unica:
transformar um nome em forma comparavel (`norm_name`), decompo-lo em prenome,
sobrenomes e sufixos (`split_name_pt`), e derivar os conjuntos e prefixos que o
matching consome. O vocabulario de particulas e sufixos vive aqui porque e um
conceito unico, mesmo sendo consumido tambem pelo matching.

Este modulo NAO define limpeza de mojibake: `strip_bad_utf` e `demojibake` sao
autoridade de `domain.py`, unificadas pela OPP-20260929-4LE3. Ter duas funcoes
com esse nome gerava falso positivo de divergencia no harness de paridade.
"""
from __future__ import annotations

import string
import unicodedata

from .domain import strip_bad_utf
''',
    "csv_ingest": '''"""Leitura do CSV de matches e agregacao por match.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52. Responsabilidade unica:
ler o arquivo tolerando encoding, descobrir as colunas e reduzir varias linhas do
mesmo match a uma, somando os cM dos segmentos.
"""
from __future__ import annotations

import pandas as pd

from .domain import demojibake
from .name_normalization import norm_name
''',
    "matching": '''"""Indices do GEDCOM e decisao de aceitacao de candidatos.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52. Responsabilidade unica:
construir os indices sobre a arvore carregada e decidir, para cada match do CSV,
quais pessoas do GEDCOM sao candidatas aceitas e por que.

Nao depende de pandas: quem le o CSV e `csv_ingest`.
"""
from __future__ import annotations

from thefuzz import fuzz

from .name_normalization import (
    COMMON_SURNAMES,
    GENERIC_GIVENS,
    STOP_WORDS,
    drop_short_tokens,
    norm_name,
    soft_prefix_jaccard,
    split_name_pt,
    surnames_set,
    token_prefixes,
)
from .upload import get_name, people
''',
    "dna_analysis": '''"""Tarefa 04 - Analise de DNA.

Cruza a arvore GEDCOM com um CSV de matches (ex.: GEDmatch). Agrega
segmentos duplicados por match (somando cM), faz matching difuso de nomes
com filtro anti-falso-positivo, calcula o caminho ancestral ate a pessoa-raiz
e preve o parentesco por faixa de cM. Renderiza resultados ordenados por cM
decrescente e lista os descartados para auditoria.

Comportamento identico ao legado, incluindo as decisoes documentadas:
- Limiares de score/given como literais nas regras A/B/C/D (92, 90, 86, ...).
- Relaxamento de Jaccard (0.5 -> 0.33) para cM>=150 e dado nao-generico.
- Regex de ID `[A-Z]{2}\\\\d{7}`.

## Layout (OPP-20260929-ZV52)

Este modulo passou a orquestrar. As responsabilidades foram separadas em
`name_normalization`, `csv_ingest` e `matching`, e aqui ficam a tabela de cM, a
traducao de cM em parentesco e o fluxo principal.

## Superficie de compatibilidade

O bloco de reexportacao no fim do arquivo existe porque consumidores externos
importam nomes daqui: `app.py`, `tests/test_dna_analysis.py`,
`tests/test_characterization_matching.py` e `_reversa_sdd/parity/harness.py`.
Remover a reexportacao quebra esses consumidores. Enquanto eles nao forem
migrados para os modulos novos, o bloco fica.
"""
from __future__ import annotations

from .csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
from .domain import demojibake, strip_bad_utf
from .matching import build_ged_indexes, match_candidates
from .name_normalization import (
    drop_short_tokens,
    norm_name,
    soft_prefix_jaccard,
    split_name_pt,
    surname_core_tokens,
    surnames_set,
    token_prefixes,
    top_given_tokens,
)
from .path_search import find_ancestral_path, generate_mermaid_graph
from .upload import get_name, people
''',
}

# Ordem de escrita dos simbolos dentro de cada modulo, pelo nome.
ORDEM = {
    "name_normalization": [
        "STOP_WORDS", "GENERIC_GIVENS", "SURNAME_SUFFIXES", "COMMON_SURNAMES",
        "SURNAME_EQUIV", "SHORT_KEEP",
        "norm_name", "drop_short_tokens", "surname_core_tokens", "split_name_pt",
        "surnames_set", "top_given_tokens", "token_prefixes", "soft_prefix_jaccard",
    ],
    "csv_ingest": ["read_csv_with_fallback", "detect_columns", "aggregate_matches"],
    "matching": ["build_ged_indexes", "match_candidates"],
    "dna_analysis": ["SHARED_CM_DATA", "get_relationships_by_cm", "dna_analysis"],
}

RODAPE_COMPAT = '''

# ---------------------------------------------------------------------------
# Superficie de compatibilidade (ver a nota no docstring do modulo).
# Reexporta o que era definido aqui antes da OPP-20260929-ZV52.
# ---------------------------------------------------------------------------
__all__ = [
    "dna_analysis", "get_relationships_by_cm", "SHARED_CM_DATA",
    "aggregate_matches", "detect_columns", "read_csv_with_fallback",
    "build_ged_indexes", "match_candidates",
    "norm_name", "split_name_pt", "surnames_set", "top_given_tokens",
    "token_prefixes", "drop_short_tokens", "surname_core_tokens",
    "soft_prefix_jaccard", "strip_bad_utf", "demojibake",
]
'''


def texto_de(src_linhas, no):
    """Texto exato do simbolo, com as linhas de comentario imediatamente acima.

    ATENCAO ao indice: `no.lineno` e 1-based, entao o texto do simbolo comeca em
    `src_linhas[no.lineno - 1]`. A linha acima de uma linha `k` (1-based) e
    `src_linhas[k - 2]`. Uma versao anterior deste script errava esse indice por
    um e comecava o texto uma linha antes, o que fazia cada constante multilinha
    levar o prefixo da vizinha e deixar o fecha-chaves no lugar errado.
    """
    inicio = no.lineno
    while inicio - 1 >= 1 and src_linhas[inicio - 2].lstrip().startswith("#"):
        inicio -= 1
    return "".join(src_linhas[inicio - 1:no.end_lineno])


def main() -> int:
    src = open(ORIG, encoding="utf-8", newline="").read()
    linhas = src.splitlines(keepends=True)
    arvore = ast.parse(src)

    simbolos = []       # (nome, texto, primeira_linha, ultima_linha)
    for no in arvore.body:
        nomes = []
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nomes = [no.name]
        elif isinstance(no, ast.Assign):
            nomes = [t.id for t in no.targets if isinstance(t, ast.Name)]
        for n in nomes:
            if n in DESTINO:
                simbolos.append((n, texto_de(linhas, no), no.lineno, no.end_lineno))

    faltando = [n for n in DESTINO if n not in [s[0] for s in simbolos]]
    assert not faltando, "simbolos nao encontrados no original: %s" % faltando

    por_modulo = {}
    for nome, texto, _, _ in simbolos:
        por_modulo.setdefault(DESTINO[nome], {})[nome] = texto

    arquivos = {}
    for modulo, cab in CABECALHOS.items():
        partes = [cab]
        for nome in ORDEM[modulo]:
            partes.append("\n\n" + por_modulo[modulo][nome].rstrip("\n") + "\n")
        corpo = "".join(partes)
        if modulo == "dna_analysis":
            corpo += RODAPE_COMPAT
        arquivos[modulo + ".py"] = corpo

    # --- conferencia 1: o texto de cada simbolo comeca pelo proprio nome -----
    # Esta e a conferencia que pega o off-by-one de `texto_de`: com o indice
    # errado, o texto comecava pela linha da vizinha e o nome nao batia.
    problemas = []
    for nome, texto, _, _ in simbolos:
        primeira = next((l.strip() for l in texto.splitlines()
                         if l.strip() and not l.strip().startswith("#")), "")
        ok = (primeira.startswith(nome + " ") or primeira.startswith(nome + "=")
              or primeira.startswith(nome + ":") or primeira.startswith(nome + "[")
              or primeira.startswith("def " + nome + "("))
        if not ok:
            problemas.append("simbolo %s comeca por %r (esperado o proprio nome)"
                             % (nome, primeira[:60]))

    # --- conferencia 2: escreveu uma vez so, e no modulo certo ---------------
    for nome, texto, _, _ in simbolos:
        alvo = arquivos[DESTINO[nome] + ".py"]
        if texto.rstrip("\n") not in alvo:
            problemas.append("simbolo %s nao aparece em %s" % (nome, DESTINO[nome]))
        elif alvo.count(texto.rstrip("\n")) != 1:
            problemas.append("simbolo %s aparece %d vezes em %s"
                             % (nome, alvo.count(texto.rstrip("\n")), DESTINO[nome]))

    # --- conferencia 3: toda linha de codigo do original foi contabilizada ---
    # Nota honesta: esta conferencia lista o que sobrou, e o que deve sobrar sao
    # apenas banners e reguas de comentario. As provas fortes sao o compile de
    # cada arquivo, a suite e a equivalencia antes/depois, nao estas checagens.
    usadas = set()
    for _, _, ini, fim in simbolos:
        usadas.update(range(ini, fim + 1))
    orfas = []
    for i, linha in enumerate(linhas, start=1):
        if i in usadas or i <= 25:
            continue
        if not linha.strip():
            continue
        orfas.append("%4d: %s" % (i, linha.rstrip()))

    print("simbolos movidos     : %d" % len(simbolos))
    print("banners nao movidos  : %d (esperado: 15, os 5 banners)" % len(orfas))
    for o in orfas:
        print("   " + o)
    print("problemas            : %d" % len(problemas))
    for p in problemas:
        print("   " + p)

    # --- escrita do espelho -------------------------------------------------
    destino_dir = os.path.join(ESPELHO, "analisador-genealogico", "reconstructed")
    os.makedirs(destino_dir, exist_ok=True)
    for nome_arq, conteudo in arquivos.items():
        with open(os.path.join(destino_dir, nome_arq), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(conteudo)
        compile(conteudo, nome_arq, "exec")

    # --- diff no formato do git ---------------------------------------------
    def blob(t):
        d = t.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(d)).encode() + b"\0" + d).hexdigest()

    blocos = []
    for nome_arq in ["name_normalization.py", "csv_ingest.py", "matching.py",
                     "dna_analysis.py"]:
        novo = arquivos[nome_arq]
        caminho = BASE + nome_arq
        if nome_arq == "dna_analysis.py":
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
    print("diff escrito         : %s (%d bytes)" % (os.path.relpath(SAIDA_DIFF, ROOT),
                                                    len(conteudo_diff.encode("utf-8"))))
    for nome_arq, conteudo in sorted(arquivos.items()):
        print("  %-24s %4d linhas" % (nome_arq, conteudo.count("\n")))
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
