"""Sonda do candidato da OPP-20260929-NUMT: mede o ganho e prova a equivalencia.

NAO toca no modulo. Reimplementa as variantes candidatas aqui dentro, mede todas
intercaladas e compara a saida de todas contra a versao atual, em todo o corpus.

## Variantes

- **v1** e o codigo de hoje: `df.apply(build_group_key, axis=1)` e a lista completa
  de colunas em `detect_columns`.
- **v2** troca `apply(axis=1)` por `Series.map` e para na primeira coluna que casa.
  Remove a construcao de uma `Series` por linha. Continua chamando `norm_name` uma
  vez por LINHA.
- **v3** acrescenta deduplicacao: normaliza cada nome UNICO uma vez e distribui por
  `map` sobre um dicionario. O numero de chamadas Python passa a ser proporcional
  ao numero de nomes distintos, nao ao numero de linhas. E o que ataca de fato o
  `est_return` declarado na oportunidade.

## Por que medir e nao estimar

`norm_name` custa cerca de 41 us (docstring do modulo) e e o custo dominante da
fase. Sem separar overhead de pandas de custo de normalizacao, nao da para saber
se vale trocar o `apply` sozinho ou se e preciso deduplicar.

Uso:
    python <este script>
"""

from __future__ import annotations

import os
import random
import statistics
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
SCRATCH = os.path.join(ROOT, ".pytest-tmp", "numt-bench")
FIXTURES = os.path.join(ROOT, "_reversa_sdd", "parity", "fixtures", "dna")

sys.path.insert(0, os.path.join(ROOT, "analisador-genealogico"))

REPS = 15
SEED = 20261001


def detect_v2(df):
    """Mesma escolha, parando na primeira coluna que casa."""
    name_col = next((col for col in ["Name", "MatchedName", "Nome"] if col in df.columns), None)
    cm_col = next((col for col in ["cM", "TotalCM", "Total cM"] if col in df.columns), None)
    match_id_col = next(
        (c for c in df.columns
         if df[c].astype(str).str.fullmatch(r"[A-Z]{2}\d{7}").mean() > 0.3), None)
    email_cols = [c for c in df.columns if "mail" in c.lower()]
    match_email_col = email_cols[-1] if email_cols else None
    return name_col, cm_col, match_id_col, match_email_col


def _fechar(D, df, name_col, cm_col, key):
    df["_group_key"] = key
    return (
        df.groupby("_group_key", as_index=False)
        .agg({cm_col: "sum"})
        .merge(
            df[["_group_key", name_col]].drop_duplicates("_group_key"),
            on="_group_key", how="left",
        )
    )


def aggregate_v2(D, df, name_col, cm_col, match_id_col, match_email_col):
    """Chave por coluna, sem `apply(axis=1)`. Uma normalizacao por linha."""
    name_key = df[name_col].map(lambda v: D.norm_name(D.demojibake(str(v))))
    if match_id_col:
        cauda = df[match_id_col].astype(str).str.strip().str.upper()
    elif match_email_col:
        cauda = df[match_email_col].map(lambda v: D.norm_name(str(v)))
    else:
        cauda = None
    return _fechar(D, df, name_col, cm_col,
                   name_key if cauda is None else name_key + " | " + cauda)


def aggregate_v3(D, df, name_col, cm_col, match_id_col, match_email_col):
    """Idem v2, mas normaliza cada nome UNICO uma vez.

    ATENCAO: usa `.map(str)`, nunca `.astype(str)`. Em coluna de objeto, o
    `astype(str)` do pandas PRESERVA o `NaN` como float em vez de virar a string
    'nan'; a v1 converte com `str(...)` por elemento. Trocar um pelo outro faz
    `demojibake(nan)` estourar com TypeError. Foi esta sonda que pegou o erro.
    """
    nomes = df[name_col].map(str)
    mapa = {v: D.norm_name(D.demojibake(v)) for v in nomes.drop_duplicates()}
    name_key = nomes.map(mapa)
    if match_id_col:
        cauda = df[match_id_col].map(str).str.strip().str.upper()
    elif match_email_col:
        emails = df[match_email_col].map(str)
        mapa_e = {v: D.norm_name(v) for v in emails.drop_duplicates()}
        cauda = emails.map(mapa_e)
    else:
        cauda = None
    return _fechar(D, df, name_col, cm_col,
                   name_key if cauda is None else name_key + " | " + cauda)


def resumo(amostras):
    return min(amostras), statistics.median(amostras)


