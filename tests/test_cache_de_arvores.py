"""Prova do cache da árvore (`ANALISADOR_CACHE_DE_ARVORE`).

## O que este arquivo protege

O cache nasceu para remover o parse de ~50 s que se repetia a cada `POST`. Ele está **ligado por
padrão**: sem a variável de ambiente, a segunda carga vem do cache. O comportamento antigo — um
parse por chamada — volta apenas quando o operador desliga explicitamente (`0`, `false`, `nao`,
`off`, `no`).

As provas cobrem as duas metades — desligado parseia a cada chamada, ligado devolve a MESMA árvore
e parseia uma vez — e as bordas: arquivo trocado invalida, teto de capacidade despeja o mais
antigo, referência inexistente devolve `None` sem parsear e quatro threads não pagam quatro
parses.

## Por que a contagem de chamadas, e não o relógio

O projeto já registrou dois instrumentos de desempenho que mediram a coisa errada (`OBS-22` e
`OBS-23`). Cronometrar aqui tornaria o teste dependente da máquina; contar `carregar_arvore` mede
a decisão que o cache toma, que é o que pode regredir.
"""
import os
import sys
import threading
import time

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

import pytest

from application import nomes_de_exibicao
from ports import adaptadores
from ports.adaptadores import (
    VARIAVEL_DO_CACHE,
    VARIAVEL_DA_CAPACIDADE,
    ArmazenamentoEmDisco,
    CacheDeArvores,
    CarregadorDeArvoresGedcom,
)

GEDCOM_A = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Ana /Lima/\n"
    "0 TRLR\n"
)

GEDCOM_B = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Bia /Rocha/\n"
    "1 SEX F\n"
    "0 TRLR\n"
)

DONO = "dono"


class _ArmazenamentoDeUmArquivo:
    """Armazenamento mínimo que resolve qualquer referência para UM caminho.

    Existe para os testes de invalidação e de capacidade, que precisam escrever por cima do
    arquivo — coisa que `ArmazenamentoEmDisco` não permite, porque o nome dele é derivado do
    conteúdo.
    """

    def __init__(self, caminho: str):
        self.caminho = caminho

    def resolver(self, referencia, dono):
        return self.caminho if os.path.exists(self.caminho) else None


@pytest.fixture
def contador(monkeypatch):
    """Conta as chamadas reais ao parser, delegando para o parser verdadeiro."""
    chamadas = {"n": 0}
    original = adaptadores.carregar_arvore

    def contar(caminho):
        chamadas["n"] += 1
        return original(caminho)

    monkeypatch.setattr(adaptadores, "carregar_arvore", contar)
    return chamadas


def _armazenar(pasta, conteudo: bytes, nome: str = "a.ged"):
    """Grava pelo caminho real e devolve `(armazenamento, referencia)`."""
    armazenamento = ArmazenamentoEmDisco(str(pasta))
    caminho, motivo = armazenamento.guardar(conteudo, nome, "gedcom", DONO)
    assert motivo is None, f"o GEDCOM de teste foi recusado: {motivo}"
    return armazenamento, os.path.basename(caminho)


class TestLigadoPorPadrao:
    """Sem a variável, o adaptador tem de usar o cache; vazio também conta como ligado."""

    def test_sem_a_variavel_usa_o_cache(self, tmp_path, monkeypatch, contador):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        armazenamento, referencia = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))
        carregador = CarregadorDeArvoresGedcom(armazenamento)

        primeira = carregador.carregar(referencia, DONO)
        segunda = carregador.carregar(referencia, DONO)

        assert contador["n"] == 1, "sem a variável, a segunda carga tinha de vir do cache"
        assert primeira is segunda, "o cache tem de devolver a MESMA árvore"
        assert nomes_de_exibicao(segunda) == ["Ana Lima"]

    def test_valor_vazio_mantem_ligado(self, tmp_path, monkeypatch, contador):
        """`VAR=` no ambiente é um `export` sem valor, não uma intenção de desligar."""
        monkeypatch.setenv(VARIAVEL_DO_CACHE, "")
        armazenamento, referencia = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))
        carregador = CarregadorDeArvoresGedcom(armazenamento)

        carregador.carregar(referencia, DONO)
        carregador.carregar(referencia, DONO)

        assert contador["n"] == 1

    def test_a_variavel_um_tambem_liga(self, tmp_path, monkeypatch, contador):
        monkeypatch.setenv(VARIAVEL_DO_CACHE, "1")
        armazenamento, referencia = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))
        carregador = CarregadorDeArvoresGedcom(armazenamento)

        primeira = carregador.carregar(referencia, DONO)
        segunda = carregador.carregar(referencia, DONO)

        assert contador["n"] == 1, "a segunda carga tinha de vir do cache"
        assert primeira is segunda, "o cache tem de devolver a MESMA árvore"
        assert nomes_de_exibicao(segunda) == ["Ana Lima"]

    def test_referencia_inexistente_nao_parseia(self, tmp_path, monkeypatch, contador):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        armazenamento = ArmazenamentoEmDisco(str(tmp_path))
        carregador = CarregadorDeArvoresGedcom(armazenamento, cache=CacheDeArvores())

        assert carregador.carregar("0" * 16 + "__nao_existe.ged", DONO) is None
        assert contador["n"] == 0


class TestDesligadoPelaVariavel:
    @pytest.mark.parametrize("valor", ["0", "nao", "false", "off", "no"])
    def test_valores_que_desligam(self, valor, tmp_path, monkeypatch, contador):
        monkeypatch.setenv(VARIAVEL_DO_CACHE, valor)
        armazenamento, referencia = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))
        carregador = CarregadorDeArvoresGedcom(armazenamento)

        carregador.carregar(referencia, DONO)
        carregador.carregar(referencia, DONO)

        assert contador["n"] == 2


