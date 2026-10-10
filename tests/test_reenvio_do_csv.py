"""T038 (feature `011-escolher-arquivo-da-lista`, regra `RN-17`): o reenvio do CSV.

## Por que este arquivo existe separado do `test_reenvio_do_arquivo.py`

Porque o CSV **nao tem tela de envio propria**: ele entra dentro do formulario de ANALISE
(`action=dna_analysis`, campo `matches_csv`), e o caminho de codigo e outro. A regra, porem, e
a MESMA — a extração de `application/reenvio.py` existe justamente para nao haver duas
verdades sobre ela. Este arquivo mede a regra pelo OUTRO chamador.

## O defeito que a `T038` fecha, medido na pasta do operador

Antes dela, reenviar um CSV com conteudo novo deixava DOIS arquivos com o mesmo nome visivel, e
como a chave difere os dois viravam itens separados: a aba de DNA mostrava duas linhas com o
rotulo `Familias Sergipanas`, de 30.591 e 30.968 bytes. Agora a versao anterior e aposentada e
a aba fica com UMA linha.

## A analise tem de continuar funcionando

A substituicao acontece ANTES da analise, e o aviso dela acompanha a mensagem do resultado em
vez de substitui-la. Os testes conferem as duas coisas: que a versao anterior foi aposentada e
que o resultado da analise continua saindo na tela.
"""
from __future__ import annotations

import io
import os
import re
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src"), os.path.join(_RAIZ, "tests")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from fixtures.sample_dna import DNA_CSV_UTF8, DNA_GED  # noqa: E402
from ports.adaptadores import PASTA_DE_APOSENTADOS  # noqa: E402

NOME_DO_CSV = "matches.csv"
# O MESMO relatorio, com uma quebra de linha a mais no fim: conteudo DIFERENTE (chave
# diferente), conteudo LIDO igual. E o caso do "arquivo atualizado" sem mexer no que a analise
# interpreta, para o teste medir a substituicao e nao uma mudanca de resultado.
CSV_ATUALIZADO = DNA_CSV_UTF8 + "\n"


def _carregar_arvore(cliente) -> str:
    pagina = cliente.post(
        "/",
        data={"action": "upload_gedcom",
              "gedcom": (io.BytesIO(DNA_GED.encode()), "arvore.ged")},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    chave = re.search(r'name="gedcom_filename" value="([^"]+)"', pagina)
    assert chave, "o upload não devolveu a chave da árvore"
    return chave.group(1)


def _analisar(cliente, chave: str, conteudo: str):
    return cliente.post(
        "/",
        data={"action": "dna_analysis", "gedcom_filename": chave,
              "root_name": "Carlos Silva Souza",
              "matches_csv": (io.BytesIO(conteudo.encode()), NOME_DO_CSV)},
        content_type="multipart/form-data",
    )


def _mensagem(resposta) -> str:
    import html
    corpo = resposta.get_data(as_text=True)
    achado = re.search(r'role="alert">\s*([^<]+)', corpo)
    return html.unescape(achado.group(1).strip()) if achado else ""


def _csvs(pasta: str) -> list[str]:
    return sorted(n for n in os.listdir(pasta) if n.endswith(".csv"))


def _aposentados(pasta: str) -> list[str]:
    destino = os.path.join(pasta, PASTA_DE_APOSENTADOS)
    return sorted(os.listdir(destino)) if os.path.isdir(destino) else []


def _linhas_da_aba_de_dna(cliente) -> list[str]:
    corpo = cliente.get("/").get_data(as_text=True)
    tabelas = re.findall(r"(?s)<table.*?</table>", corpo)
    if len(tabelas) < 2:
        return []
    saida = []
    for linha in re.findall(r"(?s)<tr>(.*?)</tr>", tabelas[1])[1:]:
        celulas = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
            for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", linha)
        ]
        saida.append(" | ".join(celulas))
    return saida


