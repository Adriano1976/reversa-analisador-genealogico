# Unit `busca-caminho` — Requisitos

> Unit do tipo **endpoint** — cobre `POST /` com `action=path_search`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**).
> **Substitui a versão de 2026-10-05**, que descrevia **36** regras, o grafo lido por **import tardio de uma global** e o índice de nomes invalidado por `gedcom_state.versao` — duas coisas que **deixaram de existir**. Snapshot: `.reversa/snapshots/2026-10-10-pre-reextracao/busca-caminho/`
> Fontes: `code-analysis.md` §5 (67 regras `BR-C-01`..`BR-C-67`), `flowcharts/busca-caminho.md` (§11 e §13), `data-dictionary.md` §7, `domain.md` §3.1, `state-machines.md` §4, `adrs/` (03, 05, 11, 22, 24, 25, 33, 34)
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

Busca a conexão genealógica entre duas pessoas de uma árvore GEDCOM carregada. Tenta primeiro a conexão **direta** pelo ancestral comum, subindo exclusivamente por linhas parentais; se não existir, cai no **fallback indireto** por afinidade (casamentos), navegando o grafo pessoa↔família. Devolve o **parentesco documental completo** — rótulo, graus, meioses, evidência de cada salto, homônimos, caminhos alternativos — e um diagrama Mermaid. 🟢

A busca é **documental**: não há DNA nesta tela. E a unit carrega o **contrato de escape do rótulo Mermaid**, que é o ponto onde dado vindo do GEDCOM entra numa gramática de diagrama de terceiro. 🟢

> ⚠️ **O que mudou desde 2026-10-05.** A unit passou a ser a **segunda** com fronteira de aplicação completa: ganhou `Desfecho` em três valores e `ResultadoDeBusca` congelado (`ADR-33`), o erro tipado com a tabela de tradução compartilhada, e o `dono` sem comportamento. O **ciclo `core/` ↔ `reporting/` foi fechado** pelo **resolvedor de diagrama** (`ADR-34`): o renderizador **não importa mais `core`**. O **import tardio da global `graph` desapareceu** — a árvore entra por parâmetro (`ADR-24`). E o índice de nomes passou a ser invalidado por uma **chave derivada do conteúdo** em vez de uma versão de estado global — mudança que **trouxe um achado novo** (`L-24`/`E-05`, § Riscos do `design.md`).

## Responsabilidades

- Fazer `strip` nos dois nomes e localizá-los pelo texto, montando o **dossiê de homônimos** dos dois lados. 🟢
- Escolher o par entre homônimos **testando combinações**, e não aceitando o primeiro em silêncio. 🟢
- Buscar conexão **direta** por BFS bidirecional subindo apenas por pais. 🟢
- Em falha, buscar conexão **indireta** por afinidade, com teto de arestas. 🟢
- Produzir o **parentesco documental** completo, com a evidência de cada salto e os avisos de plausibilidade. 🟢
- Marcar a conexão por casamento como **afinidade em três lugares**, nunca como consanguinidade. 🟢
- **Sanitizar** o id e o rótulo dos nós Mermaid e emitir o diagrama adequado ao tipo de conexão. 🟢
- **Entregar as consultas de domínio ao renderizador** por um resolvedor, para que a apresentação não importe o núcleo. 🟢 *(novo)*
- Derivar e devolver um **desfecho tipado** em três valores, sem dar autoridade semântica ao texto da mensagem. 🟢 *(novo)*
- Distinguir **"sem conexão"** de **erro de entrada**. 🟢

## Regras de Negócio

### Resolução de pessoas e homônimos

