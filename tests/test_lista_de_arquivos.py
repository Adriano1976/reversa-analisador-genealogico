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
    from reporting.lista_de_arquivos import rotulo_limpo as _rotulo_limpo
except ImportError as _erro:  # pragma: no cover - o ramo verde e o que roda depois da T015
    _funcao_pura = None
    _rotulo_limpo = None
    _FALTA = str(_erro)


def itens_da_aba(*args, **kwargs):
    """Delegacao para a funcao pura, com falha explicita enquanto a T015 nao chega."""
    if _funcao_pura is None:
        pytest.fail("a funcao pura ainda nao existe (T015): " + _FALTA)
    return _funcao_pura(*args, **kwargs)


def rotulo_limpo(*args, **kwargs):
    """Idem, para a formatacao do rotulo (`RN-13`)."""
    if _rotulo_limpo is None:
        pytest.fail("a formatacao do rotulo ainda nao existe (RN-13): " + _FALTA)
    return _rotulo_limpo(*args, **kwargs)


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
        assert itens[0].nome_exibido == "planilha csv"

    def test_arquivo_sem_chave_vira_item_proprio_e_marcado(self):
        """`RN-10`: sem chave no nome, item proprio, nunca agrupado."""
        itens = itens_da_aba(
            [e("arvore_sem_chave.ged"), e(f"{CHAVE_A}__arvore.ged")], ".ged"
        )

        assert len(itens) == 2, "o sem chave nao pode ser agrupado com ninguem"
        sem_chave = [i for i in itens if i.chave is None]
        assert len(sem_chave) == 1
        assert sem_chave[0].nome_exibido == "arvore sem chave"

    def test_item_com_chave_ascii_e_disponivel(self):
        itens = itens_da_aba([e(f"{CHAVE_A}__arvore.ged")], ".ged")

        assert itens[0].disponivel is True
        assert itens[0].motivo_indisponivel is None

    def test_item_sem_chave_e_indisponivel_com_o_motivo(self):
        """`D-11`: a referencia exige os 16 hexadecimais, entao o item nao pode ser usado."""
        itens = itens_da_aba([e("arvore_sem_chave.ged")], ".ged")

        assert itens[0].disponivel is False
        assert "chave" in (itens[0].motivo_indisponivel or "").lower()

    def test_item_com_acento_no_nome_visivel_E_DISPONIVEL(self):
        """`RN-20`, correcao de 2026-10-10: acento no nome visivel deixou de tornar o arquivo inalcancavel.

        Este teste prendia o CONTRARIO ate hoje, e prendia um defeito: o gravador preserva acento
        porque e requisito (`RF-06`), e o resolvedor exigia um alfabeto que nao o admite. O arquivo
        `94e2402671702cac__Famílias_Sergipanas.csv` existia na pasta do operador e a tela dizia
        "nao existe mais" — falso. Ver o `BUG-20261009-6RKP`.
        """
        itens = itens_da_aba([e(f"{CHAVE_C}__Famílias_Sergipanas.csv")], ".csv")

        assert itens[0].disponivel is True, (
            "o acento voltou a tornar o arquivo inalcancavel: o resolvedor precisa aceitar o que o "
            "gravador produz (`RF-06`, `RN-20`)"
        )
        assert itens[0].motivo_indisponivel is None

    def test_item_com_espaco_no_nome_visivel_E_DISPONIVEL(self):
        """O espaco cai no mesmo caso do acento, e pela mesma razao (`RN-20`)."""
        itens = itens_da_aba([e("b70889273a505a5d__planilha de dna.xlsx")], ".xlsx")

        assert itens[0].disponivel is True

    def test_nenhum_item_e_escondido_por_estar_indisponivel(self):
        """`D-08` + `RN-11`: o item indisponivel CONTINUA na lista. Nao se esconde dado do operador.

        Correcao de 2026-10-10: a fixture usava um arquivo COM chave e com acento como caso
        indisponivel. Depois da `RN-20` ele passou a ser alcancavel — e o caso indisponivel que
        resta e o arquivo **sem chave**, que a referencia nao alcanca de jeito nenhum. Sao usados
        DOIS deles para a contagem continuar exercitando "mais de um item marcado", e nao um so.
        """
        itens = itens_da_aba(
            [e("arvore_sem_chave.ged"), e("outra_sem_chave.ged"),
             e(f"{CHAVE_A}__arvore.ged")],
            ".ged",
        )

        assert len(itens) == 3, "os dois indisponiveis tem de continuar na lista"
        assert sum(1 for i in itens if not i.disponivel) == 2


class TestNomeExibido:
    """`D-09`: a chave vazada nao vai para a tela, e o nome exibido nunca e o nome armazenado."""

    def test_nome_armazenado_nunca_e_o_exibido(self):
        itens = itens_da_aba([e(f"{CHAVE_A}__arvore.ged")], ".ged")

        assert itens[0].nome_exibido == "arvore"
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
        assert itens[0].nome_exibido == "arvore", (
            "o nome exibido nao pode carregar a chave, nem a do grupo nem a vazada"
        )

    def test_grupo_com_nomes_diferentes_exibe_a_contagem(self):
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__nome_um.ged"), e(f"{CHAVE_A}__nome_dois.ged")], ".ged"
        )

        assert itens[0].quantidade == 2


