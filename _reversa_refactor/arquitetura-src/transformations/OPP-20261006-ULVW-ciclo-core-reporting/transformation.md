---
schema_version: 1
id: OPP-20261006-ULVW
verb: decouple
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/rede-caracterizacao-depois.txt
    - safety-net/suite-depois.txt
    - safety-net/pyrefly-depois.txt
    - before-after/pyrefly-antes.txt
    - CHG-001.diff
    - CHG-002.diff
measurement:
  before: "reporting -> core: 3 arestas de import; ciclo core/ <-> reporting/ presente; 21 pontos de chamada acoplados (19 chamadas de funcao mais 2 acessos a people)"
  after: "reporting -> core: 0 arestas de import; ciclo core/ <-> reporting/ EXTINTO; 0 imports de core dentro de reporting/; os 21 pontos continuam existindo, agora satisfeitos por parametro"
change_set:
  - chg: CHG-001
    file: src/reporting/mermaid_render.py
    purpose: Remove os tres imports de core e recebe o resolvedor de dominio por parametro nas duas funcoes publicas
  - chg: CHG-002
    file: src/core/diagram_domain.py
    purpose: Novo modulo com `resolvedor_de_diagrama()`, que da nome ao contrato de dominio que o desenho consome
  - chg: CHG-001
    file: src/core/path_search.py
    purpose: Importa o resolvedor e o injeta nas duas chamadas de render
  - chg: CHG-001
    file: src/core/dna_analysis.py
    purpose: Importa o resolvedor e o injeta na chamada de render do fluxo de DNA
approval:
  by: user
  at: 2026-10-06T00:00:00Z
reversible_via: [CHG-001.diff, CHG-002.diff]
---

# OPP-20261006-ULVW, desacoplar o ciclo `core/` ↔ `reporting/`

Transformação de `decouple` sobre `src/reporting/mermaid_render.py`, `src/core/path_search.py`,
`src/core/dna_analysis.py` e o novo `src/core/diagram_domain.py`.

## Acoplamento antes, medido por AST

```text
core       -> reporting   2
reporting  -> core        3     <- o ciclo
```

Fan-out de `reporting/mermaid_render.py` para `core/`, em três imports no topo:

| Linha | Módulo | Símbolos |
|---|---|---|
| 16 | `core.family_navigation` | `exclude_tail`, `get_spouses`, `pick_spouse_for_couple`, `split_path_by_marriage` |
| 22 | `core.path_finding` | `find_ancestral_path` |
| 23 | `core.gedcom_state` | `get_name`, `people` |

Dentro do renderizador, **21 pontos de acoplamento**: 19 chamadas de função mais 2 acessos diretos a
`people`, distribuídos entre `generate_mermaid_graph` (linhas 78 a 92),
`generate_mermaid_graph_indirect_bridge` (126 a 247) e a aninhada `add_node` (181).

## A costura aplicada

Inversão de dependência por injeção, sem mover nenhuma decisão de lugar.

O renderizador deixou de importar `core` e passou a receber `dominio`, o mapeamento devolvido por
`core.diagram_domain.resolvedor_de_diagrama()`. Quem busca o dado é o chamador, que já é `core`.

### Rota descartada, com o motivo

A saída natural seria **mover o layout para o núcleo**, deixando o renderizador como serializador
puro. Isso quebraria o ciclo de forma ainda mais limpa, e foi **recusado**: as decisões de layout
(o casal do ancestral comum, o ancestral que ancora o ramo, o ponto de corte por casamento) são
decisão de negócio, e `_reversa_sdd/architecture.md` §3 diz textualmente que `reporting/` "não é
folha, e não pode ser", com o `ADR-11` mantendo essas regras ali de propósito. O verbo `decouple`
proíbe redistribuir responsabilidade entre módulos.

### Forma do resolvedor

`dict` de funções, e não classe nem `Protocol`, porque `paradigm_decision.md` manda o núcleo
permanecer em funções puras e proíbe introduzir objetos com estado no cálculo.

## Acoplamento depois, medido pelo mesmo script

```text
core       -> reporting   2     (os 2 imports que PERMANECEM: e a direcao legitima)
reporting  -> core        0     <- extinto
```

| Aresta | Antes | Depois |
|---|---|---|
| `reporting` → `core` | 3 | **0** |
| `core` → `reporting` | 2 | 2 (inalterado, é a direção legítima) |
| Ciclo `core/` ↔ `reporting/` | presente | **EXTINTO** |
| Ciclo `core/` ↔ `parsers/` | presente | presente (fora do escopo, é a `OPP-20261006-LIGH`) |
| Imports de `core` dentro de `reporting/` | 3 | **0** |

