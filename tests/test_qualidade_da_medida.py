"""Testes do estado de qualidade da medida (feature 040).

O estado responde "esta medida sustenta alguma conclusão?" e **não** "estes dois são
parentes". Os limites são os do projeto: 15,0 cM (total e maior bloco) e 900 SNPs
(corte de triagem declarado).

A fronteira é testada nos dois lados de propósito: 15,00/14,99 e 900/899. Um limite que
só é testado por dentro não prende nada.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

import pytest  # noqa: E402

from core.qualidade_da_medida import (  # noqa: E402
    INSUFICIENTE,
    PARCIAL,
    PISO_MAIOR_BLOCO_CM,
    PISO_SNPS,
    PISO_TOTAL_CM,
    RESSALVA,
    ROBUSTA,
    MOTIVOS_TEXTO,
    avaliar,
)


class TestFaixas:
    def test_total_maior_bloco_e_snps_no_piso_e_robusta(self):
        medida = avaliar(PISO_TOTAL_CM, PISO_MAIOR_BLOCO_CM, PISO_SNPS)

        assert medida["estado"] == ROBUSTA
        assert medida["rotulo"] == "Medida robusta"
        assert medida["motivos"] == ()

    def test_um_centesimo_abaixo_no_total_e_insuficiente(self):
        medida = avaliar(PISO_TOTAL_CM - 0.01, PISO_MAIOR_BLOCO_CM, PISO_SNPS)

        assert medida["estado"] == INSUFICIENTE
        assert medida["motivos"] == ("total_baixo",)

    def test_bloco_abaixo_do_piso_e_parcial(self):
        medida = avaliar(PISO_TOTAL_CM + 30, PISO_MAIOR_BLOCO_CM - 0.01, PISO_SNPS)

        assert medida["estado"] == PARCIAL
        assert medida["motivos"] == ("bloco_pequeno",)

    def test_snps_abaixo_do_piso_e_parcial(self):
        medida = avaliar(PISO_TOTAL_CM, PISO_MAIOR_BLOCO_CM, PISO_SNPS - 1)

        assert medida["estado"] == PARCIAL
        assert medida["motivos"] == ("poucos_snps",)

    def test_snps_ausentes_nao_penalizam(self):
        medida = avaliar(PISO_TOTAL_CM, PISO_MAIOR_BLOCO_CM, None)

        assert medida["estado"] == ROBUSTA

    def test_bloco_ausente_conta_como_abaixo_do_piso(self):
        medida = avaliar(PISO_TOTAL_CM, None, PISO_SNPS)

        assert medida["estado"] == PARCIAL
        assert medida["numeros"]["maior_bloco_cm"] is None


class TestContrato:
    @pytest.mark.parametrize("total, bloco, snps", [
        (154.5, 56.9, 15959),
        (16.0, 8.0, 1000),
        (9.05, 9.05, 1200),
        (0.0, None, None),
    ])
    def test_o_estado_sempre_traz_rotulo_numeros_e_ressalva(self, total, bloco, snps):
        medida = avaliar(total, bloco, snps)

        assert medida["estado"] in (ROBUSTA, PARCIAL, INSUFICIENTE)
        assert medida["rotulo"].startswith("Medida")
        assert medida["numeros"]["total_cm"] == total
        assert medida["numeros"]["maior_bloco_cm"] == bloco
        assert medida["numeros"]["snps"] == snps
        assert medida["ressalva"] == RESSALVA
        assert "não do parentesco" in medida["ressalva"]

    def test_o_motivo_tem_texto_proprio_para_a_tela(self):
        medida = avaliar(PISO_TOTAL_CM + 30, 5.0, 1000)

        assert medida["motivos_texto"] == (MOTIVOS_TEXTO["bloco_pequeno"],)
        assert "15" in medida["motivos_texto"][0]
