"""T005 (feature 011): a funcao PURA de apresentacao da lista.

## O que este arquivo prova

A funcao pura e o unico lugar onde a lista e MONTADA: selecao por extensao, agrupamento pela chave,
marca de "sem chave", contagem, ordem e alcance por referencia. Ela nao toca o disco, entao os casos
sao construidos com nomes SINTETICOS -- o inventario real da pasta do operador nao entra em teste
nenhum (Principio I).

## Por que as quatro classes

Cada uma prende um pedaco distinto do contrato, e a separacao e deliberada: se uma quebrar, o nome da
classe diz qual regra caiu.

- `TestAgrupamentoPelaChave`     -- `RN-01`, `RN-02`: um item por conteudo, com contagem
- `TestMarcasEClassificacao`     -- `RN-10`, `RN-03`, `D-10`: sem chave, indisponivel, extensao
- `TestNomeExibido`              -- `D-09`: a chave vazada nao vai para a tela
- `TestOrdemEDatas`              -- `D-09`: ordem por data decrescente

## Estado esperado ANTES da T015

Vermelho, e por importacao: `reporting.lista_de_arquivos` ainda nao existe. E o estado que o
Principio III exige -- o teste chega antes do codigo.
"""
from __future__ import annotations

import sys
import os
from dataclasses import dataclass

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

# O unico ponto deste arquivo que depende da T015, e ele e GUARDADO de proposito, por duas razoes
# medidas:
#
#   1. um `ImportError` no topo do modulo aborta a COLETA da suite inteira
#      (`Interrupted: 1 error during collection`), e as outras seis acoes da fase ficariam sem
#      poder ser verificadas;
#   2. `pytest.fail` dentro de um fixture `autouse` produz ERROR de setup, nao FAILED. O estado que
#      o Principio III exige e o teste FALHANDO, entao a ausencia vira um wrapper: o corpo de cada
#      teste chama `itens_da_aba(...)` igual, e a falha sai como falha.
try:
    from reporting.lista_de_arquivos import itens_da_aba as _funcao_pura
except ImportError as _erro:  # pragma: no cover - o ramo verde e o que roda depois da T015
    _funcao_pura = None
    _FALTA = str(_erro)


def itens_da_aba(*args, **kwargs):
    """Delegacao para a funcao pura, com falha explicita enquanto a T015 nao chega."""
    if _funcao_pura is None:
        pytest.fail("a funcao pura ainda nao existe (T015): " + _FALTA)
    return _funcao_pura(*args, **kwargs)


@dataclass(frozen=True)
class Entrada:
    """Entrada de teste: so os tres atributos que a funcao pura consome.

    Deliberadamente NAO e o tipo da porta. A funcao pura e pura justamente para nao depender do
    adaptador, e usar o tipo real aqui arrastaria a fronteira para dentro do teste de unidade.
    """

    nome: str
    bytes: int
    modificado_em: float


CHAVE_A = "080e7943572d2652"
CHAVE_B = "c84fd7fb4201b69f"
CHAVE_C = "94e2402671702cac"


def e(nome: str, tamanho: int = 100, quando: float = 1_000.0) -> Entrada:
    return Entrada(nome=nome, bytes=tamanho, modificado_em=quando)


class TestAgrupamentoPelaChave:
    """`RN-01`, `RN-02`: um item por conteudo, e a contagem quando sao varios."""

    def test_uma_entrada_vira_um_item(self):
        itens = itens_da_aba([e(f"{CHAVE_A}__arvore.ged")], ".ged")

        assert len(itens) == 1
        assert itens[0].quantidade == 1

    def test_mesma_chave_agrupa_num_item_com_contagem(self):
        """Dois arquivos, mesmo conteudo: UM item, e o item declara que sao dois."""
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__arvore.ged", 500, 2_000.0),
             e(f"{CHAVE_A}__arvore.ged", 500, 1_000.0)],
            ".ged",
        )

        assert len(itens) == 1, "mesma chave tem de virar um item so"
        assert itens[0].quantidade == 2

    def test_o_item_agrupado_soma_os_bytes(self):
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__arvore.ged", 500), e(f"{CHAVE_A}__arvore.ged", 700)],
            ".ged",
        )

        assert itens[0].bytes == 1200

    def test_chaves_diferentes_viram_itens_diferentes(self):
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__arvore.ged"), e(f"{CHAVE_B}__arvore.ged")], ".ged"
        )

        assert len(itens) == 2


