"""Compara as duas saidas da sonda de mensagens, caso a caso.

    python _comparar.py

Sai com codigo 1 se QUALQUER caso divergir em status, classe de alerta ou texto.
Comparar so o texto deixaria passar uma mudanca de `danger` para `success` — que
e exatamente o modo de renderizacao que a `D-11` tirou do texto e passou para o
campo de desfecho.
"""
from __future__ import annotations

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CAMPOS = ("status", "alerta", "mensagem")


def carregar(rotulo):
    with open(os.path.join(AQUI, "mensagens_%s.json" % rotulo), encoding="utf-8") as fh:
        return {caso["caso"]: caso for caso in json.load(fh)}


def main():
    antes, depois = carregar("antes"), carregar("depois")
    casos = list(antes.keys())
    faltando = [c for c in casos if c not in depois]
    sobrando = [c for c in depois if c not in antes]

    divergencias = []
    for caso in casos:
        if caso not in depois:
            continue
        for campo in CAMPOS:
            if antes[caso][campo] != depois[caso][campo]:
                divergencias.append((caso, campo, antes[caso][campo], depois[caso][campo]))

    print("casos comparados: %d" % len(casos))
    for caso in casos:
        marca = "DIVERGE" if any(d[0] == caso for d in divergencias) else "igual  "
        print("  %s  %-24s status=%s alerta=%s" % (
            marca, caso, depois.get(caso, {}).get("status"),
            depois.get(caso, {}).get("alerta")))

    if faltando:
        print("\nAUSENTES no depois: %s" % ", ".join(faltando))
    if sobrando:
        print("\nSOBRANDO no depois: %s" % ", ".join(sobrando))

    for caso, campo, valor_antes, valor_depois in divergencias:
        print("\nDIVERGENCIA em %s.%s:\n  antes : %s\n  depois: %s" % (
            caso, campo, ascii(valor_antes), ascii(valor_depois)))

    if divergencias or faltando or sobrando:
        print("\nRESULTADO: DIVERGENCIA")
        return 1
    print("\nRESULTADO: TEXTO E MODO DE RENDERIZACAO IDENTICOS EM %d CASOS" % len(casos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
