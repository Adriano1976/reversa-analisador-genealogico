"""Aplica o lote A da OPP-20261003-RAIZ.

Ordem, e nada e escrito antes de todas as assercoes passarem:

 1. valida que cada linha a reescrever aparece exatamente uma vez no arquivo de origem;
 2. cria `utils/__init__.py`;
 3. move os cinco modulos, sem renomear nenhum;
 4. reescreve as linhas de import e a unica citacao de caminho em docstring.

Nenhuma linha de logica e tocada.
"""
from __future__ import annotations

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PACOTE = os.path.join(ROOT, "src", "reconstructed")

INITS = [
    ("utils", '"""Ferramentas utilitarias, sem papel no nucleo."""\n'),
]

MOVES = [
    ("gedcom_state.py", "core/gedcom_state.py"),
    ("path_search.py", "core/path_search.py"),
    ("dna_analysis.py", "core/dna_analysis.py"),
    ("text_cleaning.py", "utils/text_cleaning.py"),
    ("validate.py", "utils/validate.py"),
]

PRE = {"src/reconstructed/" + destino: "src/reconstructed/" + origem for origem, destino in MOVES}

EDITS = [
    ("src/reconstructed/core/path_search.py", [
        ("from .core.family_navigation import (", "from .family_navigation import ("),
        ("from .reporting.mermaid_render import (", "from ..reporting.mermaid_render import ("),
        ("from .core.path_finding import MAX_DEPTH, MAX_HOPS, find_ancestral_path, find_indirect_path",
         "from .path_finding import MAX_DEPTH, MAX_HOPS, find_ancestral_path, find_indirect_path"),
        ("importam nomes daqui: `app.py`, `reconstructed/dna_analysis.py`,",
         "importam nomes daqui: `app.py`, `reconstructed/core/dna_analysis.py`,"),
    ]),
    ("src/reconstructed/core/dna_analysis.py", [
        ("from .core.cm_estimator import SHARED_CM_DATA, get_relationships_by_cm",
         "from .cm_estimator import SHARED_CM_DATA, get_relationships_by_cm"),
        ("from .parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback",
         "from ..parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback"),
        ("from .text_cleaning import demojibake, strip_bad_utf",
         "from ..utils.text_cleaning import demojibake, strip_bad_utf"),
        ("from .core.matching import build_ged_indexes, match_candidates",
         "from .matching import build_ged_indexes, match_candidates"),
        ("from .core.name_normalization import (", "from .name_normalization import ("),
        ("from .core.path_finding import find_ancestral_path",
         "from .path_finding import find_ancestral_path"),
        ("from .reporting.mermaid_render import generate_mermaid_graph",
         "from ..reporting.mermaid_render import generate_mermaid_graph"),
    ]),
    ("src/reconstructed/parsers/gedcom_parser.py", [
        ("from .. import gedcom_state", "from ..core import gedcom_state"),
        ("from ..gedcom_state import get_name, ref_id", "from ..core.gedcom_state import get_name, ref_id"),
    ]),
    ("src/reconstructed/parsers/csv_ingest.py", [
        ("from ..text_cleaning import demojibake", "from ..utils.text_cleaning import demojibake"),
    ]),
    ("src/reconstructed/core/name_normalization.py", [
        ("from ..text_cleaning import strip_bad_utf", "from ..utils.text_cleaning import strip_bad_utf"),
    ]),
    ("src/reconstructed/core/matching.py", [
        ("from ..gedcom_state import get_name, people", "from .gedcom_state import get_name, people"),
    ]),
    ("src/reconstructed/core/family_navigation.py", [
        ("from ..gedcom_state import child_to_family, families, get_name, people, ref_id",
         "from .gedcom_state import child_to_family, families, get_name, people, ref_id"),
    ]),
    ("src/reconstructed/core/path_finding.py", [
        ("from ..gedcom_state import people", "from .gedcom_state import people"),
        ("    from ..gedcom_state import graph", "    from .gedcom_state import graph"),
    ]),
    ("src/reconstructed/reporting/mermaid_render.py", [
        ("from ..gedcom_state import get_name, people", "from ..core.gedcom_state import get_name, people"),
    ]),
    ("src/app.py", [
        ("from reconstructed.dna_analysis import dna_analysis as dna_analysis_flow",
         "from reconstructed.core.dna_analysis import dna_analysis as dna_analysis_flow"),
        ("from reconstructed.path_search import path_search as path_search_flow",
         "from reconstructed.core.path_search import path_search as path_search_flow"),
        ("from reconstructed.validate import (", "from reconstructed.utils.validate import ("),
    ]),
    ("tests/test_upload.py", [
        ("from reconstructed import gedcom_state", "from reconstructed.core import gedcom_state"),
        ("from reconstructed.gedcom_state import get_name, ref_id",
         "from reconstructed.core.gedcom_state import get_name, ref_id"),
    ]),
    ("tests/test_path_search.py", [
        ("from reconstructed import gedcom_state", "from reconstructed.core import gedcom_state"),
        ("from reconstructed.path_search import (", "from reconstructed.core.path_search import ("),
    ]),
    ("tests/test_dna_analysis.py", [
        ("from reconstructed import gedcom_state", "from reconstructed.core import gedcom_state"),
        ("from reconstructed.dna_analysis import (", "from reconstructed.core.dna_analysis import ("),
    ]),
    ("tests/test_characterization_matching.py", [
        ("from reconstructed import gedcom_state", "from reconstructed.core import gedcom_state"),
        ("from reconstructed.dna_analysis import build_ged_indexes, dna_analysis, match_candidates",
         "from reconstructed.core.dna_analysis import build_ged_indexes, dna_analysis, match_candidates"),
    ]),
    ("tests/test_characterization_mermaid.py", [
        ("from reconstructed import gedcom_state", "from reconstructed.core import gedcom_state"),
        ("from reconstructed.path_search import path_search",
         "from reconstructed.core.path_search import path_search"),
    ]),
    ("tests/test_mermaid_escape.py", [
        ("from reconstructed.path_search import _mermaid_label, path_search",
         "from reconstructed.core.path_search import _mermaid_label, path_search"),
    ]),
    ("tests/test_domain.py", [
        ("from reconstructed.text_cleaning import (", "from reconstructed.utils.text_cleaning import ("),
    ]),
    ("tests/test_upload_seguranca.py", [
        ("from reconstructed import validate as modulo", "from reconstructed.utils import validate as modulo"),
    ]),
    ("_reversa_sdd/parity/harness.py", [
        ("from reconstructed import gedcom_state as GS", "from reconstructed.core import gedcom_state as GS"),
        ("from reconstructed import path_search as P", "from reconstructed.core import path_search as P"),
        ("from reconstructed import dna_analysis as D", "from reconstructed.core import dna_analysis as D"),
        ("from reconstructed import text_cleaning as DM", "from reconstructed.utils import text_cleaning as DM"),
    ]),
    ("_reversa_sdd/parity/_check_split_types.py", [
        ("from reconstructed import dna_analysis as D", "from reconstructed.core import dna_analysis as D"),
    ]),
    ("_reversa_sdd/parity/_verify_fix_gives_parity.py", [
        ('alvo = os.path.join(STUB, "gedcom_state.py")', 'alvo = os.path.join(STUB, "core", "gedcom_state.py")'),
    ]),
]


