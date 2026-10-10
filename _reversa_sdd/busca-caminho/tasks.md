# Unit `busca-caminho` — Tarefas de Implementação

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Substitui as tasks de 2026-10-05, que previam o grafo por **import tardio** e o índice invalidado por `gedcom_state.versao` — **nenhum dos dois existe mais**.
> Cada tarefa cita o arquivo do legado de onde o comportamento foi extraído.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] Dependências **pinadas**: `networkx==3.7`, `Flask==3.1.3` 🟢
- [ ] Unit `upload-gedcom` implementada: a **árvore como valor** `(people, families, graph, child_to_family)`, `get_name` e `ref_id` disponíveis 🟢
- [ ] Unit `tela-de-entrada` implementada: `_arvore_do_formulario` (guarda de entrada) 🟢
- [ ] A autoridade única de limpeza de nome disponível para a comparação sem acento do dossiê 🟢
- [ ] `application/traducao.py` disponível — a tabela de tradução é **compartilhada** com as outras units 🟢
- [ ] `templates/index.html` renderizando Mermaid com `securityLevel: 'strict'` 🟢
- [ ] **Não aplicável:** schema, migrations ou banco de dados 🟢
- [ ] ⚠️ **A árvore entra por parâmetro em todo o caminho.** Não existe mais `gedcom_state` nem global reatribuída — nenhuma tarefa desta unit pode depender de estado de processo 🟢

## Tarefas

### Entrada e resolução de pessoas

- [ ] T-01, Fazer `strip` nos dois nomes antes de qualquer coisa
  - Origem no legado: `src/core/path_search.py:130-131`
  - Critério de pronto: nome com espaços nas pontas resolve como o nome limpo, e o resultado carrega o nome já limpo
  - Confiança: 🟢

- [ ] T-02, Implementar `find_person_by_name` em duas passadas
  - Origem no legado: `src/core/family_navigation.py:find_person_by_name`
  - Critério de pronto: igualdade sem diferenciar maiúsculas primeiro; substring só se a igualdade não devolver nada; devolve **todos** os ids que casam
  - Confiança: 🟢

- [ ] T-03, Reportar por pessoa quando o nome não resolve
  - Origem no legado: `src/core/path_search.py:136-138`
  - Critério de pronto: `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 '{nome}' não encontrada."` com `success = False`
  - Confiança: 🟢

- [ ] T-04, Implementar `homonym_dossier` comparando **sem acento** e corrigindo mojibake
  - Origem no legado: `src/core/documentary_relationship.py:normalizar`, `homonym_dossier`
  - Critério de pronto: um nome sem acento encontra o registro com acento; `ambiguous` verdadeiro com mais de um exato **ou** com `similar_ids` não vazio; devolve **todos** os registros, sem escolher
  - Confiança: 🟢
  - ⚠️ A diferença em relação a `find_person_by_name` é **deliberada**: uma compara com acento, a outra sem, e é isso que recupera os homônimos que só diferem na acentuação

- [ ] T-05, Montar `_candidatos` unindo os ids do legado aos exatos, sem repetir e preservando a ordem
  - Origem no legado: `src/core/path_search.py:_candidatos`
  - Critério de pronto: os ids do legado vêm primeiro, os exatos entram sem duplicar, e os "parecidos" entram **apenas** como `similar_matches`, limitados a 5
  - Confiança: 🟢

- [ ] T-06, Montar `_homonimos` agregando **só os lados ambíguos**
  - Origem no legado: `src/core/path_search.py:_homonimos`
  - Critério de pronto: o rótulo e a contagem falam apenas do lado ambíguo; `ambiguous` verdadeiro se **qualquer** lado for ambíguo; `{}` quando não há ambiguidade nem parecidos, e a seção não aparece na tela
  - Confiança: 🟢

- [ ] T-07, Testar até **5 × 5** combinações, com cache, vencendo a primeira **com caminho**
  - Origem no legado: `src/core/path_search.py:LIMITE_DE_CANDIDATOS`, `path_search`
  - Critério de pronto: cache de pares `(cand1, cand2) -> documental`; vence a primeira cujo `path.ids` existe — **não** a de menor distância; sem nenhuma, usa o primeiro id de cada lado
  - Confiança: 🟢
  - ⚠️ **Isto substitui a decisão de 2026-08-03** ("homônimos usam o 1º ID"): a decisão continua acolhida como **recuo**, mas deixou de ser o comportamento principal. O caso medido que motivou a mudança está no próprio código

