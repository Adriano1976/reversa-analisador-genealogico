"""Caso de uso da busca de caminho (`T012`; `RF-01`, `RF-20`, `D-11`, `D-12`).

Chama `core.path_search.path_search` e devolve resultado tipado. O nucleo **nao**
e alterado (`D-12`): a tupla de tres elementos que ele devolve e contrato de
paridade — `_reversa_sdd/parity/harness.py:211` compara o indicador de sucesso
contra o oraculo, e nove asseracoes de teste a desempacotam.

## O desfecho, e por que ele existe

`path_search` e o unico fluxo em que o nucleo sinaliza **tres** estados, e todos
os tres viram tela de formas diferentes:

| O que o nucleo devolve | Desfecho | Modo de renderizacao |
|---|---|---|
| payload, `success=True` | `RESULTADO` | cartao de resultado |
| `None`, `success=True` | `SEM_RESULTADO` | "nenhuma conexao encontrada", **com sucesso** |
| `None`, `success=False` | `ERRO_DE_ENTRADA` | alerta de erro |

Sem esses tres valores o adaptador teria de distinguir os dois ultimos pelo
**texto** da mensagem, e o literal de tela passaria a ter autoridade semantica —
o que a `RF-20` proibe. O desfecho e derivado dos dois insumos que o nucleo ja
sinaliza, nunca do texto.
"""
from __future__ import annotations

from dataclasses import dataclass

from application import Desfecho
from core.path_search import path_search as fluxo_de_busca


@dataclass(frozen=True)
class ResultadoDeBusca:
    """Resultado da busca. `dados` e o payload do nucleo, sem renomear nada dele.

    O campo **nao** se chama `path_result`: esse e o nome do campo de template, e
    a `RF-20` proibe nome de campo de template de atravessar a fronteira. O
    adaptador de entrada e quem decide sob qual nome (se algum) ele vai ao
    template.
    """

    desfecho: Desfecho
    dados: dict | None
    mensagem: str


def path_search(person1_name: str, person2_name: str, arvore, deps,
                dono: str) -> ResultadoDeBusca:
    """Executa a busca e devolve `ResultadoDeBusca`.

    `deps` sao as dependencias de diagrama montadas **na borda** e entregues por
    parametro (`D-05`): o caso de uso nao monta a sua propria copia por
    requisicao, que e o defeito latente que a `RF-14` proibe.

    `dono` **nao** e usado para comportamento nesta onda (`RN-06`, `RF-08`): esta
    na assinatura como costura para a Onda 3, e nenhum isolamento e implementado.
    """
    dados, mensagem, sucesso = fluxo_de_busca(person1_name, person2_name, deps, arvore)
    return ResultadoDeBusca(
        desfecho=_desfecho(dados, sucesso),
        dados=dados,
        mensagem=mensagem,
    )


def _desfecho(dados, sucesso) -> Desfecho:
    """Deriva o desfecho dos DOIS insumos que o nucleo sinaliza (`D-11`).

    A ordem dos testes e a precedencia: payload presente e `RESULTADO` mesmo que o
    indicador de sucesso viesse falso — e ele nao vem, nos tres estados que o
    nucleo produz hoje. O par (payload, sucesso) cobre os tres valores, e nenhum
    deles e inalcancavel.
    """
    if dados is not None:
        return Desfecho.RESULTADO
    return Desfecho.SEM_RESULTADO if sucesso else Desfecho.ERRO_DE_ENTRADA


__all__ = ["ResultadoDeBusca", "path_search"]
