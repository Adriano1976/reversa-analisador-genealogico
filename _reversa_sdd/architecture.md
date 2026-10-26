# Arquitetura — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de **2026-10-10**. Substitui o `architecture.md` de 2026-10-05, que descrevia **3 containers**, o estado global em `core/gedcom_state.py`, **dois ciclos de pacote** e a ausência de banco de dados.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-10-pre-reextracao/architecture.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Detalhamento: `c4-context.md` (nível 1) · `c4-containers.md` (nível 2) · `c4-components.md` (nível 3) · `erd-complete.md` · `adrs/` (**36** decisões) · `domain.md` · `state-machines.md` · `permissions.md`
> Atualização de **2026-10-17**: §3 absorve o adendo `025` — a construção do grafo recebe as famílias já lidas, e não o leitor do arquivo.

---

## 1. Visão Geral da Arquitetura

Aplicação **web monolítica de um único processo**, com renderização **server-side** (Flask 3.1.3 + Jinja2) servida por **waitress 3.0.2**, **sem autenticação**, com **persistência de arquivos em disco** e **histórico opcional em PostgreSQL**.

O que define a arquitetura de hoje **não é o que definia a de 2026-10-05**. A separação em camadas existe desde então, mas o **mecanismo de integração mudou de natureza**: era **estado global mutável**, e hoje é **passagem de parâmetro e injeção explícita**.

| Camada | Onde | Linhas úteis | Contrato |
| --- | --- | ---: | --- |
| **Borda HTTP** | `src/app.py` | 559 | Valida entrada, despacha por `action`, **escolhe o render pelo desfecho**, monta as duas listas por processador de contexto, serve as **duas artes**, sobe o servidor com guarda de instância única. **Nenhuma regra de domínio**; **19 regras de superfície** (`BR-T-12..17`, `BR-E-01..06`) 🟢 |
| **Aplicação** | `src/application/` (6 módulos) | 523 | Um **caso de uso por fluxo**, que **orquestra e não decide**: chama o núcleo, projeta o resultado, registra o histórico e traduz exceções 🟢 |
| **Portas** | `src/ports/` (2 módulos) | 669 | **Quatro `Protocol`** e **três adaptadores concretos**. É a fronteira que a Onda 3 vai estender 🟢 |
| **Núcleo** | `src/core/` (15) + `parsers/` (3) + `reporting/` (3) + `utils/` (5) | ~3.300 | Toda a decisão de domínio. **Não conhece HTTP** 🟢 |
| **Apresentação** | `src/templates/index.html` | 731 | Tela única: upload, **duas abas de lista**, busca, análise, **quatro seções de resultado**, confronto e a masthead com arte. Bootstrap 5.3.3 e Mermaid 10 por CDN 🟢 |

**O que substituiu o estado global.** A árvore do GEDCOM é uma **tupla de quatro posições** `(people, families, graph, child_to_family)` que **entra por parâmetro em toda função do núcleo**. Três consequências diretas, todas verificáveis no código:

| Antes (até 2026-10-05) | Agora |
| --- | --- |
| `core/gedcom_state.py` mantinha o estado e era importado por 8 de 19 módulos | O módulo **não existe**; `core/registro.py` guarda só `get_name` e `ref_id`, que **nunca foram estado** |
| `people`/`families`/`child_to_family` eram mutados *in place*, e `graph` era reatribuído — o que obrigava import **dentro da função** | A árvore é um **valor**; não há mutação de global nem import tardio |
| O contador `versao` sinalizava a invalidação de índices derivados | Não existe mais: o cache de nomes deriva a chave do **conteúdo** recebido |

**O funcionamento é de análise sob demanda:** a cada `POST`, a árvore é obtida a partir da referência recebida no formulário e viaja como argumento até o fim da requisição. **Há um cache de árvore por processo** (feature 047, `ADR-38`): ligado por padrão, chaveado por `(caminho absoluto, mtime_ns, tamanho)`, com teto de uma árvore e *single-flight* — a segunda ação sobre o mesmo arquivo não paga o parse. O cache vive no **adaptador**, não no núcleo; desligá-lo (`ANALISADOR_CACHE_DE_ARVORE=0`) devolve o parse por requisição. Detalhamento em `addenda/047-cache-dos-indices-da-arvore.md`.

