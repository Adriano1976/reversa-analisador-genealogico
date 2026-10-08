"""Sonda de reproducao do BUG-20260929-QMLY.

Mede o comportamento REAL do caminho de upload do legado. Nao altera o projeto:
roda tudo dentro de um diretorio temporario proprio.

Uso:
    py -3.14 .pytest-tmp/probe-qmly.py
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "analisador-genealogico"))

GEDCOM_SIMPLE = (
    "0 HEAD\n"
    "1 SOUR TEST\n"
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
).encode("utf-8")


def secao(titulo: str) -> None:
    print()
    print("=" * 72)
    print(titulo)
    print("=" * 72)


def bloco(rotulo: str, valor) -> None:
    print(f"  {rotulo:<34} {valor!r}")


def main() -> int:
    # Diretorio contido no workspace: o sandbox bloqueia o temp do sistema e o
    # app cria uploads/ no CWD no momento do import.
    temp = os.path.join(PROJETO, ".pytest-tmp", "qmly-run")
    shutil.rmtree(temp, ignore_errors=True)
    os.makedirs(temp, exist_ok=True)
    anterior = os.getcwd()
    os.chdir(temp)

    from app import app

    client = app.test_client()

    secao("A. Limite de tamanho de requisicao")
    limite = app.config.get("MAX_CONTENT_LENGTH")
    bloco("app.config[MAX_CONTENT_LENGTH]", limite)
    bloco("limite ausente?", limite is None)
    with app.app_context():
        bloco("Flask MAX_CONTENT_LENGTH efetivo", app.config.get("MAX_CONTENT_LENGTH"))

    secao("B. Nome do cliente na composicao de caminho")
    nomes = [
        "arvore.ged",
        "../fora.ged",
        "..\\fora.ged",
        "sub/dir.ged",
        "C:\\Windows\\Temp\\abs.ged",
        "....//....//fora.ged",
        "nome_com_espacos_e_acentos_ção.ged",
        "\x00nulo.ged",
    ]
    uploads = os.path.join(temp, "uploads")
    base = os.path.realpath(uploads)
    for nome in nomes:
        try:
            destino = os.path.join(uploads, nome)
            real = os.path.realpath(destino)
            rel = os.path.relpath(real, base)
            escapa = rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(nome)
            print(f"  {nome!r}")
            print(f"      destino   = {destino!r}")
            print(f"      real      = {real!r}")
            print(f"      escapa de uploads? = {escapa}")
        except Exception as erro:  # noqa: BLE001
            print(f"  {nome!r}")
            print(f"      ERRO ao compor: {type(erro).__name__}: {erro}")

    secao("B2. Escape provado por gravacao real (nome com separador de caminho)")
    alvo = os.path.join(temp, "ESCAPIU.ged")
    if os.path.exists(alvo):
        os.remove(alvo)
    resposta = client.post(
        "/",
        data={
            "action": "upload_gedcom",
            "gedcom": (io.BytesIO(GEDCOM_SIMPLE), "../ESCAPIU.ged"),
        },
        content_type="multipart/form-data",
    )
    bloco("status", resposta.status_code)
    bloco("gravou FORA de uploads/?", os.path.exists(alvo))
    bloco("caminho do arquivo fora", alvo if os.path.exists(alvo) else "(nao existe)")
    bloco("sobrou algo em uploads/", sorted(os.listdir(uploads)) if os.path.isdir(uploads) else "(sem pasta)")

    secao("C. Extensao e conteudo: o parse tenta mesmo assim?")
    casos = [
        ("conteudo_gedcom.txt", GEDCOM_SIMPLE),
        ("conteudo_gedcom.sem_extensao", GEDCOM_SIMPLE),
        ("lixo.bin", b"\x00\x01\x02isto nao e gedcom\xff\xfe"),
        ("vazio.ged", b""),
    ]
    for nome_arquivo, conteudo in casos:
        resposta = client.post(
            "/",
            data={
                "action": "upload_gedcom",
                "gedcom": (io.BytesIO(conteudo), nome_arquivo),
            },
            content_type="multipart/form-data",
        )
        texto = resposta.get_data(as_text=True)
        aceitou = 'carregado!' in texto.replace("&#39;", "'")
        erro = "Erro ao processar GEDCOM" in texto
        bloco(f"{nome_arquivo} (aceito?)", aceitou)
        bloco(f"{nome_arquivo} (erro de parse?)", erro)
        bloco(f"{nome_arquivo} (status)", resposta.status_code)
        bloco(f"{nome_arquivo} (gravado em disco?)", os.path.exists(os.path.join(uploads, nome_arquivo)))

    secao("D. Colisao: dois envios com o mesmo nome")
    nome = "colisao.ged"
    primeiro = b"0 HEAD\n1 SOUR PRIMEIRO\n0 TRLR\n"
    segundo = b"0 HEAD\n1 SOUR SEGUNDO\n0 TRLR\n"
    for rotulo, conteudo in (("primeiro", primeiro), ("segundo", segundo)):
        client.post(
            "/",
            data={"action": "upload_gedcom", "gedcom": (io.BytesIO(conteudo), nome)},
            content_type="multipart/form-data",
        )
        caminho = os.path.join(uploads, nome)
        with open(caminho, "rb") as arquivo:
            em_disco = arquivo.read()
        bloco(f"apos {rotulo} envio, disco", em_disco)
        bloco(f"apos {rotulo} envio, == enviado?", em_disco == conteudo)
    bloco("o primeiro sobreviveu?", os.path.exists(os.path.join(uploads, nome)) and b"PRIMEIRO" in open(os.path.join(uploads, nome), "rb").read())

    secao("E. Recuperacao pelo nome enviado no formulario")
    resposta = client.post(
        "/",
        data={"action": "path_search", "gedcom_filename": "colisao.ged",
              "person1_name": "X", "person2_name": "Y"},
        content_type="multipart/form-data",
    )
    texto = resposta.get_data(as_text=True)
    bloco("aceitou gedcom_filename do form?", "nao existe mais" not in texto)
    bloco("status", resposta.status_code)

    os.chdir(anterior)
    shutil.rmtree(temp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