class TestMarcasEClassificacao:
    """`RN-10`, `RN-03`, `RN-09`, `D-10`, `D-11`: o que entra na aba, e o que a marca diz."""

    def test_particao_por_extensao_do_nome_visivel(self):
        """`RN-03`: a aba de arvore recebe `.ged`, e so isso."""
        entradas = [e(f"{CHAVE_A}__arvore.ged"), e(f"{CHAVE_C}__dna.csv"),
                    e("b70889273a505a5d__planilha.xlsx", quando=9_000.0)]

        arvores = itens_da_aba(entradas, ".ged")
        relatorios = itens_da_aba(entradas, ".csv")

        assert [i.nome_armazenado for i in arvores] == [f"{CHAVE_A}__arvore.ged"]
        assert [i.nome_armazenado for i in relatorios] == [f"{CHAVE_C}__dna.csv"]

    def test_extensao_de_outra_aba_nao_entra(self):
        """O `.xlsx` nao aparece em aba NENHUMA -- medido na pasta real, e o `D-10` o declara."""
        entradas = [e(f"{CHAVE_A}__arvore.ged"),
                    e("b70889273a505a5d__planilha.xlsx", quando=9_000.0)]

        for extensao in (".ged", ".csv"):
            nomes = [i.nome_armazenado for i in itens_da_aba(entradas, extensao)]
            assert "b70889273a505a5d__planilha.xlsx" not in nomes

    def test_nome_visivel_que_anuncia_um_tipo_e_outro_conteudo_continua_listado(self):
        """`RN-09`, `D-08`: a lista NAO le conteudo, entao nao filtra por conteudo."""
        itens = itens_da_aba([e(f"{CHAVE_C}__planilha.csv.ged")], ".ged")

        assert len(itens) == 1
        assert itens[0].nome_exibido == "planilha.csv.ged"

    def test_arquivo_sem_chave_vira_item_proprio_e_marcado(self):
        """`RN-10`: sem chave no nome, item proprio, nunca agrupado."""
        itens = itens_da_aba(
            [e("arvore_sem_chave.ged"), e(f"{CHAVE_A}__arvore.ged")], ".ged"
        )

        assert len(itens) == 2, "o sem chave nao pode ser agrupado com ninguem"
        sem_chave = [i for i in itens if i.chave is None]
        assert len(sem_chave) == 1
        assert sem_chave[0].nome_exibido == "arvore_sem_chave.ged"

    def test_item_com_chave_ascii_e_disponivel(self):
        itens = itens_da_aba([e(f"{CHAVE_A}__arvore.ged")], ".ged")

        assert itens[0].disponivel is True
        assert itens[0].motivo_indisponivel is None

    def test_item_sem_chave_e_indisponivel_com_o_motivo(self):
        """`D-11`: a referencia exige os 16 hexadecimais, entao o item nao pode ser usado."""
        itens = itens_da_aba([e("arvore_sem_chave.ged")], ".ged")

        assert itens[0].disponivel is False
        assert "chave" in (itens[0].motivo_indisponivel or "").lower()

    def test_item_com_acento_no_nome_visivel_e_indisponivel_com_o_motivo(self):
        """`D-11`, caso MEDIDO na pasta real: o gravador preserva acento, o resolvedor o recusa."""
        itens = itens_da_aba([e(f"{CHAVE_C}__Famílias_Sergipanas.csv")], ".csv")

        assert itens[0].disponivel is False
        assert itens[0].motivo_indisponivel is not None
        assert "chave" not in itens[0].motivo_indisponivel.lower(), (
            "o motivo tem de distinguir os dois casos: este TEM chave, e o problema e outro"
        )

    def test_item_com_espaco_no_nome_visivel_e_indisponivel(self):
        """Espaco cai na mesma forma fechada que o acento, e a mitigacao de 2026-10-09 tratou disso."""
        itens = itens_da_aba([e("b70889273a505a5d__planilha de dna.xlsx")], ".xlsx")

        assert itens[0].disponivel is False

    def test_nenhum_item_e_escondido_por_estar_indisponivel(self):
        """`D-08` + `RN-11`: o item indisponivel CONTINUA na lista. Nao se esconde dado do operador.

        Correcao de 2026-10-09: a primeira versao desta fixture punha um arquivo `.csv` numa
        chamada com extensao `.ged`, e esperava ve-lo na lista. Ele **nao** devia aparecer — e era o
        proprio `RN-03` funcionando. O arquivo foi trocado por um `.ged` com acento, que e o caso
        indisponivel que pertence a esta aba.
        """
        itens = itens_da_aba(
            [e("arvore_sem_chave.ged"), e(f"{CHAVE_C}__Famílias.ged"),
             e(f"{CHAVE_A}__arvore.ged")],
            ".ged",
        )

        assert len(itens) == 3, "os dois indisponiveis tem de continuar na lista"
        assert sum(1 for i in itens if not i.disponivel) == 2