def le(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.read()


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
                falhas.append("%s: %r aparece %d vezes, e nao uma" % (rel, antes[:55], n))
    print("  arquivos na tabela: %d" % len(EDITS))
    print("  linhas a reescrever: %d" % sum(len(p) for _, p in EDITS))
    if falhas:
        print("\n  ABORTADO, %d problema(s):" % len(falhas))
        for f in falhas:
            print("    " + f)
        return 1
    print("  todas as linhas aparecem exatamente uma vez")

    print("\nFASE 2, SUBPACOTE")
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
        print("  %-22s -> %s" % (origem, destino))

    print("\nFASE 4, IMPORT E CITACAO DE CAMINHO")
    for rel, pares in EDITS:
        alvo = os.path.join(ROOT, rel)
        texto = le(alvo)
        for antes, depois in pares:
            if texto.count(antes) != 1:
                falhas.append("%s: %r deixou de ser unico" % (rel, antes[:55]))
                continue
            texto = texto.replace(antes, depois)
        grava(alvo, texto)
        print("  %-52s %d linha(s)" % (rel, len(pares)))

    print()
    print("=" * 78)
    if falhas:
        print("RESULTADO: %d PROBLEMA(S)" % len(falhas))
        for f in falhas:
            print("  " + f)
        return 1
    print("RESULTADO: LOTE A APLICADO (%d movimentos, %d linhas)"
          % (len(MOVES), sum(len(p) for _, p in EDITS)))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
