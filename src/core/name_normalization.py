"""Normalizacao e decomposicao de nomes, e o vocabulario que isso usa.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52. Responsabilidade unica:
decompor um nome em prenome, sobrenomes e sufixos (`split_name_pt`), e derivar os
conjuntos e prefixos que o matching consome. O vocabulario de particulas e
sufixos vive aqui porque e um conceito unico, mesmo sendo consumido tambem pelo
matching.

`norm_name` foi MOVIDA para `utils/name_keys.py` pela OPP-20261006-LIGH: ela e
normalizacao de texto pura, sem dominio, e era a importacao que `csv_ingest`
fazia de `core`, fechando o ciclo `core/` <-> `parsers/`. O nome continua
importavel daqui por reexportacao.

Este modulo NAO define limpeza de mojibake: `strip_bad_utf` e `demojibake` sao
autoridade de `text_cleaning.py`, unificadas pela OPP-20260929-4LE3. Ter duas
funcoes com esse nome gerava falso positivo de divergencia no harness de
paridade.
"""
from __future__ import annotations

from utils.name_keys import norm_name
from utils.text_cleaning import strip_bad_utf


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
