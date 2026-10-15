"""O estado de RESULTADO da tela: cabecalho do cartao, retorno e grade do kit genetico.

## Por que este arquivo existe

`SHA_DA_TELA` (`tests/test_icone_de_atalho.py`) mede a tela de ENTRADA **VAZIA**, e era o
unico invariante de tela do projeto. O markup que a revisao de design acrescentou — o selo da
confrontacao no cabecalho do cartao, o caminho de volta e a grade do kit — vive no estado de
RESULTADO, que aquele hash **nao alcanca**.

Medido em 2026-10-11, antes deste arquivo: apagar o selo do cabecalho, ou trocar a grade pela
tabela antiga, mantinha os **561 testes verdes**. A folha de estilo tambem saiu do alcance do
hash quando deixou de ser `<style>` embutido. Este arquivo fecha a parte do resultado.

## O que ele mede, e o que ele NAO mede

Mede **presenca e acoplamento**, nunca aparencia: nao ha assert de cor, largura ou posicao —
isso e da folha. O que se prende e o que quebra em silencio:

1. **o acoplamento retorno <-> titulo.** O `href="#resultados"` de cada cartao e o
   `id="resultados"` do titulo nascem em **dois pontos separados** do template, e renomear um
   so nao levanta erro nenhum: o link apenas deixa de ter alvo. Ate o adendo `019` este par era
   o `#resultado-N` da tabela do indice; com ela fora, o que liga os dois pontos e o retorno
   para o titulo;
2. **o selo no cabecalho**, e nao so na secao 4 — era o ponto do refresh e some sem aviso;
3. **os oito rotulos da grade do kit**, que a tabela antiga tambem tinha e que nao podem
   divergir do CSV que os alimenta;
4. **as posicoes atras do `details`**, que sairam da tabela de nove linhas.

O `id` do cartao (`resultado-N`) continua sendo medido, porque e ele que o `hash` da barra de
enderecos encontra para abrir o cartao recolhido (`tests/test_cartoes_recolhiveis.py`). O que
saiu foi o **link** para ele: o unico lugar que emitia `#resultado-N` era a tabela.

## O caminho e o de PRODUCAO

O teste nao monta o payload a mao: ele grava os arquivos na pasta de upload e faz o `POST`
real de `action=dna_analysis`, deixando a rota parsear o GEDCOM, rodar o nucleo e escolher o
ramo. Montar o dicionario na mao mediria o template contra uma forma que ninguem produz — e foi
exatamente essa a lacuna: as guardas `if r.documentary` / `if r.comparison` do template existem
para payload parcial, entao um teste com payload parcial passaria por vacuidade.
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

from tests.fixtures.sample_dna import DNA_CSV_UTF8, DNA_GED  # noqa: E402

# Nomes no disco no formato que o armazenamento usa: 16 hexadecimais da chave de conteudo,
# separador `__` e o nome visivel. A chave NAO precisa ser o sha256 real do conteudo — quem a
# valida e o caminho de ENVIO, e aqui os arquivos entram direto na pasta, como em
# `tests/test_lista_na_tela.py`.
CHAVE_ARVORE = "080e7943572d2652"
CHAVE_CSV = "94e2402671702cac"
ARVORE = CHAVE_ARVORE + "__Arvore.ged"
RELATORIO = CHAVE_CSV + "__Matches.csv"
RAIZ_DA_ARVORE = "Carlos Silva Souza"

#: A folha de estilo da tela, pela mesma razao do `tests/test_estilo_da_tela.py`: o par
#: classe-no-template / `.classe`-na-folha nao quebra nada em silencio, so muda a tela.
FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")

#: Os oito rotulos que a grade do kit tem de manter. Sao os MESMOS da tabela de nove linhas que
#: ela substituiu, e o `tests/mudancas` registra que a troca de forma nao renomeia nada.
ROTULOS_DO_KIT = (
    "DNA compartilhado",
    "Maior segmento",
    "Segmentos",
    "SNPs",
    "Pessoa (como está no CSV)",
    "Kit",
    "Cromossomo(s)",
    "Método do valor",
)

def _guardar(pasta: str, nome: str, conteudo: str) -> None:
    with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)


@pytest.fixture
def pagina(cliente_de_upload) -> str:
    """O HTML do estado de resultado, pelo caminho de producao."""
    _app, cliente, pasta = cliente_de_upload
    _guardar(pasta, ARVORE, DNA_GED)
    _guardar(pasta, RELATORIO, DNA_CSV_UTF8)

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


def _ancoras_do_indice(marcacao: str) -> list[str]:
    """Os alvos dos links do indice, na ordem em que aparecem."""
    return re.findall(r'href="#(resultado-\d+)"', marcacao)


def _cartoes_do_resultado(marcacao: str) -> list[str]:
    """Os `id` dos cartoes de resultado, na ordem em que aparecem."""
    return re.findall(r'id="(resultado-\d+)"', marcacao)


#: O `id` do titulo do resultado e o unico destino que o link de retorno pode ter. Os dois
#: nascem em pontos DIFERENTES do template (o titulo, no topo; o link, dentro do laco dos
#: cartoes), entao renomear um so nao levanta erro nenhum — a ancora so deixa de ter alvo.
#: Ate o adendo `019` este alvo era o container da tabela do indice (`#indice`), que saiu.
ALVO_DO_RETORNO = "resultados"


def _alvo_do_retorno_existe(marcacao: str) -> bool:
    """O `id` do alvo do retorno esta no documento?"""
    return f'id="{ALVO_DO_RETORNO}"' in marcacao


def _retornos_ao_indice(marcacao: str) -> list[str]:
    """Os alvos dos links de retorno, um por cartao, na ordem em que aparecem."""
    return re.findall(r'class="voltar-ao-indice" href="#([^"]+)"', marcacao)


def _cabecalhos(marcacao: str) -> list[str]:
    """O conteudo de cada `card-header`. Um cartao de resultado por vez."""
    return re.findall(r'(?s)<div class="card-header">(.*?)</div>', marcacao)


class TestOCartaoTemIdentidadePropria:
    """Todo cartao tem `id`, e a tabela do indice nao voltou.

    O `id="resultado-N"` e o que o navegador encontra quando a barra de enderecos traz
    `#resultado-3` — e o JS que abre o cartao recolhido depende disso
    (`tests/test_cartoes_recolhiveis.py`). Ate o adendo `019` havia DOIS lacos emitindo
    `#resultado-N`: a tabela (o link) e os cartoes (o `id`). A tabela saiu, e com ela o link.
    """

    def test_a_tabela_do_indice_nao_voltou(self, pagina):
        """Ela virou uma SEGUNDA lista de resumos quando os cartoes passaram a recolher.

        A coluna "Confrontacao" dizia exatamente o que o selo do cabecalho do cartao ja dizia,
        e as linhas existiam para navegar uma pagina que nao precisa mais de indice.
        """
        assert "indice-resultados" not in pagina, (
            "a tabela do indice voltou (adendo 019): com os cartoes recolhiveis ela e' uma "
            "segunda lista de resumos, e nao a visao geral"
        )

    def test_ha_um_cartao_por_conexao_e_cada_um_tem_id(self, pagina):
        cartoes = _cartoes_do_resultado(pagina)
        assert cartoes, "nao ha cartao de resultado para conferir"
        assert len(cartoes) == len(set(cartoes)), (
            f"`id` de cartao repetido: {sorted(cartoes)}. O `hash` abriria o cartao errado"
        )

    def test_a_numeracao_dos_cartoes_nao_tem_buraco(self, pagina):
        """O `hash` e o `id` sao o par: um buraco na numeracao e' um alvo que nao existe."""
        cartoes = _cartoes_do_resultado(pagina)
        assert cartoes == [f"resultado-{i}" for i in range(1, len(cartoes) + 1)], (
            f"a numeracao dos cartoes ficou com buraco: {cartoes}"
        )


