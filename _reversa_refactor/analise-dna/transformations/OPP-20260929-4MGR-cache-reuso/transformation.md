---
schema_version: 1
id: OPP-20260929-4MGR
verb: optimize
state: applied
safety_net:
  kind: characterization
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/indice-antes.txt
    - before-after/indice-depois.txt
    - safety-net/equivalence-after-apply.txt
    - safety-net/pytest-after-apply.txt
measurement:
  before: "build_ged_indexes: mediana de 0,610 s para 2.000 pessoas; 8,0 norm_name, 2,0 split_name_pt e 2,0 surname_core_tokens por pessoa"
  after: "mediana de 0,360 s; 3,0 norm_name, 1,0 split_name_pt e 1,0 surname_core_tokens por pessoa; ganho de 1,69x"
  complexity: "O(N) antes e depois: o ganho e de fator constante, nao algoritmico"
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: given_tokens passa a derivar de key, que ja e norm_name(nm), reproduzindo o fallback de top_given_tokens, em vez de renormalizar
    diff: CHG-001.diff
  - chg: CHG-002
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: surnames passa a usar a lista ja calculada, em vez de chamar surnames_set, que refazia split_name_pt
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff]
---

## O que foi feito

Duas linhas de `build_ged_indexes` deixaram de recalcular o que já estava em mãos. É a correção de uma
regressão que a própria `OPP-20260929-AU76` introduziu quando escreveu o cache de atributos.

## Premissa verificada antes de aplicar

A mudança assume que `norm_name` é idempotente sobre os próprios tokens, ou seja, que um token
extraído de `norm_name(nm)` não muda ao passar por `norm_name` de novo. Isso foi verificado antes da
aplicação, em 14.826 tokens:

- nomes gerados de 10 prenomes e 8 sobrenomes, incluindo compostos, com hífen e com apóstrofo
- `"JoA?o Silva"` e `"Ã§ Carlos"`, que exercitam a limpeza de mojibake
- string vazia, espaço, só stop words e um nome de 80 caracteres

Resultado: **0 divergências**. A razão é que `norm_name` já removeu acentuação, pontuação e caixa, e
tokens normalizados contêm apenas caracteres de palavra.

## Medição

Sonda isolada, 2.000 pessoas sintéticas, mediana de 3 repetições:

| Medida | Antes | Depois | Ganho |
|--------|-------|--------|-------|
| `build_ged_indexes` | 0,610 s | **0,360 s** | **1,69x** |
| `norm_name` por pessoa | 8,00 | **3,00** | 2,67x |
| `split_name_pt` por pessoa | 2,00 | 1,00 | 2,0x |
| `surname_core_tokens` por pessoa | 2,00 | 1,00 | 2,0x |
| `surnames_set` por pessoa | 1,00 | **0,00** | eliminada |
| `top_given_tokens` por pessoa | 1,00 | **0,00** | eliminada |

O ganho é de **fator constante**, não algorítmico: `build_ged_indexes` era e continua sendo `O(N)`.

**Ressalva de medição, declarada:** a comparação no nível do pipeline **não** é confiável nesta sessão.
O run posterior mostrou `parse + grafo` saltando de 0,541 s para 1,644 s no mesmo comando, o que
indica carga na máquina durante a medição. Por isso a medida autoritativa é a da sonda isolada, que
usa mediana de 3 no mesmo processo. O `build_ged_indexes` medido dentro do pipeline apareceu como
0,263 s ali, contra 0,360 s na sonda, o que confirma a variância.

## Preservação de comportamento

| Rede | Resultado |
|------|-----------|
| Equivalência isolada, pré-4MGR contra pós-4MGR | 2.206 comparações, **0 divergências** |
| Suíte completa | **76 passed** |

A equivalência compara decisões de matching e também a string de motivo, que carrega os valores
calculados. Ela é o que garante que o fallback de `top_given_tokens` foi reproduzido corretamente,
inclusive para nomes compostos só de stop words.

## Estado do arquivo

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/dna_analysis.py` | 391 linhas | 396 linhas |

O arquivo cresceu porque o comentário explica a premissa. O diff tem 30 linhas e 1 hunk.

## Observações de follow-up, não aplicadas

Três redundâncias da mesma família ficaram **fora** desta transformação, para manter o diff e a
atribuição da medição sob controle:

1. `match_candidates` calcula `key = norm_name(match_name)` na linha 231 e `key_norm =
   norm_name(match_name)` na linha 256. São o mesmo valor, e `match_name` não é mutado entre elas.
2. `csv_surn_all = drop_short_tokens(surnames_set(match_name))`, na linha 238, refaz
   `split_name_pt(match_name)`, que já foi chamado na linha 236. `set(surn_csv)` é equivalente.
3. `build_ged_indexes` ainda gasta 3,0 `norm_name` por pessoa, porque `split_name_pt(nm)` normaliza
   por dentro duas vezes. Atacá-la exigiria `split_name_pt` aceitar um nome já normalizado, o que é
   mudança de contrato interno, não duas linhas.

O `build_ged_indexes` continua sendo a fase mais cara do pipeline depois desta correção.

## Reversão

Pelo `CHG-001.diff`, ou por
`git checkout -- analisador-genealogico/reconstructed/dna_analysis.py`. O estado congelado em
`.pytest-tmp/state-pre-4mgr/` permite refazer a comparação.
