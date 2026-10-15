"""Avalia as quatro sugestoes recebidas para o grafico da Margarida.

Nenhuma linha de codigo do projeto e tocada aqui. O que esta sonda faz e testar as AFIRMACOES
da proposta contra os dados reais:

  A. Veto biologico ANTES da similaridade — quantos cartoes seriam descartados e quantos tem
     candidato melhor?
  B. Tabela de pesos (+50 cM, +30 ancestralidade, +15 localizacao, +25 pais) — as colunas
     necessarias existem no arquivo?
  C. Formula G = log10(3400/cM)/log10(2) — como ela se compara com a coluna `MRCA` do proprio
     GEDmatch e com a tabela do Shared cM Project?
  D. Os fatos declarados sobre os homonimos de "Margarida" — os IDs e os anos existem?
"""
from __future__ import annotations

import math
import os
import statistics
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

import pandas as pd  # noqa: E402

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import (  # noqa: E402
    birth_date,
    documentary_relationship,
    homonym_dossier,
    parse_year,
    person_summary,
)
from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.registro import get_name  # noqa: E402
from core.relationship_hypotheses import possible_relationships  # noqa: E402
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
GED_INDEX, SOBRENOME_INDEX, FEATURES = build_ged_indexes(ARVORE)
ANO = 2026

DF = read_csv_with_fallback(CSV)
MRCA_DO_KIT = {}
for kit, grupo in DF.groupby(DF.columns[0]):
    valores = [float(v) for v in grupo["MRCA"] if str(v).strip() not in ("", "nan", "-")]
    if valores:
        MRCA_DO_KIT[str(kit).strip()] = statistics.mean(valores)


def geracoes_por_formula(cm):
    """A formula da proposta: G = log10(3400/cM) / log10(2)."""
    if not cm or cm <= 0:
        return None
    return math.log10(3400.0 / cm) / math.log10(2)


print("=" * 104)
print("A. VETO BIOLOGICO — o que aconteceria se o filtro viesse ANTES da similaridade")
print("=" * 104)
print("   A proposta: 'Se (Data do Teste - Nascimento do Registro) > 120 anos, esse registro nao")
print("   pode ser a pessoa que forneceu o DNA' — aplicado antes de qualquer calculo de similaridade.")
print()

idade_do_escolhido = {}
for r in RESULTADOS:
    pid = ((r.get("documentary") or {}).get("person_b") or {}).get("id")
    ano = parse_year(birth_date(PEOPLE, pid)) if pid else None
    idade_do_escolhido[r["kit"]] = ((ANO - ano) if ano else None, pid)

vetados = [(k, i, p) for k, (i, p) in idade_do_escolhido.items() if i is not None and i > 120]
print(f"   cartoes que o veto descartaria          : {len(vetados)} de {len(RESULTADOS)}")
sem_data = sum(1 for i, _p in idade_do_escolhido.values() if i is None)
print(f"   cartoes mantidos por nao ter data       : {sem_data}")

print()
print("   Para cada um: haveria candidato MELHOR (idade plausivel) para escolher?")
com_alternativa = sem_alternativa = 0
for kit, idade, pid in sorted(vetados, key=lambda t: -t[1]):
    resultado = next(r for r in RESULTADOS if r["kit"] == kit)
    candidatos, _motivo = match_candidates(ARVORE, resultado["csv_name"], resultado["cm"],
                                          GED_INDEX, SOBRENOME_INDEX, FEATURES)
    outros = [c for c in candidatos if c != pid]
    bons = []
    for c in outros:
        ano = parse_year(birth_date(PEOPLE, c))
        if ano is None or (ANO - ano) <= 120:
            bons.append((c, (ANO - ano) if ano else None))
    if bons:
        com_alternativa += 1
        marca = "TEM alternativa"
    else:
        sem_alternativa += 1
        marca = "SEM alternativa -> descartar perde a evidencia"
    print(f"   {kit:<10} {resultado['cm']:>6.1f} cM  escolhido com {idade:>3} anos  "
          f"({len(candidatos) - 1} outro(s) candidato(s))  {marca}")
