# Unit `busca-caminho` — Tarefas de Implementação

> Unit do tipo **endpoint** — `POST /` com `action=path_search`.
> Re-extração de **2026-10-05** (nível **Completo**). Substitui as tasks de 2026-09-30, que não previam o parentesco documental completo nem a escolha de homônimos por combinações.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] Dependências **pinadas**: `networkx==3.6.1`, `Flask==3.1.3` 🟢
- [ ] Unit `upload-gedcom` implementada: `people`, `families`, `child_to_family`, `get_name` e `ref_id` disponíveis 🟢
- [ ] A global `graph` precisa ser obtida por **import tardio dentro da função** — um import no topo capturaria `None` para sempre, porque o parser a **reatribui** a cada carga 🟢
- [ ] `text_cleaning.demojibake` disponível para a comparação de nomes do dossiê 🟢
- [ ] `templates/index.html` renderizando Mermaid com `securityLevel: 'strict'` 🟢
- [ ] **Não aplicável:** schema, migrations ou banco de dados 🟢

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

### Entrada e resolução de pessoas

- [ ] **T-01**, Validar o GEDCOM e **re-parsear** antes da busca
  - Origem no legado: `src/app.py:131-137`
  - Critério de pronto: sem `gedcom_filename` → `"Erro: Arquivo GEDCOM não encontrado."`; forma inválida ou arquivo removido → `"Erro: Arquivo '{valor}' não existe mais."`; caso contrário, árvore recarregada
  - Confiança: 🟢

- [ ] **T-02**, Implementar `find_person_by_name` em duas passadas
  - Origem no legado: `src/core/family_navigation.py:21-26`
  - Critério de pronto: igualdade sem diferenciar maiúsculas primeiro; substring só se a igualdade não devolver nada
  - Confiança: 🟢

- [ ] **T-03**, Implementar `homonym_dossier` comparando **sem acento** e corrigindo mojibake
  - Origem no legado: `src/core/documentary_relationship.py:150-161`, `:205-226`
  - Critério de pronto: um nome sem acento encontra o registro com acento; `ambiguous` é verdadeiro com mais de um exato; `differences` lista os campos divergentes
  - Confiança: 🟢
  - ⚠️ A diferença em relação a `find_person_by_name` é **deliberada**: uma compara com acento, a outra sem, e é isso que recupera os homônimos que só diferem na acentuação.

- [ ] **T-04**, Montar o dossiê dos **dois** lados e marcar a ambiguidade
  - Origem no legado: `src/core/path_search.py:92-123`
  - Critério de pronto: o rótulo e a contagem falam apenas do lado ambíguo; `ambiguous` verdadeiro se qualquer lado for ambíguo; `{}` quando cada nome é único
  - Confiança: 🟢

- [ ] **T-05**, Testar até **5 × 5** combinações e vencer a primeira **com caminho**
  - Origem no legado: `src/core/path_search.py:71`, `:150-167`
  - Critério de pronto: cache de pares `(cand1, cand2)`; vence a primeira combinação com `path`; sem nenhuma, usa o primeiro id de cada lado
  - Confiança: 🟢
  - ⚠️ **Isto substitui a decisão de 2026-08-03** ("homônimos usam o 1º ID"): a decisão continua acolhida como **recuo**, mas deixou de ser o comportamento principal. O caso medido que motivou a mudança está no próprio código.

- [ ] **T-06**, Reportar por pessoa quando o nome não resolve
  - Origem no legado: `src/core/path_search.py:138-141`
  - Critério de pronto: `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 '{nome}' não encontrada."` com `success=False`
  - Confiança: 🟢

### Navegação familiar

- [ ] **T-07**, Implementar `get_parents` com `FAMC` preferencial e fallback no índice
  - Origem no legado: `src/core/family_navigation.py:29-48`
  - Critério de pronto: usa `FAMC` se existir; senão `child_to_family`; coleta todos os `HUSB`/`WIFE`, sem duplicar
  - Confiança: 🟢

- [ ] **T-08**, Implementar `get_spouses` com o fallback **condicional**
  - Origem no legado: `src/core/family_navigation.py:51-75`
  - Critério de pronto: caminho por `FAMS`; a varredura global de `families` só roda se a lista ficou **vazia**
  - Confiança: 🟢
  - ⚠️ Reproduzir a condicional **exatamente**. Torná-la complementar **muda o resultado** da busca indireta e das pontes matrimoniais.

- [ ] **T-09**, Implementar `are_spouses`, `split_path_by_marriage`, `pick_spouse_for_couple` e `exclude_tail`
  - Origem no legado: `src/core/family_navigation.py:78-106`
  - Critério de pronto: `are_spouses` por pertinência em `set(get_spouses(...))`; `split_path_by_marriage` no **primeiro** par adjacente; `pick_spouse_for_couple` prefere o cônjuge presente no caminho; `exclude_tail` devolve `[]` quando `len(seq) <= n`
  - Confiança: 🟢