---

## 2. Containers

**Quatro containers** — detalhamento em `c4-containers.md`:

1. **Aplicação web** — o único processo (Python 3.14.6, Flask, waitress). **Nenhum estado de domínio em memória**; os únicos estados de processo são derivados e descartáveis: o cache de nomes (por conteúdo) e o cache da árvore, no adaptador (`ADR-38`).
2. **Navegador do usuário** — HTML/Jinja2 + Bootstrap + **Mermaid renderizado no cliente**, e cliente de **duas artes** servidas com `ETag`.
3. **Sistema de arquivos local** (`src/uploads/` e `src/uploads/_aposentados/`) — arquivos **imutáveis no conteúdo** e **mutáveis na posição**.
4. **PostgreSQL 16** *(novo)* — o **histórico das análises**, em 6 tabelas. **Opcional:** sem `DATABASE_URL` o registrador é nulo e a tela não muda um byte.

**Não há** container de fila, cache externo, worker assíncrono ou API externa. 🟢 O cache da árvore é **memória do processo**, não um serviço.

**Concorrência:** o processo é **single-instance por construção** (socket exclusivo ligado antes de servir) e **multi-thread** (`ANALISADOR_THREADS = 4`). 🟢 **A árvore cacheada é compartilhada entre threads, e isso é seguro por construção:** o conteúdo dos quatro componentes não é mutado depois do parse; os índices derivados são pendurados no grafo de forma idempotente (três `setattr`, sem trava, sempre o mesmo valor), e o *single-flight* garante um parse por chave. O que resta de concorrência real é a disputa sobre o **armazenamento em disco** — mecanismo 🟢, alcance não medido 🟡.

---

## 3. Componentes e estrutura de pacotes

**31 componentes** em sete unidades — inventário completo em `c4-components.md`.

| Pacote | Módulos | Papel declarado |
| --- | ---: | --- |
| *(raiz)* | 1 | `app.py`: a borda HTTP |
| `application/` | 6 | Casos de uso, desfecho, reenvio, tradução |
| `ports/` | 2 | Os quatro `Protocol` e os três adaptadores |
| `core/` | 15 | Decisão de domínio, sem saber de HTTP |
| `parsers/` | 3 | Leitura do mundo de fora — **devolve valor**; o grafo transforma dado já lido |
| `reporting/` | 3 | Emissão do diagrama e as funções puras da lista |
| `utils/` | 5 | Autoridades únicas transversais |

**A construção do grafo não lê o arquivo** (adendo `025`, 2026-10-17): `carregar_arvore` materializa `list(parser.records0("FAM"))` **uma vez** e a entrega a `build_graph_from_parser(people, familias)`; a função do grafo **não recebe mais o `GedcomReader`**. A árvore, a ordem de inserção de nós e arestas (`@ordem`) e o `child_to_family` continuam idênticos — o que saiu foi a **segunda materialização** dos registros `FAM`.

### 🟢 Os ciclos de pacote FORAM QUEBRADOS

A rodada anterior registrava **dois ciclos** como achado vermelho. **Os dois foram fechados em 2026-10-06** (`ADR-34`):

| Ciclo | Como foi quebrado |
| --- | --- |
| **`core/` ↔ `reporting/`** | `core/diagram_domain.py` expõe `resolvedor_de_diagrama(arvore)` — sete consultas **ligadas à árvore** por `functools.partial` — e o renderizador a recebe **por parâmetro**. Ele **não importa `core`** |
| **`core/` ↔ `parsers/`** | `norm_name` foi para `utils/name_keys.py`, e as funções de leitura de CSV entram **por injeção** (a classe `Dependencias`, montada na borda). `core/` **não importa `parsers/`** |

**`reporting/` continua não sendo folha, e isso é decisão declarada** (`ADR-11`): decidir o casal do ancestral comum, o ancestral que ancora o ramo e o ponto de corte por casamento é decisão de **negócio**. O que mudou foi **quem busca o dado**, não onde a decisão mora. **`utils/` continua sendo o único pacote folha real**, e ganhou `name_keys.py` justamente para continuar sendo.

---

## 4. Modelo de Dados

**Há banco de dados, e ele é opcional.** O ERD completo (**43 estruturas**, com PK/FK lógicos e — no banco — **reais**) está em `erd-complete.md`; os campos, tipos, padrões e sentinelas, em `data-dictionary.md`.