### Navegação familiar

- [ ] T-08, Implementar `get_parents` com `FAMC` preferencial e fallback no índice
  - Origem no legado: `src/core/family_navigation.py:get_parents`
  - Critério de pronto: usa o `FAMC` do registro quando existe; só sem ele consulta o índice filho→famílias; coleta `HUSB` e `WIFE` de **todas** as famílias do `FAMC`, sem duplicar
  - Confiança: 🟢

- [ ] T-09, Implementar `get_spouses` com o fallback **condicional**
  - Origem no legado: `src/core/family_navigation.py:get_spouses`
  - Critério de pronto: caminho por `FAMS`; a varredura global de `families` só roda se a lista ficou **vazia**
  - Confiança: 🟢
  - ⚠️ Reproduzir a condicional **exatamente**. Com um `FAMS` que resolve e outro que não, o fallback **não roda** e o cônjuge da segunda família desaparece. Torná-la complementar **muda o resultado** da busca indireta e das pontes

- [ ] T-10, Implementar `are_spouses`, `split_path_by_marriage`, `pick_spouse_for_couple` e `exclude_tail`
  - Origem no legado: `src/core/family_navigation.py`
  - Critério de pronto: `are_spouses` por pertinência em `set(get_spouses(...))`; `split_path_by_marriage` no **primeiro** par adjacente; `pick_spouse_for_couple` prefere o cônjuge presente no caminho, senão o primeiro; `exclude_tail(seq, n=1)` devolve `[]` quando `len(seq) <= n`
  - Confiança: 🟢

### Conexão direta

- [ ] T-11, Implementar o BFS **bidirecional** por pais (`find_ancestral_path`)
  - Origem no legado: `src/core/path_finding.py:find_ancestral_path`
  - Critério de pronto: duas fronteiras alternando **um nível de um lado** por iteração; o encontro é o nó que já consta no visitado do outro lado; o caminho **não repete** o ponto de encontro; `a == b` devolve `([a], a)`
  - Confiança: 🟢
  - ⚠️ O teto `MAX_DEPTH = 20` conta **iterações de profundidade**, não gerações. **Não reinterpretar.** Não há pesos nem limiares: o caminho é o primeiro encontrado, e a ordem de inserção das arestas é contrato de paridade

- [ ] T-12, Implementar o corte **silencioso** no teto
  - Origem no legado: `src/core/path_finding.py:MAX_DEPTH`
  - Critério de pronto: nenhum caminho dentro do teto → `(None, None)`, **sem** erro e **sem** sinalizar que o limite foi atingido
  - Confiança: 🟢
  - ⚠️ Decisão humana de 2026-09-30: preservar a fidelidade ao legado. **Não acrescentar aviso nem distinguir "limite atingido" de "sem caminho"**

### Conexão indireta

- [ ] T-13, Implementar `find_indirect_path` com caminho mais curto, compressão e o grafo **recebido**
  - Origem no legado: `src/core/path_finding.py:find_indirect_path`
  - Critério de pronto: `nx.shortest_path` **não ponderado**; rejeita se `len(caminho) − 1 > MAX_HOPS`; devolve **apenas ids de pessoa**; exige ≥ 2; o grafo vem da **árvore recebida por parâmetro**
  - Confiança: 🟢
  - ⚠️ **Não existe mais import tardio nem global reatribuída.** Um import de estado de processo aqui reintroduz o defeito que a `BR-C-08` eliminou

- [ ] T-14, Tratar `NetworkXNoPath`, `NodeNotFound`, grafo ausente e nó ausente como ausência de caminho
  - Origem no legado: `src/core/path_finding.py:find_indirect_path`
  - Critério de pronto: todos os quatro casos devolvem `None`, nunca propagam
  - Confiança: 🟢

