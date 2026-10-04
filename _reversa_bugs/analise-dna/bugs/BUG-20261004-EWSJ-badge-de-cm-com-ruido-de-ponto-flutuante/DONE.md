# BUG-20261004-EWSJ encerrado

**Data:** 2026-10-04
**resolution_kind:** `fixed`
**Veredito de spec:** `spec-gap`, com adendo em `_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md`

Este bug está encerrado. Nenhum agente deve modificar esta pasta. Reabertura: remova este arquivo
conscientemente ou registre um bug novo com relação `regression-of` apontando para este.

## O que foi entregue

- `src/utils/number_format.py`, módulo novo com `formatar_cm`, a autoridade única do formato do total
  de cM exibido.
- `src/app.py`, com o filtro Jinja `cm_br` registrado.
- `src/templates/index.html`, linha 121 passando a usar o filtro.
- `tests/test_formatacao_cm.py`, 6 testes.
- `_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md`, o adendo versionado.

## Prova

- Testes do bug: **5 falhavam antes, 6 passam depois**. O sexto é guarda de contrato do valor
  armazenado, e já passava antes por definição.
- Suíte completa: **131 aprovados e 15 erros de ambiente**, contra a base de 125 aprovados e os mesmos
  15 erros. O crescimento é exatamente os 6 testes novos.
- Paridade com o oráculo congelado: **100 por cento, zero divergência** nas 6 fixtures.
- Evidências em `fix/` e `evidence/`.