Os 21 pontos de chamada continuam existindo, porque a decisão de layout não migrou. O que mudou é
que eles agora são satisfeitos por parâmetro, e não por importação.

## Prova de preservação

| Verificação | Antes | Depois |
|---|---|---|
| Rede de caracterização Mermaid | 39 passam | **39 passam** |
| Suíte completa | 164 passam, 15 erros de ambiente | **164 passam, 15 erros idênticos** |
| `pyrefly check src` | 27 erros | **27 erros, mesmo conjunto** |
| String Mermaid | goldens de 3 caminhos mais o caso sem conexão | **idêntica, linha a linha** |
| Valor de `_LABEL_SEGURO` | lista branca fechada | **inalterado** |
| `__all__` de `path_search` | 18 nomes | **inalterado** |

Os 15 erros de suíte são `PermissionError` do sandbox em `tmp_path`, pré-existentes e alheios a
esta mudança. Os 27 erros de tipo também são pré-existentes: varredura confirmou que **nenhum deles
aponta** para `diagram_domain.py`, `mermaid_render.py`, `path_search.py` ou `dna_analysis.py`.

Prova direta do caminho de DNA, que a suíte exercita de passagem: `_montar_diagrama` foi chamada à
mão com o resolvedor injetado e devolveu o diagrama direto completo, com o nó de casal
`N_I1_I2["Joao Silva &amp; Maria Souza"]` e os três `style`. Sem caminho, devolve `None` como antes.

## Superfície alterada, completa

| Arquivo | Linha | Mudança |
|---|---|---|
| `src/reporting/mermaid_render.py` | docstring | registra o contrato de domínio e por que o layout fica |
| `src/reporting/mermaid_render.py` | imports | 3 imports de `core` removidos |
| `src/reporting/mermaid_render.py` | 68 | `generate_mermaid_graph` ganha `dominio` e aliases locais |
| `src/reporting/mermaid_render.py` | 78 | `get_spouses` passa a `dominio["get_spouses"]` |
| `src/reporting/mermaid_render.py` | 120 | `generate_mermaid_graph_indirect_bridge` ganha `dominio` e 5 aliases |
| `src/reporting/mermaid_render.py` | 141, 150, 246 | as três recursões repassam `dominio` |
| `src/core/diagram_domain.py` | novo | 52 linhas, uma função |
| `src/core/path_search.py` | 41 | importa o resolvedor |
| `src/core/path_search.py` | 173 | resolve uma vez e injeta nas duas chamadas |
| `src/core/dna_analysis.py` | 35 | importa o resolvedor |
| `src/core/dna_analysis.py` | 52 | mantém o import do render, agora na direção legítima |
| `src/core/dna_analysis.py` | 58 | `_montar_diagrama` recebe `dominio` |
| `src/core/dna_analysis.py` | 167 | resolve uma vez por análise, fora do laço |
| `src/core/dna_analysis.py` | 212 | passa `dominio` |

Zero linha de lógica de negócio alterada. A única diferença de estrutura é o parâmetro a mais e o
módulo resolvedor.

## O que esta transformação não resolve

O ciclo acionável por importação morreu. A **inversão de camada em si não**: `reporting/` continua
contendo decisão de negócio de apresentação, e isso é deliberado, porque `architecture.md` §3 exige
que continue. A decisão de fronteira segue registrada como 🔴 em `.reversa/soul.md` §3 D2, sem
decisão humana, e o texto do `architecture.md` §3 e do `c4-components.md` que afirma que
`reporting/` importa `core` **passa a estar desatualizado** e precisa de adendo.

## Reversão

```text
git apply -R _reversa_refactor/arquitetura-src/transformations/OPP-20261006-ULVW-ciclo-core-reporting/CHG-001.diff
rm src/core/diagram_domain.py
```

`git apply --reverse --check` de `CHG-001.diff` passa. `CHG-002.diff` é o arquivo novo, e a reversão
dele é a remoção do arquivo.

## Rastreabilidade

| Item | Locator |
|---|---|
| Os dois ciclos de pacote | `.reversa/soul.md` §3 D2; `_reversa_sdd/architecture.md` §3 |
| Por que `reporting/` não pode ser folha | `_reversa_sdd/architecture.md:73`; `_reversa_sdd/adrs/11-reorganizar-em-pacotes-por-responsabilidade.md` |
| Decisão do operador sobre a fronteira | registrada como 🔴 sem decisão humana em `.reversa/soul.md` §3 D2 |
| Contrato de escape, intocado | `_reversa_sdd/adrs/05-escape-de-rotulo-mermaid.md`; `BUG-20260929-J6PQ`; `BUG-20261002-T4ZM` |
| Núcleo em funções puras | `_reversa_sdd/migration/paradigm_decision.md` § Decisão do usuário |
