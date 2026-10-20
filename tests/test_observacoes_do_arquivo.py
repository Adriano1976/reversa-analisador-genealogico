"""As observacoes do ARQUIVO nao sao observacoes de um CARTAO.

Adendo 017. O aviso que vale para o CSV inteiro (`multiplos_kits`, `kit_ausente`,
linhas ignoradas, cabecalho fora do lugar, raiz ambigua) tem de aparecer **uma vez**,
no bloco proprio da analise — e **nunca** dentro da secao "5. Observacoes" de um
cartao. O aviso de um par (nome, kit) especifico continua no cartao daquele par.

O defeito medido, no arquivo real que motivou a regra
(`03f50d273442cef1__Famílias_Sergipanas.csv`, 142 cartoes):

- o aviso de multiplos kits ocupava **710 das 1010 linhas** da secao 5 (70,3%);
- aparecia em **142 de 142 cartoes**;
- em **3 dos 5 casos** falava de nomes que a triagem descartou e que nao tem cartao
  nenhum (`*Carol`, `*DPF`, `Moacir Andrade`) — o operador lia, no cartao de uma
  conexao qualquer, a contabilidade de kits de gente que nao aparece no relatorio.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _pasta in (_RAIZ, os.path.join(_RAIZ, "src"), os.path.join(_RAIZ, "tests")):
    if _pasta not in sys.path:
        sys.path.insert(0, _pasta)

from core.dna_analysis import dna_analysis  # noqa: E402
from core.genetic_evidence import build_genetic_evidence  # noqa: E402
from fixtures.helpers import arvore_de, deps  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

TEMPLATE = os.path.join(_RAIZ, "src", "templates", "index.html")

RAIZ = "Carlos Silva Souza"

# O GEDCOM minimo que faz a analise ter o que analisar: a raiz, uma pessoa que
# casa por nome (e vira cartao) e o grafo de familia que liga as duas.
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
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
0 TRLR
"""

# Dois kits para o MESMO nome: e a condicao que dispara o aviso de arquivo.
CSV_DOIS_KITS = ("Kit number,Name,cM\n"
                 "A1111111,Ana Silva Souza,100\n"
                 "B2222222,Ana Silva Souza,50\n")

# Dois kits para um nome que NAO existe na arvore: o aviso continua sendo do
# arquivo, e nenhum cartao existe para carrega-lo. Era este o caso que aparecia
# em 3 dos 5 avisos do arquivo real.
CSV_SEM_CARTAO = ("Kit number,Name,cM\n"
                  "A1111111,Zzz Ninguem,100\n"
                  "B2222222,Zzz Ninguem,50\n")


@pytest.fixture
def arvore(tmp_path):
    caminho = os.path.join(str(tmp_path), "arvore.ged")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(GED)
    return carregar_arvore(caminho)


def _escrever(tmp_path, texto, nome="matches.csv"):
    caminho = os.path.join(str(tmp_path), nome)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    return caminho


def _analisar(tmp_path, arvore, csv_texto):
    """Roda o nucleo pelo canal de producao e devolve o que a tela recebe."""
    caminho = _escrever(tmp_path, csv_texto)
    observacoes_do_arquivo = []
    resultados, descartados, mensagem = dna_analysis(
        caminho, RAIZ, deps(), arvore, observacoes_do_arquivo=observacoes_do_arquivo)
    return resultados, descartados, mensagem, observacoes_do_arquivo


# ---------------------------------------------------------------------------
# O nivel de cada aviso
# ---------------------------------------------------------------------------

def _sem_comentarios_jinja(html: str) -> str:
    """Remove `{# ... #}` antes de procurar marcadores.

    Sem isto o teste encontra o `{% if dna_results %}` que aparece DENTRO de um
    comentario que explica justamente que o bloco fica fora daquela guarda — a
    mesma armadilha que ja mordeu a sondagem de contraste dos selos.
    """
    return re.sub(r"\{#.*?#\}", "", html, flags=re.S)


