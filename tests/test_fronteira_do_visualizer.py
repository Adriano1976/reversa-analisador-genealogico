"""Guarda de fronteira do renderizador.

`reporting/` não importa `core` (ADR-34) e o pacote `graphviz` só pode ser importado dentro
de função (L-26): dependência ausente não pode derrubar `import app` nem a suíte inteira.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

MODULO = RAIZ / "src" / "reporting" / "visualizer.py"

PROIBIDOS = ("core", "parsers", "application", "flask", "waitress")


def _arvore():
    return ast.parse(MODULO.read_text(encoding="utf-8"))


def _imports_de_topo(arvore) -> list:
    nomes = []
    for no in arvore.body:
        if isinstance(no, ast.Import):
            nomes.extend(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.append(no.module)
    return nomes


def _imports_dentro_de_funcoes(arvore) -> list:
    nomes = []
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for sub in ast.walk(no):
                if isinstance(sub, ast.Import):
                    nomes.extend(alias.name for alias in sub.names)
                elif isinstance(sub, ast.ImportFrom) and sub.module:
                    nomes.append(sub.module)
    return nomes


def test_graphviz_nao_e_importado_no_topo():
    topo = _imports_de_topo(_arvore())

    assert "graphviz" not in topo, "graphviz no topo derruba import app quando falta"
    assert "graphviz" in _imports_dentro_de_funcoes(_arvore())


def test_visualizer_nao_importa_nucleo_nem_borda():
    modulos = _imports_de_topo(_arvore()) + _imports_dentro_de_funcoes(_arvore())

    for modulo in modulos:
        raiz = modulo.split(".")[0]
        assert raiz not in PROIBIDOS, f"reporting/visualizer.py importa {modulo!r}"


def test_a_api_publica_esta_exportada():
    from reporting import visualizer  # noqa: WPS433 (import tardio proposital)

    publicas = {"texto_dot", "renderizar_arvore_sugerida", "ErroDeRenderizacao",
                "resumo_evidencia", "veredito"}
    assert publicas <= set(visualizer.__all__)
    for nome in ("texto_dot", "renderizar_arvore_sugerida", "resumo_evidencia", "veredito"):
        assert callable(getattr(visualizer, nome))
