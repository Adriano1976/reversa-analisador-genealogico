"""Projeção das regiões compartilhadas para a tela e para o CSV (feature 056).

Pura: não reordena, não recalcula cM e não formata número. A camada de
apresentação e a de relatório só sabem ler dicionário — a projeção é o que
impede o template e o CSV de importarem `core/` (`ADR-34`).
"""
from __future__ import annotations


def projetar_regioes(regioes) -> list[dict]:
    """Converte as regiões classificadas em dicionários de apresentação.

    `indice` é a posição da região nesta lista (1-based), e é o que liga a linha da
    tabela de segmentos à faixa do ideograma (`id="regiao-N"` da feature 058).
    """
    projetadas = []
    for indice, item in enumerate(regioes or (), start=1):
        regiao = item.regiao
        ancestrais = sorted({
            membro.ancestral_nome for membro in item.membros if membro.ancestral_nome
        })
        projetadas.append({
            "indice": indice,
            "cromossomo": regiao.cromossomo,
            "inicio": regiao.inicio,
            "fim": regiao.fim,
            "extensao_mb": regiao.extensao_mb,
            "kits": len(regiao.kits),
            "cm_minimo": regiao.cm_minimo,
            "cm_maximo": regiao.cm_maximo,
            "snps_minimo": regiao.snps_minimo,
            "snps_maximo": regiao.snps_maximo,
            "desfecho": item.rotulo if item.desfecho else "",
            "desfecho_chave": item.desfecho or "",
            "alerta": "acúmulo" if regiao.acumulo else "",
            "acumulo": bool(regiao.acumulo),
            "membros": " | ".join(
                f"{membro.nome or 'nome não informado'} ({membro.kit})"
                for membro in item.membros
            ),
            "membros_lista": [
                {
                    "nome": membro.nome or "nome não informado",
                    "kit": membro.kit,
                    "ancestral": membro.ancestral_nome or "",
                }
                for membro in item.membros
            ],
            "ancestrais": " | ".join(ancestrais),
            "motivo": item.motivo,
        })
    return projetadas


__all__ = ["projetar_regioes"]
