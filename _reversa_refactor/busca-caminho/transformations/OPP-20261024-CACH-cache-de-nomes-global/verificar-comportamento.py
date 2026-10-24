"""Verifica, antes do gate de diff, que as asserções comportamentais do teste novo
são verdadeiras no código de hoje (o estado não muda de comportamento no caminho
simples) e mede o estresse com a janela aberta.
"""
from __future__ import annotations

import os
import sys
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core import documentary_relationship as dr  # noqa: E402


class Nome:
    def __init__(self, texto: str) -> None:
        self._texto = texto

    def format(self) -> str:
        return self._texto


class Pessoa:
    def __init__(self, nome: str) -> None:
        self.name = Nome(nome)


def arvore(*nomes: str, prefixo: str = "I"):
    return ({f"@{prefixo}{indice}@": Pessoa(nome) for indice, nome in enumerate(nomes, 1)}, {}, None, {})


alfa = arvore("Ana Alfa", "Zeca Alfa", prefixo="A")
primeiro = dr._indice_por_nome(alfa)
segundo = dr._indice_por_nome(alfa)
print("cache acerta: mapa identico na 2a chamada:", segundo is primeiro)
print("nomes:", sorted(primeiro))
assert segundo is primeiro
assert set(primeiro) == {"ana alfa", "zeca alfa"}

beta = arvore("Bruno Beta", "Yara Beta", prefixo="B")
mapa_beta = dr._indice_por_nome(beta)
print("arvore nova invalida:", mapa_beta is not primeiro, "| nomes:", sorted(mapa_beta))
assert set(mapa_beta) == {"bruno beta", "yara beta"}

print()
print("estresse: 120 rodadas, duas threads, duas arvores, janela aberta")
alfa = arvore(*[f"Alfa {i}" for i in range(400)], prefixo="A")
beta = arvore(*[f"Beta {i}" for i in range(401)], prefixo="B")

trocadas: list[list[str]] = []
original = sys.getswitchinterval()
sys.setswitchinterval(0.000001)
try:
    for _ in range(120):
        largada = threading.Barrier(3)

        def trabalho(arvore_atual, marca: str) -> None:
            largada.wait(timeout=20)
            mapa = dr._indice_por_nome(arvore_atual)
            if not all(marca in nome for nome in mapa):
                trocadas.append(sorted(mapa)[:3])

        a = threading.Thread(target=trabalho, args=(alfa, "alfa"))
        b = threading.Thread(target=trabalho, args=(beta, "beta"))
        a.start()
        b.start()
        largada.wait(timeout=20)
        a.join(timeout=20)
        b.join(timeout=20)
finally:
    sys.setswitchinterval(original)

print("requisicoes que receberam a arvore errada:", len(trocadas), "de 240")
if trocadas:
    print("exemplo:", trocadas[0])
    print("ESTRESSE REPROVA O CODIGO DE HOJE, como esperado.")
else:
    print("o estresse NAO reproduziu nesta execucao (esperado: ele e probabilistico).")
