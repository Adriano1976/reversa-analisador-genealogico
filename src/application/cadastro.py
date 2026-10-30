"""Cadastro e confirmacao de e-mail (feature 053, `RN-01`, `RN-07`, `RN-19`).

## A resposta e sempre a mesma, e isso e requisito

Existindo ou nao conta para o e-mail, `cadastrar` termina do mesmo jeito. A
diferenca vai **so por e-mail**: quem tem conta recebe o aviso de que alguem tentou
usar o endereco; quem nao tem recebe o link de confirmacao. A tela nunca diz "este
e-mail ja tem conta" — com a instancia compartilhada, essa frase seria um oraculo
de quais enderecos estao cadastrados (`RN-07`, `RF-04`).

## O que o cadastro deslogado NAO faz

Nao anexa senha a conta existente, nem altera nada nela. Quem escolhe a senha
primeiro ganharia a conta quando o dono confirmasse o e-mail — pre-sequestro. A
senha de uma conta Google nasce pela tela autenticada (`vinculo.py`, `RF-24`).

## Falha de envio nao desfaz o cadastro

A conta e criada, o envio falha, o log registra o motivo e a tela responde a frase
generica. O operador ainda consegue se recuperar: ao tentar entrar, ve a frase de
confirmacao e o reenvio. Desfazer a conta exigiria apagar registro, e apagar nao e
operacao desta entrega.
"""
from __future__ import annotations

from datetime import datetime

from core.token_de_uso_unico import Token

import logging

from core.conta import (
    ContaDeAcesso,
    ErroDeConta,
    ParametrosDeDerivacao,
    PoliticaDeSenha,
    SenhasDiferentes,
    derivar_senha,
    normalizar_email,
    novo_sub,
)
from core.token_de_uso_unico import TIPO_CONFIRMACAO, derivar, emitir
from ports import Relogio, RepositorioDeContas, TransporteDeEmail
from ports.email_smtp import EnvioIndisponivel, EnvioNaoConfigurado

from application.limite import Limitador

_log: logging.Logger = logging.getLogger(__name__)

TAMANHO_MAXIMO_DO_EMAIL = 254

ASSUNTO_CONFIRMACAO = "Confirme seu e-mail — Analisador Genealógico"
ASSUNTO_CONTA_EXISTENTE = "Sua conta no Analisador Genealógico"


class EmailInvalido(ErroDeConta):
    """O texto informado nao tem forma de e-mail (sem `@`, vazio ou grande demais)."""


