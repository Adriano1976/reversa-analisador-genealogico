---
schema_version: 1
id: OPP-20260929-NUMT
display_number: 12
context: analise-dna
verb: optimize
title: Ingestão de CSV com apply linha a linha e regex por coluna
target:
  files: [analisador-genealogico/reconstructed/dna_analysis.py]
  symbol: aggregate_matches, detect_columns
smell: trabalho por linha em Python puro onde a biblioteca já opera em coluna
roi:
  confidence: green
  impact: custo que cresce linearmente com o CSV, e CSV de GEDmatch tem milhares de linhas
  cost: medium
  est_return: ingestão proporcional ao tamanho real do arquivo, não ao número de chamadas Python
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/analise-dna/design.md#fluxo-principal, _reversa_sdd/migration/target_business_rules.md#br-migrar-016-agregação-de-segmentos-chave-_group_key-e-soma-de-cm]
---

## Antes observado

Dois pontos na ingestão:

1. `aggregate_matches` monta a chave de agrupamento com
   `df.apply(build_group_key, axis=1)`. Isso percorre o DataFrame **uma linha por vez**, e para cada
   linha chama `norm_name(demojibake(str(...)))` em Python. A chave é
   `norm_name(nome) | ID-EMAIL`, uma concatenação que se expressa em operações de coluna.
2. `detect_columns` faz, para **cada coluna** do DataFrame,
   `df[c].astype(str).str.fullmatch(regex).mean() > 0.3`. É uma varredura com regex sobre a coluna
   inteira, repetida para todas as colunas, para descobrir no máximo uma.

Medição, árvore de 1.023 pessoas e CSV de 300 linhas:

| Fase | Difuso | Aceite |
|------|--------|--------|
| `detect_columns` | 0,003 s (0,9%) | 0,003 s (0,9%) |
| `aggregate_matches` | 0,027 s (8,2%) | 0,033 s (2,6%) |

São valores pequenos nesta escala, e o ponto é a escala: um CSV real do GEDmatch tem milhares de
linhas, e as duas fases crescem linearmente com ele enquanto o resto do pipeline cresce com o número
de candidatos.

## Transformação proposta

Duas mudanças independentes, e a segunda é opcional:

1. **`aggregate_matches`**: trocar o `apply(axis=1)` por duas colunas intermediárias com
   `df[name_col].map(...)` ou por `str` de pandas, montando a chave por concatenação vetorizada. A
   regra é preservada: a chave continua sendo nome normalizado mais ID em maiúsculas, ou nome
   normalizado mais e-mail normalizado.
2. **`detect_columns`**: parar na primeira coluna que satisfaz o limiar, em vez de medir todas. Isso
   preserva a escolha, porque a semântica atual também é "a primeira que casa" (`next(...)`), mas hoje
   ela é calculada para todas antes de escolher.

## Rede de segurança exigida

- Equivalência diferencial contra estado congelado. Importa muito aqui: a chave de agrupamento define
  quais segmentos são somados, e uma diferença de normalização muda o cM total e cascateia na
  previsão de parentesco. As fixtures `duplicated.csv`, `latin1.csv` e `generic.csv` de
  `_reversa_sdd/parity/fixtures/dna/` exercitam exatamente isso.
- `tests/test_characterization_matching.py`, que congela o cM somado para o caso duplicado.
- Medição antes e depois.

## Risco

Médio. A mudança de `apply` para operação de coluna é onde mora o risco: qualquer diferença em como o
`str` do pandas trata `NaN` ou espaços muda a chave e, portanto, a soma de cM. O teste que congela
`537` para o caso duplicado é a barreira, e ele existe desde a promoção das redes de segurança.

## Observação

A segunda mudança é a de menor risco e a de menor ganho: um CSV tem poucas colunas. Se as duas forem
separadas, ela pode ser descartada sem prejuízo.

---
*Gerado pelo Reversa-Refactor em 2026-09-29.*
