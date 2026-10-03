"""Registra os CHG-*.diff da OPP-20261003-FLAT, um por lote.

Estado "antes":

- para os arquivos de `src/`, a copia congelada em `before-after/src-antes/`, tirada
  antes do achatamento, com o nivel `reconstructed/` ainda no lugar;
- para os demais, o inverso exato das transformacoes deste script, mais o `HEAD` para
  o `README.md`, o `pyrefly.toml` e o `regression-watch.md`, que nao foram tocados por
  nenhuma transformacao anterior nao commitada.

As tabelas de movimentacao e de edicao vem de `reorganizar.py`.
"""
from __future__ import annotations

import difflib
import os
import re

from reorganizar import (ESPERADO_1, ESPERADO_2, PROSA, REGRA_1, REGRA_2, ROOT,
                         SUBPACOTES, W001_ANTES, W001_DEPOIS, le)

HERE = os.path.dirname(os.path.abspath(__file__))
ANTES = os.path.join(HERE, "before-after", "src-antes")
HEAD = os.path.join(HERE, "before-after", "head")

LOTES = [
    ("CHG-001-movimentacao.diff", None),
    ("CHG-002-relativo-vira-absoluto.diff", [r.replace("src/reconstructed/", "src/", 1) for r in REGRA_1]),
    ("CHG-003-prefixo-sai-do-import.diff", REGRA_2),
    ("CHG-004-prosa-e-readme.diff", [p for p, _ in PROSA]),
    ("CHG-005-watch-w001.diff", ["_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md"]),
]


def inverso(rel, pares):
    candidatos = [rel, rel.replace("src/", "src/reconstructed/", 1)]
    for c in candidatos:
        caminho = os.path.join(ROOT, c)
        if not os.path.exists(caminho):
            continue
        texto = le(caminho)
        for antes, depois in pares:
            if texto.count(depois) != 1:
                continue
            texto = texto.replace(depois, antes)
        return texto
    raise SystemExit("nao consegui reconstruir o estado anterior de %s" % rel)


PADRAO_ABSOLUTO = re.compile(r"^(\s*(?:from|import)\s+)(parsers|core|reporting|utils)\b")


def inverso_regra2(rel):
    """O inverso da regra 2: devolve o prefixo `reconstructed.` as linhas de import.

    So alcanca linhas cujo alvo e um dos quatro pacotes do nucleo, que e exatamente o
    conjunto que a regra 2 tocou. O total e conferido em `main()`.
    """
    linhas = le(os.path.join(ROOT, rel)).splitlines(keepends=True)
    feitas = 0
    for i, linha in enumerate(linhas):
        m = PADRAO_ABSOLUTO.match(linha)
        if m:
            linhas[i] = m.group(1) + "reconstructed." + linha[m.start(2):]
            feitas += 1
    return "".join(linhas), feitas


def antes_de(rel):
    atual = le(os.path.join(ROOT, rel))
    pares = next((p for r, p in PROSA if r == rel), None)
    if pares:
        return inverso(rel, pares), atual
    if rel in REGRA_2:
        texto, feitas = inverso_regra2(rel)
        return texto, atual
    if rel.startswith("src/") and rel != "src/app.py":
        congelado = os.path.join(ANTES, "reconstructed", rel.replace("src/", "", 1))
        if os.path.exists(congelado):
            return le(congelado), atual
    if rel == "src/app.py":
        return le(os.path.join(ANTES, "app.py")), atual
    for nome in ("README.md", "pyrefly.toml",
                 "_reversa_forward__003-renomear-pasta-app-para-src__regression-watch.md"):
        if rel.replace("/", "__").endswith(nome.replace("__", "/").replace("/", "__")) or rel == nome:
            p = os.path.join(HEAD, rel.replace("/", "__"))
            if os.path.exists(p):
                return le(p), atual
    return None, atual


def diff(antes, depois, nome_antes, nome_depois):
    return "".join(difflib.unified_diff(
        antes.splitlines(keepends=True), depois.splitlines(keepends=True),
        fromfile=nome_antes, tofile=nome_depois, n=3))


def main() -> int:
    print("=" * 78)
    print("REGISTRO DOS DIFFS DA OPP-20261003-FLAT")
    print("=" * 78)

    # CHG-001: a movimentacao das quatro pastas, como renomeacao de arquivo por arquivo.
    corpo = []
    for nome in SUBPACOTES:
        base = os.path.join(ANTES, "reconstructed", nome)
        for arquivo in sorted(os.listdir(base)):
            if not arquivo.endswith(".py"):
                continue
            origem = "src/reconstructed/%s/%s" % (nome, arquivo)
            destino = "src/%s/%s" % (nome, arquivo)
            antes = le(os.path.join(base, arquivo))
            depois = le(os.path.join(ROOT, destino))
            corpo.append("rename from %s\nrename to %s\n" % (origem, destino))
            if antes != depois:
                corpo.append(diff(antes, depois, "a/" + origem, "b/" + destino))
    # o __init__.py do nivel apagado
    corpo.append(diff(le(os.path.join(ANTES, "reconstructed", "__init__.py")), "",
                      "a/src/reconstructed/__init__.py", "/dev/null"))
    with open(os.path.join(HERE, LOTES[0][0]), "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(corpo))
    print("  %-38s %6d bytes" % (LOTES[0][0], len("".join(corpo).encode("utf-8"))))

    # CHG-002 e CHG-003: conferidos contra o congelado para os arquivos de src/.
    for arquivo, alvos in LOTES[1:3]:
        corpo = []
        for rel in alvos:
            antes, depois = antes_de(rel)
            if antes is None:
                raise SystemExit("sem estado anterior para %s" % rel)
            corpo.append(diff(antes, depois, "a/" + rel, "b/" + rel))
        with open(os.path.join(HERE, arquivo), "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(corpo))
        print("  %-38s %6d bytes" % (arquivo, len("".join(corpo).encode("utf-8"))))

    # CHG-004: prosa, README e pyrefly. README e pyrefly vem do HEAD.
    corpo = []
    for rel in [p for p, _ in PROSA]:
        antes, depois = antes_de(rel)
        if antes is None:
            raise SystemExit("sem estado anterior para %s" % rel)
        corpo.append(diff(antes, depois, "a/" + rel, "b/" + rel))
    with open(os.path.join(HERE, LOTES[3][0]), "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(corpo))
    print("  %-38s %6d bytes" % (LOTES[3][0], len("".join(corpo).encode("utf-8"))))

    # CHG-005: o watch.
    rel = LOTES[4][1][0]
    atual = le(os.path.join(ROOT, rel))
    antes = atual.replace(W001_DEPOIS, W001_ANTES)
    if antes == atual:
        raise SystemExit("o W001 nao contem o texto novo")
    texto = diff(antes, atual, "a/" + rel, "b/" + rel)
    with open(os.path.join(HERE, LOTES[4][0]), "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)
    print("  %-38s %6d bytes" % (LOTES[4][0], len(texto.encode("utf-8"))))

    print()
    print("=" * 78)
    print("RESULTADO: 5 LOTES GRAVADOS (esperado %d + %d linhas de import nos lotes 2 e 3)"
          % (ESPERADO_1, ESPERADO_2))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
