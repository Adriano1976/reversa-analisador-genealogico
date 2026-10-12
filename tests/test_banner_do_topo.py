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
# `RN-16` (T036) dizia que o titulo vivia no `alt`, e NAO como texto na tela. A `RN-23` (T044)
# inverte isso, a pedido do operador: o topo passa a ter arte, subtitulo, titulo em texto e o
# texto de apresentacao. As constantes guardam os DOIS estados, porque o teste do titulo antigo
# continua valendo — o que ele prende agora e que o texto ANTIGO nao voltou.
TEXTO_DO_TITULO = "Analisador Genealógico e de DNA"   # o titulo da era `RN-16`, que saiu de cena
TITULO_NA_TELA = "Analisador Genealógico"             # o titulo de hoje (`RN-23`)
SUBTITULO = "Genetic Genealogy Path Analyzer"
ALT_DA_ARTE = "Ilustração: árvore genealógica, livro aberto e hélice de DNA"

# A caixa MEDIDA do bloco de quadriculado que ficou gravado na arte quando o limite de
# saturacao estava em 14 e depois em 30.
CAIXA_DO_BLOCO = (778, 232, 918, 338)


def _visivel(corpo: str) -> str:
    """So o texto entre tags: e ali que o antigo `<h1>` aparecia."""
    return " ".join(re.findall(r">([^<]+)<", corpo))


def _classe_do_h1(corpo: str) -> str:
    """A lista de classes do `<h1>` do produto. String vazia se ele nao existir.

    Existe porque `_visivel()` NAO responde se o operador ve o titulo: `visually-hidden`
    esconde por folha de estilo, e o texto continua entre as tags. Medido em 2026-10-11 —
    os dois testes que nomeavam "titulo visivel" seguiam verdes com o `<h1>` escondido.
    """
    achado = re.search(r'<h1[^>]*class="([^"]*)"', corpo)
    return achado.group(1) if achado else ""


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
        """`RN-08` e `RN-23`, emendada em 2026-10-11: sem a arte, o titulo tem de APARECER.

        **Este teste media a coisa errada ate 2026-10-11.** Ele procurava `TITULO_NA_TELA` em
        qualquer lugar do documento, e o texto continua no HTML mesmo quando a folha o esconde —
        entao ele passava enquanto o operador ficava **sem titulo nenhum**: o `alt` descreve a
        ilustracao, nao o produto, e o subtitulo e em ingles. Agora ele prende o EFEITO, que e o
        que ele sempre prometeu no docstring: sem a arte, o `<h1>` volta a ser visivel.
        """
        app, cliente, _pasta = cliente_de_upload
        monkeypatch.setitem(app.config, "ARTE_DO_TOPO", os.path.join(_RAIZ, "nao-existe.png"))

        assert cliente.get(CAMINHO).status_code == 404
        tela = cliente.get("/")
        assert tela.status_code == 200
        corpo = tela.get_data(as_text=True)
        assert TITULO_NA_TELA in corpo, "o titulo sumiu do documento quando a arte falta"
        assert "visually-hidden" not in _classe_do_h1(corpo), (
            "sem a arte o `h1` ficou escondido: o operador fica sem nenhuma identificacao do "
            "produto em portugues, que e o caso que este teste existe para impedir"
        )


