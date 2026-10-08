"""Sonda de perfil do matching difuso (somente leitura, sem dado real).

Gera nomes sinteticos em memoria, substitui o dict `people` do modulo
reconstructed/dna_analysis e mede:
  - custo de build_ged_indexes
  - custo de match_candidates por match
  - quantas chamadas de fuzz e de norm_name cada caminho dispara

Nenhum arquivo do projeto e alterado. Nenhum dado real e usado.
"""
import random
import sys
import time

sys.path.insert(0, r"D:\Projetos\reversa_analisador_gelealogico\analisador-genealogico")

from reconstructed import dna_analysis as dna  # noqa: E402


class Name:
    def __init__(self, s):
        self._s = s

    def format(self):
        return self._s


class Person:
    def __init__(self, s):
        self.name = Name(s)


random.seed(42)
GIVENS = ["Maria", "Jose", "Ana", "Joao", "Carlos", "Fernanda",
          "Ricardo", "Beatriz", "Paulo", "Helena"]
SURNS = ["Silva", "Oliveira", "Santos", "Souza", "Pereira", "Ferreira",
         "Almeida", "Costa", "Rodrigues", "Lima", "Gomes", "Ribeiro",
         "Carvalho", "Azevedo", "Barbosa", "Martins", "Rocha", "Dias",
         "Nunes", "Moreira"]


def gen_name():
    return f"{random.choice(GIVENS)} {random.choice(SURNS)} {random.choice(SURNS)}"


N = 3000
dna.people = {f"@I{i}@": Person(gen_name()) for i in range(N)}

# Contadores
counts = {"norm_name": 0, "fuzz_ratio": 0, "fuzz_token": 0, "fuzz_partial": 0}
_real_norm = dna.norm_name


def counting_norm(s):
    counts["norm_name"] += 1
    return _real_norm(s)


dna.norm_name = counting_norm

_real_fuzz = dna.fuzz


class CountingFuzz:
    def __getattr__(self, k):
        fn = getattr(_real_fuzz, k)
        key = {"ratio": "fuzz_ratio", "token_sort_ratio": "fuzz_token",
               "partial_ratio": "fuzz_partial"}.get(k)
        if key is None:
            return fn

        def wrapper(*a, **kw):
            counts[key] += 1
            return fn(*a, **kw)

        return wrapper


dna.fuzz = CountingFuzz()

t0 = time.perf_counter()
ged_index, surname_index, given_index = dna.build_ged_indexes()
t1 = time.perf_counter()
print(f"build_ged_indexes       : {t1 - t0:7.3f}s para {N} pessoas")
print(f"  norm_name chamado     : {counts['norm_name']} vezes "
      f"({counts['norm_name'] / N:.1f} por pessoa)")
print(f"  given_index construido: {len(given_index)} chaves (nunca lido por match_candidates)")

base = dict(counts)
M = 100
matches = [gen_name() for _ in range(M)]
t0 = time.perf_counter()
for m in matches:
    dna.match_candidates(m, 100.0, ged_index, surname_index)
t1 = time.perf_counter()
dt = t1 - t0
print(f"match_candidates        : {dt:7.3f}s para {M} matches "
      f"({1000 * dt / M:.1f} ms por match)")

d = {k: counts[k] - base[k] for k in counts}
tot = d["fuzz_ratio"] + d["fuzz_token"] + d["fuzz_partial"]
print(f"  candidatos avaliados  : {d['fuzz_token']} (1 por candidato no pool)")
print(f"  chamadas fuzz         : {tot} ({tot / M:.0f} por match)")
print(f"  norm_name no loop     : {d['norm_name']} "
      f"({d['norm_name'] / max(d['fuzz_token'], 1):.1f} por candidato)")

t0 = time.perf_counter()
for m in matches:
    _real_norm(m)
t1 = time.perf_counter()
print(f"norm_name isolado       : {(t1 - t0) * 1e6 / M:7.1f} us por chamada")

t0 = time.perf_counter()
for m in matches:
    dna.surnames_set(m)
t1 = time.perf_counter()
print(f"surnames_set isolado    : {(t1 - t0) * 1e6 / M:7.1f} us por chamada")
