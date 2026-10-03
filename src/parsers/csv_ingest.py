"""Leitura do CSV de matches e agregacao por match.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52. Responsabilidade unica:
ler o arquivo tolerando encoding, descobrir as colunas e reduzir varias linhas do
mesmo match a uma, somando os cM dos segmentos.
"""
from __future__ import annotations

import pandas as pd

from utils.text_cleaning import demojibake
from core.name_normalization import norm_name


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
    # Para na primeira coluna que casa: a lista completa era montada para depois pegar
    # o primeiro elemento, e a semantica sempre foi "a primeira que casa".
    match_id_col = next(
        (c for c in df.columns
         if df[c].astype(str).str.fullmatch(r"[A-Z]{2}\d{7}").mean() > 0.3), None)
    email_cols = [c for c in df.columns if "mail" in c.lower()]
    match_email_col = email_cols[-1] if email_cols else None
    return name_col, cm_col, match_id_col, match_email_col


def aggregate_matches(df, name_col, cm_col, match_id_col, match_email_col):
    # Chave montada por operacao de coluna. `apply(axis=1)` montava uma Series por
    # linha; aqui o nome e normalizado uma vez por nome DISTINTO, nao por linha.
    #
    # `map(str)` e obrigatorio no lugar de `astype(str)`: em coluna de objeto o
    # `astype(str)` do pandas preserva o NaN como float, e `demojibake` estoura.
    nomes = df[name_col].map(str)
    mapa = {v: norm_name(demojibake(v)) for v in nomes.drop_duplicates()}
    name_key = nomes.map(mapa)
    if match_id_col:
        cauda = df[match_id_col].map(str).str.strip().str.upper()
    elif match_email_col:
        emails = df[match_email_col].map(str)
        cauda = emails.map({v: norm_name(v) for v in emails.drop_duplicates()})
    else:
        cauda = None
    df["_group_key"] = name_key if cauda is None else name_key + " | " + cauda
    aggregated = (
        df.groupby("_group_key", as_index=False)
        .agg({cm_col: "sum"})
        .merge(
            df[["_group_key", name_col]].drop_duplicates("_group_key"),
            on="_group_key", how="left",
        )
    )
    return aggregated