class TestReenvioDoCsv:
    """`RN-17` pelo caminho da analise de DNA."""

    def test_o_csv_atualizado_substitui_a_versao_anterior(self, cliente_de_upload):
        _app, cliente, pasta = cliente_de_upload
        chave = _carregar_arvore(cliente)
        assert _analisar(cliente, chave, DNA_CSV_UTF8).status_code == 200
        antigos = _csvs(pasta)
        assert len(antigos) == 1, "pre-condicao: o primeiro CSV tem de estar gravado"

        resposta = _analisar(cliente, chave, CSV_ATUALIZADO)

        assert resposta.status_code == 200
        assert _csvs(pasta) != antigos, "o CSV gravado continua sendo o antigo"
        assert len(_csvs(pasta)) == 1, (
            "a versao anterior continuou na pasta de upload: e o defeito dos dois "
            "`Familias_Sergipanas.csv` de mesmo rotulo"
        )
        assert _aposentados(pasta) == antigos, "a versao anterior nao foi aposentada"

    def test_a_versao_anterior_do_csv_nao_e_apagada(self, cliente_de_upload):
        """`RN-07` vale para o CSV tambem, e nao so para o GEDCOM."""
        _app, cliente, pasta = cliente_de_upload
        chave = _carregar_arvore(cliente)
        _analisar(cliente, chave, DNA_CSV_UTF8)
        antigos = _csvs(pasta)

        _analisar(cliente, chave, CSV_ATUALIZADO)

        guardado = os.path.join(pasta, PASTA_DE_APOSENTADOS, antigos[0])
        assert os.path.isfile(guardado), "a versao anterior do CSV foi APAGADA"
        with open(guardado, "r", encoding="utf-8") as fh:
            assert fh.read() == DNA_CSV_UTF8, "o conteudo da versao anterior mudou"

    def test_a_aba_de_dna_fica_com_UMA_linha_daquele_nome(self, cliente_de_upload):
        _app, cliente, _pasta = cliente_de_upload
        chave = _carregar_arvore(cliente)
        _analisar(cliente, chave, DNA_CSV_UTF8)

        _analisar(cliente, chave, CSV_ATUALIZADO)

        linhas = _linhas_da_aba_de_dna(cliente)
        assert len(linhas) == 1, f"a aba de DNA ficou com {len(linhas)} linhas: {linhas}"
        assert linhas[0].startswith("matches |")

    def test_o_aviso_da_substituicao_nao_engole_o_resultado_da_analise(self, cliente_de_upload):
        """A analise e o assunto da tela; a substituicao e uma nota sobre o insumo dela."""
        _app, cliente, _pasta = cliente_de_upload
        chave = _carregar_arvore(cliente)
        _analisar(cliente, chave, DNA_CSV_UTF8)

        mensagem = _mensagem(_analisar(cliente, chave, CSV_ATUALIZADO))

        assert "pasta de aposentados" in mensagem, (
            "a substituicao do CSV nao foi anunciada: o operador nao sabe que a versao anterior saiu"
        )
        # O texto do RESULTADO tem de continuar na frente. Medido: a mensagem completa e
        # "1 conexões encontradas. 0 descartadas. O CSV 'matches.csv' substituiu a versão
        # anterior, ...". A primeira versao deste teste procurava "Ana Silva Souza", que esta
        # na TABELA de resultados e nao na mensagem — a assercao falhava com o comportamento
        # certo.
        assert "conexões encontradas" in mensagem, (
            "o aviso substituiu a mensagem do resultado da analise em vez de acompanha-la"
        )
        assert mensagem.index("conexões encontradas") < mensagem.index("pasta de aposentados"), (
            "o aviso veio ANTES do resultado: a analise e o assunto da tela"
        )

    def test_reenviar_o_mesmo_csv_nao_aposenta_nada(self, cliente_de_upload):
        """Conteudo identico continua sendo o caso em que NADA acontece."""
        _app, cliente, pasta = cliente_de_upload
        chave = _carregar_arvore(cliente)
        _analisar(cliente, chave, DNA_CSV_UTF8)
        antes = _csvs(pasta)

        _analisar(cliente, chave, DNA_CSV_UTF8)

        assert _csvs(pasta) == antes
        assert _aposentados(pasta) == [], "o reenvio identico aposentou o proprio CSV"