### Conexão direta

- [ ] **T-10**, Implementar o BFS **bidirecional** por pais (`find_ancestral_path`)
  - Origem no legado: `src/core/path_finding.py:51-85`
  - Critério de pronto: duas fronteiras alternando **um nível de um lado** por iteração; o encontro é o nó que já consta no visitado do outro lado; o caminho **não repete** o ponto de encontro; `start == end` devolve `([id], id)`
  - Confiança: 🟢
  - ⚠️ O teto `MAX_DEPTH = 20` conta **iterações de profundidade**, não gerações. Não reinterpretar.

- [ ] **T-11**, Implementar o corte **silencioso** no teto
  - Origem no legado: `src/core/path_finding.py:25`, `:85`
  - Critério de pronto: nenhum caminho dentro do teto → `(None, None)`, **sem** erro e **sem** sinalizar que o limite foi atingido
  - Confiança: 🟢
  - ⚠️ Decisão humana de 2026-09-30: preservar a fidelidade ao legado. **Não acrescentar aviso nem distinguir "limite atingido" de "sem caminho".**

### Conexão indireta

- [ ] **T-12**, Implementar `find_indirect_path` com caminho mais curto e compressão
  - Origem no legado: `src/core/path_finding.py:31-48`
  - Critério de pronto: `nx.shortest_path` não ponderado; rejeita se `len(caminho) − 1 > MAX_HOPS`; devolve **apenas ids de pessoa**; exige ≥ 2
  - Confiança: 🟢
  - ⚠️ O import de `graph` deve ficar **dentro** da função.

- [ ] **T-13**, Tratar `NetworkXNoPath` e `NodeNotFound` como ausência de caminho
  - Origem no legado: `src/core/path_finding.py:41-44`
  - Critério de pronto: as exceções do networkx devolvem `None`, nunca propagam
  - Confiança: 🟢

- [ ] **T-14**, Marcar a conexão indireta como **afinidade em três lugares**
  - Origem no legado: `src/core/path_search.py:66-67`, `:186-192`
  - Critério de pronto: `status = "affinity"` numa **cópia** do dicionário; rótulo `"Sem ancestral comum: conexão por afinidade (casamento)"`; aviso em **maiúsculas** afirmando que não há parentesco consanguíneo; a observação é acrescentada ao resultado
  - Confiança: 🟢
  - ⚠️ A marcação é feita numa **cópia**. Preservar isso; não mutar o dicionário do cache.

### Parentesco documental

- [ ] **T-15**, Implementar `documentary_relationship` com as guardas de pessoa ausente e sem caminho
  - Origem no legado: `src/core/documentary_relationship.py:436-484`
  - Critério de pronto: registro ausente → `status="not_found"` + `pessoa_ausente`; sem caminho → `status="not_found"` + `sem_caminho` (a mensagem **interpola `MAX_DEPTH`** e afirma que isso **não prova** ausência de parentesco), mais `homonimo` quando o dossiê for ambíguo
  - Confiança: 🟢

- [ ] **T-16**, Implementar `documentary_label` com os graus, a chave canônica e as meioses
  - Origem do legado: `src/core/documentary_relationship.py:290-340`
  - Critério de pronto: linha direta com prefixo `bis` repetido `n−2` vezes; colateral com menor grau 1 → irmãos, tio/tia, tio/tia-avô; demais → `gC` ou `gCrR` com `g = menor−1` e `r = maior−menor`
  - Confiança: 🟢

- [ ] **T-17**, Implementar `hop_evidence` com a idade implícita e o aviso de data impossível
  - Origem no legado: `src/core/documentary_relationship.py:41-42`, `:233-280`, `:497-507`
  - Critério de pronto: localiza a família por `FAMC`/`CHIL`, com recuo por `child_to_family`; devolve o casal declarado e as datas; `age_at_birth = ano_do_filho − ano_do_genitor`; fora de **12–70** → `plausible: False` + aviso `data_impossivel`; **sem data**, `plausible` é `None`
  - Confiança: 🟢
  - ⚠️ **Nenhuma data invalida vínculo.** O caminho é mantido como o GEDCOM o declara.

- [ ] **T-18**, Implementar `person_summary` com a ficha completa
  - Origem no legado: `src/core/documentary_relationship.py:127-143`
  - Critério de pronto: `id`, `name`, `sex`, `birth`, `birth_year`, `birth_place`, `death`, `death_year`, `parents`, `parent_names`, `spouses`, `children`, `family_as_child`
  - Confiança: 🟢

