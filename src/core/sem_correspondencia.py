"""Regra de triagem dos matches de cM alto sem correspondência na árvore (feature 039).

## O que este módulo responde

A lista de descartes de uma análise real tem centenas de nomes, e a maioria é cM baixo.
Um match de cM alto sem nenhuma pessoa com nome compatível na árvore some no meio deles.
A regra abaixo separa esses casos; quem os apresenta como cartão é `core.dna_analysis`,
com o mesmo tratamento de "Parentesco documental não encontrado".

## A regra

Um descarte é elegível quando:

1. `cm >= CM_MINIMO_SEM_CORRESPONDENCIA` — 20,0 cM é um **corte de triagem** declarado
   pelo operador, não uma faixa de parentesco publicada;
2. **nenhum** candidato do descarte tem `compativel=True`;
3. o nome normalizado **não** aparece em nenhum cartão **aceito** (de qualquer kit). O
   cartão sem correspondência não conta: ele é o próprio item.

O item é por **(nome, kit)**: dois kits do mesmo nome, sem cartão aceito, são duas
linhas, cada uma com o seu cM e o seu MRCA. Nunca há soma entre kits.

## Por que 20,0

A medição de 2026-10-22, no arquivo real, dá 60 itens com o corte em 20,0 cM (9 com o
corte antigo de 40,0; 20 com 30,0). O número é heurístico e ajustável; mudá-lo é mudança
de código, com a medição atualizada neste docstring.

## O que este módulo NÃO faz

Não decide aceitação, não recalcula cM, não relê CSV/GEDCOM, não monta cartão, não ordena,
não projeta e não persiste nada. A contagem do resumo é derivada dos cartões já
acrescentados a `resultados` pela aplicação — não há uma segunda seleção.
"""
from __future__ import annotations

from .name_normalization import norm_name

#: Corte de triagem. Ver o docstring do módulo para a medição e a ressalva.
CM_MINIMO_SEM_CORRESPONDENCIA = 20.0


def nomes_com_cartao_aceito(resultados) -> set[str]:
    """Nomes normalizados que já têm cartão ACEITO.

    O cartão sem correspondência é o **próprio item** e não conta como correspondência;
    por isso a marca `sem_correspondencia` é ignorada aqui.
    """
    return {
        norm_name(r.get("csv_name") or "")
        for r in (resultados or ())
        if not r.get("sem_correspondencia")
    }


def elegivel(descarte, nomes_com_cartao: set[str]) -> bool:
    """A regra dos três critérios, sem ordenar e sem projetar.

    `nomes_com_cartao` vem de `nomes_com_cartao_aceito`; o chamador calcula o conjunto
    uma vez e o reusa para todos os descartes da análise.
    """
    cm = descarte.get("cm")
    if cm is None or float(cm) < CM_MINIMO_SEM_CORRESPONDENCIA:
        return False
    if any(c.get("compativel") for c in (descarte.get("candidatos") or ())):
        return False
    return norm_name(descarte.get("csv_name") or "") not in nomes_com_cartao


__all__ = ["CM_MINIMO_SEM_CORRESPONDENCIA", "elegivel", "nomes_com_cartao_aceito"]
