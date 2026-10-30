"""Rotas de entrega de assets estáticos, arte visual e exportações.

Este módulo encapsula as rotas HTTP de entrega de recursos visuais da tela
e download de arquivos gerados, aliviando o módulo principal da aplicação (OPP-20261023-ASST).
"""
from __future__ import annotations

import json
import os

from flask import Blueprint, Response, current_app, request, send_file
from reporting.csv_de_descartes import csv_de_descartes

assets_bp = Blueprint("assets", __name__)


@assets_bp.route("/apple-touch-icon.png", methods=["GET"])
def icone_de_atalho():
    """Serve o icone de atalho (RF-01).

    Registrada so com GET: a recusa de escrita sai do roteador com 405.
    O ETag que o proprio send_file emite responde 304 sem corpo na rebusca.
    Arte ausente devolve 404 e nada mais muda.
    """
    caminho = current_app.config.get("ARTE_DO_ICONE")
    if not caminho or not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="image/png")


@assets_bp.route("/favicon.png", methods=["GET"])
def favicon_da_aba():
    """Serve o favicon transparente das telas de identidade (emenda E005).

    E a MESMA arte do `/apple-touch-icon.png`, derivada da mesma canonica, mas
    **sem o fundo branco**: na aba do navegador o fundo do icone aparece, e a arte
    opaca deixaria um quadrado branco em volta do desenho. O icone de atalho
    continua opaco, porque o sistema movel compoe transparencia sobre preto.
    """
    caminho = current_app.config.get("ARTE_DO_FAVICON")
    if not caminho or not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="image/png")


@assets_bp.route("/banner.png", methods=["GET"])
def banner_do_topo():
    """Serve a arte do topo da tela.

    Registrada so com GET, sem validade longa de cache: o ETag da a revalidacao
    barata sem prender o cliente. Arte ausente devolve 404 e nada mais muda.
    """
    caminho = current_app.config.get("ARTE_DO_TOPO")
    if not caminho or not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="image/png")


@assets_bp.route("/app.css", methods=["GET"])
def estilo_da_tela():
    """Serve a folha de estilo da tela.

    O mimetype e declarado explicitamente como text/css.
    Arquivo ausente devolve 404 e nada mais muda.
    """
    caminho = current_app.config.get("ESTILO_DA_TELA")
    if not caminho or not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="text/css")


@assets_bp.route("/descartes.csv", methods=["POST"])
def descartes_em_csv():
    """Baixa a lista de trabalho dos descartes (feature 035).

    O corpo vem do proprio HTML da analise via campo oculto dados.
    O formatador da camada reporting desarma formula de planilha e escapa o CSV.
    """
    try:
        itens = json.loads(request.form.get("dados") or "[]")
    except (TypeError, ValueError):
        itens = []
    if not isinstance(itens, list):
        itens = []
    return Response(
        csv_de_descartes(itens),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=descartes.csv"},
    )


__all__ = [
    "assets_bp",
    "banner_do_topo",
    "descartes_em_csv",
    "estilo_da_tela",
    "favicon_da_aba",
    "icone_de_atalho",
]
