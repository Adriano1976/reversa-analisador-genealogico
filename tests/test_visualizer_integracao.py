"""Teste fim-a-fim: GEDCOM e CSV sintéticos até o texto DOT.

Percorre a cadeia real — validação da `028`, sugestão da `029` e desenho da `030` — sem
exigir o binário `dot`: o que se verifica aqui é que os três dicionários reais produzem um
DOT válido, com as classes e a quebra no lugar.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from application.validacao import validar_arquivos  # noqa: E402
from core.cirurgia_do_grafo import arvore_sugerida  # noqa: E402
from reporting.visualizer import ROTULO_QUEBRA, texto_dot  # noqa: E402
from tests.fixtures.arvore_para_cirurgia import (  # noqa: E402
    CSV_SALTO,
    GED_SALTO_IMPOSSIVEL,
)


def _arquivo(tmp_path: Path, nome: str, conteudo: str) -> str:
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return str(caminho)


def test_da_validacao_ao_desenho(tmp_path):
    ged = _arquivo(tmp_path, "salto.ged", GED_SALTO_IMPOSSIVEL)
    csv = _arquivo(tmp_path, "salto.csv", CSV_SALTO)

    validacao = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026,
                                 incluir_documental=True)
    comparacao = validacao["comparacoes"][0]
    documental = comparacao["documental"]

    sugestao = arvore_sugerida(validacao["arvore"], documental, comparacao,
                               validacao["doador"]["id"])
    texto = texto_dot(sugestao, comparacao, documental)

    assert texto.startswith("digraph arvore_sugerida {")
    # O doador da fixture é o verde.
    assert "#a8e6cf" in texto
    # A quebra aparece com o rótulo literal e a cadeia sugerida existe.
    assert ROTULO_QUEBRA in texto
    assert "#ffd3b6" in texto
    # A caixa traz números reais vindos da validação, não inventados.
    assert " cM, " in texto and "gerações - " in texto
    # Nenhum nó de família entra no desenho.
    assert '"@F2@" [' not in texto
