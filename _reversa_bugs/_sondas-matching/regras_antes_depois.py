"""O que cada sugestao MUDA, medido. ANTES x DEPOIS, nos 62 cartoes reais.

## Como isto mede sem tocar no codigo de producao

O motor de producao continua intocado. Este script:
  1. roda a analise de DNA normal (o "ANTES");
  2. refaz a ESCOLHA DE CANDIDATO por variantes, para cada par (nome do CSV, cM);
  3. conta o que muda, com dois veredictos OBJETIVOS e independentes de opiniao:

     V1. JANELA DE VIDA — o nascimento do escolhido permite que ele tenha doado DNA?
         (idade > 115 anos em 2026 = impossivel)
     V2. COERENCIA DE GERACAO — quantos anos por geracao o caminho implica?
         (fora da faixa 13..50 = a data contradiz a distancia no grafo)

Nao afirma que a escolha nova esta CERTA: mede quantas escolhas atuais sao
impossiveis ou incoerentes, e quantas alternativas melhores existiam.

So LE os dados.
"""
from __future__ import annotations

import os
import sys
from collections import Counter

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import birth_date, parse_year  # noqa: E402
from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.name_normalization import (  # noqa: E402
    COMMON_SURNAMES, GENERIC_GIVENS, drop_short_tokens, norm_name, soft_prefix_jaccard,
    split_name_pt, surnames_set, token_prefixes,
)
from core.path_finding import find_ancestral_path  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from thefuzz import fuzz  # noqa: E402

