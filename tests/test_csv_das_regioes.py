"""Testes do CSV das regiões compartilhadas (feature 056)."""
from __future__ import annotations

from reporting.csv_das_regioes import CABECALHO, csv_das_regioes


def test_cabecalho_e_dialeto():
    conteudo = csv_das_regioes([])

    assert conteudo.startswith("\ufeff")
    assert conteudo.split("\r\n")[0].endswith(";".join(CABECALHO))
    assert "\r\n" in conteudo


def test_uma_linha_por_regiao_com_decimal_virgula():
    conteudo = csv_das_regioes([{
        "cromossomo": "7",
        "inicio": 22000000,
        "fim": 38000000,
        "extensao_mb": 16.0,
        "kits": 3,
        "cm_minimo": 35.0,
        "cm_maximo": 45.0,
        "desfecho": "Convergente",
        "alerta": "",
        "membros": "Maria (A1) | João (B2)",
        "ancestrais": "José Alves",
        "motivo": "Todos apontam o mesmo ancestral.",
    }])

    linhas = conteudo.lstrip("\ufeff").split("\r\n")
    assert len(linhas) == 3
    assert "16" in linhas[1]
    assert "35" in linhas[1] and "45" in linhas[1]
    assert "Convergente" in linhas[1]


def test_texto_perigoso_e_desarmado():
    conteudo = csv_das_regioes([{
        "cromossomo": "7", "inicio": 1, "fim": 2, "extensao_mb": 0.0,
        "kits": 3, "cm_minimo": 1.0, "cm_maximo": 2.0,
        "desfecho": "=SOMA(A1:A2)", "alerta": "", "membros": "",
        "ancestrais": "", "motivo": "",
    }])

    assert "'=SOMA" in conteudo
