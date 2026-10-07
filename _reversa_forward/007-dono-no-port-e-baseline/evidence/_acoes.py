"""Instrumento da rodada de `/reversa-coding` da feature 007.

Duas operacoes, as duas idempotentes e as duas restritas a esta feature:

    python _acoes.py marcar T001 T002 T003
        Troca `[ ]` por `[X]` APENAS no checkbox do fim da linha de acao daquele
        ID. Existe porque a linha de acao e longa (algumas passam de 500
        caracteres) e uma substituicao por correspondencia literal do texto
        inteiro seria fragil e ruidosa. O casamento e por ID na primeira celula.

    python _acoes.py progresso <arquivo.json>
        Anexa ao `progress.jsonl` uma linha compacta por objeto da lista JSON
        recebida. **Append-only:** o arquivo e aberto em modo `a`, entao linha
        anterior nunca e reescrita.

Este arquivo e instrumento de execucao, e nao entrega da feature. Ele fica em
`evidence/` pelo mesmo motivo que o `_t020_varredura.py` da feature 006 ficou: a
medicao precisa ser reproduzivel por quem ler depois.
"""
from __future__ import annotations

import json
import os
import re
import sys

FEATURE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTIONS = os.path.join(FEATURE, "actions.md")
PROGRESS = os.path.join(FEATURE, "progress.jsonl")


def marcar(ids: list[str]) -> int:
    with open(ACTIONS, encoding="utf-8", newline="") as arquivo:
        texto = arquivo.read()
    falhas = 0
    for acao in ids:
        padrao = re.compile(r"^(\| " + re.escape(acao) + r" \|.*?)`\[ \]` \|$", re.M)
        texto, quantos = padrao.subn(r"\1`[X]` |", texto)
        if quantos != 1:
            print(f"  {acao}: ESPERADO 1 substituicao, obtido {quantos}")
            falhas += 1
        else:
            print(f"  {acao}: [X]")
    with open(ACTIONS, "w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(texto)
    return falhas


def progresso(caminho: str) -> int:
    with open(caminho, encoding="utf-8") as arquivo:
        linhas = json.load(arquivo)
    with open(PROGRESS, "a", encoding="utf-8", newline="\n") as arquivo:
        for linha in linhas:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")
            print(f"  {linha['action']}: {linha['status']}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("marcar", "progresso"):
        raise SystemExit(__doc__)
    if sys.argv[1] == "marcar":
        raise SystemExit(marcar(sys.argv[2:]))
    raise SystemExit(progresso(sys.argv[2]))
