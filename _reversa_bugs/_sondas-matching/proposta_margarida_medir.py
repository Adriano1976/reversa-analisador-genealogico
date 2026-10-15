"""Mede a proposta do diagrama "ARVORE DE ADRIANO SANTOS COM CORRECAO DE CONEXAO DNA (MARGARIDA)".

A proposta traz 4 regras. Tres delas ja existem no app (nao mexer nos nos do usuario, filtrar
idade do doador, desacoplar identidade). A parte NOVA, que nao estava implementada, e:

  Regra 2 (parte nova) — cruzar o cM/MRCA do CSV com a PROFUNDIDADE do caminho documental.
  Regra 4 (nova)       — preencher o hiato com nos geracionais genericos de 25-30 anos.

Esta sonda mede, nos cartoes reais:
  A. o que a regra 2-nova (MRCA do CSV x meioses documentais) marcaria;
  B. quantos desses JA sao marcados pela janela de vida (122 anos) — ou seja, o ganho real;
  C. quantos nos genericos a regra 4 precisaria inventar em cada cartao impossivel;
  D. quantos kits tem linhas com 'Overlap' divergente (a sugestao 5, ainda pendente).

So LE. Nao escreve nada fora desta pasta.
"""
from __future__ import annotations

import os
import statistics
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

import pandas as pd  # noqa: E402

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import birth_date, parse_year  # noqa: E402
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

ANO = 2026
IDADE_IMPOSSIVEL = 122
ANOS_POR_GERACAO = 30.0

print("=" * 104)
print("0. O CSV TRAZ A COLUNA 'MRCA' — E O APP A DESCARTA?")
print("=" * 104)
df = read_csv_with_fallback(CSV)
name_col, cm_col, match_id_col, match_email_col = detect_columns(df)
print(f"   colunas detectadas pelo app : name={name_col!r} cm={cm_col!r} "
      f"id={match_id_col!r} email={match_email_col!r}")
print(f"   'MRCA' e usada pelo app?    : {match_id_col == 'MRCA'}")
print(f"   colunas cruas do arquivo    : {list(df.columns)}")

agregado = aggregate_matches(df, name_col, cm_col, match_id_col, match_email_col)
print(f"   colunas do agregado         : {list(agregado.columns)}  <- o MRCA nao sobrevive aqui")

# O MRCA cru, por kit, direto do arquivo — o app nao usa.
kit_col = df.columns[0]
mrca_por_kit: dict[str, list[float]] = {}
cm_por_kit: dict[str, float] = {}
for kit, grupo in df.groupby(kit_col):
    if "MRCA" in df.columns:
        vals = [float(v) for v in grupo["MRCA"] if str(v).strip() not in ("", "nan", "-")]
        if vals:
            mrca_por_kit[str(kit).strip()] = vals
    cm_por_kit[str(kit).strip()] = float(
        pd.to_numeric(grupo[cm_col], errors="coerce").fillna(0).sum())
print(f"   kits com MRCA no arquivo    : {len(mrca_por_kit)} de {len(cm_por_kit)}")

print()
print("=" * 104)
print("A/B. REGRA 2-NOVA: MRCA IMPLICADO PELO DNA x PROFUNDIDADE DO CAMINHO DOCUMENTAL")
print("=" * 104)
print("   meioses documentais M = deg_a + deg_b (o que a arvore diz)")
print("   meioses implicadas pelo DNA M_dna = 2 x MRCA_gedmatch (os dois lados ate o ancestral)")
print("   divergencia = M / M_dna  (>= 2.0 significa: o caminho documental e 2x mais fundo)")
print()

LINHAS = []
for r in resultados:
    doc = r.get("documentary") or {}
    pid = (doc.get("person_b") or {}).get("id")
    meioses = doc.get("meioses")
    kit = str(r.get("kit") or "").strip()
    mrca_vals = mrca_por_kit.get(kit) or []
    mrca = statistics.mean(mrca_vals) if mrca_vals else None
    ano_nasc = parse_year(birth_date(people, pid)) if pid else None
    idade = (ANO - ano_nasc) if ano_nasc else None
    anc = doc.get("common_ancestor") or {}
    ano_anc = parse_year(anc.get("birth"))
    m_dna = (2 * mrca) if mrca else None
    div = (meioses / m_dna) if (meioses and m_dna) else None
    ja_marcado = bool(idade is not None and idade > IDADE_IMPOSSIVEL)
    LINHAS.append({
        "csv": r["csv_name"], "kit": kit, "cm": r.get("cm"), "mrca": mrca,
        "meioses": meioses, "m_dna": m_dna, "div": div, "label": doc.get("label"),
        "idade": idade, "ano_anc": ano_anc, "ja": ja_marcado, "pid": pid,
    })