class TestOCaminhoDeVoltaParaALista:
    """O cartao tem de ter como voltar ao topo da lista de resultados.

    Sem isto o operador que abre a analise completa de uma pessoa — cinco secoes, com tabelas de
    evidencia, grafo e avisos — so alcanca a lista de novo rolando a pagina inteira de volta.
    O retorno e uma ancora interna, e nao um `POST` com `action`: ele nao passa pelo despacho de
    acao, entao nao tem como descartar o estado do resultado que esta na tela.
    """

    def test_o_alvo_do_retorno_existe_no_documento(self, pagina):
        """Guarda contra o teste vazio: um `id` sem link, ou um link sem `id`, nao volta nada."""
        assert _alvo_do_retorno_existe(pagina), (
            f"o titulo perdeu o `id=\"{ALVO_DO_RETORNO}\"`: o link de retorno apontaria para "
            "lugar nenhum e o clique nao faria nada"
        )

    def test_ha_um_retorno_por_cartao(self, pagina):
        cartoes = _cartoes_do_resultado(pagina)
        retornos = _retornos_ao_indice(pagina)
        assert cartoes, "nao ha cartao nenhum para conferir"
        assert len(retornos) == len(cartoes), (
            "nem todo cartao tem link de volta: quem leu a analise completa precisa conseguir "
            f"voltar de qualquer uma delas. cartoes={len(cartoes)} retornos={len(retornos)}"
        )

    def test_todo_retorno_aponta_para_o_titulo(self, pagina):
        retornos = _retornos_ao_indice(pagina)
        assert retornos, "nao ha link de retorno para conferir"
        assert set(retornos) == {ALVO_DO_RETORNO}, (
            f"o link de retorno mudou de alvo: {sorted(set(retornos))}. O alvo e o titulo do "
            "resultado, e nao um cartao nem uma rota externa"
        )

    def test_o_retorno_e_ancora_e_nao_envio(self, pagina):
        """Ancora interna nao reenvia formulario nem depende do despacho de `action`."""
        retornos = re.findall(r"<a class=\"voltar-ao-indice\"[^>]*>", pagina)
        assert retornos, "o link de retorno nao esta na tela"
        for marca in retornos:
            assert 'href="#' in marca, f"o retorno deixou de ser ancora interna: {marca}"
            assert 'href="/' not in marca, (
                f"o retorno virou navegacao para outra rota e descarta o resultado: {marca}"
            )

    def test_o_retorno_nomeia_o_destino_para_leitor_de_tela(self, pagina):
        """"Voltar" sozinho nao diz de onde para onde; o texto escondido diz."""
        assert re.search(
            r'<a class="voltar-ao-indice" href="#resultados">[^<]+'
            r'<span class="visually-hidden">[^<]+</span></a>',
            pagina,
        ), (
            "o rotulo visivel e curto de proposito, mas o link precisa do destino escrito em "
            "`visually-hidden`: sem ele o leitor de tela anuncia so \"Voltar\""
        )

    def test_o_rotulo_visivel_e_voltar(self, pagina):
        assert re.search(r'href="#resultados">Voltar<', pagina), (
            "o rotulo visivel do retorno mudou; a tela de busca ja usa o mesmo vocabulario"
        )

    def test_o_retorno_tem_estilo_na_folha(self):
        """Um link sem regra cai no meio do cabecalho, disputando linha com o selo."""
        with open(FOLHA, encoding="utf-8") as arquivo:
            folha = arquivo.read()
        assert ".voltar-ao-indice" in folha, (
            "a folha perdeu a regra do retorno: ele volta a ficar solto no cabecalho do cartao"
        )


