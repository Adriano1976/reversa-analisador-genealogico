# Unit `busca-caminho` — Design Técnico

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Substitui o design de 2026-10-05, que descrevia o grafo lido por **import tardio de uma global** e o índice de nomes invalidado por `gedcom_state.versao` — **nenhum dos dois existe mais**.
> Fontes: `application/path_search.py`, `application/__init__.py`, `core/{path_search,path_finding,family_navigation,documentary_relationship,diagram_domain}.py`, `reporting/mermaid_render.py`, `app.py` (ramo `path_search`), `flowcharts/busca-caminho.md`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Ação | Entrada | Saída | Status |
|--------|---------|------|---------|-------|--------|
| POST | `/` | `path_search` | `gedcom_filename`, `person1_name`, `person2_name` | `index.html` com `path_result` e `message` | 200 |

> 🟢 **Não há arquivo nesta requisição** — a busca opera só sobre a árvore já armazenada, endereçada pela referência. Toda recusa de negócio é HTML `200` com `success=False`; o `413` de corpo grande é a única recusa de transporte.

### Símbolos

| Símbolo | Arquivo | Assinatura | Retorno | Observação |
|---------|---------|-----------|---------|------------|
| `path_search` (caso de uso) | `application/path_search.py` | `(person1_name, person2_name, arvore, deps, dono)` | `ResultadoDeBusca` | `deps` chega **montado**; `dono` sem comportamento 🟢 |
| `_desfecho` | idem | `(dados, sucesso)` | `Desfecho` | Deriva dos **dois insumos**, nunca do texto 🟢 |
| `ResultadoDeBusca` | idem | `@dataclass(frozen=True)` | — | `desfecho`, `dados`, `mensagem` — **`dados` sem renomear** 🟢 |
| `Desfecho` | `application/__init__.py` | `Enum` | — | `RESULTADO`, `SEM_RESULTADO`, `ERRO_DE_ENTRADA` 🟢 |
| `nomes_de_exibicao` | idem | `(arvore)` | `list[str]` ordenada | Compartilhada pelos três fluxos 🟢 |
| `path_search` (núcleo) | `core/path_search.py` | `(person1_name, person2_name, deps, arvore)` | `(path_result \| None, msg, success)` | Tupla de três: **contrato de paridade** 🟢 |
| `_candidatos` | idem | `(arvore, nome, ids_do_legado)` | `(dossie, candidatos)` | Une legado + exatos, sem repetir 🟢 |
| `_homonimos` | idem | `(arvore, person1_name, person2_name, p1_ids, p2_ids)` | `dict` | Agrega **só os lados ambíguos** 🟢 |
| `find_person_by_name` | `core/family_navigation.py` | `(arvore, name_query)` | `list[str]` | Igualdade, depois substring; **com** acento 🟢 |
| `get_parents` | idem | `(arvore, person_id)` | `list[str]` | `FAMC` preferencial, fallback no índice 🟢 |
| `get_spouses` | idem | `(arvore, person_id)` | `list[str]` | Varredura global **só** se `FAMS` ficar vazio 🟢 |
| `are_spouses` / `split_path_by_marriage` / `pick_spouse_for_couple` / `exclude_tail` | idem | `(arvore, …)` | `bool` / `(left, right, par)` / `str \| None` / `list` | Primeiro par adjacente 🟢 |
| `find_ancestral_path` | `core/path_finding.py` | `(arvore, start_id, end_id, max_depth=20)` | `(path, ancestral)` | BFS **bidirecional** por pais 🟢 |
| `find_indirect_path` | idem | `(arvore, start_id, end_id, max_hops=40)` | `list[str] \| None` | Caminho mais curto no grafo **da árvore recebida** 🟢 |
| `documentary_relationship` | `core/documentary_relationship.py` | `(arvore, a_id, b_id, homonyms=None)` | `dict` | Parentesco documental completo 🟢 |
| `documentary_label` | idem | `(deg_a, deg_b)` | `dict (key, label, meioses, degrees)` | Traduz graus em parentesco 🟢 |
| `person_summary` / `_diferencas` | idem | `(arvore, person_id)` | `dict` | Ficha de **13** campos e comparação 🟢 |
| `homonym_dossier` | idem | `(arvore, name_query, similar_ids=None)` | `dict` | Compara **sem** acento 🟢 |
| `hop_evidence` | idem | `(arvore, child_id, parent_id)` | `dict` | Evidência de um salto 🟢 |
| `find_all_common_ancestors` | idem | `(arvore, a_id, b_id, max_depth=12, limit=12)` | `list[dict]` | Todos os ancestrais comuns 🟢 |
| `normalizar` / `parse_year` / `get_children` | idem | — | `str` / `int \| None` / `list[str]` | `get_children` **sem índice** 🔴 |
| `_chave_de` / `_indice_por_nome` | idem | `(people)` / `(arvore)` | `tuple` / `dict` | Chave derivada do **conteúdo** 🟢 |
| `resolvedor_de_diagrama` | `core/diagram_domain.py` | `(arvore)` | `dict` de **7** consultas ligadas | É o que impede `reporting/` de importar `core` 🟢 |
| `_mermaid_sid` / `_mermaid_label` | `reporting/mermaid_render.py` | `(raw)` / `(txt)` | `str` | Id seguro e rótulo por lista branca 🟢 |
| `generate_mermaid_graph` | idem | `(path, p1_id, p2_id, common_ancestor_id, dominio)` | `str` | Diagrama direto 🟢 |
| `generate_mermaid_graph_indirect_bridge` | idem | `(p1_id, p2_id, person_path, dominio)` | `str` | Diagrama de ponte 🟢 |

