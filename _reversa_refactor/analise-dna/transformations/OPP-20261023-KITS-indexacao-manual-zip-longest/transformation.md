---
schema_version: 1
id: OPP-20261023-KITS
verb: simplify
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
measurement:
  before: "loop com lista mutavel (`blocos = []` + `append`) e guarda de indice manual `if posicao < len(avaliacoes)`"
  after: "tupla direta por expressao geradora com `zip_longest` e fatia em `avaliacoes`, sem estado intermediario"
change_set:
  - chg: CHG-LOTE
    file: src/application/projecao_analise.py
    purpose: troca o loop imperativo de `_kits` por expressao geradora com `zip_longest`
approval:
  by: user
  at: 2026-10-23T00:32:52-03:00
reversible_via: [../OPP-20261023-MPRA-mistura-caso-uso-projecao/CHG-LOTE-extracao-e-mapper.diff]
---

# Transformacao: OPP-20261023-KITS (pareamento declarativo em `_kits`)

## O que mudou

```python
# antes
blocos = []
for posicao, kit in enumerate(kits):
    avaliacao = avaliacoes[posicao] if posicao < len(avaliacoes) else {}
    blocos.append(KitDaAnalise(..., status=avaliacao.get("status") or final, status_note=avaliacao.get("note")))
return tuple(blocos)

# depois
return tuple(
    KitDaAnalise(..., status=avaliacao.get("status") or final, status_note=avaliacao.get("note"))
    for posicao, (kit, avaliacao) in enumerate(
        zip_longest(kits, avaliacoes[:len(kits)], fillvalue={})
    )
)
```

## A fatia nao e detalhe, e a equivalencia

A proposta original desta oportunidade mostrava
`zip_longest(kits, avaliacoes, fillvalue={})` sem a fatia, e afirmava que, "quando
`avaliacoes` e mais longa, `zip_longest` trunca nos `kits`". **Isso esta errado:**
`zip_longest` para na lista mais longa, e uma `avaliacao` sobrando produziria um
`KitDaAnalise` extra, com `kit={}`. O codigo aplicado usa
`avaliacoes[:len(kits)]`, que e o que preserva o truncamento do `enumerate(kits)`
original. A prova de equivalencia da oportunidade foi corrigida.

Casos conferidos:

| `kits` | `avaliacoes` | Antes | Depois |
|---|---|---|---|
| vazio | qualquer | `()` | `()` |
| n | vazio | n blocos com estado final | n blocos com estado final (`fillvalue={}`) |
| n | m < n | n blocos, os ultimos com `{}` | identico |
| n | m > n | n blocos | n blocos, por causa da fatia |

## Diff acumulado

O diff e o das quatro transformacoes de `analise-dna`, pelo motivo declarado em
`OPP-20261023-MPRA`: as etapas foram empilhadas antes da captura.

## Rede de seguranca

| Momento | Resultado |
|---|---|
| linha de base HEAD 221b6c1 | 1615 passed, 9 skipped |
| working tree depois do lote | 1615 passed, 9 skipped |

Os testes que exercitam `_kits` passam por `projetar_analise`
(`tests/test_projecao_da_analise.py`, entre outros). Ver
[suite-antes.txt](before-after/suite-antes.txt) e
[suite-depois.txt](before-after/suite-depois.txt).
