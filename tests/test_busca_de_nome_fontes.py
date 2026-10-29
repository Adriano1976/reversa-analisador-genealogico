"""As duas fontes de nomes: arvore e relatorio (feature 052).

## O que este arquivo prende

- cada fonte normaliza com a SUA autoridade (`normalizar` na arvore, `norm_name` no
  relatorio) — e e o que impede a busca de discordar do dossie ou do matching;
- a fonte entrega ficha **so** dos identificadores pedidos, e nao de 35 mil pessoas;
- referencia que nao resolve devolve `None` (o `404` da rota), e nao tupla vazia;
- relatorio ilegivel devolve tupla vazia **mais o aviso** — a secao irma continua
  respondendo (`RF-13`).
"""
from __future__ import annotations

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (RAIZ, os.path.join(RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.busca_arvores import GED_DA_BUSCA  # noqa: E402
from fixtures.busca_relatorios import CSV_DE_MATCHES  # noqa: E402
from ports.adaptadores import (  # noqa: E402
    ArmazenamentoEmDisco,
    CarregadorDeArvoresGedcom,
)
from ports.fontes_de_nomes import (  # noqa: E402
    AVISO_RELATORIO_ILEGIVEL,
    NomesDaArvoreGedcom,
    NomesDoArquivoDeMatches,
)

#: Chave de conteudo de forma valida. O resolvedor valida a FORMA da referencia; a
#: chave nao precisa casar com o conteudo do arquivo de teste.
CHAVE = "080e7943572d2652"

ARVORE = f"{CHAVE}__arvore.ged"
RELATORIO = f"{CHAVE}__relatorio.csv"


@pytest.fixture
def pasta(tmp_path):
    return tmp_path


@pytest.fixture
def armazenamento(pasta):
    return ArmazenamentoEmDisco(str(pasta))


def _guardar(pasta, nome: str, conteudo: bytes) -> str:
    caminho = pasta / nome
    caminho.write_bytes(conteudo)
    return str(caminho)


class TestFonteDaArvore:
    def test_entrega_um_candidato_por_pessoa(self, pasta, armazenamento):
        _guardar(pasta, ARVORE, GED_DA_BUSCA.encode("utf-8"))
        fonte = NomesDaArvoreGedcom(CarregadorDeArvoresGedcom(armazenamento))

        candidatos, aviso = fonte.nomes(ARVORE, "unico")

        assert aviso is None
        assert len(candidatos) == 3
        assert all(c.origem == "arvore" for c in candidatos)

    def test_normaliza_com_a_autoridade_do_dossie(self, pasta, armazenamento):
        _guardar(pasta, ARVORE, GED_DA_BUSCA.encode("utf-8"))
        fonte = NomesDaArvoreGedcom(CarregadorDeArvoresGedcom(armazenamento))

        candidatos, _ = fonte.nomes(ARVORE, "unico")

        normalizados = {c.normalizado for c in candidatos}
        assert "jose silva e souza" in normalizados

    def test_a_ficha_e_pedida_so_para_os_identificadores_escolhidos(self, pasta, armazenamento):
        _guardar(pasta, ARVORE, GED_DA_BUSCA.encode("utf-8"))
        fonte = NomesDaArvoreGedcom(CarregadorDeArvoresGedcom(armazenamento))

        fichas = fonte.fichas(ARVORE, "unico", ("@I1@",))

        assert set(fichas) == {"@I1@"}
        assert "Silva" in fichas["@I1@"]["name"]

    def test_referencia_que_nao_resolve_devolve_none(self, armazenamento):
        fonte = NomesDaArvoreGedcom(CarregadorDeArvoresGedcom(armazenamento))

        candidatos, aviso = fonte.nomes("inexistente.ged", "unico")

        assert candidatos is None
        assert aviso is None

    def test_sem_referencia_devolve_tupla_vazia(self, armazenamento):
        fonte = NomesDaArvoreGedcom(CarregadorDeArvoresGedcom(armazenamento))

        assert fonte.nomes(None, "unico") == ((), None)


class TestFonteDoRelatorio:
    def test_agrega_o_centimorgan_por_nome(self, pasta, armazenamento):
        conteudo = "Name,Total cM,Kit\nMaria Silva,100.0,AB1\nMaria Silva,20.0,AB1\n"
        _guardar(pasta, RELATORIO, conteudo.encode("utf-8"))
        fonte = NomesDoArquivoDeMatches(armazenamento)

        candidatos, aviso = fonte.nomes(RELATORIO, "unico")

        assert aviso is None
        assert len(candidatos) == 1
        assert candidatos[0].dados["centimorgans"] == pytest.approx(120.0)

    def test_usa_norm_name_como_autoridade(self, pasta, armazenamento):
        _guardar(pasta, RELATORIO, CSV_DE_MATCHES.encode("utf-8"))
        fonte = NomesDoArquivoDeMatches(armazenamento)

        candidatos, _ = fonte.nomes(RELATORIO, "unico")

        normalizados = {c.normalizado for c in candidatos}
        assert "maria silva" in normalizados

    def test_relatorio_ilegivel_devolve_aviso_sem_derrubar(self, pasta, armazenamento, monkeypatch):
        _guardar(pasta, RELATORIO, CSV_DE_MATCHES.encode("utf-8"))
        fonte = NomesDoArquivoDeMatches(armazenamento)

        def estoura(_caminho):
            raise ValueError("conteudo inesperado")

        monkeypatch.setattr("ports.fontes_de_nomes.ler_segmentos_gedmatch", estoura)

        candidatos, aviso = fonte.nomes(RELATORIO, "unico")

        assert candidatos == ()
        assert aviso == AVISO_RELATORIO_ILEGIVEL

    def test_referencia_que_nao_resolve_devolve_none(self, armazenamento):
        fonte = NomesDoArquivoDeMatches(armazenamento)

        assert fonte.nomes("nao_existe.csv", "unico") == (None, None)

    def test_a_fonte_de_matches_nao_tem_ficha(self, pasta, armazenamento):
        _guardar(pasta, RELATORIO, CSV_DE_MATCHES.encode("utf-8"))
        fonte = NomesDoArquivoDeMatches(armazenamento)

        assert fonte.fichas(RELATORIO, "unico", ("maria silva",)) == {}
