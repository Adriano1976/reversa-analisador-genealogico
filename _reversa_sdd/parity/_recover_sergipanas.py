"""Tenta RECUPERAR o conteudo nao commitado de Familias_Sergipanas.csv que um
`git checkout --` destruiu.

## O que aconteceu

O arquivo tinha 335 linhas em disco (sha256 94e2402671702cac...) e 331 no HEAD. O
`git checkout --` que eu rodei o sobrescreveu com a versao do HEAD. O conteudo de 335
linhas NAO estava commitado, entao nao ha ref para ele — mas o git pode ter guardado o
objeto como blob DANGLING (alcancavel apenas por hash), e `git fsck --lost-found`
listou varios.

## Como este script procura

Nao adivinha por tamanho (ha varios blobs parecidos). Procura a ASSINATURA exata do
conteudo perdido: a linha `***,"Maria de Lourdes Prata de Jesus"`, que aparecia
no diff que eu vi ANTES de restaurar. Um blob que contenha essa linha E tenha 335
linhas E seja um CSV de DNA e o candidato. Se nenhum casar, o conteudo esta perdido e
o script diz isso — sem inventar.

## se encontrar

Escreve o conteudo recuperado em `.scr005-probe/Sergipanas.RECUPERADO.csv` e calcula o
sha256. NAO sobrescreve o arquivo do usuario: restaurar e decisao humana, porque o
arquivo pode ter sido alterado legitimamente depois.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = os.path.join(ROOT, ".scr005-probe")

# Assinaturas do conteudo perdido, vistas no diff ANTES da restauracao.
ASSINATURAS = [b"***", b"Maria de Lourdes Prata de Jesus"]
ALVO_LINHAS = 335


def blobs_soltos() -> list[str]:
    p = subprocess.run(["git", "fsck", "--lost-found", "--no-progress"],
                       cwd=ROOT, capture_output=True, text=True)
    out = []
    for ln in (p.stdout + p.stderr).splitlines():
        if ln.startswith("dangling blob "):
            out.append(ln.split()[-1])
    return out


def conteudo(sha: str) -> bytes | None:
    p = subprocess.run(["git", "cat-file", "-p", sha], cwd=ROOT,
                       capture_output=True)
    return p.stdout if p.returncode == 0 else None


def main() -> int:
    os.makedirs(DEST, exist_ok=True)
    blobs = blobs_soltos()
    print("=" * 74)
    print("RECUPERACAO DE CONTEUDO NAO COMMITADO — Familias_Sergipanas.csv")
    print("=" * 74)
    print("blobs soltos encontrados: %d" % len(blobs))
    print()

    achados = []
    for sha in blobs:
        b = conteudo(sha)
        if not b:
            continue
        if all(a in b for a in ASSINATURAS):
            linhas = b.count(b"\n")
            achados.append((sha, linhas, len(b)))
            print("  CANDIDATO %s  linhas=%d  bytes=%d" % (sha[:12], linhas, len(b)))

    if not achados:
        print("  NENHUM blob solto contem as assinaturas do conteudo perdido.")
        print()
        print("  Conclusao: o conteudo de 335 linhas NAO e recuperavel pelo git.")
        print("  Provavel causa: o objeto nunca foi escrito no object database (o git")
        print("  so guarda blob ao fazer add/commit/stash; uma edicao em working tree")
        print("  que nunca passou por `git add` nao deixa objeto).")
        return 1

    # Prefere o candidato com a contagem de linhas esperada.
    achados.sort(key=lambda t: (abs(t[1] - ALVO_LINHAS), -t[2]))
    sha, linhas, nbytes = achados[0]
    b = conteudo(sha)
    saida = os.path.join(DEST, "Sergipanas.RECUPERADO.csv")
    with open(saida, "wb") as fh:
        fh.write(b)
    h = hashlib.sha256(b).hexdigest()
    print()
    print("  SELECIONADO: %s (%d linhas)" % (sha[:12], linhas))
    print("  gravado em : %s" % os.path.relpath(saida, ROOT))
    print("  sha256     : %s" % h)
    print("  (o sha256 do conteudo destruido era 94e2402671702cac... — compare)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
