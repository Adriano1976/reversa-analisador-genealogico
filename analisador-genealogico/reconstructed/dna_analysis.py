"""Tarefa 04 — Análise de DNA.

Cruza a árvore GEDCOM com um CSV de matches (ex.: GEDmatch). Agrega
segmentos duplicados por match (somando cM), faz matching difuso de nomes
com filtro anti-falso-positivo, calcula o caminho ancestral até a pessoa-raiz
e prevê o parentesco por faixa de cM. Renderiza resultados ordenados por cM
decrescente e lista os descartados para auditoria.

Comportamento idêntico ao legado, incluindo as decisões documentadas:
- Limiares de score/given como literais nas regras A/B/C/D (92, 90, 86, ...).
- `HARD_MIN`/`GIVEN_MIN` declarados porém não usados (código morto).
- Relaxamento de Jaccard (0.5 -> 0.33) para cM>=150 e dado não-genérico.
- Regex de ID `[A-Z]{2}\\d{7}`.
"""
from __future__ import annotations

import re
import string
import unicodedata

import pandas as pd
from thefuzz import fuzz

from .path_search import find_ancestral_path, generate_mermaid_graph
from .upload import get_name, people

# ---------------------------------------------------------------------------
# Faixas de cM e vocabulário (idênticos ao legado)
# ---------------------------------------------------------------------------

SHARED_CM_DATA = [
    {"range": (3300, 3720), "relationship": "Pai/Mãe ↔ Filho(a)"},
    {"range": (2200, 3400), "relationship": "Irmãos completos"},
    {"range": (1317, 2312), "relationship": "Avós/Netos, Tios/Tias ↔ Sobrinhos(as), Meios-irmãos"},
    {"range": (553, 1330), "relationship": "Primos de 1º grau"},
    {"range": (200, 850), "relationship": "Primos de 1º grau (1× removido), Meios-primos, Tios-avós ↔ Sobrinhos-netos"},
    {"range": (46, 515), "relationship": "Primos de 2º grau"},
    {"range": (30, 350), "relationship": "Primos de 2º grau (1× removido), Primos de 3º grau"},
    {"range": (10, 220), "relationship": "Primos de 3º grau (1× removido), Primos de 4º grau"},
    {"range": (0, 110), "relationship": "Primos de 4º/5º grau ou mais distantes"},
]

STOP_WORDS = {"de", "da", "do", "das", "dos", "e"}
GENERIC_GIVENS = {
    "maria", "jose", "josé", "joao", "joão", "ana", "luiz", "luís", "francisco",
    "antonio", "antônio", "fernando", "carlos", "paulo", "pedro", "marcos",
    "augusto", "sergio", "sérgio", "helena",
}
SURNAME_SUFFIXES = {"filho", "neto", "junior", "júnior", "sobrinho"}
COMMON_SURNAMES = {
    "silva", "oliveira", "santos", "souza", "souza", "pereira", "ferreira", "almeida",
    "costa", "rodrigues", "lima", "gomes", "ribeiro", "carvalho", "azevedo", "albuquerque",
}
SURNAME_EQUIV = {
    "netto": "neto",
    "gouvea": "gouveia",
    "gouvêa": "gouveia",
    "gouvéia": "gouveia",
}
SHORT_KEEP = {"sa", "sá"}


def get_relationships_by_cm(cm_value):
    if not isinstance(cm_value, (int, float)) or cm_value <= 0:
        return []
    poss = [item["relationship"] for item in SHARED_CM_DATA if item["range"][0] <= cm_value <= item["range"][1]]
    return poss if poss else ["Relação distante ou indeterminada"]


# ---------------------------------------------------------------------------
# Normalização e decomposição de nomes (idênticas ao legado)
# ---------------------------------------------------------------------------

def strip_bad_utf(s):
    if s is None:
        return ""
    s = str(s)
    fixes = {
        "A�": "ç", "Ã§": "ç",
        "Ã£": "ã", "Ã¡": "á", "Ã¢": "â",
        "Ã©": "é", "Ãª": "ê", "Ã¨": "è",
        "Ã­": "í", "Ã³": "ó", "Ã´": "ô", "Ãº": "ú",
        "Ã": "Ã",
        "GouvA�": "Gouvê",
        "A�": "ç",
        "JoA�o": "João", "SA�": "Sá", "GonA�": "Gonç",
    }
    for bad, good in fixes.items():
        s = s.replace(bad, good)
    return re.sub(r"[^\w\sÁ-ú'-]", " ", s)


