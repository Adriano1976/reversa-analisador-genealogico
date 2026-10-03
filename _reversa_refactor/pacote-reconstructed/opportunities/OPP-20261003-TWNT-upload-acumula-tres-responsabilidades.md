---
schema_version: 1
id: OPP-20261003-TWNT
display_number: 19
context: pacote-reconstructed
verb: modularize
title: upload.py acumula parsing, grafo e o estado global do processo
target:
  files: [src/reconstructed/upload.py]
  symbol: load_gedcom_and_build_graph, build_graph_from_parser e as quatro globais de modulo
smell: arquivo que faz coisas demais, misturando tres responsabilidades: registro do estado global do processo, leitura do arquivo GEDCOM e construcao do grafo
roi:
  confidence: green
  impact: acoplamento. Cinco modulos importam as globais deste arquivo (`matching`, `family_navigation`, `path_finding`, `mermaid_render`, `path_search`, alem de `dna_analysis`). Separar o registro de estado do carregador da um unico ponto de acoplamento explicito, em vez de um modulo que e ao mesmo tempo dado e comportamento. E pre-requisito do subpacote `parsers/` da oportunidade OPP-20261003-GUE7
  cost: low
  est_return: estado separado do carregamento, e o split em parsers/ passa a ser honesto em vez de esconder o estado dentro do parser
state: applied
traceability:
  soul:
    - .reversa/soul.md#decisoes-fundadoras
  specs:
    - _reversa_sdd/architecture.md#3.3
    - _reversa_sdd/code-analysis.md#1
    - _reversa_sdd/busca-caminho/design.md
---

## Antes observado

`upload.py` tem 113 linhas e tres papeis:

1. **Registro de estado do processo**: as globais `people`, `families`, `graph` e `child_to_family`.
2. **Leitura de GEDCOM**: `load_gedcom_and_build_graph`, que abre o arquivo com `ged4py`.
3. **Construcao do grafo**: `build_graph_from_parser`.

Os acessores `ref_id` e `get_name` tambem vivem aqui, e o `get_name` carrega um contrato delicado: o aviso de que **nao** se deve tratar formato vazio como "Sem Nome", sob pena de quebrar a paridade com o oraculo (`DIV-001`).

O docstring do modulo ja reconhece o problema de nome ("o nome do modulo veio do legado, mas aqui nao ha upload") e documenta o contrato de mutacao in-place, que e o motivo de metade dos modulos importarem as globais no topo.

## Transformacao proposta

Separar em dois modulos, sem alterar comportamento:

| Modulo | Conteudo |
|---|---|
| `gedcom_state.py` | `people`, `families`, `graph`, `child_to_family`, `ref_id`, `get_name` |
| `gedcom_parser.py` | `load_gedcom_and_build_graph`, `build_graph_from_parser` |

**Contrato que nao pode ser ferido.** `family_navigation.py` e `path_finding.py` documentam que importam `people` no topo **de proposito**, porque a mutacao e in-place (`clear()` mais `update()`), e que `graph` e a excecao: e **reatribuido**, e por isso e importado dentro da funcao. O split precisa preservar exatamente isso. Se `graph` passar a ser mutado in-place para uniformizar, o comportamento muda em um ponto que a suite nao cobre diretamente.

O aviso de `get_name` sobre formato vazio migra junto, sem reescrita.
