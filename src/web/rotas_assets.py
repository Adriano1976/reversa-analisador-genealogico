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


# --- Os recursos embutidos (feature 054) ---
# A tela buscava o Bootstrap e o Mermaid em `cdn.jsdelivr.net`; sem rede, saia sem estilo, as
# abas nao alternavam e o diagrama nao desenhava. Os tres arquivos e as fontes passaram a ser
# servidos daqui, no mesmo regime da folha: rota explicita, `mimetype` declarado e `404` para
# arquivo ausente. Nada de diretorio estatico — `src/static/` continua proibida pelo `W004`.

#: Os 11 subconjuntos de fonte que a folha `fontes.css` referencia. O nome chega pelo
#: caminho da URL, entao a validacao e um CONJUNTO FECHADO: um nome fora daqui responde
#: `404`, e nao vira leitura de caminho arbitrario. A receita (`tests/fontes_da_tela.py`)
#: e a autoridade sobre a lista; ha teste comparando as duas.
FONTES_DA_TELA: frozenset[str] = frozenset({
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYp3tKgS4.woff2",
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYpHtKgS4.woff2",
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYpntKgS4.woff2",
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYqXtK.woff2",
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYrXtKgS4.woff2",
    "xn7gYHE41ni1AdIRggOxSuXd.woff2",
    "xn7gYHE41ni1AdIRggSxSuXd.woff2",
    "xn7gYHE41ni1AdIRggexSg.woff2",
    "xn7gYHE41ni1AdIRggixSuXd.woff2",
    "xn7gYHE41ni1AdIRggmxSuXd.woff2",
    "xn7gYHE41ni1AdIRggqxSuXd.woff2",
})


def _servir_recurso(chave: str, mimetype: str):
    """Entrega o arquivo configurado em `chave`, ou `404` se ele nao existir.

    O mimetype e sempre explicito: sem ele, `send_file` depende da tabela do sistema e um
    `.js` pode sair como `application/octet-stream`, que o navegador recusa executar.
    """
    caminho = current_app.config.get(chave)
    if not caminho or not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype=mimetype)


@assets_bp.route("/bootstrap.css", methods=["GET"])
def biblioteca_css():
    """Serve a folha do Bootstrap 5.3.3, embutida (feature 054)."""
    return _servir_recurso("BIBLIOTECA_CSS", "text/css")


@assets_bp.route("/bootstrap.js", methods=["GET"])
def biblioteca_js():
    """Serve o pacote consolidado do Bootstrap 5.3.3, que ja traz o Popper."""
    return _servir_recurso("BIBLIOTECA_JS", "text/javascript")


@assets_bp.route("/mermaid.js", methods=["GET"])
def mermaid():
    """Serve o Mermaid 10.9.8, que desenha o diagrama no cliente."""
    return _servir_recurso("MERMAID", "text/javascript")


@assets_bp.route("/fontes.css", methods=["GET"])
def folha_de_fontes():
    """Serve a folha derivada das duas familias de fonte (feature 054)."""
    return _servir_recurso("FOLHA_DE_FONTES", "text/css")


@assets_bp.route("/fontes/<arquivo>.woff2", methods=["GET"])
def fonte(arquivo: str):
    """Serve um subconjunto `woff2` do conjunto fechado.

    Nome fora do conjunto, arquivo ausente ou tentativa de sair da pasta respondem todos o
    MESMO `404` vazio: distinguir os casos diria ao cliente o que existe no disco.
    """
    nome = f"{arquivo}.woff2"
    pasta = current_app.config.get("PASTA_DE_FONTES")
    if nome not in FONTES_DA_TELA or not pasta:
        return "", 404
    caminho = os.path.join(pasta, nome)
    if not os.path.isfile(caminho):
        return "", 404
    return send_file(caminho, mimetype="font/woff2")


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
    "FONTES_DA_TELA",
    "assets_bp",
    "banner_do_topo",
    "biblioteca_css",
    "biblioteca_js",
    "descartes_em_csv",
    "estilo_da_tela",
    "favicon_da_aba",
    "folha_de_fontes",
    "fonte",
    "icone_de_atalho",
    "mermaid",
]
