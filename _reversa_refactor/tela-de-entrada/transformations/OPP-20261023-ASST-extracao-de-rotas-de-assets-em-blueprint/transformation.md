---
schema_version: 1
id: OPP-20261023-ASST
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
    - before-after/suite-pos-realocacao.txt
    - before-after/suite-pos-web.txt
measurement:
  before: "src/app.py com 888 linhas, incluindo quatro rotas de assets e download e cerca de 180 linhas de comentario de infraestrutura"
  after: "src/app.py com 737 linhas mais src/web/rotas_assets.py com 83 linhas e src/web/__init__.py; as quatro rotas em Blueprint `assets_bp`"
change_set:
  - chg: CHG-001
    file: src/app.py
    purpose: remove as quatro rotas, registra o Blueprint, remove os shims temporarios e o `import json` sem uso
  - chg: CHG-002
    file: src/rotas_assets.py
    purpose: novo modulo com o Blueprint, as tres rotas de arte e a rota de download CSV
  - chg: CHG-003
    file: src/templates/index.html
    purpose: aponta `url_for` do formulario de descartes para o endpoint do Blueprint
  - chg: CHG-004
    file: src/reporting/rotas_assets.py
    purpose: primeira realocacao, historica, de `src/` para `src/reporting/`; substituida pela CHG-005
  - chg: CHG-005
    file: src/web/rotas_assets.py
    purpose: cria o pacote `web/` e move o modulo para la, mantendo `reporting/` livre de Flask
approval:
  by: user
  at: 2026-10-23T03:08:01-03:00
reversible_via:
  - CHG-001-rotas-removidas-de-app.diff
  - CHG-002-modulo-rotas-assets.diff
  - CHG-003-template-url-for.diff
  - CHG-004-realocacao-para-reporting.diff
  - CHG-005-realocacao-para-web.diff
---

# Transformacao: OPP-20261023-ASST (rotas de assets e downloads)

## O que mudou

As quatro rotas que nao pertencem ao fluxo da tela de entrada sairam de
`src/app.py` para `src/web/rotas_assets.py`, num Blueprint registrado no import:

| Rota | Metodo | Antes | Depois |
|---|---|---|---|
| `/apple-touch-icon.png` | GET | `app.py` | `web/rotas_assets.py` |
| `/banner.png` | GET | `app.py` | `web/rotas_assets.py` |
| `/app.css` | GET | `app.py` | `web/rotas_assets.py` |
| `/descartes.csv` | POST | `app.py` | `web/rotas_assets.py` |

As rotas usam `current_app.config` em vez de `app.config`, que e o que permite o
Blueprint nao importar o modulo da aplicacao. Os caminhos das tres artes
continuam sendo configurados em `app.py`, porque `app.config` e o ponto que os
testes usam para simular arte ausente
(`monkeypatch.setitem(app.config, "ARTE_DO_ICONE", ...)`). A folha de estilo, o
banner e o icone foram verificados por `tests/test_estilo_da_tela.py`,
`tests/test_banner_do_topo.py`, `tests/test_icone_de_atalho.py` e
`tests/test_deriva_da_arte.py`; o CSV por `tests/test_csv_de_descartes.py`.

## Ajuste de fechamento feito nesta sessao

A extracao tinha sido aplicada pela sessao interrompida com tres residuos que
anulavam parte do ganho:

1. Quatro regras `app.add_url_rule(..., build_only=True)` para recriar os nomes
   de endpoint antigos. Elas apareciam no `url_map` como rotas concorrentes do
   mesmo caminho e nunca casavam, servindo so para `url_for`. Nenhum teste ou
   template usava tres delas.
2. Quatro re-exportacoes sem efeito (`icone_de_atalho = icone_de_atalho` e
   equivalentes), que nao exportavam nada: os nomes ja vinham do `import`.
3. `import json` em `app.py`, que ficou sem uso quando `descartes_em_csv` mudou
   de modulo.

