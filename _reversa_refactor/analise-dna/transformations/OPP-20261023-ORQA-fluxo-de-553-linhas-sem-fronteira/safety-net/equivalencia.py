"""Digest de equivalencia da OPP-20261023-ORQA.

Compara o resultado COMPLETO de `dna_analysis` entre duas arvores de codigo
(antes e depois), e nao so os campos que algum teste lembrou de conferir.

Uso:
    python equivalencia.py --src src
    python equivalencia.py --src C:\\temp\\shadow\\src

Imprime um sha256 por cenario e um digest combinado. Dois `--src` diferentes
devem imprimir o MESMO digest na ultima linha.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parents[5]


def _cenarios() -> list[tuple[str, str, str | None]]:
    sys.path.insert(0, str(RAIZ))
    from tests.fixtures.sample_dna import (
        DNA_CSV_DUPLICATED,
        DNA_CSV_NO_INTERSECTION,
        DNA_CSV_UTF8,
        DNA_GED,
    )

    return [
        ("utf8", DNA_GED, DNA_CSV_UTF8),
        ("duplicado", DNA_GED, DNA_CSV_DUPLICATED),
        ("sem_intersecao", DNA_GED, DNA_CSV_NO_INTERSECTION),
    ]


def _rodar(src: pathlib.Path) -> dict[str, str]:
    sys.path.insert(0, str(src))
    from core.dna_analysis import dna_analysis
    from parsers.gedcom_parser import carregar_arvore
    from tests.fixtures.helpers import deps

    dependencias = deps()
    digests: dict[str, str] = {}
    for nome, ged, csv in _cenarios():
        fd_ged, caminho_ged = tempfile.mkstemp(suffix=".ged")
        try:
            with os.fdopen(fd_ged, "w", encoding="utf-8") as arquivo:
                arquivo.write(ged)
            arvore = carregar_arvore(caminho_ged)
        finally:
            os.remove(caminho_ged)

        fd_csv, caminho_csv = tempfile.mkstemp(suffix=".csv")
        try:
            with os.fdopen(fd_csv, "w", encoding="utf-8", newline="") as arquivo:
                arquivo.write(csv)
            observacoes: list[str] = []
            cobertura: dict = {}
            resultados, descartados, mensagem = dna_analysis(
                caminho_csv,
                "Carlos Silva Souza",
                dependencias,
                arvore,
                observacoes,
                cobertura=cobertura,
            )
        finally:
            os.remove(caminho_csv)

        canonico = json.dumps(
            {
                "resultados": resultados,
                "descartados": descartados,
                "mensagem": mensagem,
                "observacoes": observacoes,
                "cobertura": cobertura,
            },
            sort_keys=True,
            ensure_ascii=False,
            default=repr,
        )
        digests[nome] = hashlib.sha256(canonico.encode("utf-8")).hexdigest()
    return digests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    argumentos = parser.parse_args()

    src = pathlib.Path(argumentos.src).resolve()
    if not (src / "core" / "dna_analysis.py").is_file():
        print(f"ABORTA: {src} nao tem core/dna_analysis.py")
        return 2

    print(f"src: {src}")
    sys.path.insert(0, str(RAIZ))
    digests = _rodar(src)
    for nome, digest in digests.items():
        print(f"  {nome:16s} {digest}")
    combinado = hashlib.sha256("".join(digests.values()).encode("utf-8")).hexdigest()
    print(f"  {'COMBINADO':16s} {combinado}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