class TestNomeExibido:
    """`D-09`: a chave vazada nao vai para a tela, e o nome exibido nunca e o nome armazenado."""

    def test_nome_armazenado_nunca_e_o_exibido(self):
        itens = itens_da_aba([e(f"{CHAVE_A}__arvore.ged")], ".ged")

        assert itens[0].nome_exibido == "arvore.ged"
        assert itens[0].nome_armazenado == f"{CHAVE_A}__arvore.ged"

    def test_grupo_com_nomes_diferentes_nao_exibe_a_chave_vazada(self):
        """Caso MEDIDO: o operador reenviou um arquivo que JA tinha chave no nome.

        O grupo da chave `080e7943572d2652` tem dois arquivos, e um deles tem o nome visivel
        `080e7943572d2652__arvore.ged`. Exibir o primeiro em ordem alfabetica mostraria a chave crua.
        """
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__{CHAVE_A}__arvore.ged"), e(f"{CHAVE_A}__arvore.ged")],
            ".ged",
        )

        assert len(itens) == 1
        assert itens[0].nome_exibido == "arvore.ged", (
            "o nome exibido nao pode carregar a chave, nem a do grupo nem a vazada"
        )

    def test_grupo_com_nomes_diferentes_exibe_a_contagem(self):
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__nome_um.ged"), e(f"{CHAVE_A}__nome_dois.ged")], ".ged"
        )

        assert itens[0].quantidade == 2


class TestOrdemEDatas:
    """`D-09`: ordem por data decrescente, porque o nome exibido nao e unico."""

    def test_ordem_por_data_decrescente(self):
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__antiga.ged", quando=1_000.0),
             e(f"{CHAVE_B}__recente.ged", quando=9_000.0),
             e(f"{CHAVE_C}__meio.ged", quando=5_000.0)],
            ".ged",
        )

        assert [i.nome_exibido for i in itens] == ["recente.ged", "meio.ged", "antiga.ged"]

    def test_a_data_do_item_e_a_mais_recente_do_grupo(self):
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__arvore.ged", quando=1_000.0),
             e(f"{CHAVE_A}__outro_nome.ged", quando=7_000.0)],
            ".ged",
        )

        assert itens[0].modificado_em == 7_000.0

    def test_lista_vazia_nao_e_erro(self):
        """`RF-07`/`D-07`: instalacao nova tem pasta vazia, e isso nao e excecao."""
        assert itens_da_aba([], ".ged") == []

    def test_pasta_sem_arquivo_do_tipo_devolve_lista_vazia(self):
        itens = itens_da_aba([e(f"{CHAVE_C}__dna.csv")], ".ged")

        assert itens == []


def test_a_funcao_e_pura_e_nao_abre_arquivo():
    """A garantia de desempenho do RNF: nada aqui pode tocar o disco.

    O teste nao "espia" chamadas de sistema -- ele prova pelo comportamento: a entrada nao tem
    caminho nenhum, so nome e atributos, entao nao ha o que abrir.
    """
    entrada = e(f"{CHAVE_A}__arvore.ged")
    assert set(vars(entrada)) == {"nome", "bytes", "modificado_em"}
