---
schema_version: 1
id: OPP-20261023-GRDA
verb: standardize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - ../../../tests/test_uso_do_cm_estimator.py
measurement:
  before: >
    nenhuma defesa estrutural contra uso novo de `core.cm_estimator`; só o aviso no
    docstring do módulo e o texto do ADR-19
  after: >
    uma guarda por AST sobre todo `src/`, com prova negativa das cinco formas de import
change_set:
  - chg: CHG-001
    file: tests/test_uso_do_cm_estimator.py
    purpose: >
      reprova qualquer import de `core.cm_estimator` em `src/` e prova que a varredura
      acusa as formas absolutas e relativas, ignorando comentário
approval:
  by: user
  at: 2026-10-23T15:41:06-03:00
  plan_at: 2026-10-23T15:35:00-03:00
reversible_via: [CHG-001-guarda-do-cm-estimator.diff]
---

## O que foi feito

Um arquivo novo, 91 linhas, nenhum módulo de produção tocado.

O `ADR-19` declara `core.cm_estimator` fora do fluxo e proíbe o uso em código novo, mas
a defesa era textual. A `OPP-20261008-JXQN` queria remover o módulo e foi declinada:
a remoção aposenta uma dimensão da matriz de paridade e exige decisão sobre
`RF-25`/`BR-D-62`. Esta guarda entrega a metade que cabe no refactor.

## As duas funções

| Função | O que faz |
|---|---|
| `test_nenhum_modulo_de_producao_importa_cm_estimator` | varre `src/**/*.py` por AST e reprova qualquer import de `core.cm_estimator`, isentando o próprio módulo |
| `test_a_varredura_acusa_import_proibido_e_ignora_comentario` | prova negativa das cinco formas de import, mais duas absolvições |

## Cobertura além do plano

O plano falava em três formas absolutas. A implementação cobre cinco, porque `src/core/`
usa import relativo, e `from . import cm_estimator` é justamente a forma que um módulo
vizinho usaria. Guardar só as absolutas deixaria aberta a porta que o próprio pacote
tem.

## Prova

| Verificação | Resultado |
|---|---|
| guarda contra a árvore atual | passa, zero culpados |
| prova negativa | 5 acusações e 2 absolvições, todas corretas |
| teste novo, sozinho | **2 passed** em 0,66 s |
| suíte antes | **1627 passed, 9 skipped** em 116,88 s |
| suíte depois | **1629 passed, 9 skipped** em 117,52 s |
| digest de equivalência | não afetado: nada de produção mudou |

## O que a guarda não faz

Não impede o uso do módulo pelos instrumentos de verificação, que é o que o mantém
vivo. Ela olha apenas `src/`. No dia em que a `JXQN` for reaberta e o módulo sair, esta
guarda perde o alvo e é declinada junto.

## Reversão

`git apply -R CHG-001-guarda-do-cm-estimator.diff`, que remove o arquivo novo.

---
*Aplicado em 2026-10-23 pelo Reversa-Refactor, sob gate de plano e de diff aprovados pelo usuário.*
