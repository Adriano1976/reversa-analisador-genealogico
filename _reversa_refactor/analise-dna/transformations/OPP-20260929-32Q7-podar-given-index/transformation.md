---
schema_version: 1
id: OPP-20260929-32Q7
verb: prune
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: death-proof
  evidence:
    - before-after/death-proof.txt
    - safety-net/equivalence-after-apply.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: Remove o indice given_index, que nenhum ponto do codigo le
    diff: CHG-001.diff
  - chg: CHG-002
    kind: documentation
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: Remove do docstring a afirmacao de que HARD_MIN e GIVEN_MIN existem, quando nenhum dos dois e declarado
    diff: CHG-002.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff]
---

## O que foi feito

Escopo corrigido durante a execucao: dos tres candidatos, apenas `given_index` existia
para podar. `HARD_MIN` e `GIVEN_MIN` **nao existem no codigo**, so no docstring que afirmava
existirem, herdado do legado. O alvo passou de 3 para 1 mais uma correcao de documentacao.

Prova de morte: 3 ocorrencias de `given_index`, todas escritas, e o unico leitor e o descarte `_` no
chamador unico. Sem entrada dinamica: a varredura por `getattr`, `globals()`, `eval`, `exec`,
`importlib` e companhia so encontra o `getattr(val, "xref_id", val)` do ged4py em `upload.py:30`.

Ressalva de spec registrada e mantida: `_reversa_sdd/analise-dna/tasks.md` T-07 lista
`given_index` populado como criterio de pronto. O desvio precisa de adendo de spec, decisao do
usuario, e nao foi aplicado nesta rodada.

Patch empilhado sobre a AU76, porque as duas tocam `build_ged_indexes`. Equivalencia contra a linha
de base: 2.206 comparacoes, 0 divergencias. Suite verde.

## Estado dos arquivos

`424` linhas antes, `421` depois.
