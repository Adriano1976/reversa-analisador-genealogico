"""Entrada com e-mail e senha (feature 053, `RN-05`).

## A falha e indistinguivel, e o tempo tambem

E-mail inexistente e senha errada levantam o **mesmo** tipo, e o caso de e-mail
inexistente executa uma derivacao falsa com o mesmo custo antes de levantar. Sem
essa derivacao, o tempo de resposta entrega o que o texto esconde.

## Conta nao confirmada so se revela depois da senha

Se a senha confere e o e-mail ainda nao foi confirmado, a tela pede a confirmacao.
Se a senha nao confere, a resposta e a generica — senao "confirme seu e-mail" viraria
um oraculo de quais contas existem e estao pendentes.

## O limite conta a FALHA, nao a tentativa

Cinco entradas bem-sucedidas nao podem bloquear a sexta. `Permitir` verifica,
`registrar` conta, e so a falha registra (`RN-15`).
"""
from __future__ import annotations

from core.conta import (
    ContaDeAcesso,
    ErroDeConta,
    ParametrosDeDerivacao,
    conferir_senha,
    credencial_falsa,
    normalizar_email,
)
from ports import Relogio, RepositorioDeContas

from application.limite import Limitador


class CredenciaisInvalidas(ErroDeConta):
    """E-mail sem conta, conta sem senha ou senha errada: a mesma resposta."""


class EmailNaoConfirmado(ErroDeConta):
    """A senha confere, mas o e-mail ainda nao foi confirmado."""

    def __init__(self, conta: ContaDeAcesso) -> None:
        self.conta = conta
        super().__init__(conta.sub)


class ServicoDeEntradaLocal:
    """Verifica credencial e devolve a conta pronta para a sessao."""

    def __init__(
        self,
        repositorio: RepositorioDeContas,
        relogio: Relogio,
        limite: Limitador,
        *,
        parametros: ParametrosDeDerivacao | None = None,
    ) -> None:
        self._repositorio: RepositorioDeContas = repositorio
        self._relogio: Relogio = relogio
        self._limite: Limitador = limite
        self._parametros: ParametrosDeDerivacao = parametros or ParametrosDeDerivacao()

    def autenticar(self, email: str, senha: str, *, origem: str = "") -> ContaDeAcesso:
        normalizado: str = normalizar_email(email)
        chave: str = f"{normalizado}|{origem or 'sem-origem'}"
        self._limite.exigir("entrada", chave)

        conta: ContaDeAcesso | None = self._repositorio.por_email(normalizado)
        if conta is None or conta.credencial is None:
            # Custo igual ao de uma conta existente: o tempo nao pode ser oraculo.
            conferir_senha(senha, credencial_falsa(self._parametros))
            self._limite.registrar("entrada", chave)
            raise CredenciaisInvalidas()

        if not conferir_senha(senha, conta.credencial):
            self._limite.registrar("entrada", chave)
            raise CredenciaisInvalidas()

        if not conta.confirmada:
            raise EmailNaoConfirmado(conta)
        return conta


__all__: list[str] = ["CredenciaisInvalidas", "EmailNaoConfirmado", "ServicoDeEntradaLocal"]