- Os dois nomes recebem **`strip` antes de qualquer coisa** (`BR-C-37`). 🟢
- A resolução é em **duas passadas**: igualdade sem diferenciar maiúsculas primeiro; substring só se a igualdade não devolver nada (`BR-C-01`). 🟢
- Pessoa 1 não resolvida → `"Pessoa 1 '{nome}' não encontrada."`; idem para a Pessoa 2, com `success = False` (`BR-C-26`). 🟢
- O **dossiê de homônimos** compara nomes **sem acento**, aplicando a correção de mojibake antes de comparar (`BR-C-23`) — porque `find_person_by_name` compara **com** acento, e um nome sem acento não acharia o registro GEDCOM. 🟢
- O dossiê devolve **todos** os registros possíveis, **sem escolher**; `ambiguous` é verdadeiro com mais de um nome exato **ou** com `similar_ids` não vazio (`BR-C-24`). 🟢
- Os **candidatos** unem os ids do legado aos **exatos** do dossiê, sem repetir e preservando a ordem; os "parecidos" entram **apenas** como `similar_matches`, limitados a **5** (`BR-C-38`). 🟢
- O dossiê agregado só é ambíguo se **algum lado** for ambíguo, e a contagem e as fichas vêm **só dos lados ambíguos** (`BR-C-39`); sem ambiguidade e sem parecidos, ele é `{}` e a seção **não aparece** na tela (`BR-C-40`). 🟢
- **Com homônimos, o sistema deixa de escolher o primeiro ID.** São testadas até **5 × 5** combinações (`LIMITE_DE_CANDIDATOS = 5` por lado), com os pares já calculados **reaproveitados por cache local**, e vence a **primeira que tiver caminho** (`BR-C-27`, `BR-C-41`, `BR-C-42`). 🟢
- **A combinação vencedora é a primeira com caminho, não a de menor distância.** 🟢
- Sem nenhuma combinação com caminho, usa-se o **primeiro id de cada lado** (`BR-C-27`). 🟢
- Caso medido no próprio código: `"Jose Vicente de Souza"` tem três registros, dois diferindo só no acento, e **só um tem pais** — antes a tela respondia "nenhuma conexão" para uma conexão que o GEDCOM contém. 🟢
- A ambiguidade **nunca é silenciosa**: com caminho e identidade ambígua, o resultado sai com `status = "ambiguous"` e o aviso `homonimo` (`BR-C-25`). 🟢

### Conexão direta

- BFS **bidirecional**: duas fronteiras, e a cada iteração **um** nível de **um** dos lados é expandido, alternadamente (`BR-C-04`, `BR-C-06`). 🟢
- Sobe **apenas por pais**: `FAMC` preferencial, com fallback no índice `child_to_family`; `HUSB` e `WIFE` de **todas** as famílias do `FAMC`, sem repetir (`BR-C-02`). 🟢
- Teto de `MAX_DEPTH = 20` **iterações de profundidade** — **não** gerações (`BR-C-04`). 🟢
- O encontro é o nó já visitado pelo outro lado, e o caminho é a concatenação **sem repetir** o ponto de encontro (`BR-C-04`). 🟢
- `start == end` devolve caminho trivial, e a pessoa é o próprio ancestral (`BR-C-05`). 🟢
- **O teto corta em silêncio**, e isso é **decisão humana de 2026-09-30**, preservada: o retorno é indistinguível de "não existe caminho", e o aviso diz que **isso não prova** ausência de parentesco. **Não acrescentar sinalização.** 🟢
- **Não há pesos nem limiares no BFS**: o caminho é o primeiro encontrado, e a ordem de inserção das arestas é contrato de paridade. 🟢

### Conexão indireta

- Executada **somente** se a direta falhar — nunca as duas. 🟢
- `nx.shortest_path` **não ponderado** sobre o grafo bipartido pessoa↔família, com teto de `MAX_HOPS = 40` **arestas** (`BR-C-07`). 🟢
- Os nós de família são **comprimidos**: o caminho devolvido contém apenas pessoas, e exige **2 ou mais**. 🟢
- **O grafo vem da árvore recebida por parâmetro** (`BR-C-08`, reescrita nesta rodada): não há import tardio nem estado de processo. Grafo ausente ou nó ausente devolve `None`, sem exceção. 🟢
- `NetworkXNoPath` e `NodeNotFound` são tratados como ausência de caminho, nunca propagados. 🟢
- Os cônjuges vêm dos `FAMS`, e a **varredura global de famílias só roda quando essa lista fica vazia** (`BR-C-03`). **A condicional é contrato:** com um `FAMS` que resolve e outro que não, o fallback **não roda** e o cônjuge da segunda família desaparece. Torná-la complementar **muda o resultado**. 🟢
- `split_path_by_marriage` devolve o **primeiro** par adjacente de cônjuges e as duas metades (`BR-C-49`); `pick_spouse_for_couple` prefere o cônjuge que aparece no caminho candidato, senão o primeiro (`BR-C-50`); `exclude_tail(seq, n=1)` corta a cauda para não duplicar o ancestral na ponta (`BR-C-51`). 🟢
- **A conexão indireta é marcada como afinidade em três lugares** (`BR-C-30`, `BR-C-31`): `status = "affinity"`, rótulo `"Sem ancestral comum: conexão por afinidade (casamento)"` e o aviso de afinidade, que afirma **em maiúsculas** que aquilo **NÃO** representa parentesco consanguíneo. A marcação é feita em uma **cópia** do dicionário. 🟢

