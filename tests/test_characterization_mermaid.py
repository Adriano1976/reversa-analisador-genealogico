"""Caracterizacao da saida Mermaid da busca de caminho.

Congela a saida exata das duas funcoes de render para o GEDCOM sintetico das
fixtures. Caracterizacao no sentido de Feathers: fixa o comportamento atual como
ele esta, para detectar mudanca.

Origem: rede de seguranca da transformacao OPP-20260929-TPSH, promovida a teste
permanente em 2026-09-29. Isto e teste de REGRESSAO, nao prova de paridade com o
legado: o oraculo diferencial nao existe mais na arvore.
"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analisador-genealogico"))

from tests.fixtures.sample_gedcom import SAMPLE_GED

from reconstructed import upload
# pyrefly: ignore [missing-import]
from reconstructed.path_search import path_search

# Saida congelada, linha por linha, para os tres caminhos de render.
GOLDEN = {
    "direto": {
        "p1": "Carlos Silva",
        "p2": "Ana Silva",
        "msg": "Conexão direta encontrada (ancestral comum).",
        "success": True,
        "text_path": "Carlos Silva → Joao Silva → Ana Silva",
        "mermaid_data": "\n".join([
            "flowchart BT",
            'N_I1_I2["Joao Silva &amp; Maria Souza"]',
            'N_I3["Carlos Silva"]',
            'N_I4["Ana Silva"]',
            "N_I3 --> N_I1_I2",
            "N_I4 --> N_I1_I2",
            "style N_I3 fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px",
            "style N_I4 fill:#ffebee,stroke:#ef5350,stroke-width:2px",
            "style N_I1_I2 fill:#fff9c4,stroke:#fbc02d,stroke-width:2px",
        ]),
    },
    "indireto": {
        "p1": "Carlos Silva",
        "p2": "Bia Oliveira",
        "msg": "Conexão indireta encontrada (via casamento/afinidade).",
        "success": True,
        "text_path": "Carlos Silva → Bia Oliveira",
        "mermaid_data": "\n".join([
            "flowchart BT",
            "subgraph COLUMNS",
            "direction BT",
            "subgraph ESQ[Ramo 1]",
            "direction BT",
            "subgraph ESQ_COLS",
            "direction BT",
            "end",
            'N_I3_I5["Carlos Silva &amp; Bia Oliveira"]',
            "end",
            "subgraph DIR[Ramo 2]",
            "direction BT",
            'N_I5["Bia Oliveira"]',
            "end",
            'N_I3_anc[" "]',
            'N_I5_anc[" "]',
            "style N_I3_anc fill:transparent,stroke:transparent,stroke-width:0",
            "style N_I5_anc fill:transparent,stroke:transparent,stroke-width:0",
            "N_I3 --- N_I3_anc",
            "N_I5_anc --- N_I5",
            "N_I3_anc --- |Casamento| N_I5_anc",
            "end",
            "style N_I5 fill:#ffebee,stroke:#ef5350,stroke-width:2px",
            "style N_I3_I5 fill:#fff9c4,stroke:#fbc02d,stroke-width:2px",
            "style N_I3 fill:#fff8e1,stroke:#f6a821,stroke-width:2px",
            "style N_I5 fill:#fff8e1,stroke:#f6a821,stroke-width:2px",
        ]),
    },
    "trivial": {
        "p1": "Carlos Silva",
        "p2": "Carlos Silva",
        "msg": "Conexão direta encontrada (ancestral comum).",
        "success": True,
        "text_path": "Carlos Silva",
        "mermaid_data": "\n".join([
            "flowchart BT",
            'N_I3["Carlos Silva"]',
            "style N_I3 fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px",
            "style N_I3 fill:#ffebee,stroke:#ef5350,stroke-width:2px",
            "style N_I3 fill:#fff9c4,stroke:#fbc02d,stroke-width:2px",
        ]),
    },
    "sem-conexao": {
        "p1": "Carlos Silva",
        "p2": "Lone Ranger",
        "msg": "Nenhuma conexão encontrada entre 'Carlos Silva' e 'Lone Ranger'.",
        "success": True,
        "text_path": None,
        "mermaid_data": None,
    },
}


@pytest.fixture(scope="module")
def carregado():
    """Carrega o GEDCOM sintetico uma unica vez para toda a suite."""
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(SAMPLE_GED)
        upload.load_gedcom_and_build_graph(path)
    finally:
        os.remove(path)
    return upload


@pytest.mark.parametrize("caso", sorted(GOLDEN))
def test_saida_mermaid_caracterizada(carregado, caso):
    """A saida de cada caminho de render tem de continuar identica, linha a linha."""
    esperado = GOLDEN[caso]
    result, msg, success = path_search(esperado["p1"], esperado["p2"])

    assert success is esperado["success"]
    assert msg == esperado["msg"]
    assert (result or {}).get("text_path") == esperado["text_path"]
    assert (result or {}).get("mermaid_data") == esperado["mermaid_data"]


def test_rotulo_com_caracteres_de_escape(carregado):
    """O `&` do rotulo continua saindo como entidade HTML, nao cru."""
    result, _, _ = path_search("Carlos Silva", "Ana Silva")
    assert "&amp;" in result["mermaid_data"]
    assert " & " not in result["mermaid_data"]
