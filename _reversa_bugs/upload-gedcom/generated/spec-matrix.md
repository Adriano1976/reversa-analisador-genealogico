<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-10T03:28:36-03:00 a partir de 2 bugs -->

# Matriz BUG x SPEC · upload-gedcom

1 dos 2 bug(s) deste contexto tem `visibility: restricted`: os locators de spec dele não são projetados
nas views, e a linha aparece agrupada. Consulte a seção `## Traceability` de cada `bug.md`.

| Seção de spec | open | active | resolved |
|---------------|------|--------|----------|
| `_reversa_sdd/upload-gedcom/contracts.md#2.1` | 0 | 0 | 1 |
| `_reversa_sdd/domain.md#3.5` | 0 | 0 | 1 |
| (omitida por política de visibilidade) | 0 | 0 | 1 |

## Lacuna de spec

**Nenhum bug deste contexto é `spec-gap`.** O `BUG-20261009-6RKP` **não** é lacuna: a spec cobre o
assunto, e o problema era que ela **se contradizia**. `contracts.md:51` manda preservar acentos e espaços
no nome visível, e `contracts.md:53` manda validar, em toda leitura, uma forma fechada que não admite nem
um nem outro.

O veredito **decidido** em 2026-10-10 é `spec-correta`: a spec estava certa, e quem divergia era o
código — o resolvedor recusava o que o gravador produz por exigência da própria spec. Não é `spec-gap` (a
spec cobre o assunto) nem `spec-desatualizada` (ela não ficou velha).

O bug restrito deste contexto tem veredito `spec-desatualizada`, com adendo em
`_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md`. Os dois vereditos do contexto são diferentes, e a
distinção importa: lá a spec ficou velha; aqui ela estava certa.

## Adendos de bug vigentes neste contexto

| Adendo | Bug | O que especifica |
|--------|-----|------------------|
| `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md` | `BUG-20260929-QMLY` | Correção da spec efetiva, com delta sobre seção existente |
| `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` | `BUG-20261009-6RKP` | Declara a `RN-20`: a referência passa a exigir um NOME, e não um alfabeto fechado |
