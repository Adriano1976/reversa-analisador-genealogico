"""Le os quatro numeros dentro de cada motivo "score insuficiente" e checa a redacao.

A mensagem acusa DUAS causas possiveis: "score insuficiente OU conflito de sobrenome".
Este script mede, sobre os descartes reais de uma analise, quantas vezes cada uma das
duas e' literalmente verdadeira — e quantas vezes NENHUMA das duas descreve a causa.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\motivo_numeros.py <resumo.json>
"""

import collections
import json
import re
import sys

PAT = re.compile(r"given=(\d+), final=([\d.]+), inter=(\d+)/(\d+), jacc=([\d.]+)")


def main():
    resumo = json.load(open(sys.argv[1], encoding="utf-8"))
    linhas = []
    for motivo, n in resumo["motivos_de_descarte"]:
        m = PAT.search(motivo or "")
        if m:
            g = int(m.group(1))
            fin = float(m.group(2))
            i = int(m.group(3))
            req = int(m.group(4))
            j = float(m.group(5))
            linhas.append((g, fin, i, req, j, n))

    tot = sum(L[5] for L in linhas)
    print(f"descartes com o motivo detalhado: {len(linhas)} textos distintos, {tot} descartes")
    print()

    def pct(k):
        return f"{k * 100 / tot:5.1f}%  ({k})"

    inter_ok = sum(n for g, f, i, req, j, n in linhas if i >= req)
    jacc_ok = sum(n for g, f, i, req, j, n in linhas if j >= 0.80)
    both_ok = sum(n for g, f, i, req, j, n in linhas if i >= req and j >= 0.80)

    print("o sobrenome, que a mensagem acusa:")
    print(f"  cumpriu o minimo de intersecao (inter>=req): {pct(inter_ok)}")
    print(f"  jacc>=0.80 (sobrenome quase igual)         : {pct(jacc_ok)}")
    print(f"  as duas coisas (sobrenome PERFEITO)        : {pct(both_ok)}")
    print("     -> nesses, 'conflito de sobrenome' e' falso: a causa e' so' o score")
    print()

    fin = sorted(f for g, f, i, req, j, n in linhas for _ in range(n))
    giv = sorted(g for g, f, i, req, j, n in linhas for _ in range(n))
    print(f"final (score composto): min={fin[0]}  mediana={fin[len(fin) // 2]}  max={fin[-1]}")
    print(f"given (similaridade do prenome): min={giv[0]}  mediana={giv[len(giv) // 2]}  max={giv[-1]}")
    print(f"  given>=85 (exigido pelo ramo 2): {pct(sum(n for g, f, i, req, j, n in linhas if g >= 85))}")
    print(f"  given>=90 (exigido pelos ramos 4 e 6): {pct(sum(n for g, f, i, req, j, n in linhas if g >= 90))}")
    print()

    req2 = collections.Counter(req for g, f, i, req, j, n in linhas for _ in range(n))
    print(f"required_intersection exigido: {dict(req2)}")
    print()

    # O teto de score alcancavel so' mexendo no prenome: dado=100 devolve 0.20*100 = 20.
    # Score atual menos a parcela do given mais 20 = teto.
    impossivel = 0
    for g, f, i, req, j, n in linhas:
        teto = round(f - 0.20 * g + 20.0, 2)
        if teto < 86:
            impossivel += n
    print(f"descartes em que NENHUM prenome salvaria o ramo 3 (teto<86 trocando so' o prenome): {pct(impossivel)}")


if __name__ == "__main__":
    main()
