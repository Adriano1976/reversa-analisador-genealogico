"""Linha de base: uma requisicao por vez, arvore pequena e arvore grande.

Separa o custo do parse do custo fixo da rota: se a arvore pequena responde em
milissegundos e a grande em segundos, o que domina e o reprocessamento do arquivo.

Uso: python linha_de_base.py --porta 5099 --pequena <ref> --grande <ref> [--repeticoes 3]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sondas_http import enviar_formulario, pedir  # noqa: E402


def medir(porta, referencia, repeticoes):
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        resposta = enviar_formulario(
            porta, {"action": "selecionar_arvore", "gedcom_filename": referencia})
        tempos.append(round(time.perf_counter() - inicio, 3))
        if resposta["status"] != 200:
            tempos[-1] = f"status {resposta['status']}"
    return tempos


def main():
    argumentos = sys.argv[1:]
    porta = int(argumentos[argumentos.index("--porta") + 1])
    pequena = argumentos[argumentos.index("--pequena") + 1]
    grande = argumentos[argumentos.index("--grande") + 1]
    repeticoes = int(argumentos[argumentos.index("--repeticoes") + 1]) \
        if "--repeticoes" in argumentos else 3

    saida = {
        "arvore_pequena": medir(porta, pequena, repeticoes),
        "arvore_grande": medir(porta, grande, repeticoes),
        "pagina_simples": [],
    }
    for _ in range(3):
        inicio = time.perf_counter()
        pedir(porta, "GET", "/")
        saida["pagina_simples"].append(round(time.perf_counter() - inicio, 3))
    print(json.dumps(saida, ensure_ascii=False))


if __name__ == "__main__":
    main()
