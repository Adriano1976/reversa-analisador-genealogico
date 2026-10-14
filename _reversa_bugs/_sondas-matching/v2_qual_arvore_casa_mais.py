"""Qual arvore casa mais gente do CSV? V1 (35.460) contra V2 (13.716).

Roda o matching de PRODUCAO para cada arvore, com o mesmo CSV, e compara:
  - conexoes aceitas / descartadas
  - quantas tem caminho documental
  - quantas tem parentesco com a raiz

So LE os arquivos.
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")
ARQUIVOS = {
    "V1 (arvore ativa)": os.path.join(
        RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged"),
    "V2 (enviado agora)": (
        r"C:\Users\venda\.dsh\attachments\v1\files\34"
        r"\343924dd424b3fba0dd221814e2ad3a8c72e48ff7125de903aee3b4c3319332a"
        r"\Adriano_Santos_V2.ged"),
}

deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)

for rotulo, caminho in ARQUIVOS.items():
    if not os.path.isfile(caminho):
        print(f"{rotulo}: arquivo ausente")
        continue
    arvore = carregar_arvore(caminho)
    try:
        resultados, descartados, mensagem = dna_analysis(CSV, "Adriano Santos", deps, arvore)
    except Exception as erro:
        print(f"{rotulo}: FALHOU -> {type(erro).__name__}: {erro}")
        continue
    com_caminho = sum(1 for r in resultados if (r["documentary"].get("path") or {}).get("ids"))
    com_grafo = sum(1 for r in resultados if r["mermaid_data"])
    avisos = sum(1 for r in resultados if r["identidade"] == "a_confirmar")
    print("=" * 90)
    print(f"{rotulo}  ({len(arvore[0]):,} pessoas)")
    print("=" * 90)
    print(f"   {mensagem}")
    print(f"   conexoes aceitas          : {len(resultados)}")
    print(f"   descartadas               : {len(descartados)}")
    print(f"   com caminho documental    : {com_caminho}")
    print(f"   com grafo Mermaid         : {com_grafo}")
    print(f"   identidade a confirmar    : {avisos}")
    print()
