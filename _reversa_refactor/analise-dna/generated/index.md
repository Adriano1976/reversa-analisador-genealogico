<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-08T11:17:31-03:00 a partir de 9 oportunidades -->
<!-- Historico: gerado em 2026-09-30 por 8 oportunidades e atualizado a mao em 2026-10-01 (NUMT e ZV52 para applied). -->
<!-- Regenerado em 2026-10-08 pelo /reversa-refactor com a OPP-20261008-JXQN. Mudancas de forma declaradas: ordem por display_number, e Rede de seguranca contando safety-net/ para TODAS as linhas (com a metrica unica, NUMT fica 1 e ZV52 fica 1). -->

# Indice de qualidade de codigo - analise-dna

> Gerado em `2026-10-08T11:17:31-03:00`. Fonte de verdade: `../opportunities/*.md`. Ordenado por `display_number`.

## Oportunidades

| # | ID | Verbo | Confianca | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #1 | `OPP-20260929-AU76` | optimize | 🟢 green | hotpath. O laço roda uma vez por match do CSV e renormaliza o mesmo candidato a cada match | low | applied | cerca de 3 vezes menos tempo por match, sem alterar nenhum resultado |
| #2 | `OPP-20260929-32Q7` | prune | 🟢 green | custo de construção pago em toda análise e uma afirmação falsa na documentação do módulo | low | applied | remove cerca de um terço do custo de build_ged_indexes e alinha o docstring ao código |
| #3 | `OPP-20260929-ZV52` | modularize | 🟡 yellow | acoplamento e clareza. É o módulo mais difícil de testar em partes e o que mais muda | medium | applied | cada responsabilidade testável isoladamente, sem tocar em nenhuma regra de negócio |
| #4 | `OPP-20260929-4LE3` | modularize | 🟢 green | risco de correção no lugar errado. Quem for ajustar mojibake tem dois alvos plausíveis | low | applied | uma única autoridade sobre limpeza de nome, com a divergência documentada em vez de escondida |
| #11 | `OPP-20260929-4MGR` | optimize | 🟢 green | hotpath. O índice passou a ser a fase mais cara da análise, e é chamado uma vez por análise | low | applied | cerca de 2,7x menos normalizações na construção do índice, sem alterar nenhum resultado |
| #12 | `OPP-20260929-NUMT` | optimize | 🟢 green | custo que cresce linearmente com o CSV, e CSV de GEDmatch tem milhares de linhas | medium | applied | ingestão proporcional ao tamanho real do arquivo, não ao número de chamadas Python |
| #13 | `OPP-20260929-IM3Q` | prune | 🟢 green | superfície de instalação e tempo de build de ambiente, sem nenhum ganho em troca | low | applied | uma dependência nativa a menos para compilar em cada ambiente novo |
| #16 | `OPP-20260929-U2NK` | prune | 🟢 green | clareza do modulo e uma pista falsa sobre onde a regex de ID vive | low | applied | uma linha a menos e nenhuma ambiguidade sobre a origem da regex de ID |
| #34 | `OPP-20261008-JXQN` | prune | 🟢 green | fecha a defesa textual do ADR-19 (as faixas continuam alcançáveis por importação) e a dívida #18, tirando do pacote 65 linhas de heurística já retirada do fluxo, sem tocar em comportamento algum | low | proposed (orfao suspeito) | 65 linhas e 2 testes a menos de heurística aposentada, com a defesa contra uso indevido passando de textual para estrutural |

## Transformacoes

| OPP | Estado | Plano | Diff proposto | Rede de seguranca |
|-----|--------|-------|---------------|-------------------|
| `OPP-20260929-AU76` | applied | sim | sim | 3 artefato(s) |
| `OPP-20260929-32Q7` | applied | sim | sim | 4 artefato(s) |
| `OPP-20260929-ZV52` | applied | sim | sim | 1 artefato(s) |
| `OPP-20260929-4MGR` | applied | - | sim | 2 artefato(s) |
| `OPP-20260929-NUMT` | applied | sim | sim | 1 artefato(s) |
| `OPP-20260929-IM3Q` | applied | - | sim | 1 artefato(s) |
| `OPP-20260929-U2NK` | applied | - | sim | 2 artefato(s) |
| `OPP-20261008-JXQN` | proposed | sim | - | 0 artefato(s) |

## Legenda

- Confianca: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`
- `promoted_to: null` marca orfao suspeito: sem referencia estatica provada morta, e o podador nao remove

---
*Gerado pelo Reversa-Refactor em 2026-10-08.*