- [ ] T-15, Marcar a conexão indireta como **afinidade em três lugares**
  - Origem no legado: `src/core/path_search.py:AVISO_AFINIDADE`, `path_search`
  - Critério de pronto: `status = "affinity"` numa **cópia** do dicionário; rótulo `"Sem ancestral comum: conexão por afinidade (casamento)"`; o aviso afirma em **maiúsculas** que **não** representa parentesco consanguíneo; a observação é acrescentada ao resultado; `relationship_key` permanece `None`; `affinity_path` traz o traço do caminho
  - Confiança: 🟢
  - ⚠️ A marcação é feita numa **cópia**. Preservar isso; não mutar o dicionário do cache

### Parentesco documental

- [ ] T-16, Implementar `documentary_relationship` com as guardas de pessoa ausente e sem caminho
  - Origem no legado: `src/core/documentary_relationship.py:documentary_relationship`
  - Critério de pronto: registro ausente → `status="not_found"` + `pessoa_ausente`; sem caminho → `status="not_found"` + `sem_caminho`, cuja mensagem **interpola `MAX_DEPTH`** e afirma que isso **não prova** ausência de parentesco, mais `homonimo` quando o dossiê for ambíguo
  - Confiança: 🟢
  - ⚠️ `MAX_DEPTH` dentro do texto é **contrato**: mudar o teto muda a mensagem

- [ ] T-17, Implementar `documentary_label` com os graus, a chave canônica e as meioses
  - Origem no legado: `src/core/documentary_relationship.py:documentary_label`
  - Critério de pronto: `(0,0)` → `SELF`; um lado zero → linha direta com `bis` repetido `n−2` vezes; menor grau 1 → irmãos, tio/tia, tio/tia-avô; demais → `gC` ou `gCrR` com `g = menor−1` e `r = maior−menor`; `meioses = deg_a + deg_b` sempre
  - Confiança: 🟢

- [ ] T-18, Implementar `hop_evidence` com a idade implícita e o aviso de data impossível
  - Origem no legado: `src/core/documentary_relationship.py:hop_evidence`
  - Critério de pronto: localiza a família por `FAMC` e, sem ele, pelo índice filho→famílias; sem família localizada, `link_source` diz isso; devolve o casal declarado e as datas; `age_at_birth = ano_do_filho − ano_do_genitor`; fora de **12–70** → `plausible: False` + aviso `data_impossivel`; **sem data**, `plausible` é `None`
  - Confiança: 🟢
  - ⚠️ **Nenhuma data invalida vínculo.** O caminho é mantido como o GEDCOM o declara. `None` **não** é falso

- [ ] T-19, Implementar `parse_year`
  - Origem no legado: `src/core/documentary_relationship.py:parse_year`
  - Critério de pronto: extrai o **primeiro** número de 3 ou 4 dígitos; `ABOUT`/`BEFORE`/`AFTER` são tolerados e **não** normalizados
  - Confiança: 🟢

- [ ] T-20, Implementar `person_summary` com a ficha de **13 campos**
  - Origem no legado: `src/core/documentary_relationship.py:person_summary`
  - Critério de pronto: `id`, `name`, `sex`, `birth`, `birth_year`, `birth_place`, `death`, `death_year`, `parents`, `parent_names`, `spouses`, `children`, `family_as_child`
  - Confiança: 🟢
  - 🔴 `get_children` **não tem índice**: cada chamada percorre todas as famílias. Registrar o custo, não "otimizar" sem medição

- [ ] T-21, Implementar `_diferencas` e `identical_data`
  - Origem no legado: `src/core/documentary_relationship.py:_diferencas`, `homonym_dossier`
  - Critério de pronto: compara data e local de nascimento, data de falecimento, pais, filhos e sexo; `identical_data` verdadeiro só com **mais de um** registro e **nenhum** campo divergente
  - Confiança: 🟢
  - 🟡 `_diferencas` é chamado **duas vezes** (uma para `differences`, outra dentro de `identical_data`), e cada chamada remonta as fichas. O comentário do código fala em "UMA vez", o que vale **dentro** de uma chamada

