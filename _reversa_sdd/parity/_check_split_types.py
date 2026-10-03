"""Verifica se `split_name_pt` devolve set ou list nos DOIS lados.

O harness reportou para `variants.ged`:
    oraculo   = ['jos', ['gouveia'], ['filho', 'neto']]
    candidato = ['jos', ['gouveia'], ['neto', 'filho']]

Se o terceiro elemento for `set` nos dois lados, `_canon()` deveria ordenar e a
divergencia NAO deveria aparecer. Como apareceu, um lado nao devolve set. Este
script responde qual — com o tipo real, nao por leitura de codigo.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GED = os.path.join(HERE, "fixtures", "gedcom", "variants.ged")
NOME = "Jos\u00e9 /Gouveia Neto/ Filho"

COLETOR = r'''
import importlib.util, json, os, shutil, sys

W = sys.argv[1]; GED = sys.argv[2]; NOME = sys.argv[3]; LADO = sys.argv[4]
tmp = os.path.join(W, ".parity-types-" + LADO)
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)

if LADO == "oracle":
    local = os.path.join(tmp, "oracle.py")
    shutil.copyfile(os.path.join(W, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py"), local)
    os.chdir(tmp)
    spec = importlib.util.spec_from_file_location("oracle", local)
    m = importlib.util.module_from_spec(spec); sys.modules["oracle"] = m
    spec.loader.exec_module(m)
    m.load_gedcom_and_build_graph(GED)
    fn = m.split_name_pt
else:
    sys.path.insert(0, os.path.join(W, "src"))
    os.chdir(tmp)
    from reconstructed import dna_analysis as D
    from reconstructed import upload as U
    U.load_gedcom_and_build_graph(GED)
    fn = D.split_name_pt

r = fn(NOME)
terceiro = r[2]
print(json.dumps({
    "lado": LADO,
    "resultado": [r[0], list(r[1]), sorted(terceiro)],
    "tipo_do_terceiro": type(terceiro).__name__,
    "tipo_do_resultado": type(r).__name__,
    "tipo_do_segundo": type(r[1]).__name__,
    "terceiro_como_saiu": list(terceiro),
}, ensure_ascii=False))
shutil.rmtree(tmp, ignore_errors=True)
'''


def lado(qual: str):
    runner = os.path.join(HERE, "_types_%s.py" % qual)
    with open(runner, "w", encoding="utf-8") as fh:
        fh.write(COLETOR)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, runner, ROOT, GED, NOME, qual],
                          capture_output=True, text=True, encoding="utf-8", env=env)
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr)
        return None
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> int:
    print("=" * 78)
    print("TIPOS REAIS de split_name_pt(%r)" % NOME)
    print("=" * 78)
    o = lado("oracle")
    c = lado("cand")
    for d in (o, c):
        if d:
            print("  %-9s resultado=%s" % (d["lado"], d["tipo_do_resultado"]))
            print("            segundo   =%s" % d["tipo_do_segundo"])
            print("            terceiro  =%s   <-- DECIDE a comparacao" % d["tipo_do_terceiro"])
            print("            saida     =%s" % d["terceiro_como_saiu"])
    print("-" * 78)
    if o and c:
        if o["tipo_do_terceiro"] == "set" and c["tipo_do_terceiro"] == "set":
            print("AMBOS set -> _canon() deveria ordenar. A divergencia seria bug do _canon().")
        elif o["tipo_do_terceiro"] != c["tipo_do_terceiro"]:
            print("TIPOS DIFERENTES (%s vs %s) -> divergencia de CONTRATO, nao de ordem."
                  % (o["tipo_do_terceiro"], c["tipo_do_terceiro"]))
            print("Compare o que o harness coleta: o oracle devolve LISTA e o candidato SET?")
        else:
            print("Ambos %s -> ordem e contrato, divergencia REAL." % o["tipo_do_terceiro"])
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
