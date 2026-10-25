"""A fiacao de registro na borda HTTP: identificador, cabecalho e linha de acesso (feature 049).

## O que este modulo faz

- `before_request`: gera o identificador curto da requisicao (`RF-03`).
- `after_request`: devolve o identificador no cabecalho `X-Request-ID` e escreve **uma**
  linha de acesso com metodo, rota, situacao e duracao (`RF-04`).

## Por que no `after_request`, e nao na rota

O cabecalho precisa sair em **toda** resposta, inclusive nas que o Flask produz sem passar
pela rota: `404` de arte ausente, `413` de corpo grande, `400` de `Host` recusado. Escrever
na rota deixaria justamente as respostas de erro sem identificador — que sao as que alguem
vai querer correlacionar com o log.

## Por que o valor NAO vem do cliente

`X-Request-ID` enviado pelo cliente e ignorado. Aceitar o valor permitiria escrever texto
arbitrario (inclusive quebra de linha) no arquivo de log, e um identificador escolhido por
quem chama nao identifica nada.
"""
from __future__ import annotations

import time

from flask import g, request

from utils import logs

CABECALHO = "X-Request-ID"

# Guardado no `g` da requisicao, e nao em variavel de modulo: `g` e do contexto da requisicao
# e nao vaza entre as quatro threads.
_CHAVE_DO_INICIO = "inicio_da_requisicao"


def instalar(aplicacao) -> None:
    """Liga os dois ganchos na aplicacao recebida."""
    aplicacao.before_request(_abrir_requisicao)
    aplicacao.after_request(_fechar_requisicao)


def _abrir_requisicao() -> None:
    logs.novo_identificador()
    setattr(g, _CHAVE_DO_INICIO, time.perf_counter())


def _fechar_requisicao(resposta):
    inicio = getattr(g, _CHAVE_DO_INICIO, None)
    duracao = (time.perf_counter() - inicio) * 1000 if inicio is not None else 0.0
    if logs.identificador_atual() == "-":
        # Defensivo: uma requisicao recusada antes do `before_request` (por exemplo pelo
        # cabecalho `Host`) ainda precisa de identificador para a linha de acesso e o
        # cabecalho combinarem.
        logs.novo_identificador()
    logs.registrar_acesso(
        request.method, request.path, resposta.status_code, duracao
    )
    resposta.headers[CABECALHO] = logs.identificador_atual()
    # O cabecalho ja saiu com o valor; o contexto volta ao neutro para a proxima linha
    # registrada fora de requisicao nao herdar um `id` que nao e dela.
    logs.esquecer_identificador()
    return resposta


def ip_do_cliente() -> str | None:
    """O IP que o servidor viu. Sem proxy no caminho, nao ha cabecalho a interpretar."""
    return request.remote_addr


def origem_da_requisicao() -> str:
    """`METODO /rota` — o mesmo par da linha de acesso, para a auditoria se localizar."""
    return f"{request.method} {request.path}"


__all__: list[str] = [
    "CABECALHO",
    "instalar",
    "ip_do_cliente",
    "origem_da_requisicao",
]
