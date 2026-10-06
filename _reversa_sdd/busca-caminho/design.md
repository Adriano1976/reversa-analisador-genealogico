# Unit `busca-caminho` — Design Técnico

> Unit do tipo **endpoint** — `POST /` com `action=path_search`.
> Re-extração de **2026-10-05** (nível **Completo**). Substitui o design de 2026-09-30, que descrevia um núcleo único e **não conhecia** o parentesco documental completo nem a escolha de homônimos por combinações.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Entrada | Saída | Status codes |
| --- | --- | --- | --- | --- |
| `POST` | `/` | `action=path_search`, `gedcom_filename`, `person1_name`, `person2_name` | `index.html` com `path_result` e `message` | `200` sempre — erro de negócio vira mensagem na tela; `413` se o corpo exceder 16 MB 🟢 |

### Símbolos

| Símbolo | Arquivo:linha | Assinatura | Retorno | Observação |
| --- | --- | --- | --- | --- |
| `path_search` | `path_search.py:126` | `(person1_name: str, person2_name: str)` | `(path_result \| None, msg, success)` | Fluxo completo 🟢 |
| `_candidatos` | `path_search.py:74` | `(nome, ids_do_legado)` | `(dossie, candidatos)` | Dossiê + lista de candidatos, **sem escolher** 🟢 |
| `_homonimos` | `path_search.py:92` | `(person1_name, person2_name, p1_ids, p2_ids)` | `dict` | Ambiguidade dos **dois** lados 🟢 |
| `find_person_by_name` | `family_navigation.py:21` | `(name_query)` | `list[str]` | Igualdade, depois substring; **com** acento 🟢 |
| `get_parents` | `family_navigation.py:29` | `(person_id)` | `list[str]` | `FAMC` preferencial, fallback `child_to_family` 🟢 |
| `get_spouses` | `family_navigation.py:51` | `(person_id)` | `list[str]` | Varredura global **só** se `FAMS` ficar vazio 🟢 |
| `are_spouses` | `family_navigation.py:78` | `(a_id, b_id)` | `bool` | — 🟢 |
| `split_path_by_marriage` | `family_navigation.py:82` | `(person_path)` | `(left, right, par)` | **Primeiro** par adjacente 🟢 |
| `pick_spouse_for_couple` | `family_navigation.py:93` | `(person_id, candidate_path)` | `str \| None` | Prefere cônjuge já no caminho 🟢 |
| `exclude_tail` | `family_navigation.py:104` | `(seq, n=1)` | `list` | Evita duplicar o ancestral 🟢 |
| `find_ancestral_path` | `path_finding.py:51` | `(start_id, end_id, max_depth=20)` | `(path, ancestral)` | BFS **bidirecional** por pais 🟢 |
| `find_indirect_path` | `path_finding.py:31` | `(start_id, end_id, max_hops=40)` | `list[str] \| None` | Caminho mais curto no grafo de famílias 🟢 |
| `documentary_relationship` | `documentary_relationship.py:436` | `(a_id, b_id, homonyms=None)` | `dict` | **Parentesco documental completo** 🟢 |
| `documentary_label` | `documentary_relationship.py:290` | `(deg_a, deg_b)` | `dict` (key, label, meioses) | Traduz graus em parentesco 🟢 |
| `person_summary` | `documentary_relationship.py:127` | `(person_id)` | `dict` (ficha) | Ficha completa da pessoa 🟢 |
| `homonym_dossier` | `documentary_relationship.py:205` | `(name_query, similar_ids)` | `dict` | Compara **sem** acento 🟢 |
| `hop_evidence` | `documentary_relationship.py:233` | `(child_id, parent_id)` | `dict` | Evidência de um salto 🟢 |
| `find_all_common_ancestors` | `documentary_relationship.py:408` | `(a_id, b_id, max_depth=12, limit=12)` | `list[dict]` | Todos os ancestrais comuns 🟢 |
| `_mermaid_sid` | `mermaid_render.py:26` | `(raw)` | `str` | Id seguro, prefixo `N_` 🟢 |
| `_mermaid_label` | `mermaid_render.py:50` | `(txt)` | `str` | Lista branca + entidades HTML 🟢 |
| `generate_mermaid_graph` | `mermaid_render.py:63` | `(path, p1_id, p2_id, common_ancestor_id)` | `str` | Diagrama direto 🟢 |
| `generate_mermaid_graph_indirect_bridge` | `mermaid_render.py:112` | `(p1_id, p2_id, person_path)` | `str` | Diagrama de ponte 🟢 |

