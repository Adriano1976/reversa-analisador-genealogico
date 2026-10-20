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
        """`RN-08`: a arte pode faltar, e a tela nao pode cair por causa dela.

        **Este teste media a coisa errada ate 2026-10-11** — procurava `TITULO_NA_TELA` em
        qualquer lugar do documento, e o texto continua no HTML mesmo quando a folha o esconde.
        Ele passava enquanto o operador ficava **sem titulo nenhum**.

        Hoje a assercao e a mesma, mas o motivo mudou: o `<h1>` e **sempre visivel** desde
        2026-10-16 (a arte nova nao traz o texto), entao a linha virou guarda contra alguem
        voltar a esconde-lo.
        """
        app, cliente, _pasta = cliente_de_upload
        monkeypatch.setitem(app.config, "ARTE_DO_TOPO", os.path.join(_RAIZ, "nao-existe.png"))

        assert cliente.get(CAMINHO).status_code == 404
        tela = cliente.get("/")
        assert tela.status_code == 200
        corpo = tela.get_data(as_text=True)
        assert TITULO_NA_TELA in corpo, "o titulo sumiu do documento quando a arte falta"
        assert "visually-hidden" not in _classe_do_h1(corpo), (
            "o `h1` ficou escondido: o operador fica sem nenhuma identificacao do produto em "
            "portugues, que e o caso que este teste existe para impedir"
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

    def test_o_titulo_do_produto_esta_sempre_visivel(self, cliente_de_upload):
        """`RN-23`: o titulo e **texto visivel**, e nao depende da arte.

        ## A condicao que existiu aqui, e por que ela saiu

        Entre 2026-10-11 e 2026-10-16 o `h1` era escondido **enquanto a arte do topo respondesse**,
        porque aquela arte trazia "Analisador Genealogico" DESENHADO: com os dois visiveis, o
        produto se nomeava duas vezes, uma logo abaixo da outra. Quem respondia era o servidor
        (`arte_do_topo_disponivel`, um processador de contexto), e nao o CSS — folha de estilo nao
        sabe se uma imagem carregou.

        A arte trocada em 2026-10-16 **nao tem o texto**, entao a condicao perdeu o objeto:
        esconder o `h1` passaria a deixar a tela sem nenhuma identificacao do produto em portugues
        (o subtitulo e em ingles e o `alt` descreve a ilustracao). O que este teste prende, a partir
        dai, e a `RN-23` **como ela esta escrita** — sem emenda.
        """
        _app, cliente, _pasta = cliente_de_upload

        assert "visually-hidden" not in _classe_do_h1(self._corpo(cliente)), (
            "o `h1` voltou a ser escondido: a arte atual nao traz o titulo, entao a tela ficaria "
            "sem nenhuma identificacao do produto em portugues"
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

    def test_o_texto_de_apresentacao_fica_em_coluna_propria_com_a_arte_ao_lado(self, cliente_de_upload):
        """`RN-24`, **emendada** pela `E001` da feature 037.

        ## O que a regra dizia, e o que ela diz agora

        A `RN-24` nasceu no adendo `011` pedindo o texto **centralizado** numa coluna mais
        estreita que o cartão. O operador apontou que a parte de cima continuava com a estética
        anterior e pediu a redistribuição em **duas colunas**, como na referência visual: texto à
        esquerda, arte à direita. A emenda está registrada no `requirements.md` da feature 037
        (`E001`) — ela não foi aplicada em silêncio.

        ## Por que a asserção olha a estrutura e a folha

        Um par de colunas não existe no HTML: quem o produz é a grade do `.masthead`. Então o
        teste prende as duas metades — o HTML com as duas colunas nomeadas e a regra da folha que
        as coloca lado a lado —, e prende também que a **ordem do documento** não mudou (a arte
        continua sendo o primeiro elemento; é a grade que a manda para a direita).
        """
        app, cliente, _pasta = cliente_de_upload

        corpo = self._corpo(cliente)
        assert 'class="masthead mb-4"' in corpo, "o bloco da masthead sumiu"
        assert 'class="masthead-arte"' in corpo, "a coluna da arte sumiu"
        assert 'class="masthead-texto"' in corpo, "a coluna do texto sumiu"

        inicio_arte = corpo.index('class="masthead-arte"')
        inicio_texto = corpo.index('class="masthead-texto"')
        assert inicio_arte < inicio_texto, (
            "a arte deixou de ser o primeiro elemento do documento: a grade e que a posiciona"
        )

        # O subtítulo, o título e os dois parágrafos vivem DENTRO da coluna do texto: nada de
        # `</div>` fecha a coluna antes do primeiro parágrafo.
        assert inicio_texto < corpo.index(SUBTITULO) < corpo.index(TITULO_NA_TELA) < corpo.index(
            "Este aplicativo web"
        ), "a ordem subtitulo, titulo e texto mudou dentro da coluna"
        assert "</div>" not in corpo[inicio_texto:corpo.index("Este aplicativo web")], (
            "a coluna do texto fecha antes do primeiro paragrafo"
        )

        with open(app.config["ESTILO_DA_TELA"], encoding="utf-8") as folha:
            estilo = folha.read()
        assert re.search(r"\.masthead\{[^}]*grid-template-columns", estilo, re.S), (
            "a folha perdeu a grade que coloca texto e arte lado a lado"
        )

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

        ## Estes pontos foram MEDIDOS na composicao de 2026-10-16

        Todos verificados como opacos no arquivo de runtime. Eles cobrem as duas familias de
        risco:

        - **arte ESCURA e pouco saturada** (capa `sat=53`, lombada `sat=35`, base do livro
          `sat=22`) — o que um limite de brilho baixo demais comecaria a comer;
        - **arte CLARA e quase neutra** — o que um teto de saturacao largo demais come. Os dois
          pontos centrais sao desta familia, e foram escolhidos a **>= 4 px de qualquer pixel de
          fundo**: prendem TINTA, e nao a antialiasing da borda.

        ## O ponto que saiu em 2026-10-16, e por que ele caiu

        A composicao anterior tinha um ponto no **preenchimento do texto dourado**
        (`(270, 212)`, `sat~24`), e era ele que prendia a faixa ESTREITA de saturacao — foi com um
        teto unico que as letras de "Analisador Genealogico" ficaram OCAS.

        A arte atual **nao tem o texto**: `(270, 212)` virou fundo e este teste caiu, corretamente.
        A familia continua representada pelos dois pontos centrais; a contagem que a prende sem
        depender de um pixel esta em
        `test_a_faixa_estreita_de_saturacao_continua_protegendo_tinta`.

        Se alguem "resolver" um residuo de fundo baixando o brilho ou alargando a saturacao, um
        destes pontos vira buraco e este teste cai.
        """
        rgba = arte.convert("RGBA")
        for rotulo, (x, y) in {
            "folha alta esquerda": (170, 75),
            "folha alta direita": (860, 75),
            "galho esquerdo": (300, 130),
            "galho direito": (700, 130),
            "tinta clara e quase neutra, no centro (1)": (511, 255),
            "tinta clara e quase neutra, no centro (2)": (489, 377),
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

    def test_a_faixa_estreita_de_saturacao_continua_protegendo_tinta(self, arte):
        """A contagem que prende a faixa estreita sem depender de um pixel so'.

        `_e_fundo` trata a faixa de 160 a 190 com teto de saturacao **estreito** (12), porque
        ali o fundo e cinza neutro (`sat` 0..7) e a tinta clara e levemente quente. Se o teto
        voltar a ser o largo (50), **toda** a tinta dessa faixa vira fundo — foi o defeito medido
        que deixou as letras de "Analisador Genealogico" ocas na composicao anterior.

        ## Os numeros sao medidos, nao escolhidos

        Na arte derivada de 2026-10-16: **455 pixels** opacos nesta faixa. Com o teto largo:
        **zero**. O piso de 150 fica com folga de 3x para baixo de proposito — pixels de borda
        mudam com qualquer ajuste na segunda passada da receita, e o que este teste prende e a
        ORDEM DE GRANDEZA, nao o valor exato.

        Este teste existe porque o ponto por pixel que fazia esse papel saiu com o texto: sem ele,
        alargar o teto passaria despercebido.
        """
        rgba = arte.convert("RGBA")
        pixels = rgba.load()
        largura, altura = rgba.size

        na_faixa = 0
        for y in range(altura):
            for x in range(largura):
                r, g, b, alfa = pixels[x, y]
                if alfa != 255:
                    continue
                maior, menor = max(r, g, b), min(r, g, b)
                if 160 <= maior < 190 and 12 < (maior - menor) <= 50:
                    na_faixa += 1

        assert na_faixa >= 150, (
            f"so' {na_faixa} pixels opacos na faixa estreita de saturacao (medido: 455). O teto "
            "de `SATURACAO_MINIMA_ESCURA` foi alargado, ou o brilho minimo baixou, e a tinta clara "
            "da arte esta sendo tratada como fundo"
        )
