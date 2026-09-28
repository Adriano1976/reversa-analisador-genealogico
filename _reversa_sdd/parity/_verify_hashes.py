"""Verifica os hashes registrados em `.state.json` contra os arquivos em disco.

## Convencao de hash do pipeline (importante nao confundir)

    .md            -> sha256 do CORPO (abaixo do front-matter, LF-normalizado,
                      com o newline final removido)
    .py .json .yaml-> sha256 do ARQUIVO INTEIRO

Este script aplica a convencao pelo SUFIXO do arquivo. A primeira versao aplicava
hash de corpo apenas quando existia `hashScope`, o que reportava 21 falsas
divergencias — o bug era da verificacao, nao dos artefatos.
"""
from __future__ import annotations

import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "_reversa_sdd", "migration", ".state.json")

# Suffixos que usam hash do ARQUIVO INTEIRO. Todo o resto (.md) usa hash de corpo.
FULL_SUFFIX = (".py", ".json", ".yaml", ".yml", ".csv", ".ged", ".feature")


def body_hash(fp: str) -> str:
    raw = open(fp, "rb").read().decode("utf-8")
    if raw.startswith("---"):
        end = raw.index("\n---", 3)
        b = raw[end + 4:]
    else:
        b = raw
    b = b.replace("\r\n", "\n")
    if b.startswith("\n"):
        b = b[1:]
    return hashlib.sha256(b.rstrip("\n").encode("utf-8")).hexdigest()


def full_hash(fp: str) -> str:
    return hashlib.sha256(open(fp, "rb").read()).hexdigest()


def main() -> int:
    d = json.load(open(STATE, encoding="utf-8"))
    ok, bad, ausentes, sem_path = 0, [], [], []
    ignorados: list[str] = []
    for nome, meta in d["artifacts"].items():
        rel = meta.get("path")
        if not rel:
            if "/" in nome:
                sem_path.append(nome)
                continue
            rel = "_reversa_sdd/migration/" + nome
        fp = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(fp):
            ausentes.append(rel)
            continue
        # Entradas de DIRETORIO tem hash agregado, nao hash de corpo/arquivo.
        if os.path.isdir(fp):
            ignorados.append(rel)
            continue
        esperado = meta["sha256"]
        # Um hash de corpo declarado explicitamente vence o sufixo.
        if meta.get("hashScope"):
            atual = body_hash(fp)
        elif fp.lower().endswith(FULL_SUFFIX):
            atual = full_hash(fp)
        else:
            atual = body_hash(fp)
        if atual == esperado:
            ok += 1
        else:
            bad.append((rel, esperado[:16], atual[:16]))

    print("=" * 74)
    print("VERIFICACAO DE HASHES — .state.json vs disco")
    print("=" * 74)
    print("conferem: %d   divergem: %d   ausentes: %d   sem path: %d"
          % (ok, len(bad), len(ausentes), len(sem_path)))
    for rel, esp, atu in bad:
        print("  DIVERGE  %-52s registrado=%s  disco=%s" % (rel, esp, atu))
    for rel in ausentes:
        print("  AUSENTE  %s" % rel)
    for nome in sem_path:
        print("  SEM PATH (registrar 'path'): %s" % nome)
    for rel in ignorados:
        print("  DIRETORIO (hash agregado, nao verificado aqui): %s" % rel)
    print("=" * 74)
    return 1 if (bad or ausentes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
