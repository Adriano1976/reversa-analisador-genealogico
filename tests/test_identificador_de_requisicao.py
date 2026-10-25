"""Testes do identificador de requisicao (`T009` da feature 049).

O identificador so vale se **ligar** duas linhas: a de acesso e a de erro da mesma
requisicao (`RN-03`, `RF-03`, `RF-04`). Estes testes cobrem as quatro propriedades que
fazem essa ligacao funcionar — presenca, formato, unicidade e nao aceitacao do valor do
cliente — mais a correlacao com a linha de acesso gravada no arquivo.
"""
import os
import re

from utils import logs

FORMATO = re.compile(r"^[0-9a-f]{8}$")


def _linhas_do_acesso() -> list[str]:
    caminho = os.path.join(logs.pasta_de_logs(), logs.ARQUIVO_GERAL)
    if not os.path.isfile(caminho):
        return []
    with open(caminho, encoding="utf-8") as arquivo:
        return [linha for linha in arquivo.read().splitlines() if "acesso: " in linha]


def test_toda_resposta_traz_o_cabecalho(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    resposta = cliente.get("/")
    assert FORMATO.match(resposta.headers["X-Request-ID"]), resposta.headers


def test_duas_requisicoes_tem_identificadores_diferentes(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    primeiro = cliente.get("/").headers["X-Request-ID"]
    segundo = cliente.get("/").headers["X-Request-ID"]
    assert primeiro != segundo


def test_o_valor_enviado_pelo_cliente_e_ignorado(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    resposta = cliente.get("/", headers={"X-Request-ID": "forjado123"})
    assert resposta.headers["X-Request-ID"] != "forjado123", (
        "o identificador do cliente foi aceito: texto de cliente entraria no arquivo de log"
    )
    assert FORMATO.match(resposta.headers["X-Request-ID"])


def test_a_linha_de_acesso_traz_o_identificador_da_requisicao(cliente_de_upload):
    """A correlacao que o operador usa: copiar o cabecalho e achar a linha."""
    _, cliente, _ = cliente_de_upload
    resposta = cliente.get("/")
    identificador = resposta.headers["X-Request-ID"]
    linhas = [linha for linha in _linhas_do_acesso() if f"[{identificador}]" in linha]
    assert linhas, (
        f"nenhuma linha de acesso carrega o identificador {identificador}: "
        "o cabecalho e o arquivo nao se falam"
    )


def test_a_linha_de_acesso_nomeia_metodo_rota_situacao_e_duracao(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    cliente.get("/")
    linha = _linhas_do_acesso()[-1]
    assert "acesso: GET /" in linha
    assert "-> 200" in linha
    assert re.search(r"\(\d+(?:\.\d+)? ms\)", linha), linha


def test_o_identificador_e_novo_a_cada_requisicao_e_nao_reaproveitado():
    """Fora de requisicao o valor e `-`; dentro, cada chamada de `novo_identificador` muda."""
    assert logs.identificador_atual() == "-"
    primeiro = logs.novo_identificador()
    assert logs.identificador_atual() == primeiro
    assert logs.novo_identificador() != primeiro
    assert FORMATO.match(primeiro)
