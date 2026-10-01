"""Prova de equivalencia antes e depois, pelo FLUXO COMPLETO.

Carrega a versao ANTERIOR de `dna_analysis.py` direto do git (HEAD), ao lado da
versao atual, e roda as duas sobre o mesmo corpus comparando o resultado inteiro:
lista de conexoes, descartados e mensagem.

Nao compara `aggregate_matches` isolado. Roda `dna_analysis`, que e o que o
usuario aciona, e cuja saida depende da chave de agrupamento que a otimizacao
reescreveu.

Uso:
    python <este script>
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
SCRATCH = os.path.join(ROOT, ".pytest-tmp", "numt-after")
FIXTURES = os.path.join(ROOT, "_reversa_sdd", "parity", "fixtures", "dna")
BENCH = os.path.join(ROOT, ".pytest-tmp", "numt-bench")
REL = "analisador-genealogico/reconstructed/dna_analysis.py"

sys.path.insert(0, os.path.join(ROOT, "analisador-genealogico"))


def carregar_antigo():
    """Extrai a versao de HEAD para um arquivo e a importa dentro do pacote."""
    os.makedirs(SCRATCH, exist_ok=True)
    src = subprocess.run(["git", "show", "HEAD:" + REL], cwd=ROOT,
                         capture_output=True).stdout.decode("utf-8")
    destino = os.path.join(SCRATCH, "_old_dna_analysis.py")
    with open(destino, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    nome = "reconstructed._old_dna_analysis"
    spec = importlib.util.spec_from_file_location(nome, destino)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "reconstructed"
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod, len(src.splitlines())


def rodar(mod, csv_path, raiz):
    try:
        return ("ok",) + tuple(mod.dna_analysis(csv_path, raiz))
    except Exception as e:
        return ("excecao", type(e).__name__, str(e))


def comparar_corpus(antigo, atual, rotulos, titulo, saida):
    saida.append("")
    saida.append("### " + titulo)
    iguais = divergentes = 0
    for rotulo, csv_path, raiz in rotulos:
        a = rodar(antigo, csv_path, raiz)
        b = rodar(atual, csv_path, raiz)
        if a == b:
            iguais += 1
            detalhe = ("%d conexoes" % len(a[1])) if a[0] == "ok" else ("%s" % a[1])
            if a[0] == "ok":
                cms = [r.get("cm") for r in a[1]]
                detalhe = "%d conexoes%s, %d descartados" % (
                    len(a[1]), (" cm=%s" % cms) if cms else "", len(a[2]))
            saida.append("  %-46s identico   %s" % (rotulo, detalhe))
        else:
            divergentes += 1
            saida.append("  %-46s DIVERGE" % rotulo)
            saida.append("      antes: %r" % (a,))
            saida.append("      depois: %r" % (b,))
    saida.append("  -> %d identicos, %d divergentes" % (iguais, divergentes))
    return divergentes


def main() -> int:
    from reconstructed import dna_analysis as atual
    from reconstructed import upload as U

    antigo, n_linhas = carregar_antigo()
    saida = []
    saida.append("Prova de equivalencia antes e depois · OPP-20260929-NUMT")
    saida.append("Versao anterior carregada de HEAD: %d linhas" % n_linhas)
    saida.append("Versao atual em disco")
    saida.append("Comparacao pelo fluxo completo `dna_analysis(csv, raiz)`")

    # --- passada 1: fixtures de DNA sobre a arvore sintetica dos testes ---------
    sys.path.insert(0, os.path.join(ROOT, "tests", "fixtures"))
    import sample_dna
    ged = os.path.join(SCRATCH, "sample.ged")
    with open(ged, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sample_dna.DNA_GED)
    U.load_gedcom_and_build_graph(ged)
    saida.append("")
    saida.append("Arvore: %d pessoas (tests/fixtures/sample_dna.py)" % len(U.people))

    rotulos = []
    for nome in sorted(f for f in os.listdir(FIXTURES) if f.endswith(".csv")):
        rotulos.append((nome, os.path.join(FIXTURES, nome), "Carlos Silva"))
    divergentes = comparar_corpus(antigo, atual, rotulos, "Fixtures de DNA (arvore dos testes)", saida)

    # --- passada 1b: os CSVs do proprio teste de caracterizacao ---------------
    # As fixtures do harness de paridade usam "Ana Silva", cujo unico token
    # nao-generico e o sobrenome. Esse e o achado caracterizado e deliberadamente
    # nao corrigido documentado no topo de tests/test_characterization_matching.py:
    # `split_name_pt` le o sobrenome como prenome, o pool fica vazio e a linha e
    # descartada. Por isso aquelas fixtures nao exercitam a ACEITACAO.
    # Estes CSVs usam "Ana Silva Souza" e produzem o cm somado de 537.
    casos = [("DNA_CSV_UTF8", sample_dna.DNA_CSV_UTF8, "w"),
             ("DNA_CSV_DUPLICATED", sample_dna.DNA_CSV_DUPLICATED, "w"),
             ("DNA_CSV_NO_INTERSECTION", sample_dna.DNA_CSV_NO_INTERSECTION, "w")]
    rotulos = []
    for nome, texto, modo in casos:
        p = os.path.join(SCRATCH, nome + ".csv")
        with open(p, modo, encoding="utf-8", newline="") as fh:
            fh.write(texto)
        rotulos.append((nome, p, "Carlos Silva"))
    p = os.path.join(SCRATCH, "DNA_CSV_LATIN1_RAW.csv")
    with open(p, "wb") as fh:
        fh.write(sample_dna.DNA_CSV_LATIN1_RAW)
    rotulos.append(("DNA_CSV_LATIN1_RAW (bytes latin-1)", p, "Carlos Silva"))
    divergentes += comparar_corpus(antigo, atual, rotulos,
                                   "CSVs do teste de caracterizacao (caminho de ACEITACAO)",
                                   saida)

    # --- passada 2: corpus grande sobre a arvore sintetica do benchmark ---------
    ged_big = os.path.join(BENCH, "bench.ged")
    if os.path.exists(ged_big):
        U.load_gedcom_and_build_graph(ged_big)
        saida.append("")
        saida.append("Arvore: %d pessoas (%s)" % (len(U.people), os.path.relpath(ged_big, ROOT)))
        rotulos = []
        for n in (300, 1000, 3000):
            p = os.path.join(BENCH, "bench_%d.csv" % n)
            if os.path.exists(p):
                rotulos.append(("bench_%d.csv" % n, p, "Joao Silva Silva"))
        if rotulos:
            divergentes += comparar_corpus(antigo, atual, rotulos,
                                           "Corpus sintetico do benchmark", saida)
    else:
        saida.append("")
        saida.append("### Corpus sintetico do benchmark")
        saida.append("  pulado: %s nao existe (rode bench_ingest.py antes)" % ged_big)

    saida.append("")
    saida.append("### VEREDITO: %s"
                 % ("EQUIVALENTE em todo o corpus" if divergentes == 0
                    else "%d DIVERGENCIA(S)" % divergentes))

    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "equivalencia-antes-depois.txt")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(saida) + "\n")
    print("\n".join(saida))
    return 1 if divergentes else 0


if __name__ == "__main__":
    raise SystemExit(main())