### Constantes

| Constante | Valor | Onde | Papel |
|-----------|-------|------|-------|
| `MAX_DEPTH` | `20` | `path_finding.py` | **Iterações** do BFS bidirecional. ⚠️ **Interpolado no aviso `sem_caminho`** 🟢 |
| `MAX_HOPS` | `40` | idem | **Arestas** do grafo bipartido — o teto em vínculos pessoa-a-pessoa é ≈ metade 🟡 |
| `MAX_DEPTH_ALTERNATIVOS` | `12` | `documentary_relationship.py` | Teto da enumeração de ancestrais comuns 🟢 |
| `LIMITE_DE_CADEIAS` | `8` | idem | Teto da contagem de cadeias (o número exibido é um **piso**) 🟡 |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | `12` / `70` | idem | **Filtro de evidência**, não regra biológica 🟢 |
| `LIMITE_DE_CANDIDATOS` | `5` | `core/path_search.py` | Teto **por lado** nas combinações com homônimos 🟢 |
| `AVISO_AFINIDADE` | texto fixo em maiúsculas | idem | Impede a leitura da afinidade como consanguinidade 🟢 |
| `_LABEL_SEGURO` | regex de **lista branca** | `mermaid_render.py` | Documentada no código, com os dois bugs que a moldaram 🟢 |
| Cores dos nós | verde / vermelho / amarelo / laranja | idem | Papel visual de cada nó 🟢 |
| Direção do diagrama | `flowchart BT` | idem | Base para o topo 🟢 |

### Contrato de retorno (`path_result`)

| Campo | Conteúdo | Conf. |
|-------|----------|-------|
| `person1_name` / `person2_name` | Nomes já com `strip` | 🟢 |
| `text_path` | Nomes do caminho unidos por `" → "` | 🟢 |
| `mermaid_data` | Texto do diagrama Mermaid | 🟢 |
| `documentary` | Resultado completo: `status`, `label`, `relationship_key`, `meioses`, `degrees`, fichas, evidência, homônimos, `additional_paths` e `warnings` | 🟢 |
| `observations` | Avisos do documental, **deduplicados**, mais o aviso de afinidade | 🟢 |

## Fluxo Principal

### Borda (`app.py`, ramo `path_search`)

1. `_arvore_do_formulario()` resolve e parseia a árvore escolhida (unit `tela-de-entrada`); erro aqui encerra o ramo. 🟢
2. Lê `person1_name` e `person2_name` **com `strip()`**. 🟢
3. `caso_de_uso_de_busca(person1_name, person2_name, arvore, _DEPENDENCIAS, DONO_DO_PROCESSO)` — as dependências de diagrama vêm **montadas uma vez na borda**, não por requisição. 🟢
4. Ramifica **pelo desfecho**, nunca pelo texto: `ERRO_DE_ENTRADA` → alerta com `success=False`; os outros dois → cartão, com `success=True` (e `path_result` ausente no `SEM_RESULTADO`). 🟢
5. `except ErroDeDominio` → `traduzir(erro).mensagem`; `except Exception` → `Ocorreu um erro: {e}`. 🟢