### Parentesco documental

- Sem os dois registros no GEDCOM, `status: not_found` com o aviso `pessoa_ausente` (`BR-C-09`). 🟢
- Sem caminho dentro do teto, o aviso diz que **isso não prova** ausência de parentesco (`BR-C-10`). **O `MAX_DEPTH` está interpolado nessa mensagem**: mudar o teto é mudar texto de contrato. 🟡
- Os **graus** são as posições do ancestral comum no caminho (`BR-C-11`). 🟢
- Rótulo e **chave canônica** vêm dos graus (`BR-C-12`..`BR-C-14`): linha direta usa prefixo `bis` repetido `n−2` vezes; colateral com menor grau 1 vira irmãos, tio/tia ou tio/tia-avô; o resto vira primos de `g` grau com `r` remoções, com `g = menor−1` e `r = maior−menor`. 🟢
- **Meioses** — os saltos pai-filho entre as duas pessoas — é a grandeza que o cM mede, e é o que liga o rótulo à tabela do Shared cM Project. 🟢
- Cada salto carrega a **evidência do registro que o sustenta**: família, casal declarado, datas e a **idade implícita** do genitor (`BR-C-15`, `BR-C-48`). Sem família localizada, `link_source` diz isso. 🟢
- Idade de genitor fora de **12–70** anos marca `plausible: False` e gera o aviso `data_impossivel` — **sem invalidar o vínculo** (`BR-C-16`). O caso medido está no próprio código: mãe nascida **11 anos depois** do filho. 🟢
- Sem data para julgar, `plausible` é **`None`**, e `None` **não** é falso (`BR-C-17`). 🟢
- O ano é o **primeiro** número de 3 ou 4 dígitos; `ABOUT`/`BEFORE` são tolerados e **não** normalizados (`BR-C-18`). 🟢
- **Todos** os ancestrais comuns são enumerados até **12** níveis, limitados a **12**, ordenados por meioses totais, depois maior distância, depois nome (`BR-C-19`). 🟢
  - 🟡 **O empate nos três critérios herda a ordem do `set`** — a varredura parte de `set(de_a) & set(de_b)` —, então a ordem pode variar com o `PYTHONHASHSEED` (`BR-C-43`). É a mesma classe do defeito que o `matching` fechou em 2026-10-05, e **aqui segue aberta**.
- Caminhos alternativos são **listados e nenhum é descartado**; a existência gera o aviso `caminhos_multiplos`, que declara que o exibido é o de menor distância total (`BR-C-20`). 🟢
- **Colapso de pedigree** é mais de **uma cadeia** de pais até o mesmo ancestral, com teto de **8** cadeias (`BR-C-21`); o aviso lista até 3 e declara o efeito no cM. 🟢 **A contagem devolve um PISO** — ela para no teto (`BR-C-44`). 🟡
- `person_summary` monta a ficha comparável com **13 campos** (`BR-C-45`); `_diferencas` compara data e local de nascimento, data de falecimento, pais, filhos e sexo (`BR-C-46`); `identical_data` é verdadeiro quando há mais de um registro e **nenhum** campo diverge (`BR-C-47`). 🟢
- **O índice `nome → ids` é reconstruído quando a chave derivada do conteúdo da árvore muda** (`BR-C-22`, reescrita nesta rodada) — antes era uma versão de estado global, que **não existe mais**. 🟢
  - 🔴→🟢 **A chave tem colisão possível** (`BR-C-22` + `E-05`): ela é `(len(people), chaves[0], chaves[-1])`, e dois GEDCOMs do **mesmo tamanho** com os **mesmos xrefs extremos** reaproveitam o índice da árvore anterior. O dossiê de homônimos passa a listar xrefs de **outra árvore**, **sem exceção** — `get_name(None)` degrada em silêncio. **CONFIRMADO POR EXECUÇÃO em 2026-10-10** (ver `design.md` § Riscos): o cenário deixou de ser inferido e a correção foi **aceita por decisão humana**, para execução depois do Passo 4. Ver `flowcharts/busca-caminho.md` §13.

### Escape do rótulo e do id Mermaid