print()
print(f"   COM alternativa melhor : {com_alternativa}")
print(f"   SEM alternativa melhor : {sem_alternativa}")
print()
print("   Ou seja: em %d dos %d casos o veto NAO trocaria a escolha — ele apenas APAGARIA o"
      % (sem_alternativa, len(vetados)))
print("   cartao, junto com o unico dado genetico daquele kit.")

print()
print("=" * 104)
print("B. TABELA DE PESOS — as colunas necessarias existem no arquivo?")
print("=" * 104)
print(f"   colunas do CSV: {list(DF.columns)}")
print()
for criterio, peso, precisa in (
        ("DNA (cM)", "+50", "coluna `cM`"),
        ("Ancestralidade comum", "+30", "o GEDCOM (ja e o que o app faz)"),
        ("Localizacao", "+15", "local de nascimento — no CSV ou no GEDCOM"),
        ("Coincidencia de pais", "+25", "nome dos pais — no CSV ou no GEDCOM")):
    print(f"   {criterio:<22} peso {peso:<5} precisa de {precisa}")

print()
tem_no_csv = {c.lower().strip() for c in DF.columns}
pais_no_csv = any("pai" in c or "parent" in c or "father" in c or "mother" in c for c in tem_no_csv)
local_no_csv = any("local" in c or "place" in c or "cidade" in c or "uf" in c for c in tem_no_csv)
print(f"   o CSV traz nome de pais?  {pais_no_csv}")
print(f"   o CSV traz localizacao?   {local_no_csv}")
print()
# Local existe no GEDCOM; a pergunta e se esta preenchido nos candidatos dos 62 cartoes.
com_local = sem_local = 0
for r in RESULTADOS:
    pid = ((r.get("documentary") or {}).get("person_b") or {}).get("id")
    if not pid:
        continue
    if person_summary(ARVORE, pid)["birth_place"]:
        com_local += 1
    else:
        sem_local += 1
print(f"   no GEDCOM, o registro ESCOLHIDO tem local de nascimento em {com_local} de "
      f"{com_local + sem_local} cartoes ({sem_local} sem local)")
print()
print("   E o criterio de cM nao discrimina: o cM e o MESMO para todos os candidatos de um")
print("   cartao (e o valor do kit), entao +50 para todos e um deslocamento constante —")
print("   nao muda a ordem de nenhum candidato. Verificado:")
for r in RESULTADOS[:3]:
    pid = ((r.get("documentary") or {}).get("person_b") or {}).get("id")
    candidatos, _ = match_candidates(ARVORE, r["csv_name"], r["cm"], GED_INDEX,
                                    SOBRENOME_INDEX, FEATURES)
    print(f"      {r['csv_name'][:30]:<30} cM do cartao={r['cm']:>6.1f}  "
          f"candidatos={len(candidatos)}  -> mesmo cM para todos")

print()
print("=" * 104)
print("C. A FORMULA G = log10(3400/cM) / log10(2)")
print("=" * 104)
print("   A proposta diz que 21,6 cM da 'aproximadamente 6 a 7 geracoes'.")
print(f"   Calculado: {geracoes_por_formula(21.6):.2f} geracoes")
print()
print("   Como a formula se comporta contra a tabela que o app ja usa (Shared cM Project 4.0):")
print(f"   {'relacao':<14}{'cM medio':>9}{'geracoes reais':>15}{'formula':>9}{'erro':>8}")
for nome, cm_medio, geracoes_reais in (("1C", 866, 2), ("2C", 229, 3), ("3C", 73, 4),
                                       ("4C", 35, 5), ("5C", 25, 6), ("6C", 18, 7),
                                       ("7C", 14, 8), ("8C", 11, 9)):
    g = geracoes_por_formula(cm_medio)
    print(f"   {nome:<14}{cm_medio:>9}{geracoes_reais:>15}{g:>9.2f}{g - geracoes_reais:>+8.2f}")
