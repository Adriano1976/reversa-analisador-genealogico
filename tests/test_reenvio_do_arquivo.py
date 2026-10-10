"""T037 (feature `011-escolher-arquivo-da-lista`, regra `RN-17`): o reenvio de um arquivo.

## O que mudou, e o que NAO mudou

Pedido do operador em 2026-10-10. Antes, os TRES desfechos do reenvio davam a MESMA resposta
— "carregado!" —, e um deles era invisivel para quem enviava:

- **mesmo nome e mesmo conteudo**: nada era gravado (`RF-09`), e a tela dizia "carregado!";
- **mesmo nome e conteudo DIFERENTE**: nascia um SEGUNDO arquivo ao lado do antigo, e a lista
  ficava com duas linhas de mesmo rotulo — o caso medido na pasta real, com dois
  `Familias_Sergipanas.csv`;
- **nome novo**: nada mudava.

Agora cada desfecho tem a sua mensagem, e o do meio passou a **substituir**.

## A substituicao APOSENTA, e nao apaga

O operador escolheu essa alternativa de forma explicita. A `RN-07` continua valendo: a versao
anterior sai da lista e **continua no disco**. O teste que prende isso e
`test_a_versao_anterior_nao_e_apagada` — se ele cair, a aplicacao passou a destruir dado.

## Por que o nome visivel e a identidade

`RN-17`: e o nome que o operador deu. A comparacao usa o nome visivel **completo**, como o
operador o escreveu — entao um `arvore.csv` NAO e substituido por um envio de `arvore.ged`.
Essa escolha e conservadora de proposito (substituir menos e mais seguro do que substituir
demais), e o teste `test_nome_diferente_nao_e_substituido` a declara.
"""
from __future__ import annotations

import html
import io
import os
import re
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from ports.adaptadores import PASTA_DE_APOSENTADOS  # noqa: E402

GEDCOM = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n0 TRLR\n"
).encode("utf-8")
# O MESMO arquivo, atualizado: uma linha a mais antes do TRLR. Continua GEDCOM valido.
GEDCOM_ATUALIZADO = GEDCOM.replace(b"0 TRLR", b"1 NOTE versao dois\n0 TRLR")

NOME = "arvore.ged"


def _enviar(cliente, nome: str, conteudo: bytes = GEDCOM):
    return cliente.post("/", data={
        "action": "upload_gedcom",
        "gedcom": (io.BytesIO(conteudo), nome),
    }, content_type="multipart/form-data")


def _mensagem(resposta) -> str:
    """A mensagem do alerta, ja DESESCAPADA.

    O Jinja escapa `'` como `&#39;`, entao comparar com o texto cru falharia por um motivo que
    nao tem nada a ver com a regra — medido: a tela entrega `Arquivo &#39;arvore.ged&#39;
    carregado!`. Desescapar aqui deixa as assercoes falarem do que importa.
    """
    corpo = resposta.get_data(as_text=True)
    achado = re.search(r'role="alert">\s*([^<]+)', corpo)
    return html.unescape(achado.group(1).strip()) if achado else ""


def _arquivos(pasta: str) -> list[str]:
    return sorted(n for n in os.listdir(pasta) if not n.startswith("_"))


def _aposentados(pasta: str) -> list[str]:
    destino = os.path.join(pasta, PASTA_DE_APOSENTADOS)
    return sorted(os.listdir(destino)) if os.path.isdir(destino) else []


def _linhas(cliente) -> list[str]:
    """As linhas da tabela da aba de arvore: (rotulo, arquivos, tamanho)."""
    corpo = cliente.get("/").get_data(as_text=True)
    tabela = re.search(r"(?s)<table.*?</table>", corpo)
    if not tabela:
        return []
    saida = []
    for linha in re.findall(r"(?s)<tr>(.*?)</tr>", tabela.group(0))[1:]:
        celulas = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
            for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", linha)
        ]
        saida.append(" | ".join(celulas))
    return saida


