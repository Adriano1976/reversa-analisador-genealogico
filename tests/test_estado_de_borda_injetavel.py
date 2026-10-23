"""Caracterizacao do estado de borda injetavel (OPP-20261023-ESTD).

O app de modulo continua com os quatro objetos padrao. Uma instancia criada por
`create_app` pode receber outros e passa a usa-los nas requisicoes.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_APP = os.path.join(RAIZ, "src")
if PASTA_APP not in sys.path:
    sys.path.insert(0, PASTA_APP)

import app as modulo  # noqa: E402


class ArmazenamentoDeMentira:
    def __init__(self):
        self.chamadas = []

    def listar(self, dono):
        self.chamadas.append(("listar", dono))
        return []

    def resolver(self, referencia, dono):
        self.chamadas.append(("resolver", referencia))
        return None

    def aposentar(self, referencia, dono):
        self.chamadas.append(("aposentar", referencia))
        return False


class CarregadorDeMentira:
    def carregar(self, referencia, dono):
        raise AssertionError("o carregador falso nao deveria ser usado aqui")


def test_create_app_guarda_as_dependencias_injetadas():
    armazenamento = ArmazenamentoDeMentira()
    carregador = CarregadorDeMentira()
    dependencias = object()
    nova = modulo.create_app(
        armazenamento=armazenamento,
        carregador=carregador,
        registro=None,
        dependencias=dependencias,
    )
    borda = nova.extensions[modulo.CHAVE_DA_BORDA]
    assert borda["armazenamento"] is armazenamento
    assert borda["carregador"] is carregador
    assert borda["registro"] is None
    assert borda["dependencias"] is dependencias


def test_requisicao_usa_o_armazenamento_injetado():
    primeiro = ArmazenamentoDeMentira()
    segundo = ArmazenamentoDeMentira()
    app_um = modulo.create_app(armazenamento=primeiro)
    app_dois = modulo.create_app(armazenamento=segundo)

    assert app_um.test_client().get("/").status_code == 200
    assert app_dois.test_client().get("/").status_code == 200

    assert [chamada[0] for chamada in primeiro.chamadas] == ["listar"]
    assert [chamada[0] for chamada in segundo.chamadas] == ["listar"]


def test_registro_none_e_distinto_de_nao_injetado():
    com_none = modulo.create_app(registro=None)
    sem_injecao = modulo.create_app()
    assert com_none.extensions[modulo.CHAVE_DA_BORDA]["registro"] is None
    assert (
        sem_injecao.extensions[modulo.CHAVE_DA_BORDA]["registro"]
        is modulo._REGISTRO
    )


def test_app_de_modulo_usa_os_objetos_padrao():
    borda = modulo.app.extensions[modulo.CHAVE_DA_BORDA]
    assert borda["armazenamento"] is modulo._ARMAZENAMENTO
    assert borda["carregador"] is modulo._CARREGADOR
    assert borda["registro"] is modulo._REGISTRO
    assert borda["dependencias"] is modulo._DEPENDENCIAS
