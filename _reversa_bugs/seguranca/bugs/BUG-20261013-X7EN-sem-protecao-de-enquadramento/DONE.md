# BUG-20261013-X7EN encerrado

**Data:** 2026-10-13
**resolution_kind:** `fixed`
**Veredito de spec:** `spec-gap`, com adendo aditivo em `_reversa_sdd/addenda/bug-BUG-20261013-X7EN-v001.md`

Este bug está encerrado. Nenhum agente deve modificar esta pasta. Reabertura: remova este arquivo
conscientemente ou registre um bug novo com relação `regression-of` apontando para este.

## O que foi entregue

- `src/app.py` — `@app.after_request` que acrescenta `X-Frame-Options: DENY` a toda resposta.
- `tests/test_cabecalho_de_enquadramento.py` — 6 testes: 4 de reprodução (uma por rota) e 2 de regressão.
- `_reversa_sdd/addenda/bug-BUG-20261013-X7EN-v001.md` — o adendo aditivo, que também registra por que
  o `Content-Security-Policy` não entrou (é o `BUG-20261013-4PYJ`, adiado por decisão).

## Prova

- Testes do bug: **4 falhavam antes, 6 passam depois** (`fix/gate1-testes-falham.txt`,
  `fix/gate2-testes-passam.txt`).
- Suíte completa: **625 passam, 9 pulados, 0 falham** (`fix/gate2-suite.txt`).
- Paridade com o oráculo congelado: **100 %, zero divergência, exit 0** (`fix/gate2-paridade.txt`).
- `SHA_DA_TELA` de `tests/test_icone_de_atalho.py` continua válido: a correção é de cabeçalho e nenhum
  byte do HTML mudou.
- Evidências em `fix/` e `evidence/`.

## O que ficou fora, e é declarado

O par fica incompleto de propósito: a verificação de origem (`BUG-20261013-Z5BC`) e o
`Content-Security-Policy` (`BUG-20261013-4PYJ`) foram adiados nesta sessão.
