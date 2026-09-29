<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-09-29T13:59:44-03:00 a partir de 4 oportunidades -->

# Índice de qualidade de código · analise-dna

> Gerado em `2026-09-29T13:59:44-03:00`. Fonte de verdade: `../opportunities/*.md`.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #1 | `OPP-20260929-AU76` | optimize | green | hotpath | low | applied | cerca de 3 vezes menos tempo por match, sem alterar nenhum resultado |
| #2 | `OPP-20260929-32Q7` | prune | green | custo de construção pago em toda análise e uma afirmação falsa na documentação do módulo | low | applied | remove cerca de um terço do custo de build_ged_indexes e alinha o docstring ao código |
| #4 | `OPP-20260929-4LE3` | modularize | green | risco de correção no lugar errado | low | proposed | uma única autoridade sobre limpeza de nome, com a divergência documentada em vez de escondida |
| #3 | `OPP-20260929-ZV52` | modularize | yellow | acoplamento e clareza | medium | proposed | cada responsabilidade testável isoladamente, sem tocar em nenhuma regra de negócio |

## Transformações

| OPP | Estado | Plano | Diff proposto | Rede de segurança |
|-----|--------|-------|---------------|-------------------|
| `OPP-20260929-32Q7` | aplicada | `plan.html` | sim | 4 artefato(s) |
| `OPP-20260929-AU76` | aplicada | `plan.html` | sim | 3 artefato(s) |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`