class TestFormatoDoRotulo:
    """`RN-13`: o rotulo sai sem extensao e sem simbolos -- e SO o rotulo.

    ## Por que esta classe existe separada

    A formatacao e a ultima coisa que acontece com o nome, e ela e a unica parte da
    apresentacao que mexe no que o operador LE sem mexer em nada do que a aplicacao
    DECIDE. Os dois ultimos testes desta classe prendem exatamente essa fronteira: a
    extensao desaparece da tela e continua decidindo a aba, e o alcance por referencia
    nao melhora nem piora porque o rotulo ficou bonito.
    """

    def test_a_extensao_sai_do_rotulo(self):
        assert rotulo_limpo("arvore.ged") == "arvore"

    def test_os_simbolos_viram_espaco(self):
        """Caso MEDIDO: e o nome real de um arquivo da pasta do operador."""
        assert rotulo_limpo("Backup-Arvore-Sandro-12-11-2024.ged") == (
            "Backup Arvore Sandro 12 11 2024"
        )

    def test_o_acento_e_preservado(self):
        """O `\\w` de Python 3 e sensivel a acento: a limpeza nao pode virar transliteracao."""
        assert rotulo_limpo("Famílias_Sergipanas.csv") == "Famílias Sergipanas"

    def test_so_a_ultima_extensao_sai(self):
        """`planilha.csv.ged` -> `planilha csv`: o `.csv` do meio e o unico sinal do tipo real.

        Apagar tudo o que parece extensao devolveria `planilha`, e o operador perderia a
        pista de que aquele `.ged` e, no conteudo, um relatorio de DNA -- que e justamente
        o que `D-08` decidiu nao esconder.
        """
        assert rotulo_limpo("planilha.csv.ged") == "planilha csv"

    def test_nome_sem_ponto_nao_e_comido(self):
        assert rotulo_limpo("sem_ponto") == "sem ponto"

    def test_nome_apenas_de_extensao_nao_vira_rotulo_vazio(self):
        """Sem raiz antes do ponto, nao ha extensao a retirar.

        A implementacao ingenua (`corta no ultimo ponto`) devolveria string VAZIA aqui, e
        a tela mostraria uma linha em branco -- pior do que um rotulo feio.
        """
        assert rotulo_limpo(".ged") == "ged"
        assert rotulo_limpo(".ged") != ""

    def test_rotulos_de_arquivos_distintos_continuam_distintos(self):
        """Dois `.ged` diferentes nao podem colidir so porque a extensao saiu."""
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__arvore.ged", quando=9_000.0),
             e(f"{CHAVE_C}__arvore.csv.ged", quando=1_000.0)],
            ".ged",
        )

        assert [i.nome_exibido for i in itens] == ["arvore", "arvore csv"]

    def test_a_aba_continua_decidida_pela_extensao_que_o_rotulo_esconde(self):
        """A fronteira: a extensao sai da TELA e continua decidindo a ABA.

        Se a formatacao tivesse sido aplicada antes da particao, o `Famílias_Sergipanas.csv`
        nao entraria em aba nenhuma -- e este teste falharia.
        """
        entradas = [e(f"{CHAVE_C}__Famílias_Sergipanas.csv"),
                    e(f"{CHAVE_A}__arvore.ged")]

        relatorios = itens_da_aba(entradas, ".csv")
        arvores = itens_da_aba(entradas, ".ged")

        assert [i.nome_exibido for i in relatorios] == ["Famílias Sergipanas"]
        assert [i.nome_exibido for i in arvores] == ["arvore"]

    def test_o_rotulo_bonito_nao_melhora_o_alcance_do_arquivo(self):
        """`D-11`: o rotulo e cosmetico e nao concede alcance nenhum.

        Correcao de 2026-10-10 (`RN-20`): este teste usava um arquivo COM chave e com acento, que
        era inalcancavel — e o acento deixou de bloquear. O caso que sustenta a assercao passou a
        ser o arquivo **sem chave**: o rotulo dele tambem fica bonito depois da formatacao, e ele
        continua indisponivel, porque o que falta nao e beleza, e a chave.
        """
        itens = itens_da_aba([e("Famílias_Sergipanas.csv")], ".csv")

        assert itens[0].nome_exibido == "Famílias Sergipanas"
        assert itens[0].disponivel is False
        assert itens[0].motivo_indisponivel is not None

    def test_a_referencia_entregue_ao_formulario_continua_sendo_o_nome_armazenado(self):
        """A formatacao nao pode tocar o que viaja entre requisicoes."""
        itens = itens_da_aba([e(f"{CHAVE_A}__Backup-Arvore-12-11-2024.ged")], ".ged")

        assert itens[0].nome_exibido == "Backup Arvore 12 11 2024"
        assert itens[0].nome_armazenado == f"{CHAVE_A}__Backup-Arvore-12-11-2024.ged"


class TestOrdemEDatas:
    """`D-09`: ordem por data decrescente, porque o nome exibido nao e unico."""

    def test_ordem_por_data_decrescente(self):
        itens = itens_da_aba(
            [e(f"{CHAVE_A}__antiga.ged", quando=1_000.0),
             e(f"{CHAVE_B}__recente.ged", quando=9_000.0),
             e(f"{CHAVE_C}__meio.ged", quando=5_000.0)],
            ".ged",
        )

        assert [i.nome_exibido for i in itens] == ["recente", "meio", "antiga"]

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