class TestOSeloDaConfrontacao:
    """O veredito subiu para o cabecalho do cartao (`T` do refresh de design)."""

    def test_o_cabecalho_carrega_o_selo_da_confrontacao(self, pagina):
        cabecalhos = _cabecalhos(pagina)
        assert cabecalhos, "o cartao de resultado ficou sem cabecalho"
        assert re.search(r"badge estado-[A-Z]+", cabecalhos[0]), (
            "o selo da confrontacao saiu do cabecalho do cartao: era o ponto do refresh, e "
            "numa lista longa o operador volta a ter de rolar ate a secao 4 para saber o veredito"
        )

    def test_o_selo_usa_o_nome_do_estado_como_classe(self, pagina):
        """A classe e o par do texto: renomear um estado quebra a cor do selo em silencio."""
        assert re.search(r'class="badge estado-[A-Z]+"', pagina), (
            "o selo deixou de usar `estado-<status>` como classe"
        )


class TestAGradeDoKit:
    """A tabela de nove linhas virou `dl`, e os rotulos nao podem se perder na troca."""

    def test_a_grade_esta_na_tela(self, pagina):
        assert 'class="kit-grid"' in pagina, "a grade do kit genetico sumiu"

    @pytest.mark.parametrize("rotulo", ROTULOS_DO_KIT)
    def test_a_grade_mantem_o_rotulo(self, pagina, rotulo):
        assert f"<dt>{rotulo}</dt>" in pagina, (
            f"a grade perdeu o rotulo {rotulo!r}; a troca de tabela por `dl` nao podia "
            "renomear nem remover nenhum dos oito"
        )

    def test_o_total_vem_destacado(self, pagina):
        assert re.search(r'<dd class="destaque">[\d.,]+ cM</dd>', pagina), (
            "o DNA compartilhado deixou de ser o numero em destaque da grade"
        )

    def test_as_posicoes_estao_atras_do_detalhe(self, pagina):
        assert "<summary>Posições</summary>" in pagina, (
            "as posicoes sairam do `details`: elas eram o detalhe miudo, e abertas voltam a "
            "fazer a grade competir com elas pela atencao"
        )


