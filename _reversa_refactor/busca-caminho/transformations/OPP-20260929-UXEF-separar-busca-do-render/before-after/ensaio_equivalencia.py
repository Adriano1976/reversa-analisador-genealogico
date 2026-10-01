"""Ensaio da divisao da path_search: pacote espelho contra o real.

NAO toca na arvore legada. Copia `analisador-genealogico/` para
`.pytest-tmp/uxef-ensaio/`, sobrepoe os 4 arquivos gerados por `gerar_divisao.py`,
e roda o MESMO runner em dois processos: um contra o pacote real, outro contra o
espelho.

O runner compara:
  - a superficie de compatibilidade (18 nomes) e o padrao da lista branca
  - o inventario de nomes publicos que somem do modulo (prova do confinamento)
  - a navegacao familiar e os dois algoritmos de busca, para todos os pares de id
  - o fluxo `path_search` ponta a ponta, com os pares do proprio teste
  - o rotulo, com amostras hostis

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
ESPELHO = os.path.join(ROOT, ".pytest-tmp", "uxef-proposta", "analisador-genealogico")
ENSAIO = os.path.join(ROOT, ".pytest-tmp", "uxef-ensaio")
REAL = os.path.join(ROOT, "analisador-genealogico")
BENCH = os.path.join(ROOT, ".pytest-tmp", "numt-bench", "bench.ged")
ARQUIVOS = ["family_navigation.py", "path_finding.py", "mermaid_render.py", "path_search.py"]

RUNNER = r'''
import json, os, sys

PKG = sys.argv[1]
ROOT = sys.argv[2]
sys.path.insert(0, PKG)
sys.path.insert(0, os.path.join(ROOT, "tests", "fixtures"))

import sample_gedcom
from reconstructed import upload as U
from reconstructed import path_search as P

API = ["path_search", "find_person_by_name", "find_ancestral_path", "find_indirect_path",
       "get_parents", "get_spouses", "are_spouses", "split_path_by_marriage",
       "pick_spouse_for_couple", "exclude_tail", "_mermaid_sid", "_mermaid_label",
       "_LABEL_SEGURO", "generate_mermaid_graph", "generate_mermaid_graph_indirect_bridge",
       "MAX_DEPTH", "MAX_HOPS", "ref_id"]

saida = {}
saida["superficie"] = {n: hasattr(P, n) for n in API}
saida["publicos"] = sorted(n for n in dir(P) if not n.startswith("_"))
saida["constantes"] = {"MAX_DEPTH": int(P.MAX_DEPTH), "MAX_HOPS": int(P.MAX_HOPS),
                       "branca": P._LABEL_SEGURO.pattern}

fd = os.path.join(ROOT, ".pytest-tmp", "uxef-ensaio-sample.ged")
with open(fd, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(sample_gedcom.SAMPLE_GED)
U.load_gedcom_and_build_graph(fd)

IDS = ["@I1@", "@I2@", "@I3@", "@I4@", "@I5@", "@I6@", "@I9@"]

def j(v):
    if isinstance(v, (set, frozenset)):
        return sorted(v)
    if isinstance(v, tuple):
        return [j(x) for x in v]
    if isinstance(v, list):
        return [j(x) for x in v]
    return v

saida["navegacao"] = {}
for i in IDS:
    saida["navegacao"][i] = {
        "no_grafo": i in U.people,
        "nome": U.get_name(U.people[i]) if i in U.people else None,
        "pais": j(P.get_parents(i)),
        "conjuges": j(P.get_spouses(i)),
    }
saida["conjuge_de"] = {a + "|" + b: P.are_spouses(a, b) for a in IDS for b in IDS if a != b}
saida["casamento"] = {i: j(P.split_path_by_marriage([i, "@I3@", "@I4@"])) for i in IDS}
saida["escolha_conjuge"] = {i: P.pick_spouse_for_couple(i) for i in IDS}
saida["pessoa_por_nome"] = {n: P.find_person_by_name(n) for n in
    ["Carlos Silva", "Ana Silva", "Bia Oliveira", "Lone Ranger", "Zzz Ninguem",
     "Silva", "silva", "", "  Carlos  Silva  "]}
saida["ancestral"] = {}
saida["indireto"] = {}
for a in IDS:
    for b in IDS:
        saida["ancestral"][a + "|" + b] = j(P.find_ancestral_path(a, b))
        saida["indireto"][a + "|" + b] = j(P.find_indirect_path(a, b))

AMOSTRAS = ["Ana Silva", "", "  ", "Joao", "Silva Souza", "A" * 40, "Nao-Existe X"]
saida["sid"] = {n: P._mermaid_sid(n) for n in AMOSTRAS}
HOSTIS = ['aspas " duplas', "crase ` no meio", "colchete ] e [", "quebra\nde linha",
          "emoji \U0001F600", "acentos ção õ", "barra \\ e barra /", "dois: pontos",
          "palavra-chave end", "> e < e &", "tab\tinterna"]
saida["label"] = {n: P._mermaid_label(n) for n in HOSTIS}

PARES = [("Carlos Silva", "Ana Silva"), ("Carlos Silva", "Bia Oliveira"),
         ("Zzz Ninguem", "Carlos Silva"), ("Carlos Silva", "Zzz Ninguem"),
         ("Carlos Silva", "Lone Ranger"), ("Carlos Silva", "Carlos Silva"),
         ("Ana Silva", "Bia Oliveira"), ("Diego Silva", "Joao Silva")]
saida["fluxo"] = {}
for n1, n2 in PARES:
    try:
        r, m, s = P.path_search(n1, n2)
        saida["fluxo"][n1 + "|" + n2] = [json.loads(json.dumps(r, ensure_ascii=False, sort_keys=True)), m, s]
    except Exception as e:
        saida["fluxo"][n1 + "|" + n2] = ["EXCECAO", type(e).__name__, str(e)]

bench = os.path.join(ROOT, ".pytest-tmp", "numt-bench", "bench.ged")
if os.path.exists(bench):
    U.load_gedcom_and_build_graph(bench)
    ids = sorted(U.people)
    if len(ids) >= 6:
        saida["fluxo_grande"] = {}
        for k in range(3):
            a, b = ids[k], ids[-1 - k]
            try:
                r, m, s = P.path_search(U.get_name(U.people[a]), U.get_name(U.people[b]))
                saida["fluxo_grande"][a + "|" + b] = [
                    len(r["mermaid_data"]) if r else None, m, s]
            except Exception as e:
                saida["fluxo_grande"][a + "|" + b] = ["EXCECAO", type(e).__name__]

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
    linhas = ["ENSAIO DA DIVISAO DA path_search · real contra pacote espelho",
              "=" * 78]
    divergencias = []

    faltam = [n for n, ok in a["superficie"].items() if ok != b["superficie"][n]]
    linhas.append("superficie de compatibilidade : %d nomes, %d divergentes%s"
                  % (len(a["superficie"]), len(faltam), (" -> " + ", ".join(faltam)) if faltam else ""))
    if faltam:
        divergencias.append("superficie")

    sumiram = sorted(set(a["publicos"]) - set(b["publicos"]))
    surgiram = sorted(set(b["publicos"]) - set(a["publicos"]))
    linhas.append("nomes publicos que somem     : %s" % (", ".join(sumiram) or "nenhum"))
    linhas.append("nomes publicos que surgem    : %s" % (", ".join(surgiram) or "nenhum"))

    # A lista de chaves e a INTERSECAO do que os dois lados produziram, e nao uma
    # lista fixa escrita aqui. Uma versao anterior tinha lista fixa e deixou de
    # comparar o `fluxo_grande` sem avisar: o ensaio passava sem ter comparado.
    chaves = [k for k in sorted(set(a) & set(b)) if k not in ("superficie", "publicos")]
    so_um_lado = sorted((set(a) ^ set(b)) - {"superficie", "publicos"})
    if so_um_lado:
        linhas.append("chaves em so um lado        : %s" % ", ".join(so_um_lado))
        divergencias.append("chaves assimetricas")

    for chave in chaves:
        if a[chave] != b[chave]:
            ruins = [k for k in a[chave] if a[chave][k] != b[chave].get(k)]
            linhas.append("%-29s : DIVERGE em %s" % (chave, ", ".join(map(str, ruins))[:200]))
            divergencias.append(chave)
            for k in ruins[:3]:
                linhas.append("    real   : %s" % json.dumps(a[chave][k], ensure_ascii=False)[:220])
                linhas.append("    ensaio : %s" % json.dumps(b[chave].get(k), ensure_ascii=False)[:220])
        else:
            n = len(a[chave]) if isinstance(a[chave], dict) else "-"
            linhas.append("%-29s : identico (%s)" % (chave, n))

    linhas.append("=" * 78)
    linhas.append("VEREDITO: %s" % ("EQUIVALENTE" if not divergencias
                                    else "%d DIVERGENCIA(S): %s" % (len(divergencias), divergencias)))
    texto = "\n".join(linhas)
    print(texto)
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensaio-divisao.txt")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto + "\n")
    return 1 if divergencias else 0


if __name__ == "__main__":
    raise SystemExit(main())
