"""Contraprova: com `get_name` do oraculo aplicado, a paridade deve ser TOTAL.

Este e o teste que decide se DIV-001 e a UNICA divergencia de comportamento entre
oraculo e candidato. Se, corrigido `get_name`, ainda sobrar divergencia, entao ha
um segundo problema escondido atras do primeiro — e o harness precisa ser
executado ate a paridade total para provar isso.

Metodo: copia `reconstructed/` para um diretorio temporario, substitui `get_name`
pela versao do oraculo, aponta o coletor do candidato para a copia e roda o harness.
NAO toca em `src/reconstructed/` (artefato de trabalho anterior).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "src", "reconstructed")
STUB = os.path.join(ROOT, ".parity-stub", "reconstructed")

ORACLE_GET_NAME = '''def get_name(person):
    """COMPORTAMENTO DO ORACULO — copia fiel de app_legacy_e43ca22.py:42-43."""
    return person.name.format() if person and person.name else "Sem Nome"
'''


def main() -> int:
    shutil.rmtree(os.path.dirname(STUB), ignore_errors=True)
    shutil.copytree(SRC, STUB)
    alvo = os.path.join(STUB, "gedcom_state.py")
    src = open(alvo, encoding="utf-8").read()

    # Substitui a funcao get_name inteira (da def ate a linha em branco dupla).
    ini = src.index("def get_name(")
    fim = src.index("\n\n\n", ini)
    novo = src[:ini] + ORACLE_GET_NAME + src[fim:]
    with open(alvo, "w", encoding="utf-8") as fh:
        fh.write(novo)

    print("=" * 78)
    print("CONTRAPROVA — candidato com get_name do ORACULO")
    print("=" * 78)
    print("stub: %s" % os.path.relpath(STUB, ROOT))
    print("substituido: def get_name(...) -> versao do oraculo")
    print()

    # Aponta o coletor do candidato para o stub.
    #
    # ARMADILHA (custou uma rodada inteira): o coletor faz `os.chdir(run_dir)` ANTES
    # de importar. Com uma entrada '' (ou o proprio run_dir) no sys.path, o Python
    # resolve `reconstructed` como NAMESPACE PACKAGE do diretorio de trabalho — cria
    # um pacote VAZIO (`__file__ = None`) que tem precedencia sobre o pacote real, e o
    # erro que aparece e `cannot import name 'upload' from 'reconstructed'
    # (unknown location)`. A mensagem nao diz "namespace package", entao engana.
    #
    # Correcao: inserir o DIRETORIO QUE CONTEM o pacote, e nao depender do CWD.
    h = os.path.join(HERE, "harness.py")
    hs = open(h, encoding="utf-8").read()
    antigo = 'sys.path.insert(0, os.path.join(W, "src"))'
    assert antigo in hs, "o coletor do candidato mudou; ajuste este script"
    hs2 = hs.replace(antigo, 'sys.path.insert(0, os.path.join(W, ".parity-stub"))')
    h_stub = os.path.join(HERE, "_harness_stub.py")
    with open(h_stub, "w", encoding="utf-8") as fh:
        fh.write(hs2)

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    ged = sys.argv[1] if len(sys.argv) > 1 else None
    cmd = [sys.executable, h_stub]
    if ged:
        cmd += ["--gedcom", ged]
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
