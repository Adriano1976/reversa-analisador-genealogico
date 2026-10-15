"""Decompoe o motivo "score insuficiente ou conflito de sobrenome".

A mensagem imprime quatro numeros: given, final, inter e jacc. Esta sonda reproduz o
laco de scoring de `core.matching.match_candidates` com instrumentacao e mostra, para
um match do CSV, CADA ramo de aceitacao — o valor obtido, o exigido e a distancia.

O valor de `reason` calculado aqui e' conferido contra o que a propria
`match_candidates` devolve: se divergirem, a instrumentacao esta' errada e o resto do
relatorio nao vale.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\motivo_score_insuficiente.py <ged> [nome_do_csv] [cm]
"""

import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from thefuzz import fuzz  # noqa: E402

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
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

NOME = "Clezia Santos"
CM = 154.5


def main():
    ged = sys.argv[1]
    nome = sys.argv[2] if len(sys.argv) > 2 else NOME
    cm = float(sys.argv[3]) if len(sys.argv) > 3 else CM

    arvore = carregar_arvore(ged)
    ged_index, surname_index, features = build_ged_indexes(arvore)

    aceitos, reason = match_candidates(arvore, nome, cm, ged_index, surname_index, features)

    given_csv, surn_csv, csv_suffixes = split_name_pt(nome)
    given_norm = norm_name(given_csv)
    csv_surn_all = drop_short_tokens(surnames_set(nome))
    key_norm = norm_name(nome)

    print(f"arvore : {os.path.basename(ged)}  ({len(arvore[0])} pessoas)")
    print(f"match  : {nome!r}  cm={cm}")
    print(f"  given_csv={given_csv!r}  given_norm={given_norm!r}  generico={given_norm in GENERIC_GIVENS}")
    print(f"  surn_csv={surn_csv}  csv_surn_all={sorted(csv_surn_all)}")
    print(f"  candidatos exatos (ged_index): {len(ged_index.get(key_norm, []))}")
    print(f"  aceitos pela match_candidates : {aceitos}")
    print(f"  reason da match_candidates    : {reason}")
    print()

    pool = set()
    for sn in surn_csv:
        pool.update(surname_index.get(sn, []))
    if not pool and surn_csv:
        pref = token_prefixes(surn_csv, min_len=3)
        for sn, pids in surname_index.items():
            if any(sn.startswith(p) for p in pref):
                pool.update(pids)
    print(f"pool por sobrenome: {len(pool)} pessoas")
    if not pool:
        return

    linhas = []
    for pid in pool:
        feat = features[pid]
        s_given = max((fuzz.ratio(given_norm, gg) for gg in feat["given_tokens"]), default=0)
        s_token = fuzz.token_sort_ratio(key_norm, feat["norm"])
        s_part = fuzz.partial_ratio(key_norm, feat["norm"])
        inter_set = csv_surn_all & feat["surnames"]
        inter_cnt_local = len(inter_set)
        common_penalty = sum(1 for s in inter_set if s in COMMON_SURNAMES)
        inter_bonus = 8.0 * inter_cnt_local - 4.0 * common_penalty
        score = round(0.55 * s_token + 0.25 * s_part + 0.20 * s_given + inter_bonus, 2)
        linhas.append((inter_cnt_local, s_given, score, pid, feat, s_token, s_part,
                       inter_set, common_penalty, inter_bonus))

    # Ordena pelos mesmos criterios do desempate (inter, given, score, xref) — invertido,
    # porque aqui interessa o melhor primeiro.
    linhas.sort(key=lambda L: (L[0], L[1], L[2]), reverse=True)

    print("top 5 do pool, pelos criterios de desempate:")
    for (ic, sg, sc, pid, feat, st, sp, iset, pen, bonus) in linhas[:5]:
        print(f"  {pid}  {get_name(arvore[0][pid])!r}")
        print(f"      s_token={st}  s_part={sp}  s_given={sg}  "
              f"inter={sorted(iset)}  common_penalty={pen}  inter_bonus={bonus}")
        print(f"      score = 0.55*{st} + 0.25*{sp} + 0.20*{sg} + {bonus} = {sc}")

    ic, sg, sc, pid, feat, st, sp, iset, pen, bonus = linhas[0]
    print()
    print(f"MELHOR: {pid}  {get_name(arvore[0][pid])!r}")

    ged_surn_best = feat["surnames"]
    inter_best = csv_surn_all & ged_surn_best
    inter_cnt = len(inter_best)
    ged_tokens = feat["tokens"]
    suffix_hit = bool(csv_suffixes & ged_tokens)
    filtro = bool(csv_surn_all and ged_surn_best and inter_cnt == 0 and not suffix_hit)
    print(f"  filtro anti-falso-positivo (sem sobrenome em comum)? {filtro}")

    required_intersection = 1
    if given_norm in GENERIC_GIVENS and len(csv_surn_all) >= 2:
        required_intersection = 2
    jacc = soft_prefix_jaccard(csv_surn_all, ged_surn_best, min_pref=4)
    jacc_ok = True
    limiar_jacc = None
    if len(csv_surn_all) >= 2:
        limiar_jacc = 0.5
        if float(cm or 0) >= 150 and given_norm not in GENERIC_GIVENS:
            limiar_jacc = 0.33
        jacc_ok = jacc >= limiar_jacc

    print(f"  required_intersection={required_intersection}  inter_cnt={inter_cnt}")
    print(f"  jacc={jacc:.2f}  jacc_ok={jacc_ok}"
          + (f"  (limiar {limiar_jacc})" if limiar_jacc is not None
             else "  (nao ha limiar: o CSV tem menos de 2 sobrenomes, entao jacc_ok e' sempre True)"))
    print()
    print("ramos de aceitacao — valor obtido / exigido:")

    def ramo(rotulo, ok, exigido, obtido):
        marca = "PASSA" if ok else "FALHA"
        print(f"  [{marca}] {rotulo}")
        print(f"          exigido: {exigido}")
        print(f"          obtido : {obtido}")

    r1 = given_norm in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.67 and sc >= 100
    ramo("1 dado generico + 2 sobrenomes", r1,
         "generico=True, inter>=2, jacc>=0.67, score>=100",
         f"generico={given_norm in GENERIC_GIVENS}, inter={inter_cnt}, jacc={jacc:.2f}, score={sc}")

    r2 = given_norm not in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.50 and sg >= 85 and sc >= 80
    ramo("2 nome proprio + 2 sobrenomes", r2,
         "generico=False, inter>=2, jacc>=0.50, given>=85, score>=80",
         f"generico={given_norm in GENERIC_GIVENS}, inter={inter_cnt}, jacc={jacc:.2f}, given={sg}, score={sc}")

    r3 = given_norm not in GENERIC_GIVENS and inter_cnt >= 1 and jacc >= 0.80 and sc >= 86
    ramo("3 nome proprio + 1 sobrenome forte  <-- este e' o caso", r3,
         "generico=False, inter>=1, jacc>=0.80, score>=86",
         f"generico={given_norm in GENERIC_GIVENS}, inter={inter_cnt}, jacc={jacc:.2f}, score={sc}"
         f"   (faltam {round(86 - sc, 2)} de score)")

    r4 = sg >= 90 and sc >= 92 and inter_cnt >= required_intersection and jacc_ok
    ramo("4 given muito alto", r4,
         "given>=90, score>=92, inter>=req, jacc_ok",
         f"given={sg}, score={sc}, inter={inter_cnt}/{required_intersection}, jacc_ok={jacc_ok}")

    r5 = sg >= 95 and sc >= 88 and inter_cnt >= required_intersection and jacc_ok
    ramo("5 given altissimo", r5,
         "given>=95, score>=88, inter>=req, jacc_ok",
         f"given={sg}, score={sc}, inter={inter_cnt}/{required_intersection}, jacc_ok={jacc_ok}")

    pref_csv = token_prefixes(surn_csv, min_len=3)
    cand_surns = feat["surnames_list"]
    prefixo_ok = bool(pref_csv) and any(sn.startswith(tuple(pref_csv)) for sn in cand_surns)
    r6 = prefixo_ok and sg >= 90 and sc >= 86 and inter_cnt >= 1 and jacc_ok
    ramo("6 prefixo de sobrenome", r6,
         "prefixo casa, given>=90, score>=86, inter>=1, jacc_ok",
         f"prefixo={prefixo_ok} ({sorted(pref_csv)} vs {cand_surns}), given={sg}, score={sc}, "
         f"inter={inter_cnt}, jacc_ok={jacc_ok}")

    fixo = 0.55 * st + 0.25 * sp + bonus
    if sg < 100:
        dado_necessario = (86 - fixo) / 0.20
        print()
        print(f"para o ramo 3 passar so' melhorando o prenome: score = {round(fixo, 2)} + 0.20*given")
        print(f"  seria preciso given >= {dado_necessario:.1f} (o observado e' {sg})")

    recomposto = (f"score insuficiente ou conflito de sobrenome "
                  f"(given={sg}, final={sc}, inter={inter_cnt}/{required_intersection}, "
                  f"jacc={jacc:.2f})")
    print()
    print(f"reason recomposta : {recomposto}")
    print(f"reason real       : {reason}")
    print(f"CONFERE           : {recomposto == reason}")


if __name__ == "__main__":
    main()
