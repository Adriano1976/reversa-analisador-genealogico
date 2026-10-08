"""Rota do icone de atalho (`T004` e `T006` da feature 009).

## O que este arquivo prova

O contrato de `interfaces/apple-touch-icon.md`. A prova de opacidade e **estrutural**:
o formato PNG declara o tipo de cor no proprio cabecalho, e o tipo **2** e `truecolor`
sem canal alfa. Nao existe pixel transparente em um PNG cujo cabecalho diz que nao ha
canal alfa, e isso dispensa a biblioteca de imagem aqui - o que importa porque ela nao
esta em `requirements.txt` (`D-09`).

O teste que prova que a **tela nao mudou** compara o `sha256` do HTML servido com o valor
medido **antes** de a rota existir (23.906 bytes). Ele nao e um teste de comportamento
novo: e a guarda do `RF-05` e da `RN-02`, e por isso ele ja passa antes da rota.
"""
from __future__ import annotations

import hashlib
import struct

import pytest

CAMINHO_DO_ICONE = "/apple-touch-icon.png"

#: Lado e tamanho da arte derivada. Herdados da receita (`tests/icone_de_atalho.py`).
LADO = 180
TAMANHO_ESPERADO = 16504

#: `sha256` do HTML de `GET /` medido em 2026-10-08, ANTES de a rota existir.
#: 23.906 bytes. Qualquer mudanca aqui e mudanca de tela, e nao desta feature.
SHA_DA_TELA = "4b7f0b0cbe27c11e5ea8d436a49957f5b2d371735a89986ad96320fb245f02fb"


def _cabecalho_png(corpo: bytes):
    """`(largura, altura, bits, tipo_de_cor)` lidos do IHDR, sem biblioteca de imagem."""
    assert corpo[:8] == b"\x89PNG\r\n\x1a\n", "o corpo nao comeca com assinatura PNG"
    assert corpo[12:16] == b"IHDR", "o primeiro chunk nao e IHDR"
    return struct.unpack(">IIBB", corpo[16:26])


@pytest.fixture
def resposta(cliente_de_upload):
    """A resposta da rota do icone, no app montado com pasta de upload temporaria."""
    _app, cliente, _pasta = cliente_de_upload
    return cliente.get(CAMINHO_DO_ICONE)


# --- T004: a rota existe e entrega a arte certa -------------------------------


def test_a_rota_do_icone_responde_200(resposta):
    """`RF-01`. Falha antes da rota existir, com `404`."""
    assert resposta.status_code == 200, (
        f"esperado 200 em {CAMINHO_DO_ICONE}, veio {resposta.status_code}"
    )


def test_o_tipo_de_conteudo_e_de_imagem(resposta):
    """`RF-01`: o tipo declarado e de imagem, e nao `text/html` do formulario."""
    tipo = resposta.headers.get("Content-Type", "")
    assert tipo.startswith("image/"), f"Content-Type inesperado: {tipo!r}"


def test_o_icone_tem_180_por_180(resposta):
    """`RF-02`. A dimensao e lida do cabecalho do PNG, nao estimada pelo tamanho."""
    largura, altura, _bits, _tipo = _cabecalho_png(resposta.get_data())
    assert (largura, altura) == (LADO, LADO), f"dimensao {largura}x{altura}, esperado {LADO}x{LADO}"


def test_o_icone_nao_tem_canal_alfa(resposta):
    """`RF-03`, por propriedade do formato.

    O tipo de cor **2** e `truecolor` sem canal alfa. E a prova mais forte de opacidade
    que existe sem decodificar pixel: nao ha onde guardar transparencia. Servir a arte
    **canonica** aqui daria tipo 6, e o icone ficaria com fundo preto no aparelho.
    """
    _l, _a, _b, tipo_de_cor = _cabecalho_png(resposta.get_data())
    assert tipo_de_cor == 2, (
        f"tipo de cor {tipo_de_cor}: esperado 2 (truecolor sem alfa). "
        "6 significaria canal alfa, e transparencia vira fundo preto no atalho."
    )


def test_o_tamanho_e_o_da_receita(resposta):
    """A ancora da receita: denuncia reamostragem, fundo ou compressao diferentes."""
    assert len(resposta.get_data()) == TAMANHO_ESPERADO, (
        f"{len(resposta.get_data())} bytes, esperado {TAMANHO_ESPERADO}. "
        "Confira a receita em tests/icone_de_atalho.py antes de suspeitar da rota."
    )


# --- T004: a tela nao mudou ---------------------------------------------------


def test_a_tela_nao_mudou_um_byte(cliente_de_upload):
    """`RF-05` e `RN-02`: `GET /` identico ao de antes da feature, byte a byte."""
    _app, cliente, _pasta = cliente_de_upload
    corpo = cliente.get("/").get_data()
    assert hashlib.sha256(corpo).hexdigest() == SHA_DA_TELA, (
        f"a tela mudou: {len(corpo)} bytes. Esperado {SHA_DA_TELA[:16]}... "
        "Esta feature NAO pode tocar no template."
    )


