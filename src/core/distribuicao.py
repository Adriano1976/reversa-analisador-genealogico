"""Distribuicao dos matches por cromossomo (feature 057).

## O que este modulo decide

Para cada cromossomo que tem regiao compartilhada, dois numeros:

- **Matches**: quantos **kits distintos** o arquivo tem ali (`RN-02`). O kit conta uma
  vez so, mesmo que apareca em duas regioes do mesmo cromossomo.
- **cM medio**: a media aritmetica simples do segmento escolhido de cada kit (`RN-03`),
  **sem somar** cM entre segmentos nem entre cromossomos.

Cromossomo sem regiao nao entra (`RN-06`): mostrar cromossomo vazio sugeriria cobertura
que o arquivo nao tem.

## Por que um segmento por kit, e nao todos

`core.regioes._montar` ja escolhe, por kit, o segmento mais forte da janela — uma regiao
nunca repete kit. Quando o mesmo kit cai em duas regioes do mesmo cromossomo, somar os
segmentos das duas contaria o mesmo match duas vezes e o denominador da media deixaria de
casar com a serie de Matches (`D-12` do roadmap 057). Aqui vale o mesmo criterio: o
segmento de maior cM, com desempate pelo menor inicio.

## O que este modulo NAO faz

Nao le arquivo, nao classifica desfecho, nao formata numero e nao calcula geometria de
desenho — isso e `application.distribuicao` e `reporting.distribuicao`.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .regioes import SegmentoDaRegiao


@dataclass(frozen=True, slots=True)
class ResumoDoCromossomo:
    """Os dois numeros de um cromossomo, ja deduplicados por kit."""

    cromossomo: str
    kits: tuple[str, ...]
    cm_medio: float


def ordem_do_cromossomo(cromossomo: str):
    """Ordem natural: numericos primeiro, por valor; o resto em ordem alfabetica."""
    # pyrefly: ignore[unnecessary-type-conversion]
    texto = str(cromossomo).strip().upper()
    return (0, int(texto), "") if texto.isdigit() else (1, 0, texto)


def distribuicao_por_cromossomo(regioes) -> tuple[ResumoDoCromossomo, ...]:
    """Uma linha por cromossomo com regiao, em ordem natural de cromossomo."""
    por_cromossomo: dict[str, list[SegmentoDaRegiao]] = defaultdict(list)
    for regiao in regioes or ():
        cromossomo = str(getattr(regiao, "cromossomo", "") or "").strip().upper()
        if not cromossomo:
            continue
        por_cromossomo[cromossomo].extend(regiao.segmentos or ())

    resumos = []
    for cromossomo, segmentos in por_cromossomo.items():
        escolhidos: dict[str, SegmentoDaRegiao] = {}
        for segmento in segmentos:
            atual = escolhidos.get(segmento.kit)
            if atual is None or (segmento.cm, -segmento.inicio) > (atual.cm, -atual.inicio):
                escolhidos[segmento.kit] = segmento
        if not escolhidos:
            continue
        kits = tuple(sorted(escolhidos))
        resumos.append(ResumoDoCromossomo(
            cromossomo=cromossomo,
            kits=kits,
            cm_medio=sum(escolhidos[kit].cm for kit in kits) / len(kits),
        ))

    return tuple(sorted(resumos, key=lambda resumo: ordem_do_cromossomo(resumo.cromossomo)))


__all__ = ["ResumoDoCromossomo", "distribuicao_por_cromossomo", "ordem_do_cromossomo"]
