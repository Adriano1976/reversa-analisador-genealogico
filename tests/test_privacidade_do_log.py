"""Testes da privacidade do log (`T010` da feature 049).

O teste mais valioso desta feature e o ultimo deste arquivo: rodar uma analise com dado
sintetico e afirmar que **nenhum nome** da arvore aparece no log capturado. E a forma
executavel do Principio I, que lista `logs` entre os caminhos por onde dado real de terceiro
nao pode passar.

Os primeiros protegem a mascara — inclusive no traceback, que e a parte que o plano anexado
declarou nao ter sido testada em prototipo.
"""
import io
import logging
import os
import re
import sys

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

from utils import logs  # noqa: E402  (o caminho acima precisa vir antes)

GEDCOM_COM_NOMES = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Joao /Silva/\n"
    "1 SEX M\n"
    "0 @I2@ INDI\n"
    "1 NAME Maria /Souza/\n"
    "1 SEX F\n"
    "0 @F1@ FAM\n"
    "1 HUSB @I1@\n"
    "1 WIFE @I2@\n"
    "0 TRLR\n"
)

CSV_DE_MATCHES = b"Name,cM\nJoao Silva,150\n"


def _ler_tudo() -> str:
    """O conteudo dos tres destinos em disco, concatenado."""
    pasta = logs.pasta_de_logs()
    if not os.path.isdir(pasta):
        return ""
    partes = []
    for nome in sorted(os.listdir(pasta)):
        if nome.endswith(".log"):
            with open(os.path.join(pasta, nome), encoding="utf-8") as arquivo:
                partes.append(arquivo.read())
    return "\n".join(partes)


def _referencia_armazenada(cliente, conteudo: bytes) -> str:
    """Faz o upload do GEDCOM e devolve a referencia que o formulario devolve."""
    pagina = cliente.post(
        "/",
        data={"action": "upload_gedcom", "gedcom": (io.BytesIO(conteudo), "arvore.ged")},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    achado = re.search(r'name="gedcom_filename" value="([^"]+)"', pagina)
    assert achado, "o envio nao devolveu a referencia do arquivo gravado"
    return achado.group(1)


def test_a_mascara_cobre_identificador_de_kit_e_email():
    texto = logs.mascarar("kit AB1234567, contato joao.silva@example.com")
    assert "AB1234567" not in texto
    assert "joao.silva@example.com" not in texto
    assert "<kit>" in texto and "<email>" in texto


def test_a_mascara_preserva_o_resto_da_mensagem():
    assert logs.mascarar("arquivo recusado: AB1234567 nao e GEDCOM") == (
        "arquivo recusado: <kit> nao e GEDCOM"
    )


def test_a_mascara_alcanca_o_traceback():
    """O formatador chamaria `formatException` na excecao CRUA se `exc_info` sobrevivesse."""
    try:
        raise KeyError("AB1234567 joao.silva@example.com")
    except KeyError:
        registro = logging.LogRecord(
            "teste", logging.ERROR, __file__, 1, "falhou ao ler", (), sys.exc_info()
        )

    logs.FiltroDePrivacidade().filter(registro)

    assert registro.exc_info is None, "exc_info sobreviveu e a excecao seria formatada crua"
    assert registro.exc_text, "o traceback nao foi materializado"
    assert "AB1234567" not in registro.exc_text
    assert "joao.silva@example.com" not in registro.exc_text
    assert "<kit>" in registro.exc_text


def test_a_mascara_alcanca_os_argumentos_da_mensagem():
    registro = logging.LogRecord(
        "teste", logging.INFO, __file__, 1, "kit=%s email=%s",
        ("AB1234567", "maria@example.com"), None,
    )
    logs.FiltroDePrivacidade().filter(registro)
    assert "AB1234567" not in registro.getMessage()
    assert "maria@example.com" not in registro.getMessage()


def test_nenhum_nome_da_arvore_aparece_no_log(cliente_de_upload):
    """O teste que a feature existe para ter: analise com nomes no arquivo e log sem eles."""
    _, cliente, _ = cliente_de_upload
    referencia = _referencia_armazenada(cliente, GEDCOM_COM_NOMES.encode())

    cliente.post(
        "/",
        data={
            "action": "dna_analysis",
            "gedcom_filename": referencia,
            "root_name": "Joao Silva",
            "matches_csv": (io.BytesIO(CSV_DE_MATCHES), "matches.csv"),
        },
        content_type="multipart/form-data",
    )

    log = _ler_tudo()
    assert log.strip(), "nada foi para o log — o teste passaria por vacuidade"
    for nome in ("Joao", "Silva", "Maria", "Souza"):
        assert nome not in log, f"o nome {nome!r} apareceu no log"
