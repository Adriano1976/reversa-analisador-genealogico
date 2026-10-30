"""Transporte de e-mail por SMTP, e o transporte nulo (feature 053, `D-07`).

## Por que biblioteca padrao, e por que import preguicoso

`smtplib` e `email.message` estao na biblioteca padrao: nenhuma dependencia nova
(`RNF-11`). O import fica no topo mesmo assim porque `smtplib` e barato; o que o
projeto evita e empacotar cliente de e-mail de terceiro.

## O que este modulo NUNCA faz

- Nao registra destinatario, assunto, corpo nem credencial. O motivo da falha e um
  rotulo curto (`smtp_timeout`, `smtp_autenticacao`, `smtp_recusado`), do tamanho
  de um `ErroDeEntrada.motivo`.
- Nao tenta de novo sozinho: um segundo envio seria um segundo e-mail. O reenvio e
  ato explicito do operador na tela.

## Sem transporte, o resto continua

`transporte_do_ambiente` devolve `TransporteNulo` quando faltam `HOST` ou
`REMETENTE`. A instancia sobe, o login de conta confirmada funciona e as telas que
dependem de envio avisam (`RN-18`).
"""
from __future__ import annotations
from typing import Any

import os
import smtplib
from email.message import EmailMessage

#: Tempo limite por envio, em segundos. Mesmo numero do `TEMPO_LIMITE` da 051.
TEMPO_LIMITE = 10

VARIAVEIS = (
    "ANALISADOR_SMTP_HOST",
    "ANALISADOR_SMTP_PORT",
    "ANALISADOR_SMTP_USUARIO",
    "ANALISADOR_SMTP_SENHA",
    "ANALISADOR_SMTP_REMETENTE",
    "ANALISADOR_SMTP_SEGURANCA",
)


class EnvioIndisponivel(RuntimeError):
    """O envio foi tentado e falhou. Carrega um motivo curto, seguro para o log."""

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)


class EnvioNaoConfigurado(EnvioIndisponivel):
    """Nao ha transporte configurado; o cadastro e a recuperacao avisam."""


class TransporteNulo:
    """O transporte de uma instalacao sem SMTP. `configurado` e `False`."""

    configurado = False

    def enviar(self, destino: str, assunto: str, corpo: str) -> None:
        raise EnvioNaoConfigurado("nao_configurado")


class EmailPorSmtp:
    """SMTP autenticado, com `starttls` por padrao."""

    configurado = True

    def __init__(
        self,
        host: str,
        remetente: str,
        *,
        porta: int = 587,
        usuario: str = "",
        senha: str = "",
        seguranca: str = "starttls",
    ) -> None:
        self._host: str = host
        self._remetente: str = remetente
        self._porta: int = porta
        self._usuario: str = usuario
        self._senha: str = senha
        self._seguranca: str = seguranca.strip().lower() or "starttls"

    def enviar(self, destino: str, assunto: str, corpo: str) -> None:
        mensagem: EmailMessage = EmailMessage()
        mensagem["From"] = self._remetente
        mensagem["To"] = destino
        mensagem["Subject"] = assunto
        mensagem.set_content(corpo, subtype="plain", charset="utf-8")
        try:
            if self._seguranca == "ssl":
                transporte = smtplib.SMTP_SSL(self._host, self._porta, timeout=TEMPO_LIMITE)
            else:
                transporte = smtplib.SMTP(self._host, self._porta, timeout=TEMPO_LIMITE)
            with transporte:
                if self._seguranca == "starttls":
                    transporte.starttls()
                if self._usuario:
                    transporte.login(self._usuario, self._senha)
                transporte.send_message(mensagem)
        except smtplib.SMTPAuthenticationError as erro:
            raise EnvioIndisponivel("smtp_autenticacao") from erro
        except smtplib.SMTPRecipientsRefused as erro:
            raise EnvioIndisponivel("smtp_destinatario_recusado") from erro
        except smtplib.SMTPException as erro:
            raise EnvioIndisponivel(f"smtp_{type(erro).__name__}") from erro
        except TimeoutError as erro:
            raise EnvioIndisponivel("smtp_timeout") from erro
        except OSError as erro:
            raise EnvioIndisponivel(f"rede_{type(erro).__name__}") from erro


def transporte_do_ambiente(ambiente: dict[str, Any] | None = None) -> TransporteNulo | EmailPorSmtp:
    """Monta o transporte a partir do ambiente; nunca levanta.

    Sem `HOST` ou `REMETENTE`, devolve o nulo. A subida continua: o envio e canal
    de confirmacao e recuperacao, e nao de entrada (`RN-18`).
    """
    valores: os._Environ[str] | dict[str, Any] = os.environ if ambiente is None else ambiente
    host: str | Any = (valores.get("ANALISADOR_SMTP_HOST") or "").strip()
    remetente: str | Any = (valores.get("ANALISADOR_SMTP_REMETENTE") or "").strip()
    if not host or not remetente:
        return TransporteNulo()
    porta: str | Any = (valores.get("ANALISADOR_SMTP_PORT") or "587").strip()
    try:
        porta_int: int = int(porta)
    except ValueError:
        porta_int = 587
    return EmailPorSmtp(
        host,
        remetente,
        porta=porta_int,
        usuario=(valores.get("ANALISADOR_SMTP_USUARIO") or "").strip(),
        senha=(valores.get("ANALISADOR_SMTP_SENHA") or "").strip(),
        seguranca=(valores.get("ANALISADOR_SMTP_SEGURANCA") or "starttls").strip(),
    )


__all__: list[str] = [
    "EmailPorSmtp",
    "EnvioIndisponivel",
    "EnvioNaoConfigurado",
    "TEMPO_LIMITE",
    "TransporteNulo",
    "transporte_do_ambiente",
]
