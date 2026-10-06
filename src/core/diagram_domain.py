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
"""
from __future__ import annotations


def resolvedor_de_diagrama() -> dict:
    """As consultas de dominio que o desenho do diagrama precisa.

    Uma entrada por simbolo que `reporting/mermaid_render.py` consumia por
    import. O renderizador recebe este mapeamento como parametro e nunca mais
    importa nada de `core`.
    """
    from .family_navigation import (
        exclude_tail,
        get_spouses,
        pick_spouse_for_couple,
        split_path_by_marriage,
    )
    from .gedcom_state import get_name, people
    from .path_finding import find_ancestral_path

    return {
        "get_name": get_name,
        "people": people,
        "get_spouses": get_spouses,
        "split_path_by_marriage": split_path_by_marriage,
        "pick_spouse_for_couple": pick_spouse_for_couple,
        "exclude_tail": exclude_tail,
        "find_ancestral_path": find_ancestral_path,
    }


__all__ = ["resolvedor_de_diagrama"]
