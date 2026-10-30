"""Favicon transparente das telas de identidade (emenda E005).

## Por que existe um favicon separado do icone de atalho

Os dois alvos pedem coisas opostas. A tela inicial do celular compoe a
transparencia sobre **preto**, entao o `apple-touch-icon` precisa ser opaco
(`tests/test_icone_de_atalho.py`). A aba do navegador mostra o **fundo da propria
arte**, e o quadrado branco do icone opaco aparecia como moldura. A correcao e uma
derivada transparente da mesma canonica (`tests/favicon_da_aba.py`).

## A prova de transparencia e estrutural

O tipo de cor **6** do PNG declara canal alfa; a leitura do canal confirma que ha
pixel totalmente transparente. O caminho opaco continua com tipo **2**, e os dois
testes juntos provam que ninguem trocou um pelo outro.
"""
from __future__ import annotations

import io
import struct

CAMINHO = "/favicon.png"

#: Herdados da receita (`tests/favicon_da_aba.py`).
LADO = 128
TAMANHO_ESPERADO = 14456


def _cabecalho_png(corpo: bytes):
    """`(largura, altura, bits, tipo_de_cor)` do IHDR, sem biblioteca de imagem."""
    assert corpo[:8] == b"\x89PNG\r\n\x1a\n", "o corpo nao comeca com assinatura PNG"
    assert corpo[12:16] == b"IHDR", "o primeiro chunk nao e IHDR"
    return struct.unpack(">IIBB", corpo[16:26])


def test_a_rota_do_favicon_e_publica_e_responde_200(app_com_contas):
    """Rota de arte e publica (`P-08`); com a guarda ligada, `302` seria regressao."""
    resposta = app_com_contas.cliente.get(CAMINHO)

    assert resposta.status_code == 200, f"esperado 200, veio {resposta.status_code}"


def test_o_tipo_de_conteudo_e_de_imagem(app_com_contas):
    resposta = app_com_contas.cliente.get(CAMINHO)

    assert resposta.headers["Content-Type"].startswith("image/")


def test_o_favicon_tem_128_por_128(app_com_contas):
    corpo = app_com_contas.cliente.get(CAMINHO).get_data()

    largura, altura, _bits, _tipo = _cabecalho_png(corpo)
    assert (largura, altura) == (LADO, LADO)


def test_o_favicon_tem_canal_alfa(app_com_contas):
    corpo = app_com_contas.cliente.get(CAMINHO).get_data()

    _l, _a, _b, tipo_de_cor = _cabecalho_png(corpo)
    assert tipo_de_cor == 6, (
        f"tipo de cor {tipo_de_cor}: esperado 6 (RGBA). O 2 e o do icone de atalho, "
        "que e opaco de proposito"
    )


def test_ha_pixels_totalmente_transparentes(app_com_contas):
    """A prova que o cabecalho sozinho nao da: o alfa chega a zero em algum pixel."""
    from PIL import Image

    corpo = app_com_contas.cliente.get(CAMINHO).get_data()
    imagem = Image.open(io.BytesIO(corpo)).convert("RGBA")

    assert imagem.getchannel("A").getextrema()[0] == 0, (
        "nenhum pixel transparente: o fundo foi composto em algum lugar da receita"
    )


def test_o_tamanho_e_o_da_receita(app_com_contas):
    corpo = app_com_contas.cliente.get(CAMINHO).get_data()

    assert len(corpo) == TAMANHO_ESPERADO, (
        f"{len(corpo)} bytes, esperado {TAMANHO_ESPERADO}. Confira "
        "tests/favicon_da_aba.py antes de suspeitar da rota."
    )


def test_a_resposta_traz_etag_e_revalida_sem_corpo(app_com_contas):
    primeira = app_com_contas.cliente.get(CAMINHO)
    marca = primeira.headers.get("ETag")
    assert marca, "a resposta nao trouxe ETag"

    segunda = app_com_contas.cliente.get(CAMINHO, headers={"If-None-Match": marca})

    assert segunda.status_code == 304
    assert segunda.get_data() == b""


def test_arte_ausente_degrada_com_404(app_com_contas, monkeypatch):
    monkeypatch.setitem(
        app_com_contas.app.config, "ARTE_DO_FAVICON", "caminho/que/nao/existe.png"
    )

    assert app_com_contas.cliente.get(CAMINHO).status_code == 404
    assert app_com_contas.cliente.get("/login").status_code == 200


def test_as_telas_de_identidade_declaram_o_favicon_transparente(app_com_contas):
    corpo = app_com_contas.cliente.get("/login").get_data(as_text=True)

    assert 'rel="icon"' in corpo
    assert 'href="/favicon.png"' in corpo
    assert 'rel="apple-touch-icon" href="/apple-touch-icon.png"' in corpo
