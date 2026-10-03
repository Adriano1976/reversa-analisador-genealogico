---
schema_version: 1
id: OPP-20261003-RGKA
display_number: 21
context: pacote-reconstructed
verb: modularize
title: a tabela de cM e a traducao para parentesco vivem dentro do fluxo de analise
target:
  files: [src/reconstructed/dna_analysis.py]
  symbol: SHARED_CM_DATA e get_relationships_by_cm
roi:
  confidence: green
  impact: coesao e auditabilidade. A tabela de faixas de cM e a funcao que a consulta sao um conhecimento de dominio isolado, preso dentro do modulo que orquestra o cruzamento. Separar permite exercita-la sozinha e cita-la como fonte. A alma do projeto registra como lacuna que **a tabela de cM nao cita fonte no codigo** (`.reversa/soul.md#lacunas`), e o principio V exige a citacao
  cost: low
  est_return: heuristica de cM isolada e auditavel, com a fonte citada que o principio V exige e a alma registra como pendencia
state: applied
traceability:
  soul:
    - .reversa/soul.md#decisoes-fundadoras
    - .reversa/soul.md#lacunas
  specs:
    - _reversa_sdd/domain.md#2.1
    - _reversa_sdd/analise-dna/requirements.md
    - .reversa/principles.md#V
---

## Antes observado

`dna_analysis.py` tem 136 linhas e concentra quatro coisas: a orquestracao do cruzamento, a tabela `SHARED_CM_DATA` com nove faixas, a funcao `get_relationships_by_cm` e o bloco de reexportacao da fachada.

A tabela e um conhecimento de dominio puro: nove faixas de cM com as relacoes provaveis de cada uma, com sobreposicao de ate quatro faixas. A funcao tem um contrato que ja foi corrigido uma vez contra a extracao anterior: o retorno e **sempre uma lista**, e `cM` menor ou igual a zero e valor nao numerico devolvem **lista vazia**, nao o literal de relacao distante.

O principio V do projeto exige que toda suposicao de genealogia genetica cite a fonte, com referencia e data de consulta. A tabela nao cita. A propria extracao registra isso como lacuna, e a alma tambem.

## Transformacao proposta

Extrair `core/cm_estimator.py` com `SHARED_CM_DATA` e `get_relationships_by_cm`, reexportados pela fachada `dna_analysis.py` para nao quebrar consumidores. Acrescentar, no modulo novo, o comentario de origem da tabela, com a referencia e a data de consulta.

**Nao e mudanca de comportamento.** O comentario nao afeta execucao, e a extracao nao altera nenhum valor de faixa nem o contrato de retorno. Se, no futuro, alguem quiser **recalibrar** as faixas, isso ja e mudanca de comportamento e sai deste verbo: vira feature.

**Cuidado na extracao.** Os testes que fixam o contrato estao em `tests/test_dna_analysis.py` (duas funcoes sobre relacoes por cM) e a caracterizacao de matching depende do valor de cM para o limiar de Jaccard. A extracao precisa manter os nomes publicos alcancaveis pelo mesmo caminho de antes.
