"""Testes do involucro de execucao da paridade (feature 010, `D-07`).

O involucro existe para que a paridade nao escreva na pasta de upload do operador. Ele
faz isso definindo `ANALISADOR_UPLOAD_FOLDER` **antes** de lancar o harness — o que
funciona porque o harness entrega o ambiente ao coletor (`harness.py:465`) e o coletor
importa a aplicacao (`:356`), que resolve a pasta no import.

Os testes **nao** executam o harness de verdade: eles injetam um script sintetico em
`script=`. Rodar a paridade inteira dentro da suite custaria minutos e misturaria a
medicao diferencial com a suite. A prova de que a paridade real fica em 100 % e que a
pasta real nao muda e de `T003` e `T017`, medidas em evidencia propria.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import rodar_paridade as RP  # noqa: E402

ROTEIRO = """
import os, sys
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    fh.write(os.environ.get("ANALISADOR_UPLOAD_FOLDER", "AUSENTE"))
sys.exit(7 if os.environ.get("ANALISADOR_UPLOAD_FOLDER") else 3)
"""


def _roteiro(tmp_path) -> str:
    caminho = tmp_path / "roteiro.py"
    caminho.write_text(ROTEIRO, encoding="utf-8")
    return str(caminho)


def test_pasta_descartavel_e_criada(tmp_path):
    pasta = RP.pasta_descartavel(str(tmp_path))

    assert os.path.isdir(pasta)
    assert os.path.basename(pasta) == "uploads"
    assert ".parity-tmp" in pasta


def test_montar_ambiente_define_a_variavel_sem_alterar_o_chamador(tmp_path):
    base = {"OUTRA": "1"}

    ambiente = RP.montar_ambiente(base, pasta=str(tmp_path / "descartavel"))

    assert base == {"OUTRA": "1"}, "o ambiente do chamador nao pode ser alterado"
    assert ambiente["OUTRA"] == "1"
    assert ambiente[RP.VARIAVEL] == str(tmp_path / "descartavel")


def test_comando_aponta_para_o_harness_do_repositorio():
    linha = RP.comando(["--pares", "4"])

    assert linha[0] == sys.executable
    assert os.path.isfile(linha[1]), "o harness tem de existir no caminho declarado"
    assert os.path.basename(linha[1]) == "harness.py"
    assert linha[2:] == ["--pares", "4"]


def test_executar_entrega_a_variavel_e_repassa_argumentos(tmp_path):
    marca = tmp_path / "marca.txt"
    pasta = str(tmp_path / "descartavel")

    codigo = RP.executar([str(marca)], script=_roteiro(tmp_path), pasta=pasta)

    assert codigo == 7, "o codigo de saida do script tem de ser devolvido"
    assert marca.read_text(encoding="utf-8") == pasta


def test_executar_sem_a_variavel_o_roteiro_sai_3(tmp_path):
    """Controle negativo: prova que o codigo 7 do teste acima vem da variavel."""
    marca = tmp_path / "marca.txt"
    sem_variavel = {k: v for k, v in os.environ.items() if k != RP.VARIAVEL}

    codigo = RP.executar([str(marca)], script=_roteiro(tmp_path), ambiente=sem_variavel)

    assert codigo == 3
    assert marca.read_text(encoding="utf-8") == "AUSENTE"
