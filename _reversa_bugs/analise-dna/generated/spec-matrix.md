<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-04T13:48:48-03:00 a partir de 1 bugs -->

# Matriz BUG ↔ SPEC · analise-dna

> Derivada de `traceability.specs` de cada `bug.md`. Linhas por seção de spec efetiva.

| Seção de spec | open | active | resolved |
|---------------|------|--------|----------|
| `_reversa_sdd/analise-dna/design.md#interface` | | | `BUG-20261004-EWSJ` |
| `_reversa_sdd/analise-dna/requirements.md#agregação` | | | `BUG-20261004-EWSJ` |
| `_reversa_sdd/analise-dna/requirements.md#critérios-de-aceitação` | | | `BUG-20261004-EWSJ` |
| `_reversa_sdd/analise-dna/requirements.md#matching` | | | `BUG-20261004-EWSJ` |
| `_reversa_sdd/analise-dna/requirements.md#saída` | | | `BUG-20261004-EWSJ` |

## Lacuna de spec

| Bug | Label | O que não estava especificado | Situação |
|-----|-------|-------------------------------|----------|
| `BUG-20261004-EWSJ` | `spec-gap` | O formato do valor de cM **exibido**: número de casas decimais e separador decimal | **Fechada** pelo adendo `_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md`, veredito `spec-gap` aprovado pelo usuário em 2026-10-04 |

O bug cita cinco seções da extração e nenhuma delas define o formato. As quatro seções de
`requirements.md` definem o **valor** (soma dos segmentos, ordenação decrescente, o cM como influência
no limiar de similaridade) e os critérios de aceitação da tela; nenhuma trata de apresentação numérica.
A seção de `design.md` define o contrato de retorno do fluxo, que entrega o `float` cru.

## Adendos de bug vigentes neste contexto

| Adendo | Bug | O que especifica |
|--------|-----|------------------|
| `_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md` | `BUG-20261004-EWSJ` | Especifica pela primeira vez o formato exibido do total de cM: até duas casas, vírgula decimal, sem zeros à direita e sem separador de milhar, com o valor armazenado mantido exato |
