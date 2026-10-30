"""Dubles da identidade local (feature 053).

A suite nao escreve no arquivo real de contas, nao fala com SMTP e nao espera o
relogio: as tres dependencias externas da feature entram pelas portas, e estes
tres objetos sao as implementacoes de teste.

## Por que o relogio e um duble, e nao `freezegun`

`Relogio` e uma porta da aplicacao (`ports/__init__.py`). Injetar o duble exercita
o **mesmo caminho** que a producao usa, e o teste de expiracao vira deterministico
sem biblioteca extra — o projeto nao adiciona dependencia para testar tempo.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from core.conta import (
    ContaDeAcesso,
    ContaDuplicada,
    ParametrosDeDerivacao,
    derivar_senha,
)
from ports.email_smtp import EnvioIndisponivel

#: Parametros baratos: mesmo algoritmo, custo de teste.
PARAMETROS_DE_TESTE = ParametrosDeDerivacao(n=1024, r=8, p=1)

#: O instante que os testes usam como "agora".
AGORA = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)


class RelogioFalso:
    """Relogio que anda quando o teste manda."""

    def __init__(self, agora: datetime | None = None) -> None:
        self._agora = agora or AGORA

    def agora(self) -> datetime:
        return self._agora

    def avancar(self, **delta) -> datetime:
        self._agora = self._agora + timedelta(**delta)
        return self._agora


class EmailQueGrava:
    """Transporte que guarda as mensagens em memoria, no lugar de enviar."""

    configurado = True

    def __init__(self) -> None:
        self.mensagens: list[dict] = []

    def enviar(self, destino: str, assunto: str, corpo: str) -> None:
        self.mensagens.append({"destino": destino, "assunto": assunto, "corpo": corpo})

    def ultimo_corpo(self) -> str:
        return self.mensagens[-1]["corpo"] if self.mensagens else ""

    def ultimo_destino(self) -> str:
        return self.mensagens[-1]["destino"] if self.mensagens else ""


class EmailDesligado:
    """Transporte nulo: a instalacao sem SMTP configurado."""

    configurado = False

    def __init__(self) -> None:
        self.tentativas: int = 0

    def enviar(self, destino: str, assunto: str, corpo: str) -> None:
        self.tentativas += 1
        raise EnvioIndisponivel("nao_configurado")


class ContasEmMemoria:
    """`RepositorioDeContas` em dicionario, com a mesma semantica do arquivo."""

    def __init__(self, relogio: RelogioFalso | None = None) -> None:
        self._contas: dict[str, ContaDeAcesso] = {}
        self._tokens: dict[str, dict] = {}
        self.relogio = relogio or RelogioFalso()
        #: Quando verdadeiro, toda operacao levanta: exercita o caminho best-effort.
        self.falhar = False

    def _conferir_saude(self) -> None:
        if self.falhar:
            raise OSError("repositorio indisponivel de proposito")

    def criar(self, conta: ContaDeAcesso) -> ContaDeAcesso:
        self._conferir_saude()
        if self.por_email(conta.email_normalizado) is not None:
            raise ContaDuplicada(conta.email_normalizado)
        if conta.google_sub and self.por_google_sub(conta.google_sub) is not None:
            raise ContaDuplicada(conta.google_sub)
        self._contas[conta.sub] = conta
        return conta

    def por_email(self, email_normalizado: str) -> ContaDeAcesso | None:
        self._conferir_saude()
        for conta in self._contas.values():
            if conta.email_normalizado == email_normalizado:
                return conta
        return None

    def por_sub(self, sub: str) -> ContaDeAcesso | None:
        self._conferir_saude()
        return self._contas.get(sub)

    def por_google_sub(self, google_sub: str) -> ContaDeAcesso | None:
        self._conferir_saude()
        for conta in self._contas.values():
            if conta.google_sub == google_sub:
                return conta
        return None

    def salvar(self, conta: ContaDeAcesso) -> None:
        self._conferir_saude()
        self._contas[conta.sub] = conta

    def anexar_token(self, sub: str, tipo: str, hash_token: str,
                     expira_em: datetime) -> None:
        self._conferir_saude()
        conta = self._contas[sub]
        campo = "token_confirmacao" if tipo == "confirmacao" else "token_redefinicao"
        anterior = getattr(conta, campo)
        if anterior:
            self._tokens.pop(anterior, None)
        self._tokens[hash_token] = {"sub": sub, "tipo": tipo, "expira_em": expira_em}
        self._contas[sub] = replace(conta, **{campo: hash_token})

    def consumir_token(self, hash_token: str, agora: datetime):
        self._conferir_saude()
        registro = self._tokens.pop(hash_token, None)
        if registro is None:
            return None
        conta = self._contas[registro["sub"]]
        campo = ("token_confirmacao" if registro["tipo"] == "confirmacao"
                 else "token_redefinicao")
        self._contas[conta.sub] = replace(conta, **{campo: None})
        if registro["expira_em"] <= agora:
            return None
        return registro["sub"], registro["tipo"]

    def token_vigente(self, hash_token: str, agora: datetime):
        self._conferir_saude()
        registro = self._tokens.get(hash_token)
        if registro is None or registro["expira_em"] <= agora:
            return None
        return registro["sub"], registro["tipo"]

    # Helpers de teste, fora da porta.
    def quantidade(self) -> int:
        return len(self._contas)

    def tem_token(self, hash_token: str) -> bool:
        return hash_token in self._tokens


def token_do_corpo(corpo: str) -> str:
    """Extrai o valor de `token=` de um link de e-mail."""
    import re

    achado = re.search(r"[?&]token=([A-Za-z0-9_\-]+)", corpo or "")
    return achado.group(1) if achado else ""


def cadastrar_e_confirmar(app, email: str = "teste@example.test",
                          senha: str = "Senha#2026") -> dict:
    """Percorre cadastro, le o link no e-mail e confirma. Devolve os corpos."""
    resposta = app.cliente.post(
        "/cadastro",
        data={"email": email, "senha": senha, "repeticao": senha},
    )
    corpo_do_email = app.email.ultimo_corpo()
    token = token_do_corpo(corpo_do_email)
    confirmacao = app.cliente.get(f"/confirmar?token={token}")
    return {
        "cadastro": resposta.get_data(as_text=True),
        "token": token,
        "confirmacao": confirmacao.get_data(as_text=True),
    }


def entrar_com_senha(app, email: str = "teste@example.test",
                     senha: str = "Senha#2026"):
    """`POST /login` com credencial local."""
    return app.cliente.post("/login", data={"email": email, "senha": senha})


def conta_local(
    *,
    email: str = "teste@example.test",
    senha: str = "Senha#2026",
    verificado: bool = True,
    sub: str = "local-" + "0" * 32,
    google_sub: str | None = None,
) -> ContaDeAcesso:
    """Uma conta pronta, com credencial derivada pelos parametros de teste."""
    return ContaDeAcesso(
        sub=sub,
        email=email,
        email_normalizado=email.strip().casefold(),
        credencial=derivar_senha(senha, parametros=PARAMETROS_DE_TESTE),
        google_sub=google_sub,
        nome="Conta de teste",
        verificado_em=AGORA.isoformat() if verificado else None,
        criado_em=AGORA.isoformat(),
        versao_de_credencial=0,
    )