- [ ] T-22, Enumerar todos os ancestrais comuns e listar os caminhos alternativos
  - Origem no legado: `src/core/documentary_relationship.py:find_all_common_ancestors`
  - Critério de pronto: até `MAX_DEPTH_ALTERNATIVOS` (12) níveis, limitado a 12, ordenado por `(meioses totais, maior distância, nome)`; caminhos alternativos listados e **nenhum descartado**; aviso `caminhos_multiplos` declarando que o exibido é o de menor distância total
  - Confiança: 🟢
  - 🟡 **O empate nos três critérios herda a ordem do `set`** — a varredura parte de `set(de_a) & set(de_b)`. A ordem pode variar com o `PYTHONHASHSEED`. O `matching` de `analise-dna` fechou essa classe de defeito com um quarto critério determinístico; **aqui ela segue aberta** (`L-25`)

- [ ] T-23, Detectar colapso de pedigree e marcar identidade ambígua
  - Origem no legado: `src/core/documentary_relationship.py:_cadeias_ate`, `documentary_relationship`
  - Critério de pronto: mais de uma cadeia até o mesmo ancestral (teto `LIMITE_DE_CADEIAS = 8`) → aviso `colapso_de_pedigree` com o ancestral e a contagem; dossiê ambíguo → `status = "ambiguous"` **havendo caminho** e aviso `homonimo`
  - Confiança: 🟢
  - ⚠️ A contagem é um **piso**: ela para no teto. E a ambiguidade **não** rebaixa `not_found` (`M-02`)

- [ ] T-24, Implementar o índice `nome → ids` com a **chave derivada do conteúdo**
  - Origem no legado: `src/core/documentary_relationship.py:_chave_de`, `_indice_por_nome`
  - Critério de pronto: `_chave_de(people)` devolve `(len(people), chaves[0], chaves[-1])` com `chaves = sorted(people)`; o índice de módulo é reconstruído quando a chave muda
  - Confiança: 🟢
  - 🔴 **A chave tem colisão possível** (`L-24`/`E-05`): dois GEDCOMs do mesmo tamanho e com os mesmos xrefs extremos reaproveitam o índice anterior, e o dossiê passa a listar xrefs de outra árvore, **sem exceção**. `id()` **não** serve como chave — é reciclado. **[Verificar]** antes de reimplementar: a correção mínima é acrescentar à chave algo derivado do conteúdo

### Diagrama

- [ ] T-25, Implementar o **resolvedor de diagrama** — sete consultas ligadas à árvore
  - Origem no legado: `src/core/diagram_domain.py:resolvedor_de_diagrama`
  - Critério de pronto: devolve um `dict` com as sete consultas já ligadas à árvore; `reporting/` **não importa `core`**; o renderizador continua chamando `get_spouses(pid)`, e não `get_spouses(arvore, pid)`
  - Confiança: 🟢
  - ⚠️ É o que **fecha o ciclo `core/` ↔ `reporting/`** (`ADR-34`). As decisões de **layout continuam no renderizador** (`ADR-11`) — o resolvedor move o acesso ao domínio, não a decisão de desenho

- [ ] T-26, Implementar `_mermaid_sid`
  - Origem no legado: `src/reporting/mermaid_render.py:_mermaid_sid`
  - Critério de pronto: coleção → primeiro elemento; remove `@`; `+` → `_`; remove tudo fora de `[A-Za-z0-9_]`; prefixa `N_`
  - Confiança: 🟢

- [ ] T-27, Implementar `_mermaid_label` com **lista branca** e a ordem correta
  - Origem no legado: `src/reporting/mermaid_render.py:_mermaid_label`, `_LABEL_SEGURO`
  - Critério de pronto: NFC → NBSP/travessões/aspas curvas normalizados → `"` vira `'` → quebras de linha achatadas → **lista branca** → **depois** `&`, `<`, `>` como entidades
  - Confiança: 🟢
  - ⚠️ **A ordem é o contrato.** Filtro antes das entidades. Inverter reintroduz o `BUG-20260929-J6PQ`. E o critério é **INERTE**, não "seguro": o que não pode passar é a aspa dupla e a crase

- [ ] T-28, Emitir o diagrama da conexão **direta**
  - Origem no legado: `src/reporting/mermaid_render.py:generate_mermaid_graph`
  - Critério de pronto: `flowchart BT`; linhagem direta é `ac_idx` em `-1`, `0` ou no último nó; **fora disso** o MRCA vira um nó de **casal**, e os dois membros são **omitidos** como nós próprios; arestas na direção correta; cores por papel (p1 verde, p2 vermelho, MRCA/casal amarelo)
  - Confiança: 🟢

