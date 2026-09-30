# Análise de Código — analisador-genealogico

> Nível de documentação: **Essencial** (`state.json` → `doc_level`)
> Re-extração de 2026-09-30. Substitui o `code-analysis.md` de 2026-08-03, que descrevia o monolito de 887 linhas.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Fonte: leitura integral de `app.py` + `reconstructed/{domain,upload,path_search,dna_analysis}.py` (1201 linhas de Python) neste workspace.

---

## 1. Visão Geral da Estrutura

O código tem **duas camadas com contratos diferentes**:

| Camada | Arquivo | Linhas | Papel |
| --- | --- | --- | --- |
| Apresentação / rota | `app.py` | 84 | Recebe HTTP, valida entrada, chama um fluxo, renderiza. Nenhuma regra de negócio. 🟢 |
| Núcleo | `reconstructed/*.py` | 1086 | Toda a lógica: parsing, grafo, matching, caminho, Mermaid. 🟢 |

O núcleo comunica-se por **estado global mutável** em `upload.py` (`people`, `families`, `graph`, `child_to_family`), importado pelos outros módulos. Não há injeção de dependência nem objeto de sessão. 🔴 (acoplamento — ver §6)

```
app.py ──► upload.load_gedcom_and_build_graph        (action=upload_gedcom)
       ──► path_search.path_search                   (action=path_search)
       ──► dna_analysis.dna_analysis                 (action=dna_analysis)

upload.py ──(globais)──► path_search.py ──(get_parents, find_ancestral_path,
                                           generate_mermaid_graph)──► dna_analysis.py
domain.py ◄── importado por upload.py (demojibake) e dna_analysis.py (strip_bad_utf, demojibake)
```

> **Leitura tardia da global `graph`:** `find_indirect_path` faz `from .upload import graph` **dentro da função** (`path_search.py:131`), para captar o rebind feito por `load_gedcom_and_build_graph`. Um import no topo capturaria `None` para sempre. 🟢

---

## 2. Módulo `upload-gedcom`

**Arquivos:** `reconstructed/upload.py` (100 linhas), `reconstructed/domain.py` (84 linhas, após a remoção das entidades mortas)
**Rota:** `POST /` com `action=upload_gedcom` (`app.py:22-34`)

### 2.1 Fluxo de controle

Texto do fluxo (nível `essencial` — sem flowchart dedicado):

1. `app.py:23` — se `gedcom` não está em `request.files` → renderiza com `"Nenhum arquivo GEDCOM enviado."`, `success=False`.
2. `app.py:26` — se `gedcom_file.filename == ''` → `"Nenhum arquivo selecionado."`.
3. `app.py:29-30` — salva em `uploads/<filename>`, usando o nome que veio do cliente.
4. `app.py:31` — chama `load_gedcom_and_build_graph(gedcom_path)`.
5. `upload.py:88` — abre `GedcomReader` como context manager; exceção sobe para o `except` de `app.py:33` e vira `f"Erro ao processar GEDCOM: {e}"`.
6. `upload.py:89-90` — materializa `INDI` e `FAM` em dicionários novos, indexados por `xref_id`.
7. `upload.py:91` — `build_graph_from_parser` monta o grafo.
8. `upload.py:95-98` — **substitui as globais in-place** (`clear()` + `update()`), mantendo válidas as referências já importadas por outros módulos.
9. `upload.py:99` — devolve `sorted([get_name(p) for p in people.values()])`.
10. `app.py:32` — renderiza o template com `all_names` e a mensagem de sucesso.

### 2.2 Algoritmos e regras

