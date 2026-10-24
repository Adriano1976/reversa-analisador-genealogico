"""Prova do memo de índices de matching preso ao grafo da árvore.

## O que este arquivo protege

`build_ged_indexes` percorre as 19.403 pessoas e custa ~8,7 s. Ele passa a guardar o trio no
próprio grafo da árvore, e a primeira coisa que não pode acontecer é o índice de uma árvore
aparecer na outra — é exatamente a classe do defeito `L-24`, que este projeto já sofreu com o
cache de nomes do módulo documental.

As provas: o mesmo objeto nas duas chamadas, a segunda não percorre as pessoas, e duas árvores
de mesmo tamanho e mesmos `xref` extremos **não** compartilham nada.
"""
import os
import sys

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

import pytest

from core import matching
from core.matching import build_ged_indexes
from parsers.gedcom_parser import carregar_arvore

# As duas arvores tem o MESMO numero de pessoas e os MESMOS xrefs extremos (@I1@ e @I9@),
# e diferem so no xref e no nome do meio. Essa e a assinatura que o `L-24` mostrou ser
# suficiente para duas arvores colidirem.
GEDCOM_A = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Ana /Lima/\n"
    "0 @I2@ INDI\n"
    "1 NAME Bia /Rocha/\n"
    "0 @I9@ INDI\n"
    "1 NAME Caio /Souza/\n"
    "0 TRLR\n"
)

GEDCOM_B = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Ana /Lima/\n"
    "0 @I4@ INDI\n"
    "1 NAME Dora /Melo/\n"
    "0 @I9@ INDI\n"
    "1 NAME Caio /Souza/\n"
    "0 TRLR\n"
)


def _arvore(tmp_path, conteudo: str, nome: str = "arvore.ged"):
    caminho = tmp_path / nome
    caminho.write_bytes(conteudo.encode("utf-8"))
    return carregar_arvore(str(caminho))


class TestMemo:
    def test_duas_chamadas_devolvem_o_mesmo_objeto(self, tmp_path):
        arvore = _arvore(tmp_path, GEDCOM_A)

        primeira = build_ged_indexes(arvore)
        segunda = build_ged_indexes(arvore)

        assert primeira is segunda, "o memo tem de devolver o MESMO trio"

    def test_a_segunda_chamada_nao_percorre_as_pessoas(self, tmp_path, monkeypatch):
        arvore = _arvore(tmp_path, GEDCOM_A)
        chamadas = {"n": 0}
        original = matching.get_name

        def contar(person):
            chamadas["n"] += 1
            return original(person)

        monkeypatch.setattr(matching, "get_name", contar)

        build_ged_indexes(arvore)
        depois_da_primeira = chamadas["n"]
        build_ged_indexes(arvore)

        assert depois_da_primeira == len(arvore[0]), "a primeira construcao percorre cada pessoa"
        assert chamadas["n"] == depois_da_primeira, "a segunda chamada nao podia percorrer ninguem"

    def test_o_trio_devolvido_tem_os_tres_indices(self, tmp_path):
        ged_index, surname_index, features = build_ged_indexes(_arvore(tmp_path, GEDCOM_A))

        assert "ana lima" in ged_index
        # "Ana" e GENERIC_GIVEN: o sobrenome dela e lido como prenome, comportamento antigo e
        # documentado. Por isso a prova do indice de sobrenomes usa a Bia.
        assert "rocha" in surname_index
        assert len(features) == 3


class TestNaoContaminacao:
    def test_duas_arvores_de_mesmo_tamanho_nao_compartilham(self, tmp_path):
        a = _arvore(tmp_path, GEDCOM_A, "a.ged")
        b = _arvore(tmp_path, GEDCOM_B, "b.ged")
        assert len(a[0]) == len(b[0]) == 3
        assert sorted(a[0])[0] == sorted(b[0])[0] == "@I1@"
        assert sorted(a[0])[-1] == sorted(b[0])[-1] == "@I9@"

        indice_a = build_ged_indexes(a)
        indice_b = build_ged_indexes(b)

        assert indice_a is not indice_b, "duas arvores distintas nao podem compartilhar o memo"
        assert not any("dora" in chave for chave in indice_a[0]), (
            "o nome exclusivo da arvore B apareceu no indice da arvore A"
        )
        assert any("dora" in chave for chave in indice_b[0])
