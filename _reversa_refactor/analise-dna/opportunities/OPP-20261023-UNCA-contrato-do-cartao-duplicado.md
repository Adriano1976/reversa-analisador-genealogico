---
schema_version: 1
id: OPP-20261023-UNCA
display_number: 50
context: analise-dna
verb: restructure
title: Contrato de 40 chaves do cartão escrito duas vezes, já com ordens diferentes
target:
  files:
    - src/core/passo_por_kit.py
    - src/core/cartao_sem_correspondencia.py
  symbol: _cartao_do_kit, _cartao_sem_correspondencia
smell: >
  Dois construtores produzem o mesmo dicionário de cartão. O do fluxo principal devolve
  40 chaves; o do match sem correspondência devolve 41, e a única diferença legítima é
  a marca `sem_correspondencia`. As duas listas já divergiram na ORDEM, e nenhum teste
  fixa o conjunto. Uma chave acrescentada só de um lado não gera erro: gera campo
  vazio na tela para um dos dois tipos de cartão.
roi:
  confidence: green
  impact: >
    Falha silenciosa no contrato que a tela inteira lê. A `OPP-20261023-CTAO` deixou os
    dois construtores em arquivos vizinhos, então a duplicação está visível mas
    continua sem guarda. O custo de acrescentar uma chave dobrou sem que nada avise.
  cost: low
  est_return: >
    O contrato declarado uma vez em `core/contrato_do_cartao.py`, com um teste de
    comportamento que compara o conjunto de chaves dos dois tipos de cartão.
state: applied
traceability:
  soul: [.reversa/soul.md#3-decisoes-fundadoras]
  specs:
    - _reversa_sdd/analise-dna/design.md
    - _reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md
---

## Antes observado

Medido por AST, nesta sessão, depois da `OPP-20261023-CTAO`:

```
cartao normal : 40 chaves
sem correspond: 41 chaves
so no normal  : []
so no sem_corr: ['sem_correspondencia']
mesma ordem?  : False
```

O cartão normal é o `return` de `_cartao_do_kit`, em `src/core/passo_por_kit.py`. O
especial é o `return` de `_cartao_sem_correspondencia`, em
`src/core/cartao_sem_correspondencia.py`.

Varredura de testes: nenhum fixa o conjunto de chaves do cartão. O único teste que
compara chaves é de `test_upload.py`, e é sobre os registros do GEDCOM.

## Por que não unificar os construtores

Unificar era a leitura óbvia e não é a certa: o cartão sem correspondência é uma
versão degenerada, com valores constantes em quase todo campo. Uma função única
precisaria de um modo, ou de uma base com sobreposição, e passaria a ter dois
caminhos internos em vez de um. O que está duplicado não são os valores: é a LISTA
de chaves.

## Transformação proposta

1. `src/core/contrato_do_cartao.py` (novo): a tupla canônica `CHAVES_DO_CARTAO`,
   com as 40 chaves, e a constante `CHAVE_SEM_CORRESPONDENCIA`.
2. `tests/test_contrato_do_cartao.py` (novo): produz um cartão de cada tipo com as
   fixtures que já existem e compara o conjunto de chaves com a tupla.

O teste é a parte que vale: declara a tupla sozinho não impede nada, mas o teste
transforma "esqueci a chave no outro construtor" em falha vermelha.

## Fronteira de comportamento

Nenhuma. A tupla é declaração de dado, e os dois construtores continuam montando os
dicionários como hoje, na ordem em que estão. O teste só lê.

## Rede de segurança

Suíte em **1625 passed, 9 skipped** (96,61 s) e o digest de equivalência
`b8d186c8…b570b5dd`, que continua válido porque nenhum valor muda.

---
*Gerado pelo Reversa-Refactor em 2026-10-23, como consequência da OPP-20261023-CTAO.*
