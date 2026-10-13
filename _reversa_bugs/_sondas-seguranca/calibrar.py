"""Calibracao local (sem HTTP): tamanho das fixtures, tempo de parse e custo da analise.

Roda no interpretador oficial do repositorio (`.venv`), com `src/` no `sys.path`,
e mede:
  1. o parse do GEDCOM grande (item 3, custo por requisicao);
  2. o custo da analise de DNA em funcao de (linhas do CSV) x (tamanho do pool de
     sobrenomes) (item 4).

Nao escreve nada no projeto: so le as fixtures do scratch e imprime JSON.
"""
import json
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from parsers.csv_ingest import (  # noqa: E402
    aggregate_matches,
    detect_columns,
    read_csv_with_fallback,
)
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

DEPS = Dependencias(
    read_csv_with_fallback,
    detect_columns,
    aggregate_matches,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)


def cronometrar(rotulo, funcao):
    inicio = time.perf_counter()
    resultado = funcao()
    decorrido = time.perf_counter() - inicio
    print(f"{rotulo}\t{decorrido:.2f}s", flush=True)
    return decorrido, resultado


def main(fixtures):
    def caminho(nome):
        return os.path.join(fixtures, nome)

    saida = {"parse": {}, "dna": {}}

    arvore_pequena = carregar_arvore(caminho("arvore_valida.ged"))
    nomes = [p.name.format() for p in arvore_pequena[0].values() if p.name]
    saida["arvore_valida"] = {"pessoas": len(arvore_pequena[0]), "nomes": nomes}

    tempo, arvore_grande = cronometrar(
        "parse arvore_grande_15000",
        lambda: carregar_arvore(caminho("arvore_grande_15000.ged")))
    saida["parse"]["arvore_grande_15000"] = {
        "segundos": round(tempo, 2),
        "pessoas": len(arvore_grande[0]),
        "bytes": os.path.getsize(caminho("arvore_grande_15000.ged")),
    }

    arvore_p150 = carregar_arvore(caminho("arvore_pool150.ged"))
    arvore_p600 = carregar_arvore(caminho("arvore_pool600.ged"))
    saida["pools"] = {"pool150": len(arvore_p150[0]), "pool600": len(arvore_p600[0])}

    matriz = [
        ("pool600_r24", arvore_p600, "matches_r24.csv"),
        ("pool600_r199", arvore_p600, "matches_r199.csv"),
        ("pool150_r49", arvore_p150, "matches_r49.csv"),
        ("pool600_r49", arvore_p600, "matches_r49.csv"),
    ]
    for rotulo, arvore, csv in matriz:
        tempo, resultado = cronometrar(
            f"dna {rotulo}",
            lambda a=arvore, c=csv: dna_analysis(caminho(c), "Carlos Silva Souza", DEPS, a))
        resultados, descartados, _mensagem = resultado
        saida["dna"][rotulo] = {
            "segundos": round(tempo, 2),
            "csv": csv,
            "resultados": len(resultados),
            "descartados": len(descartados),
            "com_caminho": sum(1 for r in resultados if (r["documentary"].get("path") or {}).get("ids")),
        }

    print(json.dumps(saida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
