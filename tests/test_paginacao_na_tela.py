"""A paginacao da lista de resultados (feature 046).

## Por que este arquivo existe

O `SHA_DA_TELA` mede a tela de ENTRADA vazia e nao alcanca o estado de resultado; o
`tests/test_estado_do_resultado.py` prende o cartao (id, retorno, selo, grade); o
`tests/test_cartoes_recolhiveis.py` prende o recolhimento. **Nenhum deles** olha para o
controle de paginacao, e a razao e simples: ele nao existia. Sem este arquivo, apagar o
`nav` inteiro, trocar o padrao de 10 por 100, ou esconder os cartoes via `innerHTML`
deixaria a suite verde — e as 68 conexoes voltariam a ser uma rolagem so.

## O que ele mede, e o que ele NAO mede

Mede **presenca, contrato e ligacao**, nunca aparencia: nao ha assert de cor, largura ou
posicao — isso e da folha.

1. **A marcacao nasce no HTML**, e nao no script. Este projeto testa markup renderizado e
   nao executa JavaScript; um controle criado no `DOMContentLoaded` passaria a existir so
   no navegador e nenhum teste o veria. Por isso as series 1 a 4 medem o documento.
2. **Nada sai do documento.** Os 68 cartoes continuam no HTML em qualquer pagina — e o
   invariante que o adendo `018` chama de "a leitura da analise como texto".
3. **O script esta LIGADO**, e nao so escrito: o seletor, os numeros e os dois botoes de
   passo tem ouvinte, e `abrirCartaoDoAlvo` mostra a pagina **antes** de abrir o cartao.
   Essa ordem e a unica coisa que nao quebra visivelmente quando erra: o cartao abre, e o
   diagrama mede um container de tamanho zero.
4. **A contagem do topo continua sendo a da ANALISE**, e nao a da pagina. E a assercao que
   impede a "correcao" bem-intencionada de trocar 68 por 10.

## O caminho e o de PRODUCAO

Como no `test_estado_do_resultado.py`: os arquivos entram na pasta de upload e o `POST` de
`action=dna_analysis` e real. Montar o payload a mao mediria o template contra uma forma
que ninguem produz.
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

from tests.fixtures.sample_dna import (  # noqa: E402
    DNA_CSV_OITO_CONEXOES,
    DNA_CSV_SESSENTA_E_OITO_CONEXOES,
    DNA_GED,
)

CHAVE_ARVORE = "080e7943572d2652"
CHAVE_CSV = "94e2402671702cac"
ARVORE = CHAVE_ARVORE + "__Arvore.ged"
RAIZ_DA_ARVORE = "Carlos Silva Souza"

FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")

#: As sete classes que o controle introduz. Cada uma tem de existir na folha: o par
#: classe-no-template / `.classe`-na-folha nao quebra nada em silencio, so muda a tela.
CLASSES_DO_CONTROLE = (
    "paginacao-das-conexoes",
    "rotulo-do-tamanho",
    "seletor-do-tamanho",
    "posicao-da-pagina",
    "botao-de-pagina",
    "numeros-das-paginas",
    "numero-de-pagina",
)

#: O padrao e 10, e as tres opcoes sao as unicas.
OPCOES_DE_TAMANHO = ("10", "20", "30")


def _guardar(pasta: str, nome: str, conteudo: str) -> None:
    with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)


def _analisar(cliente_de_upload, relatorio: str) -> str:
    """O HTML do estado de resultado com o CSV dado, pelo caminho de producao."""
    _app, cliente, pasta = cliente_de_upload
    _guardar(pasta, ARVORE, DNA_GED)
    _guardar(pasta, RELATORIO, relatorio)

    resposta = cliente.post(
        "/",
        data={
            "action": "dna_analysis",
            "gedcom_filename": ARVORE,
            "matches_csv_filename": RELATORIO,
            "root_name": RAIZ_DA_ARVORE,
        },
    )
    assert resposta.status_code == 200, (
        f"o POST de analise devolveu {resposta.status_code}; sem resultado nao ha o que medir"
    )
    return resposta.get_data(as_text=True)


RELATORIO = CHAVE_CSV + "__Matches.csv"


@pytest.fixture
def pagina_longa(cliente_de_upload) -> str:
    """68 conexoes: 7 paginas de 10, com a ultima de 8."""
    return _analisar(cliente_de_upload, DNA_CSV_SESSENTA_E_OITO_CONEXOES)


@pytest.fixture
def pagina_curta(cliente_de_upload) -> str:
    """8 conexoes: cabe numa pagina, entao nao ha o que paginar."""
    return _analisar(cliente_de_upload, DNA_CSV_OITO_CONEXOES)


def _controle(marcacao: str) -> str:
    """O bloco do controle, do `<nav>` ao `</nav>`."""
    achado = re.search(r'(?s)<nav class="paginacao-das-conexoes".*?</nav>', marcacao)
    assert achado, "o controle de paginacao nao esta no documento"
    return achado.group(0)


def _cartoes(marcacao: str) -> list[str]:
    """Os `id` dos cartoes, na ordem em que aparecem."""
    return re.findall(r'<details[^>]*id="(resultado-\d+)"', marcacao)


def _numeros(controle: str) -> list[str]:
    """Os numeros de pagina renderizados, na ordem."""
    return re.findall(r'class="numero-de-pagina"[^>]*data-pagina="(\d+)"', controle)


def _opcoes(controle: str) -> list[str]:
    """Os valores das opcoes do seletor, na ordem."""
    return re.findall(r'<option value="(\d+)"', controle)


def _scripts(marcacao: str) -> str:
    """O corpo de TODOS os `<script>` inline, juntos.

    Os que tem `src` (CDN) nao interessam: o que se procura e o script do projeto. Os
    comentarios de template sao Jinja e ja sairam na renderizacao, entao o que sobra aqui e
    codigo — diferente do markup, onde os comentarios sobrevivem e ja enganaram um regex
    (adendo `019`).
    """
    blocos = re.findall(r"(?s)<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", marcacao)
    assert blocos, "nao ha script inline no documento"
    return "\n".join(blocos)


def _folha_sem_comentario() -> str:
    with open(FOLHA, "r", encoding="utf-8") as arquivo:
        folha = arquivo.read()
    return re.sub(r"/\*.*?\*/", "", folha, flags=re.S)


class TestOControleViveNoTopoDaLista:
    """O controle fica entre a contagem e o primeiro cartao, e nao no fim da pagina."""

    def test_o_controle_esta_entre_a_contagem_e_o_primeiro_cartao(self, pagina_longa):
        contagem = pagina_longa.index("contagem-das-conexoes")
        controle = pagina_longa.index("paginacao-das-conexoes")
        primeiro_cartao = pagina_longa.index('<details class="card cartao-do-resultado"')
        assert contagem < controle < primeiro_cartao, (
            "o controle tem de ficar depois da contagem e antes do primeiro cartao: "
            f"contagem={contagem}, controle={controle}, cartao={primeiro_cartao}"
        )

    def test_o_controle_e_uma_regiao_nomeada(self, pagina_longa):
        controle = _controle(pagina_longa)
        assert 'aria-label="Paginação das conexões"' in controle, (
            "sem rotulo, o leitor de tela anuncia 'navegacao' e nada mais"
        )

    def test_a_posicao_diz_pagina_um_de_sete(self, pagina_longa):
        assert "Página 1 de 7" in _controle(pagina_longa)


class TestOSeletorDeTamanho:
    """10 e o padrao, e 10/20/30 sao as unicas opcoes."""

    def test_as_tres_opcoes_estao_no_documento(self, pagina_longa):
        assert tuple(_opcoes(_controle(pagina_longa))) == OPCOES_DE_TAMANHO

    def test_o_dez_vem_selecionado(self, pagina_longa):
        controle = _controle(pagina_longa)
        assert re.search(r'<option value="10" selected>', controle), (
            "o padrao tem de vir marcado no HTML: quem le o padrao e o `<option selected>`, "
            "e nao uma constante no script"
        )

    def test_o_seletor_tem_rotulo_associado(self, pagina_longa):
        controle = _controle(pagina_longa)
        assert re.search(r'<label[^>]*for="tamanho-da-pagina"', controle)
        assert 'id="tamanho-da-pagina"' in controle


class TestOsNumerosDasPaginas:
    """Um numero por pagina, e o corrente marcado com `aria-current`."""

    def test_ha_um_numero_por_pagina(self, pagina_longa):
        assert _numeros(_controle(pagina_longa)) == [str(n) for n in range(1, 8)]

    def test_so_o_numero_um_e_o_corrente(self, pagina_longa):
        controle = _controle(pagina_longa)
        correntes = re.findall(r'data-pagina="(\d+)" aria-current="page"', controle)
        assert correntes == ["1"], f"o corrente e um so, e e o 1; veio {correntes}"

    def test_o_anterior_comeca_desabilitado(self, pagina_longa):
        controle = _controle(pagina_longa)
        assert re.search(r'id="pagina-anterior"[^>]*disabled', controle), (
            "na primeira pagina nao ha para onde voltar"
        )

    def test_a_proxima_nao_comeca_desabilitada(self, pagina_longa):
        controle = _controle(pagina_longa)
        assert not re.search(r'id="pagina-seguinte"[^>]*disabled', controle)


class TestONadaSaiDoDocumento:
    """Os 68 cartoes continuam no HTML, e nenhum nasce escondido."""

    def test_os_sessenta_e_oito_cartoes_continuam_no_documento(self, pagina_longa):
        assert len(_cartoes(pagina_longa)) == 68

    def test_a_numeracao_dos_cartoes_nao_tem_buraco(self, pagina_longa):
        assert _cartoes(pagina_longa) == [f"resultado-{n}" for n in range(1, 69)]

    def test_nenhum_cartao_nasce_escondido(self, pagina_longa):
        assert not re.search(r"cartao-do-resultado[^>]*\shidden", pagina_longa), (
            "o HTML nasce com tudo visivel e o script e' quem esconde: sem script, o "
            "operador tem de ver a lista inteira"
        )

    def test_a_contagem_do_topo_continua_sendo_a_da_analise(self, pagina_longa):
        assert "68 conexões analisadas" in pagina_longa, (
            "a contagem e da ANALISE; trocar por 10 diria que a analise encolheu"
        )


class TestQuandoTudoCabeNumaPagina:
    """Com 8 cartoes e 10 por pagina, o controle nao existe."""

    def test_o_controle_nao_e_renderizado(self, pagina_curta):
        # A busca e' pelo MARCADO, e nao pelo nome solto: o script cita a classe e os `id` do
        # controle de proposito (e' ele que o procura na pagina), entao procurar o nome em todo
        # o documento mediria o script, nao o markup.
        assert '<nav class="paginacao-das-conexoes"' not in pagina_curta
        assert 'id="tamanho-da-pagina"' not in pagina_curta

    def test_os_oito_cartoes_estao_la(self, pagina_curta):
        assert len(_cartoes(pagina_curta)) == 8


class TestAFolhaDeEstilo:
    """As classes do controle existem, e a guarda de `[hidden]` tambem."""

    @pytest.mark.parametrize("classe", CLASSES_DO_CONTROLE)
    def test_as_classes_do_controle_existem_na_folha(self, classe):
        assert re.search(r"\." + re.escape(classe) + r"\b", _folha_sem_comentario()), (
            f".{classe} nao esta em src/assets/app.css"
        )

    def test_a_folha_esconde_o_cartao_fora_da_pagina(self):
        folha = _folha_sem_comentario()
        assert re.search(
            r"details\.cartao-do-resultado\[hidden\]\s*\{[^}]*display\s*:\s*none", folha
        ), (
            "sem uma regra propria, um `display` de biblioteca vence o atributo `hidden` e "
            "a lista volta a aparecer inteira"
        )


class TestALigacaoDoScript:
    """O controle nao e so markup: ele esta ligado, e na ordem certa."""

    def test_o_seletor_tem_ouvinte(self, pagina_longa):
        assert "tamanho-da-pagina" in _scripts(pagina_longa)

    def test_os_numeros_tem_ouvinte(self, pagina_longa):
        assert "numeros-das-paginas" in _scripts(pagina_longa)

    def test_os_dois_botoes_de_passo_tem_ouvinte(self, pagina_longa):
        script = _scripts(pagina_longa)
        assert "pagina-anterior" in script and "pagina-seguinte" in script

    def test_o_cartao_do_alvo_e_revelado_antes_de_abrir(self, pagina_longa):
        script = _scripts(pagina_longa)
        inicio = script.index("const abrirCartaoDoAlvo")
        corpo = script[inicio:]
        revelar = corpo.index("mostrarPaginaDo(alvo)")
        abrir = corpo.index("alvo.open = true")
        assert revelar < abrir, (
            "mostrar a pagina antes de abrir: aberto o cartao escondido, o `toggle` dispara "
            "e o Mermaid mede um container de tamanho zero"
        )

    def test_expandir_e_recolher_usam_a_pagina_corrente(self, pagina_longa):
        script = _scripts(pagina_longa)
        assert "cartoesDaPagina()" in script, (
            "os botoes de expandir/recolher tem de operar na fatia visivel, e nao nos 68"
        )

    def test_trocar_de_pagina_nao_usa_rede(self, pagina_longa):
        script = _scripts(pagina_longa)
        assert "fetch(" not in script and "XMLHttpRequest" not in script, (
            "a troca de pagina e local: cada POST custaria uma analise inteira"
        )
        assert "irPara(" in script