### Constantes

| Constante | Valor | Onde | Papel |
| --- | --- | --- | --- |
| `MAX_DEPTH` | `20` | `path_finding.py:25` | Iterações de profundidade do BFS bidirecional. ⚠️ **Interpolado no aviso `sem_caminho`** 🟢 |
| `MAX_HOPS` | `40` | `path_finding.py:28` | Arestas máximas do caminho indireto 🟢 |
| `MAX_DEPTH_ALTERNATIVOS` | `12` | `documentary_relationship.py:47` | Teto da enumeração de ancestrais comuns 🟢 |
| `LIMITE_DE_CADEIAS` | `8` | `documentary_relationship.py:48` | Teto da contagem de cadeias (colapso) 🟢 |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | `12` / `70` | `documentary_relationship.py:41-42` | Faixa plausível; **não** é regra biológica, é filtro de evidência 🟢 |
| `LIMITE_DE_CANDIDATOS` | `5` | `path_search.py:71` | Teto por lado nas combinações com homônimos 🟢 |
| `_LABEL_SEGURO` | regex de lista branca | `mermaid_render.py:47` | Documentada **no próprio código**, com os dois bugs que a moldaram 🟢 |

### Contrato de retorno

| Campo de `path_result` | Conteúdo | Conf. |
| --- | --- | --- |
| `person1_name` / `person2_name` | Nomes já com `strip()` | 🟢 |
| `text_path` | Nomes do caminho unidos por `" → "` | 🟢 |
| `mermaid_data` | Texto do diagrama Mermaid | 🟢 |
| `documentary` | Resultado completo do parentesco documental, com `status`, `label`, `relationship_key`, `meioses`, `degrees`, fichas, evidência e avisos | 🟢 |
| `observations` | Avisos do documental, deduplicados, mais o aviso de afinidade | 🟢 |

## Fluxo Principal

### Camada de rota (`app.py:131-174`)

1. `:126-131` — recupera `gedcom_filename`, valida presença e **forma**, resolve o caminho em disco. 🟢
2. `:132` — **re-parseia o GEDCOM** e reconstrói o grafo, antes de ramificar. 🟢
3. `:156-159` — `action == "path_search"`; lê `person1_name` e `person2_name` **com `strip()`**. 🟢
4. `:161` — `path_search_flow(person1_name, person2_name)`. 🟢
5. `:162-164` — `not success and path_result is None` → renderiza com a mensagem, `success=False`. 🟢
6. `:165-166` — caso contrário → renderiza com `path_result` e `success=True`. 🟢
7. `:167-169` — exceção → `"Ocorreu um erro: {e}"`, `success=False`. 🟢

> **Assimetria de contrato:** "sem conexão" devolve `(None, msg, True)` e cai no ramo `success=True` — ou seja, o template recebe `path_result=None` **com** sucesso. É o único caso do sistema em que ausência de resultado **não** é erro. 🟢

### Núcleo — `path_search` (`path_search.py:126-202`)

1. `:133-134` — `strip()` nos dois nomes. 🟢
2. `:136-141` — resolve as duas listas de ids; lista vazia → `"Pessoa N '{nome}' não encontrada."` com `success=False`. 🟢
3. `:143` — `_homonimos(...)` monta o dossiê dos dois lados. 🟢
4. `:150-151` — `_candidatos(...)` devolve o dossiê e a **lista** de candidatos de cada lado. 🟢
5. `:152-163` — laço aninhado com teto de **5 × 5**, em cache: vence a **primeira** combinação que tiver caminho. 🟢
6. `:165-167` — sem nenhuma combinação com caminho, usa o primeiro id de cada lado e calcula o parentesco uma vez. 🟢
7. `:169-176` — **com caminho direto**: nomes, `generate_mermaid_graph` e `"Conexão direta encontrada (ancestral comum)."` 🟢
8. `:177-182` — **sem caminho direto**: tenta `find_indirect_path`; sem caminho → `(None, "Nenhuma conexão encontrada entre '{p1}' e '{p2}'.", True)`. 🟢
9. `:183-192` — **com caminho indireto**: nomes, `generate_mermaid_graph_indirect_bridge`, e a **marcação de afinidade em três lugares** — `status = "affinity"` numa **cópia** do dicionário, rótulo próprio e o `AVISO_AFINIDADE` em maiúsculas. 🟢
10. `:194-202` — monta `path_result` com `text_path` unido por `" → "` e devolve com `success=True`. 🟢

