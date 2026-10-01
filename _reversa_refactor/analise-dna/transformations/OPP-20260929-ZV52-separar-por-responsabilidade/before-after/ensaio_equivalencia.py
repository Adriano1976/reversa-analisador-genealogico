"""Ensaio da divisao: monta um pacote espelho e compara o comportamento com o real.

NAO toca na arvore legada. Copia `analisador-genealogico/` para
`.pytest-tmp/zv52-ensaio/`, sobrepoe os 4 arquivos gerados por `gerar_divisao.py`,
e roda o MESMO runner em dois processos separados: um apontando para o pacote
real, outro para o espelho.

O runner imprime, em JSON canonico, para cada caso do corpus:
  - o resultado completo de `dna_analysis(csv, raiz)`
  - o resultado das funcoes puras do nucleo, uma a uma
  - a presenca dos 18 nomes da superficie de compatibilidade

Se os dois JSON forem iguais, a divisao preservou comportamento e superficie
antes de qualquer arquivo do projeto ser tocado.

Uso:
    python <este script>
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
ESPELHO = os.path.join(ROOT, ".pytest-tmp", "zv52-proposta", "analisador-genealogico")
ENSAIO = os.path.join(ROOT, ".pytest-tmp", "zv52-ensaio")
REAL = os.path.join(ROOT, "analisador-genealogico")
FIXTURES = os.path.join(ROOT, "_reversa_sdd", "parity", "fixtures", "dna")
BENCH = os.path.join(ROOT, ".pytest-tmp", "numt-bench")
ARQUIVOS = ["name_normalization.py", "csv_ingest.py", "matching.py", "dna_analysis.py"]

RUNNER = r'''
import json, os, sys

PKG = sys.argv[1]
ROOT = sys.argv[2]
sys.path.insert(0, PKG)
sys.path.insert(0, os.path.join(ROOT, "tests", "fixtures"))

import sample_dna
from reconstructed import upload as U
from reconstructed import dna_analysis as D

API = ["dna_analysis", "get_relationships_by_cm", "aggregate_matches", "detect_columns",
       "read_csv_with_fallback", "build_ged_indexes", "match_candidates", "norm_name",
       "split_name_pt", "surnames_set", "top_given_tokens", "token_prefixes",
       "drop_short_tokens", "surname_core_tokens", "soft_prefix_jaccard",
       "strip_bad_utf", "demojibake", "SHARED_CM_DATA"]

saida = {}
saida["superficie"] = {n: hasattr(D, n) for n in API}

def puro(nome, fn):
    try:
        v = fn()
        if isinstance(v, (set, frozenset)):
            v = sorted(v)
        elif isinstance(v, tuple):
            v = [list(x) if isinstance(x, (list, tuple, set)) else x for x in v]
        return v
    except Exception as e:
        return "ERRO:" + type(e).__name__

AMOSTRAS = ["Ana Silva Souza", "José  da Silva ", "JoÃO SILVA", "Maria de Souza Filho",
            "Zzz Ninguem dos Santos", "", "JoÃ£o Silva"]
saida["puras"] = {}
for n in AMOSTRAS:
    saida["puras"][n] = {
        "norm_name": puro(n, lambda n=n: D.norm_name(n)),
        "split_name_pt": puro(n, lambda n=n: D.split_name_pt(n)),
        "surnames_set": puro(n, lambda n=n: D.surnames_set(n)),
        "top_given_tokens": puro(n, lambda n=n: D.top_given_tokens(n)),
        "token_prefixes": puro(n, lambda n=n: D.token_prefixes(n.split())),
        "drop_short_tokens": puro(n, lambda n=n: D.drop_short_tokens(set(n.split()))),
        "surname_core_tokens": puro(n, lambda n=n: D.surname_core_tokens(n)),
        "strip_bad_utf": puro(n, lambda n=n: D.strip_bad_utf(n)),
        "demojibake": puro(n, lambda n=n: D.demojibake(n)),
    }
saida["cm"] = {str(c): puro(c, lambda c=c: D.get_relationships_by_cm(c))
               for c in [0, -1, 6, 7, 100, 350, 1000, 3720, 99999]}
saida["soft_prefix_jaccard"] = puro(
    None, lambda: [D.soft_prefix_jaccard({"silva"}, {"silva"}), 
                   D.soft_prefix_jaccard({"sil"}, {"silva"}),
                   D.soft_prefix_jaccard({"silva", "souza"}, {"silva", "lima"})])

def caso(rotulo, csv_path, raiz):
    try:
        r = D.dna_analysis(csv_path, raiz)
        return [json.loads(json.dumps(r[0], ensure_ascii=False, sort_keys=True)),
                json.loads(json.dumps(r[1], ensure_ascii=False, sort_keys=True)), r[2]]
    except Exception as e:
        return ["EXCECAO", type(e).__name__, str(e)]

def corpus(tag, ged, casos):
    fd = os.path.join(ROOT, ".pytest-tmp", "zv52-ensaio-ged-%s.ged" % tag)
    with open(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(ged)
    U.load_gedcom_and_build_graph(fd)
    return {rot: caso(rot, p, raiz) for rot, p, raiz in casos}

saida["fluxo"] = {}
casos1 = []
for nome in sorted(f for f in os.listdir(os.path.join(ROOT, "_reversa_sdd", "parity",
                                                      "fixtures", "dna")) if f.endswith(".csv")):
    casos1.append((nome, os.path.join(ROOT, "_reversa_sdd", "parity", "fixtures", "dna", nome),
                   "Carlos Silva"))
tmp = os.path.join(ROOT, ".pytest-tmp", "zv52-ensaio-csv")
os.makedirs(tmp, exist_ok=True)
for nome, texto in (("DNA_CSV_UTF8", sample_dna.DNA_CSV_UTF8),
                    ("DNA_CSV_DUPLICATED", sample_dna.DNA_CSV_DUPLICATED),
                    ("DNA_CSV_NO_INTERSECTION", sample_dna.DNA_CSV_NO_INTERSECTION)):
    p = os.path.join(tmp, nome + ".csv")
    open(p, "w", encoding="utf-8", newline="").write(texto)
    casos1.append((nome, p, "Carlos Silva"))
p = os.path.join(tmp, "DNA_CSV_LATIN1_RAW.csv")
open(p, "wb").write(sample_dna.DNA_CSV_LATIN1_RAW)
casos1.append(("DNA_CSV_LATIN1_RAW", p, "Carlos Silva"))
saida["fluxo"]["arvore_dos_testes"] = corpus("a", sample_dna.DNA_GED, casos1)

bench_ged = os.path.join(ROOT, ".pytest-tmp", "numt-bench", "bench.ged")
if os.path.exists(bench_ged):
    with open(bench_ged, encoding="utf-8") as fh:
        ged_grande = fh.read()
    casos2 = [(nome, os.path.join(ROOT, ".pytest-tmp", "numt-bench", nome), "Joao Silva Silva")
              for nome in ("bench_300.csv", "bench_1000.csv", "bench_3000.csv")
              if os.path.exists(os.path.join(ROOT, ".pytest-tmp", "numt-bench", nome))]
    if casos2:
        saida["fluxo"]["arvore_grande"] = corpus("b", ged_grande, casos2)

print(json.dumps(saida, ensure_ascii=False, sort_keys=True))
'''


def main() -> int:
    if not os.path.isdir(ESPELHO):
        print("rode gerar_divisao.py primeiro")
        return 2

    shutil.rmtree(ENSAIO, ignore_errors=True)
    shutil.copytree(REAL, os.path.join(ENSAIO, "analisador-genealogico"),
                    ignore=shutil.ignore_patterns("uploads", "__pycache__", "*.pyc"))
    destino = os.path.join(ENSAIO, "analisador-genealogico", "reconstructed")
    for nome in ARQUIVOS:
        shutil.copy2(os.path.join(ESPELHO, "reconstructed", nome),
                     os.path.join(destino, nome))

    runner = os.path.join(ENSAIO, "runner.py")
    with open(runner, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(RUNNER)

    saidas = {}
    for rotulo, pkg in (("real", REAL), ("ensaio", os.path.join(ENSAIO, "analisador-genealogico"))):
        r = subprocess.run([sys.executable, runner, pkg, ROOT], capture_output=True, cwd=ROOT)
        if r.returncode != 0:
            print("runner %s FALHOU:\n%s" % (rotulo, r.stderr.decode()[-3000:]))
            return 1
        saidas[rotulo] = json.loads(r.stdout.decode())

    a, b = saidas["real"], saidas["ensaio"]
    print("ENSAIO DA DIVISAO · real contra pacote espelho")
    print("=" * 78)
    divergencias = []

    sup = {n: (a["superficie"][n], b["superficie"][n]) for n in a["superficie"]}
    faltam = [n for n, (x, y) in sup.items() if x != y]
    print("superficie de compatibilidade : %d nomes, %d divergentes%s"
          % (len(sup), len(faltam), (" -> " + ", ".join(faltam)) if faltam else ""))
    if faltam:
        divergencias.append("superficie")

    if a["puras"] != b["puras"]:
        for amostra in a["puras"]:
            if a["puras"][amostra] != b["puras"][amostra]:
                for chave in a["puras"][amostra]:
                    if a["puras"][amostra][chave] != b["puras"][amostra][chave]:
                        divergencias.append("pura %s(%r)" % (chave, amostra))
    print("funcoes puras                 : %d amostras x 9 funcoes, %s"
          % (len(a["puras"]), "identicas" if a["puras"] == b["puras"] else "DIVERGEM"))

    print("faixas de cM                  : %s"
          % ("identicas" if a["cm"] == b["cm"] else "DIVERGEM"))
    if a["cm"] != b["cm"]:
        divergencias.append("cm")
    print("soft_prefix_jaccard           : %s"
          % ("identico" if a["soft_prefix_jaccard"] == b["soft_prefix_jaccard"] else "DIVERGE"))
    if a["soft_prefix_jaccard"] != b["soft_prefix_jaccard"]:
        divergencias.append("jaccard")

    for grupo in sorted(a["fluxo"]):
        ca, cb = a["fluxo"][grupo], b["fluxo"][grupo]
        ruins = [k for k in ca if ca[k] != cb.get(k)]
        print("fluxo completo (%s)  : %d casos, %d divergentes%s"
              % (grupo, len(ca), len(ruins), (" -> " + ", ".join(ruins)) if ruins else ""))
        for k in ruins:
            divergencias.append("fluxo %s/%s" % (grupo, k))
            print("    real   : %s" % json.dumps(ca[k], ensure_ascii=False)[:300])
            print("    ensaio : %s" % json.dumps(cb.get(k), ensure_ascii=False)[:300])

    print("=" * 78)
    print("VEREDITO: %s" % ("EQUIVALENTE" if not divergencias else
                            "%d DIVERGENCIA(S): %s" % (len(divergencias), divergencias)))
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensaio-divisao.txt")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("ENSAIO DA DIVISAO · real contra pacote espelho\n")
        fh.write("superficie: %d nomes, %d divergentes\n" % (len(sup), len(faltam)))
        fh.write("puras: %s\n" % ("identicas" if a["puras"] == b["puras"] else "DIVERGEM"))
        fh.write("cm: %s\n" % ("identicas" if a["cm"] == b["cm"] else "DIVERGEM"))
        for grupo in sorted(a["fluxo"]):
            ca, cb = a["fluxo"][grupo], b["fluxo"][grupo]
            fh.write("fluxo %s: %d casos, %d divergentes\n"
                     % (grupo, len(ca), len([k for k in ca if ca[k] != cb.get(k)])))
        fh.write("VEREDITO: %s\n" % ("EQUIVALENTE" if not divergencias else str(divergencias)))
        for grupo in sorted(a["fluxo"]):
            for k in sorted(a["fluxo"][grupo]):
                fh.write("  %s %s = %s\n" % (grupo, k,
                                             json.dumps(a["fluxo"][grupo][k], ensure_ascii=False)))
    return 1 if divergencias else 0


if __name__ == "__main__":
    raise SystemExit(main())