### Núcleo — `path_search` (`core/path_search.py`)

1. `strip()` nos dois nomes. 🟢
2. Resolve as duas listas de ids; lista vazia → `"Pessoa N '{nome}' não encontrada."` com `success=False`. 🟢
3. `_homonimos(...)` monta o dossiê agregado dos dois lados. 🟢
4. `_candidatos(...)` devolve o dossiê e a **lista** de candidatos de cada lado. 🟢
5. Laço aninhado com teto **5 × 5**, com cache de `(cand1, cand2) -> documental`: vence a **primeira** combinação cujo caminho tem `path.ids` — **não** a de menor distância. 🟢
6. Sem nenhuma combinação com caminho, usa o **primeiro id de cada lado** e calcula o parentesco uma vez. 🟢
7. **Com caminho direto:** nomes, `generate_mermaid_graph` e `"Conexão direta encontrada (ancestral comum)."` 🟢
8. **Sem caminho direto:** tenta `find_indirect_path`; sem caminho → `(None, "Nenhuma conexão encontrada entre '{p1}' e '{p2}'.", True)`. 🟢
9. **Com caminho indireto:** nomes, `generate_mermaid_graph_indirect_bridge`, e a **marcação de afinidade em três lugares** — `status = "affinity"` numa **cópia** do dicionário, rótulo próprio e o `AVISO_AFINIDADE`. 🟢
10. Monta `path_result` com `text_path` unido por `" → "` e devolve com `success=True`. 🟢

> ⚠️ **A marcação de afinidade é feita numa cópia** (`documental = dict(documental)`). O dicionário original continua `not_found`. Nenhum consumidor atual usa o original depois disso, mas a divergência entre duas referências ao "mesmo" resultado é armadilha para quem reimplementar (`M-01`, `state-machines.md`).

### BFS bidirecional (`find_ancestral_path`)

1. Duas fronteiras (`deque`) e dois conjuntos de visitados. 🟢
2. `start == end` → devolve `([id], id)`. 🟢
3. **Turno 1:** expande **um nível** do lado 1 subindo por `get_parents`; se algum nó recém-expandido já está no visitado do lado 2, o caminho é `caminho_até_ele + caminho_do_outro_lado_invertido_sem_repetir_o_encontro`. 🟢
4. **Turno 2:** mesma lógica do lado 2. 🟢
5. Teto atingido sem interseção → `(None, None)`, **em silêncio**. 🟢

### Caminho indireto (`find_indirect_path`)

1. Recebe o **grafo da árvore por parâmetro** — o import tardio da global deixou de existir (`BR-C-08`). 🟢
2. Grafo ausente ou nó inexistente → `None`. 🟢
3. `nx.shortest_path` (BFS **não ponderado**) com captura de `NetworkXNoPath` e `NodeNotFound`. 🟢
4. `len(caminho) - 1 > max_hops` → `None`. 🟢
5. Remove os nós de família; menos de **2** pessoas → `None`. 🟢

### Parentesco documental (`documentary_relationship`)

1. Registro ausente → `status = "not_found"` + aviso `pessoa_ausente`. 🟢
2. `find_ancestral_path(a, b, max_depth=MAX_DEPTH)`. 🟢
3. Sem caminho → `not_found` + aviso `sem_caminho` (que **interpola `MAX_DEPTH`** e afirma que isso não prova ausência de parentesco), mais `homonimo` se o dossiê for ambíguo. 🟢
4. Graus = posições do ancestral comum no caminho, de cada lado; `documentary_label(deg_a, deg_b)` → rótulo, chave canônica e meioses. 🟢
5. `hop_evidence` por aresta, **subindo antes do MRCA e descendo depois dele**. 🟢
6. `plausible is False` → aviso `data_impossivel`; **o caminho é mantido**. 🟢
7. Enumera todos os ancestrais comuns e monta os caminhos alternativos; havendo, aviso `caminhos_multiplos`. 🟢
8. Conta cadeias por ancestral; mais de uma → aviso `colapso_de_pedigree`. 🟢
9. Identidade ambígua → aviso `homonimo` e `status = "ambiguous"` (o status só é promovido **havendo caminho**). 🟢
10. Devolve o resultado completo. 🟢

