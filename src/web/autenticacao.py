"""Entrada pelo provedor de identidade (feature 051).

## O fluxo, e por que ele e feito aqui

OAuth 2.0, authorization code, em tres passos: o navegador vai ao provedor com um
`state` amarrado a sessao; o retorno traz um codigo de uso unico; o **servidor**
troca o codigo pelo token de acesso e le o perfil. O token nunca chega ao navegador.

A implementacao e propria, e nao de biblioteca, por decisao registrada no
`roadmap.md` (`D-03`): as bibliotecas de OAuth arrastam criptografia (JOSE) para
validar `id_token`, e o `id_token` nao e necessario — a identidade vem do endpoint
de perfil, sobre TLS, com um token que so o servidor ve. O que a biblioteca
protegeria aqui e exatamente o que os testes deste modulo prendem.

## O que NUNCA entra em log

Codigo, token, segredo e `state`. `ErroDeEntrada.motivo` e um rotulo curto
(`token_http_400`, `perfil_incompleto`), feito para o log e nao para a tela.
"""
from __future__ import annotations

import importlib.util
import os
import secrets
from dataclasses import dataclass
from urllib.parse import quote, urlencode

from web.sessao import Conta

URL_DE_AUTORIZACAO = "https://accounts.google.com/o/oauth2/v2/auth"
URL_DO_TOKEN = "https://oauth2.googleapis.com/token"
URL_DO_PERFIL = "https://openidconnect.googleapis.com/v1/userinfo"

ESCOPO = "openid email profile"
TEMPO_LIMITE = 10

#: As cinco variaveis exigidas para a entrada funcionar. A ordem e a da mensagem.
VARIAVEIS = (
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "ANALISADOR_SECRET_KEY",
    "ANALISADOR_URL_PUBLICA",
    "ANALISADOR_DONO_INICIAL",
)

PACOTE_DO_TRANSPORTE = "requests"


class ErroDeEntrada(Exception):
    """Falha do fluxo. Carrega um motivo curto, seguro para o log."""

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


@dataclass(frozen=True)
class ConfiguracaoDeEntrada:
    """As cinco variaveis ja validadas, mais a URL de retorno derivada."""

    client_id: str
    client_secret: str
    segredo: str
    url_publica: str
    dono_inicial: str

    @property
    def url_de_retorno(self) -> str:
        """A URL de retorno, fixa. Nunca vem do cabecalho `Host` (`RN-09`)."""
        return f"{self.url_publica.rstrip('/')}/callback"

    @property
    def usa_https(self) -> bool:
        """Se a URL publica e HTTPS, o cookie ganha `Secure`."""
        return self.url_publica.strip().lower().startswith("https://")

    @classmethod
    def do_ambiente(cls, ambiente: dict | None = None):
        """Le o ambiente e devolve `(configuracao, faltantes)`.

        `faltantes` vazio significa configuracao completa. A funcao e pura o
        bastante para o teste passar um dicionario no lugar do `os.environ`.
        """
        valores = os.environ if ambiente is None else ambiente
        faltantes: list[str] = [nome for nome in VARIAVEIS if not (valores.get(nome) or "").strip()]
        if faltantes:
            return None, faltantes
        return (
            cls(
                client_id=valores["GOOGLE_CLIENT_ID"].strip(),
                client_secret=valores["GOOGLE_CLIENT_SECRET"].strip(),
                segredo=valores["ANALISADOR_SECRET_KEY"].strip(),
                url_publica=valores["ANALISADOR_URL_PUBLICA"].strip(),
                dono_inicial=valores["ANALISADOR_DONO_INICIAL"].strip(),
            ),
            [],
        )


def _pedir_por_requests(metodo: str, url: str, **kwargs):
    """O transporte real: `requests`, importado AQUI (padrao `L-26`).

    O pacote nao publica stubs (`types-requests` e pacote de desenvolvimento, nao
    dependencia de runtime), entao o aviso do checador e esperado aqui — o mesmo
    caso do `waitress` em `src/app.py`, e pelo mesmo motivo.
    """
    import requests  # pyrefly: ignore[untyped-import] - sem stubs publicados

    with requests.request(metodo, url, timeout=TEMPO_LIMITE, **kwargs) as resposta:
        try:
            corpo = resposta.json()
        except ValueError:
            corpo = {}
        return resposta.status_code, corpo


