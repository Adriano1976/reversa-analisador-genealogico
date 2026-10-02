# Bug encerrado

> Bug: `BUG-20261002-T4ZM`
> Data de encerramento: 2026-10-02
> `resolution_kind`: `fixed`
> Closure policy: `local-software`, satisfeita

Este bug está encerrado. Nenhum agente deve modificar esta pasta.

Reabertura: remova este arquivo conscientemente, ou registre um bug novo com a relação
`regression-of` apontando para `BUG-20261002-T4ZM`.

## O que sustentou o encerramento

| Exigência da `closure_policy: local-software` | Situação |
|---|---|
| Testes de regressão passando | `py -3.14 -m pytest`: **101 passed** (`fix/gate2-testes-passam.txt`) |
| Veredito de spec registrado | `spec-gap`, com adendo aditivo `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v002.md` |

`resolution_kind: fixed` exige, ainda, causa raiz `confirmed` e `regression_tests` não vazio. As duas
condições estão satisfeitas no front matter do `bug.md`.

## Mudanças aplicadas

| CHG | Tipo | Artefato |
|-----|------|----------|
| `CHG-001` | code | `analisador-genealogico/reconstructed/mermaid_render.py` |
| `CHG-002` | specification | `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v002.md` |

## Ressalva declarada

Um critério de aceite ficou **não verificado**: a renderização em navegador para nome contendo os
caracteres preservados. A prova disponível é a da gramática do Mermaid e a paridade com o legado. A
closure policy não exige esse critério, e ele fica registrado como pendência de verificação, não como
cumprido.

## Reversão

`git apply --reverse` de `fix/CHG-001.diff` sobre `mermaid_render.py`, e remoção do adendo v002.
Nunca usar `git checkout` nesse arquivo enquanto o `H2YY` não estiver commitado.
