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
    "indice-resultados",
    "kit-grid",
    "destaque",
    "botao-tema",
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