- [ ] T-29, Emitir o diagrama da conexão **indireta** em subgrafos
  - Origem no legado: `src/reporting/mermaid_render.py:generate_mermaid_graph_indirect_bridge`
  - Critério de pronto: subgrafos **aninhados** (`COLUMNS`, `ESQ`/`DIR`, `*_COLS`, `*_L`, `*_R`) todos com `direction BT`; o casamento é aresta rotulada entre **âncoras invisíveis** (estilo transparente), não seta de filiação; cores de A e B; **`end` escrito pelo fim de um context manager**; delegação para o diagrama direto com `mrca=None` quando faltar par de cônjuges ou um dos ramos
  - Confiança: 🟢
  - ⚠️ Um `end` a mais ou a menos muda a árvore do diagrama **sem levantar erro**. É por isso que o fechamento é estrutural, e não posicional. O `sid` do casal usa os dois ids **ordenados** unidos por `+`, logo é independente da ordem recebida

### Fluxo e fronteira

- [ ] T-30, Montar o `path_result` com o resultado documental e as observações deduplicadas
  - Origem no legado: `src/core/path_search.py:path_search`
  - Critério de pronto: `person1_name`, `person2_name`, `text_path` unido por `" → "`, `mermaid_data`, `documentary` e `observations` sem repetição
  - Confiança: 🟢

- [ ] T-31, Orquestrar direta → indireta, com precedência da direta
  - Origem no legado: `src/core/path_search.py:path_search`
  - Critério de pronto: conexão com ancestral comum **nunca** é reportada como indireta; as duas mensagens de sucesso são exatas: `"Conexão direta encontrada (ancestral comum)."` e `"Conexão indireta encontrada (via casamento/afinidade)."`
  - Confiança: 🟢

- [ ] T-32, Distinguir ausência de conexão de erro de entrada na **tupla** do núcleo
  - Origem no legado: `src/core/path_search.py:path_search`
  - Critério de pronto: sem conexão → `(None, "Nenhuma conexão encontrada entre '{p1}' e '{p2}'.", True)`; pessoa não encontrada → `(None, msg, False)`
  - Confiança: 🟢
  - ⚠️ A tupla de **três** elementos é **contrato de paridade**: o harness compara o indicador de sucesso contra o oráculo, e nove asserções de teste a desempacotam. **Não mudar a forma**

- [ ] T-33, Definir o enum `Desfecho` e derivá-lo de `(payload, sucesso)`
  - Origem no legado: `src/application/__init__.py:Desfecho`; `src/application/path_search.py:_desfecho`
  - Critério de pronto: payload presente → `RESULTADO`; sem payload e com sucesso → `SEM_RESULTADO`; sem payload e sem sucesso → `ERRO_DE_ENTRADA`. **Nunca do texto da mensagem.** Sem quarto valor: entrada inválida que não vem do núcleo já é exceção de domínio
  - Confiança: 🟢
  - ⚠️ Sem o enum, o adaptador teria de distinguir os dois últimos pelo **texto**, dando ao literal de tela autoridade semântica

- [ ] T-34, Devolver `ResultadoDeBusca` congelado, com `dados` **sem renomear**
  - Origem no legado: `src/application/path_search.py:ResultadoDeBusca`
  - Critério de pronto: `desfecho`, `dados`, `mensagem`; o campo **não** se chama `path_result`, porque nome de campo de template não atravessa a fronteira; o adaptador decide sob que nome (se algum) ele vai ao template
  - Confiança: 🟢

- [ ] T-35, Receber as dependências de diagrama **por parâmetro** e manter `dono` sem comportamento
  - Origem no legado: `src/application/path_search.py:path_search`
  - Critério de pronto: o caso de uso **não** monta a sua própria cópia por requisição; `dono` está na assinatura e **não** participa de decisão nenhuma
  - Confiança: 🟢

- [ ] T-36, Escolher o modo de renderização pelo **desfecho** na rota
  - Origem no legado: `src/app.py:index` (ramo `path_search`)
  - Critério de pronto: `ERRO_DE_ENTRADA` → alerta com `success=False`; `RESULTADO` → cartão com `path_result`; `SEM_RESULTADO` → cartão **sem** `path_result`, com `success=True`. **Nenhum ramo lê o texto da mensagem**
  - Confiança: 🟢

