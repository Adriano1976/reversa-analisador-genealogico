"""As duas visoes do indice, e o que elas NAO podem fazer (feature 052).

## O que este arquivo prende

- a visao por token nasce na MESMA varredura da visao por nome;
- **duas arvores do mesmo tamanho e com os mesmos xrefs extremos nao compartilham
  indice** — o cenario exato que reproduzia a `L-24` antes da feature 048;
- arvore sem grafo nao pendura nada e nao falha (sonda, teste unitario);
- consultas repetidas na mesma arvore devolvem o MESMO objeto, que e o que impede
  pagar a varredura de 35 mil pessoas por busca.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.busca_arvores import GED_DA_BUSCA, GED_DA_BUSCA_IRMA  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from core.homonimos import indice_por_nome, indice_por_token  # noqa: E402


def arvore_de(tmp_path, conteudo: str, nome: str = "arvore.ged"):
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return carregar_arvore(str(caminho))


class TestAsDuasVisoes:
    def test_a_visao_por_token_agrupa_pelo_sobrenome(self, tmp_path):
        arvore = arvore_de(tmp_path, GED_DA_BUSCA)

        tokens = indice_por_token(arvore)

        assert set(tokens["silva"]) == {"@I1@", "@I3@"}

    def test_as_duas_visoes_saem_da_mesma_varredura(self, tmp_path):
        arvore = arvore_de(tmp_path, GED_DA_BUSCA)

        nomes = indice_por_nome(arvore)
        tokens = indice_por_token(arvore)

        # Todo id da visao por token tem de estar na visao por nome.
        ids_por_nome = {pid for ids in nomes.values() for pid in ids}
        ids_por_token = {pid for ids in tokens.values() for pid in ids}
        assert ids_por_token == ids_por_nome

    def test_a_segunda_consulta_devolve_o_mesmo_objeto(self, tmp_path):
        arvore = arvore_de(tmp_path, GED_DA_BUSCA)

        assert indice_por_token(arvore) is indice_por_token(arvore)


class TestSemColisao:
    def test_duas_arvores_do_mesmo_tamanho_nao_compartilham_indice(self, tmp_path):
        """A `L-24` em uma linha: a segunda arvore nao pode enxergar a primeira."""
        primeira = arvore_de(tmp_path, GED_DA_BUSCA, "primeira.ged")
        segunda = arvore_de(tmp_path, GED_DA_BUSCA_IRMA, "segunda.ged")

        assert len(primeira[0]) == len(segunda[0])
        assert sorted(primeira[0])[0] == sorted(segunda[0])[0]
        assert sorted(primeira[0])[-1] == sorted(segunda[0])[-1]

        tokens_da_segunda = indice_por_token(segunda)

        assert "silva" not in tokens_da_segunda, (
            "o indice da segunda arvore citou um sobrenome que so existe na primeira"
        )
        assert "costa" in tokens_da_segunda


class TestArvoreSemGrafo:
    def test_sem_grafo_constroi_e_nao_pendura(self, tmp_path):
        arvore = arvore_de(tmp_path, GED_DA_BUSCA)
        sem_grafo = (arvore[0], arvore[1], None, arvore[3])

        tokens = indice_por_token(sem_grafo)

        assert "silva" in tokens

    def test_sem_grafo_nao_falha_na_segunda_chamada(self, tmp_path):
        arvore = arvore_de(tmp_path, GED_DA_BUSCA)
        sem_grafo = (arvore[0], arvore[1], None, arvore[3])

        assert indice_por_token(sem_grafo) == indice_por_token(sem_grafo)
