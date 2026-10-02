"""Caracteriza a saida do render de ponte, antes de qualquer simplificacao.

O risco desta transformacao nao e comportamental, e visual: o diagrama e o produto,
e um `end` a mais ou uma ordem trocada produz um diagrama diferente sem falhar
nenhum teste que so verifique "nao vazio". Esta caracterizacao fecha esse buraco
congelando a saida EXATA de cada caso.

Duas frentes:

  A. `path_search(nome1, nome2)` para todos os pares de cada fixture de GEDCOM.
     Cobre o roteamento: conexao direta, ponte por afinidade e sem conexao.
  B. `generate_mermaid_graph_indirect_bridge` chamada DIRETO, para todo par que
     tenha caminho indireto. Isso exercita a funcao alvo muitas vezes, e nao so
     nos casos em que o roteamento escolhe a ponte.

Para cada caso guarda o sha256 da saida. O digest de todos os digests resume a
caracterizacao numa linha, que e o que se compara antes e depois.

Saida: before-after/caracterizacao-<rotulo>.txt (tabela) e .json (corpus completo).

Aceita o pacote a caracterizar como primeiro argumento, para que o ensaio possa
rodar exatamente este mesmo codigo contra um pacote espelho:

    python caracterizar.py                                  # pacote real, rotulo "antes"
    python caracterizar.py <caminho-do-pacote> <rotulo>
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", "..", ".."))
FIXTURES = os.path.join(ROOT, "_reversa_sdd", "parity", "fixtures", "gedcom")
SCRATCH = os.path.join(ROOT, ".pytest-tmp", "h2yy-carac")
AMPLEA = 10           # fixtures com ate N pessoas: todos os pares
AMOSTRA_GRANDE = 60   # fixtures maiores: pares amostrados, com semente fixa
SEED = 20261001

PKG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "analisador-genealogico")
ROTULO = sys.argv[2] if len(sys.argv) > 2 else "antes"

sys.path.insert(0, PKG)


def sha(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    os.makedirs(SCRATCH, exist_ok=True)
    from reconstructed import upload as U
    from reconstructed import path_search as P
    from reconstructed import mermaid_render as R

    rnd = random.Random(SEED)
    corpus = []
    linhas = []
    linhas.append("CARACTERIZACAO DA SAIDA DO RENDER DE PONTE (OPP-20260929-H2YY)")
    linhas.append("=" * 78)

    for nome_arq in sorted(f for f in os.listdir(FIXTURES) if f.endswith(".ged")):
        caminho = os.path.join(FIXTURES, nome_arq)
        U.load_gedcom_and_build_graph(caminho)
        ids = sorted(U.people)
        nomes = {i: U.get_name(U.people[i]) for i in ids}
        pares = [(a, b) for a in ids for b in ids if a != b]
        if len(ids) > AMPLEA:
            pares = rnd.sample(pares, min(AMOSTRA_GRANDE, len(pares)))

        n_fluxo = n_ponte_direta = n_com_ponte = 0
        for a, b in pares:
            try:
                res, msg, ok = P.path_search(nomes[a], nomes[b])
            except Exception as e:
                corpus.append({"fx": nome_arq, "via": "fluxo", "a": a, "b": b,
                               "sha": sha("EXCECAO:" + type(e).__name__)})
                continue
            saida = json.dumps([res, msg, ok], ensure_ascii=False, sort_keys=True)
            corpus.append({"fx": nome_arq, "via": "fluxo", "a": a, "b": b, "sha": sha(saida)})
            n_fluxo += 1
            if isinstance(msg, str) and "indireta" in msg:
                n_com_ponte += 1

            cam = P.find_indirect_path(a, b)
            if cam:
                try:
                    m = R.generate_mermaid_graph_indirect_bridge(a, b, cam)
                except Exception as e:
                    m = "EXCECAO:" + type(e).__name__
                corpus.append({"fx": nome_arq, "via": "ponte_direta", "a": a, "b": b,
                               "sha": sha(m)})
                n_ponte_direta += 1

        linhas.append("")
        linhas.append("%-24s %2d pessoas  %3d pares" % (nome_arq, len(ids), len(pares)))
        linhas.append("   fluxo completo      : %3d casos" % n_fluxo)
        linhas.append("   ... com ponte       : %3d casos" % n_com_ponte)
        linhas.append("   ponte chamada direto: %3d casos" % n_ponte_direta)

    digest = hashlib.sha256(
        "\n".join(sorted(c["fx"] + c["via"] + c["a"] + c["b"] + c["sha"] for c in corpus)
                  ).encode("utf-8")).hexdigest()

    linhas.append("")
    linhas.append("=" * 78)
    linhas.append("casos no corpus      : %d" % len(corpus))
    linhas.append("digest da caracterizacao : %s" % digest)
    linhas.append("")
    linhas.append("O digest e o que se compara antes e depois. Se ele bate, todas as")
    linhas.append("saidas sao identicas caso a caso, e nao apenas 'nao vazias'.")

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "caracterizacao-" + ROTULO)
    with open(base + ".txt", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(linhas) + "\n")
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(corpus, fh, ensure_ascii=False, sort_keys=True)
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