- O **id do nó** mantém apenas `[A-Za-z0-9_]`, remove `@`, troca `+` por `_` e recebe o prefixo `N_` (`BR-C-34`). Coleção vira primeiro elemento. 🟢
- O **rótulo** passa por (`BR-C-32`, `BR-C-33`): normalização **NFC** → espaço inquebrável, travessões e aspas curvas normalizados → aspa dupla vira apóstrofo → quebras de linha achatadas → **lista branca** → **e só então** `&`, `<` e `>` viram entidades HTML. 🟢
- **A ordem dos dois últimos passos é invariante do contrato.** A lista branca substituiu uma lista **negra** que era **furada pela crase** (`BUG-20260929-J6PQ`); a versão seguinte era **estreita demais** e descartava 14 caracteres sem intenção (`BUG-20261002-T4ZM`). 🟢
- O critério da lista é **INERTE, e não "seguro"**: dentro do estado `string`, o lexer do Mermaid consome tudo, de modo que colchete, dois pontos, barra e palavra-chave são inertes. O que **não pode passar** é a aspa dupla e a crase. 🟢

### Diagrama

- No diagrama **direto**, o casal do ancestral comum vira **um** nó quando o ancestral não está numa das pontas do caminho (`BR-C-35`); linhagem direta é `ac_idx` em `-1`, `0` ou no último nó (`BR-C-53`), e **os dois membros do casal são omitidos** como nós próprios quando o casal é emitido (`BR-C-54`). 🟢
- As **cores são fixas por papel** (`BR-C-58`): p1 verde, p2 vermelho, MRCA/casal amarelo e o casal da afinidade laranja. 🟢
- O diagrama **indireto** abre `subgraph`s **aninhados**, todos com `direction BT` (`BR-C-55`); o casamento é uma aresta rotulada entre duas **âncoras invisíveis**, e **não** uma seta de filiação (`BR-C-57`). 🟢
- Cada `subgraph` é fechado pelo fim de um **context manager** (`BR-C-36`): um `end` a mais ou a menos muda a árvore do diagrama **sem levantar erro nenhum** (`OPP-20260929-H2YY`). 🟢
- Sem par de cônjuges, sem caminho até A ou sem caminho até B, o diagrama indireto **cai no direto** com `mrca=None` (`BR-C-56`). 🟢
- O `sid` do par de cônjuges é o dos dois ids **ordenados** unidos por `+` — logo, **independente da ordem recebida** (`BR-C-52`). 🟢
- **O renderizador não importa `core`** (`BR-C-59`): ele recebe `dominio`, o mapeamento de **sete consultas** já ligadas à árvore. As decisões de layout continuam no renderizador, porque decidir o casal do ancestral comum é decisão de negócio (`ADR-11`). 🟢

### Fronteira e saída

