"""Verificacao da versao de credencial a cada requisicao (feature 053, `RN-10`).

## O que a guarda pergunta, e por que a pergunta e barata

A guarda da 051 decide "tem sessao?"; esta funcao decide "a sessao ainda vale?".
A diferenca aparece na redefinicao de senha: a conta incrementa a versao e toda
sessao emitida antes dela passa a ser recusada.

A consulta e uma leitura do adaptador, que guarda o documento em memoria e so
rele quando o arquivo muda (`mtime_ns` + tamanho). Em regime normal, uma
requisicao autenticada paga um `stat`.

## Falha de armazenamento nao tranca ninguem

Se o arquivo estiver corrompido ou ilegivel, a funcao devolve `True` e registra o
erro: negar acesso a todas as contas por causa de um arquivo e pior do que adiar a
revogacao. A decisao esta declarada no `roadmap.md` §9.
"""
from __future__ import annotations

import logging

from ports import RepositorioDeContas

_log: logging.Logger = logging.getLogger(__name__)


class VerificadorDeVersao:
    """Callable que a guarda da sessao consulta em cada requisicao autenticada."""

    def __init__(self, repositorio: RepositorioDeContas) -> None:
        self._repositorio: RepositorioDeContas = repositorio

    def __call__(self, conta) -> bool:
        sub = getattr(conta, "sub", "") or ""
        if not sub:
            return False
        try:
            registro = self._repositorio.por_sub(sub)
        except Exception:  # armazenamento indisponivel: nao trancar a aplicacao
            _log.exception("falha ao conferir a versao de credencial")
            return True
        if registro is None:
            # Conta so-Google ainda sem linha local: nada a revogar.
            return True
        return registro.versao_de_credencial == int(getattr(conta, "versao", 0) or 0)


__all__: list[str] = ["VerificadorDeVersao"]
