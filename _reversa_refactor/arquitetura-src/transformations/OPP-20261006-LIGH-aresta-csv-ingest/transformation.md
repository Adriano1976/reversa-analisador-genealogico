---
schema_version: 1
id: OPP-20261006-LIGH
verb: decouple
state: applied
scope_applied: aresta 1 de 2
scope_blocked: aresta 2, parsers/gedcom_parser.py -> core/gedcom_state
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/rede-depois.txt
    - safety-net/suite-depois.txt
    - safety-net/pyrefly-depois.txt
    - CHG-001.diff
    - CHG-002.diff
measurement:
  before: "parsers -> core: 3 arestas (gedcom_parser.py:15, gedcom_parser.py:16, csv_ingest.py:42); ciclo core/ <-> parsers/ presente"
  after: "parsers -> core: 2 arestas (gedcom_parser.py:15, gedcom_parser.py:16); ciclo core/ <-> parsers/ AINDA PRESENTE; parsers -> utils subiu de 1 para 2"
change_set:
  - chg: CHG-002
    file: src/utils/name_keys.py
    purpose: Novo modulo puro com `norm_name`, sem nenhuma nocao de dominio
  - chg: CHG-001
    file: src/core/name_normalization.py
    purpose: Remove a definicao local e reexporta `norm_name` de `utils.name_keys`, preservando os tres enderecos de importacao
  - chg: CHG-001
    file: src/parsers/csv_ingest.py
    purpose: Passa a importar `norm_name` de `utils`, removendo a aresta `parsers -> core`
approval:
  by: user
  at: 2026-10-06T00:00:00Z
reversible_via: [CHG-001.diff, CHG-002.diff]
---

# OPP-20261006-LIGH, aresta 1 de 2 do ciclo `core/` ↔ `parsers/`

Transformação de `decouple` aplicada **parcialmente e de propósito**. O escopo foi decidido pelo
usuário depois de o especialista reportar que a segunda aresta não é desacoplável por refactor puro.

## O ciclo tinha duas arestas, e só uma é refactor

| Aresta | Origem | Situação |
|---|---|---|
| 1 | `parsers/csv_ingest.py:42` importava `core.name_normalization.norm_name` | **resolvida nesta transformação** |
| 2 | `parsers/gedcom_parser.py:15-16` importa `core.gedcom_state` para instalar o estado | **bloqueada pela spec**, ver abaixo |

## A aresta 1, resolvida

`norm_name` é normalização de texto pura: usa só `strip_bad_utf` e `unicodedata`, e não sabe nada de
genealogia. Foi movida para `src/utils/name_keys.py`, ao lado de `text_cleaning.py`.

`core/name_normalization.py` passa a **reexportar** o nome, o que preserva os três endereços de
importação que existiam antes. Prova executada: `core.name_normalization.norm_name`,
`utils.name_keys.norm_name` e `core.dna_analysis.norm_name` são **o mesmo objeto**.

O que ficou em `core/name_normalization.py` é o que tem domínio: o vocabulário de partículas,
prenomes genéricos, sufixos de sobrenome e as equivalências, mais as funções que o consomem.

| Aresta | Antes | Depois |
|---|---|---|
| `parsers` → `core` | 3 | **2** |
| `parsers` → `utils` | 1 | 2 |
| `core` → `utils` | 4 | 5 |
| Ciclo `core/` ↔ `parsers/` | presente | **presente** |

O ciclo **não** foi extinto, porque a aresta 2 responde por ele sozinha.

## A aresta 2, bloqueada pela spec

A saída seria o parser devolver valor em vez de instalar estado, e alguém do `core` instalar. Isso
quebraria o ciclo, e **não foi feito** porque contradiz o contrato escrito em dois artefatos:

| Artefato | Texto |
|---|---|
| `_reversa_sdd/upload-gedcom/design.md:33` | `load_gedcom_and_build_graph` \| `gedcom_parser.py:50` \| `(file_path: str)` \| `list[str]` \| **Substitui o estado**; devolve nomes ordenados 🟢 |
| `_reversa_sdd/upload-gedcom/requirements.md:148` | `src/parsers/gedcom_parser.py` \| `load_gedcom_and_build_graph` `:50-69`; `build_graph_from_parser` `:18-48` 🟢 |
| `_reversa_sdd/code-analysis.md:53` | `load_gedcom_and_build_graph` \| `gedcom_parser.py:50` \| `(file_path: str)` \| `list[str]` (nomes ordenados) 🟢 |

As três condições são contraditórias entre si:

1. a função precisa **instalar estado global** (a spec diz);
2. a função precisa **morar em `parsers/`** (a spec diz);
3. `parsers/` não pode importar `core` sem fechar o ciclo.

Quebrar o ciclo exige que o parser **não** instale o estado, e isso muda o comportamento observável
de uma função que a spec fixa. O verbo `decouple` proíbe mudar comportamento observável.

**Encaminhamento:** `/reversa-forward`, com atualização da spec de `upload-gedcom`. Não é trabalho
deste time. A oportunidade `OPP-20261006-3WR5` já registra que a migração aloca esta correção ao
alvo, e o `topology_decision.md` divide o bloco em `core/tree` mais `application/upload_tree.py`.

## Achado colateral verificado e descartado

Durante a análise levantei a hipótese de que `src/parsers/gedcom_parser.py:16` importava `get_name`
sem usá-lo. **A hipótese estava errada** e foi descartada por AST: `get_name` é usado em duas
linhas, a 23 (`build_graph_from_parser`) e a 68 (`load_gedcom_and_build_graph`). Varredura de
nomes importados contra nomes usados no módulo devolve conjunto vazio de não usados.

Registrado aqui porque um "achado" falso é pior que nenhum: ele viraria um `prune` que quebraria o
módulo. Não há candidato a `prune` neste arquivo.

## Prova de preservação

| Verificação | Antes | Depois |
|---|---|---|
| Rede de caracterização Mermaid | 39 passam | **39 passam** |
| Suíte completa | 164 passam, 15 erros de ambiente | **164 passam, 15 erros idênticos** |
| `pyrefly check src` | 27 erros | **27 erros** |
| `norm_name` nos três endereços | mesmo objeto | **mesmo objeto** |

Os dois erros de `pyrefly` que citam `csv_ingest.py` (linhas 153 e 163) são **pré-existentes e
idênticos** na linha de base, confirmado por `git stash`: são sobrecargas de `pandas.read_csv`, sem
relação com `norm_name`.

## Reversão

```text
git apply -R _reversa_refactor/arquitetura-src/transformations/OPP-20261006-LIGH-aresta-csv-ingest/CHG-001.diff
rm src/utils/name_keys.py
```

`git apply --reverse --check` de `CHG-001.diff` passa.
