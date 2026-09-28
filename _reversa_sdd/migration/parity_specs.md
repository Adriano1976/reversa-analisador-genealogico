---
schemaVersion: 1
generatedAt: 2026-09-28T04:21:46Z
reversa:
  version: "1.2.58"
kind: parity_specs
producedBy: inspector
hash: "sha256:b1687e94d095b45228780b738cd573198a96765f8adee57964987b5e4f78dd39"
---

# Parity Specs

> Estratégia de validação de equivalência comportamental entre legado e sistema novo, adaptada ao paradigma escolhido em `paradigm_decision.md`.

## Estratégia geral

- **Modos de validação aplicáveis**:
  - [ ] Shadow mode (espelhamento de tráfego com comparação assíncrona) — **NÃO APLICÁVEL**
  - [x] **Characterization tests (suíte derivada do comportamento atual do legado)** — **modo primário**
  - [x] Contract tests (interfaces externas)
  - [ ] Data parity (snapshots e checksums) — **NÃO APLICÁVEL**
  - [x] **Golden file comparison** (paridade de telas, modo literal/híbrido)
  - [x] **Contract test de tela** (paridade de telas, modo modernizado)
  - [x] **Differential execution** (execução lado a lado do oráculo e do candidato)

### Por que Shadow mode e Data parity estão desmarcados — e isso não é omissão