| # | Regra | Local | Conf. |
| --- | --- | --- | --- |
| U-01 | Nome formatado é `person.name.format()`; o literal `'Sem Nome'` só ocorre se `person` ou `person.name` estiver ausente | `upload.py:47` | 🟢 |
| U-02 | Formato vazio devolve **string vazia**, e isso é o comportamento canônico — medido em dado real: 296 de 35.460 pessoas numa árvore, 17 de 3.056 em outra | `upload.py:40-45` | 🟢 |
| U-03 | O grafo é **não-direcionado** (`nx.Graph`), com dois tipos de nó: `type="person"` e `type="family"` | `upload.py:52-60` | 🟢 |
| U-04 | Aresta pessoa↔família só é criada **se a pessoa já existir como nó** (`g.has_node`), o que descarta silenciosamente referências órfãs | `upload.py:72-78` | 🟢 |
| U-05 | FAM sem `xref_id` é ignorada por completo (`continue`) | `upload.py:57-59` | 🟢 |
| U-06 | `child_to_family` acumula **todas** as famílias em que a pessoa aparece como `CHIL` (`.setdefault(...).append(...)`) | `upload.py:71` | 🟢 |
| U-07 | Extração de `xref_id`: `getattr(val, "xref_id", val)` — aceita objeto ged4py ou string crua | `upload.py:30` | 🟢 |
| U-08 | `strip_bad_utf` aplica um mapa fixo de **18 pares** de mojibake e depois remove tudo que não case `[\w\sÁ-ú'-]` | `domain.py:29-41` | 🟢 |
| U-09 | `demojibake` só tenta o round-trip `latin1 → utf-8` se a string contiver um dos marcadores `Ã`, `Â`, `A�`, `�`; aceita o resultado só se ele não contiver resíduo | `domain.py:44-54` | 🟢 |
| U-10 | `register_person` é **idempotente**: se o `xref_id` já existe, retorna sem fazer nada | `domain.py:91-92` | 🟢 |
| U-11 | Sem validação de extensão, tipo ou tamanho; o nome do arquivo vira caminho, então colisão **sobrescreve** | `app.py:29`, docstring `upload.py:5-6` | 🟢 |

> 🔴 **Gap conhecido (não é regressão nova):** `U-11` é a lacuna já registrada no bug `BUG-20260929-QMLY-upload-sem-limites`. A reconstrução reproduziu a ausência de limites de propósito, para manter fidelidade ao legado.

### 2.3 Estruturas de dados

| Entidade | Definição | Campos | Observação |
| --- | --- | --- | --- |
| Registro de pessoa (dict) | `domain.py:93-98` — **antes** da remoção de 2026-09-30 | `xref_id`; `name`; `name_clean`; `sub_records` | Pertencia a `GenealogyGraph`; **a classe foi removida** |
| ~~`Family`~~ | *(removida)* | — | **Removida em 2026-09-30** — decisão do usuário, `questions.md#pergunta-3` |
| ~~`GenealogyGraph`~~ | *(removida)* | — | **Removida em 2026-09-30** |
| ~~`DNAGroup`~~ | *(removida)* | — | **Removida em 2026-09-30** |

> 🟢 **REMOÇÃO APLICADA em 2026-09-30.** A varredura de referências confirmou que `Family`, `GenealogyGraph` e `DNAGroup` **não eram instanciadas em nenhum caminho de produção** — apareciam apenas nas próprias definições. Consultada, a decisão do usuário foi **remover** (`questions.md#pergunta-3`): arquitetura abandonada, não preparação futura.
>
> **Efeito:** `reconstructed/domain.py` caiu de 115 para **84 linhas** e hoje contém **apenas** `strip_bad_utf` e `demojibake` — o que de fato era consumido. A contradição do `networkx.MultiGraph` no docstring de `GenealogyGraph` desapareceu junto com a classe. `tests/test_domain.py` perdeu os 9 testes que exercitavam as classes extintas (suíte: 95 → 86 itens coletados).

### 2.4 Estado global

| Variável | Tipo | Declarada | Mutada em |
| --- | --- | --- | --- |
| `people` | `dict[str, registro ged4py]` | `upload.py:16` | `upload.py:95` |
| `families` | `dict[str, registro ged4py]` | `upload.py:17` | `upload.py:96` |
| `graph` | `nx.Graph \| None` | `upload.py:18` | `upload.py:97` |
| `child_to_family` | `dict[str, list[str]]` | `upload.py:19` | `upload.py:98` |

**Singleton por processo.** Dois uploads concorrentes de usuários diferentes escrevem no mesmo estado — risco de isolamento multi-tenant já registrado em `migration/risk_register.md`. 🟢

---

## 3. Módulo `busca-caminho`

**Arquivo:** `reconstructed/path_search.py` (506 linhas)
**Rota:** `POST /` com `action=path_search` (`app.py:65-78`)

### 3.1 Fluxo de controle — `path_search()` (`:463-502`)