- [ ] **T-19**, Enumerar todos os ancestrais comuns e listar os caminhos alternativos
  - Origem no legado: `src/core/documentary_relationship.py:408-424`, `:509-525`
  - Critério de pronto: até `MAX_DEPTH_ALTERNATIVOS` (12) níveis, limitado a 12, ordenado por meioses totais e depois por maior distância; caminhos alternativos listados e **nenhum descartado**; aviso `caminhos_multiplos` com a contagem
  - Confiança: 🟢

- [ ] **T-20**, Detectar colapso de pedigree e marcar identidade ambígua
  - Origem no legado: `src/core/documentary_relationship.py:361-382`, `:527-549`, `:551-552`
  - Critério de pronto: mais de uma cadeia até o mesmo ancestral (teto `LIMITE_DE_CADEIAS = 8`) → aviso `colapso_de_pedigree` com o ancestral e a contagem; dossiê ambíguo → `status = "ambiguous"` + aviso `homonimo`
  - Confiança: 🟢

- [ ] **T-21**, Implementar o índice `nome → ids` invalidado por `versao`
  - Origem no legado: `src/core/documentary_relationship.py:185-202`
  - Critério de pronto: reconstruído apenas quando `gedcom_state.versao` muda, e **não** por tamanho de `people`
  - Confiança: 🟢
  - ⚠️ Existe porque `id()` não muda com mutação *in place*, e dois GEDCOMs podem ter a mesma contagem de pessoas.

### Renderização

- [ ] **T-22**, Implementar `_mermaid_sid`
  - Origem no legado: `src/reporting/mermaid_render.py:26-31`
  - Critério de pronto: coleção → primeiro elemento; remove `@`; `+` → `_`; remove tudo fora de `[A-Za-z0-9_]`; prefixa `N_`
  - Confiança: 🟢

- [ ] **T-23**, Implementar `_mermaid_label` com **lista branca** e a ordem correta
  - Origem no legado: `src/reporting/mermaid_render.py:47`, `:50-60`
  - Critério de pronto: NFC → NBSP/travessões/aspas curvas normalizados → `"` vira `'` → quebras de linha achatadas → **lista branca** → **depois** `&`,`<`,`>` como entidades
  - Confiança: 🟢
  - ⚠️ **A ordem é o contrato.** Filtro antes das entidades. Inverter reintroduz o `BUG-20260929-J6PQ`.

- [ ] **T-24**, Emitir o diagrama da conexão **direta**
  - Origem no legado: `src/reporting/mermaid_render.py:63-108`
  - Critério de pronto: `flowchart BT`; nó de **casal** quando o ancestral comum não está numa das pontas do caminho; arestas na direção correta; cores de P1 (verde), P2 (vermelho), ancestral (amarelo) e cônjuges (âmbar)
  - Confiança: 🟢

- [ ] **T-25**, Emitir o diagrama da conexão **indireta** em subgrafos
  - Origem no legado: `src/reporting/mermaid_render.py:112-289`
  - Critério de pronto: dois ramos em subgrafos de colunas; âncoras transparentes; aresta rotulada como casamento; cores de A e B; **`end` escrito pelo fim de um context manager**; delegação para o diagrama direto quando faltar pré-requisito
  - Confiança: 🟢
  - ⚠️ Um `end` a mais ou a menos muda a árvore do diagrama **sem levantar erro**. É por isso que o fechamento é estrutural, e não posicional.

- [ ] **T-26**, Montar o `path_result` com o resultado documental e as observações
  - Origem no legado: `src/core/path_search.py:169-202`
  - Critério de pronto: `person1_name`, `person2_name`, `text_path` unido por `" → "`, `mermaid_data`, `documentary` e `observations` deduplicadas
  - Confiança: 🟢

### Fluxo e rota

- [ ] **T-27**, Orquestrar direta → indireta, com precedência da direta
  - Origem no legado: `src/core/path_search.py:172-192`
  - Critério de pronto: conexão com ancestral comum **nunca** é reportada como indireta; mensagens exatas nos três desfechos
  - Confiança: 🟢

- [ ] **T-28**, Distinguir ausência de conexão de erro de entrada via `success`
  - Origem no legado: `src/core/path_search.py:180-182`; `src/app.py:167-169`
  - Critério de pronto: sem conexão → `(None, msg, True)`; pessoa não encontrada → `(None, msg, False)`
  - Confiança: 🟢
  - ⚠️ É o único caso do sistema em que ausência de resultado **não** é erro.

- [ ] **T-29**, Tratar exceções com erro amigável na rota
  - Origem no legado: `src/app.py:172-174`
  - Critério de pronto: exceção → `"Ocorreu um erro: {e}"` com `success=False`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, Resolução de pessoa por nome, com igualdade antes de substring 🟢
