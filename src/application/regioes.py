"""Projeção das regiões compartilhadas para a tela e para o CSV (feature 056).

Pura: não reordena, não recalcula cM e não formata número. A camada de
apresentação e a de relatório só sabem ler dicionário — a projeção é o que
impede o template e o CSV de importarem `core/` (`ADR-34`).
"""
from __future__ import annotations


def projetar_regioes(regioes) -> list[dict]:
    """Converte as regiões classificadas em dicionários de apresentação."""
    projetadas = []
    for item in regioes or ():
        regiao = item.regiao
        ancestrais = sorted({
            membro.ancestral_nome for membro in item.membros if membro.ancestral_nome
        })
        projetadas.append({
            "cromossomo": regiao.cromossomo,
            "inicio": regiao.inicio,
            "fim": regiao.fim,
            "extensao_mb": regiao.extensao_mb,
            "kits": len(regiao.kits),
            "cm_minimo": regiao.cm_minimo,
            "cm_maximo": regiao.cm_maximo,
            "desfecho": item.rotulo if item.desfecho else "",
            "alerta": "acúmulo" if regiao.acumulo else "",
            "membros": " | ".join(
                f"{membro.nome or 'nome não informado'} ({membro.kit})"
                for membro in item.membros
            ),
            "ancestrais": " | ".join(ancestrais),
            "motivo": item.motivo,
        })
    return projetadas


__all__ = ["projetar_regioes"]
