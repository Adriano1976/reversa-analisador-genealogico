"""Tabela de traducao: excecao de dominio -> literal da tela e status (`T014`).

## Por que uma tabela de FUNCOES, e nao um mapa de classe para constante

Sete das nove mensagens congeladas de
`_reversa_sdd/migration/parity_tests/12-paridade-telas.feature` interpolam valores
(`"Pessoa 1 'X' nao encontrada."`, `"Nao foi possivel ler o arquivo CSV.
Tentativas feitas: ..."`). Um mapa de classe para string constante nao consegue
construi-las: a traducao precisa **receber a excecao** e devolver o texto montado.

## Os literais foram MEDIDOS, nao deduzidos

Duas condicoes parecidas tem modos de apresentacao diferentes no legado, e
escrever a tabela de cabeca erraria. Medido com a sonda
`evidence/probe_mensagens_antes.py`, antes da extracao:

| Condicao | O que a tela exibe |
|---|---|
| GEDCOM recusado na validacao | `Arquivo nao reconhecido como GEDCOM: <motivo>.` — **sem** prefixo |
| Raiz do DNA ausente do GEDCOM | `Ocorreu um erro: Seu nome 'X' nao foi encontrado no GEDCOM.` — **com** prefixo |
| CSV sem colunas obrigatorias | `Ocorreu um erro: Colunas de Nome e cM nao encontradas no CSV. ...` — com prefixo |
| CSV ilegivel | `Ocorreu um erro: Nao foi possivel ler o arquivo CSV. ...` — com prefixo |

O prefixo existe porque, no legado, as tres ultimas nascem **dentro** do fluxo de
DNA e sao capturadas pelo `except Exception` generico do ramo, que monta
`f"Ocorreu um erro: {e}"`. A primeira nasce no caminho de gravacao e sai direto,
sem passar por esse `except`. Reproduzir o prefixo onde ele existe e o que mantem
a `RN-02` — o mecanismo de sinalizacao muda, o texto observavel nao.

## A coluna de status nao tem consumidor nesta onda

`RN-05`: o mapeamento para `404`/`422` vale **somente** para a API nova, que nao
existe ainda. Nenhuma tela atual le esta coluna — o adaptador usa apenas a
mensagem. Ela esta aqui, e testada (`T024`), para que a regra de conversao exista
em um lugar so quando a API chegar, em vez de ser redescoberta la.
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

    O prefixo e o que a tela mostra hoje, e nao uma escolha nova: a excecao nasce
    dentro do fluxo de DNA e o legado a exibe atraves do `except Exception` do
    ramo.
    """
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 404)


def _dna_csv_sem_colunas(erro: DnaCsvSemColunas) -> RespostaDeErro:
    """`422`: o arquivo foi entendido, o conteudo nao serve."""
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 422)


def _csv_ilegivel(erro: CsvIlegivel) -> RespostaDeErro:
    """`422`: o arquivo nao pode ser lido por nenhuma das tentativas (`RF-21`)."""
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 422)


def _gedcom_nao_suportado(erro: GedcomNaoSuportado) -> RespostaDeErro:
    """`422` e a mensagem UNICA de conteudo recusado (`RN-18`, `T039`).

    Pedido do operador em 2026-10-10. Ate aqui o texto era montado com o motivo dentro
    (`"Arquivo nao reconhecido como GEDCOM: <motivo>."`), e o operador lia o motivo tecnico do
    validador — "nao comeca com a declaracao 0 HEAD". Agora a tela diz sempre a mesma frase,
    que e o que ele pediu.

    ## O motivo NAO se perdeu, e isso e deliberado

    Ele continua dentro da excecao (`erro`), que e quem o carrega desde a feature 006
    (`A002`): `validate.py` devolve o motivo, a excecao o transporta, e **so a apresentacao**
    deixou de exibi-lo. Quem depurar tem o motivo a um `str(erro)` de distancia, e o
    `except` do ramo de envio pode voltar a mostra-lo sem tocar no validador.

    ## O que esta mensagem custa, declarado

    As TRES recusas de conteudo — arquivo vazio, byte nulo e cabecalho ausente — passam a ter
    o MESMO texto. O operador perde a pista de qual foi o problema. A troca foi pedida com
    essa consequencia a vista; se algum dia o arquivo vazio precisar de texto proprio, e uma
    linha aqui, e o motivo para isso ja esta na excecao.
    """
    return RespostaDeErro("Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto.", 422)


def _erro_de_dominio_sem_moldura_propria(erro: ErroDeDominio) -> RespostaDeErro:
    """Rede de seguranca para um tipo de dominio novo, ainda sem moldura propria.

    Preserva o texto que o legado produziria para uma falha inesperada, em vez de
    deixar a resposta sem mensagem. E o mesmo caminho de hoje: `ErroDeDominio`
    herda de `ValueError`, entao antes da extracao esta condicao caia no
    `except Exception` do ramo.
    """
    return RespostaDeErro(f"Ocorreu um erro: {erro}", 422)


# A ordem nao e significativa: os quatro tipos sao IRMAOS, nao uma cadeia, entao
# no maximo um `isinstance` casa por excecao. O tipo mais generico fica por
# ultimo porque a busca percorre na ordem de insercao.
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
