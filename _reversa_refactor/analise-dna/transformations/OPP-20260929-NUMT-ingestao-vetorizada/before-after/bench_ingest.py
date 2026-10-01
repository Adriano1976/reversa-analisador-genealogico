"""Benchmark do gargalo de ingestao de CSV (OPP-20260929-NUMT).

Mede as duas fases que a oportunidade ataca, em isolamento e dentro do fluxo
completo:

    detect_columns      varredura por regex de TODAS as colunas, para escolher uma
    aggregate_matches   df.apply(axis=1) linha a linha, com norm_name por linha

## Complexidade declarada antes da otimizacao

| Fase | Tempo | Espaco |
|------|-------|--------|
| `detect_columns` | O(k * n), k = numero de colunas, n = linhas do CSV | O(n) temporario por coluna |
| `aggregate_matches` | O(n) chamadas Python, cada uma alocando uma `Series` com TODAS as colunas (custo do `apply(axis=1)`), mais O(n) para o `groupby` | O(n) |

As duas crescem com o **numero de linhas do CSV**, nao com o numero de candidatos
do GEDCOM. `aggregate_matches` cresce tambem com o numero de **colunas**, porque
`apply(axis=1)` monta uma `Series` por linha. O diagnostico de colunas mede isso.

## Metodologia

- `perf_counter`, minimo e mediana. O minimo e o estimador principal: e o menos
  contaminado por ruido de agendamento do sistema.
- Aquecimento antes de cada medicao, para tirar do caminho o custo de primeira
  chamada (compilacao de regex, import preguicoso de pandas).
- **Medicoes intercaladas**: a rodada externa e a repeticao, e a interna percorre
  todos os tamanhos. Medir um tamanho inteiro em bloco faz uma lentidao momentanea
  da maquina contaminar um tamanho so, o que produziu uma curva nao monotonica na
  primeira versao deste instrumento.
- As copias do DataFrame usadas em `aggregate_matches` sao criadas FORA da regiao
  cronometrada, porque a funcao muta o df ao gravar a coluna `_group_key`.
- GEDCOM e CSV sao sinteticos e deterministicos (seed fixa): o numero se reproduz
  sem depender de dado real de ninguem.

Uso:
    python <este script>
"""

from __future__ import annotations

import os
import statistics
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
SCRATCH = os.path.join(ROOT, ".pytest-tmp", "numt-bench")

sys.path.insert(0, os.path.join(ROOT, "analisador-genealogico"))

SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Pereira", "Lima", "Costa", "Almeida"]
PRENOMES = ["Joao", "Maria", "Jose", "Ana", "Carlos", "Marta", "Luiz", "Helena", "Paulo",
            "Rita", "Pedro", "Clara", "Miguel", "Sonia", "Rafael", "Ines", "Bruno",
            "Tania", "Sergio", "Vera", "Otavio", "Lidia", "Caio", "Neusa", "Ivo",
            "Bianca", "Dario", "Elisa", "Fabio", "Gilda", "Hugo", "Iara"]

TAMANHOS_CSV = [300, 1000, 3000]
LINHAS_GEDCOM = 1023
REPS_FASE = 15
REPS_FLUXO = 5
SEED = 20261001
N_COLUNAS_COMPLETO = 8
N_COLUNAS_MAGRO = 3


