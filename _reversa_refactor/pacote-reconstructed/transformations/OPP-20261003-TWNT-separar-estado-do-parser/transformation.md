---
schema_version: 1
id: OPP-20261003-TWNT
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/suite-depois.txt
    - safety-net/paridade-depois.txt
measurement:
  before: upload.py com 113 linhas e 3 responsabilidades (registro de estado, leitura de GEDCOM, construcao do grafo); 6 modulos internos importando as globais do mesmo modulo que faz o parsing
  after: gedcom_state.py com 45 linhas (estado e acesso) e gedcom_parser.py com 67 linhas (parsing e grafo); dependencia em uma unica direcao, do parser para o estado
change_set:
  - chg: CHG-001
    file: src/reconstructed/gedcom_state.py
    purpose: modulo novo com as globais, ref_id e get_name
  - chg: CHG-002
    file: src/reconstructed/gedcom_parser.py
    purpose: modulo novo com o parsing de GEDCOM e a construcao do grafo
  - chg: CHG-003
    file: src/reconstructed/upload.py
    purpose: arquivo removido; conteudo integral migrado para os dois modulos novos
  - chg: CHG-004
    file: src/reconstructed/{dna_analysis,family_navigation,matching,mermaid_render,path_finding,path_search}.py
    purpose: 9 linhas migradas de .upload para .gedcom_state, mais 2 comentarios de contrato
  - chg: CHG-005
    file: src/app.py
    purpose: import do carregador passa a vir de gedcom_parser
  - chg: CHG-006
    file: tests/{7 arquivos}
    purpose: 34 referencias migradas, incluindo 4 retornos de fixture e 11 mencoes em docstring
  - chg: CHG-007
    file: _reversa_sdd/parity/{harness,_check_split_types,_verify_fix_gives_parity}.py
    purpose: instrumentos apontando para os modulos novos, com alias livres
approval:
  by: user
  at: 2026-10-03
reversible_via:
  - CHG-001-gedcom-state.diff
  - CHG-002-gedcom-parser.diff
  - CHG-003-upload.diff
  - CHG-004-dna-analysis.diff
  - CHG-004-family-navigation.diff
  - CHG-004-matching.diff
  - CHG-004-mermaid-render.diff
  - CHG-004-path-finding.diff
  - CHG-004-path-search.diff
  - CHG-005-app.diff
  - CHG-006-test-characterization-matching.diff
  - CHG-006-test-characterization-mermaid.diff
  - CHG-006-test-dna-analysis.diff
  - CHG-006-test-domain.diff
  - CHG-006-test-mermaid-escape.diff
  - CHG-006-test-path-search.diff
  - CHG-006-test-upload.diff
  - CHG-007--check-split-types.diff
  - CHG-007--verify-fix-gives-parity.diff
  - CHG-007-harness.diff
  - aplicar-diff.py (aplicador com modo --reverter)
---

## O que foi feito

Separacao de `src/reconstructed/upload.py`, que acumulava tres responsabilidades, em dois modulos com responsabilidade unica declarada:

| Modulo | Responsabilidade | Linhas |
|---|---|---|
| `gedcom_state.py` | ser o registro do estado do processo e dar acesso aos registros de pessoa e de familia | 45 |
| `gedcom_parser.py` | traduzir um arquivo GEDCOM em registros e no grafo, substituindo o estado | 67 |

A direcao da dependencia ficou em um sentido so: o parser conhece o estado, o contrario nunca.

## O contrato preservado

A assimetria de substituicao do estado foi mantida exatamente como estava:

- `people`, `families` e `child_to_family` sao mutados **in place** (`clear()` mais `update()`), para o vinculo importado no topo pelos outros modulos continuar apontando para o objeto vivo.
- `graph` e **reatribuido** (`gedcom_state.graph = new_graph`), e por isso continua sendo importado dentro da funcao por quem o consome.

O bloco de `get_name`, incluindo o aviso de que formato vazio **nao** e "Sem Nome" e a referencia ao `DIV-001`, foi preservado literalmente, por fatiamento do arquivo original em vez de redigitacao.

## Incidente de execucao: vermelho, reversao, correcao, verde

Esta transformacao ficou **vermelha na primeira aplicacao** e o ciclo completo do protocolo foi executado. O registro fica aqui porque e exatamente para isso que a rede de seguranca existe.

**Primeira aplicacao: suite com 118 passa para 73 aprovados e 60 erros.** Causa: a regra de reescrita cobria apenas `upload.<simbolo>`, e quatro fixtures fazem `return upload`, devolvendo o modulo como valor. A checagem de sintaxe nao pega nome indefinido, entao o defeito so apareceu no teste.

**Reversao pelo diff.** Construido o `aplicar-diff.py`, que reverte aplicando os CHG ao contrario. A reversao foi provada objetivamente: a suite voltou a **118 aprovados e 15 erros**, a linha de base exata.

**Dois defeitos no proprio revertedor, corrigidos:**
1. O posicionamento dos trechos usava a linha do lado antigo em vez da linha do lado novo, e errava o deslocamento em arquivo com mais de um trecho.
2. No diff de remocao pura, o deslocamento ficava em zero e o resto do arquivo era anexado depois do conteudo restaurado, duplicando o arquivo. Detectado por medicao (226 linhas em vez de 113) e corrigido com guarda explicita.

**Segunda aplicacao: paridade com 6 divergencias.** Causa: o `harness.py` ja usava o alias `P` para `path_search`, e o alias que eu introduzi para `gedcom_parser` foi sobrescrito pelo import seguinte. O coletor do candidato morria com `AttributeError`, o que o harness conta como divergencia. Corrigido com alias livres (`GP` e `GS`), e o diff guardado foi ressincronizado para continuar espelhando o aplicado.

**Resultado final, medido:**

| Instrumento | Antes | Depois |
|---|---|---|
| Suite de testes | 118 aprovados, 15 erros de ambiente | **118 aprovados, 15 erros de ambiente** |
| Paridade com o oraculo congelado | 100 por cento | **100 por cento, zero divergencia em 6 fixtures** |
| Consistencia entre o aplicado e os diffs | nao se aplica | **20 de 20 diffs consistentes, zero falhas** |

## Nota de metodo

O aplicador e o preparador ficam nesta pasta e sao parte do artefato, nao ferramenta descartavel: o preparador deriva os modulos novos do arquivo original por fatiamento, e o aplicador reverte a partir dos diffs guardados. Foi essa dupla que permitiu reverter com precisao sem `git checkout`, que teria desfeito tambem as mudancas da feature 003, ainda nao commitadas.

O aplicador tambem torna mecanica a invariante declarada no README do registro: toda transformacao aplicada e revertivel pelo diff guardado.
