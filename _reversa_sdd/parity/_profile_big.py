"""Isola ONDE o tempo vai no GEDCOM grande — em vez de adivinhar.

Contexto: o harness estourou o timeout mesmo com a amostra de pares reduzida de
1.600 para 64. Isso REFUTA a hipotese de que os pares de caminho eram o gargalo.
Este probe mede cada fase separadamente para apontar a fase real.

Mesmo isolamento do harness: subprocesso proprio, chdir antes do import (o import
do oraculo cria uploads/ e static/ no cwd).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

COLETOR = r'''
import json, os, shutil, sys, time

W = sys.argv[1]; GED = sys.argv[2]
tmp = os.path.join(W, ".parity-profile")
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
local = os.path.join(tmp, "oracle.py")
shutil.copyfile(os.path.join(W, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py"), local)
os.chdir(tmp)

def crono(rotulo, fn):
    t = time.perf_counter()
    v = fn()
    print("%-34s %8.2fs" % (rotulo, time.perf_counter() - t), flush=True)
    return v

import importlib.util
t0 = time.perf_counter()
spec = importlib.util.spec_from_file_location("oracle", local)
m = importlib.util.module_from_spec(spec); sys.modules["oracle"] = m
spec.loader.exec_module(m)
print("%-34s %8.2fs" % ("import do oraculo", time.perf_counter() - t0), flush=True)

names = crono("load_gedcom_and_build_graph", lambda: m.load_gedcom_and_build_graph(GED))
ids = sorted(m.people.keys())
print("%-34s %8d" % ("pessoas", len(m.people)), flush=True)
print("%-34s %8d" % ("familias", len(m.families)), flush=True)

# Probes por pessoa — quantas funcoes de nome rodam sobre a LISTA COMPLETA de nomes.
crono("get_name (todas as pessoas)", lambda: [m.get_name(m.people[i]) for i in ids])
crono("norm_name (todos os nomes)", lambda: [m.norm_name(n) for n in names])
crono("strip_bad_utf (todos os nomes)", lambda: [m.strip_bad_utf(n) for n in names])
crono("demojibake (todos os nomes)", lambda: [m.demojibake(n) for n in names])
crono("split_name_pt (todos os nomes)", lambda: [m.split_name_pt(n) for n in names])
crono("surnames_set (todos os nomes)", lambda: [m.surnames_set(n) for n in names])
crono("top_given_tokens (todos os nomes)", lambda: [m.top_given_tokens(n) for n in names])
crono("surname_core_tokens (todos os nomes)", lambda: [m.surname_core_tokens(n) for n in names])

# Custo UNITARIO de uma busca de caminho no grafo grande.
a, b = ids[0], ids[-1]
n = 20
t = time.perf_counter()
for _ in range(n):
    m.find_ancestral_path(a, b)
dt = (time.perf_counter() - t) / n
print("%-34s %8.4fs  (x1600 pares = %.0fs)" % ("find_ancestral_path (unitario)", dt, dt * 1600), flush=True)

t = time.perf_counter()
for _ in range(n):
    m.find_indirect_path(a, b)
dt2 = (time.perf_counter() - t) / n
print("%-34s %8.4fs  (x1600 pares = %.0fs)" % ("find_indirect_path (unitario)", dt2, dt2 * 1600), flush=True)

shutil.rmtree(tmp, ignore_errors=True)
'''


def main() -> int:
    ged = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "src", "uploads", "Arvore_Unificada_Oficial_V1_2.ged")
    runner = os.path.join(HERE, "_profile_collector.py")
    with open(runner, "w", encoding="utf-8") as fh:
        fh.write(COLETOR)
    print("=" * 78)
    print("PERFIL DE TEMPO — %s (%.0f KB)" % (os.path.basename(ged), os.path.getsize(ged) / 1024))
    print("=" * 78, flush=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    # Sem `capture_output`: aqui QUEREMOS ver as linhas de tempo em tempo real.
    rc = subprocess.call([sys.executable, runner, ROOT, ged], env=env)
    print("=" * 78)
    print("exit=%d" % rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