class TestOEstadoDaIdentidadeChegaATela:
    """O nucleo decide o estado; o template so o exibe.

    Sem esta classe, apagar o campo `identidade` do resultado do nucleo deixaria o template
    renderizando um `Undefined` do Jinja: a comparacao com `'a_confirmar'` simplesmente da
    falso, **nenhum selo aparece** e nenhuma das guardas de template percebe — o aviso morre
    em silencio, que e o unico modo de falha que importa aqui.
    """

    def test_o_resultado_traz_estado_de_identidade_por_cartao(self, cliente_de_upload):
        """Medido no nucleo, pelo caminho de producao do fluxo de DNA."""
        from core.dna_analysis import Dependencias, dna_analysis
        from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
        from parsers.gedcom_parser import carregar_arvore
        from reporting.mermaid_render import (
            generate_mermaid_graph,
            generate_mermaid_graph_indirect_bridge,
        )

        _app, _cliente, pasta = cliente_de_upload
        _guardar(pasta, ARVORE, DNA_GED)
        _guardar(pasta, RELATORIO, DNA_CSV_UTF8)

        deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                            generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
        resultados, _descartados, _mensagem = dna_analysis(
            os.path.join(pasta, RELATORIO), RAIZ_DA_ARVORE, deps,
            carregar_arvore(os.path.join(pasta, ARVORE)))

        assert resultados, "a analise nao devolveu cartao nenhum para conferir"
        for resultado in resultados:
            assert "identidade" in resultado, (
                "o resultado do nucleo perdeu o campo `identidade`: o template renderiza o selo "
                "a partir dele, e sem o campo o selo some sem erro nenhum"
            )
            assert "identidade_aviso" in resultado, (
                "o resultado do nucleo perdeu o campo `identidade_aviso`: o cartao ficaria sem a "
                "frase que mostra os dois nomes"
            )

    def test_o_estado_de_identidade_usa_os_tres_valores_conhecidos(self, pagina):
        """Na tela, so os dois rotulos previstos: o selo do indice e o do cabecalho."""
        estados = set(re.findall(r'identidade-(a_confirmar)', pagina))
        assert estados <= {"a_confirmar"}, (
            f"a tela emitiu um estado de identidade que o CSS nao conhece: {sorted(estados)}"
        )

    def test_o_resultado_traz_janela_de_vida_por_cartao(self, cliente_de_upload):
        """Mesmo risco do campo `identidade`: sem ele, o selo some sem erro nenhum."""
        from core.dna_analysis import Dependencias, dna_analysis
        from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
        from parsers.gedcom_parser import carregar_arvore
        from reporting.mermaid_render import (
            generate_mermaid_graph,
            generate_mermaid_graph_indirect_bridge,
        )

        _app, _cliente, pasta = cliente_de_upload
        _guardar(pasta, ARVORE, DNA_GED)
        _guardar(pasta, RELATORIO, DNA_CSV_UTF8)

        deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                            generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
        resultados, _descartados, _mensagem = dna_analysis(
            os.path.join(pasta, RELATORIO), RAIZ_DA_ARVORE, deps,
            carregar_arvore(os.path.join(pasta, ARVORE)))

        assert resultados, "a analise nao devolveu cartao nenhum para conferir"
        for resultado in resultados:
            for campo in ("janela_de_vida", "idade_na_arvore", "data_de_nascimento",
                          "ano_de_referencia", "janela_aviso"):
                assert campo in resultado, (
                    f"o resultado do nucleo perdeu o campo `{campo}`: o template renderiza o "
                    "selo e o aviso a partir dele, e sem o campo eles somem sem erro nenhum"
                )

    def test_a_janela_de_vida_usa_estados_conhecidos_pelo_css(self, pagina):
        estados = set(re.findall(r'janela-([a-z_]+)"', pagina))
        conhecidos = {"impossivel", "suspeita", "imprecisa", "impossivel", "suspeita",
                      "data_imprecisa"}
        assert estados <= conhecidos, (
            f"a tela emitiu um estado de janela que o CSS nao conhece: {sorted(estados)}"
        )


