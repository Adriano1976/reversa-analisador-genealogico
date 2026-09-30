<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-09-30T13:10:36-03:00 a partir de 1 oportunidades -->

# Índice de qualidade de código · verificacao-de-tipos

> Gerado em `2026-09-30T13:10:36-03:00`. Fonte de verdade: `../opportunities/*.md`.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #17 | `OPP-20260929-Z6IO` | prune | green | a config que governa a resolucao de imports na checagem de tipos estava silenciosamente inerte, e as supressoes escondiam isso | low | applied | a checagem de tipos passa a resolver o pacote reconstruido de fato, e seis anotacoes mortas saem dos testes |

## Transformações

| OPP | Estado | Plano | Diff proposto | Rede de segurança |
|-----|--------|-------|---------------|-------------------|
| `OPP-20260929-Z6IO` | aplicada | - | sim | 2 artefato(s) |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`