### Tradução de graus (`documentary_label`)

| Condição | Rótulo | Chave canônica |
| --- | --- | --- |
| Ambos os graus zero | mesma pessoa | `SELF` 🟢 |
| Um dos graus zero, `n = 1` | Pai/Mãe | `PARENT_CHILD` 🟢 |
| Um dos graus zero, `n = 2` | Avô/Avó | `GRANDPARENT` 🟢 |
| Um dos graus zero, `n > 2` | prefixo `bis` repetido `n−2` vezes | `DIRECT_n` 🟡 |
| Menor grau 1, maior grau 1 | Irmãos | `SIBLINGS` 🟢 |
| Menor grau 1, maior grau 2 | Tio/Tia | `AUNT_UNCLE` 🟢 |
| Menor grau 1, maior grau > 2 | Tio/Tia com `bis` repetido | `GREAT_AUNT_k` 🟢 |
| Demais | Primos de `g` grau com `r` remoções | `gC` ou `gCrR`, com `g = menor−1` e `r = maior−menor` 🟢 |

> 🟡 **`bis` é repetido, não traduzido:** produz "bisbisavô" onde o português genealógico diria "trisavô". O rótulo usa numerais ordinais até 10º e o número cru acima disso.

### Escape do rótulo (`mermaid_render.py`)

1. `_mermaid_sid`: coleção → primeiro elemento; remove `@`; troca `+` por `_`; remove tudo fora de `[A-Za-z0-9_]`; prefixa `N_`. 🟢
2. `_mermaid_label`: **NFC** → NBSP/travessões/aspas curvas normalizados → `"` vira `'` → quebras de linha achatadas. 🟢
3. `_LABEL_SEGURO.sub('', s)` — **lista branca** remove o que sobra. 🟢
4. **Por último**, `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`. 🟢

> ⚠️ **A ordem dos passos 3 e 4 é invariante do contrato.** Se a conversão em entidades vier antes do filtro, o filtro pode remover pedaços da própria entidade já escapada. Não reordenar (`adrs/05`).

## Fluxos Alternativos

| Condição | Comportamento | Conf. |
| --- | --- | --- |
| Pessoa 1 ou 2 não resolvida | `"Pessoa N '{nome}' não encontrada."` com `success=False` | 🟢 |
| Homônimos sem nenhuma combinação com caminho | Usa o primeiro id de cada lado; o resultado sai marcado como ambíguo | 🟢 |
| Sem conexão direta nem indireta | `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` com **`success=True`** | 🟢 |
| Caminho mais fundo que `MAX_DEPTH` | Corte **silencioso**; o aviso diz que isso **não prova** ausência de parentesco | 🟢 |
| Caminho indireto acima de `MAX_HOPS` | Rejeitado — indistinguível de "sem caminho" | 🟢 |
| Pessoas idênticas | Caminho trivial; a pessoa é o próprio ancestral | 🟢 |
| `FAMS` parcialmente resolvido | **O fallback não roda**, e cônjuges legítimos podem faltar — contrato aceito em 2026-09-30 | 🟢 |
| Sem cônjuges no caminho indireto | O diagrama de ponte delega para o diagrama direto com `mrca=None` | 🟢 |
| Idade de genitor fora de 12–70 | Aviso `data_impossivel`; vínculo mantido | 🟢 |
| Sem data para julgar plausibilidade | `plausible = None` — **não** é falso | 🟢 |
| Colapso fora do teto (12 níveis / 8 cadeias) | **Não detectado** — e o silêncio é idêntico a "não há colapso" | 🟡 |
| Árvore carregada com o mesmo tamanho e os mesmos xrefs extremos da anterior | O índice de nomes **não** é reconstruído; o dossiê lista xrefs de outra árvore, **sem exceção** | 🔴 |
| Exceção inesperada | `"Ocorreu um erro: {e}"` com `success=False` | 🟢 |

## Dependências

