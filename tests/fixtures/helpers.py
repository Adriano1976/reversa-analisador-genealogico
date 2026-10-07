"""Helpers compartilhados das fixtures de teste.

## Por que `deps()` existe

A feature `005` (`T016`) tirou do nucleo os imports de `parsers/csv_ingest` e de
`reporting/mermaid_render`: a leitura do CSV e a emissao do diagrama passaram a
ser injetadas pela borda. Os testes chamam `dna_analysis` diretamente, entao
precisam montar as mesmas dependencias que `src/app.py` monta.

Manter isso num lugar so evita que quatro arquivos de teste repitam a lista — e
que um deles fique para tras quando a borda mudar.
"""
from __future__ import annotations


def deps():
    """As dependencias de borda que `dna_analysis` consome, na forma da classe."""
    from core.dna_analysis import Dependencias
    from parsers.csv_ingest import (
        aggregate_matches,
        detect_columns,
        read_csv_with_fallback,
    )
    from reporting.mermaid_render import (
        generate_mermaid_graph,
        generate_mermaid_graph_indirect_bridge,
    )

    return Dependencias(read_csv_with_fallback, detect_columns,
                        aggregate_matches, generate_mermaid_graph,
                        generate_mermaid_graph_indirect_bridge)


def arvore_de(fonte):
    """A arvore na forma que o nucleo recebe (feature 005, T020).

    Aceita as duas formas que aparecem nos testes, porque as duas existem durante
    a transicao (`D-11`): a propria arvore — o valor que o parse DEVOLVE, que e a
    forma de agora em diante — ou o modulo de estado, cujas globais ainda sao
    escritas por `carregar_arvore` ate `T023`.

    Passar a arvore por identidade, e nao recria-la, importa: ela e uma tupla de
    quatro estruturas, e reconstrui-la a partir de outra fonte devolveria uma
    arvore diferente da que o teste carregou.
    """
    if isinstance(fonte, tuple) and len(fonte) == 4:
        return fonte
    return (fonte.people, fonte.families, fonte.graph, fonte.child_to_family)