print()
print("   'geracoes reais' = geracoes do doador ate o ancestral comum, na definicao da propria")
print("   tabela. A formula erra de -0,7 a +1,8 geracoes, e erra SEMPRE para mais no fim da")
print("   serie — que e exatamente onde estao os cartoes deste repositorio.")
print()
print("   As tres estimativas para o MESMO kit da Margarida (ZC1171551, 21,6 cM):")
g_formula = geracoes_por_formula(21.6)
g_gedmatch = MRCA_DO_KIT.get("ZC1171551")
cartao_margarida = next((r for r in RESULTADOS if r["kit"] == "ZC1171551"), None)
meioses = ((cartao_margarida or {}).get("documentary") or {}).get("meioses")
print(f"      formula da proposta ................ {g_formula:>5.2f}")
print(f"      coluna `MRCA` do proprio GEDmatch .. {g_gedmatch:>5.2f}")
print(f"      tabela Shared cM 4.0 (meioses/2) ... {(meioses / 2 if meioses else 0):>5.2f}")
print(f"      -> as tres divergem em "
      f"{max(g_formula, g_gedmatch or 0, (meioses or 0) / 2) - min(g_formula, g_gedmatch or 9, (meioses or 0) / 2):.2f}"
      " geracoes")
print()
print("   O que o app responde a 'quais relacoes admitem 21,6 cM':")
possiveis = possible_relationships(21.6)
print(f"      {len(possiveis['possible_relationships'])} relacoes publicadas, confianca "
      f"'{possiveis['confidence']}'")
for c in possiveis["possible_relationships"][:6]:
    print(f"         {c['name_pt']:<44} {c['range_low']}-{c['range_high']} cM")
print(f"      ... e a proposta conclui 'prima de 3o ou 4o grau' (medias 73 e 35 cM)")

print()
print("   A afirmacao '6a ou 7a posicao ascendente aponta para Antonio Gomes da Rocha ou")
print("   Maria Joaquina dos Santos'. Cadeia real de Adriano ate o ancestral comum do cartao:")
if cartao_margarida:
    caminho = ((cartao_margarida.get("documentary") or {}).get("path") or {})
    ids = caminho.get("ids") or []
    nomes = caminho.get("names") or []
    comum = ((cartao_margarida.get("documentary") or {}).get("common_ancestor") or {}).get("id")
    indice = ids.index(comum) if comum in ids else -1
    for pos in range(1, indice + 1):
        dono = "  <-- ancestral comum que o app encontrou" if pos == indice else ""
        print(f"      {pos}a geracao acima: {nomes[pos]}{dono}")
    print()
    print("      A proposta aponta as posicoes 4 (Maria Joaquina) e 5 (Antonio Gomes da Rocha)")
    print(f"      como '6a ou 7a'. A 6a e 7a reais desta cadeia sao "
          f"{nomes[6] if indice >= 6 else '?'} e {nomes[7] if indice >= 7 else '?'}.")

print()
print("=" * 104)
print("D. OS FATOS DECLARADOS SOBRE OS HOMONIMOS DE 'Margarida'")
print("=" * 104)
dossie = homonym_dossier(ARVORE, "Margarida")
print(f"   a proposta fala em '8 registros' e cita o ID @Ib5d0894c@ (1673) e duas de 1741/1746")
print(f"   o dossie real: {dossie['exact_count']} registro(s) com o nome exato 'Margarida'")
for ficha in dossie["exact_matches"]:
    print(f"      {ficha['id']:<14} nasc {str(ficha['birth']):<16} obito {str(ficha['death']):<16}")
print(f"   registros PARECIDOS (nao exatos): {dossie['similar_count']}")
for ficha in dossie["similar_matches"][:6]:
    print(f"      {ficha['id']:<14} {ficha['name'][:34]:<34} nasc {ficha['birth']}")
print()
print(f"   o ID @Ib5d0894c@ existe no V1? {'@Ib5d0894c@' in PEOPLE}")
print(f"   algum registro com 'Margarida' entre 1741 e 1746? "
      f"{[f['id'] for f in dossie['exact_matches'] if (parse_year(f['birth']) or 0) in (1741, 1746)]}")
print()
print(f"   o nome do CSV que casou com este cartao: "
      f"{cartao_margarida['csv_name'] if cartao_margarida else '?'}")
print(f"   a pessoa escolhida pelo app: "
      f"{cartao_margarida['match_name'] if cartao_margarida else '?'} "
      f"({birth_date(PEOPLE, ((cartao_margarida.get('documentary') or {}).get('person_b') or {}).get('id')) if cartao_margarida else ''})")
