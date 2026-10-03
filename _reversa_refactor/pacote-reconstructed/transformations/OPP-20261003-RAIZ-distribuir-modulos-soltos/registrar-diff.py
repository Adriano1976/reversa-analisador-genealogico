"""Registra os CHG-*.diff do lote A da OPP-20261003-RAIZ, um por lote.

Estado "antes": a copia congelada em `before-after/src-antes/`, que e autoritativa
para os arquivos de `src/`. Para `tests/`, `_reversa_sdd/parity/` e `README.md`, o
inverso exato de cada edicao, com assercao de que cada trecho aparece uma vez.

As tabelas vem de `reorganizar.py`, para nao existirem duas versoes da verdade.
"""
from __future__ import annotations

import difflib
import os

from reorganizar import EDITS, MOVES, ROOT, le

HERE = os.path.dirname(os.path.abspath(__file__))
ANTES = os.path.join(HERE, "before-after", "src-antes")

LOTES = [
    ("CHG-001-utils-init.diff", ["src/reconstructed/utils/__init__.py"], True),
    ("CHG-002-movimentacao.diff", ["src/reconstructed/" + d for _, d in MOVES], False),
    ("CHG-003-import-no-pacote.diff", [
        "src/reconstructed/parsers/gedcom_parser.py",
        "src/reconstructed/parsers/csv_ingest.py",
        "src/reconstructed/core/name_normalization.py",
        "src/reconstructed/core/matching.py",
        "src/reconstructed/core/family_navigation.py",
        "src/reconstructed/core/path_finding.py",
        "src/reconstructed/reporting/mermaid_render.py",
    ], False),
    ("CHG-004-app-e-testes.diff", [
        "src/app.py",
        "tests/test_upload.py",
        "tests/test_path_search.py",
        "tests/test_dna_analysis.py",
        "tests/test_characterization_matching.py",
        "tests/test_characterization_mermaid.py",
        "tests/test_mermaid_escape.py",
        "tests/test_domain.py",
        "tests/test_upload_seguranca.py",
    ], False),
    ("CHG-005-paridade.diff", [
        "_reversa_sdd/parity/harness.py",
        "_reversa_sdd/parity/_check_split_types.py",
        "_reversa_sdd/parity/_verify_fix_gives_parity.py",
    ], False),
    ("CHG-006-readme.diff", ["README.md"], False),
]

MOVED = {"src/reconstructed/" + destino: "src/reconstructed/" + origem for origem, destino in MOVES}
EDICAO = {rel: pares for rel, pares in EDITS}

