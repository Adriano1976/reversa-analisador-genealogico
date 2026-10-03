"""Registra os CHG-*.diff da OPP-20261003-LMAY, um por lote.

Estado "antes": o conteudo de `HEAD` para cada arquivo, congelado em
`before-after/head/` no momento da aplicacao. As tres transformacoes anteriores
tinham sido commitadas antes desta, entao o `HEAD` e exatamente o estado anterior
da LMAY, e os diffs saem contra o Git, sem reconstrucao.

Conferencia independente: aplicando o INVERSO de cada edicao desta transformacao
ao arquivo atual, o resultado tem de ser igual ao `HEAD`. Se nao for, o diff
estaria descrevendo um estado que nunca existiu, e o script falha.
"""
from __future__ import annotations

import difflib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
HEAD = os.path.join(HERE, "before-after", "head")

# (arquivo, [(depois, antes), ...])  os pares servem para a conferencia inversa
EDITS = [
    ("src/reconstructed/csv_ingest.py", [
        ("from .text_cleaning import demojibake", "from .domain import demojibake"),
    ]),
    ("src/reconstructed/dna_analysis.py", [
        ("from .text_cleaning import demojibake, strip_bad_utf",
         "from .domain import demojibake, strip_bad_utf"),
    ]),
    ("src/reconstructed/name_normalization.py", [
        ("from .text_cleaning import strip_bad_utf", "from .domain import strip_bad_utf"),
        ("autoridade de `text_cleaning.py`, unificadas pela OPP-20260929-4LE3. Ter duas\n"
         "funcoes com esse nome gerava falso positivo de divergencia no harness de\n"
         "paridade.",
         "autoridade de `domain.py`, unificadas pela OPP-20260929-4LE3. Ter duas funcoes\n"
         "com esse nome gerava falso positivo de divergencia no harness de paridade."),
    ]),
    ("tests/test_domain.py", [
        ("from reconstructed.text_cleaning import (", "from reconstructed.domain import ("),
        ("    que so a implementacao antiga fazia, a que a OPP-20260929-B5F2 substituiu. O\n"
         "    corpo vivo, vindo de dna_analysis, recupera o texto quando a conversao latin1\n"
         "    para utf-8 e valida.",
         "    que so a implementacao morta de domain.py fazia. O corpo vivo, vindo de\n"
         "    dna_analysis, recupera o texto quando a conversao latin1 para utf-8 e valida."),
    ]),
    ("_reversa_sdd/parity/harness.py", [
        ("from reconstructed import text_cleaning as DM", "from reconstructed import domain as DM"),
        ("#   A reconstrucao DIVIDIU isso em duas, e a unificacao veio depois:\n"
         "#     - `dna_analysis.strip_bad_utf` = copia fiel do oraculo  <-- ESTE e o equivalente\n"
         "#     - `text_cleaning.strip_bad_utf` e `text_cleaning.demojibake` = a autoridade unica\n"
         "#\n"
         "#   HISTORICO, e nao vale mais como aviso: entre a OPP-20260929-ZV52 e a\n"
         "#   OPP-20260929-B5F2 as duas implementacoes divergiam, e comparar a do modulo de\n"
         "#   limpeza com o oraculo gerava falso positivo, porque uma delas apenas removia\n"
         "#   U+FFFD. A B5F2 unificou os corpos. Medido em 2026-10-03:\n"
         "#       D.strip_bad_utf is DM.strip_bad_utf  ->  True\n"
         "#       D.demojibake   is DM.demojibake     ->  True\n"
         "#   Sao o mesmo objeto, entao qualquer um dos dois serve de probe. O probe usado\n"
         "#   abaixo continua sendo `D.strip_bad_utf`.",
         "#   A reconstrucao DIVIDIU isso em duas:\n"
         "#     - `dna_analysis.strip_bad_utf` (L74-90) = copia fiel do oraculo  <-- ESTE e o equivalente\n"
         "#     - `domain.strip_bad_utf`    (L29-40) = outra coisa (so remove U+FFFD)\n"
         "#     - `domain.demojibake`       (L43-57) = parte do trabalho, implementacao diferente\n"
         "#   Comparar `domain.strip_bad_utf` com o oraculo gera FALSO POSITIVO de divergencia:\n"
         "#   nao e o mesmo comportamento, e nem pretende ser. O probe correto e `norm_name`\n"
         "#   (que usa a funcao certa internamente) + `D.strip_bad_utf` abaixo."),
    ]),
    ("README.md", []),
]