class TestONivelDeCadaAviso:
    """`nivel` e o que decide onde o aviso cabe — e ele vem da origem, nao da tela."""

    def test_todo_aviso_traz_nivel(self, tmp_path):
        df = read_csv_with_fallback(_escrever(tmp_path, CSV_DOIS_KITS, "nivel.csv"))
        _evidencias, avisos = build_genetic_evidence(df)
        assert avisos, "o CSV de dois kits tem de produzir aviso"
        for aviso in avisos:
            assert aviso.get("nivel") in {"arquivo", "cartao"}, (
                f"o aviso {aviso.get('code')!r} nao declara nivel")

    def test_multiplos_kits_e_kit_ausente_sao_do_arquivo(self, tmp_path):
        df = read_csv_with_fallback(_escrever(tmp_path, CSV_DOIS_KITS, "dois.csv"))
        _evidencias, avisos = build_genetic_evidence(df)
        por_codigo = {a["code"]: a for a in avisos}
        assert por_codigo["multiplos_kits"]["nivel"] == "arquivo"

        df_sem_kit = read_csv_with_fallback(
            _escrever(tmp_path, "Name,cM\nAna Silva Souza,100\n", "sem_kit.csv"))
        _evidencias, avisos = build_genetic_evidence(df_sem_kit)
        por_codigo = {a["code"]: a for a in avisos}
        assert por_codigo["kit_ausente"]["nivel"] == "arquivo"

    def test_mrca_divergente_e_do_cartao_e_diz_de_quem_e(self, tmp_path):
        """O aviso de um par (nome, kit) so pode aparecer no cartao daquele par.

        Este e o unico aviso de nivel `cartao` de `build_genetic_evidence`: ele
        carrega `chave_nome` e `chave_kit` para que o orquestrador o entregue ao
        cartao certo, e nao a todos — o mesmo vazamento, um nivel abaixo.
        """
        df = read_csv_with_fallback(_escrever(
            tmp_path,
            "Kit number,Name,cM,MRCA\n"
            "A1111111,Ana Silva Souza,100,5.0\n"
            "A1111111,Ana Silva Souza,100,9.0\n",
            "divergente.csv"))
        _evidencias, avisos = build_genetic_evidence(df)
        divergentes = [a for a in avisos if a["code"] == "mrca_divergente"]
        assert len(divergentes) == 1, [a["code"] for a in avisos]
        assert divergentes[0]["nivel"] == "cartao"
        assert divergentes[0]["chave_kit"] == "A1111111"
        assert divergentes[0]["chave_nome"], "sem a chave do nome o aviso iria para todo cartao"


# ---------------------------------------------------------------------------
# A frase reescrita: fato dos dados, e nao recibo da contabilidade do programa
# ---------------------------------------------------------------------------

class TestAFrase:
    """A frase tem de dizer de quem fala, quanto vale cada kit e o que a soma faria crer."""

    def _frase(self, tmp_path, arvore):
        _resultados, _descartados, _mensagem, observacoes = _analisar(
            tmp_path, arvore, CSV_DOIS_KITS)
        assert len(observacoes) == 1, observacoes
        return observacoes[0]

    def test_diz_o_nome_e_os_dois_kits_com_o_valor_de_cada_um(self, tmp_path, arvore):
        frase = self._frase(tmp_path, arvore)
        assert "mais de um kit" in frase
        assert "Ana Silva Souza" in frase
        assert "A1111111 com 100 cM" in frase
        assert "B2222222 com 50 cM" in frase

    def test_nomeia_a_soma_que_ela_proibe(self, tmp_path, arvore):
        """Sem o numero da soma, a frase pede que o operador acredite nela."""
        frase = self._frase(tmp_path, arvore)
        assert "150 cM" in frase
        assert "não podem ser somados" in frase

    def test_diz_o_parentesco_que_a_soma_faria_acreditar(self, tmp_path, arvore):
        """150 cM admite relacoes proximas que nenhum dos dois kits sustenta."""
        frase = self._frase(tmp_path, arvore)
        assert "Shared cM Project" in frase
        assert "nenhum dos kits sustenta" in frase

    def test_diz_que_cada_kit_tem_cartao_proprio(self, tmp_path, arvore):
        assert "próprio cartão" in self._frase(tmp_path, arvore)

    def test_o_texto_antigo_da_contabilidade_interna_saiu(self, tmp_path, arvore):
        """A redacao descrevia o programa ("cada combinação pessoa + kit foi mantida
        separada"), e nao os dados do operador — e nao dizia o que fazer."""
        frase = self._frase(tmp_path, arvore)
        assert "Cada combinação pessoa + kit foi mantida separada" not in frase
        assert "nunca foram somados entre kits diferentes" not in frase

    def test_o_cm_sai_no_formato_que_a_tela_usa(self, tmp_path, arvore):
        """`utils.number_format.formatar_cm` e a autoridade unica do formato de cM.

        Sem ela o bloco do arquivo diria "27.75 cM" enquanto o cartao logo abaixo
        diria "27,75 cM" — dois formatos para o mesmo numero na mesma pagina.
        """
        csv = ("Kit number,Name,cM\n"
               "A1111111,Ana Silva Souza,27.75\n"
               "B2222222,Ana Silva Souza,5.25\n")
        _r, _d, _m, observacoes = _analisar(tmp_path, arvore, csv)
        assert "27,75 cM" in observacoes[0]
        assert "5,25 cM" in observacoes[0]
        assert "33 cM" in observacoes[0], "a soma de 27,75 e 5,25"
        assert "27.75" not in observacoes[0]
        assert "33.0" not in observacoes[0]


# ---------------------------------------------------------------------------
# O nao-vazamento: nenhum aviso de arquivo dentro de cartao
# ---------------------------------------------------------------------------

class TestONaoVazamentoParaOCartao:

    def test_o_aviso_de_arquivo_aparece_uma_vez_e_nao_nos_cartoes(self, tmp_path, arvore):
        resultados, _descartados, _mensagem, observacoes = _analisar(
            tmp_path, arvore, CSV_DOIS_KITS)
        assert len(resultados) == 2, "os dois kits viram dois cartoes"
        assert len(observacoes) == 1, "uma vez para o arquivo"
        for resultado in resultados:
            assert not any("mais de um kit" in o for o in resultado["observations"]), (
                "o aviso de arquivo nao pode se repetir dentro do cartao")

    def test_a_contagem_que_motivou_a_regra(self, tmp_path, arvore):
        """5 nomes com dois kits davam 5 linhas identicas em CADA cartao.

        Aqui, com um nome so, o defeito teria 2 repeticoes; o numero exato do
        arquivo real esta no adendo 017 (710 de 1010 linhas, 142 de 142 cartoes).
        """
        resultados, _descartados, _mensagem, observacoes = _analisar(
            tmp_path, arvore, CSV_DOIS_KITS)
        repetidas = sum(1 for r in resultados
                        for o in r["observations"] if "mais de um kit" in o)
        assert repetidas == 0, f"o aviso de arquivo se repetiu {repetidas} vez(es)"
        assert len(observacoes) == 1

    def test_sem_cartao_nenhum_o_aviso_do_arquivo_nao_se_perde(self, tmp_path, arvore):
        """Era o caso de `*Carol`, `*DPF` e `Moacir Andrade`: nome avisado, cartao zero."""
        resultados, descartados, _mensagem, observacoes = _analisar(
            tmp_path, arvore, CSV_SEM_CARTAO)
        assert resultados == []
        assert len(descartados) == 2
        assert len(observacoes) == 1
        assert "Zzz Ninguem" in observacoes[0]

    def test_a_mensagem_de_contrato_nao_foi_ampliada(self, tmp_path, arvore):
        """A mensagem continua falando so do que sempre falou: quantas conexoes.

        Amplia-la mudaria, por tabela, um contrato de tela que o oraculo congelado
        prende (`tests/test_characterization_matching.py`).
        """
        _resultados, _descartados, mensagem, _obs = _analisar(tmp_path, arvore, CSV_DOIS_KITS)
        assert mensagem == "2 conexões encontradas. 0 descartadas."


# ---------------------------------------------------------------------------
# O cartao continua tendo as suas proprias observacoes
# ---------------------------------------------------------------------------