1. `:469-470` — `strip()` nos dois nomes.
2. `:472-477` — resolve cada nome; se algum não resolve, devolve `(None, msg, False)` com `"Pessoa 1 '{nome}' não encontrada."`.
3. `:479` — **usa sempre o primeiro ID** quando há homônimos (`p1_ids[0]`, `p2_ids[0]`).
4. `:481` — tenta caminho ancestral (`find_ancestral_path`).
5. `:482-485` — se achou: `"Conexão direta encontrada (ancestral comum)."` e Mermaid via `generate_mermaid_graph`.
6. `:487` — senão, tenta caminho indireto (`find_indirect_path`, `MAX_HOPS=40`).
7. `:488-491` — se não há caminho: devolve `(None, "Nenhuma conexão encontrada entre ...", True)` — **`success=True` apesar de não haver resultado**.
8. `:492-494` — senão: `"Conexão indireta encontrada (via casamento/afinidade)."` e Mermaid via `generate_mermaid_graph_indirect_bridge`.

### 3.2 Algoritmos

| # | Algoritmo | Local | Descrição |
| --- | --- | --- | --- |
| P-01 | Resolução de pessoa por nome | `:30-35` | Duas passadas: igualdade `case-insensitive` primeiro; se vazia, substring `case-insensitive`. |
| P-02 | Pais de uma pessoa | `:42-61` | Prefere a referência `FAMC` do próprio registro; se ausente, cai no índice `child_to_family`. Coleta todo `HUSB`/`WIFE` das famílias, sem duplicar. |
| P-03 | Cônjuges | `:64-88` | Caminho principal por `FAMS`. **Fallback condicional:** a varredura global só roda se `spouse_ids` estiver vazio. |
| P-04 | BFS bidirecional por pais | `:144-178` | Duas filas (`deque`), alternando um nível de cada lado; para quando um nó está no `visited` do outro. Teto de `MAX_DEPTH=20` **iterações de profundidade**, não de gerações. |
| P-05 | Caminho indireto | `:126-141` | `nx.shortest_path` (BFS não ponderado) no grafo pessoa↔família; rejeita se `len(path)-1 > MAX_HOPS` (40); comprime nós de família mantendo só quem está em `people`; exige ≥ 2 pessoas. |
| P-06 | Decomposição por casamento | `:95-103` | Acha o **primeiro** par adjacente que são cônjuges e parte o caminho em `left`/`right`. |
| P-07 | Compressão do caminho | `:117-119` | `exclude_tail(seq, n=1)` remove a última posição para não repetir o ancestral nas duas colunas. |
| P-08 | Emissão Mermaid (direto) | `:217-263` | `flowchart BT`; funde o ancestral comum num nó "casal" quando ele não é extremidade do caminho. |
| P-09 | Emissão Mermaid (ponte) | `:266-456` | Dois ramos com subgrafos de colunas, âncoras invisíveis e aresta rotulada `Casamento`. |

### 3.3 Regras de escape do rótulo Mermaid (críticas)

| # | Regra | Local | Conf. |
| --- | --- | --- | --- |
| P-10 | `_mermaid_sid` mantém apenas `[A-Za-z0-9_]`, remove `@`, troca `+` por `_` e prefixa `N_`. Se receber coleção, usa o primeiro elemento | `:185-190` | 🟢 |
| P-11 | `_mermaid_label` aplica NFC, normaliza espaço não-quebrável/travessões/aspas curvas, troca `"` por `'`, achata quebras de linha e então aplica **lista branca** `_LABEL_SEGURO` | `:201-214` | 🟢 |
| P-12 | Após a lista branca, `&`, `<` e `>` viram entidades HTML (`&amp;`, `&lt;`, `&gt;`) | `:214` | 🟢 |
| P-13 | A lista é **branca, não negra** — a negra anterior foi furada pela crase, que desvia o lexer Mermaid para markdown-string | `:193-201` (comentário) | 🟢 |

> **Contrato especificado pela primeira vez** no adendo `bug-BUG-20260929-J6PQ-v001.md`. É exatamente o ponto que a extração de 2026-08-03 não cobria.

### 3.4 Constantes

| Constante | Valor | Significado |
| --- | --- | --- |
| `MAX_DEPTH` | 20 | Nível máximo de subida na BFS bidirecional. 🟢 |
| `MAX_HOPS` | 40 | Máximo de arestas no caminho indireto. 🟢 |

### 3.5 Lacunas registradas no legado (reproduzidas de propósito)

