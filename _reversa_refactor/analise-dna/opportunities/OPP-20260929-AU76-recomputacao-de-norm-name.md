---
schema_version: 1
id: OPP-20260929-AU76
display_number: 1
context: analise-dna
verb: optimize
title: Recomputação de norm_name domina o custo do matching difuso
target:
  files: [analisador-genealogico/reconstructed/dna_analysis.py]
  symbol: match_candidates, build_ged_indexes
smell: normalização de nome recalculada dentro do laço de candidatos, sem memoização nem pré-cálculo por pessoa
roi:
  confidence: green
  impact: hotpath. O laço roda uma vez por match do CSV e renormaliza o mesmo candidato a cada match
  cost: low
  est_return: cerca de 3 vezes menos tempo por match, sem alterar nenhum resultado
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/domain.md#23-regras-de-namespace-de-nome-matching-viral, _reversa_sdd/migration/parity_harness.md]
---

## Roteamento

- Destino: `/reversa-optimize OPP-20260929-AU76`
- Ordem de encadeamento: **2 de 4**.
- Aprovada pelo usuário em 2026-09-29 para roteamento, com execução parando no gate.
- Motivo da posição: maior retorno medido da lista. Vem antes da `OPP-20260929-32Q7` porque as duas
  tocam as mesmas duas funções, `build_ged_indexes` e `match_candidates`, e esta tem diff maior.

## Estado do gate

Especialista acionado em 2026-09-29 em `control_mode: gated`. Plano e prova estão prontos em
`../transformations/OPP-20260929-AU76-cache-de-atributos/`. Equivalência e ganho **já medidos**
contra uma cópia sombra do pacote, sem tocar no projeto:

| Métrica (3.000 pessoas, 100 matches, mediana de 3) | Atual | Otimizada | Ganho |
|---|---|---|---|
| `build_ged_indexes` (s) | 0,390 | 0,821 | 0,48x |
| ms por match | 31,90 | 2,13 | **14,98x** |
| `norm_name` por match | 728,2 | 4,0 | **182x** |
| chamadas de fuzzy por match | 413,0 | 413,0 | 1,00x |

Ponto de equilíbrio em cerca de 15 matches por CSV: acima disso a otimização ganha, abaixo há
regressão de no máximo 0,43 s por análise. Equivalência de saída: **2.206 comparações, 0
divergências**. Suíte: 50 passed nas duas variantes.

A medição da primeira sonda desta sessão (52,4 ms por match) veio de outro corpus e de uma única
execução. O número autoritativo é o do script em `before-after/profile_matching.py`, que fixa
semente, mede 100 matches e usa a mediana de 3 repetições.

A aplicação está **bloqueada** por `.reversa/reversa-config.json` em `allowLegacyEdits: false`.
O arquivo alvo é `analisador-genealogico/reconstructed/dna_analysis.py`.

## Antes observado

Sonda em `.pytest-tmp/probe_fuzzy_profile.py`, com 3.000 pessoas sintéticas e 100 matches sintéticos
(nenhum dado real). Resultado medido nesta sessão:

| Medida | Valor |
|--------|-------|
| `build_ged_indexes` | 0,499 s (3,0 chamadas de `norm_name` por pessoa) |
| `match_candidates` | 52,4 ms por match |
| Candidatos avaliados por match | 128,5 |
| Chamadas de fuzzy por match | 514 |
| `norm_name` dentro do laço | 90.609 chamadas, ou 7,05 por candidato |
| Custo de uma chamada de `norm_name` | 41,3 µs |
| Custo de uma chamada de `surnames_set` | 72,3 µs |

Conta: 7,05 x 41,3 µs = 291 µs por candidato, vezes 128,5 candidatos = **37,4 ms dos 52,4 ms por
match (71%)**.

O que **não** é o gargalo, ao contrário da hipótese inicial: as chamadas de fuzzy. `python-Levenshtein
0.27.3` está instalado e o `thefuzz` resolve para `rapidfuzz`, que é C++. As 514 chamadas por match
custam uma fração pequena do total.

Origem da redundância, em `dna_analysis.py:275-286`: para cada candidato do pool, o código chama
`get_name`, depois `norm_name(nm)` duas vezes (linhas 279 e 280, mais o `top_given_tokens` da linha
277 que renormaliza cada token), e `surnames_set(nm)` na linha 281, que por dentro chama
`split_name_pt`, que chama `norm_name` de novo mais `surname_core_tokens`, que chama `norm_name`
outra vez. Nada disso depende do match do CSV: é atributo fixo da pessoa no GEDCOM.

## Transformação proposta

Pré-calcular os atributos normalizados de cada pessoa uma única vez, na construção do índice, e
consumi-los no laço:

1. `build_ged_indexes` passa a devolver também um mapa `pid -> features`, com nome normalizado, tokens
   de given, conjunto de sobrenomes e conjunto de tokens, todos já calculados.
2. `match_candidates` lê esse mapa em vez de renormalizar. O corpo do laço fica com as quatro
   chamadas de fuzzy e nada mais.
3. Opcional e equivalente: memoizar `norm_name`, `split_name_pt` e `surnames_set` com
   `functools.lru_cache`, o que resolve o mesmo problema sem mudar assinatura de função.

As duas formas preservam a saída porque não tocam em nenhum critério de aceitação, em nenhum limiar e
em nenhum desempate. A ordem de avaliação do pool e a regra de escolha de `best_pid` ficam intactas.

## Rede de segurança exigida

- `tests/test_dna_analysis.py` (11 testes) verde antes e depois.
- Harness de paridade `_reversa_sdd/parity/harness.py` com as fixtures de `_reversa_sdd/parity/fixtures/`,
  que é a prova de equivalência de saída mais forte disponível aqui.
- Medição antes e depois obrigatória, pelo schema (`optimize` exige `measurement`).

## Risco

Baixo. É adição de cache e pré-cálculo, sem mudança de controle de fluxo. O risco real é introduzir
divergência entre o valor cacheado e `get_name` se o GEDCOM for recarregado no meio da requisição,
o que não acontece hoje: o upload e a análise são requisições separadas, e `build_ged_indexes` é
chamado por análise.

## Observação de escopo

Uma ideia vizinha foi deliberadamente **excluída** deste registro por violar o princípio II: usar
`given_index` para podar o pool de candidatos. Podar o pool muda qual candidato vence, logo muda
comportamento observável. Isso é feature do Forward, não refactor. O índice morto em si está na
`OPP-20260929-32Q7`.
