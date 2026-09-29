---
schema_version: 1
id: OPP-20260929-H2YY
display_number: 7
context: busca-caminho
verb: simplify
title: generate_mermaid_graph_indirect_bridge com 205 linhas de montagem de string
target:
  files: [analisador-genealogico/reconstructed/path_search.py]
  symbol: generate_mermaid_graph_indirect_bridge
smell: função longa com aninhamento profundo, construindo a saída por acúmulo literal de linhas
roi:
  confidence: yellow
  impact: clareza e risco de alteração. É o trecho mais difícil de ler e o mais provável de mudança visual
  cost: medium
  est_return: mesma string gerada, com a estrutura do diagrama legível em nível de bloco
state: proposed
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/busca-caminho/design.md#interface, _reversa_sdd/migration/target_business_rules.md#br-migrar-024-conexão-indireta-por-afinidade-shortest_path-com-compressão-de-famílias]
---

## Antes observado

`generate_mermaid_graph_indirect_bridge` ocupa as linhas 247 a 451: **205 linhas**, 41% do módulo.
Dentro dela vivem quatro funções internas e uma sequência de montagem de string em quatro níveis de
aninhamento de subgrafo:

```text
subgraph COLUMNS
  subgraph ESQ[Ramo 1]
    subgraph ESQ_COLS
      subgraph ESQ_L[ ]
      subgraph ESQ_R[ ]
```

O bloco `COLUMNS > ESQ > ESQ_COLS > ESQ_L` é emitido por `lines.append` de literais consecutivos
(linhas 323 a 345), e o mesmo padrão se repete para `DIR` (linhas 382 a 402). Abrir e fechar subgrafo
depende de posição de `append("end")` no meio do fluxo, o que torna qualquer edição arriscada: um
`end` a mais ou a menos muda a árvore do diagrama sem erro de sintaxe.

Parte da complexidade é regra de negócio legítima e congelada por paridade: `split_path_by_marriage`,
o par de cônjuges no topo do ramo e as âncoras transparentes `--- |Casamento| ---` são comportamento
especificado. A oportunidade é de forma, não de regra.

## Transformação proposta

Substituir a emissão literal por helpers pequenos, mantendo a sequência de string idêntica:

1. `emit_subgraph(lines, name, body_lines)`, que escreve `subgraph`, `direction BT`, o corpo e `end` como
   uma unidade indivisível.
2. `emit_chain(lines, seq)`, para o que hoje são `add_node` mais as setas em sequência.
3. `emit_couple_node(lines, couple_id, label)`, para o par de cônjuges, que aparece duas vezes.
4. Manter `split_at` e `norm_ids` como estão, apenas renomeados se o time quiser.

Restrição dura: a lista final de linhas tem de ser **idêntica**, linha por linha. É isso que a
caracterização verifica.

## Rede de segurança exigida

- Caracterização obrigatória antes de tocar: capturar a string Mermaid de saída para cada fixture de
  `_reversa_sdd/parity/fixtures/gedcom/` (inclusive `affinity.ged`, que é o caso deste caminho) e
  comparar byte a byte depois.
- `tests/test_path_search.py` verde.
- Harness de paridade verde.

## Risco

Médio. O risco não é comportamental, é visual: o diagrama é o produto, e uma diferença de `end` ou de
ordem produz um diagrama diferente sem falhar teste nenhum que só verifique "não vazio". A
caracterização por fixture é o que fecha esse buraco.

## Observação

Esta é a transformação com **menor retorno de execução** da lista deste contexto, e a de maior custo de
leitura. É candidata natural a ficar por último, ou a não ser feita. Fica registrada porque o custo de
manutenção do trecho é real.
