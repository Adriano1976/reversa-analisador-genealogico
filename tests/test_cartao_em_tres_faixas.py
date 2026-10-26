"""O cartão de conexão em três faixas — título, selos e sinais (feature 036).

A mudança é de arranjo, e arranjo não quebra sozinho: um `span` que sai do lugar devolve o
título para a linha dos selos sem erro nenhum na tela. Este arquivo prende o arranjo no
template **renderizado** (não no fonte) e as regras que o sustentam na folha.

O recorte é o mesmo dos outros testes de cartão: `render_template` com o dicionário sintético
de `tests/fixtures/resultado_para_cartao.py`, sem subir servidor e sem arquivo real
(princípio I).
"""
from __future__ import annotations

import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pasta in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _pasta not in sys.path:
        sys.path.insert(0, _pasta)

from tests.fixtures import resultado_para_cartao as fixo  # noqa: E402

TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")
FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")
MARCADOR = '<details class="card cartao-do-resultado"'


def _pagina(resultado=None) -> str:
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        return render_template("index.html", dna_results=[resultado or fixo.resultado()])


def _cartao(pagina: str) -> str:
    partes = pagina.split(MARCADOR)
    assert len(partes) == 2, "o cartão não foi renderizado"
    return partes[1]


def _cabecalho(cartao: str) -> str:
    achado = re.search(r'(?s)<div class="card-header">(.*?)</div>', cartao)
    assert achado, "o cartão perdeu o `card-header`"
    return achado.group(1)


@pytest.fixture(scope="module")
def pagina() -> str:
    return _pagina()


@pytest.fixture(scope="module")
def cabecalho(pagina) -> str:
    return _cabecalho(_cartao(pagina))


@pytest.fixture(scope="module")
def folha() -> str:
    with open(FOLHA, encoding="utf-8") as arquivo:
        return arquivo.read()


class TestOArranjoDoCabecalho:
    """O que o operador vê fechado: título, selos e sinais, nesta ordem."""

    def test_o_titulo_vem_antes_dos_selos_e_dos_sinais(self, cabecalho):
        for marcador in ("titulo-da-conexao", "selos-do-cabecalho", "cabecalho-sinais"):
            assert marcador in cabecalho, f"a faixa `{marcador}` sumiu do cabeçalho"
        posicoes = [
            cabecalho.index("titulo-da-conexao"),
            cabecalho.index("selos-do-cabecalho"),
            cabecalho.index("cabecalho-sinais"),
        ]
        assert posicoes == sorted(posicoes), (
            "as três faixas saíram de ordem no cabeçalho: o título tem de vir primeiro, "
            "depois os selos, depois os sinais"
        )

    def test_o_titulo_tem_faixa_propria(self, cabecalho):
        assert re.search(
            r'(?s)<span class="titulo-da-conexao">.*?</span>\s*<span class="selos-do-cabecalho">',
            cabecalho,
        ), (
            "o título e os selos voltaram a dividir a mesma faixa: o `span` do título tem de "
            "fechar antes de a faixa dos selos abrir"
        )

    def test_os_selos_ficam_dentro_da_faixa_propria(self, cabecalho):
        """O recorte vai da faixa dos selos até o "Voltar": os quatro selos moram ali."""
        inicio = cabecalho.index("selos-do-cabecalho")
        fim = cabecalho.index("voltar-ao-indice")
        faixa = cabecalho[inicio:fim]
        for selo in ("selo-dado", "estado-CONFLITANTE", "validacao-conflito"):
            assert selo in faixa, (
                f"o selo `{selo}` saiu da faixa própria e voltou a competir com o título"
            )

    def test_o_voltar_e_o_chevron_ficam_no_mesmo_grupo_flex(self, cabecalho):
        """Os dois controles têm de ser irmãos no mesmo contêiner.

        Antes, o "Voltar" era item do grid e o chevron era um `::after` absoluto do
        `summary`. Quando um selo novo aumentava a altura do cabeçalho, cada um era
        posicionado por uma referência diferente e o grupo desalinhava.
        """
        assert 'class="controles-do-cabecalho"' in cabecalho
        grupo = cabecalho.split('class="controles-do-cabecalho"', 1)[1]
        assert "voltar-ao-indice" in grupo
        assert "indicador-de-abrir" in grupo
        assert grupo.index("voltar-ao-indice") < grupo.index("indicador-de-abrir"), (
            "o indicador tem de vir depois do Voltar, como no desenho aprovado"
        )

    def test_o_cabecalho_nao_ganhou_div(self, cabecalho):
        """Um `div` aqui truncaria o extrator dos testes no primeiro `</div>`."""
        assert "<div" not in cabecalho, (
            "entrou um `div` dentro do `card-header`: os extratores de `_cabecalhos` cortam "
            "o cabeçalho no primeiro `</div>` e o resto da extração se perde"
        )

    def test_o_link_continua_no_cabecalho_e_intacto(self, cabecalho):
        """O desenho novo não pode custar o contrato do "Voltar"."""
        assert re.search(
            r'<a class="voltar-ao-indice" href="#resultados">Voltar'
            r'<span class="visually-hidden">',
            cabecalho,
        ), (
            "o link de retorno saiu do cabeçalho ou perdeu o formato que os testes prendem"
        )


class TestAFolha:
    """As regras que sustentam o arranjo, escopadas no cartão."""

    def test_as_tres_faixas_tem_area_de_grid(self, folha):
        assert "grid-template-areas" in folha, (
            "a folha perdeu o arranjo em três faixas"
        )
        for area in ('"titulo acao"', '"selos acao"', '"sinais acao"'):
            assert area in folha, f"a área {area} sumiu do arranjo"

    def test_o_titulo_mede_1_4_rem(self, folha):
        regra = re.search(r"\.titulo-da-conexao\{([^}]*)\}", folha)
        assert regra, "a regra do título sumiu da folha"
        assert "font-size:1.4rem" in regra.group(1), (
            "o título deixou de medir 1,4 rem — a escala decidida em 2026-10-19"
        )

    def test_o_casco_e_escopado_no_cartao(self, folha):
        regra = re.search(r"details\.card\.cartao-do-resultado\{([^}]*)\}", folha)
        assert regra, "o casco do cartão não está escopado em `.cartao-do-resultado`"
        corpo = regra.group(1)
        # O raio saiu do literal 16 px em 2026-10-26 e passou a ler o degrau de fora da
        # escala (`--r-3`), o mesmo do cartão principal. O que este teste prende continua
        # sendo o mesmo: o casco TEM raio próprio, e ele é o maior da escala.
        for declaracao in ("border-radius:var(--r-3)", "linear-gradient", "position:relative"):
            assert declaracao in corpo, f"o casco perdeu `{declaracao}`"

    def test_a_barra_lateral_existe(self, folha):
        assert ".cartao-do-resultado::before{" in folha, (
            "a barra lateral do cartão sumiu"
        )

    def test_o_hover_do_cabecalho_nao_sublinha(self, folha):
        assert re.search(
            r"\.cartao-do-resultado > summary\.sumario-do-cartao:hover\{[^}]*"
            r"text-decoration:none",
            folha,
        ), (
            "a regra global `details>summary:hover` voltou a valer no cartão: o cabeçalho "
            "inteiro sublinha ao passar o mouse"
        )

    def test_o_telefone_empilha_as_faixas(self, folha):
        assert '"titulo" "selos" "sinais" "acao"' in folha, (
            "o arranjo de telefone sumiu: o 'Voltar' volta a disputar a linha do título"
        )