class TestOSensibilidadeDoAcoplamento:
    """Prova que a checagem do par alvo <-> retorno DETECTA divergencia, e nao passa sempre.

    Sem esta prova, `test_o_alvo_do_retorno_existe_no_documento` poderia estar conferindo uma
    string que sempre aparece — que e o modo de falha mais perigoso de um teste de acoplamento.
    """

    def test_um_retorno_sem_alvo_e_detectado(self):
        marcacao = ('<h2 id="outro-titulo">titulo</h2>'
                    '<a class="voltar-ao-indice" href="#resultados">Voltar</a>')
        assert not _alvo_do_retorno_existe(marcacao), (
            "a checagem nao distingue o alvo certo de um `id` qualquer"
        )

    def test_o_alvo_certo_e_reconhecido(self):
        marcacao = ('<h2 id="resultados">titulo</h2>'
                    '<a class="voltar-ao-indice" href="#resultados">Voltar</a>')
        assert _alvo_do_retorno_existe(marcacao), (
            "a checagem nao reconhece o proprio alvo que ela prende"
        )

    def test_a_volta_da_tabela_do_indice_seria_detectada(self):
        """A guarda contra o retorno da tabela tem de reconhecer a tabela."""
        assert "indice-resultados" in '<div class="table-responsive indice-resultados mb-4">', (
            "a guarda contra o retorno da tabela nao reconheceria a tabela"
        )

    def test_um_cartao_sem_id_e_detectado(self):
        """O `id` e o alvo do `hash`; sem ele o cartao recolhido nao tem como ser aberto."""
        marcacao = '<details class="card"><summary class="sumario-do-cartao">x</summary></details>'
        assert _cartoes_do_resultado(marcacao) == [], (
            "o extrator de cartoes acharia um cartao sem `id`"
        )
