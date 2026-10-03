"""Conta as referencias vivas ao modulo `domain` antes e depois da LMAY.

Varre apenas os arquivos que importam ou citam o modulo:
    src/**.py, tests/**.py, _reversa_sdd/parity/*.py, README.md

Fica de fora, de proposito:
    - `_reversa_sdd/domain.md`, que e uma spec e nao o modulo
    - residuo gerado pelo harness (`_collect_*.py`, `_obs_*.json`)
    - `__pycache__`
    - `_reversa_refactor/**`, que e evidencia historica e nao deve ser reescrita

Uso:
    py -3.14 medir-referencias.py --rotulo antes
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

PADROES = [
    ("import do pacote", re.compile(r"reconstructed\.domain\b")),
    ("import relativo", re.compile(r"from\s+\.domain\s+import")),
    ("import do pacote pelo nome", re.compile(r"from\s+reconstructed\s+import\s+domain\b")),
    ("citacao de arquivo", re.compile(r"\bdomain\.py\b")),
    ("citacao de simbolo", re.compile(r"\bdomain\.(strip_bad_utf|demojibake)\b")),
]

IGNORAR_ARQUIVOS = {"_collect_oracle.py", "_collect_cand.py", "_obs_oracle.json", "_obs_cand.json"}


def arquivos():
    for sub in ("src", "tests", os.path.join("_reversa_sdd", "parity")):
        base = os.path.join(ROOT, sub)
        for raiz, dirs, nomes in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for nome in sorted(nomes):
                if nome in IGNORAR_ARQUIVOS:
                    continue
                if nome.endswith(".py") or nome.endswith(".md"):
                    yield os.path.relpath(os.path.join(raiz, nome), ROOT).replace("\\", "/")
    yield "README.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rotulo", default="atual")
    args = ap.parse_args()

    total = 0
    por_tipo = {}
    linhas = []

    for rel in sorted(set(arquivos())):
        caminho = os.path.join(ROOT, rel)
        if not os.path.exists(caminho):
            continue
        with open(caminho, encoding="utf-8") as fh:
            for n, linha in enumerate(fh, 1):
                for tipo, padrao in PADROES:
                    if padrao.search(linha):
                        total += 1
                        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
                        linhas.append("  %-52s %4d  %-26s %s" % (rel, n, tipo, linha.strip()[:60]))
                        break

    saida = []
    saida.append("=" * 100)
    saida.append("REFERENCIAS VIVAS AO MODULO `domain` (medido por varredura, nao estimado)")
    saida.append("=" * 100)
    saida.append("total: %d" % total)
    for tipo, n in sorted(por_tipo.items()):
        saida.append("  %-30s %d" % (tipo, n))
    saida.append("")
    saida.extend(linhas if linhas else ["  (nenhuma referencia viva)"])
    saida.append("=" * 100)
    texto = "\n".join(saida)

    destino = os.path.join(HERE, "before-after", "referencias-%s.txt" % args.rotulo)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")
    # O console do Windows e cp1252 e as linhas do README tem caractere de
    # desenho de caixa. O arquivo ja esta gravado em UTF-8 antes daqui.
    sys.stdout.reconfigure(errors="replace")
    print(texto)
    print("\ngravado em %s" % os.path.relpath(destino, ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
