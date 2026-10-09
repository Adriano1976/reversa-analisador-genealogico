"""T016 - a paridade continua 100 % e nao suja a pasta canonica (RF-07).

Roda o involucro `tests/rodar_paridade.py` (nunca o `harness.py` direto, que escreve as
sondas na pasta real) e confere duas coisas:

1. a saida termina em `PARIDADE 100 %`;
2. o inventario de `src/uploads` e **identico** antes e depois -- nome e `sha256` por
   arquivo. E o `RF-04` da feature 010, que esta feature nao pode quebrar.

O instrumento de inventario e o da propria feature 010 (`tests/manutencao_de_uploads.py`),
para que a conferencia seja comparavel com as medicoes anteriores.
"""
from __future__ import annotations

import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))

from manutencao_de_uploads import inventariar  # noqa: E402

CANONICA = os.path.join(RAIZ, "src", "uploads")
INVOLUCRO = os.path.join(RAIZ, "tests", "rodar_paridade.py")
EVIDENCIA = os.path.join(AQUI, "T016-paridade.txt")


def resumo(inventario: dict) -> str:
    return "%d arquivos, %d bytes" % (len(inventario), sum(t for t, _ in inventario.values()))


def main() -> int:
    antes = inventariar(CANONICA)
    print("inventario de src/uploads ANTES : " + resumo(antes))

    r = subprocess.run([sys.executable, INVOLUCRO], capture_output=True, text=True, cwd=RAIZ)
    saida = (r.stdout or "") + (r.stderr or "")
    linhas = saida.strip().splitlines()
    print("exit code do involucro           : %d" % r.returncode)
    print("ultimas linhas:")
    for linha in linhas[-6:]:
        print("   " + linha)

    depois = inventariar(CANONICA)
    print("inventario de src/uploads DEPOIS: " + resumo(depois))

    cem_por_cento = "PARIDADE 100" in saida
    identico = antes == depois
    print("saida contem PARIDADE 100 %%      : %s" % cem_por_cento)
    print("inventario identico antes/depois : %s" % identico)
    if not identico:
        for nome in sorted(set(antes) ^ set(depois)):
            print("   diferenca de nome: " + nome)
        for nome in sorted(set(antes) & set(depois)):
            if antes[nome][1] != depois[nome][1]:
                print("   sha256 mudou: " + nome)

    texto = "\n".join([
        "# T016 - paridade pelo involucro, e a pasta canonica intacta",
        "# Gerado em: 2026-10-09",
        "# Comando: python tests/rodar_paridade.py",
        "#",
        "# inventario de src/uploads ANTES : " + resumo(antes),
        "# inventario de src/uploads DEPOIS: " + resumo(depois),
        "# inventario identico antes/depois: " + str(identico),
        "# saida contem PARIDADE 100 %%     : " + str(cem_por_cento),
        "# exit code do involucro          : %d" % r.returncode,
        "",
        "## saida completa do involucro",
        "",
    ] + ["    " + linha for linha in linhas]) + "\n"
    with open(EVIDENCIA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)
    print("evidencia: " + EVIDENCIA)

    return 0 if (cem_por_cento and identico and r.returncode == 0) else 3


if __name__ == "__main__":
    sys.exit(main())
