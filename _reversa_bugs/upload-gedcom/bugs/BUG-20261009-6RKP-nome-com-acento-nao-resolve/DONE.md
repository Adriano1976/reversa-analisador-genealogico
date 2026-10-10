# BUG-20261009-6RKP encerrado

**Data:** 2026-10-10
**resolution_kind:** `fixed`
**Veredito de spec:** `spec-correta` — a spec estava CERTA e o CÓDIGO divergia dela. Decisão do
operador registrada no bloco `approval` e declarada como `RN-20` em
`_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md`.

Este bug está encerrado. Nenhum agente deve modificar esta pasta. Reabertura: remova este arquivo
conscientemente ou registre um bug novo com relação `regression-of` apontando para este.

## O que foi entregue

- `src/utils/validate.py` — `chave_recebida_e_valida` deixa de exigir um alfabeto fechado e passa a
  exigir que a referência seja um NOME. Acento e espaço, que o gravador sempre preservou (`RF-06`),
  passam a ser aceitos; `/`, `\`, NUL e `..` continuam recusados (`CHG-001`).
- `src/app.py` — o **segundo defeito** desta pasta, que o registro deixou em aberto: guarda em volta
  do parse do GEDCOM, traceback para o log e mensagens de erro sem a chave de conteúdo (`CHG-003`,
  tratado como `T042` da feature 011).
- `tests/test_forma_da_referencia.py` — 32 testes (`CHG-002`).
- `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` — a `RN-20`, regra declarada.

## Prova

- **Sonda contra a pasta real, depois do conserto:** 13 de 13 arquivos aceitos pela forma, 0
  recusados. Antes, 7 de 19 eram recusados e a tela dizia "não existe mais" sobre eles.
- **Suíte completa:** 517 passam, 9 pulados, zero falhas.
- **Conserto reproduzido pela rota:** `POST` com `gedcom_filename` apontando para um `.csv` devolvia
  `500` com traceback; agora devolve `200` com mensagem.
- Evidências em `evidence/`; o manifesto da mitigação anterior em `fix/manifesto-renomeacao.md`.

## Nota sobre a mitigação, que continua valendo

A mitigação de 2026-10-09 renomeou 4 arquivos com chave para tirar acento e espaço do nome visível, e
é **reversível** (`fix/manifesto-renomeacao.md`). **Este conserto não a desfaz:** os nomes ASCII
permanecem, e nada é renomeado de volta. O conserto cuida do que entra a partir de agora.

Por consequência, o alcance do `D-11` mudou de tamanho: o **único** caso de item indisponível que
resta é o arquivo **sem chave**. A marca amarela da lista ficou sem objeto para acento e espaço.
