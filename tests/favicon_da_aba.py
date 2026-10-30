"""Receita do favicon transparente das telas de identidade (emenda E005).

## Por que uma arte separada, e por que transparente

O `apple-touch-icon.png` e **opaco de proposito**: o sistema movel compoe a
transparencia sobre PRETO no atalho da tela inicial, e servir a arte crua daria um
quadrado preto (`tests/icone_de_atalho.py`). Na **aba do navegador** a regra e a
oposta: o icone aparece sobre a barra de abas, e um quadrado branco opaco fica
visivel como uma moldura. A tela principal (`index.html`) ja usa um icone
transparente embutido; as telas de identidade passam a usar esta derivada, com a
mesma arte e o mesmo lado declarado (128x128).

## A derivacao, e a fonte unica

A fonte e a mesma canonica do icone de atalho (`docs/assets/img/logo.png`,
512x512 com alfa). A transformacao e so reamostragem LANCZOS para 128x128,
**sem compor fundo** — o alfa e preservado. A arte e commitada em
`src/assets/favicon.png` porque dentro do container nao existe `docs/` (o
`.dockerignore` e lista de permissao), e o teste de deriva regenera a partir da
canonica e compara pixel a pixel, incluindo o canal alfa.

## Como regenerar

    .\\.venv\\Scripts\\python.exe -m tests.favicon_da_aba
"""
from __future__ import annotations

import io
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

#: A mesma fonte canonica do icone de atalho.
ARTE_CANONICA = RAIZ / "docs" / "assets" / "img" / "logo.png"

#: A arte de runtime, servida por `GET /favicon.png`.
ARTE_DE_RUNTIME = RAIZ / "src" / "assets" / "favicon.png"

#: Lado do favicon. Igual ao `sizes` que a tela principal declara para o seu data URI.
LADO = 128

#: Ancla da receita: denuncia reamostragem com outro filtro, fundo composto ou
#: compressao diferente. Medido na primeira execucao, em 2026-10-30.
TAMANHO_ESPERADO = 14456


def arte_derivada(caminho_canonico: Path = ARTE_CANONICA):
    """A imagem derivada, transparente. Nao escreve nada em disco."""
    from PIL import Image

    origem = Image.open(caminho_canonico).convert("RGBA")
    return origem.resize((LADO, LADO), Image.LANCZOS)


def bytes_da_arte(caminho_canonico: Path = ARTE_CANONICA) -> bytes:
    """Os bytes exatos do PNG derivado, com a compressao da receita."""
    buffer = io.BytesIO()
    arte_derivada(caminho_canonico).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def gravar_arte(
    caminho_destino: Path = ARTE_DE_RUNTIME,
    caminho_canonico: Path = ARTE_CANONICA,
) -> int:
    """Regenera a arte de runtime e devolve quantos bytes foram gravados."""
    conteudo = bytes_da_arte(caminho_canonico)
    caminho_destino.parent.mkdir(parents=True, exist_ok=True)
    caminho_destino.write_bytes(conteudo)
    return len(conteudo)


def _principal() -> int:
    if not ARTE_CANONICA.exists():
        print(f"ERRO: arte canonica nao encontrada em {ARTE_CANONICA}")
        return 2
    gravados = gravar_arte()
    imagem = arte_derivada()
    print(f"canonica : {ARTE_CANONICA} ({ARTE_CANONICA.stat().st_size} bytes)")
    print(f"destino  : {ARTE_DE_RUNTIME}")
    print(f"gravado  : {gravados} bytes (esperado {TAMANHO_ESPERADO})")
    print(f"dimensao : {imagem.size}")
    print(f"canal a  : {imagem.getchannel('A').getextrema()}")
    return 0 if gravados == TAMANHO_ESPERADO else 1


if __name__ == "__main__":
    raise SystemExit(_principal())