| # | Lacuna | Local |
| --- | --- | --- |
| P-14 | Homônimos: usa o **primeiro ID** encontrado, sem desempate nem aviso. 🔴 | `:479` |
| P-15 | Famílias adotivas/complexas assumem caminho por pais. 🔴 | docstring `:8-10` |
| P-16 | `get_parents` ignora irmãos quando não há `FAMC` nem entrada em `child_to_family`. 🟡 | `:47-48` |
| P-17 | No passo 7, `success=True` com `path_result=None` — a tela precisa distinguir "sem conexão" de erro por outro meio. 🟡 | `:488-491` |

---

## 4. Módulo `analise-dna`

**Arquivo:** `reconstructed/dna_analysis.py` (395 linhas)
**Rota:** `POST /` com `action=dna_analysis` (`app.py:44-63`)

### 4.1 Fluxo de controle — `dna_analysis()` (`:340-395`)

1. `:346-349` — resolve a pessoa-raiz por **substring** `case-insensitive` no nome; usa o primeiro ID; se não achar, `raise ValueError("Seu nome '{root_name}' não foi encontrado no GEDCOM.")`.
2. `:351` — `read_csv_with_fallback`: tenta `utf-8`, cai para `latin-1` só em `UnicodeDecodeError`; depois `strip()` nos nomes das colunas.
3. `:352-354` — `detect_columns`; se faltar coluna de nome ou de cM → `raise ValueError("Colunas de Nome e cM não encontradas no CSV.")`.
4. `:355` — `aggregate_matches` agrupa e soma cM.
5. `:357` — `build_ged_indexes` constrói índices e o cache de atributos.
6. `:362-391` — para cada match agregado: tenta casar candidatos; se casou, busca caminho ancestral **até a raiz**; se o caminho existe, acrescenta ao resultado; senão registra o motivo do descarte.
7. `:393` — ordena por `cm` decrescente.
8. `:394` — `"{n} conexões encontradas. {m} descartadas."`

### 4.2 Algoritmos e regras de negócio

| # | Regra | Local | Conf. |
| --- | --- | --- | --- |
| D-01 | Normalização de nome: `strip_bad_utf` → `NFKD` → remove diacríticos → `/` vira espaço → pontuação vira espaço → minúsculas → espaços colapsados | `:74-81` | 🟢 |
| D-02 | Chave de agrupamento do CSV = `norm(demojibake(nome))` **mais** o ID (`[A-Z]{2}\d{7}`) se houver, senão o e-mail normalizado, unidos por `" \| "` | `:174-180` | 🟢 |
| D-03 | A cM do match é a **soma** dos segmentos do grupo (`agg({cm_col: "sum"})`) | `:183-190` | 🟢 |
| D-04 | Detecção da coluna de ID: qualquer coluna em que ≥ 30 % dos valores casem `[A-Z]{2}\d{7}`; usa a **primeira** encontrada | `:163-167` | 🟢 |
| D-05 | Detecção da coluna de e-mail: colunas cujo nome contenha `mail` (case-insensitive); usa a **última** | `:168-169` | 🟢 |
| D-06 | Nomes de coluna aceitos: `Name`/`MatchedName`/`Nome` e `cM`/`TotalCM`/`Total cM` | `:161-162` | 🟢 |
| D-07 | Fórmula do score: `round(0.55*token_sort_ratio + 0.25*partial_ratio + 0.20*ratio(given) + (8*inter − 4*common_penalty), 2)` | `:272` | 🟢 |
| D-08 | Bônus de interseção de sobrenomes = `8.0 × (nº em comum) − 4.0 × (quantos são sobrenomes comuns)` | `:270-271` | 🟢 |
| D-09 | Desempate do melhor candidato: mais sobrenomes em comum → maior `given` → maior `score` | `:274-277` | 🟢 |
| D-10 | **Filtro anti-falso-positivo:** se ambos os lados têm sobrenomes, a interseção é 0 e não há acerto de sufixo → descarta com `"sem sobrenome em comum (filtro anti-falso-positivo)"` | `:287-289` | 🟢 |
| D-11 | `required_intersection` sobe de 1 para 2 quando o prenome é genérico **e** há ≥ 2 sobrenomes no CSV | `:291-293` | 🟢 |
| D-12 | Jaccard com prefixo suave; limiar **0.5** quando há ≥ 2 sobrenomes no CSV | `:295-298` | 🟢 |
| D-13 | O limiar cai para **0.33** só quando `cM ≥ 150` **e** o prenome **não** é genérico | `:299-301` | 🟢 |
| D-14 | Limiares de aceitação (6 ramos, avaliados em ordem) | `:305-320` | 🟢 |
| D-15 | Conflito de nome do meio: se o CSV tem token que não é prenome nem sobrenome e é disjunto dos tokens do GEDCOM, o aceite é rebaixado a `score ≥ 96`, `given ≥ 92`, `inter ≥ required` e `jacc_ok` | `:322-326` | 🟢 |
| D-16 | Faixas de cM: 9 faixas declaradas, **sobrepostas** | `:30-40` | 🟢 |
| D-17 | `get_relationships_by_cm`: `cM ≤ 0` ou não numérico → **lista vazia**. Positivo fora de todas as faixas → `["Relação distante ou indeterminada"]` | `:62-66` | 🟢 |
| D-18 | O contrato de D-16/D-17 é **lista**, nunca escalar — 50 cM casa 4 faixas ao mesmo tempo | `:65` | 🟢 |
| D-19 | `STOP_WORDS` = `de, da, do, das, dos, e`; `SHORT_KEEP` = `sa, sá` sobrevivem a `drop_short_tokens` | `:42`, `:59`, `:84-85` | 🟢 |
| D-20 | `SURNAME_EQUIV`: `netto→neto`, `gouvea→gouveia`, `gouvêa→gouveia`, `gouvéia→gouveia` | `:53-58`, `:95` | 🟢 |
| D-21 | Sufixos de sobrenome removidos e guardados à parte: `filho, neto, junior, júnior, sobrinho` | `:48`, `:91-93` | 🟢 |
| D-22 | `GENERIC_GIVENS` tem 20 prenomes (com e sem acento) | `:43-47` | 🟢 |
| D-23 | `soft_prefix_jaccard` usa prefixo mínimo de 4 quando algum token é curto **ou termina em ponto** | `:128-144` | 🟢 |
| D-24 | O resultado de cada match aceito é o **primeiro** candidato que tiver caminho ancestral até a raiz (`break`) | `:374-389` | 🟢 |
| D-25 | Motivos de descarte registrados: sem candidato por sobrenome, filtro anti-falso-positivo, score insuficiente, sem caminho subindo por pais | `:255`, `:289`, `:330-331`, `:391` | 🟢 |

