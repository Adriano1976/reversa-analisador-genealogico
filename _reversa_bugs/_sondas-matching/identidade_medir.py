"""Mede o impacto do caminho 3: quantos cartoes cada DEFINICAO de divergencia marca.

A pergunta que este script responde: se a tela passar a avisar "identidade a confirmar"
quando o nome do CSV e o nome da pessoa escolhida no GEDCOM divergirem, qual regra separa
o sinal (prenome diferente) do ruido (acento, ordem, abreviacao)?

Le os arquivos reais de src/uploads/ e NAO escreve neles.
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.name_normalization import norm_name  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from thefuzz import fuzz  # noqa: E402

GED = os.path.join(RAIZ, "src", "uploads", "c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")
RAIZ_DA_ARVORE = "Adriano Santos"

deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
arvore = carregar_arvore(GED)
resultados, descartados, mensagem = dna_analysis(CSV, RAIZ_DA_ARVORE, deps, arvore)

print(f"{mensagem}\n")


def prenome_do_csv(csv: str) -> str:
    return norm_name(csv).split()[0] if norm_name(csv).split() else ""


def prenome_do_ged(ged: str) -> str:
    return norm_name(ged).split()[0] if norm_name(ged).split() else ""


linhas = []
for r in resultados:
    csv_nome, ged_nome = r["csv_name"] or "", r["match_name"] or ""
    n_csv, n_ged = norm_name(csv_nome), norm_name(ged_nome)
    g_csv = norm_name(csv_nome).split()[0] if norm_name(csv_nome).split() else ""
    g_ged = norm_name(ged_nome).split()[0] if norm_name(ged_nome).split() else ""
    linhas.append({
        "csv": csv_nome,
        "ged": ged_nome,
        "cm": r["cm"],
        "cru": csv_nome != ged_nome,
        "norm": n_csv != n_ged,
        "tokens": set(n_csv.split()) != set(n_ged.split()),
        "fuzz_given": fuzz.ratio(g_csv, g_ged),
        "fuzz_tudo": fuzz.token_sort_ratio(n_csv, n_ged),
        "prenome_difere": g_csv != g_ged,
    })

total = len(linhas)
print("=" * 100)
print("QUANTOS CARTOES CADA DEFINICAO MARCA")
print("=" * 100)
definicoes = [
    ("A. Texto difere (cru)", lambda x: x["cru"]),
    ("B. Nome normalizado difere", lambda x: x["norm"]),
    ("C. Conjunto de tokens difere (ignora ordem)", lambda x: x["tokens"]),
    ("D. Prenome normalizado difere", lambda x: x["prenome_difere"]),
    ("E. Prenome difere E ainda assim foi aceito com similaridade alta (>=90)",
     lambda x: x["prenome_difere"] and x["fuzz_tudo"] >= 90),
]
for rotulo, teste in definicoes:
    marcados = [x for x in linhas if teste(x)]
    print(f"   {rotulo:<62} {len(marcados):>3} de {total}")

print()
print("=" * 100)
print("OS CARTOES QUE A DEFINICAO D (PREMOME DIFERE) MARCA")
print("=" * 100)
print(f"   {'similaridade':>12} {'prenome':>8} {'cM':>7}  CSV -> GEDCOM")
for x in sorted((l for l in linhas if l["prenome_difere"]),
                key=lambda l: -l["fuzz_tudo"]):
    print(f"   {x['fuzz_tudo']:>12} {x['fuzz_given']:>8} {x['cm']:>7}  "
          f"{x['csv']}  ->  {x['ged']}")

print()
print("=" * 100)
print("OS CARTOES QUE A DEFINICAO D NAO MARCA (ruido que fica calado)")
print("=" * 100)
for x in linhas:
    if not x["prenome_difere"] and x["cru"]:
        print(f"   {x['csv']}  ->  {x['ged']}")