def norm_name(s):
    s = strip_bad_utf(str(s))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("/", " ")
    s = "".join(ch if ch not in set(string.punctuation) else " " for ch in s)
    s = " ".join(s.lower().split())
    return s


def drop_short_tokens(S, n=3):
    return {t for t in S if len(t) >= n or t in SHORT_KEEP}


def surname_core_tokens(name, keep_last=3):
    n = norm_name(name)
    toks = [t for t in n.split() if t and t not in STOP_WORDS]
    suffixes = []
    while toks and toks[-1] in SURNAME_SUFFIXES:
        suffixes.append(toks.pop())
    base = [t for t in toks[-keep_last:] if t not in GENERIC_GIVENS]
    base = [SURNAME_EQUIV.get(t, t) for t in base]
    return base, suffixes


def split_name_pt(s):
    n = norm_name(s)
    toks = [t for t in n.split() if t]
    given = next((t for t in toks if t not in STOP_WORDS and t not in GENERIC_GIVENS), toks[0] if toks else "")
    base, suffixes = surname_core_tokens(s, keep_last=3)
    surnames = [t for t in base if t != given and t not in GENERIC_GIVENS]
    return given, surnames, set(suffixes)


def surnames_set(name):
    _, surnames, _ = split_name_pt(name)
    return set(surnames)


def top_given_tokens(name, k=2):
    n = norm_name(name)
    toks = [t for t in n.split() if t not in STOP_WORDS]
    return toks[:k] or n.split()[:k]


def token_prefixes(tokens, min_len=3):
    out = set()
    for t in tokens:
        t = norm_name(t)
        if len(t) >= min_len:
            out.add(t[:min_len])
    return out


def demojibake(s):
    if not s:
        return s
    if any(p in s for p in ("Ã", "Â", "A�", "�")):
        try:
            fixed = s.encode("latin1").decode("utf-8")
            if "�" not in fixed and "Ã" not in fixed and "A�" not in fixed:
                return fixed
        except Exception:
            pass
    return s


def soft_prefix_jaccard(a, b, min_pref=4, min_len=2) -> float:
    a = {t for t in a if len(t) >= min_len}
    b = {t for t in b if len(t) >= min_len}
    if not a and not b:
        return 0.0
    a_short = any(len(t) <= min_pref or t.endswith(".") for t in a)
    b_short = any(len(t) <= min_pref or t.endswith(".") for t in b)
    if a_short or b_short:
        def prefset(S):
            return {t if len(t) <= min_pref else t[:min_pref] for t in S}
        ap, bp = prefset(a), prefset(b)
        inter = len(ap & bp)
        union = len(ap | bp) or 1
        return inter / union
    inter = len(a & b)
    union = len(a | b) or 1
    return inter / union


# ---------------------------------------------------------------------------
# Leitura e agregação do CSV
# ---------------------------------------------------------------------------

def read_csv_with_fallback(path):
    try:
        df = pd.read_csv(path, encoding="utf-8", skipinitialspace=True)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1", skipinitialspace=True)
    df.columns = [col.strip() for col in df.columns]
    return df


def detect_columns(df):
    name_col = next((col for col in ["Name", "MatchedName", "Nome"] if col in df.columns), None)
    cm_col = next((col for col in ["cM", "TotalCM", "Total cM"] if col in df.columns), None)
    id_cols_guess = [
        c for c in df.columns
        if df[c].astype(str).str.fullmatch(r"[A-Z]{2}\d{7}").mean() > 0.3
    ]
    match_id_col = id_cols_guess[0] if id_cols_guess else None
    email_cols = [c for c in df.columns if "mail" in c.lower()]
    match_email_col = email_cols[-1] if email_cols else None
    return name_col, cm_col, match_id_col, match_email_col


