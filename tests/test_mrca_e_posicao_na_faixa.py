"""O antepassado comum mais recente e a posicao do valor na faixa (feature 043).

## O que este arquivo prende

O bloco 3 da tela passou a mostrar duas colunas que a lista de nomes escondia:

1. **Antepassado comum mais recente** — `bisavós` para um primo de 2º grau. Nao e
   dado do Shared cM Project: e a **definicao** do parentesco. O risco obvio desta
   coluna e inventar grau, e e ele que a ida e volta fecha: `GRAUS_ATE_O_MRCA`
   alimenta `documentary_label`, e `documentary_label` tem de devolver a mesma
   chave. Duas fontes que discordem quebram aqui, e nao na tela.
2. **Onde o valor cai** — `na ponta inferior` da faixa publicada. Descreve a fonte;
   nao e probabilidade.

## O que este arquivo NAO mede

Nao mede a tabela do HTML (isso e `test_tabela_do_bloco_3.py`) nem a redacao exata
das frases: `na ponta inferior` pode virar `no extremo inferior` sem que regra
nenhuma mude.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from core import graus_de_parentesco  # noqa: E402
from core.documentary_relationship import documentary_label, nome_do_grau  # noqa: E402
from core.relationship_hypotheses import (  # noqa: E402
    GRAUS_ATE_O_MRCA,
    GRAUS_DAS_MEIAS_RELACOES,
    POSICOES_NA_FAIXA,
    SCP40_ROWS,
    mrca_da_relacao,
    posicao_na_faixa,
    possible_relationships,
)

CHAVES_PUBLICADAS = [linha[0] for linha in SCP40_ROWS]


class TestOAntepassadoComum:
    def test_toda_relacao_publicada_diz_onde_procurar(self):
        sem_mrca = [chave for chave in CHAVES_PUBLICADAS if not mrca_da_relacao(chave)]
        assert not sem_mrca, (
            f"{sem_mrca} ficaram sem antepassado comum: a coluna apareceria vazia no cartao"
        )

    def test_o_grado_concorda_com_o_rotulo_documental(self):
        """A ida e volta: os graus daqui DEVOLVEM a mesma chave em `documentary_label`.

        As tres meias-relacoes ficam de fora porque `documentary_label` nao as produz
        — `(1,1)` e SIBLINGS para ele, e a diferenca da meia-relacao nao esta no grau.
        """
        divergentes = []
        for chave, graus in GRAUS_ATE_O_MRCA.items():
            devolvida = documentary_label(*graus)["key"]
            if devolvida != chave:
                divergentes.append((chave, graus, devolvida))
        assert not divergentes, (
            "grau e rotulo discordam (chave, graus, o que documentary_label devolveu): "
            f"{divergentes}"
        )

    def test_meia_relacao_tem_o_grado_do_equivalente_completo(self):
        """Meia-relacao nao e mais funda: o que muda e quantos dos dois sao compartilhados."""
        pares = {
            "HALF_SIBLINGS": (1, 1),
            "HALF_1C": (2, 2),
            "HALF_2C": (3, 3),
        }
        assert GRAUS_DAS_MEIAS_RELACOES == pares
        for chave, esperado in pares.items():
            mrca = mrca_da_relacao(chave)
            assert tuple(mrca["graus"]) == esperado
            assert "um de dois" in mrca["rotulo"], (
                f"{chave}: o rotulo precisa dizer que so um lado e compartilhado, "
                f"e veio {mrca['rotulo']!r}"
            )
            assert "compartilhado" in mrca["detalhe"]

    def test_grado_diferente_mostra_os_dois_lados(self):
        """`2C1R` — "primo de 2º grau dos pais" — nao tem UM antepassado so.

        De um lado sao 3 geracoes, do outro 4. Escolher um dos dois seria inventar
        qual das pessoas e a raiz da analise.
        """
        mrca = mrca_da_relacao("2C1R")
        assert mrca["graus"] == [3, 4]
        assert mrca["rotulo"] == "bisavós e trisavós"
        assert mrca["detalhe"] == "3 e 4 gerações acima"

    def test_ascendente_direto_avisa_que_um_dos_dois_e_o_antepassado(self):
        mrca = mrca_da_relacao("GRANDPARENT")
        assert mrca["rotulo"] == "avós"
        assert "próprio antepassado" in mrca["detalhe"]

    def test_chave_desconhecida_nao_inventa_antepassado(self):
        assert mrca_da_relacao("1C6R") is None


class TestOPluralDoAntepassado:
    """`bisavós`, e nao `bisavôs`: o acento muda com o numero."""

    PLURAL = {
        2: "avós",
        3: "bisavós",
        4: "trisavós",
        5: "tetravós",
        6: "pentavós",
        7: "hexavós",
        8: "heptavós",
        9: "octavós",
        10: "nonavós",
    }

    @pytest.mark.parametrize("graus,esperado", sorted(PLURAL.items()))
    def test_o_plural_esta_na_serie(self, graus, esperado):
        assert nome_do_grau(graus, plural_ancestral=True) == esperado

    def test_o_genitor_e_pai_e_mae_nao_avo(self):
        assert nome_do_grau(1, plural_ancestral=True) == "pais"
        assert nome_do_grau(1) == "pai/mãe"

    @pytest.mark.parametrize("graus", sorted(PLURAL))
    def test_nenhum_plural_e_formado_com_s(self, graus):
        plural = nome_do_grau(graus, plural_ancestral=True)
        assert "ôs" not in plural, (
            f"{plural!r}: o plural do avo troca o acento (`avós`), nao ganha `s`"
        )

    def test_a_serie_continua_valendo_para_o_neto(self):
        assert nome_do_grau(3, plural_neto=True) == "bisneto(a)"


class TestAposicaoNaFaixa:
    @pytest.mark.parametrize("cm,baixo,alto,esperado", [
        (0, 0, 100, "ponta_inferior"),
        (10, 0, 100, "ponta_inferior"),
        (30, 0, 100, "abaixo_do_centro"),
        (50, 0, 100, "centro"),
        (70, 0, 100, "acima_do_centro"),
        (95, 0, 100, "ponta_superior"),
        (100, 0, 100, "ponta_superior"),
    ])
    def test_a_faixa_e_lida_em_cinco_posicoes(self, cm, baixo, alto, esperado):
        posicao = posicao_na_faixa(cm, baixo, alto)
        assert posicao["chave"] == esperado
        assert posicao["rotulo"] == POSICOES_NA_FAIXA[esperado]

    def test_faixa_de_largura_zero_fica_no_centro(self):
        """Sem intervalo nao ha posicao a ler — e o centro e a resposta honesta."""
        posicao = posicao_na_faixa(80, 80, 80)
        assert posicao["chave"] == "centro"
        assert posicao["percentual"] == 50

    def test_fora_da_faixa_nao_estoura_a_barra(self):
        """A barra e desenhada com `left: percentual%`: 120% sairia da faixa."""
        for cm in (-50, 0, 500):
            posicao = posicao_na_faixa(cm, 10, 100)
            assert 0 <= posicao["percentual"] <= 100
            assert 0.0 <= posicao["fracao"] <= 1.0


class TestOPayloadDoBloco3:
    def test_cada_possibilidade_leva_o_antepassado_e_a_posicao(self):
        bloco = possible_relationships(150)
        candidatas = bloco["possible_relationships"]
        assert candidatas
        for candidata in candidatas:
            assert candidata["mrca"] and candidata["mrca"]["rotulo"]
            assert candidata["posicao"] and candidata["posicao"]["rotulo"]

    def test_o_payload_atravessa_json(self):
        """O nucleo tambem alimenta o historico: nada aqui pode ser nao serializavel."""
        bloco = possible_relationships(150)
        json.dumps(bloco)

    def test_nao_ha_probabilidade_nem_percentual_de_parentesco(self):
        """A coluna `Probabilidade` foi recusada em 2026-10-22 — e nao pode voltar.

        A fonte nao publica probabilidade por relacao, e os percentuais somariam 100%,
        fechando o mundo num conjunto que o projeto recusa fechar. O que entrou no
        lugar foi `posicao`, que descreve a faixa publicada.
        """
        bloco = possible_relationships(150)
        for candidata in bloco["possible_relationships"]:
            proibidas = {chave for chave in candidata if "probab" in chave.lower()}
            assert not proibidas, f"o payload voltou a carregar probabilidade: {proibidas}"


class TestAMudancaDeCasaDaSerie:
    def test_documentary_relationship_reexporta_o_nome_do_grau(self):
        """Quem importava `nome_do_grau` de la continua funcionando."""
        assert nome_do_grau is graus_de_parentesco.nome_do_grau

    def test_o_modulo_novo_nao_importa_nada_do_projeto(self):
        """Ele e o corte do ciclo: se importar `networkx`, o caminho do CSV o arrasta.

        `core.relationship_hypotheses` importa este modulo, e aquele e importado no
        caminho da leitura do CSV. Um import de grafo aqui apareceria la.
        """
        caminho = os.path.join(_RAIZ, "src", "core", "graus_de_parentesco.py")
        with open(caminho, encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
        imports = [linha.strip() for linha in linhas
                   if linha.startswith(("import ", "from "))]
        assert imports == ["from __future__ import annotations"], (
            f"o modulo sem dependencia ganhou import: {imports}"
        )