O unico consumidor real do nome antigo era `src/templates/index.html:1796`
(`url_for('descartes_em_csv')`). O template passou a usar
`url_for('assets.descartes_em_csv')`, que resolve para o **mesmo** `/descartes.csv`:
o HTML de `GET /` nao muda um byte, e o hash `SHA_DA_TELA` de
`tests/test_icone_de_atalho.py` continua valido. Com isso, os shims e as
re-exportacoes foram removidos e o `url_map` ficou com seis regras, sem
duplicata.

## Realocacao para `src/web/` (2026-10-23)

O modulo nasceu em `src/rotas_assets.py`, na raiz do pacote, ao lado de `app.py`.
A pedido do usuario, saiu da raiz para uma subpasta de `src/`, em duas etapas:

1. `CHG-004`: de `src/rotas_assets.py` para `src/reporting/rotas_assets.py`.
2. `CHG-005`: de `src/reporting/rotas_assets.py` para `src/web/rotas_assets.py`,
   com o novo pacote `src/web/__init__.py`.

A segunda etapa desfaz a primeira a pedido do usuario: `reporting/` deve continuar
livre de framework. Ele e a camada de apresentacao (transformacao de resultado em
apresentacao) e nao deve conhecer Flask. A escolha por `reporting/` na primeira
etapa era pragmatica, e a propria ASST a citava como alternativa, mas o custo
declarado (importar Flask) foi recusado.

O pacote `web/` passa a ser a borda HTTP: e o unico lugar, alem de `app.py`, que
conhece o framework. Nenhuma outra camada importa Flask, e `reporting/` voltou a
ser livre dele.

| Pacote | Importa Flask |
|---|---|
| `app.py` | sim, sempre foi |
| `web/` | sim, desde 2026-10-23 |
| `reporting/` | nao |
| `application/`, `ports/`, `core/`, `parsers/`, `utils/` | nao |

O `__init__.py` de `web/` declara a responsabilidade do pacote. O de `reporting/`
nao foi tocado, porque nao reexporta nada, e o `Blueprint` e consumido por
`app.py` pelo caminho completo.

## Reversibilidade

Os tres primeiros diffs foram reconstruidos a partir do `HEAD 221b6c1` e
verificados em cadeia com DEAD e DISP. O `CHG-004` foi gerado sobre o estado
seguinte a eles, e o `CHG-005` sobre o estado do `CHG-004`. A aplicacao na ordem
`CHG-001` a `CHG-005` produz o estado atual; a reversao na ordem inversa devolve o
modulo a `src/rotas_assets.py`. As duas realocacoes ficam no registro porque
aconteceram: a `CHG-004` e historica e a `CHG-005` e o destino final.

## Rede de seguranca

| Momento | Resultado |
|---|---|
| linha de base HEAD 221b6c1 | 1615 passed, 9 skipped |
| working tree depois do lote e da limpeza | 1615 passed, 9 skipped |
| working tree depois da realocacao para `reporting/` | 1615 passed, 9 skipped |
| working tree depois da realocacao para `web/` | 1615 passed, 9 skipped |

Medicao do lote combinado; ver a nota de escopo em
[suite-antes.txt](before-after/suite-antes.txt). Durante a limpeza, os quatro
arquivos de teste das rotas e o de CSV foram rodados isoladamente: 108 passed.
Depois da primeira realocacao, os cinco arquivos direcionados deram 113 passed
([suite-pos-realocacao.txt](before-after/suite-pos-realocacao.txt)); depois da
segunda, os mesmos 113 passed e a suite completa esta em
[suite-pos-web.txt](before-after/suite-pos-web.txt).

## Aprovacao

O horario e o da gravacao em disco do estado transformado. A sessao interrompida
nao registrou gate em artefato; a limpeza de fechamento foi feita nesta sessao e
esta coberta pelo mesmo diff reconstruido.
