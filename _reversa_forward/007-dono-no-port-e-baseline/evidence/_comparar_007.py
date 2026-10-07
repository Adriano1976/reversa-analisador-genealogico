"""T012 — comparacao das 19 mensagens de tela contra a entrega da feature 006.

A sonda (`probe_mensagens.py`, copia byte a byte da que a feature 006 entregou)
roda os 19 casos contra o `app.py` ATUAL e grava `mensagens_depois.json`. O lado
"antes" desta comparacao nao e o `app.py` anterior a extracao da 006: e o
**resultado que a 006 registrou ao entregar**, preservado aqui como
`mensagens_baseline_006.json`.

Isso e o que a `RN-03` desta feature exige provar: **nenhuma mensagem visivel ao
operador muda**. A comparacao e de **status HTTP, classe do alerta e texto** —
comparar so o texto deixaria passar justamente a troca de modo de renderizacao que
a `D-11` da feature 006 existia para impedir.

Uso:

    .venv\\Scripts\\python.exe _comparar_007.py

Sai 0 quando os 19 casos batem, 1 em qualquer divergencia.
"""
from __future__ import annotations

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(AQUI, "mensagens_baseline_006.json")
ATUAL = os.path.join(AQUI, "mensagens_depois.json")
SAIDA = os.path.join(AQUI, "T012-mensagens.txt")

ESPERADO = 19


def carregar(caminho: str) -> list[dict]:
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def main() -> int:
    antes = carregar(BASELINE)
    depois = carregar(ATUAL)
    linhas: list[str] = []
    problemas: list[str] = []

    linhas.append(f"casos no baseline (entrega da 006): {len(antes)}")
    linhas.append(f"casos agora: {len(depois)}")
    linhas.append("")

    nomes_antes = [caso["caso"] for caso in antes]
    nomes_depois = [caso["caso"] for caso in depois]
    if nomes_antes != nomes_depois:
        problemas.append(
            f"a LISTA de casos mudou. so no baseline: "
            f"{sorted(set(nomes_antes) - set(nomes_depois))}; so agora: "
            f"{sorted(set(nomes_depois) - set(nomes_antes))}")
    if len(depois) != ESPERADO:
        problemas.append(f"a sonda rodou {len(depois)} casos, e o esperado sao {ESPERADO}")

    for antes_caso, depois_caso in zip(antes, depois):
        nome = antes_caso["caso"]
        divergencias = [
            campo for campo in ("status", "alerta", "mensagem")
            if antes_caso[campo] != depois_caso[campo]
        ]
        if divergencias:
            problemas.append(f"{nome}: diverge em {divergencias}")
            linhas.append(f"  DIVERGE {nome}")
            for campo in divergencias:
                linhas.append(f"    {campo}: 006={antes_caso[campo]!r}")
                linhas.append(f"    {campo}: ago={depois_caso[campo]!r}")
        else:
            linhas.append(
                f"  ok {nome}  status={depois_caso['status']} "
                f"alerta={depois_caso['alerta']}")

    # Guarda contra verde vacuo: zero caso comparado nao e conformidade.
    if not antes or not depois:
        problemas.append("a comparacao nao mediu nada: uma das listas esta vazia")

    linhas.append("")
    linhas.append("=" * 70)
    if problemas:
        linhas.append("RESULTADO: DIVERGENCIA")
        for problema in problemas:
            linhas.append(f"  - {problema}")
    else:
        linhas.append(
            f"RESULTADO: TEXTO E MODO DE RENDERIZACAO IDENTICOS EM {len(depois)} CASOS")
        linhas.append("  status HTTP, classe do alerta e texto, caso a caso")
    linhas.append("=" * 70)

    texto = "\n".join(linhas) + "\n"
    print(texto)
    with open(SAIDA, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
