"""Credencial: derivacao, sal e comparacao (`RN-04`).

O teste usa parametros baratos (`n=1024`): o caminho e o MESMO da producao, e o
que muda e o custo. Um teste que derive com `n=2**14` a cada caso pagaria segundos
por nada.
"""
from __future__ import annotations

from core.conta import (
    Credencial,
    ParametrosDeDerivacao,
    conferir_senha,
    credencial_falsa,
    derivar_senha,
)

PARAMETROS = ParametrosDeDerivacao(n=1024, r=8, p=1)
SENHA = "Senha#2026"


def test_deriva_e_confere_a_mesma_senha():
    credencial = derivar_senha(SENHA, parametros=PARAMETROS)
    assert conferir_senha(SENHA, credencial)


def test_senha_errada_nao_confere():
    credencial = derivar_senha(SENHA, parametros=PARAMETROS)
    assert not conferir_senha("Senha#2027", credencial)


def test_o_sal_muda_a_cada_derivacao():
    uma = derivar_senha(SENHA, parametros=PARAMETROS)
    outra = derivar_senha(SENHA, parametros=PARAMETROS)
    assert uma.sal != outra.sal
    assert uma.hash != outra.hash


def test_o_sal_pedido_deixa_a_derivacao_deterministica():
    uma = derivar_senha(SENHA, parametros=PARAMETROS, sal=b"0" * 16)
    outra = derivar_senha(SENHA, parametros=PARAMETROS, sal=b"0" * 16)
    assert uma == outra


def test_os_parametros_ficam_gravados_junto_do_hash():
    credencial = derivar_senha(SENHA, parametros=PARAMETROS)
    assert credencial.algoritmo == "scrypt"
    assert (credencial.n, credencial.r, credencial.p) == (1024, 8, 1)


def test_credencial_serializa_e_volta_igual():
    credencial = derivar_senha(SENHA, parametros=PARAMETROS)
    voltou = Credencial.de_dicionario(credencial.para_dicionario())
    assert voltou == credencial
    assert conferir_senha(SENHA, voltou)


def test_credencial_incompleta_e_recusada_na_leitura():
    try:
        Credencial.de_dicionario({"algoritmo": "scrypt"})
    except ValueError as erro:
        assert "credencial incompleta" in str(erro)
    else:
        raise AssertionError("credencial incompleta deveria falhar")


def test_senha_com_acento_confere():
    senha = "Açúcar#2026"
    credencial = derivar_senha(senha, parametros=PARAMETROS)
    assert conferir_senha(senha, credencial)
    assert not conferir_senha("Acucar#2026", credencial)


def test_credencial_ausente_nunca_confere():
    assert not conferir_senha(SENHA, None)


def test_credencial_falsa_nao_confere_a_senha_real():
    falsa = credencial_falsa(PARAMETROS)
    assert not conferir_senha(SENHA, falsa)
    assert falsa.n == 1024, "a falsa tem que ter o mesmo custo"


def test_algoritmo_desconhecido_nunca_confere():
    credencial = Credencial(algoritmo="md5", n=1024, r=8, p=1, sal="", hash="")
    assert not conferir_senha(SENHA, credencial)
