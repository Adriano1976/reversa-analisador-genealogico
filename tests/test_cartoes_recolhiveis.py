"""Cada cartão de resultado é um `<details>` — o operador abre o que quer ler.

O cartão passou a ser o elemento que **esconde conteúdo**, então a árvore tem de estar certa:
um `<details>` que nunca fecha não vira erro de HTML, o navegador fecha por conta própria no
lugar errado e engole os cartões seguintes. Por isso a checagem estrutural aqui é feita com um
parser, e não com `re.findall` — regex não distingue árvore bem formada de árvore que o
navegador teve de consertar.

Duas propriedades andam juntas com o recolhimento, e as duas são testadas:

1. **O diagrama dentro do cartão fechado.** Era o motivo declarado no template para NÃO
   colapsar os cartões: o Mermaid mede o container para dimensionar o SVG, e fechado o
   container tem tamanho zero — o desenho sai quebrado e marcado como `data-processed`, de
   modo que abrir depois não conserta. A solução já existia para o `grafo-do-registro`; o que
   mudou foi o seletor, que deixou de nomear aquela classe e passou a alcançar qualquer
   `details` com diagrama.
2. **Nada some do documento.** O `<details>` esconde visualmente, mas o texto continua no
   HTML — é o que preserva a garantia de que a análise é legível como texto. Um teste que só
   contasse cartões fechados não veria a diferença entre "recolhido" e "removido".
"""
from __future__ import annotations

import os
import re
import sys
from html.parser import HTMLParser

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pasta in (_RAIZ, os.path.join(_RAIZ, "src"), os.path.join(_RAIZ, "tests")):
    if _pasta not in sys.path:
        sys.path.insert(0, _pasta)

TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")
FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")

RAIZ = "Carlos Silva Souza"

GED = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Carlos /Silva Souza/
1 SEX M
1 FAMS @F1@
0 @I2@ INDI
1 NAME Ana /Silva Souza/
1 SEX F
1 FAMC @F1@
0 @I3@ INDI
1 NAME Pedro /Silva Souza/
1 SEX M
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
1 CHIL @I3@
0 TRLR
"""

CSV = ("Name,cM\n"
       "Ana Silva Souza,100\n"
       "Pedro Silva Souza,50\n")

NOME_GED = "0000000000000001__cartoes.ged"
NOME_CSV = "0000000000000002__cartoes.csv"


# ---------------------------------------------------------------------------
# Estrutura: a arvore do cartao, lida por parser
# ---------------------------------------------------------------------------

class _ArvoreDosCartoes(HTMLParser):
    """A arvore de `details.card` do documento.

    Guarda, por cartao: se ele fecha, quantos `summary` e quantos `div.card-body` tem
    dentro, e se veio aberto. O `summary` e contado DENTRO do cartao — um `summary`
    fora de um `details` e conteudo invalido que o navegador reposiciona.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pilha: list = []
        self.cartoes: list[dict] = []
        self.summary_orfaos = 0
        self.desbalanceados = 0
        self.fecha_sem_abrir = 0

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        classes = (atributos.get("class") or "").split()
        if tag == "details":
            cartao = None
            if "card" in classes:
                cartao = {"id": atributos.get("id"), "aberto": "open" in atributos,
                          "summary": 0, "summary_nomeado": 0, "corpo": 0, "fechou": False,
                          "do_resultado": "cartao-do-resultado" in classes,
                          "descartados": "bloco-descartados" in classes}
                self.cartoes.append(cartao)
            self.pilha.append(cartao)
            return
        if tag == "summary":
            # Orfao e o `summary` SEM `details` nenhum em volta. Um `summary` dentro de um
            # `details` que nao e cartao (as "Posicoes", o grafo) e legitimo: a pilha guarda
            # `None` justamente para esses, e so a pilha VAZIA significa orfao.
            if not self.pilha:
                self.summary_orfaos += 1
            elif self.pilha[-1] is not None:
                dono = self.pilha[-1]
                dono["summary"] += 1
                if "sumario-do-cartao" in classes:
                    dono["summary_nomeado"] += 1
        if tag == "div" and "card-body" in classes:
            for dono in reversed(self.pilha):
                if dono is not None:
                    dono["corpo"] += 1
                    break

    def handle_endtag(self, tag):
        if tag != "details":
            return
        if not self.pilha:
            self.fecha_sem_abrir += 1
            return
        cartao = self.pilha.pop()
        if cartao is not None:
            cartao["fechou"] = True

    @property
    def cartoes_nao_fechados(self) -> int:
        return sum(1 for c in self.cartoes if not c["fechou"])


