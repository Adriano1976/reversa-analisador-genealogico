"""Mede o CUSTO da gravacao na analise (`T026`, RNF de Desempenho).

Roda **dentro do conteiner**, onde o driver existe. Mede a mesma analise duas
vezes — com a persistencia desabilitada (`registro=None`, o estado da `D-02`) e
habilitada — e compara.

**Criterio:** o tempo com persistencia tem de ficar **abaixo do dobro** do tempo
sem ela. E o que o RNF de Desempenho pede ("a gravacao nao pode dobrar o tempo da
analise"), e o `roadmap.md` §10 registra o item.

Cinco execucoes de cada lado, e vale a **menor** — a mediana e a media carregam o
ruido das outras threads e do proprio PostgreSQL subindo pagina de cache. A menor
e a que mais se aproxima do custo do trabalho, e nao do custo do ambiente.

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

ARVORE = "/tmp/e2e/arvore.ged"
CSV = "/tmp/e2e/matches_dois_kits.csv"
RAIZ = "Carlos Silva Souza"
REF = "medicao-t026__arvore.ged"
EXECUCOES = 5

DEPS = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)


def medir(registro):
    tempos = []
    for _ in range(EXECUCOES):
        inicio = time.perf_counter()
        caso_de_uso(CSV, RAIZ, ARVORE_CARREGADA, DEPS, "unico", REF, registro)
        tempos.append(time.perf_counter() - inicio)
    return min(tempos), sum(tempos) / len(tempos)


def limpar():
    import psycopg2
    con = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with con:
            with con.cursor() as cur:
                cur.execute("DELETE FROM dna_analysis WHERE tree_ref = %s", (REF,))
    finally:
        con.close()


ARVORE_CARREGADA = carregar_arvore(ARVORE)
limpar()

sem_min, sem_media = medir(None)
com_min, com_media = medir(RegistroDeAnalisesPostgres(os.environ["DATABASE_URL"]))

gravadas = None
import psycopg2  # noqa: E402
con = psycopg2.connect(os.environ["DATABASE_URL"])
try:
    with con.cursor() as cur:
        cur.execute("SELECT count(*) FROM dna_analysis WHERE tree_ref = %s", (REF,))
        gravadas = cur.fetchone()[0]
finally:
    con.close()
limpar()

razao = com_min / sem_min if sem_min else float("inf")
print("execucoes por lado      : %d" % EXECUCOES)
print("sem persistencia (menor): %.4f s   (media %.4f s)" % (sem_min, sem_media))
print("com persistencia (menor): %.4f s   (media %.4f s)" % (com_min, com_media))
print("razao                   : %.2fx" % razao)
print("analises gravadas       : %d  (esperado: %d)" % (gravadas, EXECUCOES))
print("CRITERIO (< 2.00x)      : %s" % ("PASS" if razao < 2.0 else "FAIL"))