- [ ] **TT-02**, Conexão direta trivial (pessoas idênticas) e com ancestral comum 🟢
- [ ] **TT-03**, Fluxo completo da busca direta, com rótulo, graus e meioses 🟢
- [ ] **TT-04**, Conexão indireta por casamento, com o status `affinity` 🟢
- [ ] **TT-05**, `find_indirect_path` isoladamente 🟢
- [ ] **TT-06**, Pessoa não encontrada, distinguindo Pessoa 1 de Pessoa 2 🟢
- [ ] **TT-07**, Sem conexão — e com `success=True` 🟢
- [ ] **TT-08**, **Escolha entre homônimos**: três registros, só um com pais, conexão encontrada e resultado marcado como ambíguo 🟢
- [ ] **TT-09**, Dossiê recupera registro que difere apenas na acentuação 🟢
- [ ] **TT-10**, Aviso `data_impossivel` emitido **sem** invalidar o vínculo (caso medido: mãe nascida 11 anos depois do filho) 🟢
- [ ] **TT-11**, Aviso `colapso_de_pedigree` com ancestral e número de cadeias 🟢
- [ ] **TT-12**, Caminhos alternativos listados e `caminhos_multiplos` emitido 🟢
- [ ] **TT-13**, **Escape do rótulo: crase neutralizada**, e nenhum caractere que quebra a gramática sobrevive 🟢
- [ ] **TT-14**, **Entidades HTML preservadas** e caracteres legítimos intactos 🟢
- [ ] **TT-15**, Caracterização da saída Mermaid (`test_characterization_mermaid.py`) 🟢
- [ ] **TT-16**, Fuzz de rótulo com payloads hostis combinados e varredura de nomes reais — **promover a teste permanente** (hoje vive como evidência do adendo `bug-J6PQ`) 🟡
- [ ] **TT-17**, Teto de `MAX_DEPTH` e de `MAX_HOPS` (não existe no legado — criar) 🟡
- [ ] **TT-18**, `split_path_by_marriage` com múltiplos casamentos no caminho (não existe — cria) 🟡

## Tarefas de Migração de Dados

**Não aplicável** — sem banco de dados e sem volume a migrar. 🟢

## Ordem Sugerida

1. **T-07 a T-09 (navegação familiar) primeiro.** São a base do BFS e das pontes; dependem só dos dicionários, não do grafo.
2. **T-02 a T-06 (resolução de pessoas e homônimos).** Independentes, testáveis isoladamente.
3. **T-15 a T-21 (parentesco documental).** Dependem de T-07 e T-10; é o bloco que dá conteúdo ao resultado.
4. **T-10 e T-11 (conexão direta).** Dependem de T-07.
5. **T-12 e T-13 (conexão indireta).** Dependem da global `graph` e de T-09.
6. **T-22 e T-23 (escape).** Funções puras: podem ser feitas a qualquer momento, mas **antes** de T-24 e T-25.
7. **T-24 e T-25 (diagramas).** Dependem de T-23 e T-09.
8. **T-26 a T-29 (fluxo e rota) por último.**
9. **Bloqueios:** nada aqui funciona sem `upload-gedcom`. A unit `analise-dna` depende de T-10, T-15 e T-24 desta unit.

## Lacunas Pendentes (🔴)

- ✅ **`L-06` RESOLVIDA em 2026-10-05 por verificação no template:** `index.html:43-45` usa `success` para a **cor do alerta** e `:457` usa `path_result` para o **cartão**. Os três desfechos produzem telas distintas — a lacuna não se confirma.
- **`M-01`:** o estado `affinity` é atribuído a uma **cópia** do dicionário; o original segue `not_found`. Nenhum consumidor atual usa o original, mas a divergência é armadilha para reimplementação.
- **`M-02`:** a ambiguidade de identidade rebaixa `found` para `ambiguous`, mas **não** rebaixa `not_found`. Não há indicação de que a assimetria seja intencional.
- **`L-20`:** `get_children` sem índice e fichas completas por resultado — custo real, sem limite medido.
- **`L-17`:** o colapso além do teto (12 níveis / 8 cadeias) não é detectado, e o aviso não distingue "sem colapso" de "fora do alcance".
- **Inversão de camada:** `reporting/` importa `core/` e contém decisão de apresentação com efeito de negócio. Não há decisão humana registrada sobre manter essa fronteira.
- ✅ **Já decididas, não são pendências:** corte silencioso do `MAX_DEPTH` (2026-09-30, aceito); varredura condicional de `get_spouses` (2026-09-30, contrato); afinidade nunca é consanguinidade; escape por lista branca com entidades depois do filtro.

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*
