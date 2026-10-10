"""Tabela de traducao de erro de dominio (`T024`; moldura x motivo, `T029`/`A002`).

Dois grupos, com perguntas diferentes:

- **Grupo A (`T024`)** pergunta se a tabela de `application/traducao.py` reproduz
  o mapa MEDIDO antes da refatoracao (19 casos, zero divergencia). Ele exercita
  `traduzir` DIRETAMENTE, sem subir requisicao HTTP nenhuma: subir uma aplicacao
  para perguntar "qual e o texto deste erro" seria medir o Flask, e nao a tabela.
  Aqui importa a MENSAGEM e o STATUS, um a um.

- **Grupo B (`T029`, achado `A002` da auditoria)** pergunta ONDE mora a moldura
  literal. A `GedcomNaoSuportado` carrega so o motivo devolvido por
  `utils/validate.py`; o texto que o operador le (`"Arquivo nao reconhecido como
  GEDCOM: <motivo>."`) e montado pela traducao. Sem esse teste a moldura pode
  voltar para dentro da excecao sem nenhum sinal, e a fronteira de aplicacao
  perde a razao de existir: texto de tela dentro do nucleo.

O que este arquivo NAO mede: se o operador ve a moldura na tela. Isso ja e medido
ponta a ponta pela suite de paridade
(`_reversa_sdd/migration/parity_tests/12-paridade-telas.feature`). Aqui a medicao
e cirurgica, sobre a tabela.
"""
import os
import re
import sys

import pytest

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

from application import traducao  # noqa: E402
from application.traducao import RespostaDeErro, traduzir  # noqa: E402
from core.erros import (  # noqa: E402
    CsvIlegivel,
    DnaCsvSemColunas,
    ErroDeDominio,
    GedcomNaoSuportado,
    PessoaNaoEncontrada,
)
from utils.validate import validar_conteudo_gedcom  # noqa: E402

CAMINHO_DO_APP = os.path.join(PROJETO, "src", "app.py")

# O prefixo do legado. Ele NAO e decoracao: as tres excecoes que o carregam
# nasciam dentro do fluxo de DNA e eram capturadas pelo `except Exception`
# generico do ramo, que montava exatamente este texto. O `GedcomNaoSuportado`
# sai sem ele porque nasce no caminho de gravacao, que respondia direto.
PREFIXO_GENERICO = "Ocorreu um erro: "
# `RN-18` (2026-10-10): a mensagem de conteudo recusado deixou de ser uma MOLDURA com o motivo
# tecnico dentro e passou a ser uma frase unica, pedida pelo operador. O nome da constante
# mudou junto, de `MOLDURA_GEDCOM` para `MENSAGEM_GEDCOM`: ela nao e mais uma moldura em volta
# de um motivo, e sim o texto inteiro que a tela mostra.
MENSAGEM_GEDCOM = "Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."

# Motivos EXATOS que `utils.validate.validar_conteudo_gedcom` devolve hoje
# (`src/utils/validate.py:98`, `:100` e `:104`). Cada linha da tabela e o texto
# literal que a excecao carrega; o teste seguinte prende o motivo na origem com
# `validar_conteudo_gedcom`, de modo que mudar o texto la sem mudar aqui faca o
# teste falhar em vez de passar medindo uma copia desatualizada.
ENTRADAS_INVALIDAS = [
    (b"", "arquivo vazio",
     "conteudo vazio: e a primeira recusa do validador"),
    (b"0 HEAD\n0 TRLR\n\x00", "conteudo binario",
     "byte nulo no conteudo: controle nao tem o byte removido, ele recusa"),
    (b"isso nao e gedcom\n", "não começa com a declaração 0 HEAD",
     "sem a declaracao de cabecalho que abre todo GEDCOM valido"),
]


# ---------------------------------------------------------------------------
# Grupo A — a tabela de traducao (T024)
# ---------------------------------------------------------------------------