- Sem conexão nos dois estágios → `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` com **`success = True`** (`BR-C-29`): "não achei" **não é erro**. É o **único** caso do sistema em que ausência de resultado não é erro. 🟢
- O **desfecho** é derivado de `(payload, sucesso)`, **nunca do texto** (`BR-C-60`): payload presente → `RESULTADO`; sem payload e com sucesso → `SEM_RESULTADO`; sem payload e sem sucesso → `ERRO_DE_ENTRADA`. 🟢
- O **campo de template não atravessa a fronteira** (`BR-C-61`): `dados` é o payload do núcleo, sem renomear nada. 🟢
- O caso de uso **não monta** as dependências de diagrama por requisição — elas chegam por parâmetro, montadas uma vez na borda (`BR-C-62`). 🟢
- `dono` está na assinatura e **não participa de decisão nenhuma** (`BR-C-63`). 🟢
- A rota escolhe o modo de renderização **pelo desfecho** (`BR-C-64`); erro de domínio passa pela tabela de tradução e falha inesperada vira `Ocorreu um erro: {e}` com `success = False` (`BR-C-65`). 🟢
- O `__all__` de `core/path_search.py` declara **apenas** `path_search` (`BR-C-66`): o bloco que reexportava **17 nomes** foi removido. 🟢
- `nomes_de_exibicao` é a lista **ordenada** de `get_name` sobre a árvore, compartilhada pelos três fluxos (`BR-C-67`). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Fazer `strip` nos dois nomes antes de qualquer resolução | Must | Nome com espaços nas pontas resolve como o nome limpo 🟢 |
| RF-02 | Resolver pessoa por nome em duas passadas (igualdade, depois substring), sem diferenciar maiúsculas | Must | Nome exato tem precedência sobre substring 🟢 |
| RF-03 | Reportar **por pessoa** quando o nome não resolve | Must | `"Pessoa 1 '{nome}' não encontrada."` distingue de Pessoa 2; `success = False` 🟢 |
| RF-04 | Montar o dossiê de homônimos dos dois lados, comparando **sem acento** e corrigindo mojibake | Must | Um nome sem acento encontra o registro com acento 🟢 |
| RF-05 | Unir os ids do legado aos exatos **sem repetir e preservando a ordem**, com os parecidos só como `similar_matches` (≤ 5) | Must | A ordem de inserção dos candidatos é estável e determinística 🟢 |
| RF-06 | Marcar a ambiguidade **agregada**, vazia quando cada lado é único | Must | Dossiê `{}` quando não há ambiguidade nem parecidos, e a seção não aparece 🟢 |
| RF-07 | Testar até **5 × 5** combinações, com cache de pares, vencendo a **primeira com caminho** | Must | Três registros de mesmo nome, só um com pais → a conexão é encontrada 🟢 |
| RF-08 | Sem nenhuma combinação com caminho, usar o **primeiro id de cada lado** | Should | O comportamento do legado é preservado como recuo 🟢 |
| RF-09 | Buscar conexão direta por BFS bidirecional subindo **apenas por pais**, com teto de **20 iterações** | Must | Caminho com ancestral comum, rótulo e meioses completos 🟢 |
| RF-10 | Alternar **um nível de um lado** por iteração, costurando sem repetir o ponto de encontro | Must | Nenhum nó aparece duas vezes no caminho 🟢 |
| RF-11 | Tratar pessoas idênticas com caminho trivial | Should | O caminho é a própria pessoa, e ela é o ancestral 🟢 |
| RF-12 | Cortar **em silêncio** no teto, sem distinguir "limite atingido" de "sem caminho" | Must | Caminho mais fundo que o teto devolve ausência, **sem** aviso de limite — decisão humana de 2026-09-30 🟢 |
| RF-13 | Resolver pais por `FAMC`, com fallback no índice, sem duplicar | Must | Pessoa com `FAMC` não consulta o índice; duplicados são removidos 🟢 |
| RF-14 | Resolver cônjuges pelos `FAMS`, com varredura global **apenas** quando a lista fica vazia | Must | `FAMS` parcialmente resolvido **não** dispara o fallback (comportamento intencional) 🟢 |
| RF-15 | Cair para a busca indireta **somente** quando a direta falhar | Must | Conexão com ancestral comum **nunca** é reportada como indireta 🟢 |
| RF-16 | Buscar a indireta pelo caminho mais curto no grafo, com teto de **40 arestas** e compressão dos nós de família | Must | O caminho devolvido contém apenas ids de pessoa, e exige ≥ 2 🟢 |
| RF-17 | Obter o grafo da **árvore recebida por parâmetro** | Must | Nenhum import tardio, nenhuma global; grafo ou nó ausente → `None`, sem exceção 🟢 |
| RF-18 | Tratar `NetworkXNoPath` e `NodeNotFound` como ausência de caminho | Must | Nenhuma exceção do networkx propaga 🟢 |
| RF-19 | Marcar a conexão indireta como **afinidade nos três lugares** | Must | `status = "affinity"`, rótulo próprio e aviso em maiúsculas afirmando que **não** há parentesco consanguíneo 🟢 |
| RF-20 | Fazer a marcação de afinidade em uma **cópia** do dicionário | Should | O dicionário em cache permanece `not_found` 🟢 |
| RF-21 | Produzir rótulo legível, **chave canônica** e **meioses** a partir dos graus | Must | Linha direta, colateral e primos seguem as fórmulas de grau e remoção 🟢 |
| RF-22 | Anexar a **evidência de cada salto**, com família, casal declarado, datas e idade implícita | Must | Um item de evidência por aresta do caminho 🟢 |
| RF-23 | Avisar `data_impossivel` fora de 12–70 anos **sem invalidar o vínculo**, e devolver `plausible = None` sem data | Must | O caminho é mantido; `None` não é falso 🟢 |
| RF-24 | Extrair o ano como o primeiro número de 3 ou 4 dígitos, sem normalizar `ABOUT`/`BEFORE` | Should | Datas qualificadas não são reinterpretadas 🟢 |
| RF-25 | Enumerar **todos** os ancestrais comuns até 12 níveis, limitados a 12, ordenados por meioses, distância e nome | Should | A cardinalidade respeita o teto 🟢 |
| RF-26 | Listar caminhos alternativos **sem descartar nenhum**, com o aviso `caminhos_multiplos` | Must | O caminho exibido é o de menor distância total; os demais estão listados 🟢 |
| RF-27 | Detectar colapso de pedigree por contagem de cadeias, com teto 8 | Should | Aviso nomeia o ancestral e o número de cadeias — que é um **piso** 🟡 |
| RF-28 | Montar a ficha comparável de **13** campos e comparar os homônimos campo a campo | Must | `differences` lista os campos divergentes; `identical_data` só com **nenhuma** divergência 🟢 |
| RF-29 | Marcar identidade ambígua no resultado, com o aviso `homonimo` | Must | Resultado com `status = "ambiguous"` e a contagem de registros 🟢 |
| RF-30 | Reconstruir o índice `nome → ids` quando a **chave derivada do conteúdo** da árvore muda | Must | Duas árvores diferentes reconstroem o índice; a mesma árvore não 🟢 |
| RF-31 | Sanitizar o **id** do nó Mermaid | Must | Apenas `[A-Za-z0-9_]` sobrevive, com prefixo `N_` 🟢 |
| RF-32 | Sanitizar o **rótulo** por **lista branca**, com as entidades HTML aplicadas **depois** do filtro | Must | Aspa dupla e crase neutralizadas; `&`, `<`, `>` viram entidades; acentos e pontuação legítima sobrevivem 🟢 |
| RF-33 | Emitir o diagrama da conexão **direta**, fundindo o casal do ancestral comum em um nó e omitindo os membros como nós próprios | Must | `flowchart BT`; nó de casal presente quando o ancestral não é extremidade do caminho 🟢 |
| RF-34 | Emitir o diagrama da conexão **indireta** em subgrafos aninhados `direction BT`, com a aresta de casamento entre âncoras invisíveis | Must | Cada `subgraph` é fechado por context manager; a aresta é rotulada como casamento 🟢 |
| RF-35 | Aplicar cores fixas por papel nos nós | Should | p1 verde, p2 vermelho, MRCA/casal amarelo, casal da afinidade laranja 🟢 |
| RF-36 | Delegar ao diagrama direto quando faltar pré-requisito do indireto | Must | Sem par de cônjuges ou sem um dos ramos, o diagrama sai na forma direta com `mrca=None` 🟢 |
| RF-37 | Entregar as **sete consultas de domínio** ao renderizador, para que ele não importe `core` | Must | `reporting/` não importa nenhum módulo de `core/` 🟢 |
| RF-38 | Derivar o **desfecho** de `(payload, sucesso)`, nunca do texto da mensagem | Must | Os três valores são alcançáveis e independentes do literal 🟢 |
| RF-39 | Devolver `ResultadoDeBusca` congelado com `dados` sem renomear, dependências por parâmetro e `dono` sem comportamento | Must | `dados` é o payload do núcleo; `deps` chega montado; `dono` não altera nada 🟢 |
| RF-40 | Escolher o modo de renderização **pelo desfecho** na rota | Must | Sem conexão → cartão com sucesso; erro de entrada → alerta de erro 🟢 |
| RF-41 | Passar o erro de domínio pela tabela de tradução; falha inesperada vira `Ocorreu um erro: {e}` | Must | Nenhuma exceção derruba a aplicação 🟢 |
| RF-42 | Declarar em `__all__` **apenas** `path_search` | Could | O bloco que reexportava 17 nomes não existe mais 🟢 |
| RF-43 | Compartilhar `nomes_de_exibicao` como lista **ordenada** entre os três fluxos | Must | A ordem da lista é contrato da tela 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Performance | BFS **bidirecional** em vez de unidirecional: reduz a explosão combinatória de subir duas linhagens | `path_finding.py:find_ancestral_path` | 🟢 |
| Performance | Tetos explícitos: **20 iterações** no BFS, **40 arestas** no indireto, **12** ancestrais, **8** cadeias, **5** candidatos por lado | `path_finding.py`, `documentary_relationship.py`, `core/path_search.py` | 🟢 |
| Performance | 🔴 `get_children` varre **todas** as famílias do arquivo, **sem índice**, a cada chamada — e `person_summary` o chama uma vez por ficha | `documentary_relationship.py:get_children` | 🟢 |
| Performance | 🔴 `person_a` e `person_b` são **fichas completas** em cada resultado: no caso real de 71 conexões foram **142 fichas** para uma tela que exibe poucas | `documentary_relationship.py:documentary_relationship` | 🟢 |
| Performance | 🟡 `_diferencas` é chamado **duas vezes** em `homonym_dossier` (uma para `differences`, outra dentro de `identical_data`), e cada chamada remonta as fichas de todos os ids | `documentary_relationship.py:homonym_dossier` | 🟢 |
| Segurança | O **escape do rótulo é a única defesa** contra conteúdo do GEDCOM quebrar o diagrama. `securityLevel: 'strict'` cobre XSS, **não** a gramática | `mermaid_render.py:_LABEL_SEGURO`, `templates/index.html` | 🟢 |
| Confiabilidade | **Nenhuma data invalida vínculo**: o sistema registra a evidência e avisa | `documentary_relationship.py:hop_evidence` | 🟢 |
| Reprodutibilidade | 🟡 A ordem de `common_ancestors` e de `additional_paths` **pode variar com o `PYTHONHASHSEED`** quando dois ancestrais empatam em meioses, distância **e** nome | `documentary_relationship.py:find_all_common_ancestors` | 🟡 |
| Reprodutibilidade | A escolha entre homônimos nesta unit **é determinística**: percorre uma **lista** com teto de 5×5 — diferente do desempate do matching de `analise-dna`, que percorria um `set` até 2026-10-05 | `core/path_search.py:path_search` | 🟢 |
| Manutenibilidade | 🟢 **A inversão de camada de 2026-10-05 foi fechada:** `reporting/mermaid_render.py` **não importa `core`**; recebe o resolvedor de diagrama. O ciclo `core/` ↔ `reporting/` deixou de existir (`ADR-34`) | `core/diagram_domain.py:resolvedor_de_diagrama` | 🟢 |
| Manutenibilidade | 🔴 **O renderizador ainda contém decisão de negócio** — decidir o casal do ancestral comum é decisão de domínio que vive na apresentação, por decisão declarada (`ADR-11`) | `mermaid_render.py:generate_mermaid_graph` | 🟢 |
| Observabilidade | **Nenhum log, métrica ou trace.** A única visibilidade é o texto do caminho, o diagrama e os avisos | — | 🟢 |
| Internacionalização | Todas as mensagens e rótulos ao operador são literais em português | `core/path_search.py`, `documentary_relationship.py` | 🟢 |

