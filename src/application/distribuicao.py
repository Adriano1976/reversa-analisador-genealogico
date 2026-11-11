"""Projecao da distribuicao por cromossomo para a tela (feature 057).

Pura: nao reordena, nao formata numero e nao calcula geometria. Mesma regra de
`application.regioes` — o template e o relatorio nao importam `core/` (`ADR-34`).
"""
from __future__ import annotations


def projetar_distribuicao(resumos) -> list[dict]:
    """Converte os resumos do nucleo em dicionarios de apresentacao."""
    return [
        {
            "cromossomo": resumo.cromossomo,
            # `RN-02`: o numero de matches e o tamanho do conjunto de kits, ja
            # deduplicado pelo nucleo.
            "kits": len(resumo.kits),
            "cm_medio": resumo.cm_medio,
        }
        for resumo in resumos or ()
    ]


__all__ = ["projetar_distribuicao"]
