"""O grafico do cartao "Manoel da Silva Vieira (25,4 cM)": quais dados o produzem.

Roda o caminho de PRODUCAO para esse par (raiz Adriano Santos x o match aceito) e mostra:
o caminho documental, o ancestral comum, o casal do ancestral e o texto Mermaid emitido.
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.diagram_domain import resolvedor_de_diagrama  # noqa: E402
from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

GED = os.path.join(RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")

arvore = carregar_arvore(GED)
people = arvore[0]
deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
resultados, _d, _m = dna_analysis(CSV, "Adriano Santos", deps, arvore)

alvo = "Manoel da Silva Vieira"
r = next((x for x in resultados if x["match_name"] == alvo), None)
assert r, "nao achei o cartao"

doc = r["documentary"]
raiz_id = (doc.get("person_a") or {}).get("id")
match_id = (doc.get("person_b") or {}).get("id")
caminho = (doc.get("path") or {}).get("ids") or []
comum = (doc.get("common_ancestor") or {}).get("id")

print("=" * 100)
print("OS DADOS QUE ALIMENTAM O GRAFICO")
print("=" * 100)
print(f"   cartao            : Analise de conexao com {r['match_name']}")
print(f"   cM                : {r['cm']}")
print(f"   confronto         : {(r['comparison'] or {}).get('label')}")
print(f"   rotulo documental : {doc.get('label')}")
print(f"   meioses           : {doc.get('meioses')}")
print(f"   p1 (raiz)         : {raiz_id} {get_name(people[raiz_id])}")
print(f"   p2 (o match)      : {match_id} {get_name(people[match_id])}")
print(f"   ancestral comum   : {comum} {get_name(people[comum]) if comum else '-'}")
print()
print(f"   caminho ({len(caminho)} nos):")
for i, pid in enumerate(caminho):
    marca = ""
    if pid == comum:
        marca = "   <-- ANCESTRAL COMUM"
    if pid in (raiz_id, match_id):
        marca += "   <-- ponta"
    print(f"      {i:>2}. {pid} {get_name(people[pid])}{marca}")

pos_comum = caminho.index(comum) if comum in caminho else -1
print()
print(f"   posicao do ancestral comum no caminho: {pos_comum} (0 = primeira pessoa)")
print(f"   e ancestralidade direta? {pos_comum in (-1, 0, len(caminho) - 1)}")

dominio = resolvedor_de_diagrama(arvore)
conjuges = dominio["get_spouses"](comum) if comum else []
print(f"   conjuge(s) do ancestral comum: {[(c, get_name(people[c])) for c in conjuges]}")

print()
print("=" * 100)
print("O TEXTO MERMAID EMITIDO (e o que cada linha significa)")
print("=" * 100)
for linha in (r["mermaid_data"] or "").splitlines():
    print(f"   {linha}")
