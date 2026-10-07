"""Caso de uso da analise de DNA (`T013`; `RF-01`, `RF-14`, `RF-20`).

Chama o fluxo do nucleo e devolve resultado tipado. Nao ha decisao de negocio
aqui: matching, ordem de apresentacao, cM e confronto continuam todos em
`core.dna_analysis` (`RN-01`).

## Por que o caminho do CSV entra pronto, e nao a referencia

O adaptador de entrada grava o CSV pelo port de armazenamento e passa o
**caminho** devolvido, que e o que `RF-09` fixa: `guardar` devolve o caminho
completo do arquivo e nunca um nome a ser remontado. O caminho e o que o fluxo do
nucleo precisa para ler — `deps.read_csv` recebe caminho. Este caso de uso, por
isso, **nao** recebe port nenhum: ele nao faz I/O, so orquestra.

## O que NAO esta aqui

- A guarda "Por favor, carregue o arquivo CSV de matches.": ela decide sobre o
  **formulario**, e continua na borda.
- A montagem de `Dependencias`: ela vem por parametro, montada uma unica vez na
  borda (`RF-14`, `D-05`).
"""
from __future__ import annotations

from dataclasses import dataclass

from core.dna_analysis import dna_analysis as fluxo_dna


@dataclass(frozen=True)
class ResultadoDeAnalise:
    """Resultado da analise. Os campos nao sao nomes de campo de template (`RF-20`).

    O fluxo de DNA **nao** tem desfecho de tres valores: ele ou levanta excecao de
    dominio, ou devolve resultado com mensagem de contrato. A distincao
    resultado/sem-resultado que a `D-11` criou existe para a busca de caminho, e
    inventa-la aqui seria criar um valor de enum que nenhum caminho preenche.
    """

    resultados: list
    descartados: list
    mensagem: str


def dna_analysis(caminho_do_csv: str, root_name: str, arvore, deps,
                 dono: str) -> ResultadoDeAnalise:
    """Executa a analise e devolve `ResultadoDeAnalise`.

    `dono` **nao** e usado para comportamento nesta onda (`RN-06`, `RF-08`): esta
    na assinatura como costura para a Onda 3, e nenhum isolamento e implementado.
    """
    resultados, descartados, mensagem = fluxo_dna(caminho_do_csv, root_name, deps, arvore)
    return ResultadoDeAnalise(
        resultados=resultados,
        descartados=descartados,
        mensagem=mensagem,
    )


__all__ = ["ResultadoDeAnalise", "dna_analysis"]
