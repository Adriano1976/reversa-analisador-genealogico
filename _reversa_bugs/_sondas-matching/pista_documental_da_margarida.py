"""Que "pista documental" e essa, no cartao da Margarida?

A frase que eu usei — "o parentesco e real e e a unica pista documental que existe" — precisa
ser testada, e nao repetida. As perguntas:

  A. Qual e o nome que veio do CSV, e o que ele da ao matcher?
  B. Quais das 8 "Margarida" tem caminho ate o Adriano?
  C. O ancestral comum deste cartao e compartilhado com outros, ou exclusivo?
  D. A Margarida de 1673 TEM descendencia registrada? Chega a alguem contemporaneo?
  E. O ancestral comum tem outros filhos documentados — ou seja, ha outras linhas por onde o
     doador poderia descer?
  F. O que o cartao ja diz sobre a identidade (selo) deste registro?

So LE.
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import (  # noqa: E402
    birth_date,
    death_date,
    documentary_relationship,
    get_children,
    homonym_dossier,
    parse_year,
    person_summary,
)
from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.name_normalization import norm_name, split_name_pt, surname_core_tokens  # noqa: E402
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
RAIZ_ID = next(pid for pid, p in PEOPLE.items() if "adriano santos" in get_name(p).lower())
GED_INDEX, SOB, FEAT = build_ged_indexes(ARVORE)
CARTAO = next(r for r in RESULTADOS if r["kit"] == "ZC1171551")
DOC = CARTAO["documentary"]
ESCOLHIDO = DOC["person_b"]["id"]
MRCA = DOC["common_ancestor"]["id"]
ANO = 2026

print("=" * 100)
print("A. O NOME QUE VEIO DO CSV")
print("=" * 100)
print(f"   csv_name ................ {CARTAO['csv_name']!r}")
partes = split_name_pt(CARTAO["csv_name"])
print(f"   split_name_pt ........... {partes}")
print(f"   prenome(s) .............. {[norm_name(p) for p in partes[:1]]}")
print(f"   sobrenomes (core) ....... {surname_core_tokens(CARTAO['csv_name'])}")
print()
print("   O matcher decide por SOBRENOME + prenome. Com este nome, o que ele tem em maos?")
candidatos, motivo = match_candidates(ARVORE, CARTAO["csv_name"], CARTAO["cm"],
                                      GED_INDEX, SOB, FEAT)
print(f"   candidatos .............. {len(candidatos)}")
print(f"   motivo .................. {motivo}")
for pid in candidatos:
    print(f"      {pid:<14} {get_name(PEOPLE[pid])[:30]:<30} nasc {str(birth_date(PEOPLE, pid))}")

print()
print("=" * 100)
print("B. DAS 'Margarida', QUAIS TEM CAMINHO ATE O ADRIANO?")
print("=" * 100)
dossie = homonym_dossier(ARVORE, "Margarida")
for ficha in dossie["exact_matches"]:
    pid = ficha["id"]
    d = documentary_relationship(ARVORE, RAIZ_ID, pid)
    tem = bool((d.get("path") or {}).get("ids"))
    marca = "  <-- ESCOLHIDA" if pid == ESCOLHIDO else ""
    print(f"   {pid:<14} nasc {str(ficha['birth']):<16} caminho: {'SIM' if tem else 'NAO':<4}"
          f" {('(' + str(d.get('label')) + ')') if tem else ''}{marca}")

print()
print("=" * 100)
print("C. O ANCESTRAL COMUM E COMPARTILHADO OU EXCLUSIVO?")
print("=" * 100)
grupos = {}
for r in RESULTADOS:
    anc = ((r.get("documentary") or {}).get("common_ancestor") or {}).get("id")
    if anc:
        grupos.setdefault(anc, []).append(r)
for anc, lista in grupos.items():
    nome = ((lista[0]["documentary"] or {}).get("common_ancestor") or {}).get("name")
    marca = "  <-- o deste cartao" if anc == MRCA else ""
    print(f"   {str(nome)[:38]:<38} {anc:<14} {len(lista)} cartao(oes){marca}")

print()
print("=" * 100)
print("D. A 'Margarida' DE 1673 TEM DESCENDENCIA REGISTRADA?")
print("=" * 100)
print(f"   {get_name(PEOPLE[ESCOLHIDO])}  nasc {birth_date(PEOPLE, ESCOLHIDO)}  "
      f"obito {death_date(PEOPLE, ESCOLHIDO) or '—'}")
ficha = person_summary(ARVORE, ESCOLHIDO)
print(f"   conjuge(s) ... {[get_name(PEOPLE.get(s)) for s in ficha['spouses']] or '—'}")
filhos = get_children(ARVORE, ESCOLHIDO)
print(f"   filhos ....... {len(filhos)}")
for f in filhos:
    print(f"      {f:<14} {get_name(PEOPLE[f])[:34]:<34} nasc {birth_date(PEOPLE, f)}")

print()
print("=" * 100)
print("E. O ANCESTRAL COMUM: OUTRAS LINHAS POR ONDE O DOADOR PODERIA DESCER")
print("=" * 100)
print(f"   ancestral comum: {get_name(PEOPLE[MRCA])}  nasc {birth_date(PEOPLE, MRCA)}")
filhos_mrca = get_children(ARVORE, MRCA)
print(f"   filhos documentados: {len(filhos_mrca)}")
for f in filhos_mrca:
    # quantos descendentes ao todo, e se algum e posterior a 1900
    pilha, vistos, total, recentes = [f], set(), 0, []
    while pilha:
        atual = pilha.pop()
        if atual in vistos:
            continue
        vistos.add(atual)
        total += 1
        ano = parse_year(birth_date(PEOPLE, atual))
        if ano and ano >= 1900:
            recentes.append((atual, ano))
        pilha.extend(get_children(ARVORE, atual))
    marca = "  <-- A ESCOLHIDA" if f == ESCOLHIDO else ""
    print(f"      {f:<14} {get_name(PEOPLE[f])[:30]:<30} nasc {str(birth_date(PEOPLE, f)):<14}"
          f" descendentes={total:<4} nascidos >=1900: {len(recentes)}{marca}")
    for pid, ano in recentes[:3]:
        print(f"            {get_name(PEOPLE[pid])[:34]:<34} nasc {ano}")

print()
print("=" * 100)
print("F. O QUE O CARTAO JA DIZ SOBRE A IDENTIDADE DESSE REGISTRO")
print("=" * 100)
print(f"   identidade .............. {CARTAO['identidade']}")
print(f"   identidade_aviso ........ {' '.join(str(CARTAO['identidade_aviso']).split())[:200]}")
print(f"   estado do documental .... {DOC.get('status')}")
print(f"   homonimos no dossie ..... {DOC.get('homonyms', {}).get('exact_count')}")
print(f"   janela de vida .......... {CARTAO['janela_de_vida']} ({CARTAO['idade_na_arvore']} anos)")