**Os seis ramos de aceitação (D-14), na ordem em que o código os avalia:**

| Ramo | Condição | Linha |
| --- | --- | --- |
| 1 | prenome genérico **e** `inter ≥ 2` **e** `jacc ≥ 0.67` **e** `score ≥ 100` | `:305-306` |
| 2 | prenome não-genérico **e** `inter ≥ 2` **e** `jacc ≥ 0.50` **e** `given ≥ 85` **e** `score ≥ 80` | `:307-308` |
| 3 | prenome não-genérico **e** `inter ≥ 1` **e** `jacc ≥ 0.80` **e** `score ≥ 86` | `:309-310` |
| 4 | `given ≥ 90` **e** `score ≥ 92` **e** `inter ≥ required` **e** `jacc_ok` | `:311-312` |
| 5 | `given ≥ 95` **e** `score ≥ 88` **e** `inter ≥ required` **e** `jacc_ok` | `:313-314` |
| 6 (bônus) | prefixo de sobrenome do CSV casa com sobrenome do GED **e** `given ≥ 90` **e** `score ≥ 86` **e** `inter ≥ 1` **e** `jacc_ok` | `:316-320` |

> **Correção factual contra a extração anterior.** `HARD_MIN = 92` e `GIVEN_MIN = 90` **não existem** em nenhum arquivo de `analisador-genealogico/`. Eram código morto do monolito original (`app_legacy_e43ca22.py:653-654`) e a reconstrução **nunca os implementou**. Os literais 92 e 90 aparecem somente dentro dos ramos 4 e 5 de D-14, como valores de comparação, não como constantes nomeadas. 🟢
> `analise-dna/design.md` e `analise-dna/requirements.md` da extração anterior afirmavam que eles estavam "declarados mas não usados" na reconstrução — isso era **falso**. O adendo `003-refactor-code-quality` já corrigia o registro.

### 4.3 Faixas de cM (D-16) — tabela completa

