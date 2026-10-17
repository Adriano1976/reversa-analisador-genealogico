# Data Delta: desempenho da carga da árvore GEDCOM

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Modelo extraído em: `_reversa_sdd/data-dictionary.md`, `_reversa_sdd/erd-complete.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Veredito

**Não há delta de dados.** Nenhum campo é criado, removido ou alterado; nenhuma tabela, índice,
payload de porta ou coluna do PostgreSQL muda; nenhuma migração existe. O delta desta feature é de
**contrato interno de função** e de **alocação transitória**.

## 2. A árvore — forma, tipos e ordem (sem mudança)

`_reversa_sdd/data-dictionary.md#1` descreve a árvore como tupla de quatro posições. Ela continua
sendo exatamente isso, e é o que `ports/adaptadores.py:257` devolve à aplicação.

| Posição | Estrutura | Chave / ordem | Muda? |
|---|---|---|---|
| 0 | `people: dict` | `ref_id(xref_id)` → registro `INDI`, na **ordem do arquivo** | **não** |
| 1 | `families: dict` | `ref_id(xref_id)` → registro `FAM`, na **ordem do arquivo** | **não** |
| 2 | `graph: networkx.Graph` | nós de pessoa na ordem de `people`, depois famílias na ordem do arquivo; arestas na ordem de `HUSB`, `WIFE`, `CHIL` | **não** (e é exigido idêntico, inclusive a ordem) |
| 3 | `child_to_family: dict` | xref do filho → **lista** de famílias na ordem em que aparecem | **não** |

**Ordem é contrato, não detalhe** (`@ordem`, `_reversa_sdd/migration/parity_specs.md#4`): a ordem de
inserção das arestas decide qual caminho `nx.shortest_path` devolve quando há dois de mesmo
comprimento. Por isso a mudança passa a **lista de registros na ordem do arquivo**, e não o
dicionário.

## 3. Delta de contrato interno (a única assinatura que muda)

`src/parsers/gedcom_parser.py:26`

| | Antes | Depois |
|---|---|---|
| Assinatura | `build_graph_from_parser(people_dict: dict, parser)` | `build_graph_from_parser(people_dict: dict, familias)` |
| Origem das famílias | itera `parser.records0("FAM")` **internamente** | recebe a sequência **já materializada** pelo chamador |
| Leitura de arquivo | sim (via `parser`) | **não** (`RN-03`) |

`src/parsers/gedcom_parser.py:73-75`

| | Antes | Depois |
|---|---|---|
| Materialização `INDI` | `records0("INDI")` → dict | igual |
| Materialização `FAM` | `records0("FAM")` → dict, **e de novo** dentro do grafo | `list(records0("FAM"))` **uma vez**; o dict é montado dessa lista |
| Chamada do grafo | `build_graph_from_parser(new_people, parser)` | `build_graph_from_parser(new_people, familias)` |

O que **não** muda na assinatura pública: `carregar_arvore(file_path) -> Tree` continua igual, e o
adaptador da porta não é tocado.

## 4. Alocação transitória

| | Antes | Depois |
|---|---|---|
| Registros `FAM` materializados por carga | **2 × 6.930 = 13.860** | **6.930** |
| Chamadas a `read_record` por carga | 49.321 | **42.391** |
| Objetos de registro vivos ao mesmo tempo | dois conjuntos completos (um no dict, outro criado e descartado no grafo) | **um** conjunto |
| Lista adicional de referências | — | 6.930 ponteiros (dezenas de KB) |

A direção do pico de memória é de **redução**: um conjunto inteiro de 6.930 registros deixa de ser
criado. O valor exato do pico não foi medido — a feature não o exige, e afirmá-lo sem medição seria
o mesmo erro que ela existe para evitar.

## 5. Caso de borda que justifica a decisão de forma

`families` é chaveado por `ref_id` (`src/core/registro.py:35-37`), e `ref_id(None)` devolve `None`.
Duas famílias sem `xref_id` no mesmo arquivo caem **na mesma chave** do dicionário, e o dicionário
fica com menos entradas do que o arquivo tem. Passar `families.values()` ao grafo iteraria menos
famílias do que a segunda passada atual — uma diferença silenciosa, ainda que o grafo final tenda a
ser o mesmo porque toda família sem `xref_id` é ignorada (`BR-U-18`).

Por isso a fonte da lista é `records0("FAM")`, **a mesma sequência** que o código percorre hoje. A
cardinalidade do dicionário `families` continua como está, com o mesmo comportamento de colapso —
esta feature **não** o conserta, e não foi pedida para isso.

## 6. PostgreSQL, payloads e disco

| Estrutura | Muda? |
|---|---|
| 6 tabelas de `init.sql` (`analysis`, `analysis_person`, `match_result`, `match_path_node`, `dna_kit`, `descartado`) | **não** |
| `AnaliseParaRegistrar` e os 5 payloads da porta | **não** |
| `analysis_person.completa`, `match_result.matched_person_xref` (FK composta) | **não** |
| Arquivos em `src/uploads/` e `_aposentados/` | **não** (a árvore real é lida, nunca escrita) |
| Caches de módulo (`_INDICE_DE_NOMES`, `L-24`) | **não** (e a colisão de chave segue como dívida aberta, alheia a esta feature) |

## 7. Migração

**n/a.** Nada a migrar: não há dado persistido com a forma antiga, e a árvore é reconstruída a cada
requisição. A compatibilidade é com o **comportamento**, e ela é provada por impressão digital
(`roadmap.md` `D-04`) e pela paridade.