def nomes_do_gedcom(n_pessoas: int) -> list:
    """Nome completo por pessoa, com sobrenomes agrupados como numa arvore real."""
    nomes = []
    for i in range(n_pessoas):
        p = PRENOMES[i % len(PRENOMES)]
        s1 = SOBRENOMES[(i // 3) % len(SOBRENOMES)]
        s2 = SOBRENOMES[(i // 11) % len(SOBRENOMES)]
        nomes.append("%s %s %s" % (p, s1, s2))
    return nomes


def gerar_gedcom(caminho: str, n_pessoas: int) -> list:
    """GEDCOM minimo e valido: INDIs com NAME, FAMs com HUSB/WIFE/CHIL."""
    nomes = nomes_do_gedcom(n_pessoas)
    linhas = ["0 HEAD", "1 SOUR BENCH", "1 GEDC", "2 VERS 5.5.1", "2 FORM LINEAGE-LINKED"]
    for i, nome in enumerate(nomes, start=1):
        partes = nome.split()
        linhas.append("0 @I%d@ INDI" % i)
        linhas.append("1 NAME %s /%s/" % (partes[0], " ".join(partes[1:])))
        linhas.append("1 SEX %s" % ("M" if i % 2 else "F"))
    fam, pai = 1, 1
    while pai + 2 <= n_pessoas:
        linhas.append("0 @F%d@ FAM" % fam)
        linhas.append("1 HUSB @I%d@" % pai)
        linhas.append("1 WIFE @I%d@" % (pai + 1))
        linhas.append("1 CHIL @I%d@" % (pai + 2))
        fam += 1
        pai += 3
    linhas.append("0 TRLR")
    with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(linhas) + "\n")
    return nomes


def gerar_csv(caminho: str, nomes: list, n_linhas: int, seed: int, n_colunas: int) -> None:
    """CSV com a forma de um export do GEDmatch.

    As 8 colunas existem de proposito: `detect_columns` varre TODAS elas com regex
    para descobrir no maximo uma, e `apply(axis=1)` monta uma Series com todas.
    """
    import random
    rnd = random.Random(seed)
    todas = ["Name", "Match Name", "cM", "Total cM", "Match ID", "Email",
             "Chromosomes", "SNPs"]
    cabecalho = todas[:n_colunas]
    linhas = [",".join(cabecalho)]
    for i in range(n_linhas):
        nome = nomes[rnd.randrange(len(nomes))]
        cm = rnd.choice([15, 22, 37, 48, 63, 88, 120, 175, 240, 310, 480, 700])
        mid = "%s%s%d" % (chr(65 + i % 26), chr(65 + (i // 26) % 26), 1000000 + i)
        valores = {"Name": nome, "Match Name": nome, "cM": str(cm), "Total cM": str(cm * 3),
                   "Match ID": mid, "Email": "match%d@exemplo.test" % i,
                   "Chromosomes": str(rnd.randint(1, 23)), "SNPs": str(rnd.randint(300, 9000))}
        linhas.append(",".join(valores[c] for c in cabecalho))
    with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(linhas) + "\n")


def resumo(amostras: list) -> tuple:
    return min(amostras), statistics.median(amostras)


def main() -> int:
    os.makedirs(SCRATCH, exist_ok=True)
    gedcom = os.path.join(SCRATCH, "bench.ged")
    nomes = gerar_gedcom(gedcom, LINHAS_GEDCOM)

    from reconstructed import upload as U
    from reconstructed import dna_analysis as D

    U.load_gedcom_and_build_graph(gedcom)
    print("GEDCOM sintetico : %d pessoas, %d familias" % (len(U.people), len(U.families)))
    print("CSV por escala   : %s linhas, %d colunas (%d no diagnostico)"
          % (TAMANHOS_CSV, N_COLUNAS_COMPLETO, N_COLUNAS_MAGRO))
    print("repeticoes       : %d por fase, %d por fluxo, com aquecimento e intercaladas"
          % (REPS_FASE, REPS_FLUXO))
    print("=" * 78)

    # --- preparo (fora de qualquer regiao cronometrada) ---------------------
    casos = []
    for n in TAMANHOS_CSV:
        csv_path = os.path.join(SCRATCH, "bench_%d.csv" % n)
        gerar_csv(csv_path, nomes, n, SEED + n, N_COLUNAS_COMPLETO)
        csv_magro = os.path.join(SCRATCH, "bench_%d_magro.csv" % n)
        gerar_csv(csv_magro, nomes, n, SEED + n, N_COLUNAS_MAGRO)
        df = D.read_csv_with_fallback(csv_path)
        df_magro = D.read_csv_with_fallback(csv_magro)
        casos.append({
            "n": n, "csv": csv_path, "raiz": " ".join(nomes[0].split()[:2]),
            "df": df, "cols": D.detect_columns(df),
            "df_magro": df_magro, "cols_magro": D.detect_columns(df_magro),
            "det": [], "agg": [], "magro": [], "fluxo": [],
        })

    # --- aquecimento -------------------------------------------------------
    for c in casos:
        D.detect_columns(c["df"])
        d = c["df"].copy()
        D.aggregate_matches(d, *c["cols"])
        d = c["df_magro"].copy()
        D.aggregate_matches(d, *c["cols_magro"])
        D.dna_analysis(c["csv"], c["raiz"])

    # --- fases, intercaladas por tamanho -----------------------------------
    for _ in range(REPS_FASE):
        for c in casos:
            t0 = time.perf_counter()
            D.detect_columns(c["df"])
            c["det"].append(time.perf_counter() - t0)
        for c in casos:
            d = c["df"].copy()
            t0 = time.perf_counter()
            D.aggregate_matches(d, *c["cols"])
            c["agg"].append(time.perf_counter() - t0)
        for c in casos:
            d = c["df_magro"].copy()
            t0 = time.perf_counter()
            D.aggregate_matches(d, *c["cols_magro"])
            c["magro"].append(time.perf_counter() - t0)

    # --- fluxo completo, intercalado ---------------------------------------
    for _ in range(REPS_FLUXO):
        for c in casos:
            t0 = time.perf_counter()
            D.dna_analysis(c["csv"], c["raiz"])
            c["fluxo"].append(time.perf_counter() - t0)

    # --- relatorio ---------------------------------------------------------
    for c in casos:
        c["t_det"] = resumo(c["det"])
        c["t_agg"] = resumo(c["agg"])
        c["t_magro"] = resumo(c["magro"])
        c["t_fluxo"] = resumo(c["fluxo"])
        soma = c["t_det"][0] + c["t_agg"][0]
        print("\n### CSV de %d linhas  |  colunas detectadas: %s" % (c["n"], c["cols"]))
        print("  detect_columns     min %8.5f s   mediana %8.5f s   %5.1f%% do fluxo"
              % (c["t_det"][0], c["t_det"][1], 100.0 * c["t_det"][0] / c["t_fluxo"][0]))
        print("  aggregate_matches  min %8.5f s   mediana %8.5f s   %5.1f%% do fluxo"
              % (c["t_agg"][0], c["t_agg"][1], 100.0 * c["t_agg"][0] / c["t_fluxo"][0]))
        print("  fluxo completo     min %8.5f s   mediana %8.5f s" % c["t_fluxo"])
        print("  soma das duas fases: %8.5f s   %5.1f%% do fluxo (min)"
              % (soma, 100.0 * soma / c["t_fluxo"][0]))
        print("  so %d colunas       min %8.5f s   (mesmas %d linhas, %d -> %d colunas)"
              % (N_COLUNAS_MAGRO, c["t_magro"][0], c["n"], N_COLUNAS_COMPLETO, N_COLUNAS_MAGRO))

    print("\n" + "=" * 78)
    print("CRESCIMENTO COM O TAMANHO DO CSV (minimo)")
    print("%8s %14s %14s %14s" % ("linhas", "detect_col", "aggregate", "fluxo"))
    for c in casos:
        print("%8d %14.5f %14.5f %14.5f" % (c["n"], c["t_det"][0], c["t_agg"][0], c["t_fluxo"][0]))

    print("\nDEPENDENCIA DE aggregate_matches COM O NUMERO DE COLUNAS (minimo)")
    print("%8s %16s %16s %10s" % ("linhas", "8 colunas", "3 colunas", "razao"))
    for c in casos:
        r = c["t_agg"][0] / c["t_magro"][0] if c["t_magro"][0] else 0
        print("%8d %16.5f %16.5f %9.2fx" % (c["n"], c["t_agg"][0], c["t_magro"][0], r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
