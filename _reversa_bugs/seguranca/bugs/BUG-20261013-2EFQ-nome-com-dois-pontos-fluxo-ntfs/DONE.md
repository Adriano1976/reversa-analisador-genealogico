# BUG-20261013-2EFQ encerrado

**Data:** 2026-10-13
**resolution_kind:** `fixed`
**Veredito de spec:** `spec-desatualizada`, com adendo versionado em `_reversa_sdd/addenda/bug-BUG-20261013-2EFQ-v001.md`

Este bug está encerrado. Nenhum agente deve modificar esta pasta. Reabertura: remova este arquivo
conscientemente ou registre um bug novo com relação `regression-of` apontando para este.

## O que foi entregue

- `src/utils/validate.py` — `_CARACTERES_SUBSTITUIDOS` (o conjunto da **escrita**) passa a incluir `:`;
  `_SEPARADORES` (o conjunto que responde "isto é um caminho?" na **leitura**) fica intacto, para não
  apertar o alcance de arquivos já gravados.
- `tests/test_nome_com_dois_pontos.py` — 14 testes: 4 de reprodução que **tocam o disco** e 10 de
  regressão (nomes reservados do Windows, acento e espaço preservados, escape de pasta, resolução).
- `_reversa_sdd/addenda/bug-BUG-20261013-2EFQ-v001.md` — o adendo versionado, que emenda a enumeração
  de caracteres saneados em `upload-gedcom/contracts.md#2.1`, `RF-06`, `BR-U-10` e `design.md`.

## Prova

- Testes do bug: **4 falhavam antes, 14 passam depois** (`fix/gate1-testes-falham.txt`,
  `fix/gate2-testes-passam.txt`).
- Suíte completa: **625 passam, 9 pulados, 0 falham** (`fix/gate2-suite.txt`).
- Paridade com o oráculo congelado: **100 %, zero divergência, exit 0** (`fix/gate2-paridade.txt`).
- **Nenhum reparo de dados foi necessário**: medido, nenhum arquivo do operador tem `:` — nem na pasta,
  nem nos aposentados.
- Evidências em `fix/` e `evidence/`.

## O que este encerramento NÃO cobre

- A varredura da pasta real do operador (nenhum `:` foi encontrado, mas a pasta não é varrida pelo
  runtime).
- Outros caracteres inválidos do Windows sem medição que os justifique: não entraram.
- Nomes reservados de dispositivo: **medidos como inofensivos** pelo prefixo de chave, e presos por
  teste de regressão.
