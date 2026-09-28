"""Remove o residuo gerado pelos probes de paridade.

## Por que isto existe

`harness.py` grava, a cada execucao, duas coisas em `_reversa_sdd/parity/`:

    _collect_oracle.py   copia do ORACLE_COLLECTOR embutido
    _collect_cand.py     copia do CANDIDATE_COLLECTOR embutido
    _obs_oracle.json     observacoes coletadas do oraculo
    _obs_cand.json       observacoes coletadas do candidato

Os dois primeiros sao **copias geradas** dos coletores que vivem embutidos em
`harness.py` — a fonte da verdade e o `harness.py`. Os dois ultimos sao corpus
grandes. Nenhum dos quatro foi registrado em `.state.json`, porque sao residuo,
nao artefato.

E os probes deixam diretorios temporarios na raiz do projeto:

    .parity-tmp/             TMPDIR redirecionado por _probe_fix_impact.py
    .parity-pytest-tmp/      criado numa tentativa com --basetemp (abandonada)
    .parity-run-oracle/      diretorio de trabalho do coletor do oraculo
    .parity-run-cand/        diretorio de trabalho do coletor do candidato

## Nota honesta sobre o sandbox

O sandbox pode NEGAR a remocao de diretorios no workspace (o mesmo motivo pelo
qual o fixture `tmp_path` do pytest nao funciona aqui). Este script faz o
melhor esforco e **reporta o que nao conseguiu remover**, em vez de fingir
sucesso. Residuo que sobra e inofensivo: nada no pipeline o le.

Uso:
    python _reversa_sdd/parity/_clean_residue.py
    python _reversa_sdd/parity/_clean_residue.py --dry-run
"""
from __future__ import annotations

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# Arquivos gerados dentro de parity/ (nunca os 3 fontes: harness, make_fixtures, _probe).
FILES = ["_collect_oracle.py", "_collect_cand.py", "_obs_oracle.json", "_obs_cand.json"]

# Diretorios temporarios na raiz do projeto.
DIRS = [".parity-tmp", ".parity-pytest-tmp", ".parity-run-oracle", ".parity-run-cand"]

# NUNCA remover: sao fontes registradas em .state.json.
PROTEGIDOS = {"harness.py", "make_fixtures.py", "_probe_fix_impact.py", "_clean_residue.py", "fixtures"}


def main() -> int:
    dry = "--dry-run" in sys.argv
    print("=" * 70)
    print("LIMPEZA DE RESIDUO DOS PROBES DE PARIDADE" + ("  [DRY-RUN]" if dry else ""))
    print("=" * 70)

    removidos, falhas = [], []

    for name in FILES:
        p = os.path.join(HERE, name)
        if name in PROTEGIDOS or not os.path.exists(p):
            continue
        if dry:
            print("  removeria  %s" % name)
            continue
        try:
            os.remove(p)
            removidos.append(name)
            print("  removido   %s" % name)
        except OSError as e:
            falhas.append((name, e))
            print("  FALHOU     %s (%s)" % (name, type(e).__name__))

    for name in DIRS:
        p = os.path.join(ROOT, name)
        if not os.path.isdir(p):
            continue
        if dry:
            print("  removeria  %s/" % name)
            continue
        try:
            shutil.rmtree(p)
            removidos.append(name + "/")
            print("  removido   %s/" % name)
        except OSError as e:
            falhas.append((name + "/", e))
            print("  FALHOU     %s/ (%s)" % (name, type(e).__name__))

    print("-" * 70)
    print("removidos: %d   falhas: %d" % (len(removidos), len(falhas)))
    if falhas:
        print()
        print("O sandbox negou a remocao de: %s" % ", ".join(n for n, _ in falhas))
        print("Isso e esperado neste ambiente e e INOFENSIVO — nada no pipeline le")
        print("esses caminhos. O harness os recria na proxima execucao.")
    print("=" * 70)
    # Nunca retorna erro por residuo que o sandbox nao deixa remover.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
