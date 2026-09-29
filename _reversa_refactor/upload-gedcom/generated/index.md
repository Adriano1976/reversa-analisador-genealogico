<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-09-29T15:43:34-03:00 a partir de 4 oportunidades -->

# Índice de qualidade de código · upload-gedcom

> Gerado em `2026-09-29T15:43:34-03:00`. Fonte de verdade: `../opportunities/*.md`.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #9 | `OPP-20260929-SEQO` | prune | green | superfície de instalação e efeito colateral em disco no start da aplicação | low | applied | menos dependência instalada e nenhuma pasta criada sem motivo |
| #14 | `OPP-20260929-DW3U` | prune | green | superfície de leitura e uma pista falsa, na forma de uma propriedade quebrada | low | applied | menos código sem consumidor, ao custo de decisão sobre a linha de base de testes |
| #8 | `OPP-20260929-B5F2` | modularize | green | 124 linhas e 14 testes que não protegem nada do que roda; pistas falsas para quem investiga | low | applied | menos superfície de leitura, ao custo de decisão explícita sobre a linha de base de testes |
| #10 | `OPP-20260929-EHNZ` | decouple | yellow | acoplamento estrutural | high | proposed | nenhum ganho como refactor. Ver a nota de escopo abaixo antes de rotear |

## Transformações

| OPP | Estado | Plano | Diff proposto | Rede de segurança |
|-----|--------|-------|---------------|-------------------|
| `OPP-20260929-B5F2` | aplicada | - | sim | 2 artefato(s) |
| `OPP-20260929-DW3U` | aplicada | - | sim | 1 artefato(s) |
| `OPP-20260929-SEQO` | aplicada | `plan.html` | sim | 5 artefato(s) |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`
