"""Prova do defeito da OPP-20261024-CACH, contra o codigo de 2026-10-24.

Nao toca em arquivo do projeto. Importa o modulo real, substitui o dicionario de
modulo por um espiao que estaciona a thread A exatamente entre a publicacao de
`chave` e o `return`, e mostra que A devolve o mapa da arvore da thread B.

Este espiao so existe porque o estado de hoje e um `dict`. Depois da costura ele
deixa de ser instalavel, e a guarda permanente vira outra coisa: uma verificacao
estrutural por AST mais uma verificacao de comportamento. Ver o plano.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core import documentary_relationship as dr  # noqa: E402
from parsers import gedcom_parser  # noqa: E402

GED_ALFA = """0 HEAD
1 SOUR PROVA
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Ana /Alfa/
1 SEX F
0 @I2@ INDI
1 NAME Zeca /Alfa/
1 SEX M
0 TRLR
"""

GED_BETA = """0 HEAD
1 SOUR PROVA
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @I1@ INDI
1 NAME Bruno /Beta/
1 SEX M
0 @I2@ INDI
1 NAME Yara /Beta/
1 SEX F
0 @I3@ INDI
1 NAME Xisto /Beta/
1 SEX M
0 TRLR
"""


def carregar(texto: str):
    fd, caminho = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(texto)
    try:
        return gedcom_parser.carregar_arvore(caminho)
    finally:
        try:
            os.unlink(caminho)
        except OSError:
            pass


class DicionarioEspiao(dict):
    """Estaciona a thread chamada `A` logo depois de publicar `chave`.

    O gancho e o proprio `__setitem__`: a linha 350 do modulo grava `chave` e, a
    partir dali, a linha 351 relê o global. O espiao transforma esse intervalo em
    um ponto de encontro deterministico.
    """

    def __init__(self, estacionou: threading.Event, liberar: threading.Event):
        super().__init__({"chave": (), "mapa": {}})
        self._estacionou = estacionou
        self._liberar = liberar

    def __setitem__(self, chave, valor):
        super().__setitem__(chave, valor)
        if chave == "chave" and threading.current_thread().name == "A":
            self._estacionou.set()
            self._liberar.wait(timeout=20)


def main() -> int:
    if not isinstance(dr._INDICE_DE_NOMES, dict):
        print("ESTADO ATUAL NAO E UM DICT: o espiao nao se aplica.")
        print("type(_INDICE_DE_NOMES) =", type(dr._INDICE_DE_NOMES).__name__)
        return 2

    arvore_alfa = carregar(GED_ALFA)
    arvore_beta = carregar(GED_BETA)

    estacionou = threading.Event()
    liberar = threading.Event()
    dr._INDICE_DE_NOMES = DicionarioEspiao(estacionou, liberar)

    resultado: dict = {}
    erros: list[str] = []

    def trabalho_a():
        try:
            resultado["a"] = dr._indice_por_nome(arvore_alfa)
        except Exception:  # noqa: BLE001
            erros.append(traceback.format_exc())

    a = threading.Thread(target=trabalho_a, name="A")
    a.start()

    if not estacionou.wait(timeout=20):
        print("a thread A nao chegou ao ponto de publicacao de `chave`")
        liberar.set()
        a.join(timeout=5)
        return 2

    # A esta parada dentro do __setitem__ de `chave`, com o mapa da alfa ja
    # publicado. A thread principal publica agora o mapa da beta, inteiro.
    mapa_beta = dr._indice_por_nome(arvore_beta)
    liberar.set()
    a.join(timeout=20)

    if erros:
        print("ERRO NA THREAD A:")
        print(erros[0])
        return 2

    mapa_a = resultado["a"]
    nomes_alfa = set(mapa_a)
    tem_nome_da_beta = any("beta" in nome for nome in nomes_alfa)
    tem_nome_da_alfa = any("alfa" in nome for nome in nomes_alfa)

    print("nomes no mapa devolvido para a thread A:", sorted(nomes_alfa))
    print("nomes no mapa devolvido para a thread B:", sorted(mapa_beta))
    print()
    print("A devolveu o mapa da PROPRIA arvore (alfa)?", tem_nome_da_alfa and not tem_nome_da_beta)
    print("A devolveu os nomes da arvore da thread B?", tem_nome_da_beta)
    print("mesma lista de nomes para as duas?", sorted(nomes_alfa) == sorted(mapa_beta))
    print()
    if tem_nome_da_beta and not tem_nome_da_alfa:
        print("DEFEITO PROVADO: a requisicao A, que pediu a arvore alfa,")
        print("recebeu o indice da arvore beta.")
        return 0
    print("nao reproduziu nesta execucao.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
