"""Teste de renderização real (PNG e SVG).

Este é o único arquivo que precisa do binário `dot`. Em máquina sem Graphviz ele é
**pulado com motivo**, e isso é declarado: a ausência do binário não pode deixar a suíte
vermelha nem esconder regressão de verdade.
"""
from __future__ import annotations

import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from reporting import visualizer as vz  # noqa: E402
from tests.fixtures import sugestao_para_desenho as fixo  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("dot") is None,
    reason="binário `dot` do Graphviz não está no PATH; instale o Graphviz para rodar",
)


def test_gera_png(tmp_path):
    destino = str(tmp_path / "arvore.png")

    caminho = vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                            fixo.documental(), destino)

    assert caminho == destino
    assert os.path.isfile(destino)
    assert os.path.getsize(destino) > 0
    assert [item.name for item in tmp_path.iterdir()] == ["arvore.png"]


def test_gera_svg(tmp_path):
    destino = str(tmp_path / "arvore.svg")

    vz.renderizar_arvore_sugerida(fixo.sugestao(), fixo.resultado(),
                                  fixo.documental(), destino)

    assert os.path.isfile(destino)
    with open(destino, encoding="utf-8") as arquivo:
        conteudo = arquivo.read()
    assert "<svg" in conteudo
    assert vz.ROTULO_QUEBRA in conteudo