| Faixa | Parentesco declarado |
| --- | --- |
| 3300 – 3720 | Pai/Mãe ↔ Filho(a) |
| 2200 – 3400 | Irmãos completos |
| 1317 – 2312 | Avós/Netos, Tios/Tias ↔ Sobrinhos(as), Meios-irmãos |
| 553 – 1330 | Primos de 1º grau |
| 200 – 850 | Primos de 1º grau (1× removido), Meios-primos, Tios-avós ↔ Sobrinhos-netos |
| 46 – 515 | Primos de 2º grau |
| 30 – 350 | Primos de 2º grau (1× removido), Primos de 3º grau |
| 10 – 220 | Primos de 3º grau (1× removido), Primos de 4º grau |
| 0 – 110 | Primos de 4º/5º grau ou mais distantes |

> ⚠️ As faixas **se sobrepõem até 4 vezes**: 50 cM casa 4 faixas simultaneamente; 300 cM casa 3; 3400, 800 e 15 casam 2. Qualquer consumidor que trate o retorno como escalar está errado. 🟢

### 4.4 Otimização registrada (comportamento preservado)

`build_ged_indexes` (`:198-230`) calcula `norm_name` e `surnames_set` **uma vez por análise** e guarda em `features[pid]`, em vez de renormalizar dentro do laço de candidatos. Medição registrada no adendo `003`: 27,77 ms → 2,29 ms por match (12,13×). Nenhuma decisão de aceitação mudou de valor. 🟢

---

## 5. Dicionário de Dados Resumido

Nível `essencial` embute a tabela aqui, sem `data-dictionary.md` separado.

### 5.1 Entidades

| Entidade | Origem | Campos | Observação |
| --- | --- | --- | --- |
| PERSON | registro `INDI` do ged4py | `xref_id`, `name`, `sub_records` (`FAMC`, `FAMS`, eventos) | Não persistido. 🟢 |
| FAMILIA | registro `FAM` do ged4py | `xref_id`, `HUSB`, `WIFE`, `CHIL` | `HUSB`/`WIFE` opcionais. 🟢 |
| FAMILIA (dataclass `Family`) | ~`domain.py:61`~ | — | **REMOVIDA em 2026-09-30** — não instanciada em produção. 🟢 |
| DNA_MATCH (agregado) | derivado do CSV | `_group_key`, `cm` (soma), `matched_name` | Chave = nome normalizado + ID **ou** e-mail. 🟢 |
| DNAGroup (dataclass) | ~`domain.py:106`~ | — | **REMOVIDA em 2026-09-30** — não instanciada em produção. 🟢 |

### 5.2 Estruturas de runtime

| Estrutura | Chave | Valor | Onde |
| --- | --- | --- | --- |
| `people` | `xref_id` | registro `INDI` | global `upload.py` |
| `families` | `xref_id` | registro `FAM` | global `upload.py` |
| `graph` | — | `nx.Graph` com nós `person` e `family` | global `upload.py` |
| `child_to_family` | `xref_id` do filho | lista de `xref_id` de famílias | global `upload.py` |
| `ged_index` | nome normalizado | lista de `pid` | local de `build_ged_indexes` |
| `surname_index` | sobrenome | lista de `pid` | local de `build_ged_indexes` |
| `features` | `pid` | `norm`, `given_tokens`, `surnames`, `surnames_list`, `tokens` | cache local |
| `path_result` | — | `person1_name`, `person2_name`, `text_path`, `mermaid_data` | retorno de `path_search()` |
| item de resultado de DNA | — | `match_name`, `cm`, `text_path`, `mermaid_data`, `relationships`, `csv_name` | retorno de `dna_analysis()` |
| item de descarte | — | `csv_name`, `motivo` | retorno de `dna_analysis()` |

### 5.3 Constantes de domínio

| Constante | Valor | Local |
| --- | --- | --- |
| `SHARED_CM_DATA` | 9 faixas | `dna_analysis.py:30-40` |
| `STOP_WORDS` | 6 palavras | `:42` |
| `GENERIC_GIVENS` | 20 prenomes | `:43-47` |
| `SURNAME_SUFFIXES` | 5 sufixos | `:48` |
| `COMMON_SURNAMES` | 16 itens, **15 únicos** (`souza` duplicado) | `:49-52` |
| `SURNAME_EQUIV` | 4 equivalências | `:53-58` |
| `SHORT_KEEP` | `sa`, `sá` | `:59` |
| `MAX_DEPTH` | 20 | `path_search.py:22` |
| `MAX_HOPS` | 40 | `path_search.py:23` |
| `_LABEL_SEGURO` | regex de lista branca | `path_search.py:201` |
| `UPLOAD_FOLDER` | `"uploads"` | `upload.py:21` |
| `app.secret_key` | `'f@milyse@rch_dna_edition_v16'` | `app.py:11` |

