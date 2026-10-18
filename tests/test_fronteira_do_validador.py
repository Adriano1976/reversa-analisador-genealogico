"""Guarda de fronteira do núcleo de validação.

O `core.validator` é puro: não pode importar `parsers`, `application`,
`reporting`, a borda HTTP nem consultar relógio. A fachada é que faz I/O.
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

PROIBIDOS = ("parsers", "application", "reporting", "flask", "datetime", "time")


def _modulos_importados(caminho: Path) -> set[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            modulos.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            modulos.add(no.module)
    return modulos


def test_validator_nao_importa_borda_nem_relogio():
    modulos = _modulos_importados(RAIZ / "src" / "core" / "validator.py")

    for modulo in modulos:
        raiz = modulo.split(".")[0]
        assert raiz not in PROIBIDOS, f"core/validator.py importa {modulo!r}"


def test_validator_nao_importa_arvore_nem_parsers():
    fonte = (RAIZ / "src" / "core" / "validator.py").read_text(encoding="utf-8")

    assert "carregar_arvore" not in fonte
    assert "read_csv" not in fonte
    assert "from parsers" not in fonte
    assert "import parsers" not in fonte


def test_a_api_publica_do_nucleo_existe():
    from core.validator import (  # noqa: WPS433 (import tardio proposital)
        agregar_resultados,
        estimar_mrca,
        validar_comparacao,
    )

    assert callable(estimar_mrca)
    assert callable(validar_comparacao)
    assert callable(agregar_resultados)