> Inferido a partir do código. **Não** há autenticação, cache entre requisições, fila, retry ou timeout — as linhas correspondentes foram omitidas por falta de evidência.

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

Dado um par que compartilha um ancestral alcançado por mais de uma cadeia de pais
Quando o parentesco documental é calculado
Então o aviso "colapso_de_pedigree" nomeia o ancestral e o número de cadeias
E o número apresentado é um piso, porque a contagem para no teto de 8

Dado um nome vindo do GEDCOM que contém aspa dupla seguida de crase
Quando o diagrama é emitido
Então o rótulo do nó é neutralizado
E o diagrama continua sendo um flowchart válido

Dado um nome com "&", "<" ou ">"
Quando o diagrama é emitido
Então esses caracteres aparecem como entidades HTML
E os caracteres legítimos (acentos, pontos, parênteses) sobrevivem intactos

Dado duas pessoas existentes e nenhum caminho entre elas em nenhum dos dois estágios
Quando o operador busca o caminho
Então a tela exibe "Nenhuma conexão encontrada entre 'X' e 'Y'."
E o desfecho é SEM_RESULTADO, com success = True

Dado um nome que não existe na árvore
Quando o operador busca o caminho
Então a tela exibe "Pessoa 1 'X' não encontrada." (ou Pessoa 2, conforme o caso)
E o desfecho é ERRO_DE_ENTRADA