> ⚠️ **A marcação de afinidade é feita numa cópia** (`documental = dict(documental)` em `:186`). O dicionário original continua `not_found`. Nenhum consumidor atual usa o original depois disso, mas a divergência entre duas referências ao "mesmo" resultado é armadilha para quem reimplementar (`M-01` em `state-machines.md`). 🟢

### BFS bidirecional (`find_ancestral_path`, `path_finding.py:51-85`)

1. `:53-56` — duas fronteiras (`deque`) e dois conjuntos de visitados. 🟢
2. `:58-59` — `start == end` → devolve a própria pessoa como caminho e como ancestral. 🟢
3. `:60-72` — **turno 1:** expande **um nível** do lado 1 subindo por `get_parents`; se algum nó recém-expandido já está no visitado do lado 2, o caminho é `caminho_até_ele + caminho_do_outro_lado_invertido_sem_repetir_o_encontro`. 🟢
4. `:73-84` — **turno 2:** mesma lógica do lado 2. 🟢
5. `:85` — teto atingido sem interseção → `(None, None)`. 🟢

### Caminho indireto (`find_indirect_path`, `path_finding.py:31-48`)

1. `:38` — `from .gedcom_state import graph` **dentro da função** — capta o rebind da global. 🟢
2. `:39-40` — grafo ausente ou nó inexistente → `None`. 🟢
3. `:41-44` — `nx.shortest_path` (BFS não ponderado) com captura de `NetworkXNoPath` e `NodeNotFound`. 🟢
4. `:45-46` — `len(caminho) - 1 > max_hops` → `None`. 🟢
5. `:47-48` — remove os nós de família; menos de 2 pessoas → `None`. 🟢

### Parentesco documental (`documentary_relationship.py:436-568`)

1. `:443-446` — registro ausente → `status = "not_found"` + aviso `pessoa_ausente`. 🟢
2. `:448` — `find_ancestral_path(a, b, max_depth=MAX_DEPTH)`. 🟢
3. `:452-484` — sem caminho → `status = "not_found"` + aviso `sem_caminho` (e `homonimo`, se o dossiê for ambíguo). 🟢
4. `:486-488` — graus: posições do ancestral comum no caminho, de cada lado. 🟢
5. `:488` — `documentary_label(deg_a, deg_b)` → rótulo, chave canônica e meioses. 🟢
6. `:490-495` — `hop_evidence` por aresta do caminho, na direção correta. 🟢
7. `:497-507` — `plausible is False` → aviso `data_impossivel`; **o caminho é mantido**. 🟢
8. `:509-525` — enumera todos os ancestrais comuns e monta os caminhos alternativos; havendo, aviso `caminhos_multiplos`. 🟢
9. `:527-539` — conta cadeias por ancestral; mais de uma → aviso `colapso_de_pedigree`. 🟢
10. `:541-549` — identidade ambígua → aviso `homonimo`. 🟢
11. `:551-568` — devolve o resultado completo, com `status = "ambiguous"` quando há ambiguidade e `"found"` caso contrário. 🟢

### Tradução de graus (`documentary_label`, `:290-340`)

| Condição | Rótulo | Chave canônica |
| --- | --- | --- |
| Ambos os graus zero | mesma pessoa | `SELF` 🟢 |
| Um dos graus zero, `n = 1` | Pai/Mãe | `PARENT_CHILD` 🟢 |
| Um dos graus zero, `n = 2` | Avô/Avó | `GRANDPARENT` 🟢 |
| Um dos graus zero, `n > 2` | prefixo `bis` repetido `n−2` vezes | — 🟢 |
| Menor grau 1, maior grau 1 | Irmãos | `SIBLINGS` 🟢 |
| Menor grau 1, maior grau 2 | Tio/Tia | `AUNT_UNCLE` 🟢 |
| Menor grau 1, maior grau > 2 | Tio/Tia com `bis` repetido | `GREAT_AUNT_k` 🟢 |
| Demais | Primos de `g` grau com `r` remoções | `gC` ou `gCrR`, com `g = menor−1` e `r = maior−menor` 🟢 |

### Escape do rótulo (`mermaid_render.py:26-60`)

1. `:26-31` — `_mermaid_sid`: coleção → primeiro elemento; remove `@`; troca `+` por `_`; remove tudo fora de `[A-Za-z0-9_]`; prefixa `N_`. 🟢
2. `:50-58` — `_mermaid_label`: NFC → NBSP/travessões/aspas curvas normalizados → `"` vira `'` → quebras de linha achatadas. 🟢
3. `:59` — `_LABEL_SEGURO.sub('', s)` — **lista branca** remove o que sobra. 🟢
4. `:60` — **por último**, `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`. 🟢

