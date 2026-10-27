"""A impressao do resultado por pessoa (feature 050).

## Por que este arquivo existe

Nenhum teste do projeto olha para a impressao: o `SHA_DA_TELA` mede a tela de ENTRADA
vazia, o `test_estado_do_resultado.py` prende o cartao e o `test_paginacao_na_tela.py`
prende a pagina da lista. Sem este arquivo, apagar o botao do cabecalho, o bloco de
identificacao, o container de impressao ou as regras de `@media print` deixaria a suite
verde — e a feature inteira sumiria sem um unico teste vermelho.

## O que ele mede, e o que ele NAO mede

Mede **presenca, contrato e ligacao**, nunca aparencia: nao ha assert de cor de tela,
largura ou posicao — isso e da folha, e a folha e presa pelo par classe-no-template /
`.classe`-na-folha.

1. **A marcacao nasce no HTML.** Este projeto testa markup renderizado e nao executa
   JavaScript: um botao montado no `DOMContentLoaded` passaria a existir so no navegador,
   e nenhum teste o veria.
2. **O comando e por cartao, e o nome acessivel identifica a pessoa.** Um "Imprimir"
   generico no topo da pagina nao diz de quem e a folha.
3. **A identificacao leva a referencia armazenada**, a mesma chave de conteudo que a
   auditoria da feature 049 usa — e nao o rotulo visivel.
4. **O container nao existe na tela vazia.** Ele nasce dentro do ramo dos resultados;
   fora dele, a tela de entrada ganharia marcacao nova sem ter cartao para imprimir.
5. **A folha de estilo isola o documento na impressao**, e nao na tela.

## O caminho e o de PRODUCAO

Como no `test_paginacao_na_tela.py`: os arquivos entram na pasta de upload e o `POST` de
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

from tests.fixtures.sample_dna import DNA_CSV_OITO_CONEXOES, DNA_GED  # noqa: E402

CHAVE_ARVORE = "080e7943572d2652"
CHAVE_CSV = "94e2402671702cac"
ARVORE = CHAVE_ARVORE + "__Arvore.ged"
RELATORIO = CHAVE_CSV + "__Matches.csv"
RAIZ_DA_ARVORE = "Carlos Silva Souza"
PESSOA_DO_CSV = "Ana Silva Souza"

FOLHA = os.path.join(_RAIZ, "src", "assets", "app.css")

#: As classes que a feature introduz. Cada uma tem de existir na folha: o par
#: classe-no-template / `.classe`-na-folha nao quebra nada em silencio, so muda a tela.
#: O container entra por ID (`#area-de-impressao`) e tem assert proprio.
CLASSES_DA_IMPRESSAO = (
    "imprimir-conexao",
    "identificacao-da-impressao",
    "linha-da-identificacao",
    "quando-da-impressao",
    "cartao-em-impressao",
    "folha-do-diagrama",
    "origem-da-impressao",
)


def _guardar(pasta: str, nome: str, conteudo: str) -> None:
    with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)


def _analisar(cliente_de_upload) -> str:
    """O HTML do estado de resultado, pelo caminho de producao."""
    _app, cliente, pasta = cliente_de_upload
    _guardar(pasta, ARVORE, DNA_GED)
    _guardar(pasta, RELATORIO, DNA_CSV_OITO_CONEXOES)

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


def _folha_sem_comentario() -> str:
    """A folha servida, sem comentarios e sem espacos.

    Sem espacos porque a comparacao e de CONTEUDO: `display: none` e `display:none`
    sao a mesma regra, e prender a formatacao tornaria o teste refem do estilo de
    escrita de quem edita a folha.
    """
    with open(FOLHA, "r", encoding="utf-8") as arquivo:
        folha = arquivo.read()
    sem_comentario = re.sub(r"/\*.*?\*/", "", folha, flags=re.S)
    return re.sub(r"\s+", "", sem_comentario)


def _scripts(marcacao: str) -> str:
    """O corpo de TODOS os `<script>` inline, juntos."""
    blocos = re.findall(r"(?s)<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", marcacao)
    assert blocos, "nao ha script inline no documento"
    return "\n".join(blocos)


@pytest.fixture
def pagina(cliente_de_upload) -> str:
    """Oito conexoes: oito cartoes, um por kit."""
    return _analisar(cliente_de_upload)


class TestOComandoPorCartao:
    """Cada cartao tem o seu comando, no cabecalho, com o nome da pessoa."""

    def test_cada_cartao_tem_um_comando(self, pagina):
        cartoes = re.findall(r'<details[^>]*class="card cartao-do-resultado"', pagina)
        comandos = re.findall(r'<button[^>]*class="imprimir-conexao"', pagina)
        assert len(cartoes) == 8, f"esperados 8 cartoes, medidos {len(cartoes)}"
        assert len(comandos) == len(cartoes), (
            f"{len(comandos)} comandos para {len(cartoes)} cartoes: cada conexao tem de "
            "poder ser impressa sozinha"
        )

    def test_o_comando_aponta_para_o_cartao(self, pagina):
        alvos = set(re.findall(r'class="imprimir-conexao"[^>]*data-imprimir="(resultado-\d+)"', pagina))
        assert alvos == {f"resultado-{n}" for n in range(1, 9)}, (
            f"os alvos medidos foram {sorted(alvos)}"
        )

    def test_o_comando_e_um_botao_de_verdade(self, pagina):
        assert re.search(r'<button type="button" class="imprimir-conexao"', pagina), (
            "tem de ser `<button type=\"button\">`: um link dispararia navegacao, e um "
            "botao sem `type` dentro de formulario submitiria a pagina"
        )

    def test_o_nome_acessivel_identifica_a_pessoa(self, pagina):
        rotulos = re.findall(r'class="imprimir-conexao"[^>]*aria-label="([^"]+)"', pagina)
        assert rotulos, "o comando nao tem nome acessivel"
        assert all(PESSOA_DO_CSV in rotulo for rotulo in rotulos), (
            f'"Imprimir" sozinho nao diz de quem e a folha; medidos: {rotulos[:2]}'
        )

    def test_o_comando_fica_depois_do_voltar_no_documento(self, pagina):
        trecho = re.search(r'class="controles-do-cabecalho".*?</span>\s*</span>', pagina, flags=re.S)
        assert trecho, "o grupo de controles do cabecalho nao esta no documento"
        bloco = trecho.group(0)
        assert bloco.index("voltar-ao-indice") < bloco.index("imprimir-conexao"), (
            "o comando foi pedido ao lado do \"Voltar\", depois dele"
        )


class TestAIdentificacaoDaFolha:
    """O bloco que so aparece no papel: de qual analise esta folha saiu."""

    def test_cada_cartao_tem_a_identificacao(self, pagina):
        assert pagina.count('class="identificacao-da-impressao"') == 8

    def test_os_tres_campos_sao_as_referencias_armazenadas(self, pagina):
        blocos = re.findall(
            r'(?s)<div class="identificacao-da-impressao">(.*?)</div>',
            pagina,
        )
        assert blocos, "o bloco de identificacao nao esta no documento"
        for bloco in blocos:
            assert "Árvore:" in bloco and ARVORE in bloco
            assert "CSV:" in bloco and RELATORIO in bloco
            assert "Raiz:" in bloco and RAIZ_DA_ARVORE in bloco

    def test_o_momento_e_um_lugar_vazio_preenchido_no_clique(self, pagina):
        assert '<time class="quando-da-impressao"></time>' in pagina, (
            "o servidor nao tem a hora da impressao: o lugar nasce vazio e o script preenche"
        )


class TestOContainerDeImpressao:
    """O destino do clone existe com resultado, e nao na tela de entrada."""

    def test_o_container_existe_no_resultado(self, pagina):
        assert re.search(r'<div id="area-de-impressao" aria-hidden="true"></div>', pagina)

    def test_o_container_nao_existe_na_tela_vazia(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        tela = cliente.get("/").get_data(as_text=True)
        assert '<div id="area-de-impressao"' not in tela, (
            "o container nasce no ramo dos resultados: a tela de entrada nao ganha marcacao "
            "nova (RF-11). O script pode cita-lo — o que nao pode e o ELEMENTO existir."
        )


class TestAFolhaDeEstilo:
    """As regras que fazem a folha sair so com uma pessoa."""

    @pytest.mark.parametrize("classe", CLASSES_DA_IMPRESSAO)
    def test_a_classe_existe_na_folha(self, classe):
        assert f".{classe}" in _folha_sem_comentario(), (
            f"`.{classe}` nao esta em app.css: o par classe-no-template / classe-na-folha "
            "se rompeu"
        )

    def test_o_container_fica_oculto_na_tela(self):
        assert "#area-de-impressao{display:none}" in _folha_sem_comentario()

    def test_a_identificacao_fica_oculta_na_tela(self):
        assert ".identificacao-da-impressao{display:none}" in _folha_sem_comentario()

    def test_a_isolacao_so_vale_na_impressao(self):
        folha = _folha_sem_comentario()
        assert "@mediaprint{" in folha
        assert "body.imprimindo>*:not(#area-de-impressao)" in folha, (
            "sem a regra de isolamento, a folha imprime a pagina inteira"
        )

    def test_o_desenho_abre_folha_propria(self):
        assert ".folha-do-diagrama{break-before:page}" in _folha_sem_comentario()

    def test_a_linha_de_tabela_nao_e_cortada(self):
        assert "tr{break-inside:avoid}" in _folha_sem_comentario()

    def test_o_rodape_repete_em_toda_folha(self):
        folha = _folha_sem_comentario()
        assert ".origem-da-impressao{position:fixed" in folha, (
            "o rodape fixo e o que leva a origem a todas as folhas"
        )

    def test_os_selos_viram_contorno_no_papel(self):
        folha = _folha_sem_comentario()
        assert "#area-de-impressao.badge{background:#fff!important" in folha, (
            "o navegador nao imprime fundos por padrao: texto branco sobre cor cheia "
            "sumiria no papel"
        )

    def test_o_papel_e_sempre_claro(self):
        assert "--ink:#111" in _folha_sem_comentario(), (
            "os tokens do tema claro tem de ser redeclarados na impressao"
        )


class TestOLigarDoScript:
    """O que a suite consegue prender do comportamento, sem executar JavaScript."""

    def test_a_rotina_de_impressao_esta_no_documento(self, pagina):
        script = _scripts(pagina)
        assert "imprimirCartao" in script
        assert "montarDocumentoDaImpressao" in script
        assert "area-de-impressao" in script

    def test_o_clique_nao_alterna_o_cartao(self, pagina):
        script = _scripts(pagina)
        assert "preventDefault" in script and "stopPropagation" in script, (
            "o botao mora dentro do `summary`: sem as duas guardas, o clique recolhe o "
            "cartao junto"
        )
        assert "closest(\"details.cartao-do-resultado\")" in script

    def test_a_espera_do_desenho_observa_o_dom(self, pagina):
        script = _scripts(pagina)
        assert "MutationObserver" in script, (
            "o Mermaid e assincrono: sem esperar o SVG, o desenho sai em branco"
        )

    def test_a_restauracao_usa_afterprint(self, pagina):
        script = _scripts(pagina)
        assert "afterprint" in script

    def test_as_folhas_do_desenho_nascem_com_titulo(self, pagina):
        script = _scripts(pagina)
        assert "folha-do-diagrama" in script
        assert "origem-da-impressao" in script
