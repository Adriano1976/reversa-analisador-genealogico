"""Caracterizacao da saida Mermaid da busca de caminho.

Congela a saida exata das duas funcoes de render para o GEDCOM sintetico das
fixtures. Caracterizacao no sentido de Feathers: fixa o comportamento atual como
ele esta, para detectar mudanca.

Origem: rede de seguranca da transformacao OPP-20260929-TPSH, promovida a teste
permanente em 2026-09-29. Isto e teste de REGRESSAO, nao prova de paridade com o
legado: o oraculo diferencial nao existe mais na arvore.

**Atualizado em 2026-10-26 (passagem de design do diagrama).** O rotulo do no
deixou de ser o nome cru e passou a ser uma CAIXA DE TAMANHO FIXO — 190 px para
pessoa, 230 px para o casal — com o nome em negrito e uma segunda linha (datas,
ou espaco que segura a altura). O casal saiu de "A &amp; B" para duas linhas com
o xis entre elas. As cores e as arestas NAO mudaram. A forma esperada mora nos
helpers `_pessoa`/`_casal` abaixo, para o teste continuar legivel e mesmo assim
prender o markup exato.
"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures.sample_gedcom import SAMPLE_GED

from parsers import gedcom_parser
from core.path_search import path_search
from tests.fixtures.helpers import arvore_de as _arvore_de
from tests.fixtures.helpers import deps as _deps
from tests.fixtures.arvore_atual import atual, guardar


def _pessoa(nome, detalhe="&nbsp;"):
    """A caixa de pessoa, exatamente como `reporting.mermaid_render` a emite."""
    return (
        "<div style='width:190px;min-height:44px;text-align:center;line-height:1.3'>"
        f"<strong>{nome}</strong><br/>"
        f"<span style='font-size:12.5px;color:#6A6150'>{detalhe}</span></div>"
    )


def _casal(nome1, nome2, detalhe="&nbsp;"):
    """A caixa do casal: duas linhas com o xis e a faixa de anos embaixo."""
    return (
        "<div style='width:230px;min-height:66px;text-align:center;line-height:1.3'>"
        f"<strong>{nome1}</strong><br/><strong>\u00d7 {nome2}</strong><br/>"
        f"<span style='font-size:12.5px;color:#6A6150'>{detalhe}</span></div>"
    )


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
            f'N_I1_I2["{_casal("Joao Silva", "Maria Souza")}"]',
            f'N_I3["{_pessoa("Carlos Silva")}"]',
            f'N_I4["{_pessoa("Ana Silva")}"]',
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
            f'N_I3_I5["{_casal("Carlos Silva", "Bia Oliveira")}"]',
            "end",
            "subgraph DIR[Ramo 2]",
            "direction BT",
            f'N_I5["{_pessoa("Bia Oliveira")}"]',
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
            f'N_I3["{_pessoa("Carlos Silva")}"]',
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
    """Carrega o GEDCOM sintetico uma unica vez para toda a suite.

    Devolve a ARVORE, e nao o modulo de estado: os testes usam `atual()`, que le
    o que o parse devolveu.
    """
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(SAMPLE_GED)
        guardar(gedcom_parser.carregar_arvore(path))
    finally:
        os.remove(path)
    return atual()


@pytest.mark.parametrize("caso", sorted(GOLDEN))
def test_saida_mermaid_caracterizada(carregado, caso):
    """A saida de cada caminho de render tem de continuar identica, linha a linha."""
    esperado = GOLDEN[caso]
    result, msg, success = path_search(esperado["p1"], esperado["p2"], _deps(), atual())

    assert success is esperado["success"]
    assert msg == esperado["msg"]
    assert (result or {}).get("text_path") == esperado["text_path"]
    assert (result or {}).get("mermaid_data") == esperado["mermaid_data"]


def test_o_no_carrega_a_caixa_de_tamanho_fixo(carregado):
    """O nome nao estica mais o retangulo: a largura vem do rotulo, nao do texto.

    Sem data no GEDCOM sintetico, a segunda linha sai como `&nbsp;` — o que segura a
    altura e mantem as caixas iguais. A largura do casal e' maior que a da pessoa.
    """
    result, _, _ = path_search("Carlos Silva", "Ana Silva", _deps(), atual())
    mermaid = result["mermaid_data"]

    assert "<strong>Carlos Silva</strong>" in mermaid
    assert "width:190px" in mermaid
    assert "width:230px" in mermaid
    assert "&nbsp;" in mermaid


def test_o_casal_nao_usa_mais_o_e_comercial(carregado):
    """Dois nomes numa linha so se liam como uma pessoa de nome composto."""
    result, _, _ = path_search("Carlos Silva", "Ana Silva", _deps(), atual())
    mermaid = result["mermaid_data"]

    assert " &amp; " not in mermaid
    assert "\u00d7 Maria Souza" in mermaid