> ⚠️ **A ordem dos passos 3 e 4 é invariante do contrato.** Se a conversão em entidades vier antes do filtro, o filtro pode remover pedaços da própria entidade já escapada. Não reordenar (`adrs/05`). 🟢

## Fluxos Alternativos

| Condição | Comportamento | Conf. |
| --- | --- | --- |
| Pessoa 1 ou 2 não resolvida | `"Pessoa N '{nome}' não encontrada."` com `success=False` | 🟢 |
| Homônimos sem nenhuma combinação com caminho | Usa o primeiro id de cada lado; o resultado sai marcado como ambíguo | 🟢 |
| Sem conexão direta nem indireta | `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` com **`success=True`** | 🟢 |
| Caminho mais fundo que `MAX_DEPTH` | Corte **silencioso**; o aviso diz que isso **não prova** ausência de parentesco | 🟢 |
| Caminho indireto com mais de `MAX_HOPS` arestas | Rejeitado — indistinguível de "sem caminho" | 🟢 |
| Pessoas idênticas | Caminho trivial; a pessoa é o próprio ancestral | 🟢 |
| `FAMS` parcialmente resolvido | **O fallback não roda**, e cônjuges legítimos podem faltar — contrato aceito em 2026-09-30 | 🟢 |
| Sem cônjuges no caminho indireto | O diagrama de ponte delega para o diagrama direto | 🟢 |
| Idade de genitor fora de 12–70 | Aviso `data_impossivel`; vínculo mantido | 🟢 |
| Colapso fora do teto de 12 níveis / 8 cadeias | **Não detectado** — e o silêncio é idêntico a "não há colapso" | 🟡 |
| Exceção inesperada | `"Ocorreu um erro: {e}"` com `success=False` | 🟢 |

## Dependências

| Dependência | Versão | Como usa | Conf. |
| --- | --- | --- | --- |
| **networkx** | 3.6.1 | `nx.Graph`, `nx.shortest_path`, `NetworkXNoPath`, `NodeNotFound` | 🟢 |
| Unit `upload-gedcom` | — | `people`, `families`, `child_to_family`, `get_name`, `ref_id` e a global **reatribuída** `graph` | 🟢 |
| `utils/text_cleaning` | — | Mojibake na comparação de nomes (`normalizar`) | 🟢 |
| `templates/index.html` | — | Renderiza o diagrama; Mermaid com `securityLevel: 'strict'` | 🟢 |
| Unit `analise-dna` | — | **Depende desta**: usa `documentary_relationship`, `family_navigation`, `path_finding` e `mermaid_render` | 🟢 |

> 🔴 **Inversão de camada registrada:** `reporting/mermaid_render.py` importa `core.family_navigation`, `core.path_finding` e `core.gedcom_state`. O renderizador **navega o domínio** para decidir *como desenhar* — há decisão de negócio dentro da apresentação (`architecture.md` §3, `c4-components.md`). 🟢

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
| --- | --- | --- |
| Direta primeiro, indireta como fallback — **nunca as duas** | `path_search.py:172-192` | 🟢 |
| BFS bidirecional **manual**, em vez de `nx.lowest_common_ancestor`, porque a subida é restrita às arestas de paternidade | `path_finding.py:51-85` | 🟢 |
| **Escolha entre homônimos por teste de combinações** (5×5, em cache), e não pelo primeiro id | `path_search.py:152-167` | 🟢 |
| O dossiê compara **sem acento**, e não com acento como `find_person_by_name` | `documentary_relationship.py:150-161` | 🟢 |
| Ambigüidade **avisada** em vez de silenciosa | `documentary_relationship.py:541-549` | 🟢 |
| Compressão dos nós de família no caminho indireto | `path_finding.py:47-48` | 🟢 |
| **Import tardio** da global `graph`, para captar a reatribuição | `path_finding.py:38` | 🟢 |
| `get_spouses` faz varredura global **apenas** se `FAMS` ficar vazio — fallback total, não complemento | `family_navigation.py:66-75` | 🟢 |
| **Data não invalida vínculo**: registra evidência e avisa | `documentary_relationship.py:497-507` | 🟢 |
| Afinidade marcada em **três lugares** (redundância deliberada) | `path_search.py:186-192`, `:66-67` | 🟢 |
| **Afinidade é atribuída a uma cópia** do dicionário | `path_search.py:186` | 🟢 |
| Lista **branca** no rótulo, com entidades **depois** do filtro | `mermaid_render.py:47`, `:59-60` | 🟢 |
| `subgraph` fechado por **context manager** | `mermaid_render.py:160-175` | 🟢 |
| Indexação `nome → ids` invalidada por `versao`, e não por tamanho | `documentary_relationship.py:185-202` | 🟢 |
| `get_children` varre todas as famílias, sem índice | `documentary_relationship.py:112-124` | 🟢 |

