"""A adocao dos dados anteriores a identidade (feature 051, `RN-15`).

Testa a rotina pura, sem Flask: copia, marcador, idempotencia e a chamada a porta
de historico. A arvore usada e sintetica, e nenhum arquivo real entra aqui.
"""
from __future__ import annotations

import os

from application.dono_inicial import (
    DONO_ANTERIOR,
    MARCADOR,
    garantir_dados_do_dono,
    ha_dados_nao_atribuidos,
)


class RegistroFalso:
    """A porta de historico, em memoria."""

    def __init__(self, linhas=3):
        self.linhas = linhas
        self.chamadas = []

    def adotar(self, dono_anterior, dono_novo):
        self.chamadas.append((dono_anterior, dono_novo))
        return self.linhas


def _semear(pasta):
    with open(os.path.join(pasta, "080e7943572d2652__arvore.ged"), "wb") as arquivo:
        arquivo.write(b"0 HEAD\n0 TRLR\n")
    with open(os.path.join(pasta, "94e2402671702cac__dna.csv"), "wb") as arquivo:
        arquivo.write(b"nome,cm\nMaria,100\n")
    os.makedirs(os.path.join(pasta, "_aposentados"), exist_ok=True)
    with open(os.path.join(pasta, "_aposentados", "antiga.ged"), "wb") as arquivo:
        arquivo.write(b"0 HEAD\n0 TRLR\n")


def test_copia_os_dados_para_a_conta_inicial_sem_apagar_originais(tmp_path):
    pasta = str(tmp_path)
    _semear(pasta)
    registro = RegistroFalso()

    relatorio = garantir_dados_do_dono(pasta, "1001", registro)

    destino = os.path.join(pasta, "1001")
    assert relatorio.copiou is True
    assert relatorio.copiados == 3, "os dois arquivos da raiz e o aposentado"
    assert sorted(os.listdir(destino)) == [
        "080e7943572d2652__arvore.ged",
        "94e2402671702cac__dna.csv",
        "_aposentados",
    ]
    assert os.path.isfile(os.path.join(destino, "_aposentados", "antiga.ged"))
    assert os.path.isfile(os.path.join(pasta, "080e7943572d2652__arvore.ged")), (
        "o original foi movido ou apagado: a migracao copia, nunca move"
    )
    assert os.path.isfile(os.path.join(pasta, MARCADOR))
    assert registro.chamadas == [(DONO_ANTERIOR, "1001")]


def test_a_segunda_execucao_nao_copia_de_novo(tmp_path):
    pasta = str(tmp_path)
    _semear(pasta)
    garantir_dados_do_dono(pasta, "1001", RegistroFalso())

    relatorio = garantir_dados_do_dono(pasta, "1001", RegistroFalso())

    assert relatorio.copiou is False
    assert relatorio.copiados == 0
    assert sorted(os.listdir(os.path.join(pasta, "1001"))) == [
        "080e7943572d2652__arvore.ged",
        "94e2402671702cac__dna.csv",
        "_aposentados",
    ]


def test_a_porta_de_historico_e_chamada_em_toda_entrada(tmp_path):
    """O `UPDATE` e idempotente por construcao, entao a chamada pode se repetir."""
    pasta = str(tmp_path)
    _semear(pasta)
    registro = RegistroFalso()

    garantir_dados_do_dono(pasta, "1001", registro)
    garantir_dados_do_dono(pasta, "1001", registro)

    assert registro.chamadas == [(DONO_ANTERIOR, "1001"), (DONO_ANTERIOR, "1001")]


def test_arquivo_ja_existente_no_destino_e_pulado(tmp_path):
    pasta = str(tmp_path)
    _semear(pasta)
    destino = os.path.join(pasta, "1001")
    os.makedirs(destino)
    with open(os.path.join(destino, "080e7943572d2652__arvore.ged"), "wb") as arquivo:
        arquivo.write(b"JA-EXISTIA")

    relatorio = garantir_dados_do_dono(pasta, "1001", RegistroFalso())

    assert relatorio.copiados == 2
    assert relatorio.pulados == 1
    with open(os.path.join(destino, "080e7943572d2652__arvore.ged"), "rb") as arquivo:
        assert arquivo.read() == b"JA-EXISTIA", "a copia sobrescreveu um arquivo do dono"


def test_o_aviso_de_dados_nao_atribuidos(tmp_path):
    pasta = str(tmp_path)
    _semear(pasta)

    assert ha_dados_nao_atribuidos(pasta) is True

    garantir_dados_do_dono(pasta, "1001", None)

    assert ha_dados_nao_atribuidos(pasta) is False


def test_pasta_ausente_nao_quebra_nem_cria_marcador(tmp_path):
    pasta = os.path.join(str(tmp_path), "nao-existe")

    relatorio = garantir_dados_do_dono(pasta, "1001", None)

    assert relatorio.copiou is False
    assert not os.path.exists(pasta)
