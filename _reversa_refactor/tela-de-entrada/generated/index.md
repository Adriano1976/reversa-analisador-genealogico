<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-23T03:45:00-03:00 a partir de 5 oportunidades -->
<!-- Reconciliado em 2026-10-23: OPP-20261023-DISP passou a applied (diff reconstruido e verificado); evidencia de suite substituida por medicao real; OPP-20261023-SERV permanece declined. -->

# Indice de qualidade de codigo: tela-de-entrada

> Gerado em `2026-10-23T03:45:00-03:00`. Fonte de verdade: `../opportunities/*.md`. Ordenado por `display_number`.

## Oportunidades

| # | ID | Verbo | Confianca | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #39 | `OPP-20261023-DISP` | restructure | 🟢 green | rota principal acumulava 5 acoes em cascata procedural com duplicacao de try/except e render_template | medium | **applied** | index() de 234 para 19 linhas; 5 handlers dedicados e dois mapas de acao |
| #40 | `OPP-20261023-ASST` | modularize | 🟢 green | rotas de assets estaticos e download poluiam o modulo principal da aplicacao | low | **applied** | Blueprint `assets_bp` em `src/web/rotas_assets.py`; app.py de 888 para 737 linhas |
| #41 | `OPP-20261023-SERV` | decouple | 🟢 green | logica de rede, socket exclusivo de SO e Waitress embutidos no app | low | declined | recusada: `tests/test_servidor_producao.py` exige o bloco no AST de `app.py` |
| #42 | `OPP-20261023-FACT` | modularize | 🟡 yellow | instancia Flask criada como singleton global no import, junto de config, seguranca e rotas | medium | **applied** | composition root explicito (`create_app`), com isolamento de configuracao; 6 testes novos |
| #43 | `OPP-20261023-DEAD` | prune | 🟢 green | guarda `arvore is None` declarada inalcancavel pelo proprio comentario | low | **applied** | ramo morto unificado; checagem mantida para estreitar tipo |

## Transformacoes

| OPP | Estado | Registro | Diff de reversao | Rede de seguranca |
|-----|--------|----------|------------------|-------------------|
| `OPP-20261023-DISP` | applied | [transformation.md](../transformations/OPP-20261023-DISP-despachador-de-acoes-na-rota-principal/transformation.md) | `CHG-001-despachador-de-acoes.diff` (471 linhas) | 1615 passed, 9 skipped antes e depois (lote) |
| `OPP-20261023-ASST` | applied | [transformation.md](../transformations/OPP-20261023-ASST-extracao-de-rotas-de-assets-em-blueprint/transformation.md) | `CHG-001` a `CHG-005` (app, modulo, template, realocacoes) | 1615/9 no lote + 113 direcionados e suite completa apos cada realocacao |
| `OPP-20261023-SERV` | declined | - | - | contrato estatico de AST em `tests/test_servidor_producao.py` |
| `OPP-20261023-FACT` | applied | [transformation.md](../transformations/OPP-20261023-FACT-padrao-application-factory/transformation.md) | `CHG-001-fabrica-do-app.diff` (317 linhas) | 1615 passed, 9 skipped antes; 1621 passed, 9 skipped depois |
| `OPP-20261023-DEAD` | applied | [transformation.md](../transformations/OPP-20261023-DEAD-verificacao-inalcancavel-de-arvore/transformation.md) | `CHG-001-guarda-unificada.diff` (19 linhas) | 1615/9 no lote + prova de inalcancabilidade |

## Auditoria de 2026-10-23

O lote de `tela-de-entrada` foi aplicado por uma sessao que parou no meio: as tres
transformacoes estavam no codigo, mas o registro estava incompleto e, em parte,
incorreto.

| Constatacao | Correcao |
|---|---|
| `OPP-20261023-DISP` aplicada no codigo e marcada `proposed` no indice, sem `transformation.md` | Estado corrigido para `applied`; registro escrito; diff real gerado |
| o `proposed.diff` de DISP era um esboco com `...` e nao aplicava | Removido; substituido por `CHG-001-despachador-de-acoes.diff` |
| os arquivos de suite herdados declaravam `Python 3.12.3`, `pytest 8.3.2` e `pyproject.toml`, que o projeto nao tem | Substituidos pela medicao real: 1615 passed, 9 skipped em 190,29 s (HEAD) e 197,00 s (working tree) |
| `DEAD` e `ASST` tinham `green_before`/`green_after` sem prova valida | Medicao real nas duas pontas; prova de inalcancabilidade anexada a DEAD |
| a extracao de ASST deixou quatro regras `build_only`, quatro re-exportacoes sem efeito e `import json` sem uso | Removidos; `url_for` do template aponta para `assets.descartes_em_csv` |
| o `plan.md` de DISP apontava linhas 415-645, e a oportunidade 560-792 | Corrigido para 561-794 na linha de base `HEAD 221b6c1` |

Verificacao de tipos: **nao remedida**. O `pyrefly` nao esta instalado no `.venv`
(`No module named pyrefly`), e o numero de 27 erros do README e de 2026-10-06,
em outro ambiente.

### FACT aplicada depois do fechamento do lote

A `OPP-20261023-FACT`, que estava `proposed`, foi aprovada em plano e em diff e
aplicada no mesmo dia. `create_app(config=None)` existe em `src/app.py`, o app de
modulo e criado por ele, e `tests/test_fabrica_do_app.py` acrescenta 6 testes. A
suite foi de 1615 para 1621 passed, com as mesmas 9 exclusoes. O limite segue
declarado: a fabrica isola configuracao, nao o estado de borda.

## Legenda

- Confianca: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*
