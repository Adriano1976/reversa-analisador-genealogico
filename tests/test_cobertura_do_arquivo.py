"""Testes da cobertura do arquivo (feature 040).

A medida é derivada das evidências já montadas — nenhum teste aqui relê CSV, e é isso que
os casos verificam: os números têm de sair do dicionário de evidências, e não de uma
segunda passada pelo arquivo.

Os percentuais são testados com números que fecham na mão (1 em 3, 1 em 2), e não com o
arquivo real do operador: a medição real vive no `onboarding.md`.
"""
from __future__ import annotations

import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

import pandas as pd  # noqa: E402

from core.cobertura_do_arquivo import medir  # noqa: E402
from core.genetic_evidence import build_genetic_evidence  # noqa: E402

# Ana: 28 cM em 2 segmentos, maior 20, SNPs 1.500. Bia: 12 cM, maior 12, SNPs 800.
CSV = (
    "Name,cM,Chromosome,SNPs,Kit,Source\n"
    "Ana Silva Souza,20,1,1000,AB1234567,Genera\n"
    "Ana Silva Souza,8,2,500,AB1234567,Genera\n"
    "Bia Oliveira,12,3,800,CD7654321,-\n"
)


def _medir(texto=CSV, linhas=None):
    evidencias, _avisos = build_genetic_evidence(pd.read_csv(io.StringIO(texto)))
    return medir(evidencias, linhas if linhas is not None else len(texto.strip().splitlines()) - 1)


class TestNumeros:
    def test_conta_linhas_pessoas_e_kits(self):
        cobertura = _medir(linhas=3)

        assert cobertura["linhas"] == 3
        assert cobertura["evidencias"] == 2
        assert cobertura["kits"] == 2

    def test_conta_cromossomos_distintos(self):
        assert _medir()["cromossomos"] == 3

    def test_mediana_do_total_por_evidencia(self):
        # Totais: 28 e 12 -> mediana 20.
        assert _medir()["mediana_cm"] == 20.0

    def test_percentual_de_segmentos_abaixo_do_piso(self):
        # 1 de 3 segmentos abaixo de 10 cM.
        cobertura = _medir()

        assert cobertura["segmentos"] == 3
        assert cobertura["segmentos_abaixo_do_piso"] == 1
        assert cobertura["percentual_abaixo_do_piso"] == 33

    def test_percentual_de_evidencias_sem_bloco_de_15(self):
        # Bia tem maior bloco de 12.
        cobertura = _medir()

        assert cobertura["evidencias_sem_bloco"] == 1
        assert cobertura["percentual_sem_bloco"] == 50

    def test_total_acima_do_piso_com_bloco_abaixo(self):
        # Ana passa de 15 e tem bloco de 20; Bia não passa de 15.
        cobertura = _medir()

        assert cobertura["total_acima"] == 1
        assert cobertura["total_acima_com_bloco_abaixo"] == 0

    def test_snps_abaixo_sem_contar_ausente_como_zero(self):
        cobertura = _medir()

        assert cobertura["evidencias_snps_baixo"] == 1


class TestFontes:
    def test_laboratorios_ordenados_por_contagem_e_nome(self):
        cobertura = _medir()

        assert cobertura["laboratorios"] == (("Genera", 1), ("não declarada", 1))
        assert cobertura["quantidade_de_laboratorios"] == 1
        assert cobertura["grafias"] == 2

    def test_celulas_sem_laboratorio_trazem_motivo_e_contagem(self):
        cobertura = _medir()

        assert cobertura["sem_laboratorio"] == (("texto de formulário", 1),)
        assert cobertura["sem_laboratorio_total"] == 1

    def test_csv_sem_coluna_de_fonte_nao_inventa_laboratorio(self):
        cobertura = _medir("Name,cM\nAna Silva Souza,20\n", linhas=1)

        assert cobertura["tem_coluna_de_fonte"] is False
        assert cobertura["laboratorios"] == ()
        assert cobertura["grafias"] == 0
        assert cobertura["quantidade_de_laboratorios"] == 0


class TestVazio:
    def test_arquivo_sem_evidencia_devolve_zeros(self):
        cobertura = medir({}, 0)

        assert cobertura["evidencias"] == 0
        assert cobertura["segmentos"] == 0
        assert cobertura["mediana_cm"] == 0.0
        assert cobertura["percentual_abaixo_do_piso"] == 0
        assert cobertura["percentual_sem_bloco"] == 0
        assert cobertura["tem_coluna_de_fonte"] is False
