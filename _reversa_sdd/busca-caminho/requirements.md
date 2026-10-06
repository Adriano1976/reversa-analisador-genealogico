# Unit `busca-caminho` — Requisitos

> Unit do tipo **endpoint** — cobre `POST /` com `action=path_search`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-05** (nível **Completo**).
> Substitui a versão de 2026-09-30, que descrevia um núcleo único de 500 linhas e **não conhecia** o parentesco documental completo (evidência por salto, colapso de pedigree, caminhos múltiplos, escolha de homônimos por teste de combinações). Snapshot: `.reversa/snapshots/2026-10-05-pre-reextracao/busca-caminho/`
> Fontes: `code-analysis.md` §4 (36 regras `BR-C-*`), `flowcharts/busca-caminho.md`, `data-dictionary.md` §7, `domain.md` §3.1, `state-machines.md` §4, `adrs/` (03, 05, 11, 22)
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

Busca a conexão genealógica entre duas pessoas de uma árvore GEDCOM carregada. Tenta primeiro a conexão **direta** pelo ancestral comum, subindo exclusivamente por linhas parentais; se não existir, cai no **fallback indireto** por afinidade (casamentos), navegando o grafo pessoa↔família. Devolve o **parentesco documental completo** — rótulo, graus, meioses, evidência de cada salto, homônimos, caminhos alternativos — e um diagrama Mermaid. 🟢

A busca é **documental**: não há DNA nesta tela. E a unit carrega o **contrato de escape do rótulo Mermaid**, que é o ponto onde dado vindo do GEDCOM entra numa gramática de diagrama de terceiro. 🟢

## Responsabilidades

- Localizar as duas pessoas pelo nome, montando o **dossiê de homônimos** dos dois lados. 🟢
- Escolher o par entre homônimos **testando combinações**, e não aceitando o primeiro em silêncio. 🟢
- Buscar conexão **direta** por BFS bidirecional subindo apenas por pais. 🟢
- Em falha, buscar conexão **indireta** por afinidade, com teto de arestas. 🟢
- Produzir o **parentesco documental** completo, com a evidência de cada salto e os avisos de plausibilidade. 🟢
- Marcar a conexão por casamento como **afinidade em três lugares**, nunca como consanguinidade. 🟢
- **Sanitizar** o id e o rótulo dos nós Mermaid e emitir o diagrama adequado ao tipo de conexão. 🟢
- Distinguir **"sem conexão"** de **erro de entrada**. 🟢

## Regras de Negócio

### Resolução de pessoas e homônimos

- A resolução é em **duas passadas**: igualdade sem diferenciar maiúsculas primeiro; substring só se a igualdade não devolver nada. 🟢
- O **dossiê de homônimos** compara nomes **sem acento**, aplicando a correção de mojibake antes de comparar — porque `find_person_by_name` compara **com** acento, e um CSV ou formulário sem acento não encontraria o registro. 🟢
- **Com homônimos, o sistema deixa de escolher o primeiro ID.** São testadas até **5 × 5** combinações (em cache) e vence a **primeira que tiver caminho**. Caso medido no próprio código: `"Jose Vicente de Souza"` tem três registros, dois diferindo só no acento, e **só um tem pais** — antes a tela respondia "nenhuma conexão" para uma conexão que o GEDCOM contém. 🟢
- Sem nenhuma combinação com caminho, usa-se o primeiro id de cada lado. 🟢
- A ambiguidade **nunca é silenciosa**: o resultado sai com `status = "ambiguous"` e o aviso `homonimo`, pedindo conferência das fichas. 🟢
- Pessoa 1 não resolvida → `"Pessoa 1 '{nome}' não encontrada."`; idem para Pessoa 2, com `success = False`. 🟢

### Conexão direta

- BFS **bidirecional**: duas fronteiras, e a cada iteração **um** nível de **um** dos lados é expandido, alternadamente. 🟢
- Sobe **apenas por pais** (`FAMC` preferencial; fallback no índice `child_to_family`), com pais duplicados removidos. 🟢
- Teto de `MAX_DEPTH = 20` **iterações de profundidade** — **não** gerações. Cada iteração expande um nível de um dos lados. 🟢
- O encontro é detectado quando o nó recém-expandido já consta no conjunto visitado do outro lado; o caminho é a concatenação dos dois percursos, **sem repetir** o ponto de encontro. 🟢
- `start == end` devolve caminho trivial, e a pessoa é o próprio ancestral. 🟢
- **O teto corta em silêncio.** Decisão humana de 2026-09-30: preservar a fidelidade ao legado, sem sinalização. O retorno é indistinguível de "não existe caminho" e o aviso diz que **isso não prova** ausência de parentesco. 🟢