def aggregate_matches(df, name_col, cm_col, match_id_col, match_email_col):
    def build_group_key(row):
        parts = [norm_name(demojibake(str(row[name_col])))]
        if match_id_col:
            parts.append(str(row[match_id_col]).strip().upper())
        elif match_email_col:
            parts.append(norm_name(str(row[match_email_col])))
        return " | ".join(parts)

    df["_group_key"] = df.apply(build_group_key, axis=1)
    aggregated = (
        df.groupby("_group_key", as_index=False)
        .agg({cm_col: "sum"})
        .merge(
            df[["_group_key", name_col]].drop_duplicates("_group_key"),
            on="_group_key", how="left",
        )
    )
    return aggregated


# ---------------------------------------------------------------------------
# Índices + matching difuso
# ---------------------------------------------------------------------------

def build_ged_indexes():
    ged_index = {}
    surname_index = {}
    given_index = {}
    for pid, person in people.items():
        nm = get_name(person)
        key = norm_name(nm)
        ged_index.setdefault(key, []).append(pid)
        given, surnames, _ = split_name_pt(nm)
        given_index.setdefault(given, []).append(pid)
        for sn in surnames:
            if sn:
                surname_index.setdefault(sn, []).append(pid)
    return ged_index, surname_index, given_index


def match_candidates(match_name, cm_value, ged_index, surname_index):
    """Retorna `(candidate_pids, reason)` seguindo o bloco de scoring do legado."""
    key = norm_name(match_name)
    candidate_pids = ged_index.get(key, [])
    reason = None

    if not candidate_pids:
        given_csv, surn_csv, csv_suffixes = split_name_pt(match_name)
        given_norm = norm_name(given_csv)
        csv_surn_all = drop_short_tokens(surnames_set(match_name))

        pool = set()
        for sn in surn_csv:
            pool.update(surname_index.get(sn, []))

        if not pool and surn_csv:
            pref = token_prefixes(surn_csv, min_len=3)
            for sn, pids in surname_index.items():
                if any(sn.startswith(p) for p in pref):
                    pool.update(pids)

        if not pool:
            reason = "sem candidatos por sobrenome (abreviação/corrupção?)"
        else:
            best_pid = None
            best_score = best_g = -1
            best_inter = -1
            key_norm = norm_name(match_name)

            for pid in pool:
                nm = get_name(people[pid])
                ged_given_candidates = [norm_name(t) for t in top_given_tokens(nm, k=2)]
                s_given = max((fuzz.ratio(given_norm, gg) for gg in ged_given_candidates), default=0)
                s_token = fuzz.token_sort_ratio(key_norm, norm_name(nm))
                s_part = fuzz.partial_ratio(key_norm, norm_name(nm))
                ged_surn_set = surnames_set(nm)
                inter_set = csv_surn_all & ged_surn_set
                inter_cnt_local = len(inter_set)
                common_penalty = sum(1 for s in inter_set if s in COMMON_SURNAMES)
                inter_bonus = 8.0 * inter_cnt_local - 4.0 * common_penalty
                score = round(0.55 * s_token + 0.25 * s_part + 0.20 * s_given + inter_bonus, 2)

                if (inter_cnt_local > best_inter or
                        (inter_cnt_local == best_inter and s_given > best_g) or
                        (inter_cnt_local == best_inter and s_given == best_g and score > best_score)):
                    best_pid, best_score, best_g, best_inter = pid, score, s_given, inter_cnt_local

            if best_pid is not None:
                nm_best = get_name(people[best_pid])
                ged_surn_best = surnames_set(nm_best)
                inter_best = csv_surn_all & ged_surn_best
                inter_cnt = len(inter_best)

                ged_tokens = set(norm_name(nm_best).split())
                suffix_hit = bool(csv_suffixes & ged_tokens)
                if csv_surn_all and ged_surn_best and inter_cnt == 0 and not suffix_hit:
                    candidate_pids = []
                    reason = "sem sobrenome em comum (filtro anti-falso-positivo)"
                else:
                    required_intersection = 1
                    if given_norm in GENERIC_GIVENS and len(csv_surn_all) >= 2:
                        required_intersection = 2

                    jacc = soft_prefix_jaccard(csv_surn_all, ged_surn_best, min_pref=4)
                    jacc_ok = True
                    if len(csv_surn_all) >= 2:
                        threshold = 0.5
                        if float(cm_value or 0) >= 150 and given_norm not in GENERIC_GIVENS:
                            threshold = 0.33
                        jacc_ok = jacc >= threshold

                    ACCEPT = False

                    if (given_norm in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.67 and best_score >= 100):
                        ACCEPT = True
                    elif (given_norm not in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.50 and best_g >= 85 and best_score >= 80):
                        ACCEPT = True
                    elif (given_norm not in GENERIC_GIVENS and inter_cnt >= 1 and jacc >= 0.80 and best_score >= 86):
                        ACCEPT = True
                    elif (best_g >= 90 and best_score >= 92 and inter_cnt >= required_intersection and jacc_ok):
                        ACCEPT = True
                    elif (best_g >= 95 and best_score >= 88 and inter_cnt >= required_intersection and jacc_ok):
                        ACCEPT = True
                    else:
                        pref_csv = token_prefixes(surn_csv, min_len=3)
                        if pref_csv:
                            cand_given, cand_surns, _ = split_name_pt(nm_best)
                            if any(sn.startswith(tuple(pref_csv)) for sn in cand_surns) and best_g >= 90 and best_score >= 86 and inter_cnt >= 1 and jacc_ok:
                                ACCEPT = True

                    if ACCEPT:
                        csv_tokens = drop_short_tokens({t for t in norm_name(match_name).split() if t not in STOP_WORDS})
                        csv_middle = csv_tokens - {given_norm} - csv_surn_all
                        if csv_middle and csv_middle.isdisjoint(ged_tokens):
                            ACCEPT = (best_score >= 96 and best_g >= 92 and inter_cnt >= required_intersection and jacc_ok)

                    candidate_pids = [best_pid] if ACCEPT else []
                    if not candidate_pids:
                        reason = (f"score insuficiente ou conflito de sobrenome "
                                  f"(given={best_g}, final={best_score}, inter={inter_cnt}/{required_intersection}, jacc={jacc:.2f})")

    return candidate_pids, reason