## Estado Interno

| Estado | Escopo | Observação | Conf. |
| --- | --- | --- | --- |
| `people`, `families`, `graph`, `child_to_family` | global do processo | Produzidos pelo upload; **lidos** aqui | 🟢 |
| `versao` | global do processo | Invalida o índice `nome → ids` | 🟢 |
| Índice `{"versao", "mapa"}` | cache de módulo | Reconstruído só quando `versao` muda | 🟢 |
| `cache` de pares `(cand1, cand2)` | local da requisição | Evita recalcular o parentesco na busca por combinações | 🟢 |
| `path_result` | local da requisição | Renderizado e descartado | 🟢 |

> **Nada é persistido** e não há sessão. A busca sempre opera sobre a árvore re-parseada **nesta** requisição, a partir da chave recebida no formulário. 🟢

## Observabilidade

- **Nenhum `logging`, métrica ou trace é emitido.** 🔴
- As mensagens de resultado e de erro, o texto do caminho e os avisos são o **único** sinal ao usuário. 🟢
- O contrato de escape tem **evidência própria fora da aplicação**: `tests/test_mermaid_escape.py`, o fuzz de **288 payloads** combinados e a varredura de **30.000 nomes**, registrados no adendo `bug-BUG-20260929-J6PQ`. 🟢

## Riscos e Lacunas

- 🔴 **O `reporting/` contém decisão de negócio.** O renderizador usa `get_spouses`, `pick_spouse_for_couple`, `split_path_by_marriage` e `exclude_tail` para decidir **como desenhar**. Trocar a apresentação muda a leitura do parentesco. Não há decisão humana registrada sobre manter essa fronteira. 🟢
- 🔴 **`get_children` varre todas as famílias sem índice**, e `person_a`/`person_b` são **fichas completas** em cada resultado (142 fichas nos 71 casos reais). Custo real, sem limite medido (`L-20`). 🟢
- 🔴 **Colapso de pedigree além do teto não é detectado**, e o aviso não distingue "sem colapso" de "colapso fora do alcance". 🟡
- 🟡 **O `MAX_DEPTH` está interpolado na mensagem** do aviso `sem_caminho`: mudar o teto muda **texto de contrato** (`spec-impact-matrix.md` §5). 🟢
- 🟡 **O corte silencioso do `MAX_DEPTH` é decisão humana** de 2026-09-30 (preservar fidelidade, sem sinalização). A consequência aceita: uma árvore com mais de ~20 níveis faz a conexão direta falhar em silêncio e cair para a busca indireta, que pode achar um laço por afinidade **sem significado genealógico**. 🟢
- 🟡 **A varredura condicional de `get_spouses` é contrato**, não descuido: com `FAMS` parcialmente resolvido, cônjuges legítimos podem faltar e o fallback **não** corrige. Torná-la complementar **muda o resultado** da busca indireta e das pontes. 🟢
- 🟡 **`split_path_by_marriage` acha só o primeiro par de cônjuges**; caminhos com múltiplas afinidades renderizam de forma simplificada. 🟡
- 🟡 **O caminho indireto não passa pela checagem de plausibilidade de datas** — a faixa 12–70 só é aplicada ao caminho **direto**. 🟡
- 🟢 **`L-06` RESOLVIDA em 2026-10-05 por verificação no template.** O receio era que "sem conexão" e "erro" fossem indistinguíveis por terem a mesma forma de `path_result`. **Não são:** `index.html:43-45` decide a **cor do alerta** por `success` (`'success' if success else 'danger'`) e `:457` decide se o **cartão de resultado** aparece, por `path_result`. Os três desfechos — conexão, sem conexão e erro — produzem telas visualmente distintas. Deixou de ser lacuna. 🟢
- 🟢 **Resolvido por decisão de produto anterior:** o vazamento de gramática Mermaid por aspa dupla + crase (`BUG-20260929-J6PQ`) e o descarte de 14 caracteres inertes (`BUG-20261002-T4ZM`), ambos com teste de regressão. 🟢

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*
