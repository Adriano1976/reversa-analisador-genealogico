"""Caso de uso da analise de DNA (`T013`; `RF-01`, `RF-14`, `RF-20`).

Chama o fluxo do nucleo e devolve resultado tipado; nao ha decisao de negocio
aqui: matching, ordem de apresentacao, cM e confronto continuam em
`core.dna_analysis` (`RN-01`).

Entra o caminho do CSV pronto, nao a referencia: o adaptador de entrada grava pelo
port de armazenamento e passa o caminho devolvido, que e o que `RF-09` fixa — `guardar`
devolve o caminho completo do arquivo e nunca um nome a remontar. E o que o nucleo
precisa para ler: `deps.read_csv` recebe caminho.

Persistencia (feature 008; `D-01`, `D-15`, `T015`): recebe a porta
`RegistroDeAnalises` e a chama depois de o nucleo terminar. `registro` tem valor
padrao `None`, e `None` e o estado desabilitado da `D-02`: sem `DATABASE_URL` a
borda monta um registrador nulo, o comportamento e o de antes da feature e a tela
nao muda um byte.

A projecao para o payload da porta vive em `application.projecao_analise`
(`OPP-20261023-MPRA`): pura e sem efeito, le o que o nucleo devolveu e nada mais
— nao chama funcao do nucleo, nao recalcula cM, nao reordena e nao formata
(`D-15`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.dna_analysis import dna_analysis as fluxo_dna

# OPP-20261023-MPRA e OPP-20261023-CLSM: a projecao pura foi extraida e
# encapsulada no padrao Mapper (ProjetorDeAnalise); re-exportada aqui para
# compatibilidade com importadores existentes.
from application.projecao_analise import ProjetorDeAnalise, projetar_analise  # noqa: F401


@dataclass(frozen=True)
class ResultadoDeAnalise:
    """Resultado da analise. Os campos nao sao nomes de campo de template (`RF-20`).

    O fluxo de DNA **nao** tem desfecho de tres valores: ele ou levanta excecao de
    dominio, ou devolve resultado com mensagem de contrato.

    `aviso_de_persistencia` e o **unico** campo que a feature 008 acrescentou; tem
    valor padrao para as construcoes existentes continuarem validas. Nulo
    significa "nada a avisar" — gravado, ou persistencia desabilitada — e a tela
    nao renderiza nada (`D-02`, `RF-17`).

    `observacoes_do_arquivo` sao os avisos da ANALISE, nao de um cartao: mesmo
    nome em mais de um kit, CSV sem coluna de kit, linhas ignoradas, cabecalho
    fora do lugar, raiz ambigua. Tem valor padrao pela mesma razao, e a tela os
    mostra em bloco unico.
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

    `dono` e costura arquitetural intencional da Onda 3 (`RN-06`, `RF-08`, `ADR-26`):
    repassado para `registro.registrar(analise, dono)` e gravado na coluna
    `owner_id TEXT NOT NULL` do Postgres. Nesta onda nao aplica isolamento
    comportamental em consultas; fica para integridade de schema e expansao futura.

    `referencia_da_arvore` e `registro` tem valor padrao, e **`None` em qualquer um
    dos dois significa nao registrar**, o estado desabilitado da `D-02`. Sem a
    referencia nao ha o que gravar: ela e a chave de conteudo que o `RF-03` exige,
    e inventa-la seria criar um identificador que nao existe.
    """
    # Observacoes do ARQUIVO inteiro, nao de um cartao: nascem no nucleo e ganham
    # canal proprio na tela; sem isso, eram copiadas para cada cartao (adendo 017).
    _observacoes: list[str] = []
    _cobertura: dict = {}
    resultados, descartados, mensagem = fluxo_dna(caminho_do_csv, root_name, deps, arvore,
                                                  observacoes_do_arquivo=_observacoes,
                                                  candidatos_fixos=candidatos_fixos,
                                                  cobertura=_cobertura)

    # FEATURE 039: os cartoes sem correspondencia JA' estao em `resultados`; a tela
    # so' precisa do tamanho. Derivar daqui evita que a contagem e a lista divirjam.
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


__all__: list[str] = ["ProjetorDeAnalise", "ResultadoDeAnalise", "dna_analysis", "projetar_analise"]