| Dependência | Versão | Como usa | Conf. |
| --- | --- | --- | --- |
| **networkx** | **3.7** | `nx.Graph`, `nx.shortest_path`, `NetworkXNoPath`, `NodeNotFound`. (**O artefato de 2026-10-05 dizia `3.6.1` — o `requirements.txt` foi realinhado ao `.venv` em 2026-10-05 e fixa `3.7`.**) | 🟢 |
| Unit `upload-gedcom` | — | A **árvore como valor** `(people, families, graph, child_to_family)` e a porta de armazenamento | 🟢 |
| Unit `tela-de-entrada` | — | `_arvore_do_formulario` e a lista de nomes | 🟢 |
| Unit `analise-dna` | — | **Depende desta**: usa `documentary_relationship`, `family_navigation`, `path_finding` e a renderização | 🟢 |
| `utils/text_cleaning` | — | Mojibake na comparação de nomes do dossiê | 🟢 |
| `application/traducao.py` | — | Tabela de tradução de erro, compartilhada | 🟢 |
| `templates/index.html` | — | Renderiza o diagrama; Mermaid com `securityLevel: 'strict'` | 🟢 |
| **nenhuma integração de rede** | — | Não há HTTP de saída, banco nem fila nesta unit | 🟢 |

> 🟢 **A inversão de camada registrada em 2026-10-05 foi FECHADA.** `reporting/mermaid_render.py` **não importa `core`**: recebe `dominio`, o `dict` de sete consultas ligado à árvore por `functools.partial`. O ciclo `core/` ↔ `reporting/` deixou de existir (`ADR-34`).

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
| --- | --- | --- |
| Direta primeiro, indireta como fallback — **nunca as duas** | `core/path_search.py:path_search` | 🟢 |
| BFS bidirecional **manual**, em vez de `nx.lowest_common_ancestor`, porque a subida é restrita às arestas de paternidade | `path_finding.py:find_ancestral_path` | 🟢 |
| **Sem pesos e sem limiares** no BFS: o caminho é o primeiro encontrado, e a ordem de inserção das arestas é contrato de paridade | `path_finding.py` | 🟢 |
| **Corte silencioso** no teto do BFS — decisão humana de 2026-09-30 | `path_finding.py:MAX_DEPTH` | 🟢 |
| **Escolha entre homônimos por teste de combinações** (5×5, em cache), vencendo a primeira **com caminho** | `core/path_search.py:path_search` | 🟢 |
| O dossiê compara **sem acento**, e não com acento como `find_person_by_name` | `documentary_relationship.py:normalizar` | 🟢 |
| Ambigüidade **avisada** em vez de silenciosa | `documentary_relationship.py:homonym_dossier` | 🟢 |
| Compressão dos nós de família no caminho indireto | `path_finding.py:find_indirect_path` | 🟢 |
| **O grafo vem da árvore recebida por parâmetro** — o import tardio da global foi eliminado | `path_finding.py:find_indirect_path` | 🟢 |
| `get_spouses` faz varredura global **apenas** se `FAMS` ficar vazio — fallback total, não complemento | `family_navigation.py:get_spouses` | 🟢 |
| **Data não invalida vínculo**: registra evidência e avisa | `documentary_relationship.py:hop_evidence` | 🟢 |
| Afinidade marcada em **três lugares** (redundância deliberada), **numa cópia** do dicionário | `core/path_search.py` | 🟢 |
| Lista **branca** no rótulo, com entidades **depois** do filtro | `mermaid_render.py:_LABEL_SEGURO` | 🟢 |
| `subgraph` fechado por **context manager** | `mermaid_render.py:generate_mermaid_graph_indirect_bridge` | 🟢 |
| O **resolvedor de diagrama** entrega sete consultas já ligadas à árvore, e o renderizador **não importa `core`** | `core/diagram_domain.py:resolvedor_de_diagrama` | 🟢 |
| As decisões de **layout continuam no renderizador** — decidir o casal do ancestral comum é decisão de negócio (`ADR-11`) | `mermaid_render.py:generate_mermaid_graph` | 🟢 |
| O **desfecho tipado** em três valores, derivado de `(payload, sucesso)` | `application/path_search.py:_desfecho` | 🟢 |
| `dados` é o payload **sem renomear** — nome de campo de template não atravessa a fronteira | `application/path_search.py:ResultadoDeBusca` | 🟢 |
| O caso de uso **não monta** as dependências de diagrama: elas chegam por parâmetro | `application/path_search.py:path_search` | 🟢 |
| O índice `nome → ids` é invalidado por uma **chave derivada do conteúdo** — não por `id()`, que é reciclado (medido em 2026-10-06, `test_6d`), e sim por `(len(people), primeira chave, última chave)` | `documentary_relationship.py:_chave_de` | 🟢 |
| `get_children` varre todas as famílias, **sem índice** | `documentary_relationship.py:get_children` | 🔴 |