# ---------------------------------------------------------------------------
# Fluxo principal (equivalente ao bloco dna_analysis do legado)
# ---------------------------------------------------------------------------

def dna_analysis(csv_path: str, root_name: str):
    """Executa o fluxo completo de análise de DNA.

    Retorna `(results_sorted, skipped, message)` ou lança exceção.
    `root_name` deve existir no GEDCOM.
    """
    root_person_ids = [pid for pid, p in people.items() if root_name.lower() in get_name(p).lower()]
    if not root_person_ids:
        raise ValueError(f"Seu nome '{root_name}' não foi encontrado no GEDCOM.")
    root_id = root_person_ids[0]

    df = read_csv_with_fallback(csv_path)
    name_col, cm_col, match_id_col, match_email_col = detect_columns(df)
    if not name_col or not cm_col:
        raise ValueError("Colunas de Nome e cM não encontradas no CSV.")
    aggregated = aggregate_matches(df, name_col, cm_col, match_id_col, match_email_col)

    ged_index, surname_index, _ = build_ged_indexes()

    results_list = []
    skipped_matches = []

    for _, row in aggregated.iterrows():
        csv_name_raw = str(row[name_col]).strip()
        match_name = demojibake(csv_name_raw)
        cm_value = row[cm_col]

        candidate_pids, reason = match_candidates(match_name, cm_value, ged_index, surname_index)

        if not candidate_pids:
            skipped_matches.append({"csv_name": csv_name_raw, "motivo": reason or "não encontrado"})
            continue

        added = False
        for pid in candidate_pids:
            path, common_ancestor = find_ancestral_path(root_id, pid)
            if path:
                nomes = [get_name(people[p_id]) for p_id in path]
                probable_relationships = get_relationships_by_cm(cm_value)
                mermaid_data = generate_mermaid_graph(path, root_id, pid, common_ancestor)
                results_list.append({
                    "match_name": get_name(people[pid]),
                    "cm": cm_value,
                    "text_path": " → ".join(nomes),
                    "mermaid_data": mermaid_data,
                    "relationships": ", ".join(probable_relationships),
                    "csv_name": csv_name_raw,
                })
                added = True
                break
        if not added:
            skipped_matches.append({"csv_name": csv_name_raw, "motivo": "sem caminho subindo por pais (pais ausentes no GED?)"})

    results_sorted = sorted(results_list, key=lambda x: x.get("cm", 0), reverse=True)
    message = f"{len(results_sorted)} conexões encontradas. {len(skipped_matches)} descartadas."
    return results_sorted, skipped_matches, message