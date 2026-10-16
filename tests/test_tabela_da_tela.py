"""T035 (feature `011-escolher-arquivo-da-lista`): a lista virou TABELA com colunas.

## O que mudou, e por que isto merece teste proprio

Ate a `T034`, cada arquivo era um `<li>` com o nome de um lado e os botoes do outro: o
tamanho, a data e a contagem do grupo apareciam como texto solto, sem rotulo. A `T035`
transformou isso numa tabela com linha de cabecalho, e a mudanca **nao e cosmetica**:

- o nome exibido NAO e unico — ha tres itens com o rotulo `Arvore Unificada Oficial V1 2`
  na pasta real —, e a tabela passa a dar ENDERECO para a data e o tamanho, que sao o que
  distingue um item do outro (`D-09`);
- a contagem do grupo (`RN-01`) deixa de ser um badge que so aparece quando e maior que um
  e vira uma COLUNA, com o numero sempre visivel;
- a marca de indisponivel (`RN-11`, `D-11`) vira uma coluna de situacao, com o visto
  verde do caso bom e o motivo escrito no caso ruim.

## O que a tabela deliberadamente NAO tem

A tela de referencia que originou o pedido tem uma coluna "Numero" com link. Aqui ela nao
existe: esta aplicacao nao tem identificador publico de arvore, e a **chave de conteudo nao
pode ocupar esse lugar** — ela e exatamente o que o `D-09` proibe mostrar. O teste
`test_a_tabela_nao_exibe_a_chave` prende isso.

## Por que o caso da tela vazia esta aqui

A tabela inteira vive DENTRO do `{% if %}` da lista, entao a tela sem arquivo nenhum fica
byte a byte igual a de antes — e e por isso que o `SHA_DA_TELA` de
`test_icone_de_atalho.py` continua valendo sem atualizacao. Isso nao e sorte: e a razao de
a tabela ter sido posta dentro do ramo, e o teste declara a decisao.
"""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import datetime

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from reporting.lista_de_arquivos import formatar_data_br  # noqa: E402

GEDCOM = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n0 TRLR\n"
)
CHAVE_A = "080e7943572d2652"
CHAVE_B = "c84fd7fb4201b69f"

COLUNAS = ["Nome", "Situação", "Arquivos", "Tamanho", "Enviado em", "Gerenciar"]


def _guardar(pasta: str, nome: str, conteudo: bytes = GEDCOM.encode("utf-8")) -> str:
    caminho = os.path.join(pasta, nome)
    with open(caminho, "wb") as fh:
        fh.write(conteudo)
    return caminho


def _corpo(cliente) -> str:
    return cliente.get("/").get_data(as_text=True)


def _visivel(corpo: str) -> str:
    """So o texto entre tags: a chave circula em campo oculto, e isso e correto."""
    return " ".join(re.findall(r">([^<]+)<", corpo))


