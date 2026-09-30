---
schema_version: 1
id: OPP-20260929-4MGR
display_number: 11
context: analise-dna
verb: optimize
title: build_ged_indexes recalcula normalizações que já tem em mãos
target:
  files: [analisador-genealogico/reconstructed/dna_analysis.py]
  symbol: build_ged_indexes
smell: o cache de atributos renormaliza o mesmo nome em vez de reusar o que acabou de calcular
roi:
  confidence: green
  impact: hotpath. O índice passou a ser a fase mais cara da análise, e é chamado uma vez por análise
  cost: low
  est_return: cerca de 2,7x menos normalizações na construção do índice, sem alterar nenhum resultado
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/domain.md#23-regras-de-namespace-de-nome-matching-viral, _reversa_sdd/analise-dna/design.md#interface]
---

## Origem deste achado: uma regressão introduzida pela AU76

Esta oportunidade nasceu da re-inventariação de 2026-09-29, feita depois das cinco transformações.
Ela corrige uma ineficiência que a própria `OPP-20260929-AU76` introduziu: o cache de atributos foi
escrito reusando as funções existentes sem perceber que duas delas repetem trabalho já feito ali
mesmo.

## Antes observado

Contagem instrumentada, 2.000 pessoas sintéticas:

| Chamada | Total | Por pessoa |
|---------|-------|-----------|
| `get_name` | 2.000 | 1,00 |
| `norm_name` | 16.000 | **8,00** |
| `split_name_pt` | 4.000 | **2,00** |
| `surname_core_tokens` | 4.000 | **2,00** |
| `surnames_set` | 2.000 | 1,00 |
| `top_given_tokens` | 2.000 | 1,00 |

Antes da AU76, `build_ged_indexes` fazia 3,0 `norm_name` por pessoa. Hoje faz 8,0.

O corpo atual, com as linhas que importam:

```python
    nm = get_name(person)
    key = norm_name(nm)                                  # 1 norm_name
    ged_index.setdefault(key, []).append(pid)
    _given, surnames, _suffixes = split_name_pt(nm)       # +2 norm_name por dentro
    ...
        "given_tokens": [norm_name(t) for t in top_given_tokens(nm, k=2)],   # +3
        "surnames": surnames_set(nm),                    # +2, refazendo split_name_pt
```

As duas redundâncias:

1. `surnames_set(nm)` chama `split_name_pt(nm)` por dentro e devolve `set(surnames)`. A lista
   `surnames` já foi calculada duas linhas acima. `set(surnames)` dá o mesmo resultado.
2. `top_given_tokens(nm, k=2)` refaz `norm_name(nm)`, que já está em `key`, e cada token devolvido é
   renormalizado, o que é idempotente porque `key` já passou por `norm_name`. Dá para derivar de
   `key.split()` filtrando `STOP_WORDS`, que é exatamente o que `top_given_tokens` faz.

## Medição

| Cenário | Valor |
|---------|-------|
| `build_ged_indexes`, 2.000 pessoas, mediana de 3 | 0,787 s |
| Participação no pipeline de aceite, árvore de 1.023 pessoas e 300 matches | 0,212 s de 0,328 s, **64,7%** |
| Participação no pipeline difuso, mesma árvore | 0,227 s de 1,287 s, 17,6% |

O índice é custo fixo por análise, pago antes de o primeiro match ser avaliado. Ele pesa
proporcionalmente mais quanto menos trabalho o matching tiver, o que é exatamente o cenário criado
pela AU76.

## Transformação proposta

Reusar o que já está calculado, sem tocar em nenhuma regra:

```python
        "given_tokens": [t for t in key.split() if t not in STOP_WORDS][:2],
        "surnames": set(surnames),
```

Isso derruba `norm_name` por pessoa de 8,0 para 3,0 e `split_name_pt` de 2,0 para 1,0. A equivalência
de saída é verificável com o mesmo harness diferencial usado nas outras otimizações.

## Rede de segurança exigida

- Equivalência diferencial contra estado congelado, no corpus sintético, com zero divergências.
- `tests/test_characterization_matching.py`, que congela as decisões do matching, e
  `tests/test_dna_analysis.py`.
- Medição antes e depois, obrigatória para `optimize`.

## Risco

Baixo, com um ponto de atenção real: `top_given_tokens` tem um fallback (`toks[:k] or n.split()[:k]`)
para o caso de todos os tokens serem stop words. A derivação precisa reproduzir esse fallback, senão
nomes compostos só de stop words mudam de comportamento. O teste de caracterização cobre esse caso
com as fixtures atuais, mas a equivalência diferencial é o que garante.

## Observação

Esta oportunidade **não depende** de nenhuma das restantes. É a de maior retorno da re-inventariação, e
o diff é de duas linhas.

---
*Gerado pelo Reversa-Refactor em 2026-09-29.*