def test_a_tela_nao_declara_o_icone_de_atalho(cliente_de_upload):
    """`RN-02`: a descoberta e por caminho convencional, sem declaracao no documento."""
    _app, cliente, _pasta = cliente_de_upload
    corpo = cliente.get("/").get_data().decode("utf-8")
    assert "apple-touch-icon" not in corpo, (
        "a tela passou a declarar o icone de atalho; a decisao era NAO tocar no template"
    )


def test_a_tela_mantem_o_icone_da_aba_embutido(cliente_de_upload):
    """`RF-09`: o icone da aba continua sendo o `data URI`, e nao uma segunda rota."""
    _app, cliente, _pasta = cliente_de_upload
    corpo = cliente.get("/").get_data().decode("utf-8")
    assert corpo.count('rel="icon"') == 1, "o icone da aba sumiu ou foi duplicado"
    assert corpo.count("data:image") == 1, "o icone da aba deixou de ser embutido"


# --- T006: metodo, cache, caminhos nao servidos e ausencia da arte ------------


def test_escrita_no_caminho_do_icone_e_recusada(cliente_de_upload):
    """`RF-06`: a rota e de leitura. A recusa sai do roteador, sem codigo nosso."""
    _app, cliente, _pasta = cliente_de_upload
    recusa = cliente.post(CAMINHO_DO_ICONE, data={"qualquer": "coisa"})
    assert recusa.status_code == 405, (
        f"escrita no icone devolveu {recusa.status_code}, esperado 405 (metodo nao permitido)"
    )


def test_a_resposta_traz_marca_de_versao(resposta):
    """`RF-07`: sem marca de versao o cliente nao tem como revalidar barato."""
    assert resposta.headers.get("ETag"), "a resposta nao trouxe ETag"


def test_requisicao_repetida_nao_traz_corpo(resposta, cliente_de_upload):
    """`RF-07`: a rebusca com a marca de versao responde 'nao modificado', sem corpo."""
    _app, cliente, _pasta = cliente_de_upload
    marca = resposta.headers["ETag"]
    repetida = cliente.get(CAMINHO_DO_ICONE, headers={"If-None-Match": marca})
    assert repetida.status_code == 304, (
        f"rebusca devolveu {repetida.status_code}, esperado 304"
    )
    assert repetida.get_data() == b"", "a resposta de 'nao modificado' trouxe corpo"


def test_nenhuma_validade_longa_de_cache(resposta):
    """`RF-07` e `D-05`: a arte foi trocada duas vezes em um dia.

    Uma validade de um ano congelaria o cliente que ja tivesse buscado, e o `ETag` nao
    salva - ele so age depois de a validade expirar.
    """
    cabecalho = resposta.headers.get("Cache-Control", "")
    if "max-age" in cabecalho:
        valor = int(cabecalho.split("max-age=")[1].split(",")[0].strip())
        assert valor <= 86400, (
            f"Cache-Control declara {valor}s de validade: e longo demais para uma arte "
            "que muda. O limite desta feature e um dia (RF-07)"
        )


@pytest.mark.parametrize("caminho", ["/apple-touch-icon-precomposed.png", "/favicon.ico"])
def test_os_caminhos_nao_servidos_continuam_sem_resposta(cliente_de_upload, caminho):
    """`RF-11` e `RN-09`: nenhum caminho sem consumidor foi criado.

    O alias legado pertence a sistemas anteriores; e o `favicon.ico` so e buscado quando
    o documento NAO declara icone - e o template declara. Criar qualquer um dos dois
    repetiria a divida #17, que este projeto ja fechou.
    """
    _app, cliente, _pasta = cliente_de_upload
    assert cliente.get(caminho).status_code == 404, (
        f"{caminho} passou a responder: e superficie sem consumidor (RN-09)"
    )


def test_a_tela_continua_de_pe_sem_a_arte(cliente_de_upload, monkeypatch):
    """`RN-08`: o icone ausente degrada, e nao derruba nada.

    Aponta a configuracao para um caminho inexistente em vez de mexer no arquivo: o teste
    nao pode alterar a arte do repositorio para provar um caso de ausencia.
    """
    app, cliente, _pasta = cliente_de_upload
    monkeypatch.setitem(app.config, "ARTE_DO_ICONE", "caminho/que/nao/existe.png")

    assert cliente.get(CAMINHO_DO_ICONE).status_code == 404
    tela = cliente.get("/")
    assert tela.status_code == 200, "a tela caiu por causa do icone ausente (RN-08)"
    assert hashlib.sha256(tela.get_data()).hexdigest() == SHA_DA_TELA, (
        "a tela mudou de conteudo quando a arte ficou ausente"
    )