Dado um serviço que carregou duas árvores diferentes no mesmo processo
Quando o dossiê de homônimos é consultado na segunda
Então o índice de nomes corresponde à segunda árvore
E nenhuma ficha de pessoa da primeira árvore é listada
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| RF-32 Escape do rótulo | **Must** | **Sem isso o diagrama inteiro deixa de renderizar** — foi o `BUG-20260929-J6PQ` |
| RF-09/RF-10/RF-12 Conexão direta, alternância e teto | **Must** | Núcleo da busca |
| RF-15/RF-16/RF-17/RF-18 Conexão indireta | **Must** | Sem o fallback, todo parentesco por afinidade fica invisível |
| RF-21/RF-22 Rótulo, meioses e evidência por salto | **Must** | É a saída que o operador lê |
| RF-01/RF-02/RF-03/RF-04 Resolução de pessoas e dossiê | **Must** | Pré-condição de todo o fluxo |
| RF-19/RF-20 Marcação de afinidade | **Must** | Redundância deliberada: impede leitura de afinidade como consanguinidade |
| RF-38/RF-39/RF-40 Desfecho, resultado tipado e rota | **Must** | Sem o desfecho, o adaptador inferiria o modo de renderização **do texto** |
| RF-23 Aviso de data impossível | **Must** | Impede que um vínculo cronologicamente absurdo passe como normal |
| RF-31 Sanitização do id do nó | **Must** | Sem ela, um `xref_id` inesperado quebra o diagrama |
| RF-33/RF-34/RF-36 Emissão dos diagramas | **Must** | Saída principal |
| RF-41 Tradução de erro | **Must** | Mantém o texto observável com a condição agora tipada |
| RF-37 Resolvedor de diagrama | **Must** | É o que fecha o ciclo `core/` ↔ `reporting/` |
| RF-05/RF-06/RF-07/RF-29 Escolha entre homônimos com aviso | **Should** | O fluxo funciona com o primeiro id; a taxa de acerto é que muda |
| RF-26 Caminhos alternativos | **Should** | O caminho principal basta para responder |
| RF-25 Enumeração de ancestrais comuns | **Should** | Enriquece o resultado; o rótulo vem do ancestral principal |
| RF-27 Colapso de pedigree | **Should** | Aviso importante, mas não altera o caminho |
| RF-28 Ficha e diferenças | **Should** | Enriquece a conferência; o veredito não depende dela |
| RF-35 Cores por papel | **Should** | Leitura visual, não resultado |
| RF-24 Extração do ano | **Should** | Alimenta a plausibilidade, que é aviso |
| RF-30 Invalidação do índice | **Should** | Sem ela a busca continua correta para uma árvore por processo |
| RF-11 Pessoas idênticas | **Could** | Caso de borda acionado raramente |
| RF-08 Recuo para o primeiro id | **Could** | Só ocorre quando nenhuma combinação tem caminho |
| RF-42 `__all__` mínimo | **Could** | Higiene de módulo, sem consumidor de produção |

