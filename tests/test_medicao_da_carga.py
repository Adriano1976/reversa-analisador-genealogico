"""Testes da medicao nomeada (`T012` da feature 049).

A medicao existe para responder uma pergunta de decisao: o cache da arvore (features 025 e
047) compensa? Para isso a linha precisa **nomear a etapa** e trazer milissegundos — um
numero solto no log nao diz o que foi medido.
"""
import io
import os
import re

from utils import logs


def _linhas_do_geral() -> list[str]:
    caminho = os.path.join(logs.pasta_de_logs(), logs.ARQUIVO_GERAL)
    if not os.path.isfile(caminho):
        return []
    with open(caminho, encoding="utf-8") as arquivo:
        return arquivo.read().splitlines()


GEDCOM = (
    "0 HEAD\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "0 @I1@ INDI\n"
    "1 NAME Clara /Melo/\n"
    "1 SEX F\n"
    "0 TRLR\n"
)


def test_a_carga_da_arvore_e_medida_em_milissegundos(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    cliente.post(
        "/",
        data={"action": "upload_gedcom", "gedcom": (io.BytesIO(GEDCOM.encode()), "arvore.ged")},
        content_type="multipart/form-data",
    )

    linhas = [linha for linha in _linhas_do_geral() if "carregar_arvore:" in linha]
    assert linhas, "a carga da arvore nao foi medida"
    assert re.search(r"carregar_arvore: \d+(?:\.\d+)? ms", linhas[-1]), linhas[-1]


def test_a_medicao_nao_carrega_dado_pessoal(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    cliente.post(
        "/",
        data={"action": "upload_gedcom", "gedcom": (io.BytesIO(GEDCOM.encode()), "arvore.ged")},
        content_type="multipart/form-data",
    )

    linha = [linha for linha in _linhas_do_geral() if "carregar_arvore:" in linha][-1]
    assert "Clara" not in linha and "Melo" not in linha