class TestOCartaoNaoFicouMudo:
    """Separar nao pode esvaziar o cartao: o que e do cartao tem de continuar nele.

    Desde o bloco de endogamia da secao 2, o aviso de bloco pequeno nao fica mais
    na secao 5: ele continua no cartao, mas no bloco proprio, com os numeros. O
    que este teste guarda — o aviso NAO subir para o bloco do ARQUIVO — continua
    valendo, e agora guarda tambem que ele nao aparece duas vezes no cartao.
    """

    def test_o_segmento_fraco_continua_no_cartao_do_seu_kit(self, tmp_path, arvore):
        csv = ("Kit number,Name,cM\n"
               "A1111111,Ana Silva Souza,12.5\n")
        resultados, _descartados, _mensagem, observacoes = _analisar(tmp_path, arvore, csv)
        assert len(resultados) == 1
        cartao = resultados[0]
        assert cartao["kit"] == "A1111111"
        assert cartao["endogamia"]["evidencia_fraca"] is True
        assert "abaixo de 15 cM" in cartao["endogamia"]["mensagem"], (
            "o aviso do bloco pequeno tem de continuar no cartao daquele kit — "
            "agora no bloco da secao 2")
        assert not any("menos de 15 cM" in o for o in cartao["observations"]), (
            "o mesmo aviso nao pode aparecer tambem na secao 5")
        assert not any("menos de 15 cM" in o for o in observacoes), (
            "e nao pode ter subido para o bloco do arquivo")


# ---------------------------------------------------------------------------
# O template: o bloco do arquivo, uma vez, fora da guarda dos resultados
# ---------------------------------------------------------------------------

class TestOTextoDoTemplate:

    @staticmethod
    def _template():
        with open(TEMPLATE, encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_o_bloco_do_arquivo_existe_e_percorre_a_lista(self):
        html = self._template()
        assert "observacoes_do_arquivo" in html
        # A ANCORA NAO INCLUI `class="`: o bloco passou a levar `card` junto com a classe dele
        # quando virou `<details>` (adendo 022), e prender a ordem das classes faria o teste
        # cair por um detalhe de markup que nao muda nada na tela.
        assert "observacoes-do-arquivo" in html
        assert "Observações do arquivo" in html
        assert "{% for observacao in observacoes_do_arquivo %}" in html

    def test_o_bloco_fica_fora_da_guarda_de_dna_results(self):
        """Com zero conexoes aceitas nao ha cartao nenhum — e o aviso do arquivo e
        justamente o que explica o zero."""
        html = _sem_comentarios_jinja(self._template())
        posicao_bloco = html.index("observacoes-do-arquivo")
        posicao_guarda = html.index("{% if dna_results %}")
        assert posicao_bloco < posicao_guarda, (
            "o bloco do arquivo tem de renderizar tambem quando nao ha resultado")

    def test_o_bloco_vem_depois_da_guarda_que_o_encerra(self):
        """A guarda anterior (`aviso_de_persistencia`) nao pode engolir o bloco."""
        html = _sem_comentarios_jinja(self._template())
        bloco = html[html.index("{% if observacoes_do_arquivo %}"):]
        assert bloco.index("{% endif %}") < bloco.index("{% if dna_results %}")


# ---------------------------------------------------------------------------
# Na tela, pelo caminho de producao
# ---------------------------------------------------------------------------

NOME_GED = "0000000000000001__observacoes.ged"
NOME_CSV = "0000000000000002__observacoes.csv"


def _pagina(cliente, pasta, csv_texto):
    """O HTML do estado de resultado, com o POST real (a chave tem a forma que o
    armazenamento valida — sem ela o POST cai no estado de entrada e o teste mede
    uma pagina vazia por vacuidade)."""
    for nome, conteudo in ((NOME_GED, GED), (NOME_CSV, csv_texto)):
        with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
    return cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": NOME_GED,
        "matches_csv_filename": NOME_CSV,
        "root_name": RAIZ,
    }).get_data(as_text=True)