def _motivo(entrada):
    """Motivo textual para a entrada invalida, ou o frontao quando ela passa.

    O parametro e uma tupla `(conteudo, motivo, porque)` do bloco acima. O
    `assert` existe para o id do caso no relatorio do pytest ser legivel, e
    porque um caso que deixasse de ser invalido faria o teste medir o caminho
    feliz sem avisar.
    """
    conteudo, motivo, _porque = entrada
    return motivo


TABELA_MEDIDA = [
    pytest.param(
        PessoaNaoEncontrada("Seu nome 'X' nao foi encontrado no GEDCOM."),
        PREFIXO_GENERICO + "Seu nome 'X' nao foi encontrado no GEDCOM.",
        404,
        id="PessoaNaoEncontrada",
    ),
    pytest.param(
        DnaCsvSemColunas("Colunas de Nome e cM nao encontradas no CSV."),
        PREFIXO_GENERICO + "Colunas de Nome e cM nao encontradas no CSV.",
        422,
        id="DnaCsvSemColunas",
    ),
    pytest.param(
        CsvIlegivel("Nao foi possivel ler o arquivo CSV."),
        PREFIXO_GENERICO + "Nao foi possivel ler o arquivo CSV.",
        422,
        id="CsvIlegivel",
    ),
    pytest.param(
        GedcomNaoSuportado("arquivo vazio"),
        MENSAGEM_GEDCOM,
        422,
        id="GedcomNaoSuportado",
    ),
]


@pytest.mark.parametrize("erro, mensagem_esperada, status_esperado", TABELA_MEDIDA)
def test_tabela_reproduz_o_texto_e_o_status_medidos(erro, mensagem_esperada,
                                                    status_esperado):
    """`T024`: o par (mensagem, status) e o que a sonda diferencial mediu.

    A assercao e de IGUALDADE, e nao de "contem": um prefixo a mais ou um ponto
    final a menos muda o que o operador le, e e exatamente isso que a `RN-02`
    protege. O prefixo `"Ocorreu um erro: "` das tres primeiras vem do
    `except Exception` do legado; a moldura sem prefixo da quarta vem do caminho
    de gravacao. Reproduzir os dois e o que mantem a paridade.
    """
    resposta = traduzir(erro)

    assert isinstance(resposta, RespostaDeErro), (
        "traduzir deixou de devolver o resultado tipado"
    )
    assert resposta.mensagem == mensagem_esperada
    assert resposta.status == status_esperado


def test_raiz_do_dominio_tambem_tem_traducao():
    """Rede de seguranca: um tipo de dominio novo NUNCA chega sem resposta.

    `ErroDeDominio` esta na tabela (`traducao.py:108`) justamente para que a
    proxima onda que criar um tipo e esquecer de registrar o tradutor proprio
    receba o texto generico do legado — e nao um `TypeError` na cara do
    operador. Sem esta assercao, remover a linha da raiz passaria despercebido
    pela suite: o `raise` do fim de `traduzir` so dispara em execucao.
    """
    resposta = traduzir(ErroDeDominio("falha de dominio sem moldura propria"))

    assert resposta.mensagem == PREFIXO_GENERICO + "falha de dominio sem moldura propria"
    assert resposta.status == 422
    # A raiz tem de continuar irma do tipo generico de linguagem (`RF-05`): se a
    # heranca de `ValueError` cair, as quatro assercoes existentes da suite caem
    # junto e a razao fica escondida.
    assert isinstance(ErroDeDominio("x"), ValueError)


