"""Definir a primeira senha de uma conta autenticada (feature 053, `RF-24`).

## Por que esta tela existe

Sem ela, quem entra pelo Google nunca poderia passar a entrar por senha — e o
proprio operador, que ja tem conta Google com arquivos, ficaria dependente do
provedor para sempre. O caminho e autenticado de proposito: a sessao prova que
quem define a senha e quem entrou, e o cadastro deslogado nunca toca conta
existente (pre-sequestro, `RN-20`).

## O que ela NAO faz

Nao incrementa a versao da credencial (nao havia credencial anterior para revogar)
e nao serve para trocar senha: conta que ja tem credencial e recusada pela borda
antes de chegar aqui.
"""
from __future__ import annotations

from core.conta import (
    ContaDeAcesso,
    ContaNaoEncontrada,
    ParametrosDeDerivacao,
    PoliticaDeSenha,
    SenhaJaDefinida,
    SenhasDiferentes,
    derivar_senha,
)
from ports import Relogio, RepositorioDeContas


class ServicoDeDefinirSenha:
    """Anexa credencial a conta da sessao, preservando `sub` e pasta."""

    def __init__(
        self,
        repositorio: RepositorioDeContas,
        relogio: Relogio,
        *,
        politica: PoliticaDeSenha | None = None,
        parametros: ParametrosDeDerivacao | None = None,
    ) -> None:
        self._repositorio: RepositorioDeContas = repositorio
        self._relogio: Relogio = relogio
        self._politica: PoliticaDeSenha = politica or PoliticaDeSenha()
        self._parametros: ParametrosDeDerivacao = parametros or ParametrosDeDerivacao()

    def ja_tem_senha(self, sub: str) -> bool:
        """Se a conta ja tem credencial, a tela de definir nao se aplica."""
        conta: ContaDeAcesso | None = self._repositorio.por_sub(sub)
        return conta is not None and conta.tem_senha

    def definir(self, sub: str, senha: str, repeticao: str) -> ContaDeAcesso:
        if senha != repeticao:
            raise SenhasDiferentes()
        self._politica.exigir(senha)
        conta: ContaDeAcesso | None = self._repositorio.por_sub(sub)
        if conta is None:
            raise ContaNaoEncontrada(sub)
        if conta.tem_senha:
            raise SenhaJaDefinida(sub)
        atualizada: ContaDeAcesso = conta.com_credencial(derivar_senha(senha, parametros=self._parametros))
        if not atualizada.confirmada:
            # A sessao ja provou a identidade; a conta passa a confirmada junto.
            atualizada = atualizada.confirmar(self._relogio.agora().isoformat())
        self._repositorio.salvar(atualizada)
        return atualizada


__all__: list[str] = ["ServicoDeDefinirSenha"]
