"""Acesso a registro do GEDCOM: nome de exibicao e identificador.

Modulo PURO: nao le nem escreve estado de modulo, nao faz I/O e nao importa
framework. Sao funcoes sobre um registro que o chamador entrega.

## Por que existe separado

Nasceu na feature `005-nucleo-puro-src` (`T008`), que removeu o estado global de
`src/core/gedcom_state.py` — modulo apagado no `T023` desta mesma feature. `get_name`
e `ref_id` nao eram estado: sao leitura de registro, e ficavam no mesmo arquivo
apenas por proximidade historica. Separar permitiu tirar as duas de dentro do modulo
de estado sem duplicar a copia fiel do oraculo — que e o ativo de paridade mais
delicado deste nucleo.

## Sobre `get_name` — nao "melhore" esta funcao

O corpo e copia LITERAL do oraculo (`_reversa_sdd/oracle/app_legacy_e43ca22.py:42-43`):

    return person.name.format() if person and person.name else "Sem Nome"

O legado devolve `''` quando `person.name` existe mas `.format()` resulta vazio,
e esse caso OCORRE em dado real (296 pessoas em 35.460 em
`Arvore_Unificada_Oficial_V1_2.ged`; 17 em 3.056 em `Adriano_Santos.ged`). O
literal "Sem Nome" nunca foi observado nos dados, e e inalcancavel a partir de um
INDI real: remover a tag `NAME` nao produz `person.name is None`, porque o ged4py
ainda entrega um objeto `Name` cujo `.format()` e `''`.

Uma versao anterior tratava o formato vazio como "Sem Nome" e quebrava a paridade
com o oraculo (DIV-001). O achado esta em `_reversa_sdd/migration/parity_harness.md`
e o teste que o fixa e `tests/test_upload.py`.
"""
from __future__ import annotations


def ref_id(val):
    """Extrai o xref_id de um objeto ged4py; retorna o valor se ja for str."""
    return getattr(val, "xref_id", val)


def get_name(person) -> str:
    """Nome formatado do registro; 'Sem Nome' APENAS se ausente.

    Copia fiel do oraculo (`app_legacy_e43ca22.py:42-43`). Ver o aviso no
    docstring do modulo antes de alterar.
    """
    return person.name.format() if person and person.name else "Sem Nome"
