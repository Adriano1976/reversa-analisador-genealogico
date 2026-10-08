"""Deriva da arte de runtime contra a canonica (`T005`, `RF-10` da feature 009).

## Por que nao se compara o `sha256` dos dois arquivos

Porque daria **alarme falso**. Medido nesta feature: o MESMO desenho existe em disco com
32.317 bytes (`docs/assets/img/logo.png`) e, vindo de outra codificacao, com 44.069 bytes
- e a diferenca de pixel entre os dois e **zero**. Uma comparacao por hash acusaria
divergencia onde nao ha nenhuma, e um teste que grita sem motivo e desligado.

## O que se compara, entao

**Pixel a pixel.** A arte de runtime nao e copia da canonica: e uma **renderizacao
derivada** (opaca, 180x180). Entao o teste nao compara os dois arquivos: ele **regenera**
a derivada a partir da canonica, com a receita de `tests/icone_de_atalho.py`, e compara o
resultado com o arquivo commitado. Isso detecta tanto troca de desenho quanto edicao de um
unico pixel, e e a unica comparacao que faz sentido entre um arquivo derivado e sua fonte.
"""
from __future__ import annotations

import io
import pathlib

import pytest
from PIL import Image, ImageChops

from tests.icone_de_atalho import ARTE_DE_RUNTIME, arte_derivada, bytes_da_arte


def _imagens_diferem(caminho: pathlib.Path) -> bool:
    """`True` se a arte regenerada divergir em algum pixel do arquivo em `caminho`.

    Compara **pixel**, nunca bytes: recompressao do mesmo desenho nao conta como deriva.
    """
    if not caminho.exists():
        raise AssertionError(
            f"arte de runtime ausente em {caminho}. Regenere com "
            "'python -m tests.icone_de_atalho' antes de rodar o teste de deriva."
        )
    commitada = Image.open(caminho).convert("RGB")
    regenerada = arte_derivada().convert("RGB")
    if commitada.size != regenerada.size:
        return True
    return ImageChops.difference(commitada, regenerada).getbbox() is not None


def test_a_arte_commitada_e_a_que_a_receita_produz():
    """`RF-10`. Se a canonica mudar e ninguem regenerar, este teste falha."""
    assert not _imagens_diferem(ARTE_DE_RUNTIME), (
        "a arte de runtime divergiu da canonica: alguem editou a arte, ou a canonica "
        "mudou e a derivada nao foi regerada. Rode: python -m tests.icone_de_atalho"
    )


def test_o_teste_de_deriva_e_sensivel_a_um_unico_pixel(tmp_path):
    """Prova que a comparacao **detecta** deriva, e nao apenas passa sempre.

    Sem esta prova, o teste acima poderia estar comparando algo consigo mesmo e passar
    por vacuidade - que e o modo de falha mais perigoso de um teste de fidelidade.
    """
    alterada = tmp_path / "um-pixel-a-mais.png"
    imagem = Image.open(ARTE_DE_RUNTIME).convert("RGB").copy()
    original = imagem.getpixel((90, 90))
    imagem.putpixel((90, 90), tuple((canal + 1) % 256 for canal in original))
    imagem.save(alterada, format="PNG", optimize=True)

    assert _imagens_diferem(alterada), (
        "um pixel alterado NAO foi detectado: a comparacao nao esta comparando pixel"
    )


def test_recompressao_do_mesmo_desenho_nao_e_deriva(tmp_path):
    """O caso que elimina a comparacao por `sha256` (`D-08`).

    O mesmo desenho, salvo com outra compressao, muda de bytes e **nao** muda de pixel.
    O teste de deriva tem de passar - comparar bytes daria alarme falso aqui.
    """
    reencodada = tmp_path / "mesmo-desenho-outra-compressao.png"
    Image.open(ARTE_DE_RUNTIME).convert("RGB").save(reencodada, format="PNG", compress_level=1)

    assert reencodada.read_bytes() != ARTE_DE_RUNTIME.read_bytes(), (
        "a recompressao nao mudou os bytes; o caso nao esta exercitando o que promete"
    )
    assert not _imagens_diferem(reencodada), (
        "recompressao do MESMO desenho foi tratada como deriva: e o alarme falso que a "
        "comparacao por sha256 produziria"
    )


def test_a_arte_de_runtime_esta_dentro_de_src():
    """`RF-04` e `D-03`: e o unico caminho que entra no contexto de build da imagem."""
    partes = ARTE_DE_RUNTIME.resolve().parts
    assert "src" in partes, f"a arte nao esta sob src/: {ARTE_DE_RUNTIME}"
    assert "static" not in partes, (
        f"a arte caiu numa pasta estatica: {ARTE_DE_RUNTIME}. src/static/ e proibida (W004)"
    )


def test_a_receita_esta_no_tests_e_nao_no_runtime():
    """`D-09`: `requirements.txt` e lista de RUNTIME e nao deve citar a biblioteca de imagem.

    O container nao precisa dela: a arte chega pronta dentro da imagem. Se ela entrar no
    arquivo de dependencias, o peso vai para a imagem por causa de um teste.
    """
    raiz = pathlib.Path(__file__).resolve().parent.parent
    conteudo = (raiz / "requirements.txt").read_text(encoding="utf-8").lower()
    for nome in ("pillow", "pil=="):
        assert nome not in conteudo, (
            f"'{nome}' apareceu em requirements.txt: e dependencia de TESTE (D-09)"
        )
