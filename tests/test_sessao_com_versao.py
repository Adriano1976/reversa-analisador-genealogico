"""Versao de credencial e a guarda da sessao (`RN-10`)."""
from __future__ import annotations

from application.sessao_da_conta import VerificadorDeVersao
from tests.fixtures.identidade import ContasEmMemoria, conta_local
from web.sessao import Conta


def test_aceita_quando_a_versao_da_sessao_e_a_atual():
    repositorio = ContasEmMemoria()
    conta = conta_local()
    repositorio.criar(conta)

    assert VerificadorDeVersao(repositorio)(Conta(sub=conta.sub, versao=0))


def test_recusa_sessao_de_versao_anterior():
    repositorio = ContasEmMemoria()
    conta = conta_local()
    repositorio.criar(conta)
    repositorio.salvar(conta.com_versao_incrementada())

    assert not VerificadorDeVersao(repositorio)(Conta(sub=conta.sub, versao=0))
    assert VerificadorDeVersao(repositorio)(Conta(sub=conta.sub, versao=1))


def test_conta_sem_registro_local_e_aceita():
    # Conta so-Google ainda sem linha no arquivo: nao ha versao a comparar.
    assert VerificadorDeVersao(ContasEmMemoria())(Conta(sub="1001"))


def test_falha_do_repositorio_nao_tranca_a_aplicacao():
    repositorio = ContasEmMemoria()
    repositorio.falhar = True

    assert VerificadorDeVersao(repositorio)(Conta(sub="local-x"))


def test_sessao_sem_sub_e_recusada():
    assert not VerificadorDeVersao(ContasEmMemoria())(Conta(sub=""))
