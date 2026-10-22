"""Os rotulos de parentesco em portugues: `trisavô`, e nao `bisbisavô`.

## Por que este arquivo existe

Em 2026-10-14 o cartao da "Margarida" exibia, na coluna do parentesco:

    Tio/Tia-bisbisbisbisbisbisbisbisavô/avó ↔ Sobrinho(a)-bisbisbisbisbisbisbisbisneto(a)

A palavra nao existe em portugues. O codigo montava o rotulo repetindo `"bis" * (grau - 2)`,
e a repeticao so vale para o SEGUNDO grau acima dos pais: o terceiro e `tris-`, o quarto
`tetra-`, e assim por diante (`avô → bisavô → trisavô → tetravô → pentavô → hexavô`).

## O que este arquivo mede, e o que ele NAO mede

Mede a **palavra**, grau a grau, inclusive os que nenhum cartao atual alcanca — porque o
defeito original nao estava num grau especifico: estava na regra de formacao, e a varredura
de (0,0) a (12,12) mostrou que atingia **todo** grau a partir do quarto. Um teste so no grau
do cartao da Margarida teria fechado 1 caso e deixado os outros abertos.

Nao mede acento de `avô`/`avó` nem a escolha de genero: sao texto de contrato antigo, e
mexer neles mudaria rotulo que ja estava correto.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from core.documentary_relationship import documentary_label, nome_do_grau  # noqa: E402
from core.graus_de_parentesco import geracoes_de_diferenca, nome_do_primo  # noqa: E402
from core.relationship_hypotheses import SCP40_ROWS  # noqa: E402

#: A serie portuguesa, do avo ao nono. A fonte e a nomenclatura genealogica corrente:
#: pais, avos, bisavos, trisavos, tetravos, pentavos, hexavos, heptavos, octavos, nonavos.
SERIE = {
    2: ("avô/avó", "neto(a)"),
    3: ("bisavô/avó", "bisneto(a)"),
    4: ("trisavô/avó", "trisneto(a)"),
    5: ("tetravô/avó", "tetraneto(a)"),
    6: ("pentavô/avó", "pentaneto(a)"),
    7: ("hexavô/avó", "hexaneto(a)"),
    8: ("heptavô/avó", "heptaneto(a)"),
    9: ("octavô/avó", "octaneto(a)"),
    10: ("nonavô/avó", "nonaneto(a)"),
}

#: O que NAO pode aparecer em rotulo nenhum. O detector procura o defeito, e nao a forma
#: correta — a primeira versao dele marcava `bisneto`, que e palavra legitima. A segunda
#: marcava `10º avô`, porque `0º avô` casa DENTRO dele: o `\b` a esquerda resolve.
DEFEITO = re.compile(r"bisbis|\b([aeiou])\1vô|([aeiou])\2neto|\b0º avô")


class TestASerieDosAvos:
    """`trisavô`, `tetravô`... — a serie inteira, e nao so o grau que apareceu na tela."""

    @pytest.mark.parametrize("graus,esperado", sorted(SERIE.items()))
    def test_o_nome_do_avo_esta_na_serie(self, graus, esperado):
        assert nome_do_grau(graus) == esperado[0]

    @pytest.mark.parametrize("graus,esperado", sorted(SERIE.items()))
    def test_o_nome_do_neto_esta_na_serie(self, graus, esperado):
        assert nome_do_grau(graus, plural_neto=True) == esperado[1]

    @pytest.mark.parametrize("graus", sorted(SERIE))
    def test_nenhum_nome_da_serie_e_malformado(self, graus):
        for nome in (nome_do_grau(graus), nome_do_grau(graus, plural_neto=True)):
            assert not DEFEITO.search(nome), (
                f"{nome!r} (grau {graus}) tem palavra malformada: o prefixo do grau nao pode "
                "ser 'bis' repetido, e a consoante final de 'tetra'/'penta' nao pode dobrar a "
                "vogal do radical"
            )

    def test_a_serie_nao_regete_bis(self):
        """O defeito original, fixado: `bis` so aparece UMA vez em cada palavra."""
        for graus in range(3, 11):
            for nome in (nome_do_grau(graus), nome_do_grau(graus, plural_neto=True)):
                assert nome.count("bis") == (1 if graus == 3 else 0), (
                    f"{nome!r} repete 'bis': a partir do quarto grau a serie usa tris/tetra/penta"
                )


class TestORotuloDoCartao:
    """O que efetivamente vai para a tela."""

    @pytest.mark.parametrize("deg_a,deg_b,esperado", [
        (0, 1, "Pai/Mãe ↔ Filho(a)"),
        (0, 2, "Avô/Avó ↔ Neto(a)"),
        (0, 3, "bisavô/avó ↔ bisneto(a)"),
        (0, 4, "trisavô/avó ↔ trisneto(a)"),
        (0, 5, "tetravô/avó ↔ tetraneto(a)"),
    ])
    def test_linha_direta(self, deg_a, deg_b, esperado):
        assert documentary_label(deg_a, deg_b)["label"] == esperado

    @pytest.mark.parametrize("maior,esperado", [
        (3, "Tio/Tia-avô/avó ↔ Sobrinho(a)-neto(a)"),
        (4, "Tio/Tia-bisavô/avó ↔ Sobrinho(a)-bisneto(a)"),
        (5, "Tio/Tia-trisavô/avó ↔ Sobrinho(a)-trisneto(a)"),
        (6, "Tio/Tia-tetravô/avó ↔ Sobrinho(a)-tetraneto(a)"),
    ])
    def test_colateral_tio_tia(self, maior, esperado):
        assert documentary_label(1, maior)["label"] == esperado

    def test_o_caso_da_margarida(self):
        """O cartao que revelou o defeito: `(11, 1)` — 9 vezes removido.

        Antes: `Tio/Tia-bisbisbisbisbisbisbisbisavô/avó ↔ Sobrinho(a)-bisbisbisbisbisbisbisbisneto(a)`
        (64 caracteres de palavra inventada). Agora: 2 palavras curtas.
        """
        d = documentary_label(11, 1)
        assert d["label"] == "Tio/Tia-nonavô/avó ↔ Sobrinho(a)-nonaneto(a)"
        assert d["removed"] if "removed" in d else d["degrees"]["removed"] == 9
        assert len(d["label"]) < 60, (
            "o rotulo da Margarida voltou a ser um paragrafo: era 130 caracteres com o defeito"
        )

    @pytest.mark.parametrize("deg_a,deg_b", [(2, 5), (1, 11), (3, 9), (0, 12), (7, 2)])
    def test_nenhum_rotulo_de_parentesco_e_malformado(self, deg_a, deg_b):
        rotulo = documentary_label(deg_a, deg_b)["label"]
        assert not DEFEITO.search(rotulo), f"rotulo malformado em ({deg_a},{deg_b}): {rotulo!r}"


class TestAGeracaoDeDiferenca:
    """`uma geração de diferença`, e não `1× removido` (2026-10-22).

    O termo antigo tinha dois defeitos: a concordância oscilava (`1× removido` contra
    `2× removidos`, no mesmo par de rótulos) e "removido" é vocabulário de quem já
    conhece a tabela — removido de quê? A forma nova diz o mesmo sem dicionário, e é a
    tradução corrente do inglês *once removed*.
    """

    @pytest.mark.parametrize("quantidade,esperado", [
        (1, "uma geração de diferença"),
        (2, "duas gerações de diferença"),
        (3, "três gerações de diferença"),
        (4, "quatro gerações de diferença"),
        (10, "dez gerações de diferença"),
        (11, "11 gerações de diferença"),
    ])
    def test_a_contagem_por_extenso(self, quantidade, esperado):
        assert geracoes_de_diferenca(quantidade) == esperado

    def test_o_singular_nao_recebe_s(self):
        assert "gerações" not in geracoes_de_diferenca(1)

    @pytest.mark.parametrize("grau,removidos,esperado", [
        (1, 0, "Primos de 1º grau"),
        (2, 1, "Primos de 2º grau (uma geração de diferença)"),
        (3, 2, "Primos de 3º grau (duas gerações de diferença)"),
    ])
    def test_o_nome_do_primo(self, grau, removidos, esperado):
        assert nome_do_primo(grau, removidos) == esperado

    def test_o_rotulo_do_bloco_3_e_o_do_documental_sao_o_mesmo(self):
        """Fonte única: `SCP40_ROWS` e `documentary_label` não podem divergir.

        Antes desta mudança os dois escreviam a mesma relação de dois jeitos — a
        tabela dizia `(1× removido)` e o documental dizia `com 2× remoção` para a
        mesma contagem de gerações.
        """
        for grau in range(1, 6):
            for removidos in range(0, 4):
                if not removidos:
                    continue
                chave = f"{grau}C{removidos}R"
                linha = next((l for l in SCP40_ROWS if l[0] == chave), None)
                rotulo_documental = documentary_label(grau + 1, grau + 1 + removidos)["label"]
                assert rotulo_documental == nome_do_primo(grau, removidos)
                if linha:
                    assert linha[2] == rotulo_documental, (
                        f"{chave}: a tabela publicada e o documental dizem coisas diferentes"
                    )


class TestOsOutrosRamosNaoForamTocados:
    """Irmaos, tio/tia e primos nao usam a serie dos avos, e nao podiam ter mudado."""

    @pytest.mark.parametrize("deg_a,deg_b,esperado", [
        (1, 1, "Irmãos"),
        (1, 2, "Tio/Tia ↔ Sobrinho(a)"),
        (2, 2, "Primos de 1º grau"),
        (2, 3, "Primos de 1º grau (uma geração de diferença)"),
        (2, 4, "Primos de 1º grau (duas gerações de diferença)"),
        (4, 7, "Primos de 3º grau (três gerações de diferença)"),
        (6, 9, "Primos de 5º grau (três gerações de diferença)"),
    ])
    def test_os_rotulos_continuam_iguais(self, deg_a, deg_b, esperado):
        """O par e `(menor, maior)` das subidas ate o MRCA.

        Escrevi esta tabela deslocada na primeira vez — usei `(grau, grau+removidos)`, e o
        grau do primo e `menor - 1`, nao `menor`. O teste me corrigiu: `(1,1)` e Irmaos, e
        nao "Primos de 1º grau".
        """
        assert documentary_label(deg_a, deg_b)["label"] == esperado


class TestAcimaDaSerie:
    """Acima de `nonavô` a serie usa ordinal, e o ordinal esta certo."""

    @pytest.mark.parametrize("graus,esperado", [
        (11, "9º avô/avó"),
        (12, "10º avô/avó"),
    ])
    def test_usa_ordinal_acima_da_serie(self, graus, esperado):
        """`9º avô` para 11 geracoes parece errado e nao e: o ordinal conta a partir de `1º avô`.

        Registro o engano porque eu marquei esta forma como defeito ao revisar: o ordinal de
        `NOVO_ROMANO` conta a partir do AVO, e nao do bisavo — 11 geracoes sao 9 graus acima
        dele. `undecavô` seria a alternativa, e e palavra que quase ninguem reconhece.
        """
        assert nome_do_grau(graus) == esperado

    def test_o_ordinal_nunca_e_zero(self):
        """`10º avô` CONTEM `0º avô` — a checagem tem de ser na abertura, nao por substring.

        Caí nesta duas vezes: primeiro no detector do rotulo, depois aqui. O ordinal de `10º`
        e valido; o que nao pode existir e a string comecando em `0º`.
        """
        for graus in range(11, 16):
            nome = nome_do_grau(graus)
            assert not nome.startswith("0º"), (
                f"grau {graus} caiu em `0º avô`: o ordinal esta deslocado"
            )
            assert re.match(r"^\d+º ", nome), f"grau {graus} nao comecou com ordinal: {nome!r}"
