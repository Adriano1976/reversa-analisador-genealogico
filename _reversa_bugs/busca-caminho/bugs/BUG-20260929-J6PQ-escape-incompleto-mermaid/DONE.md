# Bug encerrado

> Bug: `BUG-20260929-J6PQ`
> Data de encerramento: 2026-09-29
> `resolution_kind`: `fixed`
> Closure policy: `local-software`, satisfeita

Este bug está encerrado. Nenhum agente deve modificar esta pasta.

Reabertura: remova este arquivo conscientemente, ou registre um bug novo com a relação
`regression-of` apontando para `BUG-20260929-J6PQ`.

## O que sustentou o encerramento

| Exigência da `closure_policy: local-software` | Situação |
|---|---|
| Testes de regressão passando | `py -3.14 -m pytest`: **95 passed** (`fix/gate2-testes-passam.txt`) |
| Veredito de spec registrado | `spec-gap`, com adendo aditivo `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md` |

`resolution_kind: fixed` exige, ainda, causa raiz `confirmed` e `regression_tests` não vazio. As duas
condições estão satisfeitas no front matter do `bug.md`.

## Mudanças aplicadas

| CHG | Tipo | Artefato |
|-----|------|----------|
| `CHG-001` | code | `analisador-genealogico/reconstructed/path_search.py` |
| `CHG-002` | specification | `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md` |

Reversão: `git checkout -- analisador-genealogico/reconstructed/path_search.py` e remoção do adendo.
