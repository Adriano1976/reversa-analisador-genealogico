"""Aplica a reorganizacao em subpacotes da OPP-20261003-GUE7.

Ordem, e nada e escrito antes de todas as assercoes passarem:

 1. valida que cada linha de import a reescrever aparece exatamente uma vez;
 2. cria os `__init__.py` de `parsers/` e `reporting/`;
 3. move os sete modulos;
 4. reescreve as linhas de import.

Nenhuma linha de logica e tocada. O que muda e o caminho do modulo e o caminho que
os outros usam para chegar nele.
"""
from __future__ import annotations

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PACOTE = os.path.join(ROOT, "src", "reconstructed")

INITS = [
    ("parsers", '"""Leitura do mundo de fora: o arquivo GEDCOM e o CSV de matches."""\n'),
    ("reporting", '"""Transformacao de resultado em apresentacao."""\n'),
]

MOVES = [
    ("gedcom_parser.py", "parsers/gedcom_parser.py"),
    ("csv_ingest.py", "parsers/csv_ingest.py"),
    ("matching.py", "core/matching.py"),
    ("name_normalization.py", "core/name_normalization.py"),
    ("path_finding.py", "core/path_finding.py"),
    ("family_navigation.py", "core/family_navigation.py"),
    ("mermaid_render.py", "reporting/mermaid_render.py"),
]

# Os caminhos abaixo sao os de DEPOIS da movimentacao.
EDITS = [
    ("src/reconstructed/parsers/gedcom_parser.py", [
        ("from . import gedcom_state", "from .. import gedcom_state"),
        ("from .gedcom_state import get_name, ref_id", "from ..gedcom_state import get_name, ref_id"),
    ]),
    ("src/reconstructed/parsers/csv_ingest.py", [
        ("from .text_cleaning import demojibake", "from ..text_cleaning import demojibake"),
        ("from .name_normalization import norm_name", "from ..core.name_normalization import norm_name"),
    ]),
    ("src/reconstructed/core/matching.py", [
        ("from .gedcom_state import get_name, people", "from ..gedcom_state import get_name, people"),
    ]),
    ("src/reconstructed/core/name_normalization.py", [
        ("from .text_cleaning import strip_bad_utf", "from ..text_cleaning import strip_bad_utf"),
    ]),
    ("src/reconstructed/core/path_finding.py", [
        ("from .gedcom_state import people", "from ..gedcom_state import people"),
        ("    from .gedcom_state import graph", "    from ..gedcom_state import graph"),
    ]),
    ("src/reconstructed/core/family_navigation.py", [
        ("from .gedcom_state import child_to_family, families, get_name, people, ref_id",
         "from ..gedcom_state import child_to_family, families, get_name, people, ref_id"),
    ]),
    ("src/reconstructed/reporting/mermaid_render.py", [
        ("from .family_navigation import (", "from ..core.family_navigation import ("),
        ("from .path_finding import find_ancestral_path",
         "from ..core.path_finding import find_ancestral_path"),
        ("from .gedcom_state import get_name, people", "from ..gedcom_state import get_name, people"),
    ]),
    ("src/reconstructed/dna_analysis.py", [
        ("from .csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback",
         "from .parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback"),
        ("from .matching import build_ged_indexes, match_candidates",
         "from .core.matching import build_ged_indexes, match_candidates"),
        ("from .name_normalization import (", "from .core.name_normalization import ("),
        ("from .path_finding import find_ancestral_path",
         "from .core.path_finding import find_ancestral_path"),
        ("from .mermaid_render import generate_mermaid_graph",
         "from .reporting.mermaid_render import generate_mermaid_graph"),
    ]),
    ("src/reconstructed/path_search.py", [
        ("from .family_navigation import (", "from .core.family_navigation import ("),
        ("from .mermaid_render import (", "from .reporting.mermaid_render import ("),
        ("from .path_finding import MAX_DEPTH, MAX_HOPS, find_ancestral_path, find_indirect_path",
         "from .core.path_finding import MAX_DEPTH, MAX_HOPS, find_ancestral_path, find_indirect_path"),
    ]),
    ("src/app.py", [
        ("from reconstructed.gedcom_parser import load_gedcom_and_build_graph",
         "from reconstructed.parsers.gedcom_parser import load_gedcom_and_build_graph"),
    ]),
    ("tests/test_characterization_matching.py", [
        ("from reconstructed import gedcom_parser", "from reconstructed.parsers import gedcom_parser"),
    ]),
    ("tests/test_dna_analysis.py", [
        ("from reconstructed import gedcom_parser", "from reconstructed.parsers import gedcom_parser"),
    ]),
    ("tests/test_upload.py", [
        ("from reconstructed import gedcom_parser", "from reconstructed.parsers import gedcom_parser"),
        ("from reconstructed.gedcom_parser import build_graph_from_parser",
         "from reconstructed.parsers.gedcom_parser import build_graph_from_parser"),
    ]),
    ("tests/test_mermaid_escape.py", [
        ("from reconstructed import gedcom_parser", "from reconstructed.parsers import gedcom_parser"),
    ]),
    ("tests/test_path_search.py", [
        ("from reconstructed import gedcom_parser", "from reconstructed.parsers import gedcom_parser"),
    ]),
    ("tests/test_characterization_mermaid.py", [
        ("from reconstructed import gedcom_parser", "from reconstructed.parsers import gedcom_parser"),
    ]),
    ("_reversa_sdd/parity/harness.py", [
        ("from reconstructed import gedcom_parser as GP",
         "from reconstructed.parsers import gedcom_parser as GP"),
    ]),
    ("_reversa_sdd/parity/_check_split_types.py", [
        ("from reconstructed import gedcom_parser as U",
         "from reconstructed.parsers import gedcom_parser as U"),
    ]),
]