def test_status_da_traducao_nao_tem_consumidor_no_adaptador_de_entrada():
    """`RN-05`: o campo `status` existe para a API futura e NENHUMA tela o le.

    Este teste e honesto sobre o que faz: ele INSPECIONA O FONTE de
    `src/app.py`, nao a execucao. Nao ha como medir "ausencia de leitura" por
    comportamento — nenhum ramo de tela falharia hoje se alguem passasse a usar
    `traduzir(erro).status` como codigo HTTP, e e essa mudanca silenciosa que o
    teste existe para impedir. Um teste de execucao mediria o resultado do
    renderizador, que e identico nos dois mundos; por isso a medicao e textual.

    Duas condicoes, as duas necessarias:

    1. Nenhum ramo que traduz le `status` (regex sobre o trecho
       `traduzir(...)` que o adaptador escreve).
    2. Os tres ramos que traduzem usam `.mensagem` — a condicao que da sentido a
       primeira: sem ela, o teste passaria porque o adaptador simplesmente nao
       traduz.

    Quando a API nova chegar, ela vai ler este campo, e o teste sera reescrito
    com a linha nova declarada — nao apagado.
    """
    with open(CAMINHO_DO_APP, encoding="utf-8") as fonte:
        texto = fonte.read()

    # Os espacos sao colapsados ANTES do regex de proposito: sem isso, uma
    # chamada quebrada em duas linhas (`traduzir(erro)\n    .status`) escaparia
    # da busca e o teste passaria verde medindo um fonte que ele nao leu. O que
    # o colapso faz e remover a diferenca entre as formas de escrever a MESMA
    # leitura.
    normalizado = " ".join(texto.split())

    leituras = re.findall(r"traduzir\([^)]*\)\s*\.\s*status", normalizado)
    assert leituras == [], (
        "o adaptador de entrada passou a ler o status da traducao; a RN-05 diz "
        "que a coluna nao tem consumidor nesta onda: %r" % leituras
    )

    usos = re.findall(r"traduzir\([^)]*\)\s*\.\s*mensagem", normalizado)
    assert len(usos) == 3, (
        "esperados os tres ramos de traduzir (upload, dna_analysis e "
        "path_search), encontrados %d" % len(usos)
    )

    # A coluna esta aqui, e nao sumiu: o que o teste prende e a AUSENCIA DE
    # CONSUMIDOR, e nao a ausencia do campo.
    assert traduzir(PessoaNaoEncontrada("x")).status == 404
    assert "status" in RespostaDeErro.__dataclass_fields__


# ---------------------------------------------------------------------------
# Grupo B — a moldura mora na traducao, nao na excecao (T029 / A002)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entrada", ENTRADAS_INVALIDAS, ids=_motivo)
def test_motivo_exato_continua_sendo_o_que_o_validador_produz(entrada):
    """Prende o motivo na ORIGEM para o Grupo B nao medir uma copia velha.

    As linhas de `ENTRADAS_INVALIDAS` sao literais, de proposito: um teste que
    derivasse o motivo chamando o validador seria circular — passaria mesmo que
    o texto do motivo mudasse, que e justamente o evento que a `T029` existe
    para tornar visivel. Chamando o validador AQUI, uma mudanca de texto em
    `utils/validate.py` quebra este teste com a mensagem dizendo qual motivo
    divergiu, em vez de a suite inteira seguir verde medindo outro texto.
    """
    conteudo, motivo, _porque = entrada

    assert validar_conteudo_gedcom(conteudo) == motivo


@pytest.mark.parametrize("entrada", ENTRADAS_INVALIDAS, ids=_motivo)
def test_excecao_carrega_apenas_o_motivo(entrada):
    """`T029`/`A002`: a excecao NUNCA contem a moldura de apresentacao.

    `str(erro)` e o motivo cru. Se a moldura voltar para dentro da excecao, a
    traducao a aplica DE NOVO e o operador passa a ler
    `"Arquivo nao reconhecido como GEDCOM: Arquivo nao reconhecido como GEDCOM:
    ..."`. Este e o teste que impede esse vazamento de texto de tela para dentro
    do nucleo — o inverso do objetivo da Onda 2.
    """
    conteudo, motivo, _porque = entrada

    erro = GedcomNaoSuportado(motivo)

    assert str(erro) == motivo, "a excecao deixou de carregar so o motivo"
    assert MENSAGEM_GEDCOM not in str(erro), (
        "a moldura vazou para dentro da excecao; a traducao vai duplica-la"
    )
    assert "GEDCOM" not in str(erro).replace(motivo, ""), (
        "ha texto de apresentacao alem do motivo dentro da excecao"
    )