class TestTabelaComColunas:
    """O pedido do operador: as informacoes separadas em colunas, como na tela de referencia."""

    def test_a_lista_e_uma_tabela_com_linha_de_cabecalho(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged")

        corpo = _corpo(cliente)

        assert "<table" in corpo, "a lista continua sem ser uma tabela"
        assert "<thead" in corpo, "a tabela nao tem linha de cabecalho"
        for coluna in COLUNAS:
            assert f">{coluna}<" in corpo, f"a coluna {coluna!r} nao esta no cabecalho"

    def test_cada_item_ocupa_uma_linha(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged")
        _guardar(pasta, f"{CHAVE_B}__outra.ged")

        corpo = _corpo(cliente)

        assert len(re.findall(r"<tr>", corpo)) == 3, (
            "esperado: 1 linha de cabecalho + 2 itens. Um item por linha e o que a tabela promete"
        )

    def test_a_coluna_situacao_marca_o_disponivel_com_o_visto(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged")

        corpo = _corpo(cliente)

        assert "&#10003;" in corpo, "o item disponivel nao ganhou o visto na coluna de situacao"
        assert "&#9888;" not in corpo, "apareceu marca de alerta para um item que funciona"

    def test_a_coluna_situacao_traz_o_motivo_do_indisponivel(self, cliente_de_upload):
        """`RN-11`: o indisponivel continua na tabela, com o motivo escrito."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, "arvore_sem_chave.ged")

        corpo = _corpo(cliente)

        assert "&#9888;" in corpo, "o indisponivel nao ganhou a marca de alerta"
        assert "sem chave de conteúdo no nome" in corpo, (
            "a coluna de situacao nao diz POR QUE o item nao serve"
        )

    def test_a_coluna_arquivos_traz_a_contagem_do_grupo(self, cliente_de_upload):
        """`RN-01`/`RN-02`: dois arquivos do mesmo conteudo sao UM item, e a coluna diz quantos."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged")
        _guardar(pasta, f"{CHAVE_A}__arvore_repetida.ged")

        corpo = _corpo(cliente)
        linhas = re.findall(r"<tr>(.*?)</tr>", corpo, re.S)

        assert len(linhas) == 2, "os dois arquivos do mesmo conteudo tem de virar UMA linha"
        celulas = re.findall(r"<td[^>]*>(.*?)</td>", linhas[1], re.S)
        assert len(celulas) == len(COLUNAS), "a linha nao tem uma celula por coluna"
        assert celulas[2].strip() == "2", f"a coluna Arquivos trouxe {celulas[2].strip()!r}"

    def test_a_coluna_enviado_em_traz_a_data_do_arquivo(self, cliente_de_upload):
        """A data vem do `os.stat` da pasta, e a coluna a exibe no formato brasileiro."""
        _app, cliente, pasta = cliente_de_upload
        caminho = _guardar(pasta, f"{CHAVE_A}__arvore.ged")
        quando = datetime(2024, 3, 15, 12, 0).timestamp()
        os.utime(caminho, (quando, quando))

        corpo = _corpo(cliente)

        assert "15/03/2024" in corpo, "a data do arquivo nao chegou a coluna 'Enviado em'"

    def test_a_coluna_gerenciar_tem_os_dois_botoes(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged")

        corpo = _corpo(cliente)

        assert 'class="btn btn-sm btn-success">Abrir</button>' in corpo
        assert 'class="btn btn-sm btn-danger">Apagar</button>' in corpo

    def test_a_tabela_nao_exibe_a_chave_de_conteudo(self, cliente_de_upload):
        """`D-09`: a coluna "Numero" da tela de referencia NAO pode ser a chave."""
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged")

        corpo = _corpo(cliente)
        visivel = _visivel(corpo)

        assert "arvore" in visivel, "pre-condicao: a tabela tem de estar no ar para medir algo"
        assert CHAVE_A not in visivel, "a chave de conteudo virou TEXTO na tabela"


    def test_a_coluna_tamanho_traz_o_valor_na_unidade_certa(self, cliente_de_upload):
        """`T020`: o item mostra o TAMANHO, e nao so o rotulo da coluna.

        **Atualizado em 2026-10-16, a pedido do operador.** A coluna mostrava o total em bytes
        (`1.200 bytes`) e passou a mostrar a unidade que se le de relance — `8,54 MB` em vez de
        `8.955.472 bytes`.

        O arquivo tem exatamente **1 MB** (1.048.576 bytes), o primeiro valor da faixa de MB,
        entao o literal esperado nao depende do proprio filtro para saber o que esperar.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged", b"x" * (1024 * 1024))

        assert "1 MB" in _corpo(cliente), "a coluna Tamanho nao trouxe o valor em MB"

    def test_arquivo_abaixo_de_1_mb_sai_em_kb(self, cliente_de_upload):
        """O corte em 1 MB, medido na tela e nao so' na funcao.

        Sem o corte, os CSVs deste acervo — 56.307 bytes — apareceriam como `0,05 MB`, que
        ninguem le. Com ele, a mesma faixa sai em KB.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged", b"x" * (55 * 1024))

        assert "55 KB" in _corpo(cliente), "arquivo abaixo de 1 MB nao saiu em KB"

    def test_o_numero_exato_de_bytes_continua_na_celula(self, cliente_de_upload):
        """O `title` da celula — o numero exato que a unidade curta nao mostra.

        `1,17 KB` nao diz quantos bytes o arquivo tem, e duas versoes do mesmo CSV podem diferir
        por poucos bytes. O `title` e' o que mantem o dado exato a um hover de distancia.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged", b"x" * 1200)

        corpo = _corpo(cliente)

        assert "1,17 KB" in corpo, "pre-condicao: 1200 bytes dao 1,17 KB"
        assert 'title="1.200 bytes"' in corpo, (
            "o numero exato em bytes saiu da celula: nao sobra onde ler o tamanho real do arquivo"
        )

    def test_a_aba_de_dna_tem_as_mesmas_colunas(self, cliente_de_upload):
        """`T020` diz "as duas listas", e o teste so olhava a de arvore.

        Lacuna medida em 2026-10-10: da aba de DNA so se assertava o NOME do relatorio. As
        colunas de situacao, tamanho, data e gerenciar dela nao tinham prova.

        O arquivo de ARVORE e necessario ALÉM do CSV, e a primeira versao deste teste o esqueceu:
        cada tabela vive dentro do ramo da sua lista, entao sem arvore na pasta a aba de arvore
        nao desenha tabela nenhuma — e a contagem de tabelas media isso, e nao o cabecalho.
        """
        _app, cliente, pasta = cliente_de_upload
        _guardar(pasta, f"{CHAVE_A}__arvore.ged")
        _guardar(pasta, f"{CHAVE_B}__relatorio.csv", b"nome,cm\nMaria,100\n")

        corpo = _corpo(cliente)
        tabelas = re.findall(r"(?s)<table.*?</table>", corpo)

        assert len(tabelas) == 2, "esperava uma tabela por aba"
        cabecalho = re.findall(r"<th[^>]*>([^<]*)</th>", tabelas[1])
        assert cabecalho == COLUNAS, f"o cabecalho da aba de DNA e {cabecalho}"


class TestTelaVazia:
    """A decisao de a tabela viver dentro do `{% if %}` da lista."""

    def test_a_tela_sem_arquivo_nao_tem_tabela(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        corpo = _corpo(cliente)

        assert "<table" not in corpo, (
            "a tabela aparece sem nenhum arquivo: ela tem de viver dentro do ramo da lista"
        )
        assert "Nenhuma árvore armazenada ainda" in corpo, "a orientacao de envio sumiu"


class TestFormatarDataBr:
    """`formatar_data_br`: a conversao da coluna, e o guarda que evita `500` na tela."""

    def test_converte_um_instante_local(self):
        quando = datetime(2024, 3, 15, 12, 0).timestamp()

        assert formatar_data_br(quando) == "15/03/2024"

    def test_o_formato_e_sempre_dois_dois_quatro(self):
        assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", formatar_data_br(time.time()))

    @pytest.mark.parametrize("valor", [float("nan"), float("inf"), 1e30, -1e30])
    def test_instante_impossivel_devolve_celula_vazia_e_nao_excecao(self, valor):
        """Uma celula de data nao pode derrubar a tela de entrada inteira com `500`."""
        assert formatar_data_br(valor) == ""


class TestOFormatoDoTamanho:
    """`formatar_tamanho`: a unidade e a precisao, medidas nas BORDAS.

    Os testes de rota acima provam que a coluna usa o filtro; estes provam o que o filtro faz nos
    pontos em que ele decide — o corte de 1 MB e o arredondamento de duas casas. Sao testes de
    UNIDADE de proposito: um caso de fronteira de um byte nao se monta pela tela sem escrever um
    arquivo de 1 MB menos um byte.
    """

    @pytest.mark.parametrize("quantidade,esperado", [
        (0, "0 KB"),
        (512, "0,5 KB"),
        (1024, "1 KB"),
        (1200, "1,17 KB"),
        (55 * 1024, "55 KB"),
        # O byte ANTES do corte: arredonda para 1024 KB, e nao para 1 MB. E' a consequencia
        # honesta de um corte exato, e nenhum arquivo real cai nesta largura de um byte.
        (1024 * 1024 - 1, "1024 KB"),
        (1024 * 1024, "1 MB"),
        (1024 * 1024 + 1, "1 MB"),
        (8_955_472, "8,54 MB"),
        (100 * 1024 * 1024, "100 MB"),
    ])
    def test_a_unidade_e_a_precisao(self, quantidade, esperado):
        from utils.number_format import formatar_tamanho

        assert formatar_tamanho(quantidade) == esperado

    def test_zeros_a_direita_saem(self):
        """`100 MB`, e nao `100,00 MB` — a mesma politica de `formatar_cm`."""
        from utils.number_format import formatar_tamanho

        assert formatar_tamanho(100 * 1024 * 1024) == "100 MB"
        assert formatar_tamanho(1024) == "1 KB"

    @pytest.mark.parametrize("valor", [None, "", "nao e numero"])
    def test_valor_ausente_vira_travessao_e_nao_excecao(self, valor):
        """Ausencia de dado nao e' dado zero: vira travessao, como em `formatar_inteiro`."""
        from utils.number_format import formatar_tamanho

        assert formatar_tamanho(valor) == "—"

    def test_a_base_e_1024_e_nao_1000(self):
        """A mesma base do teto de upload (`TETO_DE_UPLOAD_EM_MB`), para nao haver dois numeros
        para o mesmo arquivo."""
        from utils.number_format import formatar_tamanho

        assert formatar_tamanho(1024 * 1024) == "1 MB"
        assert formatar_tamanho(1_000_000) == "976,56 KB"
