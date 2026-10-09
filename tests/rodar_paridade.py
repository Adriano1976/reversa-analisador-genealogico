"""Executa o harness de paridade com a pasta de upload isolada (feature 010, `D-07`).

## O problema que este involucro resolve

O coletor do candidato, embutido em `_reversa_sdd/parity/harness.py`, importa a
aplicacao (`harness.py:356`) e a aplicacao resolve a pasta de upload **no import**
(`src/app.py:115,123,129`). Como a pasta e ancorada no arquivo do app desde a feature
006, o `os.chdir` que o coletor ja faz (`harness.py:259`) **nao** a redireciona.

Resultado medido em 2026-10-09: cada execucao da paridade gravava sondas (`*__probe.ged`)
e as fixtures de DNA na pasta **real** do operador — 18 arquivos, 6.631 bytes de residuo.

## A correcao, e por que ela e por fora

O harness lanca cada coletor com `env = dict(os.environ, ...)` (`harness.py:465`), entao
uma variavel definida **antes** da chamada chega ao processo do coletor e a pasta e
resolvida no destino descartavel. Isso permite isolar o instrumento **sem editar o
instrumento** — que continua byte a byte igual, como convem a regua que ele e.

**Consequencia declarada:** invocar `harness.py` direto, sem este involucro, ainda suja a
pasta real. Este e o caminho documentado de execucao (`README.md`, `onboarding.md`).

## Uso

    .venv\\Scripts\\python.exe tests\\rodar_paridade.py [argumentos do harness]

Qualquer argumento e repassado ao harness (`--gedcom`, `--pares`, `--timeout`, ...), e o
codigo de saida devolvido e o mesmo do harness.
"""
from __future__ import annotations

import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join(RAIZ, "_reversa_sdd", "parity", "harness.py")
VARIAVEL = "ANALISADOR_UPLOAD_FOLDER"
# `.parity-tmp/` ja esta no `.gitignore`, entao a pasta descartavel nao entra no
# versionamento nem aparece em `git status`.
PASTA_RELATIVA = os.path.join(".parity-tmp", "uploads")


def pasta_descartavel(raiz: str | None = None) -> str:
    """Pasta que recebe o que a paridade enviar. Criada se nao existir."""
    caminho = os.path.join(raiz or RAIZ, PASTA_RELATIVA)
    os.makedirs(caminho, exist_ok=True)
    return caminho


def montar_ambiente(base: dict | None = None, pasta: str | None = None) -> dict:
    """Ambiente do coletor: o do chamador com a pasta de upload redirecionada.

    Devolve uma **copia**: o ambiente do processo que invoca o involucro nao e alterado.
    """
    ambiente = dict(os.environ if base is None else base)
    ambiente[VARIAVEL] = pasta or pasta_descartavel()
    return ambiente


def comando(argumentos=(), script: str | None = None) -> list:
    """Linha de comando do harness, com os argumentos recebidos."""
    return [sys.executable, script or HARNESS, *argumentos]


def executar(argumentos=(), script: str | None = None, pasta: str | None = None,
             ambiente: dict | None = None) -> int:
    """Roda o harness com a pasta isolada e devolve o codigo de saida dele.

    `ambiente` existe para o controle negativo do teste: entregar um ambiente **sem** a
    variavel prova que o redirecionamento — e nao o roteiro de teste — e a causa do
    comportamento observado. Sem ele, o ambiente e o do chamador com a pasta trocada.
    """
    processo = subprocess.run(
        comando(argumentos, script),
        env=ambiente if ambiente is not None else montar_ambiente(pasta=pasta or pasta_descartavel()),
        cwd=RAIZ,
    )
    return processo.returncode


def main(argv: list | None = None) -> int:
    argumentos = list(sys.argv[1:] if argv is None else argv)
    destino = pasta_descartavel()
    print("pasta de upload isolada: " + destino, flush=True)
    return executar(argumentos, pasta=destino)


if __name__ == "__main__":
    sys.exit(main())
