"""Guarda de fronteira do núcleo de cirurgia do grafo.

`core.cirurgia_do_grafo` é puro: recebe a árvore por parâmetro, devolve valor, não lê
arquivo, não consulta relógio e não conhece a borda HTTP. Quem lê arquivo é a fachada
`application.correcao`.
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

MODULO = RAIZ / "src" / "core" / "cirurgia_do_grafo.py"

PROIBIDOS = ("parsers", "application", "reporting", "flask", "waitress",
             "datetime", "time", "pathlib", "os")


def _modulos_importados(caminho: Path) -> set[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            modulos.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            modulos.add(no.module)
    return modulos


def test_cirurgia_nao_importa_borda_nem_relogio():
    modulos = _modulos_importados(MODULO)

    for modulo in modulos:
        raiz = modulo.split(".")[0]
        assert raiz not in PROIBIDOS, f"core/cirurgia_do_grafo.py importa {modulo!r}"


def test_cirurgia_nao_le_arquivo_nem_parseia_gedcom():
    fonte = MODULO.read_text(encoding="utf-8")

    assert "carregar_arvore" not in fonte
    assert "read_csv" not in fonte
    assert "from parsers" not in fonte
    assert "open(" not in fonte


def test_a_api_publica_do_nucleo_existe_e_esta_exportada():
    from core.cirurgia_do_grafo import (  # noqa: WPS433 (import tardio proposital)
        __all__,
        arvore_sugerida,
        desacoplar_identidade,
        injetar_geracoes,
        juncao,
        ramo_base,
        ramo_base_intacto,
    )

    publicas = {"ramo_base", "ramo_base_intacto", "juncao",
                "desacoplar_identidade", "injetar_geracoes", "arvore_sugerida"}
    assert publicas <= set(__all__)
    for funcao in (ramo_base, ramo_base_intacto, juncao,
                   desacoplar_identidade, injetar_geracoes, arvore_sugerida):
        assert callable(funcao)
