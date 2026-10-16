"""Qual portao fechou, de verdade, para cada descarte?

`matching.py` tem SEIS ramos de aceitacao visiveis... e mais um bloco depois deles que
pode DESFAZER a aceitacao: a penalidade de token do meio.

    if ACCEPT:
        csv_middle = csv_tokens - {given_norm} - csv_surn_all
        if csv_middle and csv_middle.isdisjoint(ged_tokens):
            ACCEPT = (best_score >= 96 and best_g >= 92 and ...)

Esse bloco nao aparece na mensagem. Um descarte pode exibir `given=100, final=88.25,
inter=1/1, jacc=1.00` — todos os numeros suficientes para o ramo 5 — e cair assim mesmo,
porque o nome do CSV tem tokens intermediarios que o candidato nao tem.

Este script replica `match_candidates` com instrumentacao, SO' para saber qual portao
fechou, e CONFERE contra a funcao real nos 456 grupos. Se houver uma divergencia
sequer, a replicacao esta' errada e os numeros nao valem.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\qual_portao_fechou.py <ged>
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from thefuzz import fuzz  # noqa: E402

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.matching import build_ged_indexes, match_candidates  # noqa: E402
from core.name_normalization import (  # noqa: E402
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
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

CSV = os.path.join(R, "src", "uploads", "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ = "Adriano Santos"


def replicar(arvore_indices, match_name, cm_value, ged_index, surname_index, features):
    """Copia fiel de `core.matching.match_candidates`, devolvendo tambem o portao."""
    key = norm_name(match_name)
    candidate_pids = ged_index.get(key, [])
    reason = None
    portao = None
    ramo_que_passou = None
    detalhe = {}

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
            primeiros = [t for t in norm_name(match_name).split() if t not in STOP_WORDS]
            if not surn_csv:
                if len(primeiros) > 1:
                    reason = "o sobrenome foi lido como prenome (nome sem sobrenome isolável)"
                else:
                    reason = "o nome não tem sobrenome (nome único)"
            elif not csv_surn_all:
                reason = "sobrenome curto demais para buscar (inicial ou abreviação)"
            else:
                reason = "nenhum sobrenome do nome existe no GEDCOM"
            portao = "pool vazio (nenhum sobrenome casou)"
            detalhe = {"given": given_norm, "surn_csv": surn_csv, "csv_surn_all": sorted(csv_surn_all)}
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
                        (inter_cnt_local == best_inter and s_given == best_g and score > best_score) or
                        (inter_cnt_local == best_inter and s_given == best_g and score == best_score
                         and best_pid is not None and pid < best_pid)):
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
                    portao = "filtro anti-falso-positivo (nenhum sobrenome em comum)"
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
                    ramos = [
                        (given_norm in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.67 and best_score >= 100, "1"),
                        (given_norm not in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.50 and best_g >= 85 and best_score >= 80, "2"),
                        (given_norm not in GENERIC_GIVENS and inter_cnt >= 1 and jacc >= 0.80 and best_score >= 86, "3"),
                        (best_g >= 90 and best_score >= 92 and inter_cnt >= required_intersection and jacc_ok, "4"),
                        (best_g >= 95 and best_score >= 88 and inter_cnt >= required_intersection and jacc_ok, "5"),
                    ]
                    for ok, nome_ramo in ramos:
                        if ok:
                            ACCEPT = True
                            ramo_que_passou = nome_ramo
                            break
                    if not ACCEPT:
                        pref_csv = token_prefixes(surn_csv, min_len=3)
                        cand_surns = feat_best["surnames_list"]
                        if any(sn.startswith(tuple(pref_csv)) for sn in cand_surns) and best_g >= 90 and best_score >= 86 and inter_cnt >= 1 and jacc_ok:
                            ACCEPT = True
                            ramo_que_passou = "6"

                    if ACCEPT:
                        csv_tokens = drop_short_tokens({t for t in norm_name(match_name).split() if t not in STOP_WORDS})
                        csv_middle = csv_tokens - {given_norm} - csv_surn_all
                        if csv_middle and csv_middle.isdisjoint(ged_tokens):
                            # O SETIMO PORTAO: ele nao esta' na mensagem.
                            desfez = not (best_score >= 96 and best_g >= 92
                                          and inter_cnt >= required_intersection and jacc_ok)
                            if desfez:
                                portao = (f"ramo {ramo_que_passou} passou, mas a penalidade de token do meio "
                                          f"desfez a aceitacao")
                                detalhe = {"tokens_do_meio": sorted(csv_middle),
                                           "tokens_do_candidato": sorted(ged_tokens),
                                           "exigiria": "score>=96, given>=92"}
                            ACCEPT = (best_score >= 96 and best_g >= 92
                                      and inter_cnt >= required_intersection and jacc_ok)

                    candidate_pids = [best_pid] if ACCEPT else []
                    if not candidate_pids:
                        reason = (f"score insuficiente ou conflito de sobrenome "
                                  f"(given={best_g}, final={best_score}, inter={inter_cnt}/{required_intersection}, jacc={jacc:.2f})")
                        if portao is None:
                            portao = "nenhum dos 6 ramos"
                        detalhe.update({"ramo_que_passou": ramo_que_passou, "best_pid": best_pid,
                                        "given": best_g, "score": best_score, "inter": inter_cnt,
                                        "jacc": jacc, "required": required_intersection,
                                        "csv_surn_all": sorted(csv_surn_all)})
            else:
                portao = "pool sem candidato avaliado"
    else:
        portao = "casamento exato de nome (aceito direto)"

    return candidate_pids, reason, portao, detalhe


def main():
    ged = sys.argv[1]
    arvore = carregar_arvore(ged)
    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar_profundidade)
    resultados, descartados, msg = dna_analysis(CSV, RAIZ, deps, arvore, observacoes_do_arquivo=[])
    ged_index, surname_index, features = build_ged_indexes(arvore)

    print(f"arvore: {os.path.basename(ged)} ({len(arvore[0])} pessoas)")
    print(f"{msg}")
    print()

    grupos = [(r["csv_name"], r["kit"], r["cm"]) for r in resultados]
    grupos += [(d["csv_name"], d["kit"], d["cm"]) for d in descartados]

    divergencias = []
    contagem = collections.Counter()
    por_cm = collections.defaultdict(list)

    for nome, kit, cm in grupos:
        reais, reason_real = match_candidates(arvore, nome, cm, ged_index, surname_index, features)
        meus, reason_meu, portao, det = replicar(arvore, nome, cm, ged_index, surname_index, features)
        if (reais != meus) or (bool(reais) != (reason_meu is None)) or (
                not reais and reason_real != reason_meu):
            divergencias.append((nome, kit, reais, meus, reason_real, reason_meu))
        contagem[portao] += 1
        por_cm[portao].append((cm or 0, nome))

    print(f"grupos conferidos: {len(grupos)}")
    print(f"DIVERGENCIAS entre a replicacao e a funcao real: {len(divergencias)}")
    for d in divergencias[:10]:
        print(f"   {d}")
    print()
    if divergencias:
        print("!! a replicacao nao e' fiel — os numeros abaixo nao valem")
        return
    print("replicacao fiel: aceita/recusa e texto do motivo batem em 100% dos grupos")
    print()

    print("qual portao fechou, por grupo (nome, kit):")
    for portao, n in contagem.most_common():
        cms = sorted(c for c, _ in por_cm[portao])
        print(f"  {n:>4}  {portao}")
        print(f"        cM max={cms[-1]}  mediana={cms[len(cms)//2]}")
    print()

    alvo = "penalidade de token do meio"
    vetados = [(cm, nome) for p, lst in por_cm.items() if alvo in str(p) for cm, nome in lst]
    if vetados:
        print(f"VETADOS PELO SETIMO PORTAO (todos os numeros visiveis passavam): {len(vetados)}")
        for cm, nome in sorted(vetados, reverse=True):
            print(f"  {cm:>7} cM  {nome!r}")


if __name__ == "__main__":
    main()