@pytest.mark.parametrize("entrada", ENTRADAS_INVALIDAS, ids=_motivo)
def test_traducao_e_quem_monta_a_moldura_em_volta_do_motivo(entrada):
    """A moldura e da traducao: motivo + moldura sao o texto medido, uma vez so.

    Repare na assercao de ocorrencia UNICA: ela e o que prova que a moldura foi
    aplicada exatamente uma vez. Contar uma vez prende os dois defeitos de uma
    so vez — a moldura ausente (texto sem contexto para o operador) e a moldura
    duplicada (excecao carregando apresentacao).
    """
    _conteudo, motivo, _porque = entrada

    resposta = traduzir(GedcomNaoSuportado(motivo))

    assert resposta.mensagem == MENSAGEM_GEDCOM, (
        "a mensagem de conteudo recusado mudou: a `RN-18` fixa UMA frase para os tres motivos"
    )
    assert motivo not in resposta.mensagem, (
        f"o motivo tecnico ({motivo!r}) voltou para a tela: a `RN-18` o esconde do operador, e "
        "ele continua disponivel dentro da excecao para quem depura"
    )
    assert resposta.mensagem.endswith(".")
    assert resposta.status == 422


def test_motivo_de_gedcom_nao_leva_prefixo_generico():
    """O `GedcomNaoSuportado` e a UNICA excecao do mapa sem o prefixo generico.

    Ele nao nasce dentro do fluxo de DNA: nasce no caminho de gravacao, que
    respondia direto. Se alguem "padronizar" as cinco linhas da tabela com o
    mesmo prefixo, a tela muda para o operador sem que nenhum outro teste
    perceba — a paridade so olha o texto exibido, e este teste olha a REGRA.
    """
    resposta = traduzir(GedcomNaoSuportado("arquivo vazio"))

    assert not resposta.mensagem.startswith(PREFIXO_GENERICO)

    # E as outras quatro continuam COM o prefixo: a assimetria e uma so, e
    # declarada, nao um acidente da ultima linha escrita.
    com_prefixo = [
        traduzir(PessoaNaoEncontrada("a")),
        traduzir(DnaCsvSemColunas("b")),
        traduzir(CsvIlegivel("c")),
        traduzir(ErroDeDominio("d")),
    ]
    assert all(r.mensagem.startswith(PREFIXO_GENERICO) for r in com_prefixo)


def test_tabela_cobre_todo_tipo_declarado_na_hierarquia():
    """Nenhum tipo da hierarquia pode ficar fora da tabela de traducoes.

    A varredura e sobre `core.erros`, e nao sobre uma lista escrita aqui: um
    tipo novo entra na varredura sozinho e este teste o cobra. Cobertura parcial
    seria pior que a ausencia da tabela, porque o tipo esquecido cairia no
    tradutor da raiz e receberia uma moldura generica em silencio.
    """
    declarados = {
        nome for nome in dir(__import__("core.erros", fromlist=["erros"]))
        if not nome.startswith("_")
    }
    import core.erros as modulo_erros

    tipos = {
        getattr(modulo_erros, nome)
        for nome in declarados
        if isinstance(getattr(modulo_erros, nome), type)
        and issubclass(getattr(modulo_erros, nome), ErroDeDominio)
    }

    faltando = tipos - set(traducao._TRADUTORES)
    assert faltando == set(), (
        "tipo de dominio sem tradutor na tabela: %s"
        % sorted(t.__name__ for t in faltando)
    )
