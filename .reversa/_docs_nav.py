"""Navegacao do mini-site, derivada de pagesGenerated. Fonte unica para o
data.js (window.RV_DATA.nav) e para a injecao estatica dos <a> no <nav>.
"""

NAV = [
    {"id": "index", "href": "index.html", "label": "Visão geral"},
    {"id": "arquitetura", "href": "arquitetura.html", "label": "Arquitetura 3D"},
    {"id": "modulos", "href": "modulos.html", "label": "Módulos"},
    {"id": "metricas", "href": "metricas.html", "label": "Métricas"},
    {"id": "timeline", "href": "timeline.html", "label": "Timeline"},
    {"id": "glossario", "href": "glossario.html", "label": "Glossário"},
    {"id": "deck", "href": "deck.html", "label": "Deck"},
    {"id": "upload-gedcom", "href": "features/upload-gedcom.html", "label": "Upload de GEDCOM"},
    {"id": "busca-caminho", "href": "features/busca-caminho.html", "label": "Busca de caminho"},
    {"id": "analise-dna", "href": "features/analise-dna.html", "label": "Análise de DNA"},
]


def nav_para(paginas):
    """Filtra a navegacao pelo que realmente existe em pagesGenerated."""
    return [n for n in NAV if n["href"] in paginas]


def html_links(itens, prefixo="", indent="  "):
    """prefixo e o caminho relativo ate a raiz do mini-site ("" na raiz,
    "../" em features/), o mesmo que o nav.js usa via data-base-path."""
    linhas = []
    for it in itens:
        linhas.append('%s<a href="%s%s" data-page-id="%s">%s</a>'
                      % (indent, prefixo, it["href"], it["id"], it["label"]))
    return "\n".join(linhas)