| Onde o dado vive | Estruturas | Persiste? |
| --- | ---: | --- |
| Memória, por requisição | 24 | Não — morre com a requisição |
| Memória, de módulo | 2 (o cache de nomes e o cache de árvores) | Vive com o processo: o primeiro chaveado por conteúdo, o segundo pelo arquivo (`ADR-38`) |
| Disco | 2 (na pasta e aposentado) | **Sim** — conteúdo imutável, **posição mutável** |
| Payload de fronteira | 9 | Não — uma requisição |
| **PostgreSQL** | **6 tabelas** | **Sim, e é opcional** |

> 🟡 **O cache de árvores é memória de processo, não domínio.** Custa ~337 MB por árvore de ~19 mil pessoas, mais ~31 MB de índices; o teto é 1 e a invalidação é pelo arquivo. Desligado, a árvore morre no fim da requisição — a diferença é o tempo de vida em RAM, não o conteúdo.

> ⚠️ **`None` significa "não sei / não existe", nunca zero.** É invariante do sistema.
> ⚠️ **A árvore NÃO é duplicada no banco.** Ela continua sendo o arquivo imutável de `src/uploads/`, referenciado por `tree_ref`; o que se grava é o **retrato** das pessoas daquela análise.
> 🔴 **Nenhum código de `src/` lê as tabelas.** A persistência só escreve — não há como reconstruir uma análise pela aplicação.
> 🔴 **O banco persiste dado pessoal sem política de retenção** (`L-29`): nome, sexo, datas e local de nascimento, inclusive de pessoas vivas.

---

## 5. O Fluxo que Define o Sistema

A decisão de arquitetura mais consequente **não** é estrutural, é de domínio: o fluxo de análise está separado em **três eixos que não se contaminam** e um **confronto** que os compara sem alterá-los (`ADR-14`). **Nenhuma das features 005 a 012 tocou nisso.**

```text
Parentesco documental (GEDCOM)  ─┐
                                 ├─►  CONFRONTO  ─►  COMPATIVEL | POSSIVEL | CONFLITANTE | INCONCLUSIVO
Evidência genética (CSV)  ───────┤
   └─► Possibilidades (SCP 4.0) ─┘
```

- O **parentesco documental** nunca lê cM; a **evidência genética** não conhece o GEDCOM. 🟢
- O DNA **não** altera o parentesco documental: conflito vira **aviso e rol de causas**, nunca reescrita de vínculo. 🟢
- O cM **nunca** é usado sozinho para afirmar parentesco. 🟢

**O que a estrutura ganhou em volta desse fluxo**, e que é a marca desta rodada:

| Ganho | Efeito arquitetural |
| --- | --- |
| **Fronteira de aplicação** com quatro portas | O núcleo não conhece disco, banco nem HTTP; a Onda 3 tem onde ancorar |
| **Projeção pura** do resultado | O adaptador de banco recebe dado **plano** e só escreve — é o que permite a persistência ser opcional |
| **Desfecho em três valores** | O modo de renderização deixou de ser inferido do texto da mensagem |
| **Armazenamento por conteúdo com aposentadoria** | O sistema passou a ter seu **primeiro ciclo de vida** durável (a posição do arquivo) |
| **Arte derivada com receita única** | A apresentação ganhou um contrato verificável por pixel |

Detalhamento das regras em `domain.md` §2 e §3; as máquinas de decisão, em `state-machines.md`. As **233 regras** catalogadas estão em `code-analysis.md` e em `.reversa/context/modules.json`; os fluxos por unidade, em `flowcharts/`.

---

## 6. Mapa de Integrações Externas

