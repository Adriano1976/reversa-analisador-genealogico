"""Token de uso unico da identidade local (feature 053).

## O que o token e, e o que ele nunca e gravado

Um valor aleatorio de 32 bytes em forma segura para URL, entregue uma vez — no
link do e-mail — e guardado **apenas como derivacao**. Quem ler o arquivo de
contas nao consegue usar o token de ninguem (`RN-08`, `RN-19`).

## Dois tipos, duas validades, a mesma mecanica

| Tipo | Validade | Consumo |
|---|---|---|
| `confirmacao` | 24 horas | `GET /confirmar`, ao abrir o link |
| `redefinicao` | 60 minutos | `POST /redefinir-senha`, ao enviar a senha nova |

A diferenca de consumo e deliberada: o `GET` da redefinicao **nao** consome,
porque scanners de e-mail abrem links antes do dono e quebrariam o fluxo.

## A comparacao e em tempo constante

`conferir` usa `hmac.compare_digest`. A busca no repositorio e por hash, entao na
pratica a comparacao nem chega a ser feita em producao; ela existe para o caso de
o adaptador receber o token em claro no futuro, e para o teste prender a
propriedade.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

TIPO_CONFIRMACAO = "confirmacao"
TIPO_REDEFINICAO = "redefinicao"

#: Validade por tipo, em minutos. O dicionario e o contrato.
VALIDADE: dict[str, timedelta] = {
    TIPO_CONFIRMACAO: timedelta(hours=24),
    TIPO_REDEFINICAO: timedelta(minutes=60),
}

#: Entropia do token, em bytes.
TAMANHO_EM_BYTES = 32


class TipoDeTokenInvalido(ValueError):
    """O tipo pedido nao esta em `VALIDADE`."""


@dataclass(frozen=True)
class Token:
    """Token emitido. `texto` so existe no instante da emissao."""

    tipo: str
    hash: str
    expira_em: datetime
    texto: str | None = None

    def para_registro(self) -> dict:
        """O que vai para o armazenamento: sem o texto, nunca."""
        return {
            "tipo": self.tipo,
            "expira_em": self.expira_em.isoformat(),
        }


def derivar(texto: str) -> str:
    """sha256 hexadecimal do token em claro."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def emitir(tipo: str, agora: datetime, texto: str | None = None) -> Token:
    """Emite um token do tipo pedido, valido a partir de `agora`.

    `texto` existe para o teste fixar o valor; em producao e sempre aleatorio.
    """
    if tipo not in VALIDADE:
        raise TipoDeTokenInvalido(tipo)
    valor: str = texto if texto is not None else secrets.token_urlsafe(TAMANHO_EM_BYTES)
    return Token(
        tipo=tipo,
        hash=derivar(valor),
        expira_em=agora + VALIDADE[tipo],
        texto=valor,
    )


def valido(token: Token, agora: datetime) -> bool:
    """Se o token ainda vale no instante informado."""
    return token.expira_em > agora


def conferir(texto: str, hash_guardado: str | None) -> bool:
    """Compara o texto com o hash guardado, em tempo constante."""
    if not hash_guardado:
        return False
    return hmac.compare_digest(derivar(texto), hash_guardado)


__all__: list[str] = [
    "TAMANHO_EM_BYTES",
    "TIPO_CONFIRMACAO",
    "TIPO_REDEFINICAO",
    "VALIDADE",
    "TipoDeTokenInvalido",
    "Token",
    "conferir",
    "derivar",
    "emitir",
    "valido",
]
