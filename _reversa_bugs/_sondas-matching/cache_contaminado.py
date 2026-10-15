"""O caso contaminado: o indice da arvore ANTERIOR servindo a analise da TRATADA.

A chave do cache e' `(len(people), primeiro xref, ultimo xref)`. As duas versoes desta arvore
tem 35.460 pessoas e os mesmos xrefs — a chave e' IDENTICA. Quem consultar primeiro manda: o
indice de uma serve a outra, em qualquer ordem.

Este script constroi o indice a partir da arvore ANTERIOR e, em seguida, roda a analise na
TRATADA — que e' o que acontece na aplicacao quando o operador analisa uma arvore e depois a
outra, no mesmo processo.

Compara com o resultado LIMPO da tratada (medido em processo proprio):
  cartoes=90  identidade={confirmada: 54, a_confirmar: 12, grafia: 24}  documental_ambiguo=7

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\cache_contaminado.py
"""

import collections
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

P = os.path.join(R, "src", "uploads")
ANTES = os.path.join(P, "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
TRATADO = os.path.join(P, "e10c087ae4973fc9__Arvore_Unificada_Oficial_V1_2_Tratado.ged")
CSV = os.path.join(P, "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ = "Adriano Santos"

LIMPO = {"cartoes": 90, "identidade": {"confirmada": 54, "a_confirmar": 12, "grafia": 24},
         "documental_ambiguo": 7}


def main():
    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar_profundidade)

    # 1. PRIMEIRA consulta do processo: a arvore ANTERIOR. E' ela que enche o cache.
    antes = carregar_arvore(ANTES)
    quantos = homonym_dossier(antes, "Margarida")["exact_count"]
    print(f"1. indice construido a partir da arvore ANTERIOR: "
          f"dossier('Margarida') = {quantos}  (correto para ela)")

    # 2. Agora a TRATADA, no mesmo processo — e o cache NAO invalida.
    tratado = carregar_arvore(TRATADO)
    contaminado = homonym_dossier(tratado, "Margarida")["exact_count"]
    print(f"2. mesma consulta na TRATADA, mesmo processo:     "
          f"dossier('Margarida') = {contaminado}  (o certo seria 0)")

    # 3. A analise na tratada, com o cache contaminado.
    resultados, _d, _m = dna_analysis(CSV, RAIZ, deps, tratado, observacoes_do_arquivo=[])
    estados = dict(collections.Counter(str(r.get("identidade")) for r in resultados))
    ambiguos = sum(1 for r in resultados
                   if (r.get("documentary") or {}).get("ambiguous_identity"))
    print(f"\n3. analise na TRATADA com o cache contaminado:")
    print(f"     cartoes = {len(resultados)}   identidade = {estados}")
    print(f"     documental_ambiguo = {ambiguos}")
    print(f"\n   resultado LIMPO, medido em processo proprio:")
    print(f"     cartoes = {LIMPO['cartoes']}   identidade = {LIMPO['identidade']}")
    print(f"     documental_ambiguo = {LIMPO['documental_ambiguo']}")

    print("\n" + "=" * 100)
    if len(resultados) == LIMPO["cartoes"] and estados == LIMPO["identidade"] \
            and ambiguos == LIMPO["documental_ambiguo"]:
        print("VEREDITO: o cache errado NAO mudou o que o operador ve.")
        print("  Ele muda o dossier de homonimos, e neste arquivo o dossier nao chega a")
        print("  alterar veredito de cartao nenhum — mas o valor esta' errado.")
    else:
        print("VEREDITO: o cache errado MUDA o resultado do operador.")


if __name__ == "__main__":
    main()
