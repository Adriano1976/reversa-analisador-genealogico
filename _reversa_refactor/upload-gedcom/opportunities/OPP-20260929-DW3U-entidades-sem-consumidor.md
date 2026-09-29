---
schema_version: 1
id: OPP-20260929-DW3U
display_number: 14
context: upload-gedcom
verb: prune
title: Entidades de domain.py sem consumidor e propriedade g quebrada
target:
  files: [analisador-genealogico/reconstructed/domain.py, tests/test_domain.py]
  symbol: Family, GenealogyGraph, DNAGroup, GenealogyGraph.g
smell: entidades mantidas apenas pelos próprios testes, com uma propriedade que nunca poderia funcionar
roi:
  confidence: green
  impact: superfície de leitura e uma pista falsa, na forma de uma propriedade quebrada
  cost: low
  est_return: menos código sem consumidor, ao custo de decisão sobre a linha de base de testes
state: proposed
traceability:
  soul: [.reversa/soul.md#entidades-centrais]
  specs: [_reversa_sdd/architecture.md#3-erd-resumido, _reversa_sdd/reconstruction-plan.md#tarefa-01-entidades-de-domínio]
---

## Contexto: o que a B5F2 resolveu e o que ela deixou

A `OPP-20260929-B5F2`, opção B, promoveu `domain.py` a autoridade da limpeza de nome. Isso deu ao
módulo um consumidor de produção legítimo, `dna_analysis`, e encerrou a duplicação de `strip_bad_utf`
e `demojibake`.

O que a promoção **não** resolveu foram as entidades. Depois dela, `domain.py` tem duas metades com
situações opostas:

| Parte | Consumidor |
|-------|-----------|
| `strip_bad_utf`, `demojibake` | `dna_analysis`, caminho de produção |
| `Family`, `GenealogyGraph`, `DNAGroup` | apenas `tests/test_domain.py` |

## Antes observado

Nenhum módulo de produção instancia qualquer das três entidades. `upload.py` usa `ged4py` e
`networkx` diretamente, com dicionários e um `nx.Graph`, sem passar por `GenealogyGraph`.

Dentro das entidades, um achado concreto:

```python
    @property
    def g(self):
        """Retorna o grafo (lazy) — definido na Tarefa 02."""
        return self.conexoes
```

`self.conexoes` **nunca é definido** em nenhum ponto da classe, e não existe nenhuma atribuição a
esse nome no módulo. A propriedade é um `AttributeError` garantido para quem a chamar. Nenhum teste a
chama, e nenhum código a usa. Ela é a pista falsa que este registro reporta.

## Transformação proposta

Três saídas, e a escolha é humana porque as três mexem em algo diferente:

| Opção | O que faz | Custo |
|-------|-----------|-------|
| **A** | Remove as três entidades e a propriedade `g`, junto com os testes correspondentes de `tests/test_domain.py` | A suíte cai. Precisa de decisão explícita, como na opção A da B5F2 |
| **B** | Remove apenas a propriedade `g`, que é defeito puro, e mantém as entidades | Menor, e não mexe em teste nenhum: nenhum teste cobre `g` |
| **C** | Dá consumidor às entidades, fazendo `upload.py` usá-las | É reescrita de `upload.py`, logo é feature, não refactor |

A recomendação é a **B** como passo imediato, porque corrige um defeito real sem custo de decisão, e
deixar a **A** como decisão separada.

## Rede de segurança exigida

- Opção B: `prune` com `preservation.method: death-proof`. A prova é a varredura que mostra zero
  chamadas de `.g` em código e em testes.
- Opção A: prova de morte para as três entidades mais decisão humana sobre a linha de base.

## Risco

Baixo na opção B. Na opção A, o risco é de processo: as entidades foram entregues pela Tarefa 01 da
reconstrução e estão citadas em `reconstruction-report.md`, então removê-las desvia de um registro de
entrega, do mesmo modo que a remoção do `given_index` desviou do critério da T-07.
