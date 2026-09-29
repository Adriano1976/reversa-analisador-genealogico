<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-09-29T15:43:34-03:00 a partir de 4 oportunidades -->

# Índice de qualidade de código · busca-caminho

> Gerado em `2026-09-29T15:43:34-03:00`. Fonte de verdade: `../opportunities/*.md`.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #5 | `OPP-20260929-TPSH` | restructure | green | risco de correção pela metade | low | applied | uma única autoridade de escape e de id de nó, eliminando a divergência em curso |
| #15 | `OPP-20260929-5XGJ` | standardize | green | quem lê precisa entender por que três formatos coexistem, e um deles tem supressão de aviso | low | proposed | uma única regra de import no arquivo, com o motivo escrito |
| #6 | `OPP-20260929-UXEF` | modularize | yellow | acoplamento e testabilidade | medium | proposed | busca testável sem render, e o render isolado como o ponto onde o escape vive |
| #7 | `OPP-20260929-H2YY` | simplify | yellow | clareza e risco de alteração | medium | proposed | mesma string gerada, com a estrutura do diagrama legível em nível de bloco |

## Transformações

| OPP | Estado | Plano | Diff proposto | Rede de segurança |
|-----|--------|-------|---------------|-------------------|
| `OPP-20260929-TPSH` | aplicada | `plan.html` | sim | 5 artefato(s) |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`
