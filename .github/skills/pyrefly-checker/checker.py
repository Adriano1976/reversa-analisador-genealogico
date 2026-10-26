#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executa o Pyrefly sobre um alvo e traduz o resultado.

Uso:
    checker.py                                     # projeto inteiro
    checker.py src\\ports                           # um diretorio
    checker.py src\\ports\\adaptadores.py -p strict   # um arquivo, com flags

Saida:
    0 = nenhum diagnostico
    1 = o Pyrefly achou problemas de tipo
    2 = nao foi possivel rodar (ambiente, caminho inexistente, config invalida)

O binario e o do interpretador que executa este arquivo (`sys.executable -m
pyrefly`), e nao o que estiver no PATH: assim o script funciona sem venv ativo
e nao confunde "comando ausente" com "erro de tipo".

Pode ser chamado de qualquer subpasta: a raiz e achada subindo a arvore, e os
alvos relativos sao resolvidos contra o diretorio de onde o comando rodou.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

# Opcoes do `pyrefly check` que consomem o argumento seguinte como valor: sem
# esta lista, `--min-severity warn` seria lido como se "warn" fosse um alvo.
_OPCOES_COM_VALOR = frozenset({
    "-p", "--preset", "-c", "--config", "-o", "--output", "--output-format",
    "-j", "--threads", "--color", "--min-severity", "--project-excludes",
    "--project-includes", "--search-path", "--site-packages-path",
    "--python-version", "--python-platform", "--baseline",
    "--baseline-error-level", "--only", "--ignore", "--error", "--warn",
    "--enabled-ignores", "--ignore-missing-imports", "--replace-imports-with-any",
})


def _resolver_alvos(argv: list[str]) -> list[str]:
    """Alvos relativos viram absolutos contra o diretorio de chamada.

    A execucao acontece na raiz do projeto (para achar o `pyrefly.toml`), mas o
    usuario pensa a partir de onde esta. Sem isto, `checker.py ports` dentro de
    `src/` procuraria `ports` na raiz.
    """
    atual = Path.cwd()
    resolvidos: list[str] = []
    indice = 0
    while indice < len(argv):
        argumento = argv[indice]
        if argumento in _OPCOES_COM_VALOR and indice + 1 < len(argv):
            resolvidos.extend((argumento, argv[indice + 1]))
            indice += 2
            continue
        if argumento.startswith("-"):
            resolvidos.append(argumento)
        else:
            caminho = Path(argumento)
            resolvidos.append(str(caminho if caminho.is_absolute() else atual / caminho))
        indice += 1
    return resolvidos


def _raiz_do_projeto() -> Path | None:
    """Pasta mais proxima (subindo) que tenha `pyrefly.toml` ou `pyproject.toml`."""
    pasta: Path = Path(__file__).resolve().parent
    while True:
        if (pasta / "pyrefly.toml").exists() or (pasta / "pyproject.toml").exists():
            return pasta
        if pasta.parent == pasta:
            return None
        pasta = pasta.parent


def main(argv: list[str]) -> int:
    if importlib.util.find_spec("pyrefly") is None:
        print("[pyrefly] nao instalado neste interpretador; use .venv\\Scripts\\python.exe.",
              file=sys.stderr)
        return 2

    raiz: Path | None = _raiz_do_projeto()
    if raiz is None:
        print("[pyrefly] pyrefly.toml/pyproject.toml nao encontrado acima deste arquivo.",
              file=sys.stderr)
        return 2

    comando: list[str] = [sys.executable, "-m", "pyrefly", "check", *_resolver_alvos(argv)]
    print(f"[pyrefly] cwd={raiz} :: {' '.join(comando)}")

    resultado: subprocess.CompletedProcess[str] = subprocess.run(
        comando, cwd=raiz, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    saida: str = (resultado.stdout + resultado.stderr).strip()

    if resultado.returncode == 0:
        print("[pyrefly] 0 erros.")
        return 0

    # Configuracao quebrada e caminho inexistente saem com exit 1, mas nao sao
    # "problema de tipo": sao ambiente, e o agente nao deve tentar corrigir codigo.
    nao_e_tipo: bool = any(
        marca in saida
        for marca in ("Fatal configuration error", "does not exist", "failed to parse")
    )
    if resultado.returncode == 1 and not nao_e_tipo:
        print("[pyrefly] problemas encontrados (exit 1):")
        print(saida)
        return 1

    print(f"[pyrefly] nao foi possivel rodar (exit {resultado.returncode}):")
    print(saida)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