def _arvore(pagina: str) -> _ArvoreDosCartoes:
    arvore = _ArvoreDosCartoes()
    arvore.feed(pagina)
    arvore.close()
    return arvore


@pytest.fixture(scope="module")
def template() -> str:
    with open(TEMPLATE, encoding="utf-8") as arquivo:
        return arquivo.read()


@pytest.fixture(scope="module")
def folha() -> str:
    with open(FOLHA, encoding="utf-8") as arquivo:
        return arquivo.read()


@pytest.fixture
def pagina(cliente_de_upload) -> str:
    _app, cliente, pasta = cliente_de_upload
    for nome, conteudo in ((NOME_GED, GED), (NOME_CSV, CSV)):
        with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
    return cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": NOME_GED,
        "matches_csv_filename": NOME_CSV,
        "root_name": RAIZ,
    }).get_data(as_text=True)


# ---------------------------------------------------------------------------
# A arvore, na tela renderizada
# ---------------------------------------------------------------------------

def _cabecalhos_dos_cartoes(pagina: str) -> list[str]:
    """Os `card-header` dos cartoes de RESULTADO, um por cartao.

    O bloco das observacoes do arquivo tambem e' um `details.card` com `card-header` — ele
    recolhe pela mesma forma, e **nao** e' cartao de resultado. Contar todos misturaria os
    dois; o corte e' pelo marcador que o template poe so' no cartao (`cartao-do-resultado`).
    """
    partes = pagina.split('<details class="card cartao-do-resultado"')[1:]
    cabecalhos = []
    for parte in partes:
        achado = re.search(r'(?s)<div class="card-header">(.*?)</div>', parte)
        if achado:
            cabecalhos.append(achado.group(1))
    return cabecalhos


