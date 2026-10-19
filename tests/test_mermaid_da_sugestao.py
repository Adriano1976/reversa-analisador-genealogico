"""Testes do desenho Mermaid da árvore sugerida.

Verificam o contrato exato do texto: classes de cor, cadeia virtual, aresta rompida por
último e o índice do `linkStyle` — a parte que quebra em silêncio se a ordem mudar.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from reporting.mermaid_render import mermaid_da_sugestao  # noqa: E402
from reporting.visualizer import ROTULO_QUEBRA  # noqa: E402

DOCUMENTAL = {
    "path": {"ids": ["@I1@", "@I2@", "@I10@", "@I4@"],
             "names": ["Doador", "Pai", "Ancestral", "Primo"]},
    "common_ancestor": {"id": "@I10@"},
    "degrees": {"a_up": 2, "b_up": 2},
}


def _resumo(geracoes: int = 3) -> dict:
    return {"geracoes": geracoes,
            "rotulos": [f"Geração {ordem}" for ordem in range(1, geracoes + 1)]}


def _arestas(texto: str) -> list:
    return [linha for linha in texto.splitlines()
            if "-->" in linha or "-.->" in linha]


# ---------------------------------------------------------------------------
# Estrutura e cores
# ---------------------------------------------------------------------------

def test_o_desenho_abre_como_grafo_e_traz_as_tres_classes():
    texto = mermaid_da_sugestao(DOCUMENTAL, _resumo())

    assert texto.startswith("graph TD")
    assert "classDef base fill:#a8e6cf,stroke:#4a7c68" in texto
    assert "classDef doc fill:#f5f5f5,stroke:#666666" in texto
    assert "classDef virt fill:#ffd3b6,stroke:#a8724a" in texto


def test_o_doador_e_base_e_os_demais_sao_documentais():
    texto = mermaid_da_sugestao(DOCUMENTAL, _resumo())

    assert 'N_I1["Doador"]:::base' in texto
    assert 'N_I2["Pai"]:::doc' in texto
    assert 'N_I4["Primo"]:::doc' in texto


def test_as_geracoes_virtuais_se_chamam_geracao_k():
    texto = mermaid_da_sugestao(DOCUMENTAL, _resumo(3))

    assert 'V1["Geração 1"]:::virt' in texto
    assert 'V2["Geração 2"]:::virt' in texto
    assert 'V3["Geração 3"]:::virt' in texto


# ---------------------------------------------------------------------------
# Cadeia e quebra
# ---------------------------------------------------------------------------

def test_a_cadeia_liga_o_ancestral_ao_filho_passando_pelas_geracoes():
    texto = mermaid_da_sugestao(DOCUMENTAL, _resumo(2))

    assert "N_I10 --> V1" in texto
    assert "V1 --> V2" in texto
    assert "V2 --> N_I2" in texto


def test_a_aresta_rompida_e_tracejada_e_rotulada():
    texto = mermaid_da_sugestao(DOCUMENTAL, _resumo())

    assert f"N_I10 -.->|{ROTULO_QUEBRA}| N_I2" in texto


def test_a_aresta_rompida_e_a_ultima_e_o_linkstyle_aponta_para_ela():
    texto = mermaid_da_sugestao(DOCUMENTAL, _resumo(2))
    arestas = _arestas(texto)

    assert "-.->" in arestas[-1], "a aresta rompida tem de ser a última"
    assert arestas[-1].strip().startswith("N_I10 -.->")
    assert f"linkStyle {len(arestas) - 1} stroke:red" in texto


def test_o_trecho_vertical_do_caminho_continua_desenhado():
    texto = mermaid_da_sugestao(DOCUMENTAL, _resumo())

    assert "N_I1 --> N_I2" in texto
    assert "N_I10 --> N_I4" in texto


# ---------------------------------------------------------------------------
# Recusas, determinismo e escape
# ---------------------------------------------------------------------------

def test_sem_geracoes_nao_desenha():
    assert mermaid_da_sugestao(DOCUMENTAL, _resumo(0)) is None
    assert mermaid_da_sugestao(DOCUMENTAL, {"geracoes": 0}) is None


def test_sem_caminho_nao_desenha():
    assert mermaid_da_sugestao({"path": {"ids": []}}, _resumo()) is None
    assert mermaid_da_sugestao({}, _resumo()) is None


def test_sem_ancestral_no_caminho_nao_desenha():
    documental = {**DOCUMENTAL, "common_ancestor": {"id": "@I99@"}}

    assert mermaid_da_sugestao(documental, _resumo()) is None


def test_o_texto_e_deterministico():
    primeiro = mermaid_da_sugestao(DOCUMENTAL, _resumo())
    segundo = mermaid_da_sugestao(DOCUMENTAL, _resumo())

    assert primeiro == segundo


def test_nome_com_aspas_e_parentese_nao_quebra_a_gramatica():
    documental = {
        "path": {"ids": ["@I1@", "@I2@"],
                 "names": ['Doador "José" (neto)', "Pai & Cia"]},
        "common_ancestor": {"id": "@I2@"},
    }

    texto = mermaid_da_sugestao(documental, _resumo(1))

    assert '"' not in texto.replace('["', "").replace('"]', "").replace('|', "")
    assert "&amp;" in texto