# O README foi editado a mao (a arvore), e nao consta da tabela de edicoes do
# `reorganizar.py`. O par inverso fica aqui, explicito.
README_ANTES = "\n".join([
    "│   ├── core/                   # Decisão sobre o que foi lido, sem saber de HTTP",
    "│   │   ├── cm_estimator.py     # Tradução de cM em relações prováveis (faixas heurísticas)",
    "│   │   ├── matching.py         # Índices do GEDCOM e decisão de aceitação de candidatos",
    "│   │   ├── name_normalization.py  # Normalização e decomposição de nomes (norm_name, split_name_pt)",
    "│   │   ├── path_finding.py     # Busca direta por ancestral comum (MRCA) e indireta por afinidade",
    "│   │   └── family_navigation.py   # Resolução de pessoa por nome e navegação de parentesco",
    "│   ├── reporting/              # Transformação de resultado em apresentação",
    "│   │   └── mermaid_render.py   # Emissão do diagrama Mermaid e contrato de escape do rótulo",
    "│   ├── gedcom_state.py         # Estado do GEDCOM carregado: pessoas, famílias e grafo",
    "│   ├── text_cleaning.py        # Autoridade única de limpeza de mojibake (strip_bad_utf, demojibake)",
    "│   ├── validate.py             # Validação do upload: nome visível, chave de conteúdo e GEDCOM",
    "│   ├── path_search.py          # Fachada da busca de caminhos, consumida pelo app.py",
    "│   └── dna_analysis.py         # Fachada do cruzamento GEDCOM × CSV, consumida pelo app.py",
])
README_DEPOIS = "\n".join([
    "│   ├── core/                   # Decisão sobre o que foi lido, sem saber de HTTP",
    "│   │   ├── cm_estimator.py     # Tradução de cM em relações prováveis (faixas heurísticas)",
    "│   │   ├── matching.py         # Índices do GEDCOM e decisão de aceitação de candidatos",
    "│   │   ├── name_normalization.py  # Normalização e decomposição de nomes (norm_name, split_name_pt)",
    "│   │   ├── path_finding.py     # Busca direta por ancestral comum (MRCA) e indireta por afinidade",
    "│   │   ├── family_navigation.py   # Resolução de pessoa por nome e navegação de parentesco",
    "│   │   ├── gedcom_state.py     # Estado do GEDCOM carregado: pessoas, famílias e grafo",
    "│   │   ├── path_search.py      # Fachada da busca de caminhos, consumida pelo app.py",
    "│   │   └── dna_analysis.py     # Fachada do cruzamento GEDCOM × CSV, consumida pelo app.py",
    "│   ├── reporting/              # Transformação de resultado em apresentação",
    "│   │   └── mermaid_render.py   # Emissão do diagrama Mermaid e contrato de escape do rótulo",
    "│   └── utils/                  # Ferramentas utilitárias, sem papel no núcleo",
    "│       ├── text_cleaning.py    # Autoridade única de limpeza de mojibake (strip_bad_utf, demojibake)",
    "│       └── validate.py         # Validação do upload: nome visível, chave de conteúdo e GEDCOM",
])


def inverso(rel):
    texto = le(os.path.join(ROOT, rel))
    for antes, depois in EDICAO[rel]:
        n = texto.count(depois)
        if n != 1:
            raise SystemExit("%s: %r aparece %d vezes" % (rel, depois[:55], n))
        texto = texto.replace(depois, antes)
    return texto


def antes_de(rel):
    atual = le(os.path.join(ROOT, rel))
    if rel == "README.md":
        n = atual.count(README_DEPOIS)
        if n != 1:
            raise SystemExit("README.md: a arvore nova aparece %d vezes" % n)
        return atual.replace(README_DEPOIS, README_ANTES), atual
    if rel in MOVED:
        return le(os.path.join(ANTES, MOVED[rel].replace("src/", "", 1))), atual
    if rel in EDICAO:
        return inverso(rel), atual
    return None, atual


def diff(antes, depois, nome_antes, nome_depois):
    return "".join(difflib.unified_diff(
        antes.splitlines(keepends=True), depois.splitlines(keepends=True),
        fromfile=nome_antes, tofile=nome_depois, n=3))


def main() -> int:
    print("=" * 78)
    print("REGISTRO DOS DIFFS DO LOTE A DA OPP-20261003-RAIZ")
    print("=" * 78)
    total = 0
    for arquivo, alvos, sao_novos in LOTES:
        corpo = []
        for rel in alvos:
            antes, depois = antes_de(rel)
            if sao_novos and antes is None:
                corpo.append(diff("", depois, "/dev/null", "b/" + rel))
            elif rel in MOVED:
                origem = MOVED[rel]
                corpo.append("rename from %s\nrename to %s\n" % (origem, rel))
                corpo.append(diff(antes, depois, "a/" + origem, "b/" + rel))
            else:
                corpo.append(diff(antes, depois, "a/" + rel, "b/" + rel))
        texto = "".join(corpo)
        with open(os.path.join(HERE, arquivo), "w", encoding="utf-8", newline="") as fh:
            fh.write(texto)
        print("  %-34s %2d arquivo(s)  %6d bytes" % (arquivo, len(alvos), len(texto.encode("utf-8"))))
        total += len(alvos)
    print()
    print("=" * 78)
    print("RESULTADO: 6 LOTES, %d ARQUIVOS TOCADOS" % total)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