def comparar(D, df, rotulo, problemas):
    """Compara v1, v2 e v3 na mesma entrada e registra divergencia."""
    cols = D.detect_columns(df)
    cols2 = detect_v2(df)
    if cols != cols2:
        problemas.append("%s: colunas detectadas diferem: %s vs %s" % (rotulo, cols, cols2))
        return None
    if not cols[0] or not cols[1]:
        return "fora-do-fluxo"
    base = D.aggregate_matches(df.copy(), *cols)
    for rot, fn in (("v2", aggregate_v2), ("v3", aggregate_v3)):
        alt = fn(D, df.copy(), *cols2)
        if not base.equals(alt):
            problemas.append("%s: saida de %s difere da v1" % (rotulo, rot))
            return None
    return cols


def main() -> int:
    from reconstructed import dna_analysis as D

    print("SONDA DO CANDIDATO · OPP-20260929-NUMT")
    print("=" * 78)

    print("\n### Equivalencia: v1 contra v2 e v3")
    problemas = []
    for nome in sorted(f for f in os.listdir(FIXTURES) if f.endswith(".csv")):
        df = D.read_csv_with_fallback(os.path.join(FIXTURES, nome))
        cols = comparar(D, df, nome, problemas)
        veredito = ("fora do fluxo" if cols == "fora-do-fluxo"
                    else ("identico" if cols else "DIVERGE"))
        print("  %-22s linhas=%d  colunas=%s  %s" % (nome, len(df), cols, veredito))

    import pandas as pd
    bordas = {
        "cabecalho-so": pd.DataFrame({"Name": [], "cM": [], "Match ID": []}),
        "sem-id-sem-email": pd.DataFrame({"Name": ["Ana Silva Souza"], "cM": [200]}),
        "cm-numerico": pd.DataFrame({"Name": ["Ana Silva Souza"], "cM": [200.5],
                                     "Match ID": ["AB1234567"]}),
        "id-e-email": pd.DataFrame({"Name": ["Ana Silva Souza"], "cM": [200],
                                    "Match ID": ["AB1234567"], "Email": ["a@b.c"]}),
        "nome-nan": pd.DataFrame({"Name": [None, "Ana Silva Souza"], "cM": [10, 20],
                                  "Match ID": ["AB1234567", "CD7654321"]}),
        "nome-vazio": pd.DataFrame({"Name": ["", "   "], "cM": [10, 20],
                                    "Match ID": ["AB1234567", "CD7654321"]}),
        "mojibake": pd.DataFrame({"Name": ["JoÃ£o Silva", "Ana Souza"], "cM": [10, 20],
                                  "Match ID": ["AB1234567", "CD7654321"]}),
        "duplicado": pd.DataFrame({"Name": ["Ana Silva Souza", "Ana Silva Souza"],
                                   "cM": [387, 150], "Match ID": ["AB1234567", "AB1234567"]}),
        "email-repetido": pd.DataFrame({"Name": ["Ana Silva Souza", "Ana Souza"],
                                        "cM": [387, 150],
                                        "Email": ["A@X.com", "a@x.com"]}),
    }
    for rotulo, df in bordas.items():
        cols = comparar(D, df, rotulo, problemas)
        veredito = ("fora do fluxo" if cols == "fora-do-fluxo"
                    else ("identico" if cols else "DIVERGE"))
        print("  %-22s linhas=%d  colunas=%s  %s" % (rotulo, len(df), cols, veredito))

    print("\n### Veredito: %s"
          % ("IDENTICO em todo o corpus" if not problemas else "DIVERGENCIAS"))
    for p in problemas:
        print("  !! %s" % p)

    # ------------------------------------------------------------- medicao
    print("\n" + "=" * 78)
    print("### Ganho medido: v1, v2, v3 intercalados, minimo de %d repeticoes" % REPS)
    print("(negativo = mais rapido que a v1)")

    nomes = ["N%d %s %s" % (i, ["Silva", "Souza", "Lima"][i % 3], ["Costa", "Pereira"][i % 2])
             for i in range(1023)]
    rnd = random.Random(SEED)
    os.makedirs(SCRATCH, exist_ok=True)

    for n in (300, 1000, 3000):
        linhas = ["Name,Match Name,cM,Total cM,Match ID,Email,Chromosomes,SNPs"]
        for i in range(n):
            nome = nomes[rnd.randrange(len(nomes))]
            cm = rnd.choice([15, 37, 88, 175, 480])
            linhas.append("%s,%s,%d,%d,%s%s%d,m%d@x.test,%d,%d"
                          % (nome, nome, cm, cm * 3, chr(65 + i % 26),
                             chr(65 + (i // 26) % 26), 1000000 + i, i,
                             rnd.randint(1, 23), rnd.randint(300, 9000)))
        p = os.path.join(SCRATCH, "probe_%d.csv" % n)
        open(p, "w", encoding="utf-8", newline="\n").write("\n".join(linhas) + "\n")

        df = D.read_csv_with_fallback(p)
        cols = D.detect_columns(df)
        unicos = df["Name"].nunique()
        am = {"det1": [], "det2": [], "agg1": [], "agg2": [], "agg3": []}

        D.detect_columns(df)
        detect_v2(df)
        D.aggregate_matches(df.copy(), *cols)
        aggregate_v2(D, df.copy(), *cols)
        aggregate_v3(D, df.copy(), *cols)

        for _ in range(REPS):
            t0 = time.perf_counter()
            D.detect_columns(df)
            am["det1"].append(time.perf_counter() - t0)
            t0 = time.perf_counter()
            detect_v2(df)
            am["det2"].append(time.perf_counter() - t0)

            d = df.copy()
            t0 = time.perf_counter()
            D.aggregate_matches(d, *cols)
            am["agg1"].append(time.perf_counter() - t0)
            d = df.copy()
            t0 = time.perf_counter()
            aggregate_v2(D, d, *cols)
            am["agg2"].append(time.perf_counter() - t0)
            d = df.copy()
            t0 = time.perf_counter()
            aggregate_v3(D, d, *cols)
            am["agg3"].append(time.perf_counter() - t0)

        print("\n  CSV de %d linhas  |  %d nomes distintos em %d linhas" % (n, unicos, n))
        m1, _ = resumo(am["det1"])
        m2, _ = resumo(am["det2"])
        print("    detect_columns     v1 %8.5f s   v2 %8.5f s   %+6.1f%%"
              % (m1, m2, 100.0 * (m2 - m1) / m1))
        m1, _ = resumo(am["agg1"])
        for chave, rot in (("agg2", "v2 (map)     "), ("agg3", "v3 (map+dedup)")):
            m2, _ = resumo(am[chave])
            print("    aggregate_matches  v1 %8.5f s   %s %8.5f s   %+6.1f%%"
                  % (m1, rot, m2, 100.0 * (m2 - m1) / m1))
    # Controle decisivo: a v3 e sempre melhor que a v2, ou so quando ha nomes
    # repetidos? Mesmo tamanho, nenhuma repeticao. Se a v3 perder aqui, ela nao
    # domina a v2 e a escolha depende da forma do CSV.
    n = 3000
    linhas = ["Name,cM,Match ID"]
    for i in range(n):
        linhas.append("Pessoa%d Sobrenome%d,%d,AB%07d" % (i, i, 15 + (i % 700), 1000000 + i))
    p = os.path.join(SCRATCH, "probe_unico_%d.csv" % n)
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(linhas) + "\n")

    df = D.read_csv_with_fallback(p)
    cols = D.detect_columns(df)
    am = {"agg1": [], "agg2": [], "agg3": []}
    D.aggregate_matches(df.copy(), *cols)
    aggregate_v2(D, df.copy(), *cols)
    aggregate_v3(D, df.copy(), *cols)
    for _ in range(REPS):
        d = df.copy()
        t0 = time.perf_counter()
        D.aggregate_matches(d, *cols)
        am["agg1"].append(time.perf_counter() - t0)
        d = df.copy()
        t0 = time.perf_counter()
        aggregate_v2(D, d, *cols)
        am["agg2"].append(time.perf_counter() - t0)
        d = df.copy()
        t0 = time.perf_counter()
        aggregate_v3(D, d, *cols)
        am["agg3"].append(time.perf_counter() - t0)

    m1, _ = resumo(am["agg1"])
    print("\n  CONTROLE: %d linhas, %d nomes distintos (nenhuma repeticao)"
          % (n, df["Name"].nunique()))
    for chave, rot in (("agg2", "v2 (map)     "), ("agg3", "v3 (map+dedup)")):
        m2, _ = resumo(am[chave])
        print("    aggregate_matches  v1 %8.5f s   %s %8.5f s   %+6.1f%%"
              % (m1, rot, m2, 100.0 * (m2 - m1) / m1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
