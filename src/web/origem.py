"""Checagem de origem dos `POST` de identidade (feature 053, `D-14`).

## O vetor que sobra com `SameSite=Lax`

O cookie de sessao nao acompanha `POST` de outro site, mas o **login CSRF** nao
precisa disso: um formulario hostil envia as credenciais do atacante, e a resposta
grava a sessao do atacante no navegador da vitima — que passa a enviar os proprios
arquivos para a conta dele. A defesa aqui e a origem do pedido: navegador moderno
manda `Origin` em `POST` de formulario, e `Sec-Fetch-Site` diz `cross-site`.

## Sem token CSRF nesta entrega

Um token em sessao anonima resolveria o mesmo problema com mais estado e mais uma
tela. A decisao esta no `roadmap.md` (`D-14`); o custo declarado e que cliente que
nao mande nenhum dos dois cabecalhos passa — o que cobre navegador antigo e
ferramenta de teste, e nao cobre o atacante de navegador atual.
"""
from __future__ import annotations

from typing import Any

from urllib.parse import urlparse

from flask import current_app, request


def veio_de_fora() -> bool:
    """`True` quando o pedido veio de outra origem, segundo os cabecalhos do navegador."""
    if (request.headers.get("Sec-Fetch-Site") or "").strip().lower() == "cross-site":
        return True
    referencia: str = (request.headers.get("Origin") or request.headers.get("Referer") or "").strip()
    if not referencia:
        return False
    partes = urlparse(referencia)
    if not partes.netloc:
        return True
    permitidos: list[Any] = list(current_app.config.get("TRUSTED_HOSTS") or [])
    if partes.netloc in permitidos:
        return False
    nomes: set[Any] = {endereco.split(":")[0].strip().lower() for endereco in permitidos}
    return (partes.hostname or "").strip().lower() not in nomes


__all__: list[str] = ["veio_de_fora"]
