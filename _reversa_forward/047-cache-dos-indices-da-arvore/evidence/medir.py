"""Instrumento de medicao da feature 047: duas cargas e uma analise, por fase.

Uso:

    .\\.venv\\Scripts\\python.exe _reversa_forward\\047-cache-dos-indices-da-arvore\\evidence\\medir.py ^
        --ged <caminho.ged> --csv <caminho.csv> --raiz "Nome do doador" --cache off

O programa sobe a aplicacao com pasta de upload descartavel, faz tres `POST` (upload, selecao e
analise) e imprime um JSON com o tempo de cada fase e o `sha256` do HTML final.

## O que ele NAO faz

- Nao grava nome, `xref`, cM nem HTML: so contagens, tempos e hashes.
- Nao usa a pasta real de uploads: cria uma pasta temporaria dentro do workspace e apaga no fim.
- Nao depende do cache existir: o estado e ligado por variavel de ambiente, lida antes do
  `import app`, e o instrumento funciona igual antes e depois da feature.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RAIZ, "src"))


def medir(ged: str, csv: str, raiz: str, cache: str) -> dict:
    """Roda os tres POST e devolve as medidas. `cache` e "on" ou "off"."""
    pasta = os.path.join(RAIZ, f"_medicao_047_{cache}")
    shutil.rmtree(pasta, ignore_errors=True)
    os.makedirs(pasta)
    import app as modulo
    import core.dna_analysis as nucleo
    from application import nomes_de_exibicao
    from ports.adaptadores import ArmazenamentoEmDisco, CarregadorDeArvoresGedcom

    tempos = {}

    def cronometrar(nome, funcao):
        def envolvida(*a, **k):
            t = time.perf_counter()
            try:
                return funcao(*a, **k)
            finally:
                tempos[nome] = tempos.get(nome, 0) + time.perf_counter() - t
        return envolvida

    try:
        armazenamento = ArmazenamentoEmDisco(pasta)
        carregador = CarregadorDeArvoresGedcom(armazenamento)
        carregador.carregar = cronometrar("parse", carregador.carregar)
        aplicacao = modulo.create_app(armazenamento=armazenamento, carregador=carregador,
                                      registro=None)
        cliente = aplicacao.test_client()

        conteudo_ged = open(ged, "rb").read()
        conteudo_csv = open(csv, "rb").read()

        t = time.perf_counter()
        resposta = cliente.post("/", data={"action": "upload_gedcom",
                                           "gedcom": (io.BytesIO(conteudo_ged), "arvore.ged")},
                                content_type="multipart/form-data")
        tempos["upload"] = time.perf_counter() - t
        assert resposta.status_code == 200, resposta.status_code
        referencia = os.listdir(pasta)[0]

        nomes = nomes_de_exibicao(carregador.carregar(referencia, "processo"))
        if raiz not in nomes:
            candidatos = [n for n in nomes if n.lower().startswith(raiz.lower().split()[0])]
            if not candidatos:
                raise SystemExit(f"raiz nao encontrada: {raiz!r}")
            raiz = candidatos[0]

        t = time.perf_counter()
        resposta = cliente.post("/", data={"action": "selecionar_arvore",
                                           "gedcom_filename": referencia})
        tempos["selecao"] = time.perf_counter() - t
        assert resposta.status_code == 200

        nucleo.build_ged_indexes = cronometrar("indices", nucleo.build_ged_indexes)
        modulo.caso_de_uso_dna = cronometrar("analise", modulo.caso_de_uso_dna)
        modulo.render_template = cronometrar("render", modulo.render_template)

        t = time.perf_counter()
        resposta = cliente.post("/", data={"action": "dna_analysis",
                                           "gedcom_filename": referencia,
                                           "root_name": raiz,
                                           "matches_csv": (io.BytesIO(conteudo_csv), "matches.csv")},
                                content_type="multipart/form-data")
        tempos["dna"] = time.perf_counter() - t
        assert resposta.status_code == 200, resposta.status_code

        # Segunda analise na MESMA arvore: e o caso que a feature promete (indices ja construidos).
        antes_dos_indices = tempos.get("indices", 0)
        t = time.perf_counter()
        resposta2 = cliente.post("/", data={"action": "dna_analysis",
                                            "gedcom_filename": referencia,
                                            "root_name": raiz,
                                            "matches_csv": (io.BytesIO(conteudo_csv), "matches.csv")},
                                 content_type="multipart/form-data")
        dna2 = time.perf_counter() - t
        indices2 = tempos.get("indices", 0) - antes_dos_indices
        assert resposta2.status_code == 200, resposta2.status_code

        arvore = carregador.carregar(referencia, "processo")
        html = resposta.data
        return {
            "cache": cache,
            "raiz": raiz,
            "pessoas": len(arvore[0]),
            "familias": len(arvore[1]),
            "arestas": arvore[2].number_of_edges(),
            "upload_s": round(tempos.get("upload", 0), 2),
            "selecao_s": round(tempos.get("selecao", 0), 2),
            "dna_s": round(tempos.get("dna", 0), 2),
            "parse_no_dna_s": round(tempos.get("parse", 0), 2),
            "indices_s": round(tempos.get("indices", 0), 2),
            "analise_s": round(tempos.get("analise", 0), 2),
            "render_s": round(tempos.get("render", 0), 3),
            "dna2_s": round(dna2, 2),
            "indices_no_dna2_s": round(indices2, 2),
            "html_bytes": len(html),
            "html_sha256": hashlib.sha256(html).hexdigest(),
        }
    finally:
        shutil.rmtree(pasta, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mede upload, selecao e analise por fase.")
    parser.add_argument("--ged", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--raiz", required=True)
    parser.add_argument("--cache", choices=["on", "off"], default="off")
    argumentos = parser.parse_args()

    # A variavel tem de existir ANTES do import de `app`, que monta o carregador no import.
    # `setdefault` nao serve: em "off" ela precisa estar ausente.
    if argumentos.cache == "on":
        os.environ["ANALISADOR_CACHE_DE_ARVORE"] = "1"
    else:
        os.environ.pop("ANALISADOR_CACHE_DE_ARVORE", None)

    print(json.dumps(medir(argumentos.ged, argumentos.csv, argumentos.raiz, argumentos.cache),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
