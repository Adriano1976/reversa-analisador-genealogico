"""Mede o custo de import de cada fronteira, antes da divisao da path_search.

Diferente da ZV52, aqui a suspeita e que o ganho de import seja PEQUENO: todo
bloco de `path_search.py` depende de `.upload`, que arrasta ged4py e networkx, e
o que domina o custo e o `.upload`, nao o modulo em si. Esta medicao existe para
confirmar ou derrubar essa suspeita, em vez de presumi-la.

Cada alvo roda em um processo NOVO.

Uso:
    python <este script>
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
REPS = 5

ALVOS = [
    ("reconstructed.path_search", "tudo (busca + render + handler)"),
    ("reconstructed.upload", "ged4py + networkx (todos os blocos dependem)"),
    ("reconstructed.domain", "piso: sem dependencia pesada"),
    ("networkx", "so networkx"),
    ("ged4py.parser", "so ged4py"),
    ("unicodedata", "so unicodedata (o render precisa)"),
    ("re", "so re (o render precisa)"),
    ("collections", "so collections (a busca precisa)"),
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
    print("CUSTO DE IMPORT POR FRONTEIRA (processo novo, minimo de %d)" % REPS)
    print("=" * 78)
    print("%-30s %10s %12s  %s" % ("alvo", "modulos", "ms", "dependencias caras"))
    for alvo, _ in ALVOS:
        amostras, modulos, deps = [], None, None
        for _ in range(REPS):
            r = subprocess.run([sys.executable, "-c", CODIGO.format(alvo=alvo)],
                               capture_output=True, cwd=ROOT)
            if r.returncode != 0:
                print("%-30s FALHOU: %s" % (alvo, r.stderr.decode()[-160:]))
                break
            n, ms, d = r.stdout.decode().strip().split(" ", 2)
            modulos, deps = int(n), d
            amostras.append(float(ms))
        else:
            print("%-30s %10d %12.2f  %s" % (alvo, modulos, min(amostras), deps or "-"))
    print("=" * 78)
    print("Leitura: o que decide o custo aqui e o `.upload`. Se `path_search` e")
    print("`upload` medirem quase o mesmo, entao separar os blocos NAO reduz import,")
    print("e o ganho da transformacao e de coesao, nao de tempo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