- [ ] T-37, Passar o erro de domínio pela tabela de tradução e tratar a falha inesperada
  - Origem no legado: `src/app.py:index`; `src/application/traducao.py`
  - Critério de pronto: `except ErroDeDominio` → `traduzir(erro).mensagem` com `success=False`; `except Exception` → `"Ocorreu um erro: {e}"` com `success=False`
  - Confiança: 🟢

- [ ] T-38, Declarar em `__all__` **apenas** `path_search`, e compartilhar `nomes_de_exibicao`
  - Origem no legado: `src/core/path_search.py:__all__`; `src/application/__init__.py:nomes_de_exibicao`
  - Critério de pronto: o bloco que reexportava **17 nomes** não existe; `nomes_de_exibicao` é `sorted` sobre `get_name`, compartilhada pelos três fluxos
  - Confiança: 🟢
  - ⚠️ A ordem da lista de nomes é **contrato da tela**

## Tarefas de Teste

- [ ] TT-01, Resolução de pessoa por nome, com igualdade antes de substring 🟢
- [ ] TT-02, Conexão direta trivial (pessoas idênticas) e com ancestral comum 🟢
- [ ] TT-03, Fluxo completo da busca direta, com rótulo, graus e meioses 🟢
- [ ] TT-04, Conexão indireta por casamento, com o status `affinity` 🟢
- [ ] TT-05, `find_indirect_path` isoladamente 🟢
- [ ] TT-06, Pessoa não encontrada, distinguindo Pessoa 1 de Pessoa 2 🟢
- [ ] TT-07, Sem conexão — e com `success=True` 🟢
- [ ] TT-08, **Escolha entre homônimos**: três registros, só um com pais, conexão encontrada e resultado marcado como ambíguo 🟢
- [ ] TT-09, Dossiê recupera registro que difere apenas na acentuação 🟢
- [ ] TT-10, Aviso `data_impossivel` emitido **sem** invalidar o vínculo (caso medido: mãe nascida 11 anos depois do filho) 🟢
- [ ] TT-11, Aviso `colapso_de_pedigree` com ancestral e número de cadeias 🟢
- [ ] TT-12, Caminhos alternativos listados e `caminhos_multiplos` emitido 🟢
- [ ] TT-13, **Escape do rótulo: crase neutralizada**, e nenhum caractere que quebra a gramática sobrevive 🟢
- [ ] TT-14, **Entidades HTML preservadas** e caracteres legítimos intactos 🟢
- [ ] TT-15, Caracterização da saída Mermaid (`tests/test_characterization_mermaid.py`) 🟢
- [ ] TT-16, **Desfecho**: os três valores, derivados de `(payload, sucesso)` (`tests/test_desfecho_do_resultado.py`) 🟢
- [ ] TT-17, **A rota não lê o texto**: mudar a mensagem **não** muda o modo de renderização 🟡
- [ ] TT-18, **O renderizador não importa `core`**: verificação de que `reporting/` não tem import de núcleo (`tests/test_dependencias_nucleo.py`) 🟢
- [ ] TT-19, **A árvore entra por parâmetro**: duas árvores no mesmo processo produzem buscas independentes (`tests/test_arvore_devolvida.py`) 🟢
- [ ] TT-20, **Colisão do cache de nomes**: duas árvores do mesmo tamanho com os mesmos xrefs extremos **não** podem compartilhar o índice — teste que hoje **falharia** (`L-24`) 🔴
- [ ] TT-21, **Determinismo da ordem de `common_ancestors`** com empate nos três critérios (`L-25`) 🔴
- [ ] TT-22, Teto de `MAX_DEPTH` e de `MAX_HOPS` (não existe no legado — criar) 🟡
- [ ] TT-23, `split_path_by_marriage` com múltiplos casamentos no caminho (não existe — cria) 🟡
- [ ] TT-24, Fuzz de rótulo com payloads hostis combinados e varredura de nomes reais — **promover a teste permanente** (hoje vive como evidência do adendo `bug-J6PQ`) 🟡