com_caminho = [l for l in LINHAS if l["meioses"]]
com_mrca = [l for l in com_caminho if l["mrca"]]
print(f"   cartoes com caminho documental      : {len(com_caminho)} de {len(LINHAS)}")
print(f"   ... e com MRCA no CSV para comparar : {len(com_mrca)}")

for limiar in (1.3, 1.6, 2.0, 2.5):
    marcaria = [l for l in com_mrca if l["div"] and l["div"] >= limiar]
    novos = [l for l in marcaria if not l["ja"]]
    print(f"   limiar {limiar}: marcaria {len(marcaria):>3} cartoes | "
          f"ja marcados pela janela: {len(marcaria) - len(novos):>3} | NOVOS: {len(novos):>3}")

print()
print("-" * 104)
print("   Os cartoes que a regra 2-nova marcaria e a janela de vida NAO pega (limiar 2.0):")
print("-" * 104)
print(f"   {'kit':<10} {'cM':>6} {'MRCA':>5} {'M_doc':>6} {'M_dna':>6} {'div':>5} {'idade':>6}  parentesco documental")
novos20 = [l for l in com_mrca if l["div"] and l["div"] >= 2.0 and not l["ja"]]
for l in sorted(novos20, key=lambda x: -x["div"]):
    print(f"   {l['kit']:<10} {l['cm']:>6.1f} {l['mrca']:>5.2f} {l['meioses']:>6} "
          f"{l['m_dna']:>6.1f} {l['div']:>5.2f} {str(l['idade']):>6}  {str(l['label'])[:44]}")
print(f"   -> {len(novos20)} cartoes")

print()
print("-" * 104)
print("   Contraprova: os cartoes que a janela JA marca — a regra 2-nova concorda?")
print("-" * 104)
for l in sorted([x for x in LINHAS if x["ja"]], key=lambda x: -(x["idade"] or 0)):
    d = f"{l['div']:.2f}" if l["div"] else "  - "
    print(f"   {l['kit']:<10} {l['cm']:>6.1f} {str(l['mrca']):>5} {str(l['meioses']):>6} "
          f"{str(round(l['m_dna'], 1) if l['m_dna'] else '-'):>6} {d:>5} {l['idade']:>6}  {str(l['label'])[:40]}")

print()
print("=" * 104)
print("C. REGRA 4: QUANTOS NOS GENERICOS O HIATO EXIGIRIA (25-30 anos por no)")
print("=" * 104)
print(f"   {'kit':<10} {'ano ancestral':>13} {'idade do no':>11} {'nos @30a':>9} {'nos @25a':>9}  cM")
total30 = total25 = 0.0
for l in sorted([x for x in LINHAS if x["ano_anc"]], key=lambda x: x["ano_anc"]):
    hiato = ANO - l["ano_anc"]
    if hiato <= IDADE_IMPOSSIVEL:
        continue
    n30 = hiato / 30.0
    n25 = hiato / 25.0
    total30 += n30
    total25 += n25
    print(f"   {l['kit']:<10} {l['ano_anc']:>13} {hiato:>11} {n30:>9.1f} {n25:>9.1f}  {l['cm']}")
print(f"   -> total de nos genericos a INVENTAR: {total30:.0f} (@30a) a {total25:.0f} (@25a)")

print()
print("=" * 104)
print("D. SUGESTAO 5 (pendente): linhas do MESMO kit com 'Overlap' divergente")
print("=" * 104)
if "Overlap" in df.columns:
    divergentes = []
    for kit, grupo in df.groupby(kit_col):
        vals = {str(v).strip() for v in grupo["Overlap"] if str(v).strip() not in ("", "nan")}
        if len(vals) > 1:
            divergentes.append(str(kit).strip())
    print(f"   kits cujas linhas divergem no 'Overlap': {len(divergentes)} de {df[kit_col].nunique()}")
    for kit in divergentes[:12]:
        vals = sorted({str(v).strip() for v in df[df[kit_col] == kit]["Overlap"]})
        print(f"      {kit:<10} overlap: {', '.join(vals)}")
    print("   (Overlap diferente por linha = segmentos de limiares/fontes distintos;")
    print("    somar o cM dessas linhas mistura evidencias de qualidade diferente.)")
else:
    print("   coluna Overlap nao encontrada")
