"""Refina a regra de "identidade a confirmar" e mede o que sobra.

Pergunta: qual regra separa FALSO POSITIVO PERIGOSO (prenome de outra pessoa, aceito com
similaridade alta) de VARIACAO DE GRAFIA (Camila/Camilla, Therezinha/Terezinha)?

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
LIMITE = 12   # primeiro nome nunca passa disto em portugues; corta o efeito do sobrenome
MIN_FUZZ = 85  # a similaridade que a aceitacao ja exigia nos ramos principais


def _prenome(nome: str) -> str:
    partes = norm_name(nome).split()
    return partes[0] if partes else ""


def classificar(csv_nome: str, ged_nome: str) -> str:
    """'confirmada' | 'grafia' | 'a_confirmar' — a regra proposta."""
    n_csv, n_ged = norm_name(csv_nome), norm_name(ged_nome)
    if n_csv == n_ged:
        return "confirmada"
    p_csv, p_ged = _prenome(csv_nome), _prenome(ged_nome)
    if p_csv == p_ged:
        return "grafia"
    a = p_csv[:LIMITE]
    b = p_ged[:LIMITE]
    if fuzz.ratio(a, b) >= MIN_FUZZ or a[:3] == b[:3]:
        return "grafia"
    return "a_confirmar"


deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
arvore = carregar_arvore(GED)
resultados, _descartados, mensagem = dna_analysis(CSV, "Adriano Santos", deps, arvore)

print(f"{mensagem}\n")

por_classe: dict[str, list] = {"confirmada": [], "grafia": [], "a_confirmar": []}
for r in resultados:
    classe = classificar(r["csv_name"] or "", r["match_name"] or "")
    por_classe[classe].append(r)

total = len(resultados)
print("=" * 100)
print("RESULTADO DA REGRA PROPOSTA")
print("=" * 100)
for classe in ("confirmada", "grafia", "a_confirmar"):
    print(f"   {classe:<14} {len(por_classe[classe]):>3} de {total}")

print()
print("=" * 100)
print("OS QUE PASSAM A AVISAR (a_confirmar) — prenome de outra pessoa")
print("=" * 100)
print(f"   {'cM':>7}  nome no CSV  ->  nome do GEDCOM")
for r in sorted(por_classe["a_confirmar"], key=lambda r: -(r["cm"] or 0)):
    print(f"   {r['cm']:>7}  {r['csv_name']}  ->  {r['match_name']}")

print()
print("=" * 100)
print("OS QUE FICAM CALADOS COMO 'grafia' (o sinal nao se perde, so nao alarma)")
print("=" * 100)
for r in sorted(por_classe["grafia"], key=lambda r: -(r["cm"] or 0)):
    print(f"   {r['csv_name']}  ->  {r['match_name']}")

print()
print("=" * 100)
print("SANIDADE: os nomes de grafia diferente sao equivalencia conhecida?")
print("=" * 100)
for r in por_classe["grafia"]:
    p_csv, p_ged = _prenome(r["csv_name"]), _prenome(r["match_name"])
    if p_csv != p_ged:
        print(f"   prenome difere: {p_csv!r} x {p_ged!r}   ({r['csv_name']})")