| Sistema externo | Tipo | Protocolo / formato | Uso | Conf. |
| --- | --- | --- | --- | --- |
| **Nenhuma API REST/GraphQL** consumida ou produzida | — | — | A aplicação é standalone | 🟢 |
| **Nenhum webhook, fila, evento ou mensageria** | — | — | Não há integração assíncrona | 🟢 |
| **PostgreSQL 16** | Banco | TCP local (`127.0.0.1:5432`), driver `psycopg2`, **sem TLS** | Histórico das análises. **Opcional** | 🟢 |
| **GEDCOM (`.ged`)** | Arquivo | Formato GEDCOM, lido por `ged4py` | Parsing da árvore; **parseado a cada requisição** | 🟢 |
| **CSV de matches de DNA** | Arquivo | CSV com colunas de Nome, cM, kit/ID/e-mail; `utf-8` com recuo para `latin-1` | Agregação de segmentos | 🟢 |
| **CDN de assets web** | Assets | HTTPS | Bootstrap 5.3.3 e Mermaid 10, carregados pelo navegador | 🟢 |
| **Exportadores de CSV** | Indireto | GEDmatch, MyHeritage, FamilyTreeDNA e similares | A detecção de coluna de ID depende do padrão `[A-Z]{2}\d{7}`; a leitura é tolerante a separador, preâmbulo e linha torta | 🟡 |
| **Fonte estatística** | Dado embutido | Tabela publicada do **Shared cM Project 4.0** (março/2020, 59.714 envios) | 27 relações publicadas | 🟢 |
| **Bibliotecas de imagem** | Dependência **de teste** | `PIL` no `.venv`, **fora de `requirements.txt`** | Gerar as duas artes derivadas. **O container não precisa dela** | 🟢 |

**Nenhuma integração de rede com terceiros.** O único tráfego de saída é o download dos assets de CDN feito pelo navegador do próprio usuário, e o `INSERT` no Postgres local. 🟢

---

## 7. Dívidas Técnicas Consolidadas

Consolidação das **28** dívidas do `code-analysis.md` §9 com os achados desta fase. Ordenadas por **gravidade × probabilidade de morder quem reimplementar**.

