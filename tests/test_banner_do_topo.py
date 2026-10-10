"""T036 (feature `011-escolher-arquivo-da-lista`): a arte do topo no lugar do titulo.

## O que foi pedido, e o que a arte enviada tinha de errado

O operador pediu que o `<h1>Analisador Genealógico e de DNA</h1>` virasse a imagem que ele
mandou. A imagem chegou em **`RGB`, sem canal alfa**, com o **quadriculado de transparencia
gravado** no bitmap: branco `ffffff` alternando com cinza `c7c7c7` em blocos de 8 px. Servir
aquele arquivo desenharia uma grade cinza atras do logo.

O que a rota serve e uma **renderizacao derivada**, com o fundo removido. A receita esta em
`tests/banner_da_tela.py`, ao lado destes testes, como a do icone esta em
`tests/icone_de_atalho.py`.

## Por que ha um teste da ARTE, e nao so da rota

Porque a receita errou **duas vezes** na mesma sessao, e das duas vezes a medicao que eu tinha
dizia "zero residuo": ela usava o MESMO limite que a regra de remocao, entao nao podia acusar
nada. Quem pegou o defeito foi compor a arte sobre magenta e olhar. O teste abaixo prende a
caixa exata do bloco que sobrou — `(778,232)` a `(918,338)`, sob o cone de luz do abajur, onde
a luz ambar tinge o quadriculado e a saturacao passa de 42 —, com um limite **mais estrito** que
o da regra, para nao repetir o erro de medir o residuo com a propria regra.
"""
from __future__ import annotations

import io
import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from tests.banner_da_tela import ARTE_DE_RUNTIME, FONTE, residuo_de_fundo  # noqa: E402

CAMINHO = "/banner.png"
TEXTO_DO_TITULO = "Analisador Genealógico e de DNA"

# A caixa MEDIDA do bloco de quadriculado que ficou gravado na arte quando o limite de
# saturacao estava em 14 e depois em 30.
CAIXA_DO_BLOCO = (778, 232, 918, 338)


def _visivel(corpo: str) -> str:
    """So o texto entre tags: e ali que o antigo `<h1>` aparecia."""
    return " ".join(re.findall(r">([^<]+)<", corpo))