### Conexão indireta

- Executada **somente** se a direta falhar — nunca as duas. 🟢
- `nx.shortest_path` não ponderado sobre o grafo bipartido pessoa↔família, com teto de `MAX_HOPS = 40` **arestas**. 🟢
- Os nós de família são **comprimidos**: o caminho devolvido contém apenas pessoas, e exige **2 ou mais**. 🟢
- O grafo é **importado dentro da função**, porque o upload o **reatribui** a cada carga — um import no topo ficaria preso ao grafo antigo, ou a `None`. 🟢
- `NetworkXNoPath` e `NodeNotFound` são tratados como ausência de caminho, nunca propagados. 🟢
- **A conexão indireta é marcada como afinidade em três lugares**: `status = "affinity"`, rótulo "Sem ancestral comum: conexão por afinidade (casamento)" e um aviso **em maiúsculas** de que aquilo **NÃO** representa parentesco consanguíneo. 🟢

### Parentesco documental

- O rótulo e a **chave canônica** vêm dos graus: linha direta usa prefixo `bis` repetido `n−2` vezes; colateral com menor grau 1 vira irmãos, tio/tia ou tio/tia-avô; o resto vira primos de `g` grau com `r` remoções. 🟢
- **Meioses** — os saltos pai-filho entre as duas pessoas — é a grandeza que o cM mede, e é o que liga o rótulo à tabela do Shared cM Project. 🟢
- Cada salto carrega a **evidência do registro que o sustenta**: família, casal declarado, datas e a **idade implícita** do genitor. 🟢
- Idade de genitor fora de **12–70** anos marca `plausible: False` e gera o aviso `data_impossivel` — **sem invalidar o vínculo**. Sem data para julgar, `plausible` é `None`, e `None` **não** é falso. O caso medido está no próprio código: mãe nascida **11 anos depois** do filho. 🟢
- **Todos** os ancestrais comuns são enumerados até **12** níveis, limitados a **12**, ordenados por meioses totais. 🟢
- Caminhos alternativos são **listados e nenhum é descartado**; a existência gera o aviso `caminhos_multiplos`. 🟢
- **Colapso de pedigree** é detectado por **contagem de cadeias** até o mesmo ancestral (teto de **8**): mais de uma cadeia é a assinatura de colapso/endogamia, e gera aviso com o ancestral e o número de cadeias. 🟢

### Escape do rótulo e do id Mermaid

- O **id do nó** mantém apenas `[A-Za-z0-9_]`, remove `@`, troca `+` por `_` e recebe o prefixo `N_`. 🟢
- O **rótulo** passa por: normalização **NFC** → espaço inquebrável, travessões e aspas curvas normalizados → aspa dupla vira apóstrofo → quebras de linha achatadas → **lista branca** → **e só então** `&`, `<` e `>` viram entidades HTML. 🟢
- **A ordem é invariante do contrato.** A lista branca substituiu uma lista negra que era **furada pela crase** (`BUG-20260929-J6PQ`); a versão seguinte era estreita demais e descartava 14 caracteres sem intenção (`BUG-20261002-T4ZM`). 🟢
- Cada `subgraph` do diagrama indireto é fechado pelo fim de um **context manager**, e não por uma linha posicionada à mão: um `end` a mais ou a menos muda a árvore do diagrama **sem levantar erro nenhum**. 🟢

### Saída

