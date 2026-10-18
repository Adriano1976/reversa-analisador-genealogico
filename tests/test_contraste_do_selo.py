"""Contraste do selo de validação, calculado a partir da folha de estilo.

Não abre navegador nem compara imagem: lê `src/assets/app.css`, extrai as cores dos dois
blocos de tema e aplica a fórmula WCAG de luminância relativa. É a resposta ao defeito de
1,11:1 medido em 2026-10-14 — um selo cujo texto sumiu no fundo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

FOLHA = RAIZ / "src" / "assets" / "app.css"

#: Mínimo do WCAG AA para texto pequeno.
MINIMO_DE_TEXTO = 4.5

BLOCOS = {
    "claro": ":root{",
    "escuro": ':root[data-bs-theme="dark"]{',
}

VIVEIS = ("--validacao-valido", "--validacao-conflito")


def _bloco(fonte: str, seletor: str) -> str:
    inicio = fonte.index(seletor)
    fim = fonte.index("}", inicio)
    return fonte[inicio:fim]


def _cor(bloco: str, nome: str) -> str:
    achado = re.search(rf"{re.escape(nome)}\s*:\s*(#[0-9A-Fa-f]{{6}})", bloco)
    assert achado, f"{nome} não está no bloco"
    return achado.group(1)


def _luminancia(cor: str) -> float:
    limpo = cor.lstrip("#")
    canais = [int(limpo[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lineares = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lineares[0] + 0.7152 * lineares[1] + 0.0722 * lineares[2]


def _contraste(uma: str, outra: str) -> float:
    a, b = _luminancia(uma), _luminancia(outra)
    claro, escuro = max(a, b), min(a, b)
    return (claro + 0.05) / (escuro + 0.05)


def test_as_variaveis_do_selo_existem_nos_dois_temas():
    fonte = FOLHA.read_text(encoding="utf-8")

    for nome_bloco, seletor in BLOCOS.items():
        bloco = _bloco(fonte, seletor)
        for variavel in VIVEIS:
            assert _cor(bloco, variavel), f"{variavel} ausente no tema {nome_bloco}"


def test_o_contraste_do_selo_passa_nos_dois_temas():
    fonte = FOLHA.read_text(encoding="utf-8")

    for nome_bloco, seletor in BLOCOS.items():
        bloco = _bloco(fonte, seletor)
        fundo = _cor(bloco, "--bg")
        for variavel in VIVEIS:
            razao = _contraste(_cor(bloco, variavel), fundo)
            assert razao >= MINIMO_DE_TEXTO, (
                f"{variavel} no tema {nome_bloco} dá {razao:.2f}:1, abaixo de "
                f"{MINIMO_DE_TEXTO}:1")


def test_as_classes_do_selo_sao_de_contorno_e_fora_do_prefixo_dos_estados():
    fonte = FOLHA.read_text(encoding="utf-8")

    assert ".badge.validacao-valido{" in fonte
    assert ".badge.validacao-conflito{" in fonte
    # A regra `.badge[class*="estado-"]` pintaria o texto de branco; nenhuma classe do
    # selo pode casar com ela.
    assert "estado-validacao" not in fonte
    for variavel in VIVEIS:
        assert f"border:1px solid var({variavel})" in fonte