class TestAArvoreDoCartao:

    def test_ha_um_details_por_conexao(self, pagina):
        arvore = _arvore(pagina)
        do_resultado = [c for c in arvore.cartoes if c["do_resultado"]]
        assert len(do_resultado) == 2, f"cartoes: {arvore.cartoes}"
        assert {c["id"] for c in do_resultado} == {"resultado-1", "resultado-2"}

    def test_todo_details_fecha(self, pagina):
        """O navegador conserta `details` nao fechado — fechando no lugar ERRADO."""
        arvore = _arvore(pagina)
        assert arvore.cartoes_nao_fechados == 0, (
            f"{arvore.cartoes_nao_fechados} cartao(oes) sem `</details>`: o navegador vai "
            "fechar por conta propria e engolir o cartao seguinte"
        )
        assert arvore.fecha_sem_abrir == 0
        assert arvore.pilha == [], f"sobrou tag de `details` aberta: {arvore.pilha}"

    def test_cada_cartao_tem_um_summary_nomeado_e_um_corpo(self, pagina):
        for cartao in _arvore(pagina).cartoes:
            assert cartao["summary"] == 1, (
                f"o cartao {cartao['id']} tem {cartao['summary']} `summary`; sem exatamente um, "
                "o navegador escolhe sozinho qual conteudo vira o gatilho"
            )
            assert cartao["summary_nomeado"] == 1, (
                f"o `summary` do cartao {cartao['id']} perdeu a classe `sumario-do-cartao`"
            )
            assert cartao["corpo"] == 1, (
                f"o cartao {cartao['id']} tem {cartao['corpo']} `div.card-body`"
            )

    def test_nenhum_summary_fora_de_um_cartao(self, pagina):
        assert _arvore(pagina).summary_orfaos == 0

    def test_o_cartao_nasce_fechado(self, pagina):
        """A lista de cabecalhos e' a visao geral; o cartao e o detalhe.

        O bloco das observacoes do arquivo fica de FORA desta contagem e nasce ABERTO: ele
        carrega aviso, e nao detalhe. Ver `tests/test_observacoes_do_arquivo.py`.
        """
        for cartao in [c for c in _arvore(pagina).cartoes if c["do_resultado"]]:
            assert not cartao["aberto"], (
                f"o cartao {cartao['id']} veio com `open`: o recolhimento deixa de ser escolha"
            )

    def test_o_summary_embrulha_o_card_header_e_nao_o_substitui(self, pagina):
        """O cabecalho continua sendo `div.card-header` — e o que o indice le.

        Fechado, o cartao tem de continuar dizendo de quem e, quanto e o veredito: quem
        decide se vale abrir decide pelo cabecalho.
        """
        assert re.search(
            r'(?s)<summary class="sumario-do-cartao">\s*<div class="card-header">', pagina), (
            "o `card-header` saiu de dentro do `summary`: o cartao fechado perde o cabecalho"
        )
        cabecalhos = _cabecalhos_dos_cartoes(pagina)
        assert len(cabecalhos) == 2, f"cabecalhos de cartao de resultado: {len(cabecalhos)}"
        for cabecalho in cabecalhos:
            assert "Análise de conexão com" in cabecalho
            assert "voltar-ao-indice" in cabecalho, "o Voltar vive no cabecalho e nao pode sair"


# ---------------------------------------------------------------------------
# Nada some do documento
# ---------------------------------------------------------------------------

class TestONadaSome:

    def test_o_conteudo_dos_cartoes_continua_no_html(self, pagina):
        """`details` esconde na tela; o texto continua no documento.

        E o que preserva a leitura da analise como texto — `Ctrl+F`, copiar, e qualquer
        leitor que nao execute o clique. Se o recolhimento tivesse sido feito removendo o
        conteudo, esta assercao seria a unica a acusar.
        """
        for marcador in ("Parentesco documental", "Evidência genética",
                         "Confrontação GEDCOM × DNA", "Observações"):
            assert marcador in pagina, f"o recolhimento levou junto a secao {marcador!r}"

    def test_o_cabecalho_e_a_visao_geral_da_lista(self, pagina):
        """A tabela do indice saiu (adendo 019): a lista de cabecalhos passou a ser a visao geral.

        Nao ha mais uma segunda lista de resumos acima, e o cabecalho fechado tem de carregar
        os sinais que a coluna carregava — senao achar as conexoes com janela de vida
        impossivel ou profundidade divergente volta a exigir abrir cartao por cartao.
        """
        assert "indice-resultados" not in pagina, (
            "a tabela do indice voltou: com os cartoes recolhiveis ela e' uma segunda lista "
            "de resumos, e nao a visao geral"
        )
        cabecalhos = _cabecalhos_dos_cartoes(pagina)
        assert len(cabecalhos) == 2, f"cabecalhos de cartao de resultado: {len(cabecalhos)}"
        for cabecalho in cabecalhos:
            assert "cabecalho-sinais" in cabecalho, (
                "o cabecalho perdeu a linha de sinais (Parentesco, Janela de vida, "
                "Profundidade): com o cartao fechado, nao ha mais onde le-los"
            )
            assert "rotulo-parentesco" in cabecalho


# ---------------------------------------------------------------------------
# Os dois controles
# ---------------------------------------------------------------------------

