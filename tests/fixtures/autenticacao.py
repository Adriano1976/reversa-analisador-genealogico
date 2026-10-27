"""Provedor de identidade falso e helpers de sessao (feature 051).

A suite **nao fala com a rede**: o fluxo OAuth e exercitado com um provedor em
memoria, que devolve a conta que o teste registrou. O `state` e fixo e de uso
unico, como no contrato real.
"""
from __future__ import annotations

from web.autenticacao import ConfiguracaoDeEntrada, ErroDeEntrada, ServicoDeEntrada
from web.sessao import CHAVE_DO_STATE, Conta

CONTA_A = Conta(sub="1001", email="a@example.test", nome="Conta A")
CONTA_B = Conta(sub="1002", email="b@example.test", nome="Conta B")

ESTADO_DE_TESTE = "estado-de-teste"


class ProvedorFalso:
    """O provedor, em memoria: codigo entra, conta sai."""

    def __init__(self) -> None:
        self.contas: dict[str, Conta] = {}
        self.falhar_na_troca = False

    def novo_state(self) -> str:
        return ESTADO_DE_TESTE

    def url_de_autorizacao(self, state: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state}"

    def trocar_codigo(self, codigo: str) -> str:
        if self.falhar_na_troca:
            raise ErroDeEntrada("token_http_400")
        if codigo not in self.contas:
            raise ErroDeEntrada("codigo_desconhecido")
        return codigo

    def ler_perfil(self, token: str) -> Conta:
        if token not in self.contas:
            raise ErroDeEntrada("codigo_desconhecido")
        return self.contas[token]


def servico_de_teste(provedor: ProvedorFalso | None = None,
                     dono_inicial: str = CONTA_A.email) -> ServicoDeEntrada:
    """Um servico pronto, com a configuracao minima que a entrada exige."""
    configuracao = ConfiguracaoDeEntrada(
        client_id="cliente-de-teste",
        client_secret="segredo-de-teste",
        segredo="chave-de-sessao-de-teste",
        url_publica="http://127.0.0.1:5000",
        dono_inicial=dono_inicial,
    )
    return ServicoDeEntrada(configuracao, provedor or ProvedorFalso())


def entrar_como(cliente, provedor: ProvedorFalso, conta: Conta):
    """Percorre o fluxo de entrada com o provedor falso e devolve a resposta do callback."""
    codigo = f"codigo-{conta.sub}"
    provedor.contas[codigo] = conta
    with cliente.session_transaction() as sessao:
        sessao[CHAVE_DO_STATE] = ESTADO_DE_TESTE
    return cliente.get(f"/callback?state={ESTADO_DE_TESTE}&code={codigo}")