class ProvedorGoogle:
    """O lado de saida do fluxo: URL de autorizacao, troca do codigo e perfil."""

    def __init__(self, configuracao: ConfiguracaoDeEntrada, pedir=None) -> None:
        self._configuracao: ConfiguracaoDeEntrada = configuracao
        self._pedir = pedir or _pedir_por_requests

    def novo_state(self) -> str:
        """32 bytes de entropia, url-safe: o valor que amarra o retorno a sessao."""
        return secrets.token_urlsafe(32)

    def url_de_autorizacao(self, state: str) -> str:
        """A URL do consentimento, com a URL de retorno fixa da configuracao."""
        parametros: dict[str, str] = {
            "client_id": self._configuracao.client_id,
            "redirect_uri": self._configuracao.url_de_retorno,
            "response_type": "code",
            "scope": ESCOPO,
            "state": state,
            "access_type": "online",
        }
        return f"{URL_DE_AUTORIZACAO}?{urlencode(parametros, quote_via=quote)}"

    def trocar_codigo(self, codigo: str) -> str:
        """Troca o codigo pelo token de acesso. Devolve o token, que nao e logado."""
        dados: dict[str, str] = {
            "code": codigo,
            "client_id": self._configuracao.client_id,
            "client_secret": self._configuracao.client_secret,
            "redirect_uri": self._configuracao.url_de_retorno,
            "grant_type": "authorization_code",
        }
        try:
            status, corpo = self._pedir("POST", URL_DO_TOKEN, data=dados)
        except Exception as erro:  # rede, DNS, TLS, tempo esgotado
            raise ErroDeEntrada(f"rede_{type(erro).__name__}") from erro
        if status != 200 or not (corpo or {}).get("access_token"):
            raise ErroDeEntrada(f"token_http_{status}")
        return str(corpo["access_token"])

    def ler_perfil(self, token: str) -> Conta:
        """Le `sub`, e-mail e nome no endpoint de perfil."""
        try:
            status, corpo = self._pedir(
                "GET", URL_DO_PERFIL, headers={"Authorization": f"Bearer {token}"}
            )
        except Exception as erro:
            raise ErroDeEntrada(f"rede_{type(erro).__name__}") from erro
        if status != 200:
            raise ErroDeEntrada(f"perfil_http_{status}")
        corpo = corpo or {}
        sub: str = str(corpo.get("sub") or "").strip()
        email: str = str(corpo.get("email") or "").strip()
        if not sub or not email:
            raise ErroDeEntrada("perfil_incompleto")
        if corpo.get("email_verified") is not True:
            raise ErroDeEntrada("email_nao_verificado")
        return Conta(sub=sub, email=email, nome=str(corpo.get("name") or "").strip())


class ServicoDeEntrada:
    """O que a borda consome: a configuracao e o provedor, juntos."""

    def __init__(self, configuracao: ConfiguracaoDeEntrada, provedor: ProvedorGoogle) -> None:
        self.configuracao = configuracao
        self.provedor = provedor

    def entrar(self, codigo: str) -> Conta:
        """Do codigo a conta: troca e perfil, nesta ordem."""
        return self.provedor.ler_perfil(self.provedor.trocar_codigo(codigo))


def servico_do_ambiente(ambiente: dict | None = None):
    """Monta o servico, ou devolve `(None, faltantes)` para a subida recusar.

    A ausencia do pacote de transporte entra na MESMA lista: com a entrada ligada,
    subir sem ele daria erro na primeira troca de codigo, e nao na subida.
    """
    configuracao, faltantes = ConfiguracaoDeEntrada.do_ambiente(ambiente)
    if configuracao is None:
        # A checagem e pelo valor, e nao pela lista: e o que estreita o tipo para o
        # checador, e o contrato de `do_ambiente` garante que um vem com o outro.
        return None, faltantes
    if importlib.util.find_spec(PACOTE_DO_TRANSPORTE) is None:
        return None, [
            f"o pacote {PACOTE_DO_TRANSPORTE} "
            "(instale com: python -m pip install -r requirements.txt)"
        ]
    return ServicoDeEntrada(configuracao, ProvedorGoogle(configuracao)), []


__all__: list[str] = [
    "ConfiguracaoDeEntrada",
    "ErroDeEntrada",
    "ProvedorGoogle",
    "ServicoDeEntrada",
    "servico_do_ambiente",
]
