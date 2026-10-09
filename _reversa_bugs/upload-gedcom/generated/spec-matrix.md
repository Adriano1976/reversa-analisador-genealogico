<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-09T15:30:33-03:00 a partir de 2 bugs -->

# Matriz BUG x SPEC · upload-gedcom

1 dos 2 bug(s) deste contexto tem `visibility: restricted`: os locators de spec dele não são projetados
nas views, e a linha aparece agrupada. Consulte a seção `## Traceability` de cada `bug.md`.

| Seção de spec | open | active | resolved |
|---------------|------|--------|----------|
| `_reversa_sdd/upload-gedcom/contracts.md#2.1` | 1 | 0 | 0 |
| `_reversa_sdd/domain.md#3.5` | 1 | 0 | 0 |
| (omitida por política de visibilidade) | 0 | 0 | 1 |

## Lacuna de spec

**Nenhum bug deste contexto é `spec-gap`.** O `BUG-20261009-6RKP` **não** é lacuna: a spec cobre o
assunto, e o problema é que ela **se contradiz**. `contracts.md:51` manda preservar acentos e espaços no
nome visível, e `contracts.md:53` manda validar, em toda leitura, uma forma fechada que não admite nem um
nem outro. O veredito tende a `spec-desatualizada`, com decisão humana e adendo, e não a `spec-gap`.

O bug restrito deste contexto tem veredito `spec-desatualizada`, com adendo em
`_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md`.

## Adendos de bug vigentes neste contexto

| Adendo | Bug | O que especifica |
|--------|-----|------------------|
| `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md` | `BUG-20260929-QMLY` | Correção da spec efetiva, com delta sobre seção existente |
