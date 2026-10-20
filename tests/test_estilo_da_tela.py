"""Rota da folha de estilo (`/app.css`) e o contrato de classes com o template.

## Por que a folha sai por ROTA, e nao por pasta estatica

`src/static/` e **proibida** pelo `W004` (feature 003) e o `RN-07` da feature 009 proibe
configurar diretorio estatico. A folha mora em `src/assets/` — a pasta que o
`.dockerignore` deixa entrar na imagem (`!src/**`) — e sai pela mesma forma das duas rotas
de arte: `GET` sozinho, `ETag`, `304` na rebusca e `404` sem corpo quando o arquivo nao
esta la.

## O que este arquivo mede, e o que ele NAO mede

Ele mede **contrato de rota** e **acoplamento de nomes**. Nao mede aparencia: cor e
espacamento nao tem assert, porque um teste de pixel de folha de estilo envelhece a cada
ajuste de gosto e passa a ser desligado. O que ele prende e o que quebra em silencio — a
rota sumir, o `Content-Type` deixar de ser `text/css` (e o navegador ignorar a folha sem
dizer nada), e um nome de classe usado pelo template nao existir mais no arquivo.
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

CAMINHO = "/app.css"
TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")
FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")

#: Os quatro estados da confrontacao sao TAMBEM nomes de classe CSS
#: (`badge estado-<status>`). Renomear um estado muda o texto e quebra a cor do selo em
#: silencio, sem nenhum outro teste que prenda o par — este prende.
ESTADOS = ("COMPATIVEL", "POSSIVEL", "CONFLITANTE", "INCONCLUSIVO")

#: Classes que a folha PRECISA manter porque o template as usa. Nao e a lista inteira da
#: folha: e a lista do acoplamento. Uma classe daqui sumir nao levanta erro em lugar
#: nenhum — a tela so fica diferente, e ninguem percebe.
CLASSES_DO_TEMPLATE = (
    "main-card",
    "secao",
    "rotulo-fonte",
    "tabela-evidencia",
    "alerta-aviso",
    "documental-ambiguo",
    "graph-container",
    "mermaid",
    "kit-grid",
    "destaque",
    "botao-tema",
    # A terceira verificacao (profundidade do caminho x estimativa do kit) e o selo
    # combinado do cabecalho. Entram na lista pelo mesmo motivo dos outros: sumir da folha
    # nao levanta erro nenhum, so deixa a tela diferente.
    #
    # O selo combinado NAO comeca com `estado-` de proposito: aquele prefixo e reivindicado
    # por `.badge[class*="estado-"]{color:#fff}`, e o texto branco sobre o creme de
    # `--aviso-bg` dava 1,11:1. Ver `TestOContrasteDosSelos`.
    "profundidade-divergencia",
    "profundidade-atencao",
    "alerta-profundidade",
    "alerta-profundidade-divergencia",
    "identidade-impossivel",
    "legenda-do-grafo",
    "legenda-marca",
    # O veredicto do doador e o diagrama recolhido, do mesmo lote: o cartao em que a data do
    # registro impede que ele tenha doado o DNA.
    "veredicto-do-doador",
    "grafo-do-registro",
    # O selo do parentesco que nao e do doador, no indice.
    "parentesco-do-registro",
    # O cartao de resultado recolhivel: o `summary` embrulha o `card-header`, e sumir da folha
    # deixaria o cabecalho sem cursor e sem o sinal de que ha o que abrir.
    "sumario-do-cartao",
    "controles-dos-cartoes",
    "botao-do-cartao",
    # A segunda linha do cabecalho do cartao: o que a tabela do indice dava (Parentesco, Janela
    # de vida, Profundidade) e que subiu para o cartao quando a tabela saiu — adendo 019.
    "cabecalho-sinais",
    "rotulo-parentesco",
    # O bloco recolhivel dos descartados: mesma forma dos cartoes, aparencia de apendice.
    "bloco-descartados",
)


@pytest.fixture
def folha() -> str:
    with open(FOLHA, encoding="utf-8") as arquivo:
        return arquivo.read()


@pytest.fixture
def template() -> str:
    with open(TEMPLATE, encoding="utf-8") as arquivo:
        return arquivo.read()


def _o_que_o_navegador_recebe(marcacao: str) -> str:
    """O template sem o que NAO vira documento: comentario Jinja e comentario HTML.

    Sem esta limpeza o teste mede a prosa dos comentarios: a propria explicacao de que o
    `<style>` saiu cita `<style>`, e o assert acusaria a documentacao da mudanca.
    """
    sem_jinja = re.sub(r"\{#.*?#\}", "", marcacao, flags=re.S)
    return re.sub(r"<!--.*?-->", "", sem_jinja, flags=re.S)


@pytest.fixture
def resposta(cliente_de_upload):
    _app, cliente, _pasta = cliente_de_upload
    return cliente.get(CAMINHO)


class TestRotaDaFolha:
    """O contrato de HTTP, igual ao das duas rotas de arte."""

    def test_a_rota_serve_a_folha(self, resposta):
        assert resposta.status_code == 200

    def test_o_tipo_e_text_css(self, resposta):
        """Sem `text/css` o navegador NAO aplica a folha, e nao avisa ninguem."""
        assert resposta.headers["Content-Type"].startswith("text/css"), (
            "Content-Type errado: o navegador ignora a folha em silencio"
        )

    def test_a_folha_nao_vem_vazia(self, resposta):
        assert len(resposta.get_data()) > 1000, "a folha veio vazia ou truncada"

    def test_escrita_na_rota_e_recusada(self, cliente_de_upload):
        """`RF-06` da 009, por analogia: a rota e de leitura, e a recusa sai do roteador."""
        _app, cliente, _pasta = cliente_de_upload
        assert cliente.post(CAMINHO, data={"x": "y"}).status_code == 405

    def test_a_resposta_traz_marca_de_versao(self, resposta):
        assert resposta.headers.get("ETag"), "a resposta nao trouxe ETag"

    def test_requisicao_repetida_nao_traz_corpo(self, resposta, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        marca = resposta.headers["ETag"]
        repetida = cliente.get(CAMINHO, headers={"If-None-Match": marca})
        assert repetida.status_code == 304
        assert repetida.get_data() == b"", "a resposta de 'nao modificado' trouxe corpo"

    def test_folha_ausente_devolve_404_e_a_tela_continua_de_pe(
        self, cliente_de_upload, monkeypatch
    ):
        """A degradacao e a folha faltar, e nao a tela cair."""
        app, cliente, _pasta = cliente_de_upload
        monkeypatch.setitem(app.config, "ESTILO_DA_TELA", "caminho/que/nao/existe.css")

        assert cliente.get(CAMINHO).status_code == 404
        assert cliente.get("/").status_code == 200, (
            "a tela caiu por causa da folha ausente"
        )


class TestA_Folha_Esta_No_Lugar_Certo:
    """`W004` e `RN-07`: nem pasta estatica, nem diretorio estatico configurado."""

    def test_a_folha_mora_sob_src(self):
        partes = os.path.normpath(FOLHA).split(os.sep)
        assert "src" in partes, f"a folha saiu de src/: {FOLHA}"

    def test_a_folha_nao_esta_em_pasta_estatica(self):
        partes = os.path.normpath(FOLHA).split(os.sep)
        assert "static" not in partes, (
            f"a folha caiu numa pasta estatica: {FOLHA}. src/static/ e proibida (W004)"
        )

    def test_o_app_nao_serve_a_folha_por_caminho_estatico(self, cliente_de_upload):
        """`RN-07` da 009: a folha nao pode reabrir a superficie estatica.

        O `static_folder` padrao do Flask existe e aponta para `src/static/` — o que o
        `W004` exige e que a PASTA nao exista e que nada seja alcancavel por ali. O que
        este teste prende e o efeito, e nao a configuracao: se a folha (ou qualquer outra
        coisa) passar a responder em `/static/...`, a decisao foi desfeita.
        """
        _app, cliente, _pasta = cliente_de_upload
        assert cliente.get("/static/app.css").status_code == 404, (
            "a folha passou a ser alcancavel por caminho estatico (W004/RN-07)"
        )

    def test_a_pasta_estatica_continua_ausente(self):
        assert not os.path.isdir(os.path.join(_RAIZ, "src", "static")), (
            "src/static/ reapareceu no disco: e o W004 reaberto"
        )


class TestO_Acoplamento_Com_O_Template:
    """O que quebra em silencio quando alguem mexe na folha ou no template."""

    def test_a_tela_aponta_para_a_folha_servida(self, template):
        assert '<link href="/app.css" rel="stylesheet">' in template, (
            "o template nao carrega /app.css: a identidade visual nao chega a tela"
        )

    def test_o_estilo_inline_nao_voltou(self, template):
        """O `<style>` embutido saiu, e nao pode voltar pela metade.

        Sem esta guarda, a proxima correcao de aparencia entra no `<style>` por habito, a
        folha e o embutido divergem, e a que vence passa a depender da ordem no documento.
        """
        assert "<style" not in _o_que_o_navegador_recebe(template), (
            "o template voltou a ter `<style>` embutido; a folha e a autoridade unica"
        )

    def test_as_classes_do_template_existem_na_folha(self, folha):
        faltando = [nome for nome in CLASSES_DO_TEMPLATE if f".{nome}" not in folha]
        assert not faltando, f"a folha perdeu classe usada pelo template: {faltando}"

    @pytest.mark.parametrize("estado", ESTADOS)
    def test_os_quatro_estados_tem_cor(self, folha, estado):
        assert f".estado-{estado}" in folha, (
            f"o estado {estado} perdeu a regra de cor; o selo fica sem fundo e o texto branco "
            "some no branco da pagina"
        )

    def test_o_template_emite_a_classe_de_estado(self, template):
        assert "estado-{{ result.comparison.status }}" in template, (
            "o template deixou de usar o nome do estado como classe do selo"
        )

    def test_o_cabecalho_usa_o_rotulo_combinado(self, template):
        """O selo do cabecalho nao pode contradizer o aviso logo abaixo.

        Medido num cartao real: "Compatível" no cabecalho e "nenhuma pessoa com essa idade
        pode ter doado DNA" no aviso seguinte. Os dois estavam certos sobre eixos diferentes,
        mas o selo e o mais visivel — entao o cabecalho le `confrontacao_efetiva`, e a secao 4
        continua lendo o veredito de cM, que e outra pergunta.
        """
        assert "estado-{{ result.confrontacao_efetiva }}" in template, (
            "o cabecalho voltou a mostrar o veredito cru do confronto"
        )


class TestO_Controle_De_Tema:
    """Claro como PADRAO, escuro por escolha do operador, e a escolha lembrada."""

    def test_o_padrao_e_o_claro(self, template):
        """A decisao explicita: quem nunca escolheu abre a aplicacao no branco.

        A versao anterior decidia por `matchMedia('(prefers-color-scheme: dark)')`, entao quem
        tinha o Windows no escuro caia no escuro **sem ter pedido**. O padrao voltar a depender
        do sistema e a regressao que este teste prende.
        """
        corpo = _o_que_o_navegador_recebe(template)
        assert "'light'" in corpo, "o tema padrao deixou de ser o claro"
        assert "matchMedia" not in corpo, (
            "a preferencia do sistema voltou a decidir o tema: o padrao tem de ser o claro"
        )

    def test_o_botao_de_tema_esta_na_tela(self, template):
        assert 'id="botao-tema"' in template, "a tela perdeu o controle de tema"
        assert 'class="botao-tema"' in template

    def test_ha_um_botao_so_no_documento(self, template):
        """Ele vive fora dos dois ramos da tela: duas copias seriam dois `id` iguais."""
        assert template.count('id="botao-tema"') == 1, (
            "o botao de tema foi duplicado; `id` repetido faz o `getElementById` pegar so o "
            "primeiro e o segundo botao nascer morto"
        )

    def test_o_botao_informa_o_estado_e_a_acao(self, template):
        """`aria-pressed` carrega o ESTADO e o `aria-label`, a ACAO — os dois sao necessarios."""
        assert "aria-pressed" in template, (
            "o botao nao informa se o tema escuro esta ligado ou desligado"
        )
        assert "aria-label" in template, "o botao nao diz o que o clique faz"

    def test_a_escolha_do_operador_e_lembrada(self, template):
        assert "localStorage.setItem('tema'" in template, (
            "a escolha de tema nao e guardada: o operador teria de reescolher a cada visita"
        )

    def test_o_botao_sobrevive_ao_armazenamento_indisponivel(self, template):
        """Em modo privativo `localStorage` lanca; a pagina tem de continuar utilizavel."""
        assert "try" in template and "catch" in template, (
            "sem guarda, `localStorage` bloqueado derruba o script e o botao nasce morto"
        )

    def test_o_botao_tem_estilo_na_folha(self, folha):
        assert ".botao-tema" in folha, (
            "o botao de tema ficaria sem posicao nem forma na folha"
        )


class TestOTextoDoSobreODestrutivo:
    """O "Apagar" no tema escuro: branco fixo sobre `#EE9A88` dava **2,18:1**.

    Medido em 2026-10-11, e o defeito era do refresh de design: o `.btn-primary` sempre usou
    `var(--on-primary)`, que o tema escuro redefine, e o `.btn-danger` ficou com `#fff` escrito
    a mao. No claro o literal funcionava (6,69:1), entao a folha parecia certa.
    """

    def _regra_do_destrutivo(self, folha: str) -> str:
        bloco = re.search(r"\.btn-danger\{([^}]*)\}", folha, re.S)
        assert bloco, "a regra do `.btn-danger` sumiu da folha"
        return bloco.group(1)

    def test_a_cor_do_texto_nao_e_fixada(self, folha):
        regra = self._regra_do_destrutivo(folha)
        assert "var(--on-danger)" in regra, (
            "o `.btn-danger` precisa tirar a cor do texto de `--on-danger`"
        )
        assert "#fff" not in regra.lower(), (
            "o `.btn-danger` voltou a fixar branco: no tema escuro o rotulo do 'Apagar' "
            "desaparece no hover (2,18:1)"
        )

    def test_os_dois_temas_definem_a_cor_do_texto(self, folha):
        assert folha.count("--on-danger:") == 2, (
            "`--on-danger` precisa ser definida no tema claro E no escuro: e a cor do texto "
            "SOBRE o `--danger`, e o `--danger` muda de tom entre os dois"
        )


# ---------------------------------------------------------------------------
# CONTRASTE DOS SELOS.
#
# O caso medido, em 2026-10-14: o operador relatou que o selo combinado do cabecalho estava
# "em branco, pois nao consigo ler". Nao era a regra do selo: era
# `.badge[class*="estado-"]{color:#fff}` — especificidade (0,2,0) — vencendo
# `.estado-identidade_impossivel`, (0,1,0). Texto branco sobre o creme de `--aviso-bg`:
# **1,11:1** no tema claro. No escuro o mesmo selo dava 15,26:1, porque la `--aviso-bg` e
# escuro — um teste de um tema so nao pegaria.
#
# Um teste que lesse apenas a regra do selo teria passado com a tela ilegivel. Por isso a cor
# efetiva e resolvida pela CASCATA: todas as regras que casam com o elemento, vencendo a de
# maior especificidade (e, no empate, a ultima) — que e o que o navegador faz.
#
# Os dois erros que a sonda `_reversa_bugs/_sondas-matching/contraste_dos_selos.py` cometeu
# antes de servir, e que estao corrigidos aqui: os COMENTARIOS precisam sair antes do parser
# (senao o seletor vira `/* ... */ .badge[...]` e nada casa), e seletor de ELEMENTO (`body`,
# `h1,h2,h3`) casaria com tudo e todo selo herdaria a cor do `h5`.
# ---------------------------------------------------------------------------

#: Os selos que o template emite, na forma exata de `class="..."`.
SELOS_DO_TEMPLATE = (
    "badge estado-COMPATIVEL",
    "badge estado-POSSIVEL",
    "badge estado-CONFLITANTE",
    "badge estado-INCONCLUSIVO",
    "badge identidade-a-confirmar",
    "badge identidade-impossivel",
    "badge janela-impossivel",
    "badge janela-suspeita",
    "badge janela-imprecisa",
    "badge profundidade-divergencia",
    "badge profundidade-atencao",
    "badge parentesco-do-registro",
    "badge endogamia-estrutural",
    "badge endogamia-filtro",
)

#: WCAG 2.1, nivel AA para texto normal.
CONTRASTE_MINIMO = 4.5

_BLOCO_CSS = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
_VAR = re.compile(r"var\((--[\w-]+)\)")


def _sem_comentario(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _sem_media(css: str) -> str:
    """Os blocos `@media` saem: nenhum deles toca em selo, e o parser nao os entende."""
    saida, i = [], 0
    while i < len(css):
        if css.startswith("@media", i):
            j = css.index("{", i)
            profundidade = 0
            while j < len(css):
                if css[j] == "{":
                    profundidade += 1
                elif css[j] == "}":
                    profundidade -= 1
                    if profundidade == 0:
                        break
                j += 1
            i = j + 1
            continue
        saida.append(css[i])
        i += 1
    return "".join(saida)


def _regras(css: str) -> list:
    return [(" ".join(sel.split()), corpo)
            for sel, corpo in _BLOCO_CSS.findall(_sem_media(_sem_comentario(css)))]


def _variaveis(css: str, tema: str) -> dict:
    valores = {}
    for seletor, corpo in _regras(css):
        vale = seletor == ":root" or (
            seletor == ':root[data-bs-theme="dark"]' and tema == "escuro")
        if not vale:
            continue
        for decl in corpo.split(";"):
            nome, _, valor = decl.partition(":")
            if nome.strip().startswith("--"):
                valores[nome.strip()] = valor.strip()
    return valores


def _resolve(valor: str, variaveis: dict) -> str:
    anterior = None
    while anterior != valor:
        anterior = valor
        valor = _VAR.sub(lambda m: variaveis.get(m.group(1), m.group(0)), valor)
    return valor.strip()


def _casa(seletor: str, classes: str) -> bool:
    if not seletor or seletor.startswith(("@", ":")) or " " in seletor or ">" in seletor:
        return False
    nomes = re.findall(r"\.([\w-]+)", seletor)
    atributos = re.findall(r'\[class\*="([^"]+)"\]', seletor)
    if not nomes and not atributos:
        return False
    if not all(nome in classes.split() for nome in nomes):
        return False
    return all(alvo in classes for alvo in atributos)


def _especificidade(seletor: str) -> int:
    return len(re.findall(r"\.([\w-]+)", seletor)) + seletor.count("[class")


def _valor_efetivo(css: str, classes: str, propriedade: str, variaveis: dict):
    """O valor que o NAVEGADOR aplica: maior especificidade e, no empate, a ultima regra."""
    vencedor = None
    for indice, (seletor, corpo) in enumerate(_regras(css)):
        if not _casa(seletor, classes):
            continue
        for decl in corpo.split(";"):
            nome, _, valor = decl.partition(":")
            nome = nome.strip()
            if nome == propriedade or (propriedade == "background-color"
                                       and nome == "background"):
                chave = (_especificidade(seletor), indice)
                if vencedor is None or chave >= vencedor[0]:
                    vencedor = (chave, valor.strip())
    return _resolve(vencedor[1], variaveis) if vencedor else None


def _rgb(cor):
    if cor is None:
        return None
    cor = cor.strip().lower()
    if cor in ("transparent", "none", "inherit", "initial"):
        return None
    if cor.startswith("#"):
        hexa = cor[1:]
        if len(hexa) == 3:
            hexa = "".join(c * 2 for c in hexa)
        return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))
    achado = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", cor)
    return tuple(int(achado.group(i)) for i in (1, 2, 3)) if achado else None


def _luminancia(cor) -> float:
    def canal(valor):
        valor = valor / 255
        return valor / 12.92 if valor <= 0.03928 else ((valor + 0.055) / 1.055) ** 2.4
    vermelho, verde, azul = cor
    return (0.2126 * canal(vermelho) + 0.7152 * canal(verde) + 0.0722 * canal(azul))


def _contraste(cor_a, cor_b) -> float:
    la, lb = _luminancia(cor_a), _luminancia(cor_b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


class TestOContrasteDosSelos:
    """Todo selo da tela tem de ser legivel nos DOIS temas.

    O defeito que originou esta classe era invisivel para um teste de tema unico: no escuro o
    mesmo selo dava 15,26:1. E era invisivel para um teste que lesse so a regra do selo,
    porque quem vencia a cor era outra regra.
    """

    @pytest.mark.parametrize("tema", ["claro", "escuro"])
    @pytest.mark.parametrize("classes", SELOS_DO_TEMPLATE)
    def test_o_texto_do_selo_e_legivel_sobre_o_proprio_fundo(self, folha, classes, tema):
        variaveis = _variaveis(folha, tema)
        texto = _rgb(_valor_efetivo(folha, classes, "color", variaveis))
        fundo = _rgb(_valor_efetivo(folha, classes, "background-color", variaveis))
        # Selo sem fundo proprio fica sobre o cartao, que e `--surface` nos dois temas.
        if fundo is None:
            fundo = _rgb(_resolve("var(--surface)", variaveis))

        assert texto and fundo, (
            f"nao consegui resolver a cor efetiva de `{classes}` no tema {tema}: "
            f"texto={texto} fundo={fundo}. O parser ou a folha mudaram de forma."
        )
        razao = _contraste(texto, fundo)
        assert razao >= CONTRASTE_MINIMO, (
            f"`{classes}` no tema {tema}: texto {texto} sobre fundo {fundo} da "
            f"{razao:.2f}:1, abaixo de {CONTRASTE_MINIMO}:1. O operador nao consegue ler."
        )

    def test_o_prefixo_estado_e_reservado_aos_quatro_estados(self, folha):
        """Quem tem `estado-` no nome herda `color:#fff` — e isso so serve para cor cheia.

        O selo combinado do cabecalho se chamava `.estado-identidade_impossivel` e saiu branco
        sobre creme por causa desta regra. O nome mudou; esta guarda impede que outro selo de
        aviso volte a usar o prefixo, e confere que a regra do branco continua existindo (sem
        ela, os quatro estados ficariam com texto escuro sobre cor cheia).
        """
        brancos = _valor_efetivo(folha, "badge estado-COMPATIVEL", "color",
                                 _variaveis(folha, "claro"))
        assert brancos and brancos.replace(" ", "") == "#fff", (
            "a regra do texto branco dos estados mudou: confira se o prefixo `estado-` ainda "
            "esta reservado"
        )
        # Os comentarios saem antes das checagens de TEXTO: o comentario de
        # `.identidade-impossivel` cita o nome antigo para documentar o defeito, e sem esta
        # limpeza a guarda acharia a propria documentacao. Foi a mesma armadilha que a sonda
        # caiu, e por isso ela esta registrada nos dois lugares.
        codigo = _sem_comentario(folha)
        for estado in ESTADOS:
            assert f".estado-{estado}" in codigo
        assert ".estado-identidade" not in codigo, (
            "um selo de aviso voltou a usar o prefixo `estado-`: ele sairia com texto branco"
        )

    def test_os_selos_de_aviso_partem_da_paleta_de_aviso(self, folha):
        """Contraste igual ao dos vizinhos, e nao cor inventada."""
        claro = _variaveis(folha, "claro")
        for classes in ("badge identidade-impossivel", "badge janela-impossivel",
                        "badge profundidade-divergencia"):
            # `_valor_efetivo` ja resolve o `var()`: comparar com o literal daria sempre
            # diferente.
            assert (_valor_efetivo(folha, classes, "background-color", claro)
                    == _resolve("var(--aviso-bg)", claro))
            assert (_valor_efetivo(folha, classes, "color", claro)
                    == _resolve("var(--danger)", claro))
