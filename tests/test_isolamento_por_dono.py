"""O portao da feature 051: dois donos, e a recusa indistinguivel de inexistencia.

Este arquivo e o teste negativo do `RISK-005`: A nao alcanca o que e de B, a
resposta e `404` (nunca `403`), e o texto e o de arquivo inexistente. Se este
arquivo ficar vermelho, a feature nao pode ser declarada entregue.
"""
from __future__ import annotations

import io
import os

from tests.fixtures.autenticacao import CONTA_A, CONTA_B, entrar_como

GEDCOM = (
    "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n1 NAME Maria /Souza/\n1 SEX F\n"
    "0 @I2@ INDI\n1 NAME Joao /Silva/\n1 SEX M\n"
    "0 @I3@ INDI\n1 NAME Ana /Silva/\n1 SEX F\n0 TRLR\n"
)


def _cliente_para(app_autenticado, conta):
    cliente = app_autenticado.app.test_client()
    entrar_como(cliente, app_autenticado.provedor, conta)
    return cliente


def _enviar(cliente, nome="arvore.ged", conteudo=None):
    return cliente.post(
        "/",
        data={
            "action": "upload_gedcom",
            "gedcom": (io.BytesIO((conteudo or GEDCOM).encode("utf-8")), nome),
        },
        content_type="multipart/form-data",
    )


def _arquivos_de(app_autenticado, conta):
    pasta = os.path.join(app_autenticado.pasta, conta.sub)
    return sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []


def test_a_lista_de_um_dono_nao_mostra_o_arquivo_do_outro(app_autenticado):
    cliente_a = _cliente_para(app_autenticado, CONTA_A)
    cliente_b = _cliente_para(app_autenticado, CONTA_B)
    _enviar(cliente_a)

    corpo_a = cliente_a.get("/").get_data(as_text=True)
    corpo_b = cliente_b.get("/").get_data(as_text=True)

    assert "arvore.ged" in corpo_a
    assert "arvore.ged" not in corpo_b, "a lista de B mostrou o arquivo de A (RN-03)"
    assert _arquivos_de(app_autenticado, CONTA_A) != []
    assert _arquivos_de(app_autenticado, CONTA_B) == []


def test_a_referencia_de_outro_dono_e_inexistente(app_autenticado):
    cliente_a = _cliente_para(app_autenticado, CONTA_A)
    cliente_b = _cliente_para(app_autenticado, CONTA_B)
    _enviar(cliente_a)
    referencia = _arquivos_de(app_autenticado, CONTA_A)[0]

    resposta = cliente_b.post(
        "/",
        data={
            "action": "path_search",
            "gedcom_filename": referencia,
            "person1_name": "Joao Silva",
            "person2_name": "Ana Silva",
        },
    )
    corpo = resposta.get_data(as_text=True)

    assert resposta.status_code == 404, (
        "a recusa por dono alheio tem de ser 404, e nao 403 nem 200 (RN-06, RISK-005)"
    )
    assert "não existe mais" in corpo
    assert "não foi possível" not in corpo.lower()
    assert "Conexão direta" not in corpo, "a arvore de A foi carregada por B"


def test_aposentar_referencia_de_outro_dono_nao_move_nada(app_autenticado):
    cliente_a = _cliente_para(app_autenticado, CONTA_A)
    cliente_b = _cliente_para(app_autenticado, CONTA_B)
    _enviar(cliente_a)
    referencia = _arquivos_de(app_autenticado, CONTA_A)[0]

    resposta = cliente_b.post(
        "/", data={"action": "aposentar_arquivo", "arquivo_a_aposentar": referencia}
    )

    assert resposta.status_code == 404
    assert referencia in _arquivos_de(app_autenticado, CONTA_A), (
        "B aposentou o arquivo de A: a referencia de outro dono moveu dado"
    )


def test_o_mesmo_conteudo_em_dois_donos_sao_dois_arquivos(app_autenticado):
    cliente_a = _cliente_para(app_autenticado, CONTA_A)
    cliente_b = _cliente_para(app_autenticado, CONTA_B)

    _enviar(cliente_a)
    _enviar(cliente_b)

    arquivos_a = _arquivos_de(app_autenticado, CONTA_A)
    arquivos_b = _arquivos_de(app_autenticado, CONTA_B)
    assert arquivos_a == arquivos_b and len(arquivos_a) == 1, (
        "o mesmo conteudo por dois donos tem de gerar um arquivo em CADA pasta"
    )

    cliente_a.post(
        "/", data={"action": "aposentar_arquivo", "arquivo_a_aposentar": arquivos_a[0]}
    )

    assert arquivos_a[0] not in _arquivos_de(app_autenticado, CONTA_A)
    assert _arquivos_de(app_autenticado, CONTA_B) == arquivos_b, (
        "aposentar o arquivo de A afetou o de B (RN-05)"
    )


def test_a_arvore_do_proprio_dono_continua_acessivel(app_autenticado):
    cliente_a = _cliente_para(app_autenticado, CONTA_A)
    _enviar(cliente_a)
    referencia = _arquivos_de(app_autenticado, CONTA_A)[0]

    resposta = cliente_a.post(
        "/",
        data={
            "action": "path_search",
            "gedcom_filename": referencia,
            "person1_name": "Joao Silva",
            "person2_name": "Ana Silva",
        },
    )

    assert resposta.status_code == 200
    assert "Conexão" in resposta.get_data(as_text=True)
