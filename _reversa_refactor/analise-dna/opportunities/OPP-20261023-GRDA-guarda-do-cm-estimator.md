---
schema_version: 1
id: OPP-20261023-GRDA
display_number: 51
context: analise-dna
verb: standardize
title: A defesa do ADR-19 é textual, e nada impede um import novo de cm_estimator
target:
  files: [src/core/cm_estimator.py, tests/]
  symbol: guarda de importação por AST
smell: >
  O ADR-19 declara `core.cm_estimator` fora do fluxo e proíbe o uso em código novo. O
  módulo repete o aviso no próprio docstring. Nada disso é verificado: um `from
  core.cm_estimator import ...` acrescentado em qualquer módulo de `src/` passa na
  suíte sem que ninguém saiba, e o projeto passaria a ter duas autoridades sobre cM, a
  tabela escrita à mão e a do Shared cM Project 4.0 que `relationship_hypotheses` usa.
roi:
  confidence: green
  impact: >
    A `OPP-20261008-JXQN` queria remover o módulo, e o bloqueio é de política e de spec:
    a remoção aposenta uma dimensão da matriz de paridade e exige decisão sobre RF-25 e
    BR-D-62. Esta oportunidade recupera a metade que o refactor pode entregar sozinho,
    que é a defesa ESTRUTURAL contra uso novo, sem tocar em instrumento congelado nem
    em artefato de spec.
  cost: low
  est_return: >
    Um teste de guarda que falha se qualquer módulo de `src/` importar
    `core.cm_estimator`, com prova negativa de que a guarda acusa quando o import
    aparece. A regra do ADR-19 deixa de depender de alguém ler o docstring.
state: applied
traceability:
  soul: [.reversa/soul.md#3-decisoes-fundadoras]
  specs:
    - _reversa_sdd/adrs/19-heuristicas-declaradas-como-heuristicas.md
    - _reversa_sdd/analise-dna/requirements.md
---

## Antes observado

Medido nesta sessão, depois de a auditoria de `dna_analysis.py` fechar:

| Verificação | Resultado |
|---|---|
| módulos de `src/` que importam `core.cm_estimator` | **0** |
| consumidores do módulo | `tests/test_dna_analysis.py` e o coletor que o `harness.py` escreve e executa por string |
| defesa contra uso novo | **nenhuma**. Só o aviso no docstring e o texto do ADR-19 |

O único vestígio em `src/` é a menção em prosa no docstring de `core/dna_analysis.py`,
que explica por que a reexportação saiu em `T022`.

## Transformação proposta

`tests/test_uso_do_cm_estimator.py` (novo, cerca de 40 linhas):

1. varre todos os `.py` de `src/` por AST;
2. reprova `from core.cm_estimator import ...`, `import core.cm_estimator` e
   `from core import cm_estimator`, em qualquer arquivo que não seja o próprio módulo;
3. **prova negativa**: monta um fragmento de código com o import proibido e confirma
   que a mesma varredura o acusa. Sem isso, um teste que só passa não prova nada.

É o mesmo idioma de `tests/test_dependencias_nucleo.py`, que já guarda a pureza do
núcleo por AST, com prova negativa.

## Fronteira de comportamento

Nenhuma. Arquivo novo em `tests/`, nenhum módulo de produção editado, nenhum
comportamento alterado. A suíte ganha um teste e nada mais.

## Por que não é a `JXQN`

A `JXQN` remove o módulo e, com ele, uma dimensão da paridade, e exige decisão de spec.
Esta preserva o módulo e impede uso novo. São complementares: se a `JXQN` for reaberta
um dia, esta guarda deixa de ter alvo e é declinada junto.

## Rede de segurança

Suíte em **1627 passed, 9 skipped** (116,88 s) e o digest de equivalência
`b8d186c8…b570b5dd`, que não é afetado porque nada de produção muda.

## Resultado da aplicação

Aplicada em 2026-10-23, com um arquivo novo de 91 linhas em `tests/` e nenhum módulo de
produção tocado. A guarda passa hoje, com zero culpados, e a prova negativa acusa as
cinco formas de import e absolve comentário e import alheio.

A implementação cobriu **cinco** formas em vez das três do plano: `src/core/` usa
import relativo, e `from . import cm_estimator` é a porta que o próprio pacote tem.

Suíte: **1627 passed, 9 skipped** antes (116,88 s) e **1629 passed, 9 skipped** depois
(117,52 s). O digest não é afetado, porque nada de produção mudou.

---
*Gerado pelo Reversa-Refactor em 2026-10-23, no lugar do cenário A da OPP-20261008-JXQN. Aplicada no mesmo dia.*
