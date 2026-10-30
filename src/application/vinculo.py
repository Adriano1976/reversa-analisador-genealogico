"""Vinculo de identidade por e-mail verificado (feature 053, `RN-20`).

## As duas direcoes, e a que NAO existe

| Direcao | Quando acontece | Por que e segura |
|---|---|---|
| Google -> conta local | No retorno do Google, quando o e-mail ja pertence a uma conta local confirmada | O Google so entrega conta com `email_verified` verdadeiro (051), e o `sub` do provedor e dele |
| Conta Google -> senha | Pela tela **autenticada** de definir senha | A sessao prova que quem define a senha e quem entrou |
| Cadastro deslogado -> conta existente | **Nunca.** | Quem escolhe a senha primeiro ganharia a conta quando o dono confirmasse o e-mail (pre-sequestro) |

## O `sub` nunca muda, e a pasta nunca muda de dono

A conta que ja existia e a dona do `sub` e da pasta em `src/uploads/<sub>/`. O
vinculo **anexa** a identidade nova a ela; criar uma segunda conta seria criar uma
segunda pasta e um segundo historico para a mesma pessoa (`RF-22`).

## Por que este modulo nao importa `web`

`application/` recebe dados, nao a `Conta` da sessao. A borda passa `sub`, `email`
e `nome`; assim a camada de aplicacao continua sem conhecer Flask (`RNF-04`).
"""
from __future__ import annotations

from dataclasses import replace

from core.conta import (
    ContaDeAcesso,
    ContaDuplicada,
    Credencial,
    SenhaJaDefinida,
    normalizar_email,
)
from ports import Relogio, RepositorioDeContas


class VinculoDeIdentidade:
    """Anexa identidades a conta existente, sem criar uma segunda."""

    def __init__(self, repositorio: RepositorioDeContas, relogio: Relogio) -> None:
        self._repositorio: RepositorioDeContas = repositorio
        self._relogio: Relogio = relogio

    def ao_entrar_com_google(self, sub: str, email: str, nome: str = "") -> ContaDeAcesso:
        """Devolve a conta canonica do dono que entrou pelo Google.

        Tres desfechos: a conta ja tem este `google_sub` (devolve como esta), o
        e-mail pertence a uma conta local (anexa e devolve o `sub` **dela**), ou nao
        ha conta nenhuma (cria a linha da conta Google, ja confirmada).
        """
        agora_iso: str = self._relogio.agora().isoformat()
        email_normalizado: str = normalizar_email(email)

        conta: ContaDeAcesso | None = self._repositorio.por_google_sub(sub)
        if conta is None:
            conta = self._repositorio.por_email(email_normalizado)
        if conta is None:
            nova = ContaDeAcesso(
                sub=sub,
                email=email,
                email_normalizado=email_normalizado,
                google_sub=sub,
                nome=nome,
                verificado_em=agora_iso,
                criado_em=agora_iso,
            )
            try:
                return self._repositorio.criar(nova)
            except ContaDuplicada:
                # Corrida entre duas requisicoes do mesmo dono: a linha ja existe.
                return self._repositorio.por_google_sub(sub) or nova

        mudancas: dict = {}
        if conta.google_sub is None:
            mudancas["google_sub"] = sub
        if conta.verificado_em is None:
            # Google ja provou a posse do endereco; a conta local nasce confirmada.
            mudancas["verificado_em"] = agora_iso
        if nome and not conta.nome:
            mudancas["nome"] = nome
        if email and not conta.email:
            mudancas["email"] = email
        if mudancas:
            conta = replace(conta, **mudancas)
            self._repositorio.salvar(conta)
        return conta

    def definir_primeira_senha(self, conta: ContaDeAcesso, credencial: Credencial) -> ContaDeAcesso:
        """Anexa a primeira credencial a uma conta ja autenticada.

        Nao incrementa a versao: nao havia credencial anterior para revogar, e a
        sessao que pediu a definicao e legitima (`RF-24`).
        """
        if conta.credencial is not None:
            raise SenhaJaDefinida(conta.sub)
        atualizada: ContaDeAcesso = replace(
            conta,
            credencial=credencial,
            verificado_em=conta.verificado_em or self._relogio.agora().isoformat(),
        )
        self._repositorio.salvar(atualizada)
        return atualizada


__all__: list[str] = ["VinculoDeIdentidade"]
