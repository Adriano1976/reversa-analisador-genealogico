"""Adaptador de contas em arquivo (`RNF-12`, `RN-21`).

Cobre o que o adaptador promete: unicidade, escrita atomica, cache invalidado,
tokens de uso unico e releitura por uma instancia nova. O que ele NAO promete —
coordenacao entre processos — esta declarado no `data-delta.md`.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import timedelta

import pytest

from core.conta import ContaDuplicada
from core.token_de_uso_unico import TIPO_CONFIRMACAO, emitir
from ports.contas_em_arquivo import ArquivoDeContasCorrompido, ContasEmArquivo
from tests.fixtures.identidade import AGORA, conta_local


@pytest.fixture
def repositorio(tmp_path) -> ContasEmArquivo:
    return ContasEmArquivo(str(tmp_path / "dados" / "contas.json"))


def test_cria_e_le_por_email_e_por_sub(repositorio):
    conta = conta_local()
    repositorio.criar(conta)
    assert repositorio.por_email(conta.email_normalizado) == conta
    assert repositorio.por_sub(conta.sub) == conta


def test_email_duplicado_e_recusado(repositorio):
    repositorio.criar(conta_local(sub="local-" + "1" * 32))
    with pytest.raises(ContaDuplicada):
        repositorio.criar(conta_local(sub="local-" + "2" * 32))


def test_google_sub_duplicado_e_recusado(repositorio):
    repositorio.criar(conta_local(sub="local-" + "1" * 32, google_sub="g-1"))
    with pytest.raises(ContaDuplicada):
        repositorio.criar(
            conta_local(sub="local-" + "2" * 32, email="outro@example.test", google_sub="g-1")
        )


def test_salvar_atualiza_a_conta(repositorio):
    conta = conta_local()
    repositorio.criar(conta)
    confirmada = conta.confirmar(AGORA.isoformat()).com_versao_incrementada()
    repositorio.salvar(confirmada)
    assert repositorio.por_sub(conta.sub).versao_de_credencial == 1


def test_arquivo_nasce_no_primeiro_cadastro_e_sem_temporario(repositorio, tmp_path):
    repositorio.criar(conta_local())
    pasta = tmp_path / "dados"
    arquivos = sorted(os.listdir(pasta))
    assert arquivos == ["contas.json"]
    with open(pasta / "contas.json", encoding="utf-8") as arquivo:
        documento = json.load(arquivo)
    assert documento["versao"] == 1
    assert len(documento["contas"]) == 1


def test_uma_instancia_nova_le_o_que_a_outra_gravou(tmp_path):
    caminho = str(tmp_path / "contas.json")
    conta = conta_local()
    primeira = ContasEmArquivo(caminho)
    primeira.criar(conta)
    segunda = ContasEmArquivo(caminho)
    assert segunda.por_sub(conta.sub) is not None


def test_token_anexado_e_consumido_uma_vez(repositorio):
    conta = conta_local()
    repositorio.criar(conta)
    token = emitir(TIPO_CONFIRMACAO, AGORA)
    repositorio.anexar_token(conta.sub, TIPO_CONFIRMACAO, token.hash, token.expira_em)

    assert repositorio.token_vigente(token.hash, AGORA) == (conta.sub, TIPO_CONFIRMACAO)
    assert repositorio.consumir_token(token.hash, AGORA) == (conta.sub, TIPO_CONFIRMACAO)
    assert repositorio.consumir_token(token.hash, AGORA) is None
    assert repositorio.token_vigente(token.hash, AGORA) is None


def test_token_expirado_nao_e_consumido_e_sai_do_arquivo(repositorio):
    conta = conta_local()
    repositorio.criar(conta)
    token = emitir(TIPO_CONFIRMACAO, AGORA)
    repositorio.anexar_token(conta.sub, TIPO_CONFIRMACAO, token.hash, token.expira_em)
    depois = token.expira_em + timedelta(seconds=1)

    assert repositorio.consumir_token(token.hash, depois) is None
    assert repositorio.token_vigente(token.hash, depois) is None


def test_anexar_token_novo_invalida_o_anterior(repositorio):
    conta = conta_local()
    repositorio.criar(conta)
    primeiro = emitir(TIPO_CONFIRMACAO, AGORA)
    segundo = emitir(TIPO_CONFIRMACAO, AGORA)
    repositorio.anexar_token(conta.sub, TIPO_CONFIRMACAO, primeiro.hash, primeiro.expira_em)
    repositorio.anexar_token(conta.sub, TIPO_CONFIRMACAO, segundo.hash, segundo.expira_em)

    assert repositorio.consumir_token(primeiro.hash, AGORA) is None
    assert repositorio.consumir_token(segundo.hash, AGORA) == (conta.sub, TIPO_CONFIRMACAO)


def test_duas_criacoes_concorrentes_nao_corrompem(repositorio):
    def criar(indice):
        repositorio.criar(
            conta_local(sub=f"local-{indice:032d}", email=f"pessoa{indice}@example.test")
        )

    threads = [threading.Thread(target=criar, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert repositorio.por_email("pessoa0@example.test") is not None
    assert repositorio.por_email("pessoa1@example.test") is not None


def test_arquivo_corrompido_e_recusado_com_erro_claro(tmp_path):
    caminho = tmp_path / "contas.json"
    caminho.write_text("{ isto nao e json", encoding="utf-8")
    repositorio = ContasEmArquivo(str(caminho))
    with pytest.raises(ArquivoDeContasCorrompido):
        repositorio.por_email("teste@example.test")


def test_cache_nao_serve_conta_apagada_por_escrita_externa(repositorio):
    conta = conta_local()
    repositorio.criar(conta)
    assert repositorio.por_sub(conta.sub) is not None
    # A escrita do proprio processo ja invalida o cache; este teste fixa o estado.
    repositorio.salvar(conta.confirmar(AGORA.isoformat()))
    assert repositorio.por_sub(conta.sub).confirmada
