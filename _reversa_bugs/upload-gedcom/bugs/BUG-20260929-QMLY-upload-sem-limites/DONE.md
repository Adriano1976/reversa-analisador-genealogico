# BUG-20260929-QMLY encerrado

**Data:** 2026-10-02
**resolution_kind:** `fixed`
**Veredito de spec:** `spec-desatualizada`, com adendo em `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md`

Este bug está encerrado. Nenhum agente deve modificar esta pasta. Reabertura: remova este arquivo
conscientemente ou registre um bug novo com relação `regression-of` apontando para este.

## O que foi entregue

- `analisador-genealogico/reconstructed/validate.py`, módulo novo de validação do upload.
- `analisador-genealogico/app.py`, com teto de tamanho, chave de armazenamento gerada pelo servidor e
  validação antes da gravação.
- `tests/test_upload_seguranca.py`, 27 testes.
- `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md`, o adendo versionado.

## Prova

- Testes do bug: 9 falhavam antes, 27 passam depois.
- Suíte completa: 128 passam.
- Paridade com o oráculo congelado: 100%, zero divergência.
- Evidências em `fix/` e `evidence/`.
