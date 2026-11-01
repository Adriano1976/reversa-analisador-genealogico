"""Onde ficam os dados do usuario (auditoria de 2026-10-30, `P4`).

Ate aqui, uploads, logs e contas moravam DENTRO da pasta do programa. O instalador vai
gravar em `C:\\Program Files`, que nao e gravavel por usuario comum, e o `os.makedirs` do
import derrubava o processo com `PermissionError` e traceback. Estes testes prendem as tres
coisas que a correcao promete: a raiz padrao (uma so), as sobreposicoes e o aviso de dados
antigos.

Leem o `ambiente` de parametro, e nao o do processo: medir a resolucao sem mexer no
ambiente e o mesmo desenho de `tests/test_modo_de_identidade.py` para `web/modo.py`.
"""
from __future__ import annotations

import os

import pytest

import app
from utils import pastas

LOCALAPPDATA = r"C:\Users\ana\AppData\Local"


def _raiz(local: str = LOCALAPPDATA) -> str:
    return os.path.join(local, pastas.NOME_DA_PASTA)


# --- A raiz -----------------------------------------------------------------


def test_no_windows_a_raiz_fica_no_localappdata():
    assert pastas.raiz_de_dados({"LOCALAPPDATA": LOCALAPPDATA}) == _raiz()


def test_fora_do_windows_usa_o_padrao_xdg():
    assert pastas.raiz_de_dados({"XDG_DATA_HOME": "/home/ana/.local/share"}) == os.path.join(
        "/home/ana/.local/share", pastas.NOME_DA_PASTA
    )


def test_sem_xdg_cai_no_diretorio_do_usuario():
    assert pastas.raiz_de_dados({}) == os.path.join(
        os.path.expanduser("~"), ".local", "share", pastas.NOME_DA_PASTA
    )


def test_as_tres_pastas_pendem_da_raiz():
    ambiente = {"LOCALAPPDATA": LOCALAPPDATA}

    assert pastas.pasta_de_uploads(ambiente) == os.path.join(_raiz(), "uploads")
    assert pastas.pasta_de_logs(ambiente) == os.path.join(_raiz(), "logs")
    assert pastas.arquivo_de_contas(ambiente) == os.path.join(_raiz(), "contas.json")


# --- As sobreposicoes -------------------------------------------------------


def test_analisador_dados_sobrepoe_o_padrao_da_plataforma():
    ambiente = {"LOCALAPPDATA": LOCALAPPDATA, "ANALISADOR_DADOS": r"D:\dados"}

    assert pastas.raiz_de_dados(ambiente) == r"D:\dados"
    assert pastas.pasta_de_uploads(ambiente) == os.path.join(r"D:\dados", "uploads")


def test_as_tres_sobreposicoes_vencem_a_raiz():
    ambiente = {
        "LOCALAPPDATA": LOCALAPPDATA,
        "ANALISADOR_UPLOAD_FOLDER": r"D:\u",
        "ANALISADOR_LOG_DIR": r"D:\l",
        "ANALISADOR_CONTAS": r"D:\c.json",
    }

    assert pastas.pasta_de_uploads(ambiente) == r"D:\u"
    assert pastas.pasta_de_logs(ambiente) == r"D:\l"
    assert pastas.arquivo_de_contas(ambiente) == r"D:\c.json"


# --- A recusa ---------------------------------------------------------------


def test_pasta_inacessivel_vira_erro_de_contrato(tmp_path):
    no_lugar_da_pasta = tmp_path / "nao-e-pasta"
    no_lugar_da_pasta.write_text("x", encoding="utf-8")

    with pytest.raises(pastas.PastaDeDadosInacessivel) as erro:
        pastas.preparar(str(no_lugar_da_pasta))

    assert "ANALISADOR_DADOS" in str(erro.value), (
        "a mensagem tem de nomear a variavel que resolve o problema"
    )


def test_pasta_de_upload_inutilizavel_recusa_a_subida(tmp_path, monkeypatch):
    """`P4`: sem escrita, a recusa tem nome - nunca `PermissionError` com traceback."""
    no_lugar_da_pasta = tmp_path / "nao-e-pasta"
    no_lugar_da_pasta.write_text("x", encoding="utf-8")
    monkeypatch.setenv("ANALISADOR_UPLOAD_FOLDER", str(no_lugar_da_pasta))

    with pytest.raises(app.RecusaDeSubida):
        app.create_app()


# --- O aviso de dados da versao anterior ------------------------------------


def _programa_com_uploads(tmp_path):
    """Uma pasta de programa falsa com um arquivo no lugar em que a versao antiga gravava."""
    programa = tmp_path / "programa"
    (programa / "uploads" / "unico").mkdir(parents=True)
    (programa / "uploads" / "unico" / "arvore.ged").write_text("0 HEAD", encoding="utf-8")
    return programa


def test_avisa_quando_sobraram_uploads_da_versao_anterior(tmp_path):
    programa = _programa_com_uploads(tmp_path)

    uploads, contas = pastas.restos_da_versao_antiga(
        {"LOCALAPPDATA": str(tmp_path / "local")}, pasta_do_app=str(programa)
    )

    assert uploads == os.path.join(str(programa), "uploads")
    assert contas is None


def test_avisa_quando_sobraram_contas_da_versao_anterior(tmp_path):
    programa = tmp_path / "programa"
    (programa / "dados").mkdir(parents=True)
    (programa / "dados" / "contas.json").write_text("{}", encoding="utf-8")

    uploads, contas = pastas.restos_da_versao_antiga(
        {"LOCALAPPDATA": str(tmp_path / "local")}, pasta_do_app=str(programa)
    )

    assert uploads is None
    assert contas == os.path.join(str(programa), "dados", "contas.json")


def test_nao_avisa_quando_o_destino_ja_tem_arquivo(tmp_path):
    programa = _programa_com_uploads(tmp_path)
    destino = tmp_path / "local" / pastas.NOME_DA_PASTA / "uploads"
    destino.mkdir(parents=True)
    (destino / "ja.ged").write_text("0 HEAD", encoding="utf-8")

    assert pastas.restos_da_versao_antiga(
        {"LOCALAPPDATA": str(tmp_path / "local")}, pasta_do_app=str(programa)
    ) == (None, None)


def test_nao_avisa_quando_o_operador_declarou_os_caminhos(tmp_path):
    """Com caminho declarado, a pasta do programa e historia - avisar ali seria ruido."""
    programa = _programa_com_uploads(tmp_path)

    assert pastas.restos_da_versao_antiga(
        {
            "LOCALAPPDATA": str(tmp_path / "local"),
            "ANALISADOR_UPLOAD_FOLDER": str(tmp_path / "uploads"),
        },
        pasta_do_app=str(programa),
    ) == (None, None)
