"""Mede o CUSTO da gravacao na analise (`T026`, RNF de Desempenho).

Roda **dentro do conteiner**, onde o driver existe. Mede a mesma analise duas vezes —
com a persistencia desabilitada (`registro=None`, o estado da `D-02`) e habilitada — e
compara, em **tres escalas de fixture**:

| Rotulo   | Arvore     | Matches |
|----------|------------|---------|
| `pequena`| 5 pessoas  | 2       |
| `media`  | 728        | 21      |
| `grande` | 19.682     | 71      |

A escala `grande` existe porque o criterio do RNF fala da **analise real** (71 conexoes
sobre 35.460 pessoas), e o Principio I proibe medir com o dado real. Uma arvore sintetica
do mesmo porte nao e o dado real — e o substituto que torna o criterio mensuravel.

**Criterio:** o tempo com persistencia tem de ficar **abaixo do dobro** do tempo sem ela.

Rodado como:  docker compose exec -T app python /tmp/medir_custo.py
"""
import os
import sys
import time

sys.path.insert(0, "/app/src")

from application.dna_analysis import dna_analysis as caso_de_uso  # noqa: E402
from core.dna_analysis import Dependencias  # noqa: E402
from parsers.csv_ingest import (  # noqa: E402
    aggregate_matches,
    detect_columns,
    read_csv_with_fallback,
)
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from ports.adaptadores import RegistroDeAnalisesPostgres  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

E2E = "/tmp/e2e"
DEPS = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)

# (rotulo, gedcom, csv, raiz, execucoes). A raiz entra por cenario porque o fixture
# pequeno e o de `tests/fixtures/sample_dna.py`, com outra pessoa como raiz.
CENARIOS = (
    ("pequena", "arvore.ged", "matches_dois_kits.csv", "Carlos Silva Souza", 5),
    ("media", "arvore_media.ged", "matches_media.csv", "Raiz Queiroz", 3),
    ("grande", "arvore_grande.ged", "matches_grande.csv", "Raiz Queiroz", 2),
)


def limpar(ref):
    import psycopg2
    con = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with con:
            with con.cursor() as cur:
                cur.execute("DELETE FROM dna_analysis WHERE tree_ref = %s", (ref,))
    finally:
        con.close()


def medir(rotulo, ged, csv, raiz, execucoes):
    ref = "t026-%s__arvore.ged" % rotulo
    arvore = carregar_arvore(os.path.join(E2E, ged))
    caminho_csv = os.path.join(E2E, csv)
    limpar(ref)

    def rodar(registro):
        tempos = []
        for _ in range(execucoes):
            inicio = time.perf_counter()
            resultado = caso_de_uso(caminho_csv, raiz, arvore, DEPS, "unico", ref, registro)
            tempos.append(time.perf_counter() - inicio)
        return min(tempos), resultado

    sem, resultado = rodar(None)
    registro = RegistroDeAnalisesPostgres(os.environ["DATABASE_URL"])
    com, _ = rodar(registro)

    import psycopg2
    con = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with con.cursor() as cur:
            cur.execute("SELECT count(*) FROM match_result m JOIN dna_analysis a USING "
                        "(analysis_id) WHERE a.tree_ref = %s", (ref,))
            conexoes = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM match_kit k JOIN match_result m USING "
                        "(match_id) JOIN dna_analysis a USING (analysis_id) "
                        "WHERE a.tree_ref = %s", (ref,))
            kits = cur.fetchone()[0]
    finally:
        con.close()
    limpar(ref)

    razao = com / sem if sem else float("inf")
    print("%-8s n=%-2d | sem %7.1f ms | com %7.1f ms | delta %6.1f ms | razao %5.2fx | "
          "conexoes %2d kits %2d | %s"
          % (rotulo, execucoes, sem * 1000, com * 1000, (com - sem) * 1000, razao,
             conexoes, kits, "PASS" if razao < 2.0 else "FAIL"))
    return razao


print("criterio do RNF: razao < 2.00x")
print()
for rotulo, ged, csv, raiz, execucoes in CENARIOS:
    medir(rotulo, ged, csv, raiz, execucoes)