def le(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.read()


# A validacao da fase 1 acontece antes da movimentacao, entao os sete arquivos
# movidos ainda estao no caminho antigo. Este mapa traduz o caminho de depois
# para o de antes, e nada mais.
PRE = {"src/reconstructed/" + destino: "src/reconstructed/" + origem for origem, destino in MOVES}


def grava(caminho, texto):
    with open(caminho, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)


def main() -> int:
    falhas = []

    print("=" * 78)
    print("FASE 1, VALIDACAO: nada foi escrito ainda")
    print("=" * 78)
    for rel, pares in EDITS:
        alvo = os.path.join(ROOT, PRE.get(rel, rel))
        if not os.path.exists(alvo):
            falhas.append("%s nao existe" % rel)
            continue
        texto = le(alvo)
        for antes, depois in pares:
            n = texto.count(antes)
            if n != 1:
                falhas.append("%s: %r aparece %d vezes, e nao uma" % (rel, antes[:50], n))
    print("  arquivos na tabela: %d" % len(EDITS))
    print("  linhas a reescrever: %d" % sum(len(p) for _, p in EDITS))
    if falhas:
        print("\n  ABORTADO, %d problema(s):" % len(falhas))
        for f in falhas:
            print("    " + f)
        return 1
    print("  todas as linhas aparecem exatamente uma vez")

    print("\nFASE 2, SUBPACOTES")
    for nome, doc in INITS:
        destino = os.path.join(PACOTE, nome, "__init__.py")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        if os.path.exists(destino):
            print("  ja existe   %s/__init__.py" % nome)
            continue
        grava(destino, doc)
        print("  criado      %s/__init__.py" % nome)

    print("\nFASE 3, MOVIMENTACAO")
    for origem, destino in MOVES:
        de = os.path.join(PACOTE, origem)
        para = os.path.join(PACOTE, destino)
        if not os.path.exists(de):
            falhas.append("nao existe para mover: %s" % origem)
            continue
        os.makedirs(os.path.dirname(para), exist_ok=True)
        shutil.move(de, para)
        print("  %-26s -> %s" % (origem, destino))

    print("\nFASE 4, IMPORT")
    for rel, pares in EDITS:
        alvo = os.path.join(ROOT, rel)
        texto = le(alvo)
        for antes, depois in pares:
            if texto.count(antes) != 1:
                falhas.append("%s: %r deixou de ser unico" % (rel, antes[:50]))
                continue
            texto = texto.replace(antes, depois)
        grava(alvo, texto)
        print("  %-46s %d linha(s)" % (rel, len(pares)))

    print()
    print("=" * 78)
    if falhas:
        print("RESULTADO: %d PROBLEMA(S)" % len(falhas))
        for f in falhas:
            print("  " + f)
        return 1
    print("RESULTADO: REORGANIZACAO APLICADA (%d movimentos, %d linhas de import)"
          % (len(MOVES), sum(len(p) for _, p in EDITS)))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
