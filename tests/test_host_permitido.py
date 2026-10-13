"""Lista de `Host` aceitos: a defesa contra DNS rebinding (E-02 do adendo 014).

## O que este arquivo prende

O Flask 3.1 recusa a requisicao **antes** de chegar a rota quando o cabecalho `Host` nao esta em
`config["TRUSTED_HOSTS"]`. O que este arquivo mede e **qual lista** libera todo acesso legitimo e
recusa o resto — porque errar para o lado fechado custa o operador perder o acesso, e errar para o
lado aberto nao defende nada.

## O que ele NAO mede, e por que isso importa

Ele nao mede autenticacao, e nada aqui deixa a aplicacao segura para expor. O `Host` e um cabecalho
que qualquer cliente que nao seja navegador forja em uma linha: `curl` com `-H 'Host: localhost'`
entra igual. O que a lista fecha e um vetor de **navegador** — uma pagina hostil que resolve o
proprio dominio para `127.0.0.1` e passa a falar com a aplicacao em mesma origem. Sem sessao e sem
cookie, nao havia nada entre essa pagina e as arvores, os relatorios de DNA e a acao destrutiva.

## A propriedade que mais importa: a PORTA nao participa

`127.0.0.1` sozinho libera `:5000` e `:5080`. E o que faz uma entrada cobrir o acesso local e o do
container ao mesmo tempo — e o defeito de configuracao que uma lista por porta convidaria. Ha teste
proprio para isso.
"""
from __future__ import annotations

import logging
import os
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

VARIAVEL = "ANALISADOR_HOSTS_PERMITIDOS"

#: Os `Host` que TODO acesso legitimo deste projeto envia, e o que cada um representa.
#: Medidos em 2026-10-11 com a lista padrao.
ACEITOS = [
    ("127.0.0.1:5000", "o acesso local, no endereco padrao"),
    ("127.0.0.1:5080", "o container, com a porta publicada pelo compose"),
    ("localhost:5000", "quem digita `localhost` em vez do IP"),
    ("localhost", "sem porta"),
    ("127.0.0.1", "sem porta"),
    ("127.0.0.1:9999", "outra porta qualquer: a PORTA nao participa da comparacao"),
]

#: O `Host` que a lista existe para recusar, e os que ela recusa por consequencia.
RECUSADOS = [
    ("evil.com:5000", "o ataque: o dominio do atacante re-resolvido para 127.0.0.1"),
    ("192.168.1.10:5000", "acesso pelo IP da maquina, que exige a variavel de ambiente"),
    ("genealogia.local:5000", "um nome amigavel, tambem por variavel de ambiente"),
    ("[::1]:5000", "IPv6 literal: consequencia, nao objetivo — ver a nota abaixo"),
]


@pytest.fixture
def cliente(cliente_de_upload):
    _app, cliente_de_teste, _pasta = cliente_de_upload
    return cliente_de_teste


@pytest.mark.parametrize("host,motivo", ACEITOS, ids=[h for h, _ in ACEITOS])
def test_o_acesso_legitimo_passa(cliente, host, motivo):
    assert cliente.get("/", headers={"Host": host}).status_code == 200, (
        f"o Host {host!r} foi recusado ({motivo}): o operador perderia o acesso"
    )


@pytest.mark.parametrize("host,motivo", RECUSADOS, ids=[h for h, _ in RECUSADOS])
def test_o_que_nao_esta_na_lista_e_recusado(cliente, host, motivo):
    assert cliente.get("/", headers={"Host": host}).status_code == 400, (
        f"o Host {host!r} passou ({motivo})"
    )


def test_a_porta_nao_participa_da_comparacao(cliente):
    """A propriedade que evita o pior defeito de configuracao desta lista.

    Uma lista que exigisse a porta obrigaria a manter `127.0.0.1:5000` (local) e
    `127.0.0.1:5080` (container) em sincronia — e a segunda esquecida derruba o acesso ao
    container sem que nada no codigo pareca errado.
    """
    for host in ("127.0.0.1:5000", "127.0.0.1:5080", "127.0.0.1:12345"):
        assert cliente.get("/", headers={"Host": host}).status_code == 200, host


