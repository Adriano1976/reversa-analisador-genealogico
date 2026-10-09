"""Remove a copia externa da pasta de uploads, com conferencia antes e depois (feature 012).

Uso:

    python _reversa_forward/012-pasta-canonica-no-repositorio/evidence/_remover_copia_externa.py

Por que um script, e nao um comando solto. A remocao e a unica operacao destrutiva desta
feature. Ela tem de ser **fail-closed**: se o inventario da copia externa divergir do
inventario de `src/uploads` em um unico arquivo, nada e removido. Um `Remove-Item -Recurse`
nao tem onde escrever essa condicao, e o operador nao teria como auditar depois o que foi
comparado.

O instrumento de inventario e o da propria feature 010 (`tests/manutencao_de_uploads.py`,
funcao `inventariar`): o mesmo `sha256` por arquivo que conferiu a copia quando ela nasceu.
Reaproveita-lo e o que torna a conferencia comparavel com a medicao original.

Codigos de saida: 0 removida, 2 copia externa ausente (nada a fazer),
3 conferencia recusou a remocao, 4 o alvo esta dentro do repositorio (recusa de seguranca).
"""
from __future__ import annotations

import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RAIZ, "tests"))

from manutencao_de_uploads import inventariar  # noqa: E402

ORIGEM = os.path.join(RAIZ, "src", "uploads")
EXTERNA = r"D:\dados-genealogicos\uploads"


def resumo(inventario: dict) -> str:
    bytes_totais = sum(tamanho for tamanho, _ in inventario.values())
    return "%d arquivos, %d bytes" % (len(inventario), bytes_totais)


def diferencas(a: dict, b: dict) -> tuple:
    faltando = sorted(set(a) - set(b))
    sobrando = sorted(set(b) - set(a))
    divergentes = sorted(nome for nome in set(a) & set(b) if a[nome][1] != b[nome][1])
    return faltando, sobrando, divergentes


def main() -> int:
    print("# Remocao da copia externa - feature 012")
    print("# Origem  (fica): %s" % ORIGEM)
    print("# Alvo    (sai) : %s" % EXTERNA)
    print()

    raiz_abs = os.path.abspath(RAIZ) + os.sep
    alvo_abs = os.path.abspath(EXTERNA)
    if alvo_abs.startswith(raiz_abs) or raiz_abs.startswith(alvo_abs + os.sep):
        print("RECUSADO: o alvo e a origem se contem; nada foi removido.")
        return 4

    if not os.path.isdir(EXTERNA):
        print("# A copia externa nao existe. Nada a remover.")
        print("# Inventario da origem agora: " + resumo(inventariar(ORIGEM)))
        return 2

    antes_origem = inventariar(ORIGEM)
    antes_externa = inventariar(EXTERNA)
    print("# Inventario da origem, ANTES : " + resumo(antes_origem))
    print("# Inventario da copia,  ANTES : " + resumo(antes_externa))

    faltando, sobrando, divergentes = diferencas(antes_origem, antes_externa)
    if faltando or sobrando or divergentes:
        print()
        print("RECUSADO: a copia externa nao reproduz a origem. NADA foi removido.")
        for nome in faltando:
            print("  so na origem   : " + nome)
        for nome in sobrando:
            print("  so na copia    : " + nome)
        for nome in divergentes:
            print("  sha256 diverge : " + nome)
        return 3

    print("# Conferencia: mesma lista de nomes, mesmo sha256 por arquivo. Pode remover.")
    shutil.rmtree(EXTERNA)
    print("# Removido: %s" % EXTERNA)

    depois_origem = inventariar(ORIGEM)
    print()
    print("# Inventario da origem, DEPOIS: " + resumo(depois_origem))

    faltando, sobrando, divergentes = diferencas(antes_origem, depois_origem)
    if faltando or sobrando or divergentes:
        print("FALHA: a origem mudou durante a remocao.")
        for nome in faltando:
            print("  desapareceu    : " + nome)
        for nome in sobrando:
            print("  apareceu       : " + nome)
        for nome in divergentes:
            print("  sha256 mudou   : " + nome)
        return 3

    print("# Origem intacta: identica, arquivo a arquivo, antes e depois.")
    print("# A pasta externa existe? %s" % os.path.isdir(EXTERNA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
