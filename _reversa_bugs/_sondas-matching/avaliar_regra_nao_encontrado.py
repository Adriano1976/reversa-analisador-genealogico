"""A regra proposta: cartao com caminho documental MAS janela de vida impossivel passa a ser
apresentado como "Parentesco documental nao encontrado" — como os outros.

Diferente do veto (que descartaria o cartao), esta regra MANTEM a evidencia genetica e apenas
para de afirmar o parentesco documental. Esta sonda mede o que exatamente muda:

  A. Quantos cartoes a regra alcanca, e quais.
  B. O que se perde com eles (caminho, ancestral comum, e se o ancestral e COMPARTILHADO).
  C. O que acontece com o CONFRONTO quando o estado do documental vira `not_found`.
  D. A diferenca de sentido entre "nao encontrado" de verdade e "nao encontrado" por regra.

So LE. Nao escreve nada fora desta pasta.
"""
from __future__ import annotations

import collections
import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import birth_date, parse_year  # noqa: E402
from core.evidence_comparison import compare  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

GED = os.path.join(RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")
ARVORE = carregar_arvore(GED)
PEOPLE = ARVORE[0]
DEPS = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                    anotar_profundidade)
RESULTADOS, _D, _M = dna_analysis(CSV, "Adriano Santos", DEPS, ARVORE)


def tem_caminho(r):
    return bool(((r.get("documentary") or {}).get("path") or {}).get("ids"))


print("=" * 106)
print("A. QUANTOS CARTOES A REGRA ALCANCA")
print("=" * 106)
com_caminho = [r for r in RESULTADOS if tem_caminho(r)]
sem_caminho = [r for r in RESULTADOS if not tem_caminho(r)]
print(f"   cartoes com caminho documental : {len(com_caminho)}")
print(f"   cartoes sem caminho (ja dizem 'nao encontrado') : {len(sem_caminho)}")
print()
print("   Dos COM caminho, quais tem a janela de vida acusando:")
alcancados = []
for r in com_caminho:
    janela = r.get("janela_de_vida")
    if janela in ("impossivel", "suspeita"):
        alcancados.append(r)
        print(f"      {r['kit']:<10} {r['cm']:>6.1f} cM  {janela:<10} "
              f"{r['idade_na_arvore']:>4} anos  {r['match_name'][:30]}")
print()
print(f"   -> a regra muda {len(alcancados)} cartao(oes) de {len(RESULTADOS)}")

print()
print("=" * 106)
print("B. O QUE SE PERDE COM ELES")
print("=" * 106)
# Quais ancestrais comuns sao COMPARTILHADOS entre cartoes (o achado de convergencia).
grupos = collections.defaultdict(list)
for r in RESULTADOS:
    doc = r.get("documentary") or {}
    ancestral = doc.get("common_ancestor") or {}
    if ancestral.get("id"):
        grupos[ancestral["id"]].append(r)

for r in alcancados:
    doc = r.get("documentary") or {}
    ancestral = doc.get("common_ancestor") or {}
    caminho = doc.get("path") or {}
    n_cam = 1 + len(doc.get("additional_paths") or [])
    compartilhado = grupos.get(ancestral.get("id"), [])
    print(f"   {r['kit']}  ({r['cm']:.1f} cM)  parentesco que o cartao mostra hoje:")
    print(f"      rotulo ............ {doc.get('label')}")
    print(f"      meioses ........... {doc.get('meioses')}  ({len(caminho.get('ids') or [])} nos no caminho)")
    print(f"      ancestral comum ... {ancestral.get('name')} ({ancestral.get('birth')})")
    print(f"      caminhos .......... {n_cam}")
    print(f"      grafo ............. {'SIM' if r.get('mermaid_data') else 'NAO'}")
    if len(compartilhado) > 1:
        print(f"      ANCESTRAL COMPARTILHADO com {len(compartilhado) - 1} outro(s) cartao(oes):")
        for outro in compartilhado:
            marca = "  <- este" if outro["kit"] == r["kit"] else ""
            print(f"         {outro['kit']:<10} {outro['cm']:>6.1f} cM  {outro['csv_name'][:28]}{marca}")
    else:
        print("      ancestral exclusivo deste cartao")
    print()

print("   Ancestrais comuns que so existem por causa dos cartoes alcancados:")
sozinhos = [pid for pid, lista in grupos.items()
            if all(x["kit"] in {a["kit"] for a in alcancados} for x in lista)]
print(f"      {len(sozinhos)} de {len(grupos)} ancestrais distintos")

print()
print("=" * 106)
print("C. O QUE ACONTECE COM O CONFRONTO SE O ESTADO VIRAR `not_found`")
print("=" * 106)
print("   `evidence_comparison.compare` decide pelo ESTADO: se `status == 'not_found'`, ele")
print("   entra no ramo 'sem caminho documental' e nem olha o cM. Simulando:")
print()
for r in alcancados:
    doc = dict(r.get("documentary") or {})
    doc["status"] = "not_found"
    doc["path"] = None
    simulado = compare(doc, r.get("hypotheses") or [], r.get("genetic_evidence") or {})
    print(f"   {r['kit']:<10} hoje: {r['comparison']['status']:<14} -> pela regra: {simulado['status']}")
    print(f"      hoje  : {' '.join(str(r['comparison'].get('detail') or '')[:150].split())}")
    print(f"      regra : {' '.join(str(simulado.get('detail') or '')[:150].split())}")
    print()

hoje_compara = sum(1 for r in RESULTADOS if (r.get("comparison") or {}).get("expected_range"))
print(f"   cartoes que HOJE chegam a comparar cM x parentesco : {hoje_compara} de {len(RESULTADOS)}")
restantes = [r for r in RESULTADOS if r not in alcancados]
print(f"   cartoes que chegariam a comparar pela regra ...... "
      f"{sum(1 for r in restantes if (r.get('comparison') or {}).get('expected_range'))} de {len(RESULTADOS)}")

print()
print("=" * 106)
print("D. 'NAO ENCONTRADO' DE VERDADE x 'NAO ENCONTRADO' POR REGRA")
print("=" * 106)
print("   Nos 51 cartoes sem caminho, o estado diz uma coisa sobre a ARVORE:")
exemplo = next(r for r in sem_caminho if (r.get("comparison") or {}).get("detail"))
print(f"      \"{' '.join(str(exemplo['comparison']['detail'])[:180].split())}\"")
print()
print("   Nos cartoes alcancados, a arvore TEM o caminho — o que nao fecha e a PESSOA:")
for r in alcancados:
    doc = r.get("documentary") or {}
    print(f"      {r['kit']}: caminho de {doc.get('meioses')} meioses ate "
          f"{((doc.get('common_ancestor') or {}).get('name'))} — a arvore encontrou;")
    print(f"         o que nao fecha e que {r['match_name'][:34]} nasceu em "
          f"{r['data_de_nascimento']} ({r['idade_na_arvore']} anos).")
