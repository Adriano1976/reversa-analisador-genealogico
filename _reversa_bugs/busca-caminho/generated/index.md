<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-04T13:55:34-03:00 a partir de 3 bugs -->

# Índice de bugs · busca-caminho

> Gerado em `2026-10-04T13:55:34-03:00`. Fonte de verdade: os `bug.md` deste contexto.

## Resumo

| Status | Qtd |
|--------|-----|
| active | 1 |
| resolved | 2 |

| Phase | Qtd |
|-------|-----|
| mitigating | 1 |
| patching | 2 |

## Bugs abertos e ativos

| # | ID | Severidade | Prioridade | Título | area / module / feature | Status | Phase | Bloqueado |
|---|----|-----------|-----------|--------|------------------------|--------|-------|-----------|
| 1 | `BUG-20260929-BJJH` | critical | P0 | restrito | analisador-genealogico / upload / busca-caminho | active | mitigating | **sim** |

O bug aberto está **bloqueado por condição externa**: o tratamento decidido depende da Onda 3 da
migração, onde a spec manda resolver. Ele também está **mitigado por aceite de risco** desde
2026-10-04, com o legado mantido single-tenant por contingência prevista na spec. Mitigado não é
corrigido: o bug continua aberto.

## Resolvidos

Total: 2.

| # | ID | resolution_kind | Travado (DONE.md) |
|---|----|-----------------|------------------|
| 3 | `BUG-20260929-J6PQ` | fixed | sim |
| 4 | `BUG-20261002-T4ZM` | fixed | sim |

## Visibilidade restrita

2 bug(s) deste contexto têm `visibility: restricted`. Por política, título, labels, locators de spec e detalhe não aparecem em nenhuma view. O `bug.md` de cada um permanece completo na pasta do bug.

| # | ID | Situação |
|---|----|----------|
| 1 | `BUG-20260929-BJJH` | restrito |
| 3 | `BUG-20260929-J6PQ` | restrito |

## Inconsistências

Nenhuma: as invariantes do schema foram validadas nos 5 bugs do registro, cruzando contextos. Todos os `resolved` têm `resolution_kind` e `closure.satisfied: true`, todos os `fixed` têm `root_cause.state: confirmed`, `regression_tests` e `spec_verdict`, toda trava `DONE.md` corresponde a um bug fechado, e toda relação aponta para ID existente.

## Arestas que entram neste contexto

Uma aresta de fora aponta para um bug daqui: `BUG-20261004-EWSJ` (contexto `analise-dna`) tem `related-to` com o `BUG-20261002-T4ZM`, em estado `proposed`. Ela aparece derivada na `matrix.md` e tracejada no `graph.md`.
