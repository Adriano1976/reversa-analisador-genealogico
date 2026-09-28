"""Preenche `present`/`sha256`/`captureBy`/`capturedAt` no manifest.yaml dos goldens.

## Por que edicao por linhas e nao yaml.safe_load + dump

O manifesto e um documento com COMENTARIOS que carregam informacao que nao existe em
lugar nenhum (a correcao do oracleCommand, a ordem recomendada de captura, as notas de
DEV-010). `yaml.dump` os apagaria todos. Entao este script reescreve APENAS as quatro
chaves de estado, dentro do bloco de cada tela, preservando todo o resto byte a byte.

## Entrada

Le `.golden-capture/capturas.json` (gerado por `_golden_capture.py`), que mapeia o
NOME DO ARQUIVO capturado -> status/sha256/bytes.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MANIFEST = os.path.join(ROOT, "_reversa_sdd", "screens", "golden", "manifest.yaml")
CAPTURAS = os.path.join(ROOT, ".golden-capture", "capturas.json")
CAPTURED_BY = "orchestrator (_reversa_sdd/parity/_golden_capture.py)"
CAPTURED_AT = "2026-09-28T16:20:00Z"


def main() -> int:
    if not os.path.exists(CAPTURAS):
        print("ERRO: %s nao existe — rode _golden_capture.py antes." % CAPTURAS)
        return 1
    caps = {c["name"]: c for c in json.load(open(CAPTURAS, encoding="utf-8"))}
    linhas = open(MANIFEST, encoding="utf-8").read().split("\n")

    # Localiza os blocos de tela: `  - name: <NOME>` define o inicio de cada um.
    inicios = [(i, m.group(1)) for i, l in enumerate(linhas)
               if (m := re.match(r"^  - name:\s*(\S+)", l))]
    if not inicios:
        print("ERRO: nenhum bloco `  - name:` encontrado no manifesto.")
        return 1

    limites = [(nome, ini, inicios[k + 1][0] if k + 1 < len(inicios) else len(linhas))
               for k, (ini, nome) in enumerate(inicios)]

    preenchidas, mantidas = [], []
    for nome, ini, fim in limites:
        arquivo = None
        for i in range(ini, fim):
            m = re.match(r"^    file:\s*\"?([^\"]+?)\"?\s*$", linhas[i])
            if m:
                arquivo = m.group(1)
                break
        cap = caps.get(arquivo) if arquivo else None
        if not cap:
            mantidas.append((nome, arquivo))
            continue
        # Reescreve apenas as quatro chaves de estado dentro deste bloco.
        for i in range(ini, fim):
            if re.match(r"^    present:", linhas[i]):
                linhas[i] = "    present: true"
            elif re.match(r"^    captureBy:", linhas[i]):
                linhas[i] = '    captureBy: "%s"' % CAPTURED_BY
            elif re.match(r"^    capturedAt:", linhas[i]):
                linhas[i] = '    capturedAt: "%s"' % CAPTURED_AT
            elif re.match(r"^    sha256:", linhas[i]):
                linhas[i] = '    sha256: "%s"' % cap["sha256"]
        preenchidas.append((nome, arquivo, cap["sha256"][:16], cap["bytes"]))

    # Atualiza o bloco de observacoes sobre o conjunto, que afirmava "NENHUM golden".
    txt = "\n".join(linhas)
    txt = txt.replace(
        "    NENHUM golden file foi capturado nesta execucao. Todos estao com `present: false`.",
        "    CAPTURA PARCIAL REALIZADA em 2026-09-28T16:20Z por "
        "_reversa_sdd/parity/_golden_capture.py (oraculo isolado em .golden-capture/app/,\n"
        "    legado real intocado). Capturados: SCR-001, SCR-G02, SCR-002, SCR-003, SCR-004.\n"
        "    PENDENTES: SCR-005 (exige CSV de matches + nome de raiz) e SCR-G03 (exige\n"
        "    navegador headless — DEV-010). Os pendentes seguem com `present: false`.")
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)

    print("=" * 74)
    print("MANIFEST ATUALIZADO — %s" % os.path.relpath(MANIFEST, ROOT))
    print("=" * 74)
    for nome, arq, h, b in preenchidas:
        print("  present: true   %-34s %7d bytes  %s" % (nome, b, h))
    if mantidas:
        print()
        print("  AINDA present: false (sem captura):")
        for nome, arq in mantidas:
            print("    %-34s (%s)" % (nome, arq))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
