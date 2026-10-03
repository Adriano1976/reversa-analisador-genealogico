"""Roda o COLETOR REAL do oraculo (codigo identico ao do harness) com cronometro
por fase, para achar a fase que o profile anterior nao mediu.

Descoberta que motivou isto: o profile previu ~36s para um coletor completo, mas a
execucao real passou de 329s de CPU. Logo ha uma fase nao medida.

NAO duplica o codigo a mao: extrai ORACLE_COLLECTOR do proprio harness.py e injeta
os cronometros, para que o que se mede seja EXATAMENTE o que o harness executa.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def load_collector():
    """Extrai ORACLE_COLLECTOR de harness.py — fonte unica da verdade."""
    sys.path.insert(0, HERE)
    import harness  # noqa
    return harness.ORACLE_COLLECTOR


def instrumentar(src: str) -> str:
    """Insere cronometro antes/depois de cada bloco `obs["..."] = ...`."""
    linhas = src.split("\n")
    out = ["import time as _t", "_T0 = _t.perf_counter()", ""]
    for ln in linhas:
        m = re.match(r'^(obs\["(\w+)"\]) = ', ln)
        if m:
            fase = m.group(2)
            out.append(
                'print("   %-24s %7.2fs" % ("' + fase + ' (inicio)", _t.perf_counter() - _T0), flush=True)'
            )
        out.append(ln)
    # cronometro final
    out.append('print("   %-24s %7.2fs" % ("TOTAL", _t.perf_counter() - _T0), flush=True)')
    return "\n".join(out)


def main() -> int:
    ged = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "src", "uploads", "Arvore_Unificada_Oficial_V1_2.ged")
    src = instrumentar(load_collector())
    runner = os.path.join(HERE, "_instrumented_oracle.py")
    with open(runner, "w", encoding="utf-8") as fh:
        fh.write(src)
    out = os.path.join(HERE, "_obs_instrumented.json")
    cm = "[0, 50, 350, 2200, 3400]"
    print("=" * 78)
    print("COLETOR DO ORACULO INSTRUMENTADO — %s" % os.path.basename(ged))
    print("amostra de pares = %s" % os.environ.get("PARITY_SAMPLE", "40"))
    print("=" * 78, flush=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PARITY_SAMPLE=os.environ.get("PARITY_SAMPLE", "8"))
    rc = subprocess.call([sys.executable, runner, ROOT, ged, out, cm], env=env)
    print("=" * 78)
    print("exit=%d" % rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
