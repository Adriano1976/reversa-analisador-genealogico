"""Estado do GEDCOM carregado e acesso aos registros.

Responsabilidade unica: ser o registro do estado do processo (singleton, nao
persistente) e dar acesso aos registros de pessoa e de familia.

## Contrato de estado

`load_gedcom_and_build_graph`, em `gedcom_parser`, muta `people`, `families` e
`child_to_family` in place (`clear()` mais `update()`) para que o binding
importado no topo pelos outros modulos continue apontando para o objeto vivo.
`graph` e a excecao: e reatribuido, e por isso quem o consome o importa dentro da
funcao (ver `path_finding.py`).

Extraido de `upload.py` pela OPP-20261003-TWNT. As globais e as funcoes sao as
mesmas; o que mudou foi o endereco.
"""
from __future__ import annotations

# Estado global em memória (singleton por processo) — não persistente.
people = {}
families = {}
graph = None
child_to_family: dict[str, list[str]] = {}

# Contador de carregamentos. `people`/`families` sao mutados in place, entao o
# `id()` deles nao muda quando outro GEDCOM entra; quem guarda indice derivado
# (ex.: nome normalizado -> ids, em `documentary_relationship`) precisa de um
# sinal de invalidacao que o rebind nao da. Este contador e esse sinal, e e
# incrementado por `load_gedcom_and_build_graph`.
versao = 0


def ref_id(val):
    """Extrai o xref_id de um objeto ged4py; retorna o valor se já for str."""
    return getattr(val, "xref_id", val)


def get_name(person) -> str:
    """Nome formatado do registro; 'Sem Nome' APENAS se ausente.

    Copia fiel do oraculo (app_legacy_e43ca22.py:42-43):

        return person.name.format() if person and person.name else "Sem Nome"

    ATENCAO — nao "melhore" isto para tratar formato vazio. O legado devolve '' quando
    `person.name` existe mas `.format()` resulta vazio, e esse caso OCORRE em dado real
    (296 pessoas em 35.460 em Arvore_Unificada_Oficial_V1_2.ged; 17 em 3.056 em
    Adriano_Santos.ged). O literal 'Sem Nome' nunca foi observado nos dados. Uma versao
    anterior desta funcao tratava o formato vazio como 'Sem Nome' e quebrava a paridade
    com o oraculo (DIV-001, _reversa_sdd/migration/parity_harness.md).
    """
    return person.name.format() if person and person.name else "Sem Nome"