**Shadow mode exige tráfego de produção para espelhar.** O legado **nunca foi deployado** (`architecture.md` §5 dívida #3: sem CI/CD, sem Docker, sem workflow; `inventory.md` §6: nenhum workflow, nenhum Dockerfile) e **não tem usuários** (`domain.md` §4: sem autenticação, uso local single-user). Não existe tráfego a espelhar. Marcá-lo como aplicável seria prescrever uma estratégia inexecutável.

**Data parity exige dados a comparar.** O legado **não tem banco de dados** — estado 100% em memória (`architecture.md` §1 e §5, `inventory.md` §5), sem schema, sem `data-dictionary.md`. O `data_migration_plan.md` registra volume **zero** em todas as entidades. Não há snapshot a tirar nem checksum a comparar.

**O que substitui ambos**: **differential execution em lote**. O `migration_strategy.md` (estratégia `C — Parallel Run em ondas`, confirmada pelo usuário) prescreve exatamente isso, e o próprio SKILL do Designer já exigia *"componentes críticos isoláveis para comparação"* para viabilizar Parallel Run. Como o alvo é **Python, a mesma linguagem do legado**, o oráculo e o candidato rodam **no mesmo harness**, sobre as mesmas fixtures, sem infraestrutura de comparação. Esta é a razão pela qual a estratégia de maior rigor é também a mais barata neste projeto.

> ⚠️ **Nota obrigatória do caso de borda "Estratégia Parallel Run"** (SKILL do Inspector): Parallel Run aqui é **offline/em lote, não online**. Não há dois sistemas em produção recebendo o mesmo tráfego; há um **oráculo congelado** e um **candidato** executados sobre o mesmo conjunto de entradas. Não há "campos de divergência aceitável" por latência ou consistência eventual — a comparação é **exata e síncrona**. Registrado aqui para que a expressão "Parallel Run" não seja lida como dual-write.

## Critérios de "paridade aceita"

- **Métrica primária**: **zero divergência** no núcleo congelado. Para cada fixture do corpus, o candidato deve reproduzir **exatamente** a saída do oráculo legado em: matches aceitos, matches descartados (e motivo), `total_cm`, `relationship_label`, caminho direto (ramos + MRCA) e caminho indireto (ramos + par de afinidade). Diferença de **um único dígito** em `total_cm` conta como divergência.
- **Janela de observação**: **não é temporal — é por onda.** A paridade é avaliada como **portão de saída de cada onda** do `cutover_plan.md`, não por um período de dias. A Onda 1 não avança enquanto houver qualquer divergência aberta; a Onda 2 não inicia sem a Onda 1 fechada. Justificativa: não há produção observável, então "N dias consecutivos" não tem significado — não existe tráfego gerando casos novos. A janela temporal seria uma métrica vazia.
- **Critério de bloqueio**: **qualquer divergência em aberto no núcleo congelado bloqueia**, mesmo que o resultado novo "pareça mais correto" que o do legado. O `cutover_plan.md` § Critérios de go/no-go já lista isso como **No-go absoluto**. Divergência em **fronteira** (HTTP, payload, tela) não bloqueia por si — é governada pelas deviations aprovadas.

> **Divergência entre esta métrica e a matriz de referência**: a matriz sugere *"divergência funcional < 0,01% por 60 dias"* para sistemas regulatórios. Aqui a métrica é mais estrita (**0% exato**) e a janela é substituída por portões de onda. A razão é que os 0,01% da matriz existem para absorver ruído de **tráfego real** (dados sujos, casos de borda de usuários) — e não há tráfego real. Sobre um corpus de fixtures **fechado e determinístico**, tolerar 0,01% seria tolerar uma divergência conhecida e evitável. O sistema é regulatório (LGPD/GDPR) e o núcleo é declaradamente congelado pelo brief: a tolerância correta é zero.

## Cobertura adaptada ao paradigma

> Transição detectada: **`procedural → OO com DI`**, gap **alto** (`paradigm_decision.md`), com a decisão humana de **híbrido** (opção 3): *modernizar a fronteira, preservar o núcleo*.

A matriz de referência cobre `procedural → OO` com `@paridade + @invariante`. **Isso é insuficiente para este projeto**, por três razões que a matriz não contempla e que o `paradigm_decision.md` torna obrigatórias. A cobertura abaixo é a **extensão justificada** da matriz:

### 1. Invariantes em aggregates (`@invariante`) — da matriz, mantido
- **Invariantes a validar**: `GedcomTree` I-1 (propriedade por `owner_id`), I-2 (integridade referencial GEDCOM), I-3 (unicidade de xref), I-4 (imutabilidade após parse), I-5 (ordem de inserção preservada), I-6 (nome de exibição presente, **podendo ser string vazia** — BR-MIGRAR-003 corrigido contra o oráculo); `DnaAnalysis` I-1..I-6; `AppUser` I-1..I-3.
- **Validação em factories/construtores**: o parse é a factory de `GedcomTree`; a resolução de raiz é pré-condição de `DnaAnalysis`. Casos críticos: GEDCOM com referência pendente, GEDCOM vazio, `root_name` inexistente.

### 2. Isolamento por tenant (`@isolamento`) — **dimensão nova, não está na matriz**
A matriz não prevê multitenancy porque assume OO clássico single-tenant. Aqui `owner_id` é **invariante de aggregate, não filtro de consulta** (AD-02), e a falha é **assimétrica e irreversível**: dado genético vazado não pode ser "desfeito". Cobertura obrigatória: **teste negativo** — usuário autenticado tentando acessar recurso de outro deve receber `404` (**não** `403`, para não vazar existência). Registrado como RISK-005 (crítico) e como requisito de go-live no `cutover_plan.md`.

### 3. Exatidão aritmética (`@exatidao`) — **dimensão nova, não está na matriz**
A matriz trata equivalência funcional como "mesma entrada → mesma saída". Isso é insuficiente quando a **ordem de acumulação de ponto flutuante** é significativa: `total_cm` é somado na ordem de leitura do CSV, e a tabela de cM tem **9 faixas que se sobrepõem** (ex.: 46–515 e 200–850 contêm 200–515). Um erro de centésimo pode cruzar uma fronteira de faixa e mudar a relação apresentada. Cobertura obrigatória: comparação **exata** (sem tolerância) e fixtures com cM **exatamente nas fronteiras** (46, 200, 553, 1317, 2200, 3300). Registrado como RISK-004.

### 4. Preservação de ordem determinística (`@ordem`) — **reinterpretação de tag existente**
A matriz usa `@ordem` para event-driven (ordem de mensagens por chave). Aqui **não há eventos** (AD-05), mas há um problema **análogo e igualmente real**: três ordens determinam o resultado e **não são garantidas por um banco relacional**.
- `person.source_ordinal` → a ordem da lista de `find_person_by_name` define **qual ID** o "primeiro ID" escolhe (BR-MIGRAR-026, BR-MIGRAR-027).
- `gedcom_tree.graph_edge_order_version` → `nx.shortest_path` com caminhos de mesmo comprimento retorna aquele determinado pela **ordem de inserção das arestas** (BR-MIGRAR-024).
- `match_result.result_ordinal` → ordenação por cM decrescente precisa de desempate **estável** (BR-MIGRAR-031).
**A tag `@ordem` é reutilizada com este significado**, documentado explicitamente para não ser confundida com ordenação de mensagens.

### 5. Ausência de estado compartilhado (`@composicao`/`@imutabilidade` adaptados)
A matriz usa estas tags para `OO → funcional`. Aqui o risco é **o inverso**: garantir que o alvo **não** carregue o estado global do legado (`people`, `families`, `graph`, `child_to_family`, descartados em BR-DESCARTAR-001). Cobertura: duas árvores de dois usuários processadas **concorrentemente** devem produzir resultados independentes e corretos; e a mutação in-place da reconstrução (`clear`/`update`) **não** deve existir no alvo. Registrado como RISK-005 e RISK-001.

> **O que a cobertura adaptada explicitamente NÃO inclui**: `@idempotencia`, `@dlq`, `@saga`, `@supervisao`. Todas pressupõem mensageria ou atores. O paradigma decidido é `OO com DI sobre funções puras` com processamento **síncrono por requisição** (AD-05) e o brief não define mensageria. Criar esses cenários seria cerimônia sem consumidor — e o SKILL do Inspector é explícito que a cobertura deve ser **adaptada**, não copiada.

## Paridade de telas

**Modo declarado**: **híbrido** (`screen_modernization_decision.md`) — **8 entradas literais** (SCR-001 a SCR-005 + SCR-G01 a SCR-G03) e **5 modernizadas** (SCR-006 a SCR-010).

### Telas em modo literal → `@paridade-visual` (golden file comparison)

Comparação **textual estrita** contra os golden files do `_reversa_sdd/screens/golden/manifest.yaml`, dentro das `normalizationRules` declaradas:
- `lineEndings: "\n"`, `trimTrailingSpaces: true`, `normalizeUtf8: true`
- **`ignoreStrings`**: `"Close"` → `"Fechar"` (exceção DEV-005 — única autorizada)

⚠️ **Estado dos golden files**: **nenhum foi capturado** (`manifest.yaml` lista todas as entradas com `present: false`). Conforme o caso de borda do SKILL (*"Modo literal sem golden files capturados"*), os cenários `@paridade-visual` são **emitidos mesmo assim**, mas a validação é **MANUAL até a captura ser executada**. Os comandos de captura estão no manifesto, em ordem recomendada do mais barato ao mais caro. **Enquanto não houver golden, a paridade visual das telas literais não está provada** — apenas especificada.

**Ordem de valor dos goldens** (do maior retorno pelo menor custo): `SCR-G02` (submeter formulário **sem** arquivo produz deterministicamente `"Nenhum arquivo GEDCOM enviado."` — prova paridade de mensagem congelada **sem nenhuma fixture**) → `SCR-001` (sem fixture) → `SCR-002/003/004` (uma fixture GEDCOM) → `SCR-005` (GEDCOM + CSV + raiz) → `SCR-G03` (exige navegador headless).

### Telas em modo modernizado → **contract test de tela** (sem comparação byte-a-byte)

Para SCR-006 a SCR-010, validar: hierarquia de componentes declarada, eventos correspondentes, conteúdo textual e os **4 estados** (idle, loading, error, success). Não há origem no legado — não há golden nem baseline visual. O contrato é a própria spec em `target_screens.md`.

### Propagação de deviations

Todas as **10 deviations** de `screen_deviation_log.md` estão **aprovadas** (0 pendentes) e são propagadas em § Exceções abaixo, com referência ao `DEV-XXX` original. O handoff não está bloqueado.

## Exceções

> Deviations aprovadas que **suspendem** a paridade estrita em pontos declarados. Cada exceção é rastreável ao `DEV-XXX` de `screen_deviation_log.md`.

| ID | Afeta | Exceção declarada | Efeito nos testes |
|---|---|---|---|
| **DEV-001** | adapter | Par `server-rendered-jinja2-bootstrap` → `web-spa` não consta no catálogo v1; `html_legacy__spa` usado como proxy. | Nenhum — formato `route-component` é adequado. |
| **DEV-002** | SCR-002/003/004 | `gedcom_filename` (nome do arquivo do cliente) → `tree_id` resolvido por sessão. | **Não** asserir sobre `gedcom_filename`. Asserir sobre seleção de árvore. |
| **DEV-003** | SCR-002/003/004 | `<datalist>` com todos os nomes → busca paginada. | Comparar **semântica** (autocomplete alimentado pelos nomes, ordem alfabética), não o mecanismo. |
| **DEV-004** | SCR-005 | String **Mermaid gerada no servidor** → `KinshipPath` estruturado. | ⚠️ **A exceção mais crítica.** Asserir sobre a **estrutura decomposta** (ramos, MRCA, par de afinidade), **nunca** sobre a string Mermaid. Ver § Riscos residuais. |
| **DEV-005** | SCR-G01/G02 | `aria-label="Close"` → `"Fechar"` (revisão linguística autorizada). | **Única** exceção à invariante de diff textual zero. Ignorar esta string na comparação. |
| **DEV-006** | tokens | Tokens derivados do legado por ausência de `design-system/` (EC-17). | Comparação visual de cores/tokens não é critério de paridade. |
| **DEV-007** | inventário | Inventário construído do código-fonte por ausência de `ui/inventory.md` (EC-18). | EC-03 (divergência >10%) **não foi executável** — não há artefato de Discovery para comparar. |
| **DEV-008** | tipografia | Legado **não define** família tipográfica. | Comparação visual de tipografia não é válida — não há origem. |
| **DEV-009** | SCR-001/003/004/005/G02 | Três ações no mesmo `POST /` com `status 200 (sempre)` → endpoints REST + status semântico. | Asserir sobre **motivo tipado + mensagem textual**, **não** sobre status `200` nem HTML. |
| **DEV-010** | SCR-G03 | Spinner global que **ocultava a região de resultados** → loading **local** ao formulário. | Asserir sobre **presença do loading**, **não** sobre ocultação de `#results-area`. |

## Tipos de teste a aplicar

- **Funcionais (differential execution — modo primário)**: harness Python que importa o núcleo novo e executa `analisador-genealogico/app.py` (**somente leitura**) sobre as **mesmas fixtures**, comparando as saídas com **igualdade exata**. Sem `pytest.approx`, sem tolerância, sem arredondamento. Ferramenta sugerida: `pytest` + comparação estrutural de resultados serializados (JSON canônico). É a **Onda 0** do `cutover_plan.md`.
- **Contrato (API)**: verificar que os endpoints alvo entregam payload tipado, status semântico (`200`/`404`/`422`) e as **mensagens congeladas** de BR-MIGRAR-028. Ferramenta sugerida: `httpx` + `pytest` contra a aplicação FastAPI em memória. Cobre DEV-009 sem tocar no texto.
- **Carga / performance**: **fora do escopo de paridade.** O legado re-parsa o GEDCOM a cada POST e o alvo parseia uma vez — o desempenho **muda por design** e não é critério de equivalência. Se houver meta de performance, ela é requisito novo, não paridade. Registrado para que a ausência não seja lida como lacuna.
- **Resiliência**: **não aplicável** — sem fila, sem dependência externa, sem serviço de terceiros (`architecture.md` §4: *"Nenhuma API REST/GraphQL externa consumida ou produzida"*). A única dependência é o sistema de arquivos e o banco, ambos locais.
- **Negativo de isolamento** (novo, obrigatório): usuário A autenticado acessando recurso de B → `404`. Bloqueia go-live (`cutover_plan.md` § go/no-go).

## Reuso de characterization_specs do time de descoberta

- **Origem**: `_reversa_sdd/characterization_specs/` — **NÃO EXISTE**. Não há `sequences/` nem `flowcharts/` no `_reversa_sdd/` (a descoberta rodou em nível **essencial**, conforme `architecture.md` § cabeçalho e `confidence-report.md`).
- **Lacuna documentada** (conforme o caso de borda do SKILL): os fluxos críticos foram **inferidos** de `code-analysis.md` §3 (funções e fluxos principais), das 3 units (`requirements.md` + `design.md`) e das 34 regras `BR-MIGRAR` de `target_business_rules.md`. **Não há baseline de characterization herdado** — todo o corpus de paridade precisa ser construído na Onda 0.
- **Adaptações necessárias para o sistema novo**: as entradas mudam de formulário HTML (`POST /` com campo `action`) para endpoints REST; **as saídas de domínio não mudam**. Os cenários abaixo são escritos em termos de **comportamento de domínio** (matches, cM, caminhos), não de HTTP, exatamente para permanecerem válidos independentemente do transporte.

> ⚠️ **Lacuna de rastreabilidade declarada**: como não existe `characterization_specs/` nem `code-analysis.md` com fluxos numerados além das funções descritas, a coluna `process_flows` da rastreabilidade aponta para **funções e blocos** de `code-analysis.md` §3 e para as `BR-MIGRAR` — não para IDs de fluxo formais, que não existem. Registrado para não simular uma rastreabilidade que o material de origem não oferece.

## Riscos residuais da estratégia de paridade

> Riscos que **a própria estratégia de validação** carrega. Distintos dos riscos de migração (`risk_register.md`), ainda que se sobreponham.

- **RISK-002 (crítico) — o oráculo pode ser inválido.** Se os golden files forem gerados a partir de `reconstructed/*.py` em vez de `analisador-genealogico/app.py`, toda esta estratégia se torna **circular**: validaria uma interpretação de segunda mão contra ela mesma. **Os 47 testes existentes em `tests/` têm exatamente esse defeito** — testam a reconstrução, não o legado. **Mitigação não negociável**: o harness aponta para o `app.py` legado, e o `manifest.yaml` registra a origem de cada golden.
- **RISK-003 (alto) — transcrição incompleta.** BR-MIGRAR-011 (lista de primeiros nomes genéricos) e BR-MIGRAR-012 (tabela de equivalentes de grafia, sobrenomes comuns, sufixos salvadores) existem **somente em `app.py`**. Se o port os reconstruir de memória, a divergência aparece **apenas** nos casos que exercitam esses dados. **Mitigação**: fixtures dedicadas com nomes genéricos e grafias variantes; exigir referência de linha ao `app.py` em cada constante transcrita.
- **RISK-004 (alto) — divergência aritmética.** Comparação exata é necessária, mas **exige que o oráculo seja determinístico**. Se `thefuzz`/`pandas`/`ged4py` diferirem de versão entre o ambiente do oráculo e o do alvo, a divergência **não é erro do port** (RISK-009). **Mitigação**: congelar o ambiente do oráculo e comparar versões de biblioteca **antes** de culpar o código.
- **RISK-011 (médio) — perda silenciosa da decomposição do caminho.** É o risco que **esta estratégia pode deixar passar**: nenhum cenário de matching falharia se `split_path_by_marriage`/`are_spouses` desaparecessem, porque o matching continua correto. **Mitigação obrigatória**: cenários `@paridade` **dedicados** à conexão **indireta** com múltiplas afinidades, asserindo sobre a estrutura decomposta (ver `06-decomposicao-caminho.feature`).
- **Cobertura de fixture é o teto da confiança.** Como a métrica é 0% de divergência **sobre o corpus**, a validade da métrica depende inteiramente da **qualidade do corpus**. Um corpus pobre dá paridade de 100% com confiança baixa. **Mitigação**: os cenários abaixo exigem explicitamente fixtures de borda (cM em fronteira de faixa, sobrenomes sem interseção, homônimos, encoding Latin-1, famílias adotivas, múltiplas afinidades), não apenas casos felizes.

## Saídas

`parity_tests/*.feature` — **12 arquivos**, em Gherkin (`# language: pt`):

| Arquivo | Fluxo | Tags principais |
|---|---|---|
| `01-carregar-gedcom.feature` | Parsing INDI/FAM, grafo, nomes (incl. **string vazia**), invariantes de `GedcomTree` | `@paridade @critico @invariante` |
| `02-agregacao-segmentos-cm.feature` | `_group_key`, soma de cM, ordem de acumulação, fronteiras de faixa | `@paridade @critico @exatidao @ordem` |
| `03-regras-aceitacao-abcd.feature` | Regras A/B/C/D, limiares 92/90/86/100, ordem de avaliação | `@paridade @critico` |
| `04-filtros-anti-falso-positivo.feature` | Interseção 0, sufixos salvadores, interseção adaptativa, Jaccard | `@paridade @critico` |
| `05-busca-caminho-direto.feature` | BFS bidirecional, a 20 níveis, MRCA, caminho trivial | `@paridade @critico @invariante` |
| `06-decomposicao-caminho.feature` | Conexão indireta, `max_hops=40`, `split_path_by_marriage`, `are_spouses` | `@paridade @critico @ordem` |
| `07-encoding-e-colunas-csv.feature` | Fallback UTF-8→Latin-1, colunas tolerantes, `[A-Z]{2}\d{7}` | `@paridade @critico` |
| `08-mojibake-viral.feature` | `strip_bad_utf`, `demojibake`, equivalentes de grafia, score difuso | `@paridade @critico` |
| `09-relacao-por-cm.feature` | 9 faixas com sobreposição, cM ≤ 0, ordem de avaliação | `@paridade @critico @exatidao` |
| `10-descartados-auditoria.feature` | Completude da auditoria: todo match aceito ou descartado com motivo | `@paridade @critico @invariante` |
| `11-isolamento-multitenant.feature` | Teste negativo por `owner_id`, concorrência sem estado global | `@paridade @critico @regulatorio @isolamento` |
| `12-paridade-telas.feature` | Paridade visual (literal) + contrato de tela (modernizado) | `@paridade-visual @critico` |

## Notas

- **Estes artefatos são specs, não testes executáveis.** Os `.feature` estão em Gherkin válido e não referenciam nenhum framework (regra absoluta do SKILL). O agente de codificação os traduz para `behave`/`pytest-bdd`/equivalente.
- **A estratégia inteira depende de um único ato não executado**: apontar o harness para `analisador-genealogico/app.py`. Enquanto isso não acontecer, nada aqui é verificável. É o primeiro item da Onda 0 e o pré-requisito do pré-requisito.
- **Nenhum cenário assere sobre HTML, sobre a string Mermaid ou sobre `status 200`** — exceto os de `@paridade-visual`, que comparam **texto visível** dentro das `normalizationRules`, e que dependem de goldens ainda não capturados.
- **O corpus de fixtures é a entrega mais valiosa da Onda 0.** Os fixtures Python existentes (`tests/fixtures/sample_gedcom.py`, `sample_dna.py`) e o GEDCOM de exemplo (`_reversa_sdd/upload-gedcom/exemplo_familia.ged`) são ponto de partida, **mas não cobrem os casos de borda** que os cenários exigem (fronteiras de cM, homônimos, múltiplas afinidades, GEDCOM com referência pendente). Expandir o corpus é trabalho da Onda 0, não deste artefato.