---

## 6. Dívidas Técnicas e Acoplamentos

| # | Dívida | Severidade | Evidência |
| --- | --- | --- | --- |
| 1 | **Estado global mutável** compartilhado entre requisições e entre usuários | 🔴 Alta | `upload.py:16-19`; mutação em `:95-98` |
| 2 | **Dependências sem versão fixada** | 🔴 Alta | `requirements.txt` sem operador |
| 3 | `secret_key` **hardcoded** | 🔴 Alta | `app.py:11` |
| 4 | Upload **sem validação** de extensão, tipo ou tamanho; nome do cliente vira caminho | 🔴 Alta | `app.py:29` |
| 5 | Re-parse integral do GEDCOM **a cada POST** | 🟡 Média | `app.py:31`, `:42` |
| 6 | Entidades declaradas que o fluxo real não usa | 🟢 Baixa | `domain.py:74`, `:106` |
| 7 | Sem persistência de resultados | 🟢 Baixa | `dna_analysis.py:393` monta tudo em memória |
| 8 | `README.md` do módulo anuncia `Pyvis`, que foi removido | 🟢 Baixa | `analisador-genealogico/README.md` |

> A dívida "ausência total de testes" da extração anterior **deixou de existir**: 7 arquivos, 86 itens coletados (eram 95 antes da remoção de 9 testes das entidades extintas). **CI/CD e Docker seguem ausentes.** 🟢

---

## 7. Lacunas para Validação Humana

| ID | Lacuna | Conf. |
| --- | --- | --- |
| ~~L-01~~ | ✅ **RESOLVIDA em 2026-09-30** — eram arquitetura abandonada; as três entidades foram **removidas** por decisão do usuário (`questions.md#pergunta-3`). | 🟢 |
| L-02 | `get_spouses` só faz a varredura global se nenhum `FAMS` resolveu — ✅ **RESOLVIDO em 2026-09-30**: confirmado **intencional** (economia de varredura), registrado como contrato. | 🟢 |
| L-03 | O teto de 20 do `find_ancestral_path` conta **iterações de profundidade**, não gerações — ✅ **RESOLVIDO em 2026-09-30**: corte silencioso **aceito** por decisão do usuário, preservando fidelidade ao legado. | 🟢 |
| L-04 | `soft_prefix_jaccard`: quando algum token é curto, os **dois** lados são truncados em 4 caracteres — pode criar falso positivo entre sobrenomes de mesmo prefixo. | 🟡 |
| L-05 | `COMMON_SURNAMES` contém `"souza"` **duas vezes** (`:50`). Inofensivo para um `set`, mas indica descuido na curadoria. Verificado por varredura: 16 itens, 15 únicos. | 🟢 |
| L-06 | `success=True` com `path_result=None` (P-17): a distinção "sem conexão" × "erro" depende do template, não do contrato do handler. | 🟡 |

---

## 8. Resumo para o Reversa

- **Módulos analisados:** 3 (`upload-gedcom`, `analise-dna`, `busca-caminho`) + a camada de rota `app.py`.
- **Principais algoritmos:** BFS bidirecional por pais (teto 20), caminho indireto por `shortest_path` com compressão de nós de família (teto 40), scoring difuso ponderado com 6 ramos de aceitação, agregação de segmentos cM por chave composta, emissão de Mermaid com lista branca de caracteres.
- **Entidades:** **após a remoção de 2026-09-30**, restam **2 efetivamente usadas** (registro de pessoa e agregado DNA_MATCH, ambos como `dict` em memória). As 3 declaradas e não instanciadas — `Family`, `GenealogyGraph` e `DNAGroup` — foram **removidas** por decisão do usuário (`questions.md#pergunta-3`).
- **Regras catalogadas:** 11 (upload) + 17 (caminho) + 25 (DNA) = **53**, mais as constantes de domínio.
- **Correções contra a extração anterior:** `HARD_MIN`/`GIVEN_MIN` não existem na reconstrução; a `action` de DNA é `dna_analysis` (não `process_dna`); a suíte de testes existe e é significativa; `Pyvis` e `matplotlib` foram removidos.

---

*Gerado pelo Reversa-Archaeologist em 2026-09-30 (re-extração).*