class TestOAlcanceDaRecusa:
    """A recusa e do FLASK, antes da rota: vale para tudo, e nao so para o `GET /`."""

    def test_as_rotas_de_arquivo_tambem_recusam(self, cliente):
        for caminho in ("/app.css", "/banner.png", "/apple-touch-icon.png"):
            assert cliente.get(caminho, headers={"Host": "evil.com:5000"}).status_code == 400, (
                f"{caminho} respondeu a um Host nao confiavel"
            )

    def test_a_acao_destrutiva_tambem_recusa(self, cliente):
        """O caso que da sentido a defesa: aposentar arquivo por uma pagina hostil."""
        recusa = cliente.post(
            "/",
            headers={"Host": "evil.com:5000"},
            data={"action": "aposentar_arquivo", "arquivo_a_aposentar": "x"},
        )
        assert recusa.status_code == 400, (
            "a acao destrutiva aceitou um Host nao confiavel: e exatamente o caminho que o "
            "DNS rebinding exploraria"
        )


class TestODiagnostico:
    """Recusar sem dizer POR QUE transforma um erro de configuracao em 'o app quebrou'."""

    def test_a_pagina_nomeia_o_host_recusado(self, cliente):
        corpo = cliente.get("/", headers={"Host": "192.168.1.10:5000"}).get_data(as_text=True)
        assert "192.168.1.10:5000" in corpo, (
            "a recusa nao diz qual host foi barrado: quem cai nela nao descobre o que corrigir"
        )

    def test_a_recusa_e_registrada_no_log(self, cliente, caplog):
        """A pagina so ajuda quem esta olhando o navegador; o log ajuda quem vem depois."""
        with caplog.at_level(logging.WARNING):
            cliente.get("/", headers={"Host": "evil.com:5000"})

        assert "evil.com:5000" in caplog.text, (
            "a recusa nao deixou rastro no log: o E-02 ficaria sem o unico sinal fora do navegador"
        )


class TestAAmpliacaoPorAmbiente:
    """O acesso que sai do loopback — celular na rede — se resolve sem editar codigo."""

    def test_a_variavel_acrescenta_hosts(self, monkeypatch):
        from app import HOSTS_PERMITIDOS_PADRAO, _hosts_permitidos

        monkeypatch.setenv(VARIAVEL, "192.168.1.10, genealogia.local")
        assert _hosts_permitidos() == list(HOSTS_PERMITIDOS_PADRAO) + [
            "192.168.1.10",
            "genealogia.local",
        ]

    def test_a_variavel_ausente_ou_vazia_nao_muda_nada(self, monkeypatch):
        from app import HOSTS_PERMITIDOS_PADRAO, _hosts_permitidos

        monkeypatch.delenv(VARIAVEL, raising=False)
        assert _hosts_permitidos() == list(HOSTS_PERMITIDOS_PADRAO)

        monkeypatch.setenv(VARIAVEL, "  ,  ")
        assert _hosts_permitidos() == list(HOSTS_PERMITIDOS_PADRAO), (
            "virgula solta ou espaco virou entrada na lista"
        )

    def test_o_host_acrescentado_passa_a_ser_aceito(self, cliente_de_upload, monkeypatch):
        """Prova que a lista lida e a que o Flask usa, e nao uma copia morta."""
        app, cliente_de_teste, _pasta = cliente_de_upload
        recusado = cliente_de_teste.get("/", headers={"Host": "192.168.1.10:5000"})
        assert recusado.status_code == 400, "pre-condicao: o host ainda nao esta na lista"

        monkeypatch.setitem(
            app.config, "TRUSTED_HOSTS", ["127.0.0.1", "localhost", "192.168.1.10"]
        )
        aceito = cliente_de_teste.get("/", headers={"Host": "192.168.1.10:5000"})
        assert aceito.status_code == 200, (
            "trocar `config['TRUSTED_HOSTS']` nao mudou o comportamento: a lista lida nao e a "
            "que o Flask consulta"
        )

    def test_a_lista_padrao_nao_e_vazia(self, cliente_de_upload):
        """`TRUSTED_HOSTS = None` desliga a checagem inteira, em silencio.

        E o valor padrao do Flask: sem esta guarda, alguem poderia "limpar" a configuracao e a
        suite ficaria verde, com a defesa desligada.
        """
        app, _cliente, _pasta = cliente_de_upload
        assert app.config["TRUSTED_HOSTS"], (
            "`TRUSTED_HOSTS` ficou vazio ou None: a checagem de Host esta DESLIGADA"
        )
