"""Panorama do caso real: roda a analise de producao contra os arquivos reais e mostra
(a) o cartao da Therezinha, (b) o parentesco exibido no cartao, (c) quantos cartoes tem
`match_name` (GEDCOM) diferente de `csv_name` (CSV).
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias  # noqa: E402
from core.dna_analysis import dna_analysis  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

GED = os.path.join(RAIZ, "src", "uploads", "c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")

deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
arvore = carregar_arvore(GED)

for raiz_nome in ("Adriano Santos", "Sandro"):
    try:
        resultados, descartados, mensagem = dna_analysis(CSV, raiz_nome, deps, arvore)
    except Exception as erro:
        print(f"raiz {raiz_nome!r}: {type(erro).__name__}: {erro}")
        continue
    print("=" * 78)
    print(f"raiz: {raiz_nome!r} -> {mensagem}")
    print("=" * 78)

    divergentes = [r for r in resultados if r["match_name"] != r["csv_name"]]
    print(f"cartoes: {len(resultados)} | com nome do GEDCOM != nome do CSV: {len(divergentes)}")
    for r in divergentes[:12]:
        print(f"   CSV: {r['csv_name']}")
        print(f"   GED: {r['match_name']}  ({r['cm']} cM)")
    print()

    for r in resultados:
        if "Therezinha Carvalho do Nascimento Souza" in (r["csv_name"] or ""):
            print("--- O CARTAO DA THEREZINHA ---")
            print(f"   cabecalho/indice (match_name): {r['match_name']}")
            print(f"   secao 2 (csv_name)           : {r['csv_name']}")
            print(f"   cM                           : {r['cm']}")
            print(f"   kit                          : {r['kit']}")
            doc = r["documentary"]
            print(f"   parentesco exibido           : {doc.get('label')} ({doc.get('status')})")
            print(f"   caminho                      : {r['text_path'][:160]!r}")
            print(f"   xref do match documental     : {(doc.get('person_b') or {}).get('id')}")
    break