## Tarefas de Migração de Dados

**Não aplicável** — esta unit não persiste nada: não há banco, schema nem volume a migrar. A persistência histórica existe no projeto, mas é da unit `analise-dna`. 🟢

## Ordem Sugerida

1. **T-08 a T-10 (navegação familiar) primeiro.** São a base do BFS e das pontes, e dependem só dos dicionários da árvore.
2. **T-02 a T-07 (resolução de pessoas e homônimos).** Independentes, testáveis isoladamente.
3. **T-16 a T-24 (parentesco documental).** Dependem de T-08 e T-11; é o bloco que dá conteúdo ao resultado.
4. **T-11 e T-12 (conexão direta).** Dependem de T-08.
5. **T-13 e T-14 (conexão indireta).** Dependem do grafo **recebido** e de T-10.
6. **T-26 e T-27 (escape).** Funções puras: podem ser feitas a qualquer momento, mas **antes** de T-28 e T-29.
7. **T-25 (resolvedor de diagrama)** antes de T-28 e T-29: o renderizador não pode importar `core`, então ele precisa do resolvedor para existir.
8. **T-28 e T-29 (diagramas).** Dependem de T-25, T-27 e T-10.
9. **T-30 a T-32 (núcleo) e depois T-33 a T-37 (fronteira e rota).** O desfecho (T-33) depende da forma da tupla do núcleo (T-32).
10. **T-38 (higiene de módulo)** em qualquer momento.
11. **Bloqueios:** nada aqui funciona sem `upload-gedcom` nem sem `tela-de-entrada`. A unit `analise-dna` depende de T-11, T-16 e do pacote de renderização desta unit. **T-24 depende de decisão humana** (`L-24`).

## Lacunas Pendentes (🔴)

1. **`L-24` / `E-05` — colisão da chave do cache de nomes: CONFIRMADA POR EXECUÇÃO em 2026-10-10, e a correção foi ACEITA.** O experimento (duas árvores de mesmo tamanho e mesmos extremos, carregadas no mesmo processo) fez o dossiê da segunda citar um xref inexistente e degradar em silêncio para `"Sem Nome"`. Detalhe em `design.md` § Riscos. **A execução da correção está agendada para depois do Passo 4**, para não misturar mudança de código com a verificação de regressão. Acrescentar à chave algo derivado do conteúdo; `id()` **não** serve (é reciclado). O teste `TT-20` já está escrito e é ele que passa a valer.
2. **`L-25` — a ordem de `common_ancestors` e `additional_paths` pode variar com o `PYTHONHASHSEED`.** Mesma classe do defeito fechado no `matching`; aqui **aberta**. Decidir se recebe um critério determinístico equivalente (o menor `xref_id`).
3. **`L-20` — `get_children` sem índice e fichas completas por resultado.** Custo real, sem limite medido: 142 fichas para 71 conexões reais.
4. **`M-01` — o estado `affinity` é atribuído a uma cópia** do dicionário; o original segue `not_found`. Armadilha para reimplementação.
5. **`M-02` — a ambiguidade rebaixa `found` para `ambiguous`, mas não rebaixa `not_found`.** Não há indicação de que a assimetria seja intencional.
6. **A contagem de cadeias é truncada em 8**, e o aviso não distingue "sem colapso" de "colapso fora do alcance".
7. **`reporting/` ainda contém decisão de negócio** — decidir o casal do ancestral comum (`ADR-11`). A dependência de `core` foi eliminada; a decisão, não.
8. **`MAX_HOPS` conta arestas do grafo bipartido**, e não passos entre pessoas: o teto efetivo é ≈ metade. Declarar ou renomear.
9. **O caminho indireto não passa pela checagem de plausibilidade de datas**, que existe só no caminho direto.
10. **O fuzz de rótulo (288 payloads) e a varredura de 30.000 nomes não são teste permanente** — vivem como evidência de adendo.

> ✅ **Já decididas, não são pendências:** corte silencioso do `MAX_DEPTH` (2026-09-30, aceito); varredura condicional de `get_spouses` (2026-09-30, contrato); afinidade nunca é consanguinidade; escape por lista branca com entidades depois do filtro; `L-06` fechada por verificação no template (2026-10-05).

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*
