---
schema_version: 1
id: OPP-20261024-SUPR
verb: standardize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
    - CHG-001.diff
measurement:
  before: >
    `__all__` com 18 nomes, dos quais 4 sem nenhum importador em todo o repositorio:
    `hop_evidence`, `find_all_common_ancestors`, `ROMANO` e `MAX_DEPTH`. O comentario acima da
    lista afirmava que as reexportacoes existiam "para quem ja os importava", o que e verdade
    para `nome_do_grau` e falso para `ROMANO`.
  after: >
    `__all__` com 14 nomes, cada um com importador verificado, e o comentario reescrito para
    dizer o que a medicao sustenta. Nenhum import, funcao ou constante mudou.
change_set:
  - chg: CHG-001
    file: src/core/documentary_relationship.py
    purpose: >
      quatro nomes saem de `__all__` e o comentario da reexportacao passa a citar apenas
      `nome_do_grau`; os quatro continuam no modulo e importaveis por nome
approval:
  by: user
  at: 2026-10-24T02:34:00-03:00
reversible_via: [CHG-001.diff]
---

## A medicao

Varredura por AST em `src/`, `tests/`, `_reversa_bugs/`, `_reversa_sdd/` e
`_reversa_forward/`, refeita depois da `OPP-20261024-SEPM` porque a divisao mudou de onde cada
nome mora:

| Nome em `__all__` | Importadores |
|---|---|
| `documentary_relationship` | 10 |
| `homonym_dossier` | 17 |
| `birth_date` | 15 |
| `parse_year` | 13 |
| `person_summary` | 4 |
| `documentary_label` | 4 |
| `intervalo_de_geracao_mediano` | 3 |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | 2 cada |
| `documental_nao_encontrado` | 1 |
| `normalizar` | 1 |
| `nome_do_grau` | 2 testes |
| `death_date` | 1, sonda congelada em `_reversa_bugs/` |
| `get_children` | 1, sonda congelada em `_reversa_bugs/` |
| `hop_evidence` | **0** |
| `find_all_common_ancestors` | **0** |
| `ROMANO` | **0** |
| `MAX_DEPTH` | **0** |

## O que mudou

De 18 para 14 nomes anunciados, e o comentario da reexportacao reescrito.

## O que nao mudou, e por que

Nenhum import foi tocado. Os quatro nomes continuam no modulo e continuam importaveis por
nome: `from core.documentary_relationship import ROMANO` funciona exatamente como antes. O que
mudou e so o anuncio.

A leitura agressiva, apagar o import de `ROMANO`, foi descartada: `__all__` e anuncio, a
importacao e comportamento, e remover o import quebraria qualquer consumidor fora do
repositorio sem ganho correspondente. O custo do import sem uso e uma linha, e o comentario
explica por que ela fica.

`death_date` e `get_children` tambem ficam: os dois tem consumidor real, ainda que congelado em
`_reversa_bugs/_sondas-matching/pista_documental_da_margarida.py`, que a config nao libera. A
`OPP-20261023-DOCF` ja registrou o preco de tratar consumidor congelado como ausente.

## Prova

| Verificacao | Resultado |
|---|---|
| Nomes anunciados | 18 para 14 |
| Os quatro retirados continuam importaveis | sim |
| `import *` no repositorio | zero, verificado: mexer em `__all__` nao altera importacao existente |
| Suite completa antes | 1635 passed, 9 skipped |
| Suite completa depois | **1635 passed, 9 skipped** |
| `git apply --check --reverse` | passa: aplicado byte a byte |

## Divida de documentacao que esta transformacao nao fecha

| Artefato | Afirmacao | Situacao |
|---|---|---|
| `_reversa_sdd/busca-caminho/design.md:41` | lista `hop_evidence` como superficie publica do modulo | continua importavel daqui, mas nao e mais anunciado |
| `_reversa_sdd/busca-caminho/requirements.md:281` | lista `hop_evidence` e `find_all_common_ancestors` entre as funcoes do modulo | idem |

Os dois caminhos estao em `_reversa_sdd/**`, fora dos globs liberados.