| # | Dívida | Gravidade | Referência |
| ---: | --- | --- | --- |
| 1 | 🔴 **Colisão possível da chave do cache de nomes.** `(len, primeira chave, última chave)` é igual para duas árvores do mesmo tamanho; o dossiê de homônimos passa a listar xrefs de **outra** árvore, sem exceção | 🔴 **Alta** | `documentary_relationship._chave_de`; `L-24`, `E-05` |
| 2 | 🔴 **Ausência de identidade e de isolamento.** Sem `owner_id` **funcional**, sem sessão e sem autorização. A chave de conteúdo é **identificador, não segredo**. Mitigado por aceite de risco | 🔴 **Alta** | `BUG-20260929-BJJH`; `permissions.md` §4; `adrs/18`, `adrs/26` |
| 3 | 🔴 **`psycopg2-binary` pinado e ausente do `.venv`** — a persistência fica desligada no interpretador oficial por ambiente, e não por decisão | 🔴 **Alta** | `L-26`; `adrs/13`, `adrs/27` |
| 4 | 🔴 **O histórico persiste dado pessoal sem retenção, expurgo nem consentimento** — inclusive de pessoas vivas. Apagar a árvore já não apaga o retrato | 🔴 **Alta** | `L-29`, `P-07`; `adrs/27` |
| 5 | 🔴 **Não há teste do caminho de gravação no banco.** Erro de SQL, de ordem de FK ou de tipo só apareceria no contêiner | 🔴 Alta | `L-28`, `X-05` |
| 6 | 🟡 **Ordem de `common_ancestors` e `additional_paths` sensível ao `PYTHONHASHSEED`** em empate triplo — mesma classe do defeito que o `matching` fechou | 🟡 Média | `L-25`; `adrs/23`, `adrs/36` |
| 7 | 🟡 **O resultado da suíte depende do ambiente:** com `DATABASE_URL` presente e sem o driver, 2 testes falham | 🟡 Média | `L-27` |
| 8 | 🟡 **`get_children` varre todas as famílias, sem índice**, e `person_summary` a chama em cada ficha | 🟡 Média | `L-20` |
| 9 | 🟡 **Fichas completas por pessoa em cada resultado** (142 no caso real de 71 conexões) | 🟡 Média | `L-20` |
| 10 | 🟡 **O caminho indireto não passa pela checagem de plausibilidade de datas** (12–70 só no direto) | 🟡 Média | `domain.md` §3.1 |
| 11 | 🟡 **O CSV de DNA não tem validação de conteúdo** — só a forma do nome | 🟡 Média | `P-05` |
| 12 | 🟡 **Endogamia e colapso de pedigree não são corrigidos**: o colapso é detectado, mas **não altera o veredito** | 🟡 Média | `L-17`; `adrs/21` |
| 13 | 🟡 **Relações mais distantes não publicadas na SCP 4.0** — justamente onde o caso real cai | 🟡 Média | `L-18` |
| 14 | 🟡 **O estado "aposentado" não é consultável pela aplicação** — não há coluna nem índice; quem sabe é o sistema de arquivos | 🟡 Média | `M-05` |
| 15 | 🟡 **"gravado" e "inativo" são indistinguíveis na tela** — os dois produzem aviso nulo | 🟡 Média | `M-06` |
| 16 | 🟡 **A corrida sobre o armazenamento em disco permanece** (`guardar` e `aposentar` verificam e depois agem) | 🟡 Média | `M-03`, `P-02` |
| 17 | 🟡 **Os quatro estados do confronto são também nomes de classe CSS**, sem teste que prenda o par | 🟡 Média | `code-analysis.md` §4.7 |
| 18 | 🟡 **`_diferencas` é chamado duas vezes** em `homonym_dossier`, remontando as fichas | 🟡 Baixa | `flowcharts/busca-caminho.md` §12 |
| 19 | 🟡 **`_avaliar_kit` recebe `meioses_documental` e não o usa** — superfície morta que convida a reintroduzir o critério por meioses | 🟡 Baixa | `flowcharts/analise-dna.md` §6 |
| 20 | 🟡 **`INCONCLUSIVO` é o último da ordem de conservadorismo** — um kit sem cM não rebaixa o resultado de outro kit | 🟡 Baixa | `flowcharts/analise-dna.md` §6 |
| 21 | 🟡 **`sha256` da tela mantido à mão** (três atualizações em 2026-10-10) e **caixa de regressão de arte** que descreve composição extinta | 🟡 Baixa | `adrs/29` |
| 22 | 🟡 **A arte derivada não é verificada dentro do container** | 🟡 Baixa | `X-06` |
| 23 | 🟡 **A coluna "área de teste" da matriz perdeu granularidade por arquivo** (39 arquivos) | 🟡 Baixa | `X-07` |
| 24 | 🟢 **Teto de 20 iterações do BFS corta em silêncio.** Contrato **aceito** | 🟢 Baixa (aceita) | decisão de 2026-09-30 |
| 25 | 🟢 **`get_spouses` esconde cônjuges** quando o primeiro `FAMS` resolve. Contrato **aceito** | 🟢 Baixa (aceita) | decisão de 2026-09-30 |
| 26 | 🟢 **`cm_estimator` segue como legado fora do fluxo**, com faixas sem fonte verificável | 🟢 Baixa | `adrs/19` |
| 27 | 🟢 **Duplicatas literais** em `COMMON_SURNAMES` e no mapa de mojibake | 🟢 Baixa | `code-analysis.md` §4.6 |
| 28 | 🟢 **Ausência de CI/CD.** O workflow de GitHub Pages foi **removido em 2026-10-08**; a publicação virou passo manual. **Não há pipeline de teste, build ou análise estática** | 🟢 Baixa | `c4-containers.md` |

### Dívidas **fechadas** desde a extração anterior