class TestRotaDaArte:
    """A rota da arte, com o mesmo contrato da rota do icone."""

    def test_a_rota_serve_a_arte(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        resposta = cliente.get(CAMINHO)

        assert resposta.status_code == 200
        assert resposta.headers["Content-Type"] == "image/png"
        assert len(resposta.get_data()) > 1000, "a resposta veio vazia ou truncada"

    def test_a_arte_servida_e_a_derivada_e_nao_a_fonte(self, cliente_de_upload):
        """A fonte tem o quadriculado gravado; a servida nao pode ser ela.

        A comparacao e por TAMANHO, e nao por bytes: a fonte e `RGB` com o xadrez embutido e
        mede 817.469 bytes; a derivada tem alfa e mede menos. Se alguem trocar a rota para
        servir a fonte, a tela ganha a grade cinza de volta e este teste cai.
        """
        _app, cliente, _pasta = cliente_de_upload

        servida = cliente.get(CAMINHO).get_data()

        assert len(servida) == os.path.getsize(ARTE_DE_RUNTIME)
        assert len(servida) != os.path.getsize(FONTE), (
            "a rota esta servindo a arte ORIGINAL, com o quadriculado gravado"
        )

    def test_escrita_na_rota_e_recusada(self, cliente_de_upload):
        """So `GET`: a recusa sai do roteador, sem validacao nossa que possa divergir."""
        _app, cliente, _pasta = cliente_de_upload

        assert cliente.post(CAMINHO, data={"x": "y"}).status_code == 405

    def test_a_resposta_traz_marca_de_versao(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        assert cliente.get(CAMINHO).headers.get("ETag")

    def test_requisicao_repetida_nao_traz_corpo(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        marca = cliente.get(CAMINHO).headers["ETag"]

        repetida = cliente.get(CAMINHO, headers={"If-None-Match": marca})

        assert repetida.status_code == 304
        assert repetida.get_data() == b""

    def test_arte_ausente_devolve_404_e_a_tela_continua_de_pe(self, cliente_de_upload, monkeypatch):
        """`RN-08`: a arte pode faltar, e a tela nao pode cair por causa dela.

        E o `alt` da imagem e o que garante que o operador ainda le o titulo — o `h1` perdeu
        o texto visivel, mas nao o significado.
        """
        app, cliente, _pasta = cliente_de_upload
        monkeypatch.setitem(app.config, "ARTE_DO_TOPO", os.path.join(_RAIZ, "nao-existe.png"))

        assert cliente.get(CAMINHO).status_code == 404
        tela = cliente.get("/")
        assert tela.status_code == 200
        assert TEXTO_DO_TITULO in tela.get_data(as_text=True), (
            "o titulo sumiu da tela quando a arte falta: sem o `alt`, o operador fica sem titulo"
        )


class TestArteNoLugarDoTitulo:
    """O pedido: a imagem ocupa o lugar do titulo em texto."""

    def test_a_tela_mostra_a_arte(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.get("/").get_data(as_text=True)

        assert 'src="/banner.png"' in corpo, "a arte do topo nao esta na tela"
        assert "img-fluid" in corpo, "a imagem nao foi limitada a largura do cartao"

    def test_o_titulo_em_texto_saiu_da_tela_visivel(self, cliente_de_upload):
        """Emparelhado com a presenca da arte, para nao passar vazio."""
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.get("/").get_data(as_text=True)
        visivel = _visivel(corpo)

        assert 'src="/banner.png"' in corpo, "pre-condicao: a arte tem de estar na tela"
        assert TEXTO_DO_TITULO not in visivel, (
            "o titulo continua escrito na tela, alem da arte: era para ele SAIR"
        )

    def test_o_titulo_continua_no_alt_e_no_documento(self, cliente_de_upload):
        """O `h1` fica, com a imagem dentro: o documento nao perde o titulo de nivel 1."""
        _app, cliente, _pasta = cliente_de_upload

        corpo = cliente.get("/").get_data(as_text=True)

        assert f'alt="{TEXTO_DO_TITULO}"' in corpo, (
            "a imagem perdeu o `alt`: um leitor de tela nao teria o que anunciar"
        )
        assert re.search(r"<h1[^>]*>\s*<img", corpo), (
            "o `h1` deixou de envolver a imagem"
        )


class TestArteDerivada:
    """A arte de runtime, medida. Foi aqui que a receita falhou duas vezes."""

    @pytest.fixture
    def arte(self):
        from PIL import Image
        if not os.path.exists(ARTE_DE_RUNTIME):
            pytest.fail(
                f"arte de runtime ausente em {ARTE_DE_RUNTIME}. Regenere com "
                "'python -m tests.banner_da_tela'"
            )
        return Image.open(ARTE_DE_RUNTIME)

    def test_a_arte_tem_canal_alfa(self, arte):
        """A fonte e `RGB`: sem alfa, o quadriculado gravado apareceria na tela."""
        assert arte.mode == "RGBA", f"a arte de runtime esta em {arte.mode}"

    def test_a_arte_transparente_e_uma_fatia_util_da_imagem(self, arte):
        """Nem zero (quadriculado intacto) nem quase tudo (arte comida).

        O limite e LARGO de proposito, e a segunda metade da prova e o teste das partes claras:
        aqui se prende que houve remocao, la se prende que a arte sobreviveu. A composicao atual
        (arvore, livro e texto, sem microscopio nem abajur) ocupa menos da tela e mede **71,8 %**
        transparente — o limite antigo, de 60 %, valia para a composicao anterior, que era mais
        larga. Ajustar o teto NAO afrouxa a prova: quem responde "a arte continua la" e o teste
        seguinte, ponto a ponto.
        """
        total = arte.size[0] * arte.size[1]
        opacos = arte.convert("RGBA").getchannel("A").histogram()[255]
        transparentes = 100 * (total - opacos) / total

        assert 10 <= transparentes <= 90, (
            f"{transparentes:.1f} % transparente. Zero significa quadriculado nao removido; "
            "quase tudo significa que a regra comeu a arte"
        )

    def test_a_arte_nao_tem_bloco_de_quadriculado(self, arte):
        """A regressao exata: um bloco de fundo que ficou gravado na composicao ANTERIOR.

        A caixa `(778,232)` a `(918,338)` era o bloco sob o cone de luz do abajur, onde a luz
        ambar tingia o quadriculado e a saturacao passava do limite. A composicao de hoje nao tem
        abajur, e essa caixa e FUNDO — mas ela fica como caixa de regressao: qualquer pixel de
        fundo opaco ali significa que o quadriculado voltou a sobreviver a remocao.

        `residuo_de_fundo` usa `SATURACAO_MAXIMA - 5`, mais apertado que a regra de remocao.
        Medir o residuo com o mesmo limite da regra devolveria sempre zero, e foi esse erro que
        deixou o bloco passar duas vezes.
        """
        bloco = arte.convert("RGBA").crop(CAIXA_DO_BLOCO)

        assert residuo_de_fundo(bloco) == 0, (
            f"voltou a haver fundo opaco em {CAIXA_DO_BLOCO}: o quadriculado sobreviveu a remocao"
        )

    def test_a_arte_nao_perdeu_as_partes_claras_que_sao_arte(self, arte):
        """O outro lado do risco: a regra que remove fundo claro nao pode furar a pintura.

        ## Estes pontos foram MEDIDOS na composicao de 2026-10-10

        Todos verificados como opacos no arquivo de runtime. Eles cobrem as duas famílias de risco:

        - **arte ESCURA e pouco saturada** (capa `sat=53`, lombada `sat=35`, base do livro
          `sat=22`) — o que um limite de brilho baixo demais comecaria a comer;
        - **arte CLARA e quase neutra** (o preenchimento do texto dourado, `sat~24`) — o que um
          teto de saturacao largo demais come, e foi o defeito MEDIDO: com um unico limite de
          brilho, as letras de "Analisador Genealogico" ficaram OCAS. A correcao esta em
          `_e_fundo`, que usa teto estreito na faixa de 160 a 190.

        Se alguem "resolver" um residuo de fundo baixando o brilho ou alargando a saturacao, um
        destes pontos vira buraco e este teste cai.
        """
        rgba = arte.convert("RGBA")
        for rotulo, (x, y) in {
            "folha alta esquerda": (170, 75),
            "folha alta direita": (860, 75),
            "galho esquerdo": (300, 130),
            "galho direito": (700, 130),
            "preenchimento do texto (A)": (270, 212),
            "pagina esquerda": (430, 360),
            "pagina direita": (600, 360),
            "lombada": (512, 420),
            "capa esquerda": (370, 470),
            "capa direita": (660, 470),
            "base do livro": (512, 500),
        }.items():
            assert rgba.getpixel((x, y))[3] == 255, (
                f"a arte perdeu {rotulo} em ({x}, {y}): a remocao de fundo comeu tinta"
            )
