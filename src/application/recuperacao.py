"""Recuperacao e redefinicao de senha (feature 053, `RN-08`, `RN-09`, `RN-10`).

## A resposta do pedido nao revela quem tem conta

`pedir` termina igual exista ou nao conta para o e-mail, e so envia quando existe
conta **com credencial** — conta apenas Google nao tem senha para recuperar, e a
tela de recuperacao ja diz o caminho do Google (`RN-07`).

## A senha nova e validada ANTES de o token ser consumido

Senha fraca nao pode queimar o link: o operador corrige a senha e usa o mesmo
token. O consumo vem depois da politica e da repeticao.

## Redefinir revoga as sessoes anteriores

A conta incrementa `versao_de_credencial`; a sessao carrega a versao em que nasceu
e a guarda recusa a antiga (`RN-10`). E o que impede que uma sessao roubada
sobreviva ao "resolvi o problema" do dono.
"""
from __future__ import annotations

import logging

from core.conta import (
    ContaDeAcesso,
    ErroDeConta,
    ParametrosDeDerivacao,
    PoliticaDeSenha,
    SenhasDiferentes,
    derivar_senha,
    normalizar_email,
)
from core.token_de_uso_unico import TIPO_REDEFINICAO, derivar, emitir
from ports import Relogio, RepositorioDeContas, TransporteDeEmail
from ports.email_smtp import EnvioIndisponivel, EnvioNaoConfigurado

from application.limite import Limitador

_log: logging.Logger = logging.getLogger(__name__)

ASSUNTO_REDEFINICAO = "Redefinição de senha — Analisador Genealógico"


class TokenInvalido(ErroDeConta):
    """Token ausente, expirado ou ja usado. As tres recusas sao a mesma tela."""


class ServicoDeRecuperacao:
    """Pedido de link e troca de senha."""

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

    def pedir(self, email: str) -> None:
        """Gera e envia o link quando ha conta com senha; senao, silencio.

        Levanta `EnvioNaoConfigurado` quando nao ha transporte — a tela precisa
        dizer que o envio nao esta configurado, e nao prometer uma mensagem que nao
        sai.
        """
        normalizado: str = normalizar_email(email)
        chave: str = normalizado or "sem-email"
        self._limite.exigir("recuperacao", chave)
        self._limite.registrar("recuperacao", chave)
        if not self._transporte.configurado:
            raise EnvioNaoConfigurado("nao_configurado")
        conta: ContaDeAcesso | None = self._repositorio.por_email(normalizado)
        if conta is None or not conta.tem_senha:
            return
        agora = self._relogio.agora()
        token = emitir(TIPO_REDEFINICAO, agora)
        self._repositorio.anexar_token(conta.sub, TIPO_REDEFINICAO, token.hash, token.expira_em)
        corpo: str = (
            "Para definir uma nova senha no Analisador Genealógico, abra o link:\n\n"
            f"{self._url_publica.rstrip('/')}/redefinir-senha?token={token.texto}\n\n"
            "O link vale por 60 minutos e só pode ser usado uma vez.\n"
            "Se você não pediu a troca, ignore esta mensagem: a senha atual continua valendo.\n"
        )
        try:
            self._transporte.enviar(conta.email, ASSUNTO_REDEFINICAO, corpo)
        except EnvioIndisponivel as erro:
            _log.warning("link de redefinicao nao enviado: %s", erro.motivo)

    def link_valido(self, texto_do_token: str) -> bool:
        """Se o link ainda pode ser aberto, **sem** consumir o token.

        E o que permite o `GET /redefinir-senha` mostrar o formulario ou a mensagem
        de link vencido sem queimar o token de quem so abriu a pagina.
        """
        if not texto_do_token:
            return False
        resultado: tuple[str, str] | None = self._repositorio.token_vigente(derivar(texto_do_token), self._relogio.agora())
        return resultado is not None and resultado[1] == TIPO_REDEFINICAO

    def redefinir(self, texto_do_token: str, senha: str, repeticao: str) -> ContaDeAcesso:
        """Consome o token e troca a senha, incrementando a versao da credencial."""
        if senha != repeticao:
            raise SenhasDiferentes()
        self._politica.exigir(senha)
        if not texto_do_token:
            raise TokenInvalido()
        agora = self._relogio.agora()
        resultado = self._repositorio.consumir_token(derivar(texto_do_token), agora)
        if resultado is None:
            raise TokenInvalido()
        sub, tipo = resultado
        if tipo != TIPO_REDEFINICAO:
            raise TokenInvalido()
        conta: ContaDeAcesso | None = self._repositorio.por_sub(sub)
        if conta is None:
            raise TokenInvalido()
        atualizada: ContaDeAcesso = conta.com_credencial(
            derivar_senha(senha, parametros=self._parametros)
        )
        if not atualizada.confirmada:
            atualizada = atualizada.confirmar(agora.isoformat())
        atualizada = atualizada.com_versao_incrementada()
        self._repositorio.salvar(atualizada)
        return atualizada


__all__: list[str] = ["ASSUNTO_REDEFINICAO", "ServicoDeRecuperacao", "TokenInvalido"]