| Dívida de 2026-10-05 | Como foi fechada |
| --- | --- |
| **Ciclos de pacote `core/` ↔ `reporting/` e `core/` ↔ `parsers/`** (era #5, Média) | ✅ ✅ **fechadas em 2026-10-06** pelo `ADR-34`, com o resolvedor de diagrama e a injeção das dependências de borda |
| **Contaminação entre requisições concorrentes** (era #3, **Alta**) | ✅ **fechada em 2026-10-07** pelo `ADR-24`: a árvore entra por parâmetro e **não há estado global** |
| **Nada é persistido entre requisições** (era #8, Média) | ✅ **executada em 2026-10-08** pela feature 008 — e com duas dívidas **novas** em troca (#3 e #4 desta tabela) |
| **Superfícies de compatibilidade** reexportando nomes que ninguém usa (era #17) | ✅ **removidas** (`path_search` com 17 nomes, `dna_analysis` com os dois blocos), restando uma exceção declarada: `norm_name` |
| **Desempate não determinístico** (era #1, Alta) | ✅ **implementado em 2026-10-06** e congelado por teste |
| **Divergência de ambiente de versões** (era #2) | 🔄 **substituída** pela divergência **de presença** do `psycopg2` (#3 desta tabela) |

---

## 8. Decisões Arquiteturais

**38 decisões** documentadas em `adrs/`, reconstruídas de **246 commits** e dos registros de bug e de mitigação:

| Faixa | Assunto |
| --- | --- |
| `01`–`08` | Fundação: reconstrução em módulos, rota fina, Mermaid no cliente, oráculo congelado, escape do rótulo, política de edição do legado, autoridade de limpeza, `HARD_MIN`/`GIVEN_MIN` |
| `09`–`13` | Estrutura: remoção das entidades decorativas, `/src`, pacotes por responsabilidade, waitress + instância única, pinagem de dependências |
| `14`–`17` | Domínio: **separação dos três eixos**, sobreposição de faixas, leitura tolerante do CSV, upload por chave de conteúdo |
| `18`–`23` | Operação e contrato: single-tenant por aceite de risco, heurísticas declaradas, formatação só na apresentação, endogamia, ordem de apresentação, desempate determinístico |
| **`24`–`35`** | **O ciclo forward 005 a 012:** núcleo puro, fronteira de aplicação, dono como costura, persistência opcional, Docker por permissão, arte derivada, aposentar, reenvio com substituição, elegibilidade por forma de nome, desfecho e projeção pura, ciclos quebrados, pasta de uploads |
| **`36`** | **Revalidação das 23 herdadas** — quadro completo, com as **seis** que precisam de ressalva (`02`, `06`, `12`, `13`, `17`, `23`) |
| **`37`–`38`** | **Depois do ciclo forward:** observabilidade em camadas (registro por requisição e auditoria) e **cache da árvore** por processo (chave pelo arquivo, teto 1, *single-flight*) |

---

## 9. Resumo para o Reversa

- **Containers:** **4** — aplicação web (único processo, **sem estado de domínio**, com um cache de árvore em processo), navegador (renderiza Mermaid e busca as duas artes), sistema de arquivos (conteúdo imutável, **posição mutável**) e **PostgreSQL 16 opcional**. Sem fila, cache externo ou API externa. 🟢
- **Camadas:** **7 unidades**, com **dependência estritamente descendente** — os dois ciclos de pacote da rodada anterior estão **fechados**. A integração deixou de ser estado global e passou a ser **passagem de parâmetro e injeção**. 🟢
- **Componentes:** **31**; `utils/` é o único pacote folha real; `reporting/` contém decisão de negócio de apresentação, **por decisão declarada**. 🟢
- **Integrações externas:** **zero** de rede com terceiros. Entrada por arquivo (`.ged`, `.csv`), assets por CDN no navegador, uma tabela estatística embutida e **um banco local opcional**. 🟢
- **Modelo de dados:** **43 estruturas**, das quais **6 são tabelas Postgres reais** com FK e `CHECK`. Sem constraint no GEDCOM em memória; **com** constraint onde foi implementado. 🟢
- **Regra central:** os **três eixos que não se contaminam** + confronto em quatro estados — **intocada** pelas features 005 a 012. 🟢
- **Dívidas técnicas:** **28 consolidadas**, sendo **5 de gravidade alta** — e **quatro delas são consequência direta do ciclo forward** (colisão do cache, driver ausente, dado pessoal sem retenção, ausência de teste de gravação). 🟢
- **Decisões:** **38 ADRs** (15 novas, das quais 1 de revalidação); **19 decisões humanas verificadas**, das quais **1 revertida** (010 → 012). 🟢
- **Máquinas de estado:** **1 ciclo de vida real** (a posição do arquivo) e **4 máquinas de decisão** — detalhamento em `state-machines.md`. 🟢
- **Instrumentação de desenvolvimento (fora do runtime):** oráculo congelado (`oracle/`), harness diferencial com **paridade 100%**, 7 goldens de tela (`screens/`), a suíte de migração (`migration/`) e os 38 ADRs. O repositório também hospeda o sub-projeto Node `plugins/dsh-markdownlint/` e a pasta `docs/` publicada no GitHub Pages. **Nada disso faz parte do sistema em execução.** 🟢

---

*Gerado pelo Reversa-Architect em 2026-10-10 (re-extração, nível completo).*
