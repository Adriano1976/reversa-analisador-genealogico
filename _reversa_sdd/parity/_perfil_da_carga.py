"""Perfil de tempo da CARGA da arvore e da ANALISE DE DNA — codigo de PRODUCAO.

## Por que este arquivo existe, ao lado de `_profile_big.py`

`_profile_big.py` mede o **oraculo congelado**: ele copia
`_reversa_sdd/oracle/app_legacy_e43ca22.py` para uma pasta temporaria e chama
`load_gedcom_and_build_graph` do legado. Aquilo e a regua da paridade, e nao pode
mudar. Este aqui mede o **codigo que roda hoje** — `parsers.gedcom_parser.carregar_arvore`
e `application.dna_analysis.dna_analysis` — e conta as chamadas ao `ged4py`.

## O que ele mede (feature 025)

1. **Carga da arvore**: 1 aquecimento descartado + N repeticoes, cada uma em
   **processo proprio**. A medicao de uma execucao unica nao serve: a mesma carga
   ja variou 23 % dentro do mesmo processo, e a primeira execucao de um processo
   novo chegou a quase o dobro da mediana (cache frio do sistema de arquivos).
2. **Contagem de chamadas do parser**: `records0` por tag, acessos a `index0`,
   execucoes de `_init_index` e `read_record`. E o que separa "indexacao repetida"
   (que NAO acontece: `index0` e propriedade com cache) de "materializacao
   repetida" (que acontece: `FAM` e lido duas vezes).
3. **Analise de DNA**: uma execucao por rodada, declarada como tal. Ela custa
   ~54 s, nao e alvo da mudanca e nao precisa de mediana.

## Isolamento

Importar `app` cria as pastas de upload resolvidas no arquivo do app. Para nao
deixar residuo na pasta real do operador, os filhos recebem
`ANALISADOR_UPLOAD_FOLDER` apontando para `.parity-tmp/uploads` — o mesmo
mecanismo de `tests/rodar_paridade.py`.

## Uso

    .venv\\Scripts\\python.exe _reversa_sdd\\parity\\_perfil_da_carga.py --repeticoes 3

Sem `--gedcom`/`--csv`, usa o par oficial da feature 025. Nenhuma saida contem
nome de pessoa, xref ou valor de cM.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "src")
PASTA_ISOLADA = os.path.join(RAIZ, ".parity-tmp", "uploads")

GED_PADRAO = os.path.join(SRC, "uploads",
                          "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
CSV_PADRAO = os.path.join(SRC, "uploads",
                          "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ_PADRAO = "Adriano Santos"


# ---------------------------------------------------------------------------
# Contadores. O patch e no atributo da CLASSE, entao alcanca o `GedcomReader`
# importado em qualquer modulo — inclusive o que `gedcom_parser` ja importou.
# ---------------------------------------------------------------------------

def _instalar_contadores() -> dict:
    from ged4py.parser import GedcomReader

    cont = {"records0": {}, "index0": 0, "init_index": 0, "read_record": 0}

    leitura_index0 = GedcomReader.index0.fget

    def index0(self):
        cont["index0"] += 1
        return leitura_index0(self)

    GedcomReader.index0 = property(index0)

    init_index = GedcomReader._init_index

    def _init_index(self):
        cont["init_index"] += 1
        return init_index(self)

    GedcomReader._init_index = _init_index

    records0 = GedcomReader.records0

    def records0_contando(self, tag=None):
        cont["records0"][tag] = cont["records0"].get(tag, 0) + 1
        return records0(self, tag)

    GedcomReader.records0 = records0_contando

    read_record = GedcomReader.read_record

    def read_record_contando(self, *args, **kwargs):
        cont["read_record"] += 1
        return read_record(self, *args, **kwargs)

    GedcomReader.read_record = read_record_contando
    return cont


def _coletor(modo: str, ged: str, csv: str, raiz: str) -> int:
    """Roda UM modo em processo proprio e imprime uma linha `JSON {...}`."""
    sys.path.insert(0, SRC)
    cont = _instalar_contadores()

    from parsers.gedcom_parser import carregar_arvore

    if modo == "carga":
        inicio = time.perf_counter()
        arvore = carregar_arvore(ged)
        tempo = time.perf_counter() - inicio
        people, families, graph, _c2f = arvore
        dados = {
            "modo": "carga",
            "tempo": tempo,
            "pessoas": len(people),
            "familias": len(families),
            "nos": graph.number_of_nodes(),
            "arestas": graph.number_of_edges(),
            "records0": cont["records0"],
            "index0": cont["index0"],
            "init_index": cont["init_index"],
            "read_record": cont["read_record"],
        }
    else:
        arvore = carregar_arvore(ged)  # fora do cronometro: medido no modo "carga"
        from application.dna_analysis import dna_analysis
        import app

        inicio = time.perf_counter()
        resultado = dna_analysis(csv, raiz, arvore, app._DEPENDENCIAS,
                                "dono-local", None, None)
        tempo = time.perf_counter() - inicio
        dados = {
            "modo": "dna",
            "tempo": tempo,
            "cartoes": len(resultado.resultados),
            "descartados": len(resultado.descartados),
        }

    print("JSON " + json.dumps(dados, ensure_ascii=False), flush=True)
    return 0


# ---------------------------------------------------------------------------

def _rodar_filho(modo: str, ged: str, csv: str, raiz: str, ambiente: dict) -> dict:
    comando = [sys.executable, os.path.abspath(__file__), "--coletor", modo,
               "--gedcom", ged, "--csv", csv, "--raiz", raiz]
    saida = subprocess.run(comando, env=ambiente, capture_output=True, text=True,
                           encoding="utf-8")
    if saida.returncode != 0:
        sys.stderr.write(saida.stdout or "")
        sys.stderr.write(saida.stderr or "")
        raise SystemExit("coletor falhou (modo %s, exit %d)" % (modo, saida.returncode))
    for linha in reversed((saida.stdout or "").splitlines()):
        if linha.startswith("JSON "):
            return json.loads(linha[5:])
    raise SystemExit("coletor nao devolveu JSON (modo %s)" % modo)


def _tabela(rotulo: str, tempos: list) -> None:
    mediana = statistics.median(tempos)
    variacao = 100 * (max(tempos) - min(tempos)) / min(tempos) if min(tempos) else 0.0
    print("%-28s %s" % (rotulo + " (s)",
                        " / ".join("%.2f" % t for t in tempos)))
    print("%-28s mediana=%.2f  min=%.2f  max=%.2f  variacao=%.0f%%"
          % ("", mediana, min(tempos), max(tempos), variacao))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Perfil da carga e da analise de DNA")
    parser.add_argument("--coletor", choices=["carga", "dna"], help=argparse.SUPPRESS)
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--gedcom", default=GED_PADRAO)
    parser.add_argument("--csv", default=CSV_PADRAO)
    parser.add_argument("--raiz", default=RAIZ_PADRAO)
    args = parser.parse_args(argv)

    if args.coletor:
        return _coletor(args.coletor, args.gedcom, args.csv, args.raiz)

    os.makedirs(PASTA_ISOLADA, exist_ok=True)
    ambiente = dict(os.environ, ANALISADOR_UPLOAD_FOLDER=PASTA_ISOLADA,
                    PYTHONIOENCODING="utf-8")

    print("=" * 78)
    print("PERFIL DA CARGA — codigo de producao (feature 025)")
    print("arvore: %s (%d bytes)" % (os.path.basename(args.gedcom),
                                     os.path.getsize(args.gedcom)))
    print("csv:    %s (%d bytes)" % (os.path.basename(args.csv),
                                     os.path.getsize(args.csv)))
    print("=" * 78, flush=True)

    print("aquecimento (descartado)...", flush=True)
    aquecimento = _rodar_filho("carga", args.gedcom, args.csv, args.raiz, ambiente)
    print("%-28s %.2f s" % ("aquecimento", aquecimento["tempo"]), flush=True)

    medidos = []
    for indice in range(args.repeticoes):
        medido = _rodar_filho("carga", args.gedcom, args.csv, args.raiz, ambiente)
        medidos.append(medido)
        print("%-28s %.2f s" % ("repeticao %d" % (indice + 1), medido["tempo"]),
              flush=True)

    print("-" * 78)
    _tabela("carga", [m["tempo"] for m in medidos])
    primeiro = medidos[0]
    print("%-28s pessoas=%d familias=%d nos=%d arestas=%d"
          % ("estrutura", primeiro["pessoas"], primeiro["familias"],
             primeiro["nos"], primeiro["arestas"]))
    print("%-28s records0=%s" % ("chamadas", primeiro["records0"]))
    print("%-28s index0=%d init_index=%d read_record=%d"
          % ("parser", primeiro["index0"], primeiro["init_index"],
             primeiro["read_record"]))
    print("-" * 78, flush=True)

    print("analise de DNA (1 execucao)...", flush=True)
    dna = _rodar_filho("dna", args.gedcom, args.csv, args.raiz, ambiente)
    print("%-28s %.2f s  cartoes=%d descartados=%d"
          % ("DNA", dna["tempo"], dna["cartoes"], dna["descartados"]))

    mediana_carga = statistics.median([m["tempo"] for m in medidos])
    print("%-28s %.2f s"
          % ("total estimado", mediana_carga + dna["tempo"]))
    print("-" * 78)
    print("JSON_RESUMO " + json.dumps({
        "aquecimento": aquecimento["tempo"],
        "repeticoes": [m["tempo"] for m in medidos],
        "mediana_carga": mediana_carga,
        "dna": dna["tempo"],
        "records0": primeiro["records0"],
        "index0": primeiro["index0"],
        "init_index": primeiro["init_index"],
        "read_record": primeiro["read_record"],
        "pessoas": primeiro["pessoas"],
        "familias": primeiro["familias"],
        "cartoes": dna["cartoes"],
        "descartados": dna["descartados"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