## Estado Interno

| Estado | Escopo | Observação | Conf. |
| --- | --- | --- | --- |
| `people`, `families`, `graph`, `child_to_family` | por requisição | Entram **por parâmetro**; nenhum módulo escreve global de dados — a corrida entre threads **deixou de existir** (`ADR-24`) | 🟢 |
| Cache de nomes `{chave, mapa}` | **módulo** | Chave = `(len(people), chaves[0], chaves[-1])` com `chaves = sorted(people)`. **É o único estado que sobrevive à requisição** — e a chave tem colisão possível | 🔴 |
| Cache de pares `(cand1, cand2) -> documental` | local da requisição | Evita recalcular o parentesco na busca por combinações | 🟢 |
| `dossie_por_nome`, `documental_por_pessoa` | local da requisição | Deduplicação dentro da busca (compartilhado com `analise-dna`) | 🟢 |
| `path_result` | local da requisição | Renderizado e descartado | 🟢 |

> 🔴 **O cache de nomes é o único estado de processo, e ele é a lacuna aberta da unit.** Ver `L-24` nos riscos.

## Observabilidade

| O quê | Onde | Observação |
|-------|------|------------|
| **Nenhum log** | — | A unit não registra nada: nem a busca, nem o corte por teto, nem a colisão do cache de nomes 🔴 |
| **Nenhuma métrica ou trace** | — | Não há contagem de iterações do BFS nem tempo de dossiê 🔴 |
| O texto do caminho, o diagrama e os avisos | tela | São o **único** sinal ao usuário 🟢 |
| Contrato de escape com evidência **fora** da aplicação | `tests/test_mermaid_escape.py` | O fuzz de **288 payloads** combinados e a varredura de **30.000 nomes** vivem como evidência do adendo `bug-BUG-20260929-J6PQ`, e não como teste permanente 🟡 |

## Riscos e Lacunas

