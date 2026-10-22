"""Mede as fases da analise de DNA com dados SINTETICOS, sem dado pessoal.

Uso:
    python medir_fases.py --pessoas 19403 --exatas 100 --pool 208 [--perfil]

O script inventa um GEDCOM e um CSV em um diretorio temporario do sistema, carrega
a arvore com o parser real, roda `core.dna_analysis.dna_analysis` com as mesmas
dependencias de borda que o `src/app.py` monta e imprime os tempos de cada fase.

Nenhum arquivo de `src/uploads/` e lido: o GEDCOM e o CSV sao gerados aqui. O
objetivo e localizar a fase que domina o tempo, nao reproduzir o dado do operador.
"""
from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import random
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
SRC = os.path.join(RAIZ, "src")
sys.path.insert(0, SRC)

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from parsers.csv_ingest import (  # noqa: E402
    aggregate_matches,
    detect_columns,
    read_csv_with_fallback,
)
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
    mermaid_da_sugestao,
)

ROOT = "Carlos Silva Souza"
CMA = ["Pai", "Mae", "Filho"]

# Sobrenomes com peso decrescente: o primeiro vira o pool grande do caso real.
SOBRENOMES = [
    ("Silva", 12), ("Souza", 9), ("Oliveira", 8), ("Santos", 7), ("Pereira", 6),
    ("Lima", 5), ("Costa", 4), ("Ferreira", 4), ("Almeida", 3), ("Nascimento", 3),
    ("Araujo", 3), ("Ribeiro", 2), ("Carvalho", 2), ("Gomes", 2), ("Martins", 2),
    ("Rocha", 2), ("Barbosa", 1), ("Alves", 1), ("Monteiro", 1), ("Mendes", 1),
    ("Barros", 1), ("Freitas", 1), ("Cardoso", 1), ("Ramos", 1), ("Goncalves", 1),
    ("Pinto", 1), ("Moreira", 1), ("Teixeira", 1), ("Vieira", 1), ("Correia", 1),
]


def _indi(xref, nome, sexo, fams, famc):
    linhas = [f"0 @{xref}@ INDI", f"1 NAME {nome}", f"1 SEX {sexo}"]
    if fams:
        linhas.append(f"1 FAMS @{fams[0]}@")
    for f in famc:
        linhas.append(f"1 FAMC @{f}@")
    return "\n".join(linhas) + "\n"


def _fam(xref, husb, wife, filhos):
    linhas = [f"0 @{xref}@ FAM", f"1 HUSB @{husb}@", f"1 WIFE @{wife}@"]
    for c in filhos:
        linhas.append(f"1 CHIL @{c}@")
    return "\n".join(linhas) + "\n"


def gerar_arvore(pessoas, semente=42):
    """Arvore no formato de familias de cinco, com sobrenomes ponderados.

    A familia 0 e a raiz (Carlos Silva Souza). As demais recebem um sobrenome
    sorteado com peso, o que produz um pool grande para "Silva" e pools menores
    para o resto, como no GEDCOM real.
    """
    rng = random.Random(semente)
    nomes, pesos = zip(*SOBRENOMES)
    partes = ["0 HEAD\n1 SOUR sonda-desempenho\n1 GEDC\n2 VERS 5.5.1\n"
              "2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n"]
    partes.append(_indi("I1", "Carlos /Silva Souza/", "M", ["F0"], []))
    partes.append(_indi("I2", "Ana /Souza/", "F", ["F0"], []))
    filhos0 = ["I3", "I4", "I5"]
    for xref in filhos0:
        partes.append(_indi(xref, f"{CMA[2]}{xref} /Silva Souza/", "U", [], ["F0"]))
    partes.append(_fam("F0", "I1", "I2", filhos0))

    nomes_reais = ["Carlos Silva Souza"]
    xref = 6
    fam = 1
    while xref <= pessoas:
        sobrenome = rng.choices(nomes, weights=pesos, k=1)[0]
        pai, mae = f"I{xref}", f"I{xref + 1}"
        filhos = [f"I{xref + 2}", f"I{xref + 3}", f"I{xref + 4}"]
        partes.append(_indi(pai, f"Pai{fam} /{sobrenome}/", "M", [f"F{fam}"], []))
        partes.append(_indi(mae, f"Mae{fam} /{sobrenome}/", "F", [f"F{fam}"], []))
        for filho in filhos:
            partes.append(_indi(filho, f"Filho{fam} /{sobrenome}/", "U", [],
                                [f"F{fam}"]))
        partes.append(_fam(f"F{fam}", pai, mae, filhos))
        nomes_reais.append(f"Pai{fam} {sobrenome}")
        nomes_reais.append(f"Mae{fam} {sobrenome}")
        nomes_reais.extend(f"Filho{fam} {sobrenome}" for _ in filhos)
        xref += 5
        fam += 1
    partes.append("0 TRLR\n")
    return "".join(partes), nomes_reais


