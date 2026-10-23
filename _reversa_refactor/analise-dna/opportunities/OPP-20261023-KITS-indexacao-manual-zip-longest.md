---
schema_version: 1
id: OPP-20261023-KITS
display_number: 38
context: analise-dna
verb: simplify
title: Indexação manual com guarda de tamanho em _kits substitutível por zip_longest
target:
  files: [src/application/projecao_analise.py]
  symbol: _kits
smell: >
  A função _kits usa enumerate + indexação manual com guarda `if posicao < len(avaliacoes)`
  para parear duas listas de tamanhos potencialmente diferentes. O padrão expresso é exatamente
  o que itertools.zip_longest implementa: o guard e o indexador podem desaparecer.
roi:
  confidence: green
  impact: >
    Reduz a função, elimina a lógica de indexação defensiva e deixa a
    intenção (parear duas listas, completar a mais curta com {}) explícita no nome da função
    usada. O comportamento é idêntico: posicao e kit já estão disponíveis via enumerate.
  cost: low
  est_return: >
    _kits de 17 para 14 linhas. Lógica de pareamento declarativa e tupla direta. Nenhuma mudança de comportamento.
state: applied
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/analise-dna/requirements.md#RF-05
---

## Antes observado

```python
def _kits(evidence: dict, comparison: dict) -> tuple[KitDaAnalise, ...]:
    kits = (evidence or {}).get("kits") or []
    avaliacoes = (comparison or {}).get("per_kit") or []
    final = (comparison or {}).get("status") or "INCONCLUSIVO"
    blocos = []
    for posicao, kit in enumerate(kits):
        avaliacao = avaliacoes[posicao] if posicao < len(avaliacoes) else {}  # guarda manual
        blocos.append(KitDaAnalise(
            ordinal=posicao,
            ...
            status=avaliacao.get("status") or final,
            status_note=avaliacao.get("note"),
        ))
    return tuple(blocos)
```

## Transformação proposta

```python
from itertools import zip_longest

def _kits(evidence: dict, comparison: dict) -> tuple[KitDaAnalise, ...]:
    kits = (evidence or {}).get("kits") or []
    avaliacoes = (comparison or {}).get("per_kit") or []
    final = (comparison or {}).get("status") or "INCONCLUSIVO"
    return tuple(
        KitDaAnalise(
            ordinal=posicao,
            kit=kit.get("kit"),
            source=kit.get("source"),
            total_cm=kit.get("total_cm"),
            segment_count=kit.get("segment_count"),
            largest_segment_cm=kit.get("largest_segment_cm"),
            status=avaliacao.get("status") or final,
            status_note=avaliacao.get("note"),
        )
        for posicao, (kit, avaliacao) in enumerate(zip_longest(kits, avaliacoes[:len(kits)], fillvalue={}))
    )
```

## Prova de equivalência

A guarda `avaliacoes[posicao] if posicao < len(avaliacoes) else {}` e o
`zip_longest(..., fillvalue={})` produzem o mesmo resultado quando `avaliacoes`
e mais curta: ambas devolvem `{}` para os indices faltantes.

Quando `avaliacoes` e **mais longa**, a equivalencia depende da fatia
`avaliacoes[:len(kits)]`. Sem ela, `zip_longest` iria ate a lista mais longa e
criaria `KitDaAnalise` extras com `kit={}`, que o `enumerate(kits)` original nunca
produzia. A fatia e o que preserva o truncamento.

## Rede de segurança

A suíte existente cobre o comportamento de produção de `_kits` indiretamente via `projetar_analise`.
O gate é a suíte verde antes e depois, sem nova caracterização.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*