class TestTopoDaTela:
    """`RN-23` (`T044`): arte reduzida, subtitulo, titulo em texto e o texto de apresentacao.

    ## Por que a ORDEM tem teste proprio

    O pedido foi uma **sequencia**: imagem, subtitulo abaixo dela, titulo em seguida, e o texto.
    Prender so a presenca das quatro coisas deixaria passar uma tela com elas fora de ordem — e
    ordem errada aqui nao e detalhe: o subtitulo e o titulo sao a identificacao do produto, e
    eles vem DEPOIS da arte de proposito.
    """

    @staticmethod
    def _corpo(cliente) -> str:
        return cliente.get("/").get_data(as_text=True)

    @staticmethod
    def _achatado(corpo: str) -> str:
        """O corpo com todo espaco em branco colapsado.

        Necessario porque o template QUEBRA as frases em varias linhas: procurar
        `"ajudar os usuarios a compreender"` no HTML cru falharia por causa da quebra, e nao por
        falta do texto. Medido: a frase fica partida entre `a` e `compreender`.
        """
        return re.sub(r"\s+", " ", corpo)

    def test_a_imagem_foi_reduzida_a_metade(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = self._corpo(cliente)

        assert re.search(r'<img[^>]*src="/banner\.png"[^>]*class="[^"]*\bw-50\b', corpo), (
            "a arte nao foi reduzida a 50% da largura do cartao (`w-50`)"
        )

    def test_a_ordem_e_imagem_subtitulo_titulo_texto(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = self._corpo(cliente)
        i_imagem = corpo.index('src="/banner.png"')
        i_subtitulo = corpo.index(SUBTITULO)
        i_titulo = corpo.index(TITULO_NA_TELA)
        i_texto = corpo.index("Este aplicativo web foi desenvolvido")

        assert i_imagem < i_subtitulo < i_titulo < i_texto, (
            "a ordem pedida era imagem, subtitulo, titulo e texto — a tela entregou outra"
        )

    def test_o_subtitulo_esta_na_tela(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        assert SUBTITULO in self._corpo(cliente)

    def test_o_titulo_existe_como_texto_e_o_antigo_nao_voltou(self, cliente_de_upload):
        """Inverte a `RN-16`: o titulo e TEXTO, e o texto antigo nao ressuscita.

        ## O que este teste mede, e o que ele NAO mede

        `_visivel()` le o texto ENTRE tags, entao ele responde "o titulo existe como texto no
        documento" — que e o que vale para leitor de tela e buscador. Ele **nao** responde se o
        operador VE o titulo: quem responde isso e `test_o_titulo_so_e_escondido_...` abaixo, e
        `test_arte_ausente_devolve_404_...`, na outra classe.

        A distincao foi MEDIDA em 2026-10-11: com o `<h1>` sob `visually-hidden`, os dois testes
        que nomeavam "titulo visivel" continuaram verdes, porque a folha esconde o que o regex
        continua encontrando. O nome e o docstring deste teste passaram a declarar o que ele
        realmente mede, em vez de prometer o que ele nao mede.
        """
        _app, cliente, _pasta = cliente_de_upload

        visivel = _visivel(self._corpo(cliente))

        assert TITULO_NA_TELA in visivel, "o titulo deixou de existir como texto no documento"
        assert TEXTO_DO_TITULO not in visivel, (
            "o titulo ANTIGO voltou para a tela: era para ele ter saido na `RN-16` e nao voltar"
        )

    def test_o_titulo_so_e_escondido_quando_a_arte_esta_na_tela(self, cliente_de_upload):
        """`RN-23` emendada em 2026-10-11: o `h1` duplica a arte, entao ele cede enquanto ela vem.

        A arte do topo ja desenha "Analisador Genealogico". Com os dois visiveis, o produto se
        nomeia duas vezes, uma logo abaixo da outra; sem a arte, esconder o `h1` deixaria o
        operador sem titulo nenhum. A emenda e a condicao: escondido **se, e somente se,** a arte
        responde — e quem responde isso e o servidor (`arte_do_topo_disponivel`), nao o CSS.
        """
        _app, cliente, _pasta = cliente_de_upload

        assert "visually-hidden" in _classe_do_h1(self._corpo(cliente)), (
            "com a arte na tela, o `h1` visivel repete o titulo que a arte ja desenha"
        )

    def test_o_h1_carrega_o_titulo_em_texto(self, cliente_de_upload):
        """O documento nao perde o titulo de nivel 1, e ele agora tem CONTEUDO textual."""
        _app, cliente, _pasta = cliente_de_upload

        corpo = self._corpo(cliente)

        assert re.search(rf"<h1[^>]*>\s*{re.escape(TITULO_NA_TELA)}\s*</h1>", corpo), (
            "o `h1` nao carrega o titulo como texto"
        )
        assert not re.search(r"<h1[^>]*>\s*<img", corpo), (
            "o `h1` voltou a envolver so a imagem: o titulo de nivel 1 ficaria sem texto"
        )

    def test_a_arte_tem_alt_proprio_e_nao_repete_o_titulo(self, cliente_de_upload):
        """`RN-23`: o `alt` descreve a ILUSTRACAO.

        Com o titulo escrito logo abaixo, repetir o titulo no `alt` faria o leitor de tela
        anunciar a mesma coisa duas vezes, uma delas como se fosse uma imagem.
        """
        _app, cliente, _pasta = cliente_de_upload

        corpo = self._corpo(cliente)

        assert f'alt="{ALT_DA_ARTE}"' in corpo, "a arte perdeu o `alt` que a descreve"
        assert f'alt="{TITULO_NA_TELA}"' not in corpo, (
            "o `alt` da arte virou o titulo: o leitor de tela anuncia duas vezes"
        )

    def test_o_texto_de_apresentacao_esta_centralizado_e_em_coluna_estreita(self, cliente_de_upload):
        """`RN-24` (`T045`): o texto vai centralizado, em coluna mais estreita que o cartao.

        O operador pediu a mesma **forma organizada da documentacao**: paragrafo centrado, com a
        linha curta. Antes o texto era `text-start` e corria de ponta a ponta do cartao.

        ## Por que a assercao e estrutural, e nao "contem `text-center`"

        `text-center` sozinho nao prova nada: o `div` que envolve a masthead inteira ja o tem, e
        a assercao passaria **vazia** mesmo com o paragrafo alinhado a esquerda. O que esta preso
        aqui e a ESTRUTURA que produz a coluna — a linha de grade com `justify-content-center` e
        a coluna `col-lg-*` dentro dela —, mais a ausencia do alinhamento a esquerda que existia.
        """
        _app, cliente, _pasta = cliente_de_upload

        corpo = self._corpo(cliente)
        inicio = corpo.index("Este aplicativo web")
        bloco = corpo[:inicio]

        assert "text-start" not in corpo, (
            "o texto de apresentacao voltou a ser alinhado a esquerda"
        )
        assert re.search(r'class="row justify-content-center"', corpo), (
            "o texto perdeu a linha de grade que o centra e o estreita"
        )
        assert re.search(r'class="col-lg-\d+"', corpo), (
            "o texto perdeu a coluna que o estreita: ele volta a correr de ponta a ponta"
        )
        # A coluna tem de vir DEPOIS do titulo e ANTES do texto: a organizacao e a ordem juntas.
        assert bloco.rindex('class="col-lg-') < inicio, "a coluna nao envolve o texto"
        assert bloco.rindex('class="row justify-content-center"') < bloco.rindex('class="col-lg-')

    def test_o_texto_de_apresentacao_esta_na_tela_com_as_enfases(self, cliente_de_upload):
        """As duas frases pedidas, e as tres partes que o operador marcou em negrito."""
        _app, cliente, _pasta = cliente_de_upload

        corpo = self._achatado(self._corpo(cliente))

        for trecho in (
            "Este aplicativo web foi desenvolvido para auxiliar pessoas interessadas em genealogia "
            "documental e genética.",
            "<b>ajudar os usuários a compreender como se relacionam com outras pessoas por meio da "
            "análise da árvore genealógica e de dados de DNA</b>.",
            "<b>Para utilizar o aplicativo, basta carregar</b> sua árvore genealógica, em formato "
            "GEDCOM, e um relatório de DNA do GEDmatch Ancestor Projects, em formato CSV.",
            "<b>A partir do cruzamento desses dados, o aplicativo identifica possíveis conexões "
            "genealógicas entre duas pessoas.</b>",
        ):
            assert trecho in corpo, f"nao achei na tela: {trecho[:60]!r}..."


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
