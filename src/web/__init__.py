"""Borda HTTP: Blueprints e entrega de recursos da tela.

Este e o unico pacote, alem de `app.py`, que conhece Flask. Ele existe para que
`reporting/` continue livre de framework: as rotas de assets, arte e download
moram aqui, enquanto `application/`, `ports/`, `core/`, `parsers/` e `utils/`
seguem sem dependencia de Flask.

`web/` nao guarda regra de negocio, nao importa `core/` e nao decide layout: ele
transporta bytes e formularios. A montagem continua em `app.py`, que registra o
Blueprint.
"""