def gerar_csv(nomes_reais, exatas, pool, semente=7):
    """CSV no formato do GEDmatch: `Name,cM`.

    `exatas` linhas usam nomes que EXISTEM na arvore (casamento exato, cartao
    completo). `pool` linhas usam nome inexistente com sobrenome comum: elas
    percorrem o pool inteiro do sobrenome, que e o custo por linha.
    """
    rng = random.Random(semente)
    linhas = ["Name,cM", f"{ROOT},120.0"]
    passo = max(1, len(nomes_reais) // max(1, exatas))
    escolhidos = nomes_reais[1::passo][:exatas]
    for nome in escolhidos:
        linhas.append(f"{nome},{rng.choice([25.0, 40.0, 75.0, 120.0])}")
    sobrenomes_pool = [n for n, _p in SOBRENOMES[:6]]
    for k in range(pool):
        sobrenome = rng.choice(sobrenomes_pool)
        linhas.append(f"Candidato{k} {sobrenome},{20 + (k % 15)}.5")
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pessoas", type=int, default=19403)
    ap.add_argument("--exatas", type=int, default=100)
    ap.add_argument("--pool", type=int, default=208)
    ap.add_argument("--perfil", action="store_true")
    args = ap.parse_args()

    # O sandbox do harness bloqueia criacao de diretorio por processo; os arquivos
    # vao direto para a raiz do temporario do sistema, com nome unico por processo.
    pasta = tempfile.gettempdir()
    ged = os.path.join(pasta, f"desempenho_arvore_{os.getpid()}.ged")
    csv = os.path.join(pasta, f"desempenho_matches_{os.getpid()}.csv")
    conteudo, nomes_reais = gerar_arvore(args.pessoas)
    with open(ged, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(conteudo)
    with open(csv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(gerar_csv(nomes_reais, args.exatas, args.pool))

    inicio = time.perf_counter()
    arvore = carregar_arvore(ged)
    t_parse = time.perf_counter() - inicio

    deps = Dependencias(
        read_csv_with_fallback, detect_columns, aggregate_matches,
        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
        anotar_profundidade, mermaid_da_sugestao,
    )
    inicio = time.perf_counter()
    if args.perfil:
        perfil = cProfile.Profile()
        perfil.enable()
        resultados, descartados, mensagem = dna_analysis(csv, ROOT, deps, arvore)
        perfil.disable()
    else:
        resultados, descartados, mensagem = dna_analysis(csv, ROOT, deps, arvore)
    t_analise = time.perf_counter() - inicio

    print(f"pasta: {pasta}")
    print(f"pessoas: {len(arvore[0])}  familias: {len(arvore[1])}  "
          f"linhas CSV: {args.exatas + args.pool + 1}")
    print(f"parse: {t_parse:.2f} s")
    print(f"analise: {t_analise:.2f} s")
    print(f"total: {t_parse + t_analise:.2f} s")
    print(f"resultados: {len(resultados)}  descartados: {len(descartados)}")
    print(f"mensagem: {mensagem}")

    if args.perfil:
        saida = io.StringIO()
        pstats.Stats(perfil, stream=saida).sort_stats("cumtime").print_stats(30)
        print(saida.getvalue())


if __name__ == "__main__":
    main()
