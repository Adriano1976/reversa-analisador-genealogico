---
schema_version: 1
id: OPP-20261023-ASST
display_number: 40
context: tela-de-entrada
verb: modularize
title: Extração de rotas de assets estáticos e arte para Blueprint ou módulo dedicado
target:
  files: [src/app.py]
  symbol: icone_de_atalho, banner_do_topo, estilo_da_tela, descartes_em_csv
smell: >
  O arquivo app.py mistura a rota principal da aplicacao e a orquestracao dos casos
  de uso com rotas de servico de arquivos estaticos (/apple-touch-icon.png, /banner.png,
  /app.css) e exportacao de download (/descartes.csv).
roi:
  confidence: green
  impact: >
    Separa a responsabilidade de entrega de assets estaticos e downloads da logica central
    da interface de genealogia. Aplica o padrao Blueprint do Flask para alta coesao.
  cost: low
  est_return: >
    Reducao de ~180 linhas em app.py. Mapeamento de assets isolado e reutilizavel.
state: applied
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/recursos-da-tela/requirements.md
    - _reversa_sdd/adrs/29-arte-derivada-com-receita-unica.md
---

## Antes observado

Em `src/app.py`, as linhas 359-497 e 518-541 declaram quatro rotas especializadas de entrega de arquivo:

1. `/apple-touch-icon.png`: icone derivado
2. `/banner.png`: banner derivado do topo
3. `/app.css`: folha de estilos servida com Content-Type text/css
4. `/descartes.csv`: exportacao de download de descartes

Essas rotas sao independentes do fluxo da arvore genealogica e do GEDCOM, porem poluem o modulo principal.

## Transformação proposta

Criar um Blueprint `assets_bp` (ou modulo `src/reporting/assets_routes.py` ou `src/rotas_assets.py`),
registrando-o no aplicativo principal com `app.register_blueprint(assets_bp)`.

Aplicado em `src/web/rotas_assets.py`. O modulo nasceu em `src/rotas_assets.py`,
passou por `src/reporting/rotas_assets.py` e terminou no pacote `web/`, criado para
manter `reporting/` livre de Flask. Ver
`transformations/OPP-20261023-ASST-extracao-de-rotas-de-assets-em-blueprint/transformation.md`.

## Rede de segurança

Coberto por `tests/test_icone_de_atalho.py`, `tests/test_banner_do_topo.py`,
`tests/test_deriva_da_arte.py`, `tests/test_estilo_da_tela.py` e `tests/test_csv_de_descartes.py`.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*