- Sem conexão nos dois estágios → `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` com **`success = True`** — "não achei" **não é erro**. 🟢
- Erro é entrada inválida: pessoa não encontrada devolve `success = False`. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Resolver pessoa por nome em duas passadas (igualdade, depois substring), sem diferenciar maiúsculas | Must | Nome exato tem precedência sobre substring 🟢 |
| RF-02 | Montar o dossiê de homônimos dos dois lados, comparando **sem acento** e corrigindo mojibake | Must | Um nome sem acento encontra o registro com acento 🟢 |
| RF-03 | Testar até **5 × 5** combinações de homônimos e vencer a primeira **com caminho** | Must | Três registros de mesmo nome, só um com pais → a conexão é encontrada 🟢 |
| RF-04 | Marcar identidade ambígua no resultado, com o aviso `homonimo` | Must | Resultado com `status = "ambiguous"` e a contagem de registros 🟢 |
| RF-05 | Reportar por pessoa quando o nome não resolve | Must | `"Pessoa 1 '{nome}' não encontrada."` distingue de Pessoa 2; `success = False` 🟢 |
| RF-06 | Buscar conexão direta por BFS bidirecional subindo **apenas por pais** | Must | Caminho com ancestral comum, rótulo e meioses completos 🟢 |
| RF-07 | Respeitar o teto de **20 iterações de profundidade**, com corte silencioso | Must | Caminho mais fundo que o teto devolve ausência de caminho, **sem** aviso de limite atingido 🟢 |
| RF-08 | Tratar pessoas idênticas com caminho trivial | Should | O caminho é a própria pessoa, e ela é o ancestral 🟢 |
| RF-09 | Cair para a busca indireta **somente** quando a direta falhar | Must | Conexão com ancestral comum **nunca** é reportada como indireta 🟢 |
| RF-10 | Buscar a indireta por caminho mais curto no grafo de famílias, com teto de **40 arestas** | Must | Caminho mais longo que o teto é rejeitado 🟢 |
| RF-11 | Comprimir nós de família e exigir 2 ou mais pessoas | Must | O caminho devolvido contém apenas ids de pessoa 🟢 |
| RF-12 | Marcar a conexão indireta como **afinidade** nos três lugares (status, rótulo e aviso em maiúsculas) | Must | O aviso afirma explicitamente que **não** há parentesco consanguíneo 🟢 |
| RF-13 | Distinguir "sem conexão" de erro de entrada via `success` | Must | Sem conexão → `success = True`; entrada inválida → `success = False` 🟢 |
| RF-14 | Produzir rótulo legível, **chave canônica** e **meioses** a partir dos graus | Must | Linha direta, colateral e primos seguem as fórmulas de grau e remoção 🟢 |
| RF-15 | Anexar a **evidência de cada salto**, com família, casal declarado, datas e idade implícita | Must | Um item de evidência por aresta do caminho 🟢 |
| RF-16 | Avisar `data_impossivel` fora de 12–70 anos **sem invalidar o vínculo** | Must | O caminho é mantido como o GEDCOM o declara; o aviso convida a conferir 🟢 |
| RF-17 | Enumerar **todos** os ancestrais comuns até 12 níveis, ordenados por meioses totais | Should | A cardinalidade respeita o teto configurado 🟢 |
| RF-18 | Listar caminhos alternativos **sem descartar nenhum**, com o aviso `caminhos_multiplos` | Must | O caminho exibido é o de menor distância total; os demais estão listados 🟢 |
| RF-19 | Detectar colapso de pedigree por contagem de cadeias (teto 8) e avisar | Should | Aviso `colapso_de_pedigree` nomeia o ancestral e o número de cadeias 🟢 |
| RF-20 | Sanitizar o **id** do nó Mermaid | Must | Apenas `[A-Za-z0-9_]` sobrevive, com prefixo `N_` 🟢 |
| RF-21 | Sanitizar o **rótulo** por **lista branca**, com as entidades HTML aplicadas **depois** do filtro | Must | Aspa dupla e crase neutralizadas; `&`, `<`, `>` viram entidades; acentos e pontuação legítima sobrevivem 🟢 |
| RF-22 | Emitir o diagrama da conexão **direta**, fundindo o casal do ancestral comum em um nó | Must | `flowchart BT`; nó de casal presente quando o ancestral não é extremidade do caminho 🟢 |
| RF-23 | Emitir o diagrama da conexão **indireta** em subgrafos, com a aresta de casamento | Must | Cada `subgraph` é fechado por context manager; a aresta é rotulada como casamento 🟢 |
| RF-24 | Tratar exceções com erro amigável na rota | Must | `"Ocorreu um erro: {e}"` com `success = False`, sem derrubar a aplicação 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| --- | --- | --- | --- |
| Performance | BFS **bidirecional** em vez de unidirecional: reduz a explosão combinatória de subir duas linhagens | `path_finding.py:51-85` | 🟢 |
| Performance | Teto de **20 iterações** no BFS e de **40 arestas** no caminho indireto | `path_finding.py:25`, `:28` | 🟢 |
| Performance | Cache do dossiê de homônimos por **nome**, e não por candidato; o índice `nome → ids` é reconstruído apenas quando `versao` muda | `dna_analysis.py:160-164`; `documentary_relationship.py:185-202` | 🟢 |
| Performance | 🔴 `get_children` varre **todas** as famílias do arquivo, sem índice, a cada chamada — diferente de `get_parents`, que usa `child_to_family` | `documentary_relationship.py:112-124` | 🟢 |
| Performance | 🔴 `person_a` e `person_b` são **fichas completas** em cada resultado: no caso real de 71 conexões foram **142 fichas** montadas para uma tela que exibe poucas | `documentary_relationship.py:127-143`, `:558-559` | 🟢 |
| Segurança | O **escape do rótulo é a única defesa** contra conteúdo do GEDCOM quebrar o diagrama. `securityLevel: 'strict'` cobre XSS, **não** a gramática | `mermaid_render.py:47`, `:50-60`; `index.html:182` | 🟢 |
| Confiabilidade | O grafo é lido por **import tardio**, porque é reatribuído a cada carga | `path_finding.py:38` | 🟢 |
| Reprodutibilidade | Uma falha silenciosa de gramática é possível: um `end` a mais ou a menos muda a árvore do diagrama **sem erro**. Mitigado por context manager | `mermaid_render.py:160-175` | 🟢 |
| Reprodutibilidade | A escolha entre homônimos nesta unit **é determinística**: percorre uma **lista** (`dict.fromkeys`) com teto de 5×5 — diferente do desempate do matching de `analise-dna`, que percorre um `set` | `path_search.py:85`, `:154-163` | 🟢 |
| Manutenibilidade | 🔴 O `reporting/` **depende de `core/`**: o renderizador navega o domínio para decidir *como* desenhar. Há decisão de negócio dentro da apresentação | `mermaid_render.py:16-23` | 🟢 |
| Observabilidade | **Nenhum log, métrica ou trace.** A única visibilidade é o texto do caminho, o diagrama e os avisos | — | 🟢 |
| Internacionalização | Todas as mensagens e rótulos ao operador são literais em português | `path_search.py`, `documentary_relationship.py` | 🟢 |