def le(caminho):
    with open(caminho, encoding="utf-8", newline="") as fh:
        return fh.read()


def do_head(rel):
    return le(os.path.join(HEAD, rel.replace("/", "__")))


def diff(antes, depois, nome_antes, nome_depois):
    return "".join(difflib.unified_diff(
        antes.splitlines(keepends=True), depois.splitlines(keepends=True),
        fromfile=nome_antes, tofile=nome_depois, n=3))


def grava(nome, texto):
    with open(os.path.join(HERE, nome), "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)
    print("%-42s %6d bytes" % (nome, len(texto.encode("utf-8"))))


def main() -> int:
    falhas = []
    print("=" * 78)
    print("REGISTRO DOS DIFFS DA OPP-20261003-LMAY")
    print("=" * 78)

    print("\nCONFERENCIA: o inverso das edicoes tem de reproduzir o HEAD")
    for rel, pares in EDITS:
        atual, reconstruido = le(os.path.join(ROOT, rel)), le(os.path.join(ROOT, rel))
        for depois, antes in pares:
            n = reconstruido.count(depois)
            if n != 1:
                falhas.append("%s: o trecho aparece %d vezes, e nao uma" % (rel, n))
                continue
            reconstruido = reconstruido.replace(depois, antes)
        if rel == "README.md":
            print("  %-44s sem par inverso, comparado direto" % rel)
            continue
        if reconstruido == do_head(rel):
            print("  %-44s bate com o HEAD" % rel)
        else:
            falhas.append("%s: o inverso nao reproduz o HEAD" % rel)

    print("\nCHG-001, renomeacao do modulo")
    corpo = diff(do_head("src/reconstructed/domain.py"),
                 le(os.path.join(ROOT, "src", "reconstructed", "text_cleaning.py")),
                 "a/src/reconstructed/domain.py", "b/src/reconstructed/text_cleaning.py")
    corpo = ("rename from src/reconstructed/domain.py\n"
             "rename to src/reconstructed/text_cleaning.py\n") + corpo
    grava("CHG-001-renomear-modulo.diff", corpo)

    print("\nCHG-002, importadores e comentarios de docstring")
    corpo = []
    for rel, _ in EDITS[:4]:
        corpo.append(diff(do_head(rel), le(os.path.join(ROOT, rel)), "a/" + rel, "b/" + rel))
    grava("CHG-002-importadores.diff", "".join(corpo))

    print("\nCHG-003, comentario do harness de paridade")
    rel = "_reversa_sdd/parity/harness.py"
    grava("CHG-003-harness-comentario.diff",
          diff(do_head(rel), le(os.path.join(ROOT, rel)), "a/" + rel, "b/" + rel))

    print("\nCHG-004, arvore e prosa do README")
    antes, atual = do_head("README.md"), le(os.path.join(ROOT, "README.md"))
    if antes == atual:
        falhas.append("o README nao mudou, e deveria ter mudado")
    grava("CHG-004-readme.diff", diff(antes, atual, "a/README.md", "b/README.md"))

    print()
    print("=" * 78)
    if falhas:
        print("RESULTADO: %d FALHA(S)" % len(falhas))
        for f in falhas:
            print("  " + f)
    else:
        print("RESULTADO: 4 DIFFS GRAVADOS CONTRA O ESTADO REAL DO GIT")
    print("=" * 78)
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
