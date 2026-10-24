---
schema_version: 1
id: OPP-20261023-UNCA
verb: restructure
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - ../../../tests/test_contrato_do_cartao.py
    - ../OPP-20261023-ORQA-fluxo-de-553-linhas-sem-fronteira/safety-net/equivalencia.py
measurement:
  before: >
    duas listas de chaves, 40 e 41, escritas em arquivos diferentes, já divergentes na
    ordem e sem nenhum teste que fixasse o conjunto
  after: >
    uma tupla canônica de 40 chaves em `core/contrato_do_cartao.py` e dois testes que
    comparam o conjunto produzido por cada construtor
change_set:
  - chg: CHG-001
    file: src/core/contrato_do_cartao.py
    purpose: declara `CHAVES_DO_CARTAO` e `CHAVE_SEM_CORRESPONDENCIA`
  - chg: CHG-001
    file: tests/test_contrato_do_cartao.py
    purpose: >
      produz um cartão de cada tipo pelas fixtures e compara o conjunto com a tupla
approval:
  by: user
  at: 2026-10-23T15:30:30-03:00
  plan_at: 2026-10-23T15:20:25-03:00
reversible_via: [CHG-001-contrato-e-guarda.diff]
---

## O que foi feito

Duas adições, nenhuma edição.

| Arquivo | Linhas | O que é |
|---|---|---|
| `src/core/contrato_do_cartao.py` | 67 | `CHAVES_DO_CARTAO`, tupla com as 40 chaves na ordem canônica, e `CHAVE_SEM_CORRESPONDENCIA` |
| `tests/test_contrato_do_cartao.py` | 77 | dois testes, um por tipo de cartão |

## O que a guarda prende

Cada teste produz um cartão de um tipo e compara o conjunto de chaves:

- cartão normal: exatamente `set(CHAVES_DO_CARTAO)`;
- cartão sem correspondência: `set(CHAVES_DO_CARTAO) | {CHAVE_SEM_CORRESPONDENCIA}`.

Antes, as duas listas já tinham divergido na **ordem** e nada avisava. Como o template lê
por nome, uma chave criada em um construtor e esquecida no outro virava campo vazio na
tela para metade dos cartões.

## Por que não unificar os construtores

Era a leitura óbvia e é a errada: o cartão sem correspondência é uma versão degenerada,
com valor constante em quase todo campo. Unificar exigiria um modo ou uma base com
sobreposição, trocando duplicação de dado por duplicação de fluxo. O que estava
duplicado não eram os valores: era a lista de chaves.

## Escolha declarada

A tupla tem o teste como único consumidor. Não é código morto pela regra do registro,
porque tem referência estática, mas também não é usada pelos construtores: o valor dela
é congelar a lista em um lugar só e fazer a comparação existir. Ligar os construtores a
ela exigiria reescrever os dois dicionários, que é a unificação recusada acima.

## Prova

| Verificação | Resultado |
|---|---|
| asserções contra o código anterior | as duas verdadeiras, provadas antes de aplicar |
| teste novo | **2 passed** em 2,00 s |
| suíte antes | **1625 passed, 9 skipped** em 96,61 s |
| suíte depois | **1627 passed, 9 skipped** em 116,88 s |
| digest de equivalência | `b8d186c8…b570b5dd`, idêntico |

As duas provas que importam: o teste nasce verde (não está acomodado ao resultado) e o
digest não se move (nenhum valor do cartão mudou).

## Reversão

`git apply -R CHG-001-contrato-e-guarda.diff`, que remove os dois arquivos novos.

---
*Aplicado em 2026-10-23 pelo Reversa-Refactor, sob gate de plano e de diff aprovados pelo usuário.*