> Inferido a partir do código. **Não** há autenticação, cache, fila, retry ou timeout — as linhas correspondentes foram omitidas por falta de evidência.

## Critérios de Aceitação

```gherkin
Dado um GEDCOM carregado e duas pessoas existentes com ancestral comum
Quando o operador busca o caminho entre elas
Então a tela exibe "Conexão direta encontrada (ancestral comum)."
E o resultado traz rótulo, graus e meioses
E cada salto do caminho traz a evidência do registro que o sustenta
E o diagrama Mermaid é emitido na forma direta

Dado que a busca direta falha mas existe vínculo por casamento
Quando o operador busca o caminho
Então a tela exibe "Conexão indireta encontrada (via casamento/afinidade)."
E o status do parentesco é "affinity"
E o rótulo é "Sem ancestral comum: conexão por afinidade (casamento)"
E um aviso afirma em maiúsculas que NÃO há parentesco consanguíneo

Dado um nome com três registros no GEDCOM, dos quais só um tem pais
Quando o operador busca o caminho
Então as combinações são testadas e a conexão é encontrada pelo registro com pais
E o resultado sai com status "ambiguous"
E um aviso informa quantos registros existem e pede conferência das fichas

Dado um caminho em que o genitor declarado nasceu 11 anos depois do filho
Quando o parentesco documental é calculado
Então o aviso "data_impossivel" é emitido com as datas e a diferença
E o vínculo NÃO é invalidado
E o caminho é mantido como o GEDCOM o declara

Dado um par que compartilha um ancestral alcançado por mais de uma cadeia de pais
Quando o parentesco documental é calculado
Então o aviso "colapso_de_pedigree" nomeia o ancestral e o número de cadeias

Dado um nome vindo do GEDCOM que contém aspa dupla seguida de crase
Quando o diagrama é emitido
Então o rótulo do nó é neutralizado
E o diagrama continua sendo um flowchart válido
E nenhuma aspa dupla crua ou crase sobrevive no rótulo

Dado um nome com "&", "<" ou ">"
Quando o diagrama é emitido
Então esses caracteres aparecem como entidades HTML
E os caracteres legítimos (acentos, pontos, parênteses) sobrevivem intactos

Dado duas pessoas existentes e nenhum caminho entre elas em nenhum dos dois estágios
Quando o operador busca o caminho
Então a tela exibe "Nenhuma conexão encontrada entre 'X' e 'Y'."
E a resposta NÃO é tratada como erro (success = True)

Dado um nome que não existe na árvore
Quando o operador busca o caminho
Então a tela exibe "Pessoa 1 'X' não encontrada." (ou Pessoa 2, conforme o caso)
E success = False
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
| --- | --- | --- |
| RF-21 Escape do rótulo | **Must** | **Sem isso o diagrama inteiro deixa de renderizar** — foi o `BUG-20260929-J6PQ` |
| RF-06/RF-07 Conexão direta e teto | **Must** | Núcleo da busca |
| RF-09/RF-10/RF-11 Conexão indireta | **Must** | Sem o fallback, todo parentesco por afinidade fica invisível |
| RF-14/RF-15 Rótulo, meioses e evidência por salto | **Must** | É a saída que o operador lê |
| RF-01/RF-02/RF-05 Resolução de pessoas e dossiê | **Must** | Pré-condição de todo o fluxo |
| RF-13 Distinção sem-conexão × erro | **Must** | Define o que o template mostra como erro |
| RF-16 Aviso de data impossível | **Must** | Impede que um vínculo cronologicamente absurdo passe como normal |
| RF-22/RF-23 Emissão dos diagramas | **Must** | Saída principal |
| RF-03/RF-04 Escolha entre homônimos com aviso | **Should** | O fluxo funciona com o primeiro id; a taxa de acerto é que muda |
| RF-18 Caminhos alternativos | **Should** | O caminho principal basta para responder |
| RF-17 Enumeração de ancestrais comuns | **Should** | Enriquece o resultado; o rótulo vem do ancestral principal |
| RF-19 Colapso de pedigree | **Should** | Aviso importante, mas não altera o caminho |
| RF-08 Pessoas idênticas | **Could** | Caso de borda acionado raramente |
| RF-12 Marcação de afinidade em três lugares | **Must** | Redundância deliberada: impede leitura de afinidade como consanguinidade |
| RF-20 Sanitização do id do nó | **Must** | Sem ela, um `xref_id` inesperado quebra o diagrama |

## Rastreabilidade de Código

| Arquivo | Função / símbolo | Cobertura |
| --- | --- | --- |
| `src/app.py` | ramo `path_search` `:156-169`; re-parse `:132` | 🟢 |
| `src/core/path_search.py` | `path_search` `:126-202`; `_candidatos` `:74`; `_homonimos` `:92`; `AVISO_AFINIDADE` `:66-67`; `LIMITE_DE_CANDIDATOS` `:71` | 🟢 |
| `src/core/path_finding.py` | `find_ancestral_path` `:51`; `find_indirect_path` `:31`; `MAX_DEPTH` `:25`; `MAX_HOPS` `:28` | 🟢 |
| `src/core/family_navigation.py` | `find_person_by_name` `:21`; `get_parents` `:29`; `get_spouses` `:51`; `are_spouses` `:78`; `split_path_by_marriage` `:82`; `pick_spouse_for_couple` `:93`; `exclude_tail` `:104` | 🟢 |
| `src/core/documentary_relationship.py` | `documentary_relationship` `:436-568`; `documentary_label` `:290`; `person_summary` `:127`; `homonym_dossier` `:205`; `hop_evidence` `:233`; `find_all_common_ancestors` `:408`; `parse_year` `:58`; `get_children` `:112`; `normalizar` `:150` | 🟢 |
| `src/reporting/mermaid_render.py` | `_mermaid_sid` `:26`; `_mermaid_label` `:50`; `_LABEL_SEGURO` `:47`; `generate_mermaid_graph` `:63`; `generate_mermaid_graph_indirect_bridge` `:112` | 🟢 |
| `src/templates/index.html` | badge de status do resultado `:464`; `securityLevel: 'strict'` | 🟢 |
| `tests/test_path_search.py`, `test_mermaid_escape.py`, `test_characterization_mermaid.py`, `test_confrontacao_gedcom_dna.py` | cobertura do fluxo, do contrato de escape e da caracterização | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*