class TestOsControlesDeExpandirERecolher:

    def test_os_dois_botoes_estao_na_tela(self, pagina):
        assert 'id="expandir-cartoes"' in pagina
        assert 'id="recolher-cartoes"' in pagina
        assert "Expandir todas as análises" in pagina
        assert "Recolher todas" in pagina

    def test_os_botoes_sao_type_button_e_nao_enviam_formulario(self, pagina):
        """Dentro de um formulario, um `<button>` sem `type` SUBMETE a pagina."""
        for identidade in ("expandir-cartoes", "recolher-cartoes"):
            marca = re.search(rf'<button[^>]*id="{identidade}"[^>]*>', pagina)
            assert marca, f"o botao {identidade} nao esta na tela"
            assert 'type="button"' in marca.group(0), (
                f"o botao {identidade} sem `type=\"button\"` envia o formulario"
            )

    def test_os_botoes_nao_aparecem_com_uma_conexao_so(self):
        """Com um cartao, "expandir todas" e "recolher todas" nao querem dizer nada."""
        with open(TEMPLATE, encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        assert re.search(r"\{%\s*if dna_results \| length > 1\s*%\}", fonte), (
            "os controles precisam da guarda de mais de uma conexao"
        )

    def test_os_botoes_estao_ligados_no_js(self, template):
        assert 'document.getElementById("expandir-cartoes")' in template
        assert 'document.getElementById("recolher-cartoes")' in template
        assert 'querySelectorAll("details.cartao-do-resultado")' in template, (
            "os botoes falam das ANALISES: o seletor nao pode alcancar o bloco dos descartados, "
            "que e' o outro `details` da tela"
        )


# ---------------------------------------------------------------------------
# O diagrama dentro do cartao fechado
# ---------------------------------------------------------------------------

class TestODiagramaNoCartaoFechado:
    """O motivo declarado para nao colapsar, e a solucao que ja existia no codigo."""

    def test_a_rodada_inicial_pula_o_que_esta_fechado(self, template):
        assert 'closest("details:not([open])")' in template, (
            "sem este filtro o Mermaid mede um container de tamanho zero e marca o desenho "
            "como processado: abrir depois nao conserta"
        )

    def test_o_ouvinte_de_toggle_alcanca_qualquer_details_com_diagrama(self, template):
        """O seletor deixou de nomear `grafo-do-registro`.

        O cartao em volta do grafo tem o MESMO problema do bloco do grafo; alcancar so
        aquele deixaria o cartao recolhido sem desenho ao abrir.
        """
        trecho = template[template.index("O MESMO CUIDADO VALE PARA O CARTAO"):]
        trecho = trecho[:trecho.index("}, 100);")]
        assert 'document.querySelectorAll("details")' in trecho
        assert 'detalhe.querySelector(".mermaid")' in trecho, (
            "sem a guarda de `has .mermaid`, o ouvinte e pendurado em todo `details` da tela"
        )
        assert "!el.dataset.processed" in trecho, (
            "sem a guarda de `data-processed`, reabrir o cartao redesenha o mesmo grafo"
        )


# ---------------------------------------------------------------------------
# Os dois acoplamentos que o recolhimento cria
# ---------------------------------------------------------------------------

class TestOsAcoplamentosDoRecolhimento:

    def test_o_alvo_da_ancora_abre_o_cartao(self, template):
        """Sem isto, clicar no indice leva a um cartao fechado e o link parece quebrado."""
        assert "abrirCartaoDoAlvo" in template
        assert 'addEventListener("hashchange", abrirCartaoDoAlvo)' in template
        assert "alvo.open = true" in template

    def test_o_link_dentro_do_summary_nao_recolhe_o_cartao(self, template):
        """O "Voltar" mora no cabecalho, que agora e o gatilho do `details`."""
        assert 'querySelectorAll("summary a")' in template
        assert "stopPropagation" in template

    def test_o_alvo_da_ancora_e_o_proprio_details(self, pagina):
        """A ancora abre o cartao so porque o `id` esta no `<details>`, e nao num filho.

        O `id` e' exigencia do cartao de RESULTADO: o bloco das observacoes do arquivo tem
        `details.card` sem `id` nenhum, e nao ha ancora que o alcance.
        """
        do_resultado = [c for c in _arvore(pagina).cartoes if c["do_resultado"]]
        assert do_resultado, "nao ha cartao de resultado para conferir"
        assert all(c["id"] for c in do_resultado), (
            "o `id` saiu do `details`: o hash deixa de encontrar o elemento que abre"
        )


class TestOSensibilidadeDoParser:
    """Prova que a checagem estrutural DETECTA arvore quebrada, e nao passa sempre.

    Sem esta prova, `test_todo_details_fecha` poderia estar medindo um parser que nunca
    acha nada — que e o modo de falha mais perigoso de um teste de estrutura.
    """

    def test_um_details_sem_fechar_e_detectado(self):
        arvore = _arvore('<details class="card" id="resultado-1">'
                         '<summary class="sumario-do-cartao">x</summary>'
                         '<div class="card-body">conteudo')
        assert arvore.cartoes_nao_fechados == 1, (
            "o parser nao distingue `<details>` fechado de `<details>` que o navegador "
            "teria de fechar por conta propria"
        )

    def test_um_summary_sem_details_e_detectado(self):
        arvore = _arvore('<div><summary class="sumario-do-cartao">solto</summary></div>')
        assert arvore.summary_orfaos == 1

    def test_um_summary_dentro_de_details_comum_nao_e_orfao(self):
        """A distincao que importa: `details` que nao e cartao continua valido."""
        arvore = _arvore('<details class="grafo-do-registro"><summary>Posições</summary></details>')
        assert arvore.summary_orfaos == 0
        assert arvore.cartoes == []

    def test_um_cartao_bem_formado_passa(self):
        arvore = _arvore('<details class="card" id="resultado-1">'
                         '<summary class="sumario-do-cartao">x</summary>'
                         '<div class="card-body">conteudo</div></details>')
        assert arvore.cartoes_nao_fechados == 0
        assert arvore.cartoes == [{"id": "resultado-1", "aberto": False, "summary": 1,
                                   "summary_nomeado": 1, "corpo": 1, "fechou": True,
                                   "do_resultado": False, "descartados": False}]

    def test_um_cartao_aberto_e_detectado(self):
        arvore = _arvore('<details class="card" open id="resultado-1">'
                         '<summary class="sumario-do-cartao">x</summary></details>')
        assert arvore.cartoes[0]["aberto"] is True


# ---------------------------------------------------------------------------
# A folha
# ---------------------------------------------------------------------------

class TestAFolha:

    @pytest.mark.parametrize("regra", [
        "details.card{overflow:hidden}",
        "details.card > summary.sumario-do-cartao{",
        "details.card > summary.sumario-do-cartao::-webkit-details-marker{display:none}",
        "details.card[open] > summary.sumario-do-cartao::after{",
        ".botao-do-cartao{",
        ".bloco-descartados > summary .card-header h5{",
    ])
    def test_a_regra_existe(self, folha, regra):
        assert regra in folha, f"a folha perdeu a regra {regra!r}"

    def test_o_indicador_de_aberto_muda(self, folha):
        """O losango tem de girar: um indicador que nao muda nao indica nada."""
        assert "transform:rotate(45deg)" in folha
        assert "transform:rotate(-135deg)" in folha

    def test_o_chevron_do_cartao_esta_no_fluxo_e_nao_absoluto(self, folha):
        """O grupo `Voltar` + indicador e um flex; o `::after` absoluto do summary saiu.

        O padding-right que reservava o espaço da caixa absoluta também sai: sem ele,
        o cabeçalho usa a largura inteira e os controles não competem com os selos.
        """
        assert ".controles-do-cabecalho{" in folha
        assert ".indicador-de-abrir{" in folha
        assert "padding-right:3.2rem" not in folha, (
            "o cartão voltou a reservar o espaço do chevron absoluto"
        )
        # A regra genérica continua existindo para os blocos irmãos; o cartão a
        # desliga com especificidade MAIOR. Sem `details.card` no seletor, o
        # `::after` genérico (0,2,3) vence e a tela mostra dois chevrons.
        assert "details.card > summary.sumario-do-cartao::after{" in folha
        assert ("details.card.cartao-do-resultado > summary.sumario-do-cartao::after"
                "{content:none}") in folha, (
            "o override perdeu especificidade: o ::after genérico volta a desenhar um segundo chevron"
        )


# ---------------------------------------------------------------------------
# O bloco dos descartados: o mesmo recolhimento, e o rodape da analise
# ---------------------------------------------------------------------------

CSV_COM_DESCARTADOS = ("Name,cM\n"
                       "Ana Silva Souza,100\n"
                       "Zzz Ninguem,50\n")

NOME_CSV_DESCARTADOS = "0000000000000003__descartados.csv"


@pytest.fixture
def pagina_com_descartados(cliente_de_upload) -> str:
    _app, cliente, pasta = cliente_de_upload
    for nome, conteudo in ((NOME_GED, GED), (NOME_CSV_DESCARTADOS, CSV_COM_DESCARTADOS)):
        with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
    return cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": NOME_GED,
        "matches_csv_filename": NOME_CSV_DESCARTADOS,
        "root_name": RAIZ,
    }).get_data(as_text=True)