class TestConfiguracaoDoCache:
    def test_cache_injetado_dispensa_a_variavel(self, tmp_path, monkeypatch, contador):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        armazenamento, referencia = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))
        cache = CacheDeArvores()
        carregador = CarregadorDeArvoresGedcom(armazenamento, cache=cache)

        carregador.carregar(referencia, DONO)
        carregador.carregar(referencia, DONO)

        assert contador["n"] == 1
        assert len(cache) == 1

    def test_capacidade_vem_do_ambiente(self, tmp_path, monkeypatch):
        monkeypatch.setenv(VARIAVEL_DO_CACHE, "1")
        monkeypatch.setenv(VARIAVEL_DA_CAPACIDADE, "2")
        armazenamento, _ = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))
        carregador = CarregadorDeArvoresGedcom(armazenamento)

        assert carregador._cache.capacidade == 2

    def test_capacidade_invalida_no_ambiente_cai_no_padrao(self, tmp_path, monkeypatch):
        monkeypatch.setenv(VARIAVEL_DO_CACHE, "1")
        monkeypatch.setenv(VARIAVEL_DA_CAPACIDADE, "zero")
        armazenamento, _ = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))

        assert CarregadorDeArvoresGedcom(armazenamento)._cache.capacidade == 1


class TestInvalidacao:
    def test_arquivo_trocado_no_mesmo_caminho_forca_novo_parse(self, tmp_path, monkeypatch, contador):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        caminho = tmp_path / "arvore.ged"
        caminho.write_bytes(GEDCOM_A.encode("utf-8"))
        carregador = CarregadorDeArvoresGedcom(
            _ArmazenamentoDeUmArquivo(str(caminho)), cache=CacheDeArvores())

        primeira = carregador.carregar("qualquer", DONO)
        caminho.write_bytes(GEDCOM_B.encode("utf-8"))
        # `mtime_ns` tem de mudar mesmo em disco com resolução grosseira de tempo.
        os.utime(caminho, ns=(0, 0))

        segunda = carregador.carregar("qualquer", DONO)

        assert contador["n"] == 2, "trocar o conteúdo do arquivo tem de invalidar a entrada"
        assert nomes_de_exibicao(primeira) == ["Ana Lima"]
        assert nomes_de_exibicao(segunda) == ["Bia Rocha"]

    def test_capacidade_um_despeja_o_mais_antigo(self, tmp_path, monkeypatch, contador):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        armazenamento = ArmazenamentoEmDisco(str(tmp_path))
        _, ref_a = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"), "a.ged")
        _, ref_b = _armazenar(tmp_path, GEDCOM_B.encode("utf-8"), "b.ged")
        carregador = CarregadorDeArvoresGedcom(armazenamento, cache=CacheDeArvores(capacidade=1))

        carregador.carregar(ref_a, DONO)
        carregador.carregar(ref_b, DONO)
        carregador.carregar(ref_a, DONO)

        assert contador["n"] == 3, "com teto 1, a volta para a primeira árvore reparseia"

    def test_capacidade_dois_mantem_as_duas(self, tmp_path, monkeypatch, contador):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        armazenamento = ArmazenamentoEmDisco(str(tmp_path))
        _, ref_a = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"), "a.ged")
        _, ref_b = _armazenar(tmp_path, GEDCOM_B.encode("utf-8"), "b.ged")
        carregador = CarregadorDeArvoresGedcom(armazenamento, cache=CacheDeArvores(capacidade=2))

        carregador.carregar(ref_a, DONO)
        carregador.carregar(ref_b, DONO)
        carregador.carregar(ref_a, DONO)

        assert contador["n"] == 2

    def test_capacidade_invalida_e_recusada(self):
        with pytest.raises(ValueError):
            CacheDeArvores(capacidade=0)


class TestConcorrencia:
    def test_quatro_threads_pagam_um_parse_so(self, tmp_path, monkeypatch):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        caminho = tmp_path / "arvore.ged"
        caminho.write_bytes(GEDCOM_A.encode("utf-8"))
        original = adaptadores.carregar_arvore
        chamadas = {"n": 0}
        trava = threading.Lock()

        def lento(caminho_arg):
            with trava:
                chamadas["n"] += 1
            time.sleep(0.2)
            return original(caminho_arg)

        monkeypatch.setattr(adaptadores, "carregar_arvore", lento)
        carregador = CarregadorDeArvoresGedcom(
            _ArmazenamentoDeUmArquivo(str(caminho)), cache=CacheDeArvores())

        barreira = threading.Barrier(4)
        resultados = []

        def atender():
            barreira.wait()
            resultados.append(carregador.carregar("qualquer", DONO))

        threads = [threading.Thread(target=atender) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert chamadas["n"] == 1, "as quatro requisições pagaram mais de um parse"
        assert len(resultados) == 4
        assert all(arvore is resultados[0] for arvore in resultados)


class TestObservabilidade:
    def test_o_log_conta_acerto_e_reconstrucao_sem_dado_pessoal(self, tmp_path, monkeypatch, caplog):
        monkeypatch.delenv(VARIAVEL_DO_CACHE, raising=False)
        armazenamento, referencia = _armazenar(tmp_path, GEDCOM_A.encode("utf-8"))
        carregador = CarregadorDeArvoresGedcom(armazenamento, cache=CacheDeArvores())

        with caplog.at_level("INFO", logger=adaptadores.__name__):
            carregador.carregar(referencia, DONO)
            carregador.carregar(referencia, DONO)

        texto = " ".join(registro.getMessage() for registro in caplog.records)
        assert "reconstrucao" in texto
        assert "acerto" in texto
        assert "Ana" not in texto and "Lima" not in texto
        assert "@I1@" not in texto
