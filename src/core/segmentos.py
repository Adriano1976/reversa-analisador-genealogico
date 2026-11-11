"""Segmentos que formam as regioes compartilhadas, em ordem de tabela (feature 058).

## O que este modulo decide

Achata as regioes em **uma linha por par (regiao, kit)** — o segmento que cada match
contribuiu para a regiao (`RN-02` da 058) — e fixa a **ordem da tabela**: cromossomo em
ordem natural, depois posicao inicial, depois kit (`RN-03`).

Cada linha carrega `regiao_indice`, a posicao da regiao na lista recebida. E' esse numero
que liga a linha da tabela a faixa do ideograma: a faixa vira `id="regiao-N"` no template, e
a linha aponta para ela. Derivar o vinculo de cromossomo+inicio pareceria mais simples, mas
quebraria se o mesmo cromossomo aparecesse com caixa diferente entre duas linhas do CSV —
o indice nao tem esse problema, porque nasce e morre no mesmo render.

## O que este modulo NAO faz

Nao le arquivo, nao classifica desfecho, nao formata numero e nao projeta dicionario — isso
e `application.segmentos`.
"""
from __future__ import annotations

from dataclasses import dataclass

from .distribuicao import ordem_do_cromossomo


@dataclass(frozen=True, slots=True)
class SegmentoDeRegiao:
    """Um segmento de um kit dentro de uma regiao, com o vinculo da ancora."""

    regiao_indice: int
    cromossomo: str
    inicio: int
    fim: int
    cm: float
    kit: str
    nome: str
    desfecho: str
    desfecho_chave: str


def segmentos_das_regioes(regioes) -> tuple[SegmentoDeRegiao, ...]:
    """Uma linha por (regiao, kit), na ordem da tabela."""
    linhas = []
    for posicao, item in enumerate(regioes or (), start=1):
        regiao = getattr(item, "regiao", item)
        desfecho = getattr(item, "desfecho", None)
        rotulo = getattr(item, "rotulo", "") or ""
        cromossomo = str(getattr(regiao, "cromossomo", "") or "").strip().upper()
        for segmento in regiao.segmentos or ():
            linhas.append(SegmentoDeRegiao(
                regiao_indice=posicao,
                cromossomo=cromossomo,
                inicio=segmento.inicio,
                fim=segmento.fim,
                cm=segmento.cm,
                kit=segmento.kit,
                nome=segmento.nome or "nome não informado",
                desfecho=rotulo if desfecho else "",
                desfecho_chave=desfecho or "",
            ))

    linhas.sort(key=lambda linha: (
        ordem_do_cromossomo(linha.cromossomo), linha.inicio, linha.kit,
    ))
    return tuple(linhas)


__all__ = ["SegmentoDeRegiao", "segmentos_das_regioes"]
