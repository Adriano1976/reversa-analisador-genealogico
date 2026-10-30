"""Limite de tentativas por escopo (feature 053, `D-13`).

## Por que na memoria, e por que o relogio entra por parametro

A aplicacao e instancia unica por construcao (`ADR-12`), entao um dicionario no
processo e suficiente e nao custa dependencia nem escrita no caminho quente. O
preco esta declarado: reiniciar zera o contador.

O `Relogio` e injetado porque o teste precisa atravessar a janela de quinze minutos
sem dormir. Sem isso, o teste do limite seria um `sleep` de quinze minutos ou um
monkeypatch em `datetime`, que e o que o projeto recusa desde a 051.

## Verificar e registrar sao atos separados

`permitir` so responde; `registrar` conta. A separacao existe porque a entrada
registra **apenas a falha** — cinco logins bem-sucedidos nao podem bloquear o
sexto —, enquanto o cadastro e a recuperacao registram toda tentativa. Um metodo
unico obrigaria a inventar um parametro para dizer qual dos dois comportamentos
usar, e o nome do parametro seria a regra escondida.
"""
from __future__ import annotations

from _thread import lock

from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from threading import Lock

from ports import Relogio


@dataclass(frozen=True)
class Regra:
    """Quantas tentativas cabem numa janela."""

    limite: int
    janela: timedelta


#: Os numeros da `RN-15`, um por escopo.
REGRAS: dict[str, Regra] = {
    "entrada": Regra(5, timedelta(minutes=15)),
    "cadastro": Regra(5, timedelta(hours=1)),
    "recuperacao": Regra(3, timedelta(minutes=15)),
    "reenvio": Regra(3, timedelta(hours=1)),
}


class LimiteExcedido(RuntimeError):
    """A tentativa passou do limite da janela. A tela responde generica."""

    def __init__(self, escopo: str) -> None:
        self.escopo = escopo
        super().__init__(escopo)


class Limitador:
    """Contador em processo, por `(escopo, chave)`."""

    def __init__(self, relogio: Relogio, regras: dict[str, Regra] | None = None) -> None:
        self._relogio: Relogio = relogio
        self._regras: dict[str, Regra] = regras if regras is not None else REGRAS
        self._eventos: dict[tuple[str, str], deque] = {}
        self._trava: lock = Lock()

    def permitir(self, escopo: str, chave: str) -> bool:
        """Se ainda cabe uma tentativa para esta chave, sem registrar nada."""
        regra = self._regras[escopo]
        agora = self._relogio.agora()
        with self._trava:
            fila = self._eventos.setdefault((escopo, chave), deque())
            inicio = agora - regra.janela
            while fila and fila[0] <= inicio:
                fila.popleft()
            return len(fila) < regra.limite

    def registrar(self, escopo: str, chave: str) -> None:
        """Conta uma tentativa."""
        with self._trava:
            self._eventos.setdefault((escopo, chave), deque()).append(self._relogio.agora())

    def exigir(self, escopo: str, chave: str) -> None:
        """Levanta `LimiteExcedido` quando a chave ja estourou a janela."""
        if not self.permitir(escopo, chave):
            raise LimiteExcedido(escopo)

    def limpar(self, escopo: str, chave: str) -> None:
        """Zera o escopo da chave. Usado no sucesso da entrada, se necessario."""
        with self._trava:
            self._eventos.pop((escopo, chave), None)


__all__: list[str] = ["REGRAS", "LimiteExcedido", "Limitador", "Regra"]