## Rastreabilidade de Código

| Arquivo | Função / símbolo | Cobertura |
|---------|------------------|-----------|
| `src/application/path_search.py` | `path_search` (caso de uso), `_desfecho`, `ResultadoDeBusca` | 🟢 |
| `src/application/__init__.py` | `Desfecho`, `nomes_de_exibicao` | 🟢 |
| `src/core/path_search.py` | `path_search` (núcleo), `_candidatos`, `_homonimos`, `AVISO_AFINIDADE`, `LIMITE_DE_CANDIDATOS`, `__all__` | 🟢 |
| `src/core/path_finding.py` | `find_ancestral_path`, `find_indirect_path`, `MAX_DEPTH`, `MAX_HOPS` | 🟢 |
| `src/core/family_navigation.py` | `find_person_by_name`, `get_parents`, `get_spouses`, `are_spouses`, `split_path_by_marriage`, `pick_spouse_for_couple`, `exclude_tail` | 🟢 |
| `src/core/documentary_relationship.py` | `documentary_relationship`, `documentary_label`, `person_summary`, `homonym_dossier`, `_diferencas`, `hop_evidence`, `find_all_common_ancestors`, `_cadeias_ate`, `normalizar`, `parse_year`, `get_children`, `_chave_de`, `_indice_por_nome` | 🟢 |
| `src/core/diagram_domain.py` | `resolvedor_de_diagrama` | 🟢 |
| `src/reporting/mermaid_render.py` | `_mermaid_sid`, `_mermaid_label`, `_LABEL_SEGURO`, `generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge` | 🟢 |
| `src/application/traducao.py` | `traduzir` — compartilhado com as outras units | 🟢 |
| `src/app.py` | ramo `path_search` do `index` | 🟢 |
| `src/templates/index.html` | badge de status do resultado; `securityLevel: 'strict'` | 🟢 |
| `tests/test_path_search.py`, `test_mermaid_escape.py`, `test_characterization_mermaid.py`, `test_desfecho_do_resultado.py`, `test_arvore_devolvida.py`, `test_dependencias_nucleo.py` | cobertura do fluxo, do contrato de escape, da caracterização e do desfecho | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*
