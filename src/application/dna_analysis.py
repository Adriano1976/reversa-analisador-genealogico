"""Caso de uso da analise de DNA (`T013`; `RF-01`, `RF-14`, `RF-20`).

Chama o fluxo do nucleo e devolve resultado tipado. Nao ha decisao de negocio
aqui: matching, ordem de apresentacao, cM e confronto continuam todos em
`core.dna_analysis` (`RN-01`).

## Por que o caminho do CSV entra pronto, e nao a referencia

O adaptador de entrada grava o CSV pelo port de armazenamento e passa o
**caminho** devolvido, que e o que `RF-09` fixa: `guardar` devolve o caminho
completo do arquivo e nunca um nome a ser remontado. O caminho e o que o fluxo do
nucleo precisa para ler — `deps.read_csv` recebe caminho.

## A persistencia historica (feature 008; `D-01`, `D-15`, `T015`)

O caso de uso passou a **receber a porta** `RegistroDeAnalises` e a chama-la
**depois** de o nucleo ter terminado. `registro` tem valor padrao `None`, e `None`
**e** o estado desabilitado da `D-02`: sem `DATABASE_URL` a borda monta um
registrador nulo, o comportamento e o de antes da feature, e a tela nao muda um
byte.

## Projecao do resultado para o payload da porta

A projecao vive em `application.projecao_analise` (`OPP-20261023-MPRA`).
E pura e sem efeito: le o que o nucleo devolveu e nada mais — nao chama funcao
do nucleo, nao recalcula cM, nao reordena e nao formata (`D-15`).
Re-exportada aqui para compatibilidade com os consumidores existentes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.dna_analysis import dna_analysis as fluxo_dna

# OPP-20261023-MPRA e OPP-20261023-CLSM: a projecao pura foi extraida e
# encapsulada no padrao Mapper (ProjetorDeAnalise). Re-exportada aqui para
# compatibilidade total com importadores existentes.
from application.projecao_analise import ProjetorDeAnalise, projetar_analise  # noqa: F401


@dataclass(frozen=True)
class ResultadoDeAnalise:
    """Resultado da analise. Os campos nao sao nomes de campo de template (`RF-20`).

    O fluxo de DNA **nao** tem desfecho de tres valores: ele ou levanta excecao de
    dominio, ou devolve resultado com mensagem de contrato.

    `aviso_de_persistencia` e o **unico** campo que a feature 008 acrescentou, e ele
    tem valor padrao para que as construcoes existentes continuem validas. Nulo
    significa "nada a avisar" — gravado, ou persistencia desabilitada —, e nesse
    caso a tela nao renderiza nada (`D-02`, `RF-17`).

    `observacoes_do_arquivo` sao os avisos da ANALISE (e nao de um cartao): mesmo
    nome em mais de um kit, CSV sem coluna de kit, linhas ignoradas, cabecalho fora
    do lugar, raiz ambigua. Tambem tem valor padrao pela mesma razao, e a tela os
    mostra em bloco unico — antes eles eram copiados para dentro de cada cartao.
    """

    resultados: list
    descartados: list
    mensagem: str
    aviso_de_persistencia: str | None = None
    observacoes_do_arquivo: tuple = ()
    # FEATURE 039: os cartoes sem correspondencia, na ordem da tela. Derivado de
    # `resultados`; a tela usa o tamanho.
    sem_correspondencia: tuple = ()
    # FEATURE 040: o retrato do arquivo (linhas, evidencias, laboratorios, mediana,
    # pisos). `None` quando o nucleo nao o preencheu; a tela nao renderiza o painel.
    cobertura: dict | None = None


def dna_analysis(caminho_do_csv: str, root_name: str, arvore, deps,
                 dono: str, referencia_da_arvore: str | None = None,
                 registro=None, candidatos_fixos=None) -> ResultadoDeAnalise:
    """Executa a analise e devolve `ResultadoDeAnalise`.

    `dono` e uma costura arquitetural intencional da Onda 3 (`RN-06`, `RF-08`, `ADR-26`):
    e repassado para `registro.registrar(analise, dono)` e gravado na coluna
    `owner_id TEXT NOT NULL` do Postgres. Nesta onda nao aplica isolamento comportamental
    em consultas, sendo mantido para integridade de schema e futura expansao.

    `referencia_da_arvore` e `registro` tem valor padrao, e **`None` em qualquer um
    dos dois significa nao registrar**, o estado desabilitado da `D-02`. Sem a
    referencia da arvore nao ha o que gravar: ela e a chave de conteudo que o
    `RF-03` exige, e inventa-la aqui seria criar um identificador que nao existe.
    """
    # As observacoes que valem para o ARQUIVO inteiro, e nao para um cartao. Elas
    # nascem no nucleo e ganham canal proprio na tela; sem isso, eram copiadas para
    # dentro de cada cartao (ver o adendo 017).
    _observacoes: list[str] = []
    _cobertura: dict = {}
    resultados, descartados, mensagem = fluxo_dna(caminho_do_csv, root_name, deps, arvore,
                                                  observacoes_do_arquivo=_observacoes,
                                                  candidatos_fixos=candidatos_fixos,
                                                  cobertura=_cobertura)

    # FEATURE 039: os cartoes sem correspondencia JA' estao em `resultados`; a tela so'
    # precisa do tamanho. Derivar daqui impede que a contagem e a lista divirjam.
    sem_correspondencia = tuple(r for r in resultados if r.get("sem_correspondencia"))

    aviso = None
    if registro is not None and referencia_da_arvore:
        try:
            analise = projetar_analise(
                resultados, descartados, mensagem, referencia_da_arvore,
                os.path.basename(caminho_do_csv), root_name,
            )
            _, aviso = registro.registrar(analise, dono)
        except Exception as erro:
            # A `RN-13` vale para as DUAS metades: nem a projecao nem a gravacao
            # podem impedir o resultado de chegar a tela. Uma excecao aqui seria a
            # persistencia bloqueando a analise — exatamente o que ela nao pode.
            aviso = ("Histórico não registrado: falha ao preparar os dados "
                     f"({type(erro).__name__}: {erro}).")

    return ResultadoDeAnalise(
        resultados=resultados,
        descartados=descartados,
        mensagem=mensagem,
        aviso_de_persistencia=aviso,
        observacoes_do_arquivo=tuple(_observacoes),
        sem_correspondencia=sem_correspondencia,
        cobertura=_cobertura or None,
    )


__all__ = ["ProjetorDeAnalise", "ResultadoDeAnalise", "dna_analysis", "projetar_analise"]
