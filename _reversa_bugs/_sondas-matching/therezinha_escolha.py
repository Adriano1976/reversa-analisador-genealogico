"""Sonda de diagnostico: por que o cartao de "Therezinha Carvalho do Nascimento Souza"
sai rotulado com o nome de "Soraia Carvalho do Nascimento Souza".

Nao e teste e nao altera nada: le os dois arquivos reais da pasta de uploads (so leitura) e
chama o motor de matching de producao (`build_ged_indexes` + `match_candidates`).
"""
from __future__ import annotations

import os
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.genetic_evidence import build_genetic_evidence  # noqa: E402
from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.name_normalization import norm_name, surnames_set, split_name_pt  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from thefuzz import fuzz  # noqa: E402

GED = os.path.join(RAIZ, "src", "uploads", "c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")
ALVO = "Therezinha Carvalho do Nascimento Souza"

arvore = carregar_arvore(GED)
ged_index, surname_index, features = build_ged_indexes(arvore)

# ---------------------------------------------------------------------------
# 1. Quem existe na arvore com esses nomes, e quem a arvore tem parecido
# ---------------------------------------------------------------------------
print("=" * 78)
print("1. OCORRENCIAS NA ARVORE")
print("=" * 78)
for pid, pessoa in arvore[0].items():
    nome = get_name(pessoa)
    if "Carvalho do Nascimento" in nome or "Soraia" in nome:
        print(f"   {pid:>10}  {nome}")
        print(f"              norm_name -> {norm_name(nome)!r}")
        print(f"              sobrenomes -> {sorted(surnames_set(nome))}")

print()
print(f"   norm_name(CSV)  -> {norm_name(ALVO)!r}")
print(f"   split_name_pt   -> {split_name_pt(ALVO)}")

# ---------------------------------------------------------------------------
# 2. Roda o matching de producao com o cM REAL do kit NG2749622 (7.1 + 8 + 16.8)
# ---------------------------------------------------------------------------
df = read_csv_with_fallback(CSV)
evidencias, _ = build_genetic_evidence(df)

print()
print("=" * 78)
print("2. O QUE O CSV DIZ (kit NG2749622)")
print("=" * 78)
for chave_nome, por_kit in evidencias.items():
    for ev in por_kit.values():
        if ev["kit"] == "NG2749622":
            print(f"   chave normalizada : {chave_nome!r}")
            print(f"   nome no CSV       : {ev['person_name_csv']!r}")
            print(f"   total_cm          : {ev['total_cm']}")
            print(f"   linhas somadas    : {ev['records_used']}")
            print(f"   segmentos         : {[s['cm'] for s in ev['segments']]}")

print()
print("=" * 78)
print("3. MATCHING DE PRODUCAO")
print("=" * 78)
cm_do_kit = None
for por_kit in evidencias.values():
    for ev in por_kit.values():
        if ev["kit"] == "NG2749622":
            cm_do_kit = ev["total_cm"]

candidatos, motivo = match_candidates(arvore, ALVO, cm_do_kit, ged_index, surname_index, features)
print(f"   cM usado no matching : {cm_do_kit}")
print(f"   candidatos aceitos   : {candidatos}")
print(f"   motivo (se vazio)    : {motivo}")
for pid in candidatos:
    print(f"      -> {pid}  {get_name(arvore[0][pid])}")

# ---------------------------------------------------------------------------
# 4. Os numeros que decidiram: replica o scoring do pool de sobrenomes
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("4. OS NUMEROS QUE DECIDIRAM (pool de sobrenomes do CSV)")
print("=" * 78)
given_csv, surn_csv, _suf = split_name_pt(ALVO)
given_norm = norm_name(given_csv)
from core.name_normalization import drop_short_tokens  # noqa: E402

csv_surn_all = drop_short_tokens(surnames_set(ALVO))
pool = set()
for sn in surn_csv:
    pool.update(surname_index.get(sn, []))
print(f"   sobrenomes do CSV    : {sorted(csv_surn_all)}")
print(f"   tamanho do pool      : {len(pool)}")

linhas = []
for pid in pool:
    feat = features[pid]
    s_given = max((fuzz.ratio(given_norm, gg) for gg in feat["given_tokens"]), default=0)
    s_token = fuzz.token_sort_ratio(norm_name(ALVO), feat["norm"])
    s_part = fuzz.partial_ratio(norm_name(ALVO), feat["norm"])
    inter = csv_surn_all & feat["surnames"]
    linhas.append((s_given, s_token, s_part, len(inter), pid, get_name(arvore[0][pid]), sorted(feat["surnames"])))

linhas.sort(reverse=True, key=lambda t: (t[3], t[0]))
print(f"   {'given':>6} {'token':>6} {'part':>6} {'inter':>6}  pessoa")
for s_given, s_token, s_part, inter, pid, nome, surns in linhas[:6]:
    print(f"   {s_given:>6} {s_token:>6} {s_part:>6} {inter:>6}  {nome}  [{pid}]")

# ---------------------------------------------------------------------------
# 5. Que cartao a tela monta
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("5. O CARTAO (o que vai para o cabecalho e para o indice)")
print("=" * 78)
print(f"   match_name (nome do GEDCOM escolhido) -> {get_name(arvore[0][candidatos[0]]) if candidatos else '-'}")
print(f"   csv_name   (nome do CSV, secao 2)     -> {ALVO}")
