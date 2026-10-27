"""Adocao dos dados que existiam antes da identidade (feature 051, `RN-15`).

## O problema

Antes desta feature, todo arquivo vivia na raiz da pasta de upload e todo historico
tinha `owner_id = 'unico'`. Ligar o escopo sem destino para esse acervo o tornaria
invisivel para todo mundo — ou, pior, visivel para quem entrasse primeiro.

## A regra

O dono inicial e **declarado** (`ANALISADOR_DONO_INICIAL`), e a adocao so acontece
quando a conta que acabou de entrar tem aquele e-mail verificado. A copia e feita
**uma vez**, marcada por `<pasta>/.dono-inicial`, e **nunca apaga nem move** o
original: copia. O historico e adotado a cada entrada (o `UPDATE` e condicionado a
`owner_id = 'unico'` e devolve zero depois da primeira vez), para o caso de o banco
ter sido configurado depois da marcacao.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, replace

MARCADOR = ".dono-inicial"
DONO_ANTERIOR = "unico"
PASTA_DE_APOSENTADOS = "_aposentados"

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelatorioDeAdocao:
    """O que a adocao fez nesta chamada. Tudo zero significa "nada a fazer"."""

    copiou: bool = False
    copiados: int = 0
    pulados: int = 0
    adotadas: int = 0


def garantir_dados_do_dono(pasta: str | None, dono: str, registro=None) -> RelatorioDeAdocao:
    """Garante que os dados anteriores pertencam a `dono`. Nunca levanta.

    `registro` e a porta de historico, ou `None` quando nao ha banco configurado —
    o disco e adotado do mesmo jeito.
    """
    if not pasta or not dono:
        return RelatorioDeAdocao()

    relatorio = RelatorioDeAdocao()
    if os.path.isdir(pasta) and not os.path.exists(os.path.join(pasta, MARCADOR)):
        relatorio = _copiar(pasta, dono)

    if registro is not None:
        try:
            relatorio = replace(
                relatorio, adotadas=int(registro.adotar(DONO_ANTERIOR, dono) or 0)
            )
        except Exception:
            # O historico e beneficio; falhar nele nao pode impedir o login.
            _log.exception("nao foi possivel adotar o historico anterior")
    return relatorio


def ha_dados_nao_atribuidos(pasta: str | None) -> bool:
    """Se a raiz ainda guarda arquivos que nenhuma conta pode ver.

    Verdadeiro quando ha arquivo na raiz e o marcador da adocao nao existe. E o
    sinal que o log usa para avisar que `ANALISADOR_DONO_INICIAL` pode estar errado.
    """
    if not pasta or not os.path.isdir(pasta):
        return False
    if os.path.exists(os.path.join(pasta, MARCADOR)):
        return False
    return any(
        not nome.startswith(".") and os.path.isfile(os.path.join(pasta, nome))
        for nome in os.listdir(pasta)
    )


def _copiar(pasta: str, dono: str) -> RelatorioDeAdocao:
    """Copia a raiz e os aposentados para a pasta do dono, e grava o marcador."""
    destino: str = os.path.join(pasta, dono)
    os.makedirs(destino, exist_ok=True)

    copiados = pulados = 0
    copiados, pulados = _copiar_arquivos(pasta, destino, copiados, pulados)

    origem_aposentados: str = os.path.join(pasta, PASTA_DE_APOSENTADOS)
    if os.path.isdir(origem_aposentados):
        destino_aposentados: str = os.path.join(destino, PASTA_DE_APOSENTADOS)
        os.makedirs(destino_aposentados, exist_ok=True)
        copiados, pulados = _copiar_arquivos(
            origem_aposentados, destino_aposentados, copiados, pulados
        )

    _gravar_marcador(pasta, dono)
    _log.info(
        "dados anteriores adotados pela conta inicial: %s copiados, %s ja existentes",
        copiados,
        pulados,
    )
    return RelatorioDeAdocao(copiou=True, copiados=copiados, pulados=pulados)


def _copiar_arquivos(origem: str, destino: str, copiados: int, pulados: int):
    """Copia os arquivos regulares de `origem` para `destino`, sem sobrescrever."""
    for nome in sorted(os.listdir(origem)):
        caminho: str = os.path.join(origem, nome)
        if nome.startswith(".") or not os.path.isfile(caminho):
            continue
        alvo: str = os.path.join(destino, nome)
        if os.path.exists(alvo):
            pulados += 1
            continue
        shutil.copy2(caminho, alvo)
        copiados += 1
    return copiados, pulados


def _gravar_marcador(pasta: str, dono: str) -> None:
    """Marca a adocao de forma atomica: temporario mais renomeacao."""
    caminho: str = os.path.join(pasta, MARCADOR)
    temporario: str = f"{caminho}.tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        arquivo.write(f"{dono}\n")
    os.replace(temporario, caminho)


__all__: list[str] = [
    "DONO_ANTERIOR",
    "MARCADOR",
    "RelatorioDeAdocao",
    "garantir_dados_do_dono",
    "ha_dados_nao_atribuidos",
]
