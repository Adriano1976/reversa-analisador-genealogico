"""Medicao antes/depois da OPP-20260929-AU76.

Mede as duas variantes do pacote na MESMA base sintetica, com semente fixa:
  1. build_ged_indexes (uma vez por analise)
  2. match_candidates (uma vez por match do CSV)
  3. contagem de chamadas de norm_name e de fuzz, para explicar o ganho

Nenhum dado real. Nenhum arquivo do projeto muda.
"""
import importlib
import os
import pathlib
import random
import statistics
import sys
import time

ROOT = pathlib.Path(r"D:\Projetos\reversa_analisador_gelealogico")
# A e a linha de base; B e a versao sob teste. Ver equivalence_matching.py.
REAL = pathlib.Path(os.environ.get("VARIANT_A_DIR", str(ROOT / "analisador-genealogico")))
SHADOW = pathlib.Path(os.environ.get("VARIANT_B_DIR", str(ROOT / ".pytest-tmp" / "shadow")))

GIVENS = ["Maria", "Jose", "Ana", "Joao", "Carlos", "Fernanda", "Ricardo",
          "Beatriz", "Paulo", "Helena"]
SURNS = ["Silva", "Oliveira", "Santos", "Souza", "Pereira", "Ferreira",
         "Almeida", "Costa", "Rodrigues", "Lima", "Gomes", "Ribeiro",
         "Carvalho", "Azevedo", "Barbosa", "Martins", "Rocha", "Dias",
         "Nunes", "Moreira"]

PESSOAS = 3000
MATCHES = 100
REPETICOES = 3


class _Name:
    def __init__(self, s):
        self._s = s

    def format(self):
        return self._s


class _Person:
    def __init__(self, s):
        self.name = _Name(s)


def carregar_variante(dir_pacote):
    for k in list(sys.modules):
        if k == "reconstructed" or k.startswith("reconstructed."):
            del sys.modules[k]
    for p in (str(REAL), str(SHADOW)):
        while p in sys.path:
            sys.path.remove(p)
    sys.path.insert(0, str(dir_pacote))
    return importlib.import_module("reconstructed.dna_analysis")


def montar_base(seed=42):
    rnd = random.Random(seed)
    return {f"@I{i}@": _Person(f"{rnd.choice(GIVENS)} {rnd.choice(SURNS)} {rnd.choice(SURNS)}")
            for i in range(PESSOAS)}


def nomes_de_match(n=PESSOAS // 30):
    rnd = random.Random(99)
    return [f"{rnd.choice(GIVENS)} {rnd.choice(SURNS)} {rnd.choice(SURNS)}" for _ in range(n)]


def medir(D, tag):
    D.people = montar_base()

    contagem = {"norm_name": 0, "fuzz": 0}
    real_norm = D.norm_name
    real_fuzz = D.fuzz

    def norm_contando(s):
        contagem["norm_name"] += 1
        return real_norm(s)

    class FuzzContando:
        def __getattr__(self, k):
            fn = getattr(real_fuzz, k)

            def w(*a, **kw):
                contagem["fuzz"] += 1
                return fn(*a, **kw)

            return w

    D.norm_name = norm_contando
    D.fuzz = FuzzContando()

    tempos_idx, tempos_match = [], []
    for _ in range(REPETICOES):
        contagem["norm_name"] = 0
        contagem["fuzz"] = 0
        t0 = time.perf_counter()
        idx = D.build_ged_indexes()
        t1 = time.perf_counter()
        base_norm, base_fuzz = contagem["norm_name"], contagem["fuzz"]

        nomes = nomes_de_match()
        t2 = time.perf_counter()
        for nome in nomes:
            if len(idx) == 4:
                D.match_candidates(nome, 100.0, idx[0], idx[1], idx[3])
            else:
                D.match_candidates(nome, 100.0, idx[0], idx[1])
        t3 = time.perf_counter()

        tempos_idx.append(t1 - t0)
        tempos_match.append((t3 - t2) / len(nomes))
        metricas = {
            "norm_nome_por_pessoa": base_norm / PESSOAS,
            "fuzz_por_match": (contagem["fuzz"] - base_fuzz) / len(nomes),
            "norm_por_match": (contagem["norm_name"] - base_norm) / len(nomes),
        }
    D.norm_name = real_norm
    D.fuzz = real_fuzz

    return {
        "reconstrucao": tag,
        "pessoas": PESSOAS,
        "matches_medidos": len(nomes),
        "build_ged_indexes_s": round(statistics.median(tempos_idx), 4),
        "ms_por_match": round(statistics.median(tempos_match) * 1000, 2),
        "norm_name_por_pessoa": round(metricas["norm_nome_por_pessoa"], 2),
        "norm_name_por_match": round(metricas["norm_por_match"], 1),
        "fuzz_por_match": round(metricas["fuzz_por_match"], 1),
    }


def main():
    if not SHADOW.is_dir():
        print("ERRO: sombra ausente. Rode .pytest-tmp/shadow_opt_build.py antes.")
        return 2
    antes = medir(carregar_variante(REAL), "atual")
    depois = medir(carregar_variante(SHADOW), "otimizada")

    print(f"{'metrica':<24}{'atual':>12}{'otimizada':>12}{'ganho':>10}")
    for k in ["build_ged_indexes_s", "ms_por_match", "norm_name_por_pessoa",
              "norm_name_por_match", "fuzz_por_match"]:
        a, b = antes[k], depois[k]
        ganho = f"{a / b:.2f}x" if b else "n/a"
        if k in ("ms_por_match", "norm_name_por_match"):
            ganho = f"{a / b:.2f}x"
        print(f"{k:<24}{a:>12}{b:>12}{ganho:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