class TestEnvioNovo:
    """O caminho comum nao pode ter mudado: o literal e contrato de tela congelado."""

    def test_envio_novo_mantem_a_mensagem_de_sempre(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload

        mensagem = _mensagem(_enviar(cliente, NOME))

        assert mensagem == f"Arquivo '{NOME}' carregado!", (
            "o literal do caminho comum mudou: ele e contrato de tela anterior a esta feature"
        )

    def test_envio_novo_grava_um_arquivo_e_nao_aposenta_nada(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload

        _enviar(cliente, NOME)

        assert len(_arquivos(pasta)) == 1
        assert _aposentados(pasta) == [], "um envio novo aposentou alguma coisa"


class TestReenvioIdentico:
    """Mesmo nome e mesmo conteudo: nada muda no disco, e agora o operador e avisado."""

    def test_o_reenvio_identico_avisa_que_ja_estava_armazenado(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        _enviar(cliente, NOME)

        mensagem = _mensagem(_enviar(cliente, NOME))

        assert "já estava armazenado" in mensagem, (
            "o segundo envio do MESMO arquivo continua dizendo 'carregado!': o operador nao tem "
            "como saber que a tentativa nao fez nada"
        )
        assert "mesmo conteúdo" in mensagem, (
            "o aviso tem de dizer que o conteudo e identico — sem isso, quem ATUALIZOU o arquivo "
            "e manteve o nome acha que o sistema ignorou a mudanca"
        )

    def test_o_reenvio_identico_nao_cria_arquivo_nem_aposenta(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _enviar(cliente, NOME)
        antes = _arquivos(pasta)

        _enviar(cliente, NOME)

        assert _arquivos(pasta) == antes, "o reenvio identico mexeu na pasta"
        assert _aposentados(pasta) == [], "o reenvio identico aposentou alguma coisa"

    def test_o_reenvio_identico_nao_muda_a_lista(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        _enviar(cliente, NOME)
        antes = _linhas(cliente)

        _enviar(cliente, NOME)

        assert _linhas(cliente) == antes


class TestArquivoAtualizado:
    """`RN-17`: mesmo nome, conteudo diferente. A versao anterior sai da lista, e nao do disco."""

    def test_a_versao_anterior_sai_da_lista_e_a_nova_entra(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        _enviar(cliente, NOME)
        antigos = _arquivos(pasta)

        resposta = _enviar(cliente, NOME, GEDCOM_ATUALIZADO)

        assert "atualizado" in _mensagem(resposta), (
            "a substituicao nao foi anunciada: o operador precisa saber que a versao anterior saiu"
        )
        assert len(_arquivos(pasta)) == 1, "a versao anterior continuou na pasta de upload"
        assert _arquivos(pasta) != antigos, "o arquivo servido continua sendo o antigo"
        assert _aposentados(pasta) == antigos, "a versao anterior nao foi para a pasta de aposentados"

    def test_a_versao_anterior_nao_e_apagada(self, cliente_de_upload):
        """`RN-07`: o teste mais importante desta classe. Nada de dado do operador pode sumir."""
        _app, cliente, pasta = cliente_de_upload
        _enviar(cliente, NOME)
        antigos = _arquivos(pasta)

        _enviar(cliente, NOME, GEDCOM_ATUALIZADO)

        guardado = os.path.join(pasta, PASTA_DE_APOSENTADOS, antigos[0])
        assert os.path.isfile(guardado), "a versao anterior foi APAGADA, e nao aposentada"
        with open(guardado, "rb") as fh:
            assert fh.read() == GEDCOM, "o conteudo da versao anterior mudou"

    def test_a_lista_fica_com_UMA_linha_daquele_nome(self, cliente_de_upload):
        """O defeito que a `RN-17` fecha: duas linhas com o mesmo rotulo."""
        _app, cliente, _pasta = cliente_de_upload
        _enviar(cliente, NOME)

        _enviar(cliente, NOME, GEDCOM_ATUALIZADO)

        linhas = _linhas(cliente)
        assert len(linhas) == 1, f"a lista ficou com {len(linhas)} linhas para um nome so: {linhas}"
        assert linhas[0].startswith("arvore |")

    def test_a_mensagem_diz_que_a_versao_anterior_continua_guardada(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        _enviar(cliente, NOME)

        mensagem = _mensagem(_enviar(cliente, NOME, GEDCOM_ATUALIZADO))

        assert "continua guardada" in mensagem, (
            "a mensagem nao avisa que a versao anterior sobrevive: o operador vai achar que perdeu"
        )

    def test_nome_diferente_nao_e_substituido(self, cliente_de_upload):
        """A identidade e o nome visivel COMPLETO. Substituir menos e mais seguro.

        Este teste declara a escolha conservadora da `RN-17`. Se a regra for ampliada para
        atravessar a extensao — ou para casar o radical sem extensao —, este teste e o lugar de
        registrar a mudanca.

        Ele envia outro `.ged`, e nao um `.csv`: o formulario de envio e o de GEDCOM, e o
        conteudo de um CSV e recusado pela validacao de conteudo (`RF-10`). Medido: a tentativa
        com CSV devolve recusa e **nenhum** arquivo novo, o que faria o teste medir a recusa em
        vez da substituicao.
        """
        _app, cliente, pasta = cliente_de_upload
        _enviar(cliente, "arvore.ged")
        _enviar(cliente, "outra-arvore.ged")

        assert len(_arquivos(pasta)) == 2, "um nome diferente foi tratado como o mesmo arquivo"
        assert _aposentados(pasta) == []

    def test_o_envio_identico_continua_sendo_identico_depois_da_substituicao(
        self, cliente_de_upload
    ):
        """Depois de atualizar, reenviar a versao NOVA tambem e reconhecido como identico."""
        _app, cliente, _pasta = cliente_de_upload
        _enviar(cliente, NOME)
        _enviar(cliente, NOME, GEDCOM_ATUALIZADO)

        mensagem = _mensagem(_enviar(cliente, NOME, GEDCOM_ATUALIZADO))

        assert "já estava armazenado" in mensagem
        assert "atualizado" not in mensagem
