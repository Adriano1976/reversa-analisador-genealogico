"""Curva de concorrencia do parse: N selecoes da MESMA arvore ao mesmo tempo.

Serve para separar duas perguntas que a sonda do item 3 junta:
  - o custo de reprocessar a arvore inteira por requisicao (medido em sequencia);
  - o que acontece com o processo quando varias abas pedem a mesma arvore juntas.

Tambem mede a latencia de uma pagina simples (GET /) disparada no meio da carga:
e a medida do "a aplicacao inteira para", e nao so "a requisicao demora".

Uso:
    python concorrencia.py <n> --porta 5099 --fixtures <dir> --referencia <nome armazenado>
"""
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sondas_http import enviar_formulario, pedir  # noqa: E402


def uma_rodada(porta, referencia, n):
    tempos = [None] * n
    latencia_da_pagina = []

    def trabalhador(indice):
        inicio = time.perf_counter()
        enviar_formulario(
            porta, {"action": "selecionar_arvore", "gedcom_filename": referencia})
        tempos[indice] = round(time.perf_counter() - inicio, 2)

    fios = [threading.Thread(target=trabalhador, args=(i,)) for i in range(n)]
    inicio = time.perf_counter()
    for fio in fios:
        fio.start()
    time.sleep(0.4)
    inicio_pagina = time.perf_counter()
    pedir(porta, "GET", "/")
    latencia_da_pagina.append(round(time.perf_counter() - inicio_pagina, 2))
    for fio in fios:
        fio.join()
    return {
        "n": n,
        "por_requisicao": tempos,
        "tempo_de_parede": round(time.perf_counter() - inicio, 2),
        "pagina_simples_durante_a_carga": latencia_da_pagina,
    }


def main():
    n = int(sys.argv[1])
    porta = int(sys.argv[sys.argv.index("--porta") + 1])
    fixtures = sys.argv[sys.argv.index("--fixtures") + 1]
    referencia = sys.argv[sys.argv.index("--referencia") + 1]
    saida = os.path.join(fixtures, f"concorrencia-{n}.json")
    resultado = uma_rodada(porta, referencia, n)
    with open(saida, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=2)
    print(json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    main()
