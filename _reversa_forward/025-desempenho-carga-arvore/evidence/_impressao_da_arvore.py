"""Impressao digital da ARVORE e do RESULTADO da analise de DNA (feature 025).

## Para que serve

Provar que a saida e **identica** antes e depois da mudanca no parser, sem
tolerancia (`RISK-004`), e sem transcrever dado pessoal para a evidencia: o
arquivo de saida contem **hashes e contagens**, nunca nome de pessoa, xref ou cM
(Principio I).

## O que entra no hash

Da arvore, numa serializacao canonica que preserva ORDEM — que e contrato de
paridade (`@ordem`, `parity_specs.md` secao 4):

    P|<xref>                     por pessoa, na ordem de insercao
    F|<xref>                     por familia, na ordem de insercao
    N|<no>|<label>|<type>        por no do grafo, na ordem de insercao
    E|<u>|<v>                    por aresta, na ordem de insercao
    C|<filho>|<f1>,<f2>,...      por entrada de child_to_family, na ordem

Do resultado da analise, uma projecao dos campos que a tela mostra, na ordem dos
cartoes e dos descartados, serializada em JSON com chaves ordenadas. Listas
mantem a ordem; conjuntos nao existem nessa projecao (e o serializador recusa
qualquer tipo que nao seja escalar, lista ou dicionario, justamente para nao
depender de `PYTHONHASHSEED`).

## Uso

    .venv\\Scripts\\python.exe _reversa_forward\\025-desempenho-carga-arvore\\evidence\\_impressao_da_arvore.py --saida <arquivo>

Sem `--saida`, imprime na tela.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(RAIZ, "src")

GED_PADRAO = os.path.join(SRC, "uploads",
                          "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
CSV_PADRAO = os.path.join(SRC, "uploads",
                          "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ_PADRAO = "Adriano Santos"
PASTA_ISOLADA = os.path.join(RAIZ, ".parity-tmp", "uploads")


def _sha256_de_arquivo(caminho: str) -> str:
    digest = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _sha256_de_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _serializar_arvore(people, families, graph, child_to_family) -> str:
    linhas = ["arvore-v1"]
    for chave in people:
        linhas.append("P|" + str(chave))
    for chave in families:
        linhas.append("F|" + str(chave))
    for no, dados in graph.nodes(data=True):
        linhas.append("N|%s|%s|%s" % (no, dados.get("label", ""), dados.get("type", "")))
    for origem, destino in graph.edges():
        linhas.append("E|%s|%s" % (origem, destino))
    for filho, familias_do_filho in child_to_family.items():
        linhas.append("C|%s|%s" % (filho, ",".join(familias_do_filho)))
    return "\n".join(linhas)


def _sem_tipo_desconhecido(valor):
    raise TypeError("tipo inesperado na projecao do resultado: %r" % type(valor))


_CAMPOS_DO_CARTAO = (
    "match_name", "csv_name", "identidade", "janela_de_vida",
    "idade_na_arvore", "data_de_nascimento", "data_imprecisa", "ano_de_referencia",
    "profundidade", "geracoes_documentais", "geracoes_do_kit", "cm", "kit",
    "text_path", "confrontacao_efetiva", "confrontacao_rotulo",
)


def _projecao_do_cartao(cartao: dict) -> dict:
    projecao = {campo: cartao.get(campo) for campo in _CAMPOS_DO_CARTAO}
    projecao["caminho"] = ((cartao.get("documentary") or {}).get("path") or {}).get("ids")
    projecao["ancestral_comum"] = (cartao.get("documentary") or {}).get("common_ancestor")
    projecao["documentary"] = cartao.get("documentary")
    projecao["comparison"] = cartao.get("comparison")
    projecao["genetic_evidence"] = cartao.get("genetic_evidence")
    projecao["warnings"] = cartao.get("warnings")
    projecao["observations"] = cartao.get("observations")
    projecao["mermaid_data"] = cartao.get("mermaid_data")
    return projecao


def _serializar_resultado(resultados, descartados, mensagem) -> str:
    cartoes = [_projecao_do_cartao(c) for c in resultados]
    corpo = {
        "cartoes": cartoes,
        "descartados": list(descartados),
        "mensagem": mensagem,
    }
    return json.dumps(corpo, ensure_ascii=False, sort_keys=True,
                      default=_sem_tipo_desconhecido)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Impressao digital da arvore e do DNA")
    parser.add_argument("--gedcom", default=GED_PADRAO)
    parser.add_argument("--csv", default=CSV_PADRAO)
    parser.add_argument("--raiz", default=RAIZ_PADRAO)
    parser.add_argument("--saida", default=None)
    args = parser.parse_args(argv)

    os.makedirs(PASTA_ISOLADA, exist_ok=True)
    os.environ["ANALISADOR_UPLOAD_FOLDER"] = PASTA_ISOLADA
    sys.path.insert(0, SRC)

    from parsers.gedcom_parser import carregar_arvore
    from application.dna_analysis import dna_analysis
    import app

    arvore = carregar_arvore(args.gedcom)
    people, families, graph, child_to_family = arvore
    resultado = dna_analysis(args.csv, args.raiz, arvore, app._DEPENDENCIAS,
                             "dono-local", None, None)

    impressao_arvore = _sha256_de_texto(
        _serializar_arvore(people, families, graph, child_to_family))
    impressao_dna = _sha256_de_texto(
        _serializar_resultado(resultado.resultados, resultado.descartados,
                              resultado.mensagem))

    linhas = [
        "IMPRESSAO DA ARVORE E DO RESULTADO — feature 025",
        "gedcom: %s (%d bytes) sha256_arquivo=%s"
        % (os.path.basename(args.gedcom), os.path.getsize(args.gedcom),
           _sha256_de_arquivo(args.gedcom)),
        "csv: %s (%d bytes) sha256_arquivo=%s"
        % (os.path.basename(args.csv), os.path.getsize(args.csv),
           _sha256_de_arquivo(args.csv)),
        "raiz: %s" % args.raiz,
        "pessoas=%d familias=%d nos=%d arestas=%d"
        % (len(people), len(families), graph.number_of_nodes(),
           graph.number_of_edges()),
        "cartoes=%d descartados=%d"
        % (len(resultado.resultados), len(resultado.descartados)),
        "impressao_arvore=%s" % impressao_arvore,
        "impressao_dna=%s" % impressao_dna,
    ]
    texto = "\n".join(linhas) + "\n"

    if args.saida:
        os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
        with open(args.saida, "w", encoding="utf-8") as fh:
            fh.write(texto)
    sys.stdout.write(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
