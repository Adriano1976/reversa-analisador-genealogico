"""Caracterizacao da fabrica de aplicacao (OPP-20261023-FACT).

O app de modulo continua sendo `app`. A fabrica existe para montar uma instancia
nova com configuracao propria, sem tocar no singleton importado pela suite.
"""
from __future__ import annotations

import os
import sys

from flask import Flask
from werkzeug.exceptions import RequestEntityTooLarge, SecurityError

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_APP = os.path.join(RAIZ, "src")
if PASTA_APP not in sys.path:
    sys.path.insert(0, PASTA_APP)

import app as modulo  # noqa: E402

ROTAS = {
    "/": {"GET", "POST"},
    "/app.css": {"GET"},
    "/banner.png": {"GET"},
    "/apple-touch-icon.png": {"GET"},
    "/favicon.png": {"GET"},
    "/descartes.csv": {"POST"},
}

CHAVES = (
    "MAX_CONTENT_LENGTH",
    "TRUSTED_HOSTS",
    "ARTE_DO_ICONE",
    "ARTE_DO_FAVICON",
    "ARTE_DO_TOPO",
    "ESTILO_DA_TELA",
)


def _rotas(aplicacao: Flask) -> dict[str, set[str]]:
    return {
        regra.rule: set(regra.methods or ()) - {"HEAD", "OPTIONS"}
        for regra in aplicacao.url_map.iter_rules()
        if regra.rule in ROTAS
    }


def test_create_app_devolve_instancia_nova():
    nova = modulo.create_app()
    assert isinstance(nova, Flask)
    assert nova is not modulo.app


def test_create_app_registra_as_cinco_rotas():
    assert _rotas(modulo.create_app()) == ROTAS


def test_create_app_copia_a_configuracao_padrao():
    nova = modulo.create_app()
    for chave in CHAVES:
        assert nova.config[chave] == modulo.app.config[chave]


def test_create_app_honra_a_sobreposicao():
    nova = modulo.create_app({"TESTING": True, "MAX_CONTENT_LENGTH": 123})
    assert nova.config["TESTING"] is True
    assert nova.config["MAX_CONTENT_LENGTH"] == 123


def test_criar_instancia_nao_altera_o_app_de_modulo():
    rotas_antes = sorted(regra.rule for regra in modulo.app.url_map.iter_rules())
    config_antes = {chave: modulo.app.config[chave] for chave in CHAVES}
    modulo.create_app({"TESTING": True, "MAX_CONTENT_LENGTH": 123})
    assert sorted(regra.rule for regra in modulo.app.url_map.iter_rules()) == rotas_antes
    assert {chave: modulo.app.config[chave] for chave in CHAVES} == config_antes


def test_create_app_registra_ganchos_e_tratadores():
    nova = modulo.create_app()
    tratadores = nova.error_handler_spec[None]
    assert tratadores[413][RequestEntityTooLarge] is modulo._requisicao_grande
    assert tratadores[400][SecurityError] is modulo._host_recusado
    assert nova.after_request_funcs[None]
    assert nova.template_context_processors[None]