class TestOBlocoDosDescartados:
    """O grupo recolhe pelo mesmo motivo dos cartoes — e continua sendo o rodape da analise."""

    def test_o_titulo_e_o_summary_e_traz_a_contagem(self, pagina_com_descartados):
        assert re.search(
            r'(?s)<summary class="sumario-do-cartao">\s*<div class="card-header">\s*<h5[^>]*>'
            r'Matches descartados \(1\)</h5>',
            pagina_com_descartados), (
            "o resumo do bloco tem de ser o proprio titulo, com a contagem — e nao um `<h2>` "
            "acima de um `details`"
        )

    def test_o_bloco_nasce_fechado(self, pagina_com_descartados):
        blocos = [c for c in _arvore(pagina_com_descartados).cartoes if c["descartados"]]
        assert len(blocos) == 1, f"blocos de descartados: {blocos}"
        assert not blocos[0]["aberto"], "o bloco dos descartados veio aberto"

    def test_o_bloco_tem_summary_e_corpo_como_os_cartoes(self, pagina_com_descartados):
        bloco = [c for c in _arvore(pagina_com_descartados).cartoes if c["descartados"]][0]
        assert bloco["summary_nomeado"] == 1
        assert bloco["corpo"] == 1
        assert bloco["fechou"], "o bloco dos descartados ficou sem `</details>`"

    def test_a_tabela_continua_no_documento(self, pagina_com_descartados):
        """Recolhido nao e' removido: e' o que preserva a leitura do descarte como texto."""
        assert "Zzz Ninguem" in pagina_com_descartados
        assert "sem candidatos por sobrenome" in pagina_com_descartados or (
            "Motivo" in pagina_com_descartados)

    def test_o_bloco_nao_e_alcancado_pelos_botoes_das_analises(self, pagina_com_descartados):
        """Os botoes dizem "Expandir todas as ANALISES", e nao "tudo que recolhe"."""
        assert 'class="card bloco-descartados"' in pagina_com_descartados
        for cartao in _arvore(pagina_com_descartados).cartoes:
            assert not (cartao["do_resultado"] and cartao["descartados"]), (
                "o bloco dos descartados carrega o marcador dos cartoes de analise: os botoes "
                "de expandir/recolher o alcancariam"
            )

    def test_sem_descarte_nao_ha_bloco(self, pagina):
        """A guarda `{% if skipped_matches %}`: sem descarte, o bloco nem existe."""
        assert "Matches descartados" not in pagina
        assert not [c for c in _arvore(pagina).cartoes if c["descartados"]]
