"""Sessao da borda: a conta logada, a guarda e o cookie (feature 051).

## O que este modulo e

A autoridade unica sobre "quem esta logado" na aplicacao. A conta vive no cookie
assinado do Flask, e nao em estado de processo: reiniciar o servidor nao derruba o
operador, e o processo continua sem estado de dominio (`architecture.md#2`).

## A guarda e uma so, e por ENDPOINT

`instalar_guarda` liga um `before_request` que recusa com `302` (GET) ou `303`
(POST) toda operacao de dado sem sessao. A lista publica e fechada e nomeia
endpoints, nao prefixos de caminho: um prefixo novo nasceria publico por acidente.
As tres rotas de arte e de folha de estilo continuam publicas porque a propria tela
de entrada depende delas (`P-08`).

## Por que `no-store`

Depois do logout, o botao "voltar" do navegador nao pode reexibir a tela
autenticada: sem o cabecalho, o navegador serve a pagina do cache e o operador ve
dado de uma sessao que nao existe mais (`RF-06`).
"""
from __future__ import annotations

from dataclasses import dataclass

from flask import g, redirect, request, session, url_for

#: Chave da conta no cookie de sessao.
CHAVE_DA_CONTA = "conta"

#: Chave do valor de estado do fluxo OAuth, de uso unico.
CHAVE_DO_STATE = "oauth_state"

#: Endpoints alcancaveis sem sessao. Fechada de proposito.
PUBLICOS: frozenset[str] = frozenset({
    "auth.login",
    "auth.callback",
    "assets.icone_de_atalho",
    "assets.banner_do_topo",
    "assets.estilo_da_tela",
})


@dataclass(frozen=True)
class Conta:
    """A identidade autenticada. `sub` e o dono; `email` e `nome` sao rotulo de tela."""

    sub: str
    email: str = ""
    nome: str = ""

    @property
    def rotulo(self) -> str:
        """O nome que a masthead mostra: o nome da conta, ou o e-mail como recuo."""
        return (self.nome or "").strip() or (self.email or "").strip() or self.sub


def conta_atual() -> Conta | None:
    """A conta da sessao, ou `None` quando nao ha sessao valida."""
    dados = session.get(CHAVE_DA_CONTA)
    if not isinstance(dados, dict):
        return None
    sub: str = str(dados.get("sub") or "").strip()
    if not sub:
        return None
    return Conta(
        sub=sub,
        email=str(dados.get("email") or ""),
        nome=str(dados.get("nome") or ""),
    )


def guardar_conta(conta: Conta) -> None:
    """Limpa a sessao e grava a conta.

    A limpeza vem ANTES de proposito: e a defesa contra fixacao de sessao — o
    identificador que o navegador trazia deixa de valer no instante do login.
    """
    session.clear()
    session[CHAVE_DA_CONTA] = {
        "sub": conta.sub,
        "email": conta.email,
        "nome": conta.nome,
    }
    session.permanent = True


def encerrar_sessao() -> None:
    """Descarta tudo o que a sessao guardava."""
    session.clear()


def dono_atual() -> str:
    """O `sub` da conta da requisicao. So existe com a guarda instalada."""
    return getattr(g, "dono", "") or ""


def instalar_guarda(aplicacao) -> None:
    """Liga a guarda, o `no-store` e o processador de contexto da conta."""
    aplicacao.before_request(_exigir_sessao)
    aplicacao.after_request(_sem_cache)
    aplicacao.context_processor(lambda: {"conta": conta_atual()})


def _exigir_sessao():
    """Recusa a operacao de dado sem sessao; deixa passar o que e publico."""
    conta = conta_atual()
    if conta is not None:
        setattr(g, "conta", conta)
        setattr(g, "dono", conta.sub)
        return None
    if request.endpoint is None or request.endpoint in PUBLICOS:
        return None
    # 303 no POST: o navegador troca por GET e nao reenvia o corpo ao destino.
    codigo = 302 if request.method in ("GET", "HEAD") else 303
    return redirect(url_for("auth.login"), code=codigo)


def _sem_cache(resposta):
    """Impede o cache de qualquer resposta autenticada."""
    if conta_atual() is not None:
        resposta.headers["Cache-Control"] = "no-store"
    return resposta


__all__: list[str] = [
    "CHAVE_DA_CONTA",
    "CHAVE_DO_STATE",
    "PUBLICOS",
    "Conta",
    "conta_atual",
    "dono_atual",
    "encerrar_sessao",
    "guardar_conta",
    "instalar_guarda",
]
