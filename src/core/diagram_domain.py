"""Consultas de dominio que o desenho do diagrama Mermaid precisa.

Nasceu da OPP-20261006-ULVW. Existe para dar NOME ao contrato que antes estava
implicito nos imports de `reporting/mermaid_render.py`: o renderizador precisa de
sete consultas ao dominio para decidir como desenhar, e antes as obtinha
importando `core` diretamente, o que fechava o ciclo `core/` <-> `reporting/`.

## Regra do projeto

`reporting/` NAO e folha, e nao pode ser. As decisoes de layout (o casal do
ancestral comum, o ancestral que ancora o ramo, o ponto de corte por casamento)
sao decisao de NEGOCIO, e continuam morando no renderizador
(`_reversa_sdd/architecture.md` secao 3 e ADR-11). O que muda aqui e apenas QUEM
BUSCA o dado: o chamador resolve e injeta, em vez de o renderizador importar.

## Forma

O resolvedor e um `dict` de funcoes, e nao uma classe nem um `Protocol`:
`paradigm_decision.md` manda o nucleo permanecer em funcoes puras e proibe
introduzir objetos com estado no calculo.

## A arvore entra por parametro (feature 005, T011/T012/T018)

As consultas de `family_navigation` e de `path_finding` passaram a receber a
arvore. O renderizador **nao** soube disso: o resolvedor captura a arvore
recebida e devolve funcoes ja ligadas a ela, na mesma assinatura de antes. E o
que preserva a costura da OPP-20261006-ULVW sem arrastar o renderizador para a
migracao — e o RISK-011 depende de as duas consultas de decomposicao continuarem
chegando la.

O `T018` fechou a ultima ponta: este modulo nao tem mais **nenhuma** referencia a
`gedcom_state`, nem tardia. Ele recebe a arvore e devolve consultas sobre ela. A
construcao da arvore a partir do estado vive num lugar so
(`documentary_relationship._arvore_global`), importado pelos dois fluxos que a
feature ainda nao migrou; quando `T023` remover o estado, essa construcao sai e a
arvore passa a vir da borda.
"""
from __future__ import annotations

Arvore = tuple


def resolvedor_de_diagrama(arvore: Arvore) -> dict:
    """As consultas de dominio que o desenho do diagrama precisa.

    Uma entrada por simbolo que `reporting/mermaid_render.py` consumia por
    import. O renderizador recebe este mapeamento como parametro e nunca mais
    importa nada de `core`.

    Cada funcao sai **ligada a arvore recebida** (`functools.partial`), para que
    o renderizador continue chamando `get_spouses(pid)` e nao
    `get_spouses(arvore, pid)`.
    """
    from functools import partial

    from .family_navigation import (
        exclude_tail,
        get_spouses,
        pick_spouse_for_couple,
        split_path_by_marriage,
    )
    from .path_finding import find_ancestral_path
    from .registro import get_name

    people = arvore[0]
    return {
        "get_name": get_name,
        "people": people,
        "get_spouses": partial(get_spouses, arvore),
        "split_path_by_marriage": partial(split_path_by_marriage, arvore),
        "pick_spouse_for_couple": partial(pick_spouse_for_couple, arvore),
        "exclude_tail": exclude_tail,
        "find_ancestral_path": partial(find_ancestral_path, arvore),
    }


__all__ = ["resolvedor_de_diagrama"]