class TestABlocoNaTela:

    @staticmethod
    def _bloco(pagina):
        """O trecho do bloco dos avisos, do `<details>` ate' o fim dele.

        Ele e' `<details class="card observacoes-do-arquivo …">`, e nao mais um `<div>`: a
        busca por `<div class="observacoes-do-arquivo` — que existiu aqui ate' o adendo 022 —
        devolveria vazio, e os testes que dependessem dela passariam por vacuidade.
        """
        inicio = pagina.find('<details class="card observacoes-do-arquivo')
        if inicio < 0:
            return ""
        fim = pagina.find("</details>", inicio)
        return pagina[inicio:fim if fim > 0 else len(pagina)]

    @staticmethod
    def _secoes_de_observacao(pagina):
        return re.findall(r'(?s)<span class="numero">5\.</span> Observações</h5>(.*?)</div>\s*</div>',
                          pagina)

    def test_o_bloco_do_arquivo_aparece_uma_vez_com_a_frase(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        pagina = _pagina(cliente, pasta, CSV_DOIS_KITS)
        assert "Observações do arquivo" in pagina
        assert "mais de um kit" in pagina
        assert pagina.count("A1111111 com 100 cM") == 1, (
            "a frase do arquivo tem de aparecer UMA vez na pagina inteira")

    def test_a_frase_nao_se_repete_na_secao_5_de_cada_cartao(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        pagina = _pagina(cliente, pasta, CSV_DOIS_KITS)
        secoes = self._secoes_de_observacao(pagina)
        assert secoes, "a pagina tem de ter cartoes com a secao 5"
        for secao in secoes:
            assert "mais de um kit" not in secao, (
                "o aviso do arquivo nao pode voltar para dentro do cartao")

    def test_sem_cartao_o_bloco_ainda_explica_o_zero(self, cliente_de_upload):
        """A guarda `{% if dna_results %}` nao pode esconder o aviso do arquivo."""
        _app, cliente, pasta = cliente_de_upload
        pagina = _pagina(cliente, pasta, CSV_SEM_CARTAO)
        assert "Observações do arquivo" in pagina
        assert "Zzz Ninguem" in pagina


class TestOBlocoRecolhivel:
    """O bloco virou `<details>` — e nasce ABERTO, ao contrario do bloco dos descartados."""

    def test_o_titulo_e_o_summary_e_nao_um_cabecalho_acima(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        pagina = _pagina(cliente, pasta, CSV_DOIS_KITS)
        assert re.search(
            r'(?s)<summary class="sumario-do-cartao">\s*<div class="card-header">\s*'
            r'<h5[^>]*>Observações do arquivo</h5>',
            pagina), (
            "o titulo do bloco nao virou o `summary`: sobra um cabecalho acima de um `details`"
        )

    def test_o_bloco_nasce_aberto(self, cliente_de_upload):
        """Ele carrega AVISO, e nao detalhe.

        O bloco dos descartados pode comecar fechado porque e' o rodape da analise. Este diz
        coisas que mudam a leitura do resultado — nome em mais de um kit, CSV sem coluna de
        kit, raiz ambigua —, e o adendo 017 o tirou de dentro dos cartoes justamente para ele
        ser LIDO. Escondê-lo atras de um clique desfaria aquilo.
        """
        _app, cliente, pasta = cliente_de_upload
        pagina = _pagina(cliente, pasta, CSV_DOIS_KITS)
        abertura = re.search(r'<details class="card observacoes-do-arquivo[^"]*"([^>]*)>', pagina)
        assert abertura, "o bloco dos avisos nao esta na tela"
        assert "open" in abertura.group(1), (
            "o bloco dos avisos nasceu FECHADO: aviso escondido atras de um clique"
        )

    def test_os_avisos_ficam_dentro_do_bloco(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        pagina = _pagina(cliente, pasta, CSV_DOIS_KITS)
        bloco = self._bloco(pagina)
        assert bloco, f"o bloco dos avisos nao esta na tela: {self._bloco(pagina)!r}"
        assert "mais de um kit" in bloco, (
            "o aviso saiu de dentro do bloco recolhivel"
        )

    def test_o_bloco_nao_e_alvo_de_ancora(self, cliente_de_upload):
        """Ele nao tem `id`: nenhum link manda o operador para ele, e ele nao abre por hash."""
        _app, cliente, pasta = cliente_de_upload
        pagina = _pagina(cliente, pasta, CSV_DOIS_KITS)
        assert re.search(r'<details class="card observacoes-do-arquivo[^"]*" id=', pagina) is None

    @staticmethod
    def _bloco(pagina):
        return TestABlocoNaTela._bloco(pagina)
