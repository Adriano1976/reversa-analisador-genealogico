"""Mede o custo de import de cada fronteira, ANTES da divisao.

A promessa da OPP-20260929-ZV52 e "cada responsabilidade testavel isoladamente".
O jeito de medir isso e o custo de importar so a parte que interessa: hoje,
testar `norm_name` exige importar `dna_analysis`, que arrasta pandas, thefuzz,
networkx (via path_search) e ged4py (via upload).

Cada alvo roda em um processo NOVO, para que a medicao nao seja contaminada pelo
que ja esta em `sys.modules`.

Uso:
    python <este script>
"""

from __future__ import annotations

import os
import statistics
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
REPS = 5

ALVOS = [
    ("reconstructed.dna_analysis", "tudo (hoje, para chegar em norm_name)"),
    ("reconstructed.name_normalization", "NOVO: normalizacao e vocabulario"),
    ("reconstructed.csv_ingest", "NOVO: leitura e agregacao do CSV"),
    ("reconstructed.matching", "NOVO: indices e matching"),
    ("reconstructed.domain", "so a limpeza de texto + vocabulario"),
    ("reconstructed.upload", "ged4py + networkx"),
    ("reconstructed.path_search", "networkx + render"),
    ("pandas", "so pandas (o que csv_ingest vai precisar)"),
    ("thefuzz", "so thefuzz (o que matching vai precisar)"),
    ("networkx", "so networkx"),
    ("ged4py.parser", "so ged4py"),
]

CODIGO = (
    "import sys, time\n"
    "sys.path.insert(0, 'analisador-genealogico')\n"
    "t = time.perf_counter()\n"
    "import {alvo}\n"
    "dt = (time.perf_counter() - t) * 1000.0\n"
    "caros = [m for m in sys.modules if m.split('.')[0] in "
    "('pandas', 'thefuzz', 'networkx', 'ged4py', 'numpy', 'rapidfuzz', 'Levenshtein')]\n"
    "print(len(sys.modules), '%.2f' % dt, "
    "','.join(sorted(set(m.split('.')[0] for m in caros))) or '-')\n"
)


def main() -> int:
    print("CUSTO DE IMPORT POR FRONTEIRA (processo novo por medicao, minimo de %d)" % REPS)
    print("=" * 78)
    print("%-30s %10s %12s  %s" % ("alvo", "modulos", "ms", "dependencias caras"))
    for alvo, rotulo in ALVOS:
        amostras = []
        modulos = deps = None
        for _ in range(REPS):
            r = subprocess.run([sys.executable, "-c", CODIGO.format(alvo=alvo)],
                               capture_output=True, cwd=ROOT)
            if r.returncode != 0:
                print("%-30s FALHOU: %s" % (alvo, r.stderr.decode()[-200:]))
                break
            n, ms, d = r.stdout.decode().strip().split(" ", 2)
            modulos, deps = int(n), d
            amostras.append(float(ms))
        else:
            print("%-30s %10d %12.2f  %s" % (alvo, modulos, min(amostras), deps or "-"))
    print("=" * 78)
    print("Leitura: quanto menor a coluna de dependencias caras, mais barato testar")
    print("aquela fronteira isoladamente. 'dna_analysis' puxa todas elas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
