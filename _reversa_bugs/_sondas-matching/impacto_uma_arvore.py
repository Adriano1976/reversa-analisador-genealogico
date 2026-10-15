"""Uma arvore por PROCESSO — porque o cache de indice nao distingue as duas.

`core.documentary_relationship._indice_por_nome` guarda o mapa nome->ids em variavel de
modulo e o invalida por `(len(people), primeiro xref, ultimo xref)`. As duas versoes desta
arvore tem 35.460 pessoas e os MESMOS xrefs — so' os nomes mudaram. A chave e' igual, o cache
nao invalida, e a segunda medicao no mesmo processo le o indice da PRIMEIRA.

Por isso este script mede UMA arvore e sai. Rodar duas vezes, uma por arvore, e comparar os
arquivos depois.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\impacto_uma_arvore.py <ged> <saida.json>
"""

import collections
import json
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import homonym_dossier  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

CSV = os.path.join(R, "src", "uploads", "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ = "Adriano Santos"


def main():
    ged, saida = sys.argv[1], sys.argv[2]
    arvore = carregar_arvore(ged)
    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar_profundidade)
    resultados, descartados, _msg = dna_analysis(
        CSV, RAIZ, deps, arvore, observacoes_do_arquivo=[])

    resumo = {
        "ged": os.path.basename(ged),
        "pessoas": len(arvore[0]),
        "cartoes": len(resultados),
        "descartados": len(descartados),
        "por_estado": {},
        "cartoes_detalhe": [],
        "motivos_de_descarte": collections.Counter(d.get("motivo") for d in descartados).most_common(),
    }
    for campo in ("identidade", "janela_de_vida", "profundidade", "confrontacao_efetiva"):
        resumo["por_estado"][campo] = dict(collections.Counter(
            str(r.get(campo)) for r in resultados))
    resumo["por_estado"]["documental"] = dict(collections.Counter(
        str((r.get("documentary") or {}).get("status")) for r in resultados))
    for r in resultados:
        resumo["cartoes_detalhe"].append({
            "csv_name": r.get("csv_name"),
            "kit": str(r.get("kit")),
            "pessoa": ((r.get("documentary") or {}).get("person_b") or {}).get("id"),
            "identidade": str(r.get("identidade")),
            "estado": str(r.get("confrontacao_efetiva")),
        })

    # A contagem de candidatos exatos para os nomes que o CSV pede — medida AQUI, com o
    # indice desta arvore, e nao de outra.
    df = read_csv_with_fallback(CSV)
    nomes = sorted({str(n) for n in df["Name"].dropna()})
    resumo["candidatos_por_nome"] = {n: homonym_dossier(arvore, n)["exact_count"]
                                     for n in nomes if homonym_dossier(arvore, n)["exact_count"]}
    resumo["candidatos_soma"] = sum(resumo["candidatos_por_nome"].values())

    with open(saida, "w", encoding="utf-8") as fh:
        json.dump(resumo, fh, ensure_ascii=False, indent=1)
    print(f"{os.path.basename(ged)}: cartoes={resumo['cartoes']} "
          f"descartados={resumo['descartados']} candidatos={resumo['candidatos_soma']}")
    print(f"  -> {saida}")


if __name__ == "__main__":
    main()
