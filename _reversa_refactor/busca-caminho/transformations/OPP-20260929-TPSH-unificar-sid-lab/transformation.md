---
schema_version: 1
id: OPP-20260929-TPSH
verb: restructure
state: applied
safety_net:
  kind: characterization
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - safety-net/characterize-after-apply.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/path_search.py
    purpose: Extrai _mermaid_sid e _mermaid_label para o modulo e remove as duas copias internas de cada, com alias local para nao tocar nos 45 pontos de chamada
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff]
---

## O que foi feito

As quatro definicoes internas viraram duas funcoes de modulo. As duas copias de `lab`
eram equivalentes; as duas de `sid` divergiam num ramo `isinstance` que nunca dispara, porque todos
os pontos de chamada passam `str`. Unificar adotou a versao tolerante e removeu o ramo morto.

Prova: caracterizacao da saida Mermaid (4 casos, 40 linhas) identica ao golden gravado antes da
mudanca, e suite completa verde. O diff tem 3 hunks e nao altera nenhum ponto de chamada, porque
`sid` e `lab` continuam existindo como nomes locais ligados as funcoes de modulo.

Ganho colateral: o `BUG-20260929-J6PQ` (escape incompleto no rotulo Mermaid) passa a ter um unico
ponto de correcao.

## Estado dos arquivos

`501` linhas antes, `494` depois.
