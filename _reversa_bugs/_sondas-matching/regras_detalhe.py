"""Complemento da comparacao: os casos detalhados e o que a regra de janela faz por cartao.

Responde tres perguntas que o resumo nao fecha:
  1. das 10 escolhas com idade impossivel, quantas tem ALTERNATIVA melhor e quantas nao tem?
  2. a variante "prenome primeiro" tambem PIORA algum cartao? (medido, nao suposto)
  3. o que a regra de janela faria se, em vez de descartar, apenas AVISASSE?
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import birth_date, parse_year  # noqa: E402
from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.name_normalization import norm_name  # noqa: E402
from core.path_finding import find_ancestral_path  # noqa: E402
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
raiz_id = next(pid for pid, p in people.items() if "adriano santos" in get_name(p).lower())
ged_index, surname_index, features = build_ged_indexes(arvore)

ANO, IDADE_MAX = 2026, 115


def idade(pid):
    ano = parse_year(birth_date(people, pid))
    return (ANO - ano) if ano else None


print("=" * 100)
print("1. DAS ESCOLHAS COM IDADE IMPOSSIVEL: ha alternativa melhor?")
print("=" * 100)
sem_alternativa = com_alternativa = 0
for r in resultados:
    pid = (r["documentary"].get("person_b") or {}).get("id")
    if not pid:
        continue
    id_atual = idade(pid)
    if id_atual is None or id_atual <= IDADE_MAX:
        continue
    cands, _motivo = match_candidates(arvore, r["csv_name"], r["cm"], ged_index, surname_index, features)
    alternativas = [(p, idade(p)) for p in cands if p != pid]
    boas = [(p, i) for p, i in alternativas if i is not None and i <= IDADE_MAX]
    if boas:
        com_alternativa += 1
        marca = "TEM alternativa"
    else:
        sem_alternativa += 1
        marca = "SEM alternativa -> so resta avisar"
    print(f"   {r['csv_name'][:36]:<36} ({id_atual} anos)  {marca}")
    print(f"      escolhido : {get_name(people[pid])[:34]:<34} nasc {birth_date(people, pid)}")
    print(f"      candidatos: {len(cands)}"
          + ("" if not alternativas else
             "  |  " + "; ".join(f"{get_name(people[p])[:24]} ({i} anos)" for p, i in alternativas[:3])))
print()
print(f"   COM alternativa melhor : {com_alternativa}")
print(f"   SEM alternativa melhor : {sem_alternativa}")

print()
print("=" * 100)
print("2. O QUE A REGRA DE JANELA FARIA, SE APENAS AVISASSE (nao descartasse)")
print("=" * 100)
marcaria = []
for r in resultados:
    pid = (r["documentary"].get("person_b") or {}).get("id")
    if not pid:
        continue
    i = idade(pid)
    if i is not None and i > IDADE_MAX:
        marcaria.append((r["csv_name"], get_name(people[pid]), birth_date(people, pid), i))
print(f"   cartoes que ganhariam o selo 'identidade nao confere' : {len(marcaria)} de {len(resultados)}")
print(f"   cartoes descartados pela regra (perderiam a evidencia) : 0  <-- se apenas avisar")
for csv_nome, nome, nasc, i in sorted(marcaria, key=lambda t: -t[3]):
    print(f"      {csv_nome[:34]:<34} -> {nome[:28]:<28} {str(nasc)[:14]:<14} ({i} anos)")

print()
print("=" * 100)
print("3. A VARIANTE 'PREMOME PRIMEIRO' PIORA ALGUM CARTAO?")
print("=" * 100)
from thefuzz import fuzz  # noqa: E402
from core.name_normalization import split_name_pt  # noqa: E402

pioram = []
for r in resultados:
    pid = (r["documentary"].get("person_b") or {}).get("id")
    if not pid:
        continue
    cands, _ = match_candidates(arvore, r["csv_name"], r["cm"], ged_index, surname_index, features)
    if len(cands) < 2:
        continue
    given_csv = norm_name(split_name_pt(r["csv_name"])[0])
    def dado(p):
        feat = features[p]
        return max((fuzz.ratio(given_csv, g) for g in feat["given_tokens"]), default=0)
    por_given = max(cands, key=lambda p: (dado(p), p))
    if por_given != pid:
        i_atual, i_nova = idade(pid), idade(por_given)
        mudou_para_pior = (i_atual is not None and i_atual <= IDADE_MAX
                           and i_nova is not None and i_nova > IDADE_MAX)
        if mudou_para_pior:
            pioram.append((r["csv_name"], pid, i_atual, por_given, i_nova))
        print(f"   {r['csv_name'][:34]:<34}")
        print(f"      producao : {get_name(people[pid])[:30]:<30} nasc {birth_date(people, pid)} ({i_atual} anos)")
        print(f"      prenome  : {get_name(people[por_given])[:30]:<30} nasc {birth_date(people, por_given)} ({i_nova} anos)"
              + ("   <-- PIORA" if mudou_para_pior else ""))
print()
print(f"   cartoes em que a variante escolheria alguem de janela IMPOSSIVEL: {len(pioram)}")
