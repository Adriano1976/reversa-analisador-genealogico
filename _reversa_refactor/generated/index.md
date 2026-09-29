<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-09-29T15:03:42-03:00 a partir de 15 oportunidades -->

# Registro de qualidade de código · visão global

> Gerado em `2026-09-29T15:03:42-03:00`. Ordenado por retorno estimado, não por estética.

Contextos: analise-dna, busca-caminho, upload-gedcom. Total: 15 oportunidades, 9 aplicada(s) e 6 em aberto.

## Ordem sugerida de ataque

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #1 | `OPP-20260929-AU76` | optimize | green | hotpath | low | applied | cerca de 3 vezes menos tempo por match, sem alterar nenhum resultado |
| #11 | `OPP-20260929-4MGR` | optimize | green | hotpath | low | applied | cerca de 2,7x menos normalizações na construção do índice, sem alterar nenhum resultado |
| #5 | `OPP-20260929-TPSH` | restructure | green | risco de correção pela metade | low | applied | uma única autoridade de escape e de id de nó, eliminando a divergência em curso |
| #2 | `OPP-20260929-32Q7` | prune | green | custo de construção pago em toda análise e uma afirmação falsa na documentação do módulo | low | applied | remove cerca de um terço do custo de build_ged_indexes e alinha o docstring ao código |
| #9 | `OPP-20260929-SEQO` | prune | green | superfície de instalação e efeito colateral em disco no start da aplicação | low | applied | menos dependência instalada e nenhuma pasta criada sem motivo |
| #12 | `OPP-20260929-NUMT` | optimize | green | custo que cresce linearmente com o CSV, e CSV de GEDmatch tem milhares de linhas | medium | proposed | ingestão proporcional ao tamanho real do arquivo, não ao número de chamadas Python |
| #13 | `OPP-20260929-IM3Q` | prune | green | superfície de instalação e tempo de build de ambiente, sem nenhum ganho em troca | low | applied | uma dependência nativa a menos para compilar em cada ambiente novo |
| #14 | `OPP-20260929-DW3U` | prune | green | superfície de leitura e uma pista falsa, na forma de uma propriedade quebrada | low | applied | menos código sem consumidor, ao custo de decisão sobre a linha de base de testes |
| #4 | `OPP-20260929-4LE3` | modularize | green | risco de correção no lugar errado | low | applied | uma única autoridade sobre limpeza de nome, com a divergência documentada em vez de escondida |
| #8 | `OPP-20260929-B5F2` | modularize | green | 124 linhas e 14 testes que não protegem nada do que roda; pistas falsas para quem investiga | low | applied | menos superfície de leitura, ao custo de decisão explícita sobre a linha de base de testes |
| #15 | `OPP-20260929-5XGJ` | standardize | green | quem lê precisa entender por que três formatos coexistem, e um deles tem supressão de aviso | low | proposed | uma única regra de import no arquivo, com o motivo escrito |
| #3 | `OPP-20260929-ZV52` | modularize | yellow | acoplamento e clareza | medium | proposed | cada responsabilidade testável isoladamente, sem tocar em nenhuma regra de negócio |
| #6 | `OPP-20260929-UXEF` | modularize | yellow | acoplamento e testabilidade | medium | proposed | busca testável sem render, e o render isolado como o ponto onde o escape vive |
| #7 | `OPP-20260929-H2YY` | simplify | yellow | clareza e risco de alteração | medium | proposed | mesma string gerada, com a estrutura do diagrama legível em nível de bloco |
| #10 | `OPP-20260929-EHNZ` | decouple | yellow | acoplamento estrutural | high | proposed | nenhum ganho como refactor. Ver a nota de escopo abaixo antes de rotear |

## Por contexto

| Contexto | Oportunidades | Caminho |
|----------|---------------|---------|
| `analise-dna` | 7 | `_reversa_refactor/analise-dna/` |
| `busca-caminho` | 4 | `_reversa_refactor/busca-caminho/` |
| `upload-gedcom` | 4 | `_reversa_refactor/upload-gedcom/` |

## Itens que NÃO devem ser roteados como refactor

| ID | Destino correto | Motivo |
|----|-----------------|--------|
| `OPP-20260929-EHNZ` | Forward | Trocar estado global altera arquitetura e concorrência: princípio II |
| `OPP-20260929-DW3U` (opção A) | Decisão humana antes | Remover as entidades derruba testes de `tests/test_domain.py`: mesmo dilema de linha de base |
| `OPP-20260929-DW3U` (opção C) | Forward | Dar consumidor às entidades reescreve `upload.py`: mudança de comportamento |
| poda do pool por `given_index` | Forward | Muda qual candidato vence: mudança de comportamento |

## Roteamento aprovado

Ordem de encadeamento definida pelo usuário em 2026-09-29. As 9 primeiras foram aplicadas sob o gate de edição do legado liberado; as demais seguem a mesma ordem e param no gate até serem autorizadas.

| Ordem | ID | Comando |
|-------|----|---------|
| 1 | `OPP-20260929-TPSH` | `/reversa-restructure OPP-20260929-TPSH` |
| 2 | `OPP-20260929-AU76` | `/reversa-optimize OPP-20260929-AU76` |
| 3 | `OPP-20260929-32Q7` | `/reversa-prune OPP-20260929-32Q7` |
| 4 | `OPP-20260929-SEQO` | `/reversa-prune OPP-20260929-SEQO` |
