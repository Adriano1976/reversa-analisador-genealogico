"""Indices do GEDCOM e decisao de aceitacao de candidatos.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52. Responsabilidade unica:
construir os indices sobre a arvore carregada e decidir, para cada match do CSV,
quais pessoas do GEDCOM sao candidatas aceitas e por que.

Nao depende de pandas: quem le o CSV e `csv_ingest`.
"""
from __future__ import annotations

from thefuzz import fuzz

from .name_normalization import (
    COMMON_SURNAMES,
    GENERIC_GIVENS,
    STOP_WORDS,
    drop_short_tokens,
    norm_name,
    soft_prefix_jaccard,
    split_name_pt,
    surnames_set,
    token_prefixes,
)
from .upload import get_name, people


def build_ged_indexes():
    """Constroi os indices de busca e o cache de atributos normalizados.

    O cache existe porque ``norm_name`` custa cerca de 41 us e ``surnames_set``
    cerca de 72 us: o laco de candidatos de ``match_candidates`` renormalizava o
    mesmo nome aproximadamente 7 vezes por candidato, a cada match do CSV, para
    um valor que nao depende do CSV. Calcular aqui, uma vez por analise, nao
    altera nenhuma decisao: os valores sao os mesmos.
    """
    ged_index = {}
    surname_index = {}
    features = {}
    for pid, person in people.items():
        nm = get_name(person)
        key = norm_name(nm)
        key_tokens = key.split()
        ged_index.setdefault(key, []).append(pid)
        _given, surnames, _suffixes = split_name_pt(nm)
        for sn in surnames:
            if sn:
                surname_index.setdefault(sn, []).append(pid)
        # `key` ja e norm_name(nm), e norm_name e idempotente sobre os proprios
        # tokens, entao nao ha nada a renormalizar aqui. Reproduz o fallback de
        # top_given_tokens para o caso de todos os tokens serem stop words.
        non_stop = [t for t in key_tokens if t not in STOP_WORDS]
        features[pid] = {
            "norm": key,
            "given_tokens": non_stop[:2] or key_tokens[:2],
            "surnames": set(surnames),
            "surnames_list": surnames,
            "tokens": set(key_tokens),
        }
    return ged_index, surname_index, features


def match_candidates(match_name, cm_value, ged_index, surname_index, features):
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
                feat = features[pid]
                s_given = max((fuzz.ratio(given_norm, gg) for gg in feat["given_tokens"]), default=0)
                s_token = fuzz.token_sort_ratio(key_norm, feat["norm"])
                s_part = fuzz.partial_ratio(key_norm, feat["norm"])
                ged_surn_set = feat["surnames"]
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
                feat_best = features[best_pid]
                ged_surn_best = feat_best["surnames"]
                inter_best = csv_surn_all & ged_surn_best
                inter_cnt = len(inter_best)

                ged_tokens = feat_best["tokens"]
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
                            cand_surns = feat_best["surnames_list"]
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