GED = os.path.join(RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")
RAIZ_NOME = "Adriano Santos"

ANO_DE_HOJE = 2026
IDADE_MAXIMA = 115
ANOS_POR_GERACAO_MIN, ANOS_POR_GERACAO_MAX = 13, 50

arvore = carregar_arvore(GED)
people = arvore[0]
deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
resultados, descartados, mensagem = dna_analysis(CSV, RAIZ_NOME, deps, arvore)
raiz_id = next(pid for pid, p in people.items() if RAIZ_NOME.lower() in get_name(p).lower())
ano_raiz = parse_year(birth_date(people, raiz_id))

ged_index, surname_index, features = build_ged_indexes(arvore)

# ---------------------------------------------------------------------------
# Os dois veredictos objetivos
# ---------------------------------------------------------------------------


def janela_de_vida(pid: str) -> tuple[int | None, str]:
    """(idade em 2026, veredicto) para uma pessoa da arvore."""
    ano = parse_year(birth_date(people, pid))
    if not ano:
        return None, "sem data"
    idade = ANO_DE_HOJE - ano
    return idade, ("impossivel" if idade > IDADE_MAXIMA else "possivel")


def coerencia_de_geracao(pid: str) -> tuple[float | None, str]:
    """Anos por geracao implicados pelo caminho ate a raiz."""
    caminho, _comum = find_ancestral_path(arvore, raiz_id, pid)
    if not caminho or len(caminho) < 2:
        return None, "sem caminho"
    ano = parse_year(birth_date(people, pid))
    if not ano:
        return None, "sem data"
    por_geracao = (ano_raiz - ano) / (len(caminho) - 1)
    coerente = ANOS_POR_GERACAO_MIN <= por_geracao <= ANOS_POR_GERACAO_MAX
    return round(por_geracao, 1), ("coerente" if coerente else "incoerente")


# ---------------------------------------------------------------------------
# A copia da decisao de aceitacao, para poder variar SO o desempate
# ---------------------------------------------------------------------------
def avalia(pid: str, match_name: str, cm) -> dict:
    feat = features[pid]
    given_csv, surn_csv, csv_suffixes = split_name_pt(match_name)
    given_norm = norm_name(given_csv)
    csv_surn_all = drop_short_tokens(surnames_set(match_name))
    key_norm = norm_name(match_name)

    s_given = max((fuzz.ratio(given_norm, gg) for gg in feat["given_tokens"]), default=0)
    s_token = fuzz.token_sort_ratio(key_norm, feat["norm"])
    s_part = fuzz.partial_ratio(key_norm, feat["norm"])
    ged_surn_set = feat["surnames"]
    inter_set = csv_surn_all & ged_surn_set
    inter_cnt = len(inter_set)
    common_penalty = sum(1 for s in inter_set if s in COMMON_SURNAMES)
    score = round(0.55 * s_token + 0.25 * s_part + 0.20 * s_given + (8.0 * inter_cnt - 4.0 * common_penalty), 2)
    return {"pid": pid, "given": s_given, "score": score, "inter": inter_cnt,
            "jacc": soft_prefix_jaccard(csv_surn_all, ged_surn_set, min_pref=4)}


def aceita(av: dict, match_name: str, cm) -> bool:
    """Porta dos cinco ramos A/B/C/D + rebaixamento (identica a producao)."""
    given_csv, surn_csv, csv_suffixes = split_name_pt(match_name)
    given_norm = norm_name(given_csv)
    feat = features[av["pid"]]
    csv_surn_all = drop_short_tokens(surnames_set(match_name))
    ged_tokens = feat["tokens"]
    suffix_hit = bool(csv_suffixes & ged_tokens)
    inter_cnt, jacc, best_g, best_score = av["inter"], av["jacc"], av["given"], av["score"]

    if csv_surn_all and feat["surnames"] and inter_cnt == 0 and not suffix_hit:
        return False
    required = 1
    if given_norm in GENERIC_GIVENS and len(csv_surn_all) >= 2:
        required = 2
    jacc_ok = True
    if len(csv_surn_all) >= 2:
        limite = 0.33 if (float(cm or 0) >= 150 and given_norm not in GENERIC_GIVENS) else 0.5
        jacc_ok = jacc >= limite

    ACCEPT = False
    if given_norm in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.67 and best_score >= 100:
        ACCEPT = True
    elif given_norm not in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.50 and best_g >= 85 and best_score >= 80:
        ACCEPT = True
    elif given_norm not in GENERIC_GIVENS and inter_cnt >= 1 and jacc >= 0.80 and best_score >= 86:
        ACCEPT = True
    elif best_g >= 90 and best_score >= 92 and inter_cnt >= required and jacc_ok:
        ACCEPT = True
    elif best_g >= 95 and best_score >= 88 and inter_cnt >= required and jacc_ok:
        ACCEPT = True
    else:
        pref_csv = token_prefixes(surn_csv, min_len=3)
        if pref_csv:
            if any(sn.startswith(tuple(pref_csv)) for sn in feat["surnames_list"]) \
                    and best_g >= 90 and best_score >= 86 and inter_cnt >= 1 and jacc_ok:
                ACCEPT = True
    if ACCEPT:
        csv_tokens = drop_short_tokens({t for t in norm_name(match_name).split()})
        csv_middle = csv_tokens - {given_norm} - csv_surn_all
        if csv_middle and csv_middle.isdisjoint(ged_tokens):
            ACCEPT = best_score >= 96 and best_g >= 92 and inter_cnt >= required and jacc_ok
    return ACCEPT


# ---------------------------------------------------------------------------
# ANTES
# ---------------------------------------------------------------------------
print("=" * 100)
print("ANTES — o que a producao escolhe hoje")
print("=" * 100)
print(f"   {mensagem}")

linhas = []
for r in resultados:
    doc = r["documentary"]
    pid = (doc.get("person_b") or {}).get("id")
    if not pid:
        continue
    idade, veredito_idade = janela_de_vida(pid)
    por_ger, veredito_ger = coerencia_de_geracao(pid)
    linhas.append({
        "csv": r["csv_name"], "cm": r["cm"], "pid": pid,
        "nome": get_name(people[pid]), "nasc": birth_date(people, pid),
        "idade": idade, "v_idade": veredito_idade,
        "por_ger": por_ger, "v_ger": veredito_ger,
        "identidade": r["identidade"],
    })

print()
print(f"   cartoes avaliados                        : {len(linhas)}")
print(f"   janela de vida IMPOSSIVEL (> {IDADE_MAXIMA} anos)   : "
      f"{sum(1 for x in linhas if x['v_idade'] == 'impossivel')}")
print(f"   janela de vida OK                       : "
      f"{sum(1 for x in linhas if x['v_idade'] == 'possivel')}")
print(f"   sem data de nascimento                  : "
      f"{sum(1 for x in linhas if x['v_idade'] == 'sem data')}")
print(f"   geracao INCOERENTE (fora de {ANOS_POR_GERACAO_MIN}-{ANOS_POR_GERACAO_MAX} anos) : "
      f"{sum(1 for x in linhas if x['v_ger'] == 'incoerente')}")
print(f"   identidade a confirmar                  : "
      f"{sum(1 for x in linhas if x['identidade'] == 'a_confirmar')}")

print()
print("   --- as escolhas com janela de vida IMPOSSIVEL ---")
for x in sorted((v for v in linhas if v["v_idade"] == "impossivel"), key=lambda v: -(v["idade"] or 0)):
    print(f"      {x['csv'][:38]:<38} {str(x['cm'])[:6]:>7} cM  -> {x['nome'][:30]:<30} "
          f"nasc {str(x['nasc'])[:12]:<12} ({x['idade']} anos)")

# ---------------------------------------------------------------------------
# DEPOIS — variantes
# ---------------------------------------------------------------------------
print()
print("=" * 100)
print("DEPOIS — o que cada variante faria")
print("=" * 100)


def melhor_por_precedencia(match_name, cm, ranking):
    cands, _ = match_candidates(arvore, match_name, cm, ged_index, surname_index, features)
    if not cands:
        return None, []
    avs = [avalia(p, match_name, cm) for p in cands]
    ordenados = sorted(avs, key=ranking)
    return ordenados[0]["pid"], ordenados


# Variante 1: prenome (given) antes da contagem de sobrenomes
def r_given(av):
    return (-av["given"], -av["inter"], -av["score"], av["pid"])


# Variante 2: janela de vida — descarta candidato impossivel, mantendo a ordem da producao
def r_janela(av):
    impossivel = janela_de_vida(av["pid"])[1] == "impossivel"
    return (impossivel, -av["inter"], -av["given"], -av["score"], av["pid"])


resumo = {}
for rotulo, ranking in (("1. Prenome primeiro", r_given),
                        ("2. Janela de vida primeiro", r_janela)):
    mudam, ficam_sem, melhoram = [], [], []
    for x in linhas:
        novo, avs = melhor_por_precedencia(x["csv"], x["cm"], ranking)
        if novo is None or novo == x["pid"]:
            continue
        if not aceita(next(a for a in avs if a["pid"] == novo), x["csv"], x["cm"]):
            ficam_sem.append((x, novo))
            continue
        idade_nova, v_nova = janela_de_vida(novo)
        por_ger_nova, g_nova = coerencia_de_geracao(novo)
        registro = (x, novo, idade_nova, v_nova, por_ger_nova, g_nova)
        if v_nova == "possivel" and x["v_idade"] == "impossivel":
            melhoram.append(registro)
        mudam.append(registro)
    resumo[rotulo] = (mudam, ficam_sem, melhoram)

    print(f"--- {rotulo} ---")
    print(f"   cartoes que trocam de pessoa : {len(mudam) + len(ficam_sem)}")
    print(f"   ... e a escolha nova e ACEITA: {len(mudam)}")
    print(f"   ... e a nova seria REJEITADA (cartao vira 'descartado'): {len(ficam_sem)}")
    print(f"   ... corrigem janela impossivel: {len(melhoram)}")
    for x, novo, idade_nova, v_nova, por_ger_nova, g_nova in mudam[:10]:
        marca = "  <-- CORRIGE" if v_nova == "possivel" and x["v_idade"] == "impossivel" else ""
        print(f"      {x['csv'][:34]:<34}")
        print(f"         antes: {x['nome'][:32]:<32} nasc {str(x['nasc'])[:11]:<11} {x['v_idade']}{marca}")
        print(f"         depois: {get_name(people[novo])[:32]:<32} nasc "
              f"{str(birth_date(people, novo))[:11]:<11} {v_nova}")
    for x, novo in ficam_sem[:6]:
        print(f"      REJEITADA: {x['csv'][:30]:<30} -> {get_name(people[novo])[:30]}")
    print()

# Comparacao com o MRCA do CSV
print("=" * 100)
print("BONUS — a coluna MRCA do CSV contra o que a arvore diz")
print("=" * 100)
df = read_csv_with_fallback(CSV)
mrca_por_nome = {}
for _, linha_csv in df.iterrows():
    nome = str(linha_csv["Name"]).strip()
    try:
        mrca_por_nome.setdefault(norm_name(nome), float(linha_csv["MRCA"]))
    except (TypeError, ValueError):
        pass

divergentes = []
for x in linhas:
    mrca_csv = mrca_por_nome.get(norm_name(x["csv"]))
    caminho, _c = find_ancestral_path(arvore, raiz_id, x["pid"])
    if not caminho or mrca_csv is None:
        continue
    meioses = len(caminho) - 1
    # o MRCA do CSV esta em geracoes ate o ancestral comum; meioses sao os dois lados
    geracoes_arvore = meioses / 2
    razao = round(geracoes_arvore / mrca_csv, 2) if mrca_csv else None
    if razao and (razao < 0.5 or razao > 2.0):
        divergentes.append((x, mrca_csv, meioses, geracoes_arvore, razao))

print(f"   cartoes com caminho e MRCA no CSV: "
      f"{sum(1 for x in linhas if mrca_por_nome.get(norm_name(x['csv'])))}")
print(f"   com divergencia de 2x ou mais entre CSV e arvore: {len(divergentes)}")
for x, mrca_csv, meioses, ger, razao in divergentes:
    print(f"      {x['csv'][:34]:<34} MRCA(CSV)={mrca_csv:<6} "
          f"arvore={meioses} meioses (~{ger:.1f} geracoes)  razao={razao}")
