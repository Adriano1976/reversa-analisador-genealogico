"""Arvores sinteticas para os testes da busca (feature 052).

Dado real de terceiro nunca entra em fixture (principio I). As arvores daqui sao
geradas a partir de nomes escritos no teste, e existem por tres motivos:

1. sobrenome composto e particula (`Silva e Souza`, `dos Santos`), que o casamento
   por token precisa atravessar;
2. duas arvores do MESMO tamanho e com os MESMOS xrefs extremos — o cenario que
   reproduzia a `L-24`, em que o indice de uma era reaproveitado pela outra;
3. nomes com acento, para provar que a busca ignora acento pelo caminho do projeto.
"""
from __future__ import annotations

#: Nomes usados pela arvore de referencia. O primeiro e o que o teste de acento
#: consulta; os outros dois sustentam o casamento por sobrenome.
NOMES_DA_ARVORE = (
    "Jose /Silva e Souza/",
    "Maria /dos Santos/",
    "Ana /Silva/",
)

#: Nomes da arvore de MESMO tamanho e MESMOS xrefs, com conteudo diferente — e sem
#: nenhum `Silva`. E o par que prova que o indice nao atravessa arvores.
NOMES_DA_ARVORE_IRMA = (
    "Jose /Costa e Prado/",
    "Maria /dos Ramos/",
    "Ana /Costa/",
)


def gedcom_com(nomes) -> str:
    """GEDCOM minimo com um INDI por nome, na ordem e com os xrefs de `nomes`."""
    linhas = [
        "0 HEAD",
        "1 SOUR TESTE",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
    ]
    for indice, nome in enumerate(nomes, start=1):
        linhas += [f"0 @I{indice}@ INDI", f"1 NAME {nome}", "1 SEX M"]
    linhas.append("0 TRLR")
    return "\n".join(linhas) + "\n"


#: Arvore pronta, com os nomes de referencia.
GED_DA_BUSCA = gedcom_com(NOMES_DA_ARVORE)

#: Arvore pronta, irma da anterior em tamanho e xrefs.
GED_DA_BUSCA_IRMA = gedcom_com(NOMES_DA_ARVORE_IRMA)


__all__ = [
    "GED_DA_BUSCA",
    "GED_DA_BUSCA_IRMA",
    "NOMES_DA_ARVORE",
    "NOMES_DA_ARVORE_IRMA",
    "gedcom_com",
]
