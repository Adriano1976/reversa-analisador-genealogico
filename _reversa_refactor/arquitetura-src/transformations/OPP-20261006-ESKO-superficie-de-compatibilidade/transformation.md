---
schema_version: 1
id: OPP-20261006-ESKO
verb: standardize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: pattern-only
  evidence:
    - safety-net/suite.txt
    - safety-net/rede-mermaid.txt
    - safety-net/pyrefly.txt
    - safety-net/paridade.txt
    - CHG-001.diff
    - CHG-002.diff
measurement:
  before: "18 nomes em __all__ de path_search, dos quais 12 nunca usados pelo proprio modulo; 4 consumidores importando pelo caminho errado"
  after: "__all__ com 1 nome (o que o modulo define); 0 consumidores importando pelo caminho errado; 13 imports so-reexportados removidos"
change_set:
  - chg: CHG-001
    file: tests/test_path_search.py
    purpose: Importa de core.family_navigation e core.path_finding em vez de core.path_search
  - chg: CHG-001
    file: tests/test_mermaid_escape.py
    purpose: Importa _mermaid_label de reporting.mermaid_render
  - chg: CHG-001
    file: _reversa_sdd/parity/harness.py
    purpose: Coletor do candidato importa family_navigation e path_finding em vez de alcancar os 4 nomes por path_search
  - chg: CHG-002
    file: src/core/path_search.py
    purpose: Remove os 13 imports so-reexportados, reduz __all__ a ["path_search"] e corrige as afirmacoes falsas do docstring
approval:
  by: user
  at: 2026-10-06T00:00:00Z
reversible_via: [CHG-001.diff, CHG-002.diff]
---

# OPP-20261006-ESKO, superficie de compatibilidade por caminho errado

Transformação de `standardize` em dois lotes, aprovados e aplicados nesta ordem.

## O padrão detectado

O projeto pratica uma convenção clara: **cada nome é importado do módulo onde é definido**, e cada
módulo importa apenas o que usa. `path_search.py` era a exceção, e a exceção estava documentada
como se fosse intencional.

## Lote 1, migrar os consumidores

Os consumidores reais foram medidos por AST, e a lista do docstring estava errada em metade:

| Consumidor citado no docstring | Consome a superfície? |
|---|---|
| `app.py` | **não.** Importa apenas `path_search` |
| `core/dna_analysis.py` | **não.** Não importa nada de `core.path_search` |
| `tests/test_path_search.py` | sim: `find_ancestral_path`, `find_indirect_path`, `find_person_by_name` |
| `tests/test_mermaid_escape.py` | sim: `_mermaid_label` |
| `tests/test_characterization_mermaid.py` | **não.** Importa apenas `path_search` |
| `_reversa_sdd/parity/harness.py` | sim: `get_parents`, `get_spouses`, `find_ancestral_path`, `find_indirect_path` |
| sondas do BUG-20260929-J6PQ | não existem na árvore |

| Arquivo | Antes | Depois |
|---|---|---|
| `tests/test_path_search.py:20` | `find_ancestral_path`, `find_indirect_path`, `find_person_by_name` de `core.path_search` | `core.path_finding` e `core.family_navigation` |
| `tests/test_mermaid_escape.py:28` | `_mermaid_label` de `core.path_search` | `reporting.mermaid_render` |
| `_reversa_sdd/parity/harness.py:161` | `from core import path_search as P` e 4 acessos por `P.` | `from core import family_navigation as FN` e `path_finding as PF`, com os 4 acessos remapeados |

O harness mereceu cuidado especial: ele prova a paridade do núcleo, e o lado do oráculo importa
`_reversa_sdd/oracle/app_legacy_e43ca22.py` diretamente, que é **autocontido** (define `norm_name`,
`strip_bad_utf`, `get_parents` e o resto localmente, sem importar o núcleo). Por isso o oráculo está
imune a qualquer mudança estrutural do projeto, incluindo a `OPP-20261006-LIGH` que moveu
`norm_name`. Só o lado do candidato precisou de ajuste.

## Lote 2, reduzir a superfície

Varredura por AST classificou cada import do módulo:

| Papel | Nomes |
|---|---|
| usados pelo próprio `path_search` | `resolvedor_de_diagrama`, `documentary_relationship`, `homonym_dossier`, `person_summary`, `find_person_by_name`, `generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge`, `MAX_HOPS`, `find_indirect_path`, `get_name`, `people` |
| **só reexportados** (13) | `are_spouses`, `exclude_tail`, `get_parents`, `get_spouses`, `pick_spouse_for_couple`, `split_path_by_marriage`, `_LABEL_SEGURO`, `_mermaid_label`, `_mermaid_sid`, `MAX_DEPTH`, `find_ancestral_path`, `ref_id` |

| Antes | Depois |
|---|---|
| `__all__` com 18 entradas, das quais 17 reexportadas | `__all__ = ["path_search"]` |
| 13 imports que existiam só para reexportar | removidos |
| Docstring com duas afirmações falsas e uma lista de consumidores inventada | substituído pelo registro do que foi medido |

Nota de forma: `from __future__ import annotations` foi **mantido**, apesar de a sondagem o
classificar como não usado. Não é import de símbolo, é diretiva de compilador, e removê-la seria
mudança semântica de avaliação de anotações, fora do escopo de `standardize`.

## Confirmação de que a semântica não mudou

| Verificação | Antes | Depois |
|---|---|---|
| Suíte completa | 164 passam, 15 erros de ambiente | **164 passam, 15 erros idênticos** |
| Rede de caracterização Mermaid | 39 passam | **39 passam** |
| `pyrefly check src` | 27 erros | **27 erros** |
| **Harness de paridade** | 100 por cento | **PARIDADE 100 por cento, zero divergência** |

O harness foi rodado **depois** de editado, e as 6 fixtures continuam em zero divergência. Sem essa
prova, a edição do harness seria uma alteração da própria rede que ninguém teria validado.

## Reversão

```text
git apply -R _reversa_refactor/arquitetura-src/transformations/OPP-20261006-ESKO-superficie-de-compatibilidade/CHG-001.diff
git apply -R _reversa_refactor/arquitetura-src/transformations/OPP-20261006-ESKO-superficie-de-compatibilidade/CHG-002.diff
```

`git apply --reverse --check` passa nos dois.

## Efeito colateral registrado

A `dna_analysis.py` **mantém** a superfície homóloga dela: `__all__` com 18 nomes, incluindo
`norm_name`, `strip_bad_utf` e `split_name_pt`, reexportados de `core.name_normalization`,
`core.matching`, `core.cm_estimator` e `parsers.csv_ingest`. Ela **não** foi tocada, e há dois
motivos: o harness de paridade a alcança pelo nome do módulo (`D.norm_name`, `D.split_name_pt`,
`D.get_relationships_by_cm`), então reduzi-la exige verificar aquele contrato; e ela não é o alvo
desta oportunidade. Fica registrada como candidata a `standardize` própria, com o padrão já provado
aqui.

## Rastreabilidade

| Item | Locator |
|---|---|
| Papel do `reporting/` e o escape | `_reversa_sdd/adrs/11-reorganizar-em-pacotes-por-responsabilidade.md`, `adrs/05-escape-de-rotulo-mermaid.md` |
| O harness é a prova de paridade | `.reversa/soul.md` §5; `_reversa_sdd/parity/` |
| O oráculo é congelado e autocontido | `_reversa_sdd/oracle/ORACLE_MANIFEST.md` |
| Comportamento de `path_search` | `_reversa_sdd/busca-caminho/requirements.md` e `design.md` |
