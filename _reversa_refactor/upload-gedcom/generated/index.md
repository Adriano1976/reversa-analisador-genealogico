<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-09-30T13:10:36-03:00 a partir de 4 oportunidades -->

# Índice de qualidade de código · upload-gedcom

> Gerado em `2026-09-30T13:10:36-03:00`. Fonte de verdade: `../opportunities/*.md`.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #9 | `OPP-20260929-SEQO` | prune | green | superfície de instalação e efeito colateral em disco no start da aplicação | low | applied | menos dependência instalada e nenhuma pasta criada sem motivo |
| #14 | `OPP-20260929-DW3U` | prune | green | superfície de leitura e uma pista falsa, na forma de uma propriedade quebrada | low | applied | menos código sem consumidor, ao custo de decisão sobre a linha de base de testes |
| #8 | `OPP-20260929-B5F2` | modularize | green | 124 linhas e 14 testes que não protegem nada do que roda; pistas falsas para quem investiga | low | applied | menos superfície de leitura, ao custo de decisão explícita sobre a linha de base de testes |
| #10 | `OPP-20260929-EHNZ` | decouple | yellow | acoplamento estrutural | high | **declined** | nenhum ganho como refactor. Ver a nota de escopo abaixo antes de rotear |

## Reconciliação de 2026-10-06

`OPP-20260929-EHNZ` foi marcada `declined` na auditoria das quatro configurações pedidas pelo
usuário, por dois motivos independentes:

1. **alvos mortos:** o bloco `target` aponta para `analisador-genealogico/reconstructed/*.py`, raiz
   que deixou de existir em 2026-10-03 com a `OPP-20261003-FLAT`;
2. **conteúdo duplicado:** a `OPP-20261006-3WR5` registra o mesmo acoplamento por variável global
   de módulo, com medição atualizada e sobre os arquivos atuais.

O que não foi descartado: a conclusão de que trocar o estado global não é refactor e pertence ao
Forward (princípio II), o encaminhamento com `BR-HUMANA-004`, `AMB-009` e `BR-DESCARTAR-002`, o
vínculo com o `BUG-20260929-BJJH` e a exigência de caracterização de concorrência. Tudo isso vive
agora em `OPP-20261006-3WR5`. O registro original fica preservado: `declined` nunca apaga.

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

---
*Gerado pelo Reversa-Refactor em 2026-09-30.*
