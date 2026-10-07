"""A arvore carregada pelo ULTIMO parse (feature 005, T023).

## Por que isto existe

Ate a feature 005, `load_gedcom_and_build_graph` mutava as globais de
`core.gedcom_state`, e os testes liam `_gs.people` depois. O parse passou a
DEVOLVER a arvore e a nao escrever estado, entao a leitura passou a ser do valor.

Este modulo guarda o resultado da ultima carga para os testes que precisam da
arvore depois de chama-la. Nao e estado de dominio: e o retorno do parse, que o
teste guardou porque o perdeu de vista — o parse acontece antes da assercao.

Enquanto houver uma carga por teste, e equivalente a ler o global; a diferenca e
que o valor e o que o parse DEVOLVEU, e nao um efeito colateral dele.
"""
from __future__ import annotations

ATUAL = None


def guardar(arvore):
    """Guarda a arvore devolvida pelo parse. Devolve a propria arvore.

    Existe para o `return guardar(carregar_arvore(path))` das fixtures: uma linha
    so, que carrega e registra.
    """
    global ATUAL
    ATUAL = arvore
    return arvore


def atual():
    """A arvore guardada pelo ultimo `guardar`.

    A captura e explicita (o helper de carga de cada arquivo chama `guardar`) de
    proposito: a alternativa — o parser registrar o proprio retorno — foi tentada
    em 2026-10-06 e criou um efeito colateral global que nao resolveu o problema
    real, que era o FIXTURE ler as globais depois do parse.

    Falha alto quando nada foi carregado, em vez de recorrer ao modulo de estado:
    aquele recurso existiu enquanto `carregar_arvore` escrevia as globais (`D-11`)
    e saiu com elas em `T023`. Ele escondia o defeito real — um arquivo de teste
    que carrega por fora deste helper e depois le a arvore de OUTRO arquivo, ja
    que a suite inteira compartilha um processo.
    """
    if ATUAL is None:
        raise AssertionError(
            "nenhuma arvore carregada: chame `guardar(carregar_arvore(...))` na fixture"
        )
    return ATUAL