- 🟢 ***`L-24` / `E-05` — colisão da chave do cache de nomes: CONFIRMADA POR EXECUÇÃO em 2026-10-10.*** `_chave_de` devolve `(len(people), chaves[0], chaves[-1])`, com `chaves = sorted(people)`. Dois GEDCOMs do **mesmo tamanho** e com os **mesmos xrefs extremos** reutilizam o índice da árvore **anterior**. **O experimento foi executado:** duas árvores de 4 pessoas, com a mesma chave `(4, '@I1@', '@I9@')` e xrefs interiores **diferentes** (`@I2@`/`@I3@` na primeira; `@I4@`/`@I5@` na segunda), carregadas no **mesmo processo**. O dossiê de homônimos da **segunda** árvore respondeu `exact_count: 1` citando **`@I2@`** — que **não existe** nela —, e `person_summary` degradou para `name = "Sem Nome"` **sem levantar nada**. A segunda árvore não continha nenhum "Joao". Três consequências que a leitura sozinha não dava: (1) o defeito é **real**, não hipotético; (2) a falha é **silenciosa** de ponta a ponta; (3) **o gatilho não depende do conteúdo, depende só da contagem** — medido nas duas árvores reais pequenas da pasta do operador, ambas têm `chaves[0] = '@I1000@'` e `chaves[-1] = '@I9@'`, e diferem **apenas** no tamanho (4.313 e 5.436). Duas exportações do mesmo exportador com o mesmo número de pessoas colidem. **Decisão humana de 2026-10-10: corrigir** — a correção mínima é acrescentar à chave algo derivado do conteúdo, e ela **não muda comportamento nenhum**, só o custo de reconstrução. `id()` **não** serve: é reciclado. Execução agendada para **depois do Passo 4**. Ver `flowcharts/busca-caminho.md` §13.
- 🟡 **`L-25` — a ordem de `common_ancestors` e de `additional_paths` pode variar com o `PYTHONHASHSEED`.** A varredura parte de `set(de_a) & set(de_b)` e a ordenação é estável, de modo que o empate em **meioses**, **distância** e **nome** herda a iteração do `set`. É a mesma classe do defeito que o `matching` fechou em 2026-10-05 — **e aqui segue aberta**. O `matching` resolveu com um quarto critério determinístico (o menor `xref_id`); esta unit **não** tem equivalente.
- 🔴 **`get_children` não tem índice**: cada chamada percorre **todas** as famílias do arquivo. `person_summary` o chama uma vez por ficha, e as fichas são montadas para todos os ids em cada chamada de `_diferencas` — que por sua vez é chamado **duas vezes** em `homonym_dossier`. Com vários homônimos por nome, o custo do dossiê cresce com o número de candidatos.
- 🟡 **`person_a` e `person_b` são fichas completas em cada resultado — MEDIDO em 2026-10-10, e o custo é menor do que a leitura sugeria.** Medição na árvore real de 35.460 pessoas: `person_summary` custa **15,4 ms por ficha**, de modo que as **142 fichas** do caso real de 71 conexões custam **≈ 2,2 s**. Para comparação, no mesmo ambiente: o **parse da árvore custa 20,9 s** e **uma** chamada de `homonym_dossier` custa **1,73 s**. Ou seja: as fichas são ≈ **10 %** do tempo do parse, e o gargalo real é o **parse a cada requisição** (`L-20` deixa de ser a prioridade de otimização). **Decisão humana de 2026-10-10: não otimizar agora** — a otimização mexeria em `get_children`, que alimenta também a detecção de colapso, e a ordem de inserção das arestas é **contrato de paridade** com o oráculo. O número fica registrado para quando houver uma segunda medição.
- 🟡 **O `MAX_DEPTH` está interpolado na mensagem** do aviso `sem_caminho`: mudar o teto muda **texto de contrato**.
- 🟡 **O corte silencioso do `MAX_DEPTH` é decisão humana** de 2026-09-30. A consequência aceita: uma árvore com mais de ~20 níveis faz a conexão direta falhar em silêncio e cair para a busca indireta, que pode achar um laço por afinidade **sem significado genealógico**.
- 🟡 **A varredura condicional de `get_spouses` é contrato**, não descuido: com `FAMS` parcialmente resolvido, cônjuges legítimos podem faltar e o fallback **não** corrige. Torná-la complementar **muda o resultado**.
- 🟡 **`MAX_HOPS` conta arestas do grafo bipartido**, e não passos entre pessoas: o teto efetivo em vínculos pessoa-a-pessoa é aproximadamente **metade** do valor declarado.
- 🟡 **A contagem de cadeias do colapso é truncada em 8**, então o aviso exibe um **piso**, não o total.
- 🟡 **`bis` é repetido, não traduzido** — "bisbisavô" onde o português genealógico diria "trisavô".
- 🟡 **`split_path_by_marriage` acha só o primeiro par de cônjuges**; caminhos com múltiplas afinidades renderizam de forma simplificada.
- 🟡 **O caminho indireto não passa pela checagem de plausibilidade de datas** — a faixa 12–70 só é aplicada ao caminho **direto**.
- 🟡 **`M-01` — o estado `affinity` é atribuído a uma cópia** do dicionário; o original segue `not_found`. Nenhum consumidor atual usa o original, mas a divergência é armadilha para reimplementação.
- 🟡 **`M-02` — a ambiguidade rebaixa `found` para `ambiguous`, mas não rebaixa `not_found`.** Com identidade ambígua **e** sem caminho, o status permanece `not_found` e a ambiguidade aparece **apenas** como aviso. Não há indicação de que a assimetria seja intencional.
- 🟡 **O colapso além do teto não é detectado**, e o aviso não distingue "sem colapso" de "colapso fora do alcance".
- 🟡 **`reporting/` ainda contém decisão de negócio** — decidir o casal do ancestral comum vive na apresentação, por decisão declarada (`ADR-11`). A dependência de `core` foi eliminada, a decisão não.
- 🟢 **`L-06` permanece resolvida por verificação no template:** os três desfechos produzem telas visualmente distintas — o alerta pega cor de `success` e o cartão aparece por `path_result`.
- 🟢 **Resolvido por decisão de produto anterior:** o vazamento de gramática Mermaid por aspa dupla + crase (`BUG-20260929-J6PQ`) e o descarte de 14 caracteres inertes (`BUG-20261002-T4ZM`), ambos com teste de regressão.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*
