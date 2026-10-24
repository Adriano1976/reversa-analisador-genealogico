"""Tabela de traducao: excecao de dominio -> literal da tela e status (`T014`).

A tabela e de **FUNCOES**, e nao de classe para constante: sete das nove mensagens
congeladas de `_reversa_sdd/migration/parity_tests/12-paridade-telas.feature`
interpolam valores (`"Pessoa 1 'X' nao encontrada."`, `"Nao foi possivel ler o
arquivo CSV. Tentativas feitas: ..."`), e um mapa de classe para string constante nao
consegue construi-las — a traducao precisa **receber a excecao** e devolver o texto.

Os literais foram MEDIDOS, nao deduzidos: condicoes parecidas tem modos de apresentacao
diferentes no legado. Medido com a sonda `evidence/probe_mensagens_antes.py`, antes da
extracao:

| Condicao | O que a tela exibe |
|---|---|
| GEDCOM recusado na validacao | `Arquivo nao reconhecido como GEDCOM: <motivo>.` — **sem** prefixo |
| Raiz do DNA ausente do GEDCOM | `Ocorreu um erro: Seu nome 'X' nao foi encontrado no GEDCOM.` — **com** prefixo |
| CSV sem colunas obrigatorias | `Ocorreu um erro: Colunas de Nome e cM nao encontradas no CSV. ...` — com prefixo |
| CSV ilegivel | `Ocorreu um erro: Nao foi possivel ler o arquivo CSV. ...` — com prefixo |

O prefixo existe porque, no legado, as tres ultimas nascem **dentro** do fluxo de DNA e sao
capturadas pelo `except Exception` generico do ramo, que monta `f"Ocorreu um erro: {e}"`; a
primeira nasce no caminho de gravacao e sai direto, sem esse `except`. Reproduzir o prefixo
onde ele existe mantem a `RN-02`: o mecanismo de sinalizacao muda, o texto observavel nao.

A coluna de status nao tem consumidor nesta onda: `RN-05` diz que o mapeamento para
`404`/`422` vale **somente** para a API nova, que nao existe ainda. Nenhuma tela atual le
esta coluna — o adaptador usa apenas a mensagem. Ela esta aqui, e testada (`T024`), para que
a regra de conversao exista em um lugar so quando a API chegar.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.erros import (
    CsvIlegivel,
    DnaCsvSemColunas,
    ErroDeDominio,
    GedcomNaoSuportado,
    PessoaNaoEncontrada,
)


@dataclass(frozen=True)
class RespostaDeErro:
    """O que o adaptador precisa para responder a uma excecao de dominio."""

    mensagem: str
    status: int


def _pessoa_nao_encontrada(erro: PessoaNaoEncontrada) -> RespostaDeErro:
    """`404`: a pessoa nomeada no pedido nao existe na arvore carregada.

    O prefixo e o que a tela mostra hoje, nao escolha nova: a excecao nasce dentro do fluxo
    de DNA, e o legado a exibe pelo `except Exception` do ramo.
    """
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 404)


def _dna_csv_sem_colunas(erro: DnaCsvSemColunas) -> RespostaDeErro:
    """`422`: o arquivo foi entendido, o conteudo nao serve."""
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 422)


def _csv_ilegivel(erro: CsvIlegivel) -> RespostaDeErro:
    """`422`: o arquivo nao pode ser lido por nenhuma das tentativas (`RF-21`)."""
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 422)


def _gedcom_nao_suportado(erro: GedcomNaoSuportado) -> RespostaDeErro:
    """`422` e a mensagem **unica** de conteudo recusado (`RN-18`, `T039`).

    Pedido do operador em 2026-10-10: antes, o texto levava o motivo dentro
    (`"Arquivo nao reconhecido como GEDCOM: <motivo>."`) e o operador lia o motivo tecnico
    do validador — "nao comeca com a declaracao 0 HEAD"; agora a tela diz sempre esta frase.

    O motivo NAO se perdeu, e isso e deliberado: continua na excecao (`erro`), que o carrega
    desde a feature 006 (`A002`) — `validate.py` devolve o motivo, a excecao o transporta, e
    **so a apresentacao** deixou de exibi-lo. Quem depurar o tem a um `str(erro)` de
    distancia, e o ramo de envio pode volta-lo a mostrar sem tocar no validador.

    Custo declarado: as **tres** recusas de conteudo — arquivo vazio, byte nulo e cabecalho
    ausente — passam a ter o MESMO texto, e o operador perde a pista de qual foi. A troca foi
    pedida com a consequencia a vista; se um dia o arquivo vazio precisar de texto proprio, e
    uma linha aqui, e o motivo ja esta na excecao.
    """
    return RespostaDeErro("Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto.", 422)


def _erro_de_dominio_sem_moldura_propria(erro: ErroDeDominio) -> RespostaDeErro:
    """Rede de seguranca para um tipo de dominio novo, ainda sem moldura propria.

    Preserva o texto que o legado produziria para uma falha inesperada, em vez de deixar a
    resposta sem mensagem: `ErroDeDominio` herda de `ValueError`, entao antes da extracao
    esta condicao caia no `except Exception` do ramo.
    """
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 422)


# A ordem nao e significativa: os quatro tipos sao IRMAOS, nao uma cadeia — no maximo um
# `isinstance` casa por excecao. O generico fica por ultimo: a busca percorre a insercao.
_TRADUTORES = {
    PessoaNaoEncontrada: _pessoa_nao_encontrada,
    GedcomNaoSuportado: _gedcom_nao_suportado,
    DnaCsvSemColunas: _dna_csv_sem_colunas,
    CsvIlegivel: _csv_ilegivel,
    ErroDeDominio: _erro_de_dominio_sem_moldura_propria,
}


def traduzir(erro: ErroDeDominio) -> RespostaDeErro:
    """Mensagem literal da tela e status HTTP para uma excecao de dominio."""
    for tipo, tradutor in _TRADUTORES.items():
        if isinstance(erro, tipo):
            return tradutor(erro)
    # Inalcancavel: a assinatura exige `ErroDeDominio`, e a raiz esta na tabela.
    raise TypeError("tipo sem traducao: %r" % type(erro).__name__)


__all__ = ["RespostaDeErro", "traduzir"]
