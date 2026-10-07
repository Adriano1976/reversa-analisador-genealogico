"""Camada de aplicacao da Onda 2 (`RF-01`, `RF-20`).

Um **caso de uso** por fluxo: `upload_gedcom`, `path_search` e `dna_analysis`. O
caso de uso **orquestra e nao decide** regra de negocio — limiar, peso, ordem de
avaliacao e criterio de matching continuam todos no nucleo (`RN-01`).

O que atravessa a fronteira da aplicacao para o adaptador de entrada e um
**resultado tipado**: campos nomeados, sem nome de campo de template, sem o
parametro `success=` e sem dicionario de contexto de renderizacao (`RF-20`). As
mensagens de contrato congeladas viajam como **campo declarado** do resultado, e
nao como texto montado aqui: o adaptador le o campo, nao o redige.
"""
from __future__ import annotations

from enum import Enum

from core.registro import get_name


def nomes_de_exibicao(arvore) -> list[str]:
    """Nomes de exibicao ordenados — a lista que alimenta o campo de sugestao.

    Era o retorno da casca `load_gedcom_and_build_graph`, removida em `T015`. A
    derivacao vive **aqui**, e nao duplicada em cada caso de uso e em cada ramo do
    adaptador, porque e a mesma lista para os tres fluxos: o `upload_gedcom` a
    devolve no resultado, e os outros dois ramos a pedem emprestada para o campo
    de sugestao continuar preenchido.

    A ordenacao e `sorted` sobre `get_name`, exatamente como era, e nao um
    `sort` novo: a ordem desta lista e contrato da tela.
    """
    return sorted([get_name(p) for p in arvore[0].values()])


class Desfecho(Enum):
    """O que aconteceu, em tres valores — e os tres sao alcancaveis (`D-11`).

    Existe porque a `RF-20` proibe o parametro `success=` de atravessar a
    fronteira, e sem um campo que carregue o **fato** o adaptador teria de inferir
    o modo de renderizacao do **texto da mensagem** — dando ao literal de tela
    autoridade semantica, que e exatamente o que a `RF-20` existe para impedir.

    Nao ha quarto valor para "entrada invalida" em geral: toda entrada invalida
    que **nao** vem do nucleo ja e excecao de dominio, e excecao interrompe o
    fluxo em vez de produzir valor de enum. Um valor que nenhum caminho preenche
    seria superficie sem gatilho — o mesmo defeito que o achado `A002` removeu do
    `ArmazenamentoInvalido`.

    O valor e derivado de dois insumos que o nucleo **ja** sinaliza — a presenca
    de payload e o indicador de sucesso da tupla que ele devolve —, nunca do texto
    da mensagem. Ver `application/path_search.py`.
    """

    RESULTADO = "resultado"
    SEM_RESULTADO = "sem_resultado"
    ERRO_DE_ENTRADA = "erro_de_entrada"


__all__ = ["Desfecho", "nomes_de_exibicao"]