class ServicoDeCadastro:
    """Cria conta nao confirmada, reenvia confirmacao e consome o token."""

    def __init__(
        self,
        repositorio: RepositorioDeContas,
        transporte: TransporteDeEmail,
        relogio: Relogio,
        limite: Limitador,
        *,
        politica: PoliticaDeSenha | None = None,
        parametros: ParametrosDeDerivacao | None = None,
        url_publica: str = "",
    ) -> None:
        self._repositorio: RepositorioDeContas = repositorio
        self._transporte: TransporteDeEmail = transporte
        self._relogio: Relogio = relogio
        self._limite: Limitador = limite
        self._politica: PoliticaDeSenha = politica or PoliticaDeSenha()
        self._parametros: ParametrosDeDerivacao = parametros or ParametrosDeDerivacao()
        self._url_publica: str = url_publica

    # ------------------------------------------------------------------ fluxo
    def cadastrar(self, email: str, senha: str, repeticao: str, *, origem: str = "") -> None:
        """Cadastra ou avisa, sempre com o mesmo desfecho visivel.

        Levanta `EmailInvalido`, `SenhasDiferentes`, `SenhaForaDaPolitica`,
        `LimiteExcedido` e `EnvioNaoConfigurado`; a rota traduz cada uma.
        """
        normalizado: str = self._normalizar(email)
        chave: str = origem or "sem-origem"
        self._limite.exigir("cadastro", chave)
        self._limite.registrar("cadastro", chave)
        if senha != repeticao:
            raise SenhasDiferentes()
        self._politica.exigir(senha)
        if not self._transporte.configurado:
            # Sem canal de confirmacao, criar a conta seria criar um beco sem saida.
            raise EnvioNaoConfigurado("nao_configurado")

        existente = self._repositorio.por_email(normalizado)
        if existente is not None:
            self._avisar_conta_existente(existente)
            return

        agora: datetime = self._relogio.agora()
        nova = ContaDeAcesso(
            sub=novo_sub(),
            email=email.strip(),
            email_normalizado=normalizado,
            credencial=derivar_senha(senha, parametros=self._parametros),
            criado_em=agora.isoformat(),
        )
        conta: ContaDeAcesso = self._repositorio.criar(nova)
        token: Token = emitir(TIPO_CONFIRMACAO, agora)
        self._repositorio.anexar_token(
            conta.sub, TIPO_CONFIRMACAO, token.hash, token.expira_em
        )
        self._enviar(conta.email, ASSUNTO_CONFIRMACAO, self._corpo_confirmacao(token.texto or ""))

    def reenviar_confirmacao(self, email: str) -> None:
        """Reenvia o link quando a conta existe e ainda nao confirmou."""
        normalizado: str = self._normalizar(email)
        chave: str = normalizado
        self._limite.exigir("reenvio", chave)
        self._limite.registrar("reenvio", chave)
        if not self._transporte.configurado:
            raise EnvioNaoConfigurado("nao_configurado")
        conta = self._repositorio.por_email(normalizado)
        if conta is None or conta.confirmada:
            return
        agora = self._relogio.agora()
        token = emitir(TIPO_CONFIRMACAO, agora)
        self._repositorio.anexar_token(
            conta.sub, TIPO_CONFIRMACAO, token.hash, token.expira_em
        )
        self._enviar(conta.email, ASSUNTO_CONFIRMACAO, self._corpo_confirmacao(token.texto or ""))

    def confirmar(self, texto_do_token: str) -> ContaDeAcesso | None:
        """Consome o token de confirmacao. `None` cobre invalido, usado e expirado."""
        if not texto_do_token:
            return None
        resultado = self._repositorio.consumir_token(derivar(texto_do_token), self._relogio.agora())
        if resultado is None:
            return None
        sub, tipo = resultado
        if tipo != TIPO_CONFIRMACAO:
            return None
        conta = self._repositorio.por_sub(sub)
        if conta is None:
            return None
        confirmada = conta.confirmar(self._relogio.agora().isoformat())
        self._repositorio.salvar(confirmada)
        return confirmada

    # ---------------------------------------------------------------- internos
    def _normalizar(self, email: str) -> str:
        normalizado: str = normalizar_email(email)
        if not normalizado or "@" not in normalizado or " " in normalizado:
            raise EmailInvalido(email)
        if len(normalizado) > TAMANHO_MAXIMO_DO_EMAIL:
            raise EmailInvalido(email)
        return normalizado

    def _enviar(self, destino: str, assunto: str, corpo: str) -> None:
        try:
            self._transporte.enviar(destino, assunto, corpo)
        except EnvioIndisponivel as erro:
            _log.warning("mensagem de conta nao enviada: %s", erro.motivo)

    def _url(self) -> str:
        return self._url_publica.rstrip("/")

    def _corpo_confirmacao(self, texto: str) -> str:
        return (
            "Para confirmar seu e-mail no Analisador Genealógico, abra o link:\n\n"
            f"{self._url()}/confirmar?token={texto}\n\n"
            "O link vale por 24 horas e só pode ser usado uma vez.\n"
            "Se você não pediu esta conta, ignore esta mensagem.\n"
        )

    def _avisar_conta_existente(self, conta: ContaDeAcesso) -> None:
        caminho_do_google = (
            "\nSe a conta é Google, entre com o Google e use \"Definir senha\" "
            "para passar a entrar com e-mail e senha.\n"
        )
        corpo: str = (
            "Alguém tentou criar uma conta no Analisador Genealógico com este endereço.\n\n"
            f"Se foi você, entre em {self._url()}/login ou recupere a senha em "
            f"{self._url()}/recuperar-senha.\n"
            f"{caminho_do_google}"
            "Nenhuma conta nova foi criada com esta mensagem.\n"
        )
        self._enviar(conta.email, ASSUNTO_CONTA_EXISTENTE, corpo)


__all__: list[str] = [
    "ASSUNTO_CONFIRMACAO",
    "ASSUNTO_CONTA_EXISTENTE",
    "EmailInvalido",
    "ServicoDeCadastro",
]
