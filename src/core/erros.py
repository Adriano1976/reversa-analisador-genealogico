"""Excecoes de dominio tipadas da fronteira de aplicacao (RF-03, D-01).

## A raiz herda de `ValueError`, e isso e deliberado

`ErroDeDominio` herda de `ValueError` para que as quatro assercoes que a suite
ja escreve continue passando **sem serem reescritas** (`RF-05`):
`tests/test_confrontacao_gedcom_dna.py:920`, `:936` e `tests/test_dna_analysis.py:219`,
`:241`. Sem a heranca, a `RF-05` e o cenario "A suite existente nao pode ser
reduzida" seriam violados pela propria feature que existe para preservar
comportamento.

Consequencia declarada em `requirements.md` §4: excecao de dominio e excecao de
valor da linguagem ficam na mesma linhagem. Por isso nenhum `except ValueError`
pode passar a distinguir casos pela MENSAGEM — a distincao e sempre pelo TIPO.

## Cada tipo carrega apenas a mensagem do seu ponto de deteccao

A moldura de apresentacao fica na tabela de traducao do adaptador de entrada
(`application/traducao.py`), nunca aqui. Exemplo medido: o adaptador monta hoje
`"Arquivo nao reconhecido como GEDCOM. Favor, enviar o arquivo correto."` — frase FIXA
desde a `RN-18`, sem o motivo dentro —, enquanto
`utils.validate.validar_conteudo_gedcom` continua devolvendo so o `motivo`. A excecao carrega
o motivo; a moldura e da traducao. Sem essa separacao, texto de tela vazaria para
dentro do nucleo — o inverso do objetivo da Onda 2. E e essa separacao que permite a
`RN-18` esconder o motivo da tela **sem perde-lo**: ele segue na excecao, a um `str(erro)`
de distancia de quem depura.

## Por que NAO existe um quinto tipo

`ArmazenamentoInvalido` foi descartado (achado `A002` da auditoria). A razao e
factual: `utils/validate.py` devolve **motivo em texto**, nao excecao, e e o caso
de uso que transforma o motivo na excecao de GEDCOM nao reconhecido. Um tipo que
o adaptador de armazenamento nunca levanta seria superficie sem gatilho — a mesma
classe de defeito que a divida #17 da feature 005 fechou. A falha de
armazenamento propriamente dita (object storage, escopo por dono) e outro tipo,
com outro gatilho, e pertence a Onda 3.
"""
from __future__ import annotations


class ErroDeDominio(ValueError):
    """Raiz unica das excecoes de dominio do analisador.

    Captura-la e o que o adaptador de entrada faz para traduzir a condicao de
    negocio de volta ao literal da tela. Tudo que **nao** herda daqui continua
    sendo falha inesperada e segue o caminho de ultimo recurso.
    """


class PessoaNaoEncontrada(ErroDeDominio):
    """O nome informado como raiz da analise nao existe no GEDCOM.

    **Detectado e levantado por** `core.dna_analysis.dna_analysis`, o unico ponto
    que procura a pessoa-raiz pelo nome. A mensagem que ele levanta e
    `"Seu nome '{root_name}' nao foi encontrado no GEDCOM."`, sem moldura: o
    adaptador de entrada e quem acrescenta o prefixo que a tela exibe hoje.
    """


class GedcomNaoSuportado(ErroDeDominio):
    """O conteudo enviado nao foi reconhecido como GEDCOM.

    O motivo e **detectado** por `utils.validate.validar_conteudo_gedcom`, que
    devolve texto, e a excecao e **levantada pelo caso de uso** `upload_gedcom`
    ao receber esse motivo. E o unico tipo desta hierarquia que nao nasce dentro
    do nucleo nem de um parser: nasce na aplicacao, porque e na aplicacao que o
    motivo em texto do armazenamento vira condicao de negocio tipada.
    """


class DnaCsvSemColunas(ErroDeDominio):
    """O CSV de matches nao tem as colunas obrigatorias de nome e de cM.

    Tem **dois** pontos de deteccao, e os dois levantam este tipo: o fluxo do
    nucleo (`core.dna_analysis.dna_analysis`), com a mensagem acionavel que diz o
    separador usado e as colunas encontradas, e a agregacao da evidencia genetica
    (`core.genetic_evidence.build_genetic_evidence`), com a mensagem curta. Os
    dois textos sao diferentes de proposito e nenhum deles foi alterado.
    """


class CsvIlegivel(ErroDeDominio):
    """O CSV de matches nao pode ser lido por nenhuma das tentativas (`RF-21`).

    **Detectado e levantado por** `parsers.csv_ingest.read_csv_with_fallback`
    quando utf-8 e latin-1 falham. O tipo fecha a lacuna de rastreabilidade do
    achado `A002`: o ponto de levantamento ja existia e nao tinha requisito que o
    autorizasse.

    O fallback de encoding **nao** e afetado (`RN-03`, `RF-11`): a queda para
    latin-1 acontece antes deste ponto, e nenhuma excecao de dominio intercepta
    a troca de codec.
    """


__all__ = [
    "ErroDeDominio",
    "PessoaNaoEncontrada",
    "GedcomNaoSuportado",
    "DnaCsvSemColunas",
    "CsvIlegivel",
]
