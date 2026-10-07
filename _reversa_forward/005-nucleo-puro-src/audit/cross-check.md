# Cross-check: núcleo puro em `src/core/`

> Identificador da feature: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Artefatos auditados:
> - `_reversa_forward/005-nucleo-puro-src/requirements.md`
> - `_reversa_forward/005-nucleo-puro-src/roadmap.md`
> - `_reversa_forward/005-nucleo-puro-src/actions.md`
>
> Artefatos de apoio consultados: `data-delta.md`, `investigation.md`, `onboarding.md`, `_reversa_sdd/architecture.md`, `_reversa_sdd/code-analysis.md`, `_reversa_sdd/migration/parity_specs.md`, `.reversa/principles.md` e o código de `src/`, `tests/` e `_reversa_sdd/parity/harness.py`.

## Resumo

| Severidade | Quantidade |
|---|---:|
| CRITICAL | **0** |
| HIGH | **4** (`A001`, `A002`, `A003`, `A004`) |
| MEDIUM | **5** (`A005` a `A009`) |
| LOW | **2** (`A010`, `A011`) |
| **Total** | **11** na auditoria inicial, **mais 1** (`A012`) revelado pela correção |

**Nenhum ciclo de dependência foi encontrado. Nenhum identificador fantasma foi encontrado. Nenhuma contradição com regra 🟢 de `domain.md` foi encontrada.**

> O quadro acima conta os findings da **auditoria inicial**. O `A012` foi encontrado durante a correção e está registrado na seção "Estado após as correções", no fim do relatório.

## Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|-----------|------|-----------|-----------|
| A001 | HIGH | Sanidade do actions | A maior cadeia de dependência declarada está **errada por dois**: o resumo diz 15 ações, e a cadeia real tem **17**. Além disso, a cadeia declarada **não é uma cadeia válida** — ela salta de `T004` para `T008` como se `T008` dependesse de `T004`, o que é verdade, mas omite que a sequência exige `T002`/`T004` antes; o caminho mais longo real passa por `T018` e `T023` e não por `T014` → `T017` | `actions.md:13` |
| A002 | HIGH | Consistência | A decisão `D-02` afirma que `load_gedcom_and_build_graph` "deixa de mutar as globais", o que contradiz a `D-11` ("continua atualizando as globais durante a migração") e o próprio delta arquitetural. A `D-02` descreve o **estado final** sem dizer que é o estado final | `roadmap.md:29` vs `:38` e `:53` |
| A003 | HIGH | Sanidade do actions | `T029` depende de `T026` e `T027`, mas **não** de `T028`. Como `T028` remove as docstrings que documentam o estado global, a verificação manual de `T029` pode rodar com a documentação ainda mentindo, e ficar registrada como verificação de um estado que não é o final | `actions.md:85` vs `:84` |
| A004 | HIGH | Cobertura | O cenário Gherkin **negativo** "Divergência bloqueia a Onda 1" (`requirements.md#7`) não tem ação que o verifique. `T004` e `T026` **medem** a paridade, mas nenhuma ação exige que uma divergência **bloqueie** — ou seja, o critério de recusa existe na spec e não no plano | `requirements.md:150-154`; ausente em `actions.md` |
| A005 | MEDIUM | Consistência | `RF-13` exige como critério de aceite que `parsers/gedcom_parser.py` **não mute nem atribua** estrutura global. Durante toda a migração (`D-11`) ele muta e atribui **de propósito**. O critério só é verdadeiro ao final, e nenhum artefato diz isso | `requirements.md:76` vs `roadmap.md:38` |
| A006 | MEDIUM | Coerência com o legado | O delta arquitetural diz que `gedcom_state` sofre "regra-alterada" e que "sobra apenas o acesso a registro em módulo puro". Nas duas leituras — "sobra dentro do módulo" ou "sobra em `registro.py`" — o **nome do módulo deixa de descrever o conteúdo**. `T023` remove o estado do arquivo e `T025` remove o módulo, mas nenhum artefato declara se o nome `gedcom_state` sobrevive, e a `D-06` aponta para `registro.py` | `roadmap.md:52`; `actions.md:72-74` |
| A007 | MEDIUM | Cobertura | `T002` cita `split_path_by_marriage` mas **não** `are_spouses`, que é a outra metade do RISK-011 segundo a própria `parity_specs.md` (a linha do `06-decomposicao-caminho.feature` nomeia as duas). As duas funções existem de fato em `family_navigation.py:78` e `:82`, então a exclusão é de escopo, não de existência | `actions.md:24`; `_reversa_sdd/migration/parity_specs.md:148` |
| A008 | MEDIUM | Cobertura | `A004` se agrava por um detalhe verificável: `T007` escreve um teste que **falha hoje de propósito**. Nenhuma ação revoga esse estado esperado, e o critério de pronto do roadmap exige a suíte em 164 aprovados. Se a suíte for medida entre `T007` e `T025`, ela terá **163 aprovados + 1 falha intencional** — e nenhum artefato registra que isso é esperado | `actions.md:38`, `:74`; `roadmap.md:115` |
| A009 | MEDIUM | Cobertura | O `RNF de portabilidade` do `requirements.md` ("sem uso de `socket`, `errno` ou API exclusiva do Windows") não aparece em nenhum ponto do roadmap nem do actions. `T006` afirma o teste de I/O, mas cobre `open`/`os.environ`/socket de rede, não a ausência de dependência de plataforma | `requirements.md:86`, `:181` |
| A010 | LOW | Consistência | O delta arquitetural classifica a mudança em `csv_ingest` como `regra-alterada`, enquanto as demais linhas usam `contrato-alterado` para mudança de assinatura. `csv_ingest` não tem regra de negócio alterada — a mudança é de contrato | `roadmap.md:61` |
| A011 | LOW | Sanidade do actions | O alvo de `T029` é um documento de instrução (`onboarding.md`), não um arquivo de produto. É aceitável, mas a evidência da verificação manual precisa ficar em `evidence/` para ser auditável depois — e nenhuma ação exige isso | `actions.md:85` |

## Detalhe dos findings HIGH

### A001 — cadeia de dependência declarada está errada e não é uma cadeia válida

**Impacto.** O resumo do `actions.md` é a informação que um humano usa para dimensionar a onda — é o número que responde "quanto tempo isso leva". Declarar 15 quando são 17 subestima a profundidade, e o mais grave é de outra natureza: a cadeia listada **não existe** no grafo. Ela escreve `T004 → T008` como se fosse a continuação natural e depois segue para `T014 → T017 → T020`, ignorando que `T020` depende de `T016` **e** `T017` **e** `T019`. Uma leitura que confie nessa lista conclui que `T017` é o caminho crítico, quando o caminho crítico passa por `T018` e `T023`.

**Verificação.** Enumerando todos os caminhos do grafo declarado em `actions.md`, o mais longo é:

`T008 → T009 → T011 → T012 → T013 → T014 → T016 → T018 → T020 → T021 → T022 → T023 → T025 → T026`

com **14 nós** (13 elos), mais a cauda de entrada `T002 → T004 → T008` e a dependência `T005 → T007 → T024 → T025`. A cadeia máxima de ponta a ponta tem **17 ações**:

`T002 → T004 → T008 → T009 → T011 → T012 → T013 → T014 → T016 → T018 → T020 → T021 → T022 → T023 → T025 → T027 → T029`

**Sugestão de direção.** Corrigir o resumo do `actions.md` é edição de artefato, e esta auditoria **não** escreve em `actions.md`. A direção é `/reversa-to-do` para regenerar o resumo, ou edição manual do humano.

### A002 — `D-02` contradiz `D-11` sobre a mutação das globais

**Impacto.** As duas decisões descrevem o mesmo módulo em estados diferentes sem dizer qual é qual. A `D-02` diz "deixa de mutar as globais"; a `D-11` diz "continua atualizando as globais". Um executor que leia só a `D-02` remove a mutação no passo 4 do plano e **quebra os consumidores ainda não migrados** — exatamente a falha que a `D-11` existe para prevenir. O delta arquitetural (`roadmap.md:53`) já reconcilia as duas, mas a decisão que um executor consulta primeiro não.

**Verificação.** `roadmap.md:29` (D-02) versus `roadmap.md:38` (D-11) e `roadmap.md:53` (delta de `load_gedcom_and_build_graph`).

**Sugestão de direção.** Ajustar a redação da `D-02` para declarar que descreve o **estado final**. É edição de roadmap, então a direção é `/reversa-clarify` ou edição manual — esta auditoria não altera o artefato.

### A003 — `T029` pode rodar antes de `T028`

**Impacto.** `T028` remove as docstrings que documentam o import tardio, o contador `versao` e a captura do resolvedor. `T029` é a verificação manual de aceite. Como `T029` não depende de `T028`, a ordem entre as duas fica indefinida, e a verificação de aceite pode ser registrada sobre uma árvore em que a documentação ainda descreve um mecanismo que não existe. O `onboarding.md` §Passo 9 manda registrar a evidência e conferir o estado — e o estado conferido seria parcial.

**Verificação.** `actions.md:84` (`T028`, dependência `T025`) e `actions.md:85` (`T029`, dependências `T026, T027`). `T028` não aparece na lista.

**Sugestão de direção.** Acrescentar `T028` às dependências de `T029` no `actions.md`. Edição de artefato — direção `/reversa-to-do` ou edição manual.

### A004 — o cenário negativo de divergência não tem ação

**Impacto.** O `requirements.md#7` fecha com dois cenários negativos: "Divergência bloqueia a Onda 1" e "A suíte existente não pode ser reduzida". O segundo tem `T021` (proibição de afrouxar asserção) e `T026` (medir contra a linha de base). O primeiro **não tem ação**: nenhuma tarefa exige que a execução **falhe** quando há divergência, nem confirma que o harness não reporta paridade quando um import proibido entra. A `RF-10` cobre a existência do probe, não o comportamento de bloqueio.

**Verificação.** `requirements.md:150-154`; busca por "bloqueia", "recusa" e "falha" nas descrições de `actions.md` não encontra ação correspondente. `T024` verifica o caminho negativo do teste de **dependências**, que é outro cenário.

**Sugestão de direção.** Ou o cenário vira ação (por exemplo, confirmar que o harness sai com código diferente de zero e reporta a divergência quando ela é introduzida de propósito), ou o cenário é retirado do requirements por ser afirmação de processo e não de produto. A decisão é do humano; a direção para alterar o requirements é `/reversa-clarify`.

## Itens verificados que passaram

### Cobertura

- **Os 13 requisitos funcionais têm cobertura no roadmap e nos actions.** `RF-01`/`RF-02` → `D-01`, `D-11`, `T011`–`T014`; `RF-03` → `D-01`, `T013`; `RF-04` → `D-01`, `T012`; `RF-05` → `D-01`, `T012`, `T002`; `RF-06` → `T004`, `T026`; `RF-07` → `D-09`, `T015`; `RF-08` → `T005`, `T024`; `RF-09` → `D-04`, `T016`, `T017`; `RF-10` → `D-07`, `T001`, `T002`; `RF-11` → `D-09`, `T021`, `T026`; `RF-12` → `D-05`, `T022`; `RF-13` → `D-02`, `T009`, `T023`.
- **As 11 decisões técnicas têm pelo menos uma ação correspondente.** `D-01` → `T011`–`T014`; `D-02` → `T009`; `D-03` → `T014`; `D-04` → `T016`, `T017`; `D-05` → `T022`; `D-06` → `T008`, `T025`; `D-07` → `T001`, `T004`; `D-08` → abstenção declarada (não criar `analisador/`), verificável por ausência; `D-09` → `T021`; `D-10` → `T010`; `D-11` → `T009`, `T023`.
- **Os 12 cenários Gherkin estão cobertos por decisão ou ação**, com a única exceção registrada em `A004` (o cenário negativo de divergência).
- **Todas as regras de negócio tocadas citam a origem no `_reversa_sdd/`**: `RN-01` cita `code-analysis.md#3.5` e `#4.5`; `RN-02` cita `architecture.md#1`; `RN-03` cita `code-analysis.md#4.5` (BR-C-22); `RN-04` cita `topology_decision.md#Decisão do usuário`.

### Consistência

- **Nenhum identificador fantasma.** Todas as referências cruzadas resolvem: `RF-01` a `RF-13` existem no `requirements.md`; `RN-01` a `RN-04` existem; `D-01` a `D-11` existem, e a `D-11` é citada antes de sua criação apenas em documento que a define na mesma linha; `T001` a `T029` existem.
- **Terminologia estável entre os três documentos.** `gedcom_state`, `registro.py`, `harness.py`, `árvore`, `paridade`, `linha de base`, `Onda 1` e `probe` aparecem com a mesma grafia e o mesmo sentido nos três artefatos. Não há sinônimo concorrente para o mesmo conceito.
- **`interfaces/` está corretamente ausente.** O roadmap declara que nenhum contrato externo muda (`roadmap.md:65`, `:78-80`), e o diretório não existe no disco. A ausência é coerente, não esquecimento.
- **A contagem de cenários Gherkin do `requirements.md` é 12** (10 positivos + 2 negativos), conforme medido no arquivo.
- **O `data-delta.md` é coerente com o roadmap:** nenhum schema, nenhuma migração, e o delta declarado é de papel e tempo de vida das estruturas — o que casa com `roadmap.md#6`.

### Coerência com o legado

- **Nenhuma decisão contradiz regra 🟢 do `_reversa_sdd/domain.md`.** As decisões mexem em assinatura e mecanismo, e não em regra de negócio. Os limiares do matching, a tabela de cM, o teto de 20 iterações do BFS e o teto de 40 arestas ficam intactos e são citados como intocáveis (`T012`, `T013`).
- **Todos os componentes citados existem de fato no código.** Verificado por busca: `load_gedcom_and_build_graph` (`src/parsers/gedcom_parser.py:50`), `find_person_by_name` (`family_navigation.py:21`), `get_parents` (`:29`), `get_spouses` (`:51`), `are_spouses` (`:78`), `split_path_by_marriage` (`:82`), `pick_spouse_for_couple` (`:93`), `exclude_tail` (`:104`), `build_ged_indexes` (`matching.py:27`), `match_candidates` (`matching.py:62`), `find_indirect_path` (`path_finding.py:31`), `find_ancestral_path` (`path_finding.py:51`), `get_children` (`documentary_relationship.py:112`), `resolvedor_de_diagrama` (`diagram_domain.py:25`).
- **O achado central do roadmap é confirmado por medição.** O `harness.py` de fato **não** tem probe para `build_ged_indexes` nem para `match_candidates`: os probes existentes estão em `harness.py:111-144` e cobrem contagens, nomes, grafo, filho→família, `get_parents`, `get_spouses`, 9 funções de nome, cM, caminho ancestral e caminho indireto. A afirmação de `D-07` está correta.
- **A contagem de 40 valores de cM é exata:** `CM_PROBES` (`harness.py:61-65`) tem exatamente 40 entradas. O critério de aceite de `RF-06` confere.
- **A linha de `path_finding.py:38` citada pela `T012` existe e é o import dentro da função**, conforme o roadmap descreve.
- **A tabela `@ordem` citada pelo `data-delta.md` existe** em `_reversa_sdd/migration/parity_specs.md:60-65`.
- ⚠️ **CORRIGIDO — este item estava errado.** A auditoria inicial registrou que "a contagem de 7 arquivos de teste que leem `gedcom_state` confere". **Não conferia:** são **8**. A busca original encontrou os arquivos que importam `gedcom_state` diretamente e os que usam `load_gedcom_and_build_graph`, mas deixou `tests/test_confrontacao_gedcom_dna.py` de fora da contagem, apesar de o resultado da busca o citar. Ver `A012`. Os oito arquivos são: `test_upload`, `test_dna_analysis`, `test_path_search`, `test_characterization_matching`, `test_characterization_mermaid`, `test_formatacao_cm`, `test_mermaid_escape` e `test_confrontacao_gedcom_dna`.

### Sanidade do actions

- **Nenhum ciclo de dependência.** O grafo é acíclico: todas as arestas apontam para IDs de numeração menor, e nenhuma dependência aponta para frente.
- **Todas as dependências apontam para IDs existentes.** Nenhuma referência a `T030` ou superior.
- **Nenhuma tarefa `[//]` compartilha arquivo alvo com outra `[//]`.** Verificado par a par: `T003` (`_clean_residue.py`), `T008` (`registro.py`), `T015` (`genetic_evidence.py`, `evidence_comparison.py`), `T019` (`csv_ingest.py`), `T026` (`evidence/`), `T027` (`README.md`), `T028` (`family_navigation.py`, `path_finding.py`, `diagram_domain.py`) — todos os alvos distintos entre si.
- **Os arquivos citados como alvo existem, exceto os que a feature cria:** `src/core/registro.py`, `tests/test_dependencias_nucleo.py` e `evidence/` são novos e estão declarados como criação.

## Estado após as correções de 2026-10-06

> Seção acrescentada **depois** da auditoria, para registrar o que foi corrigido, o que ficou aberto, e um finding novo que a própria correção revelou. Os findings acima **não foram reescritos** — o relatório é registro do que foi encontrado.

| Finding | Estado | O que mudou |
|---|---|---|
| A001 | ✅ **Corrigido** | `actions.md` § Resumo: maior cadeia passa a declarar **17 ações**, com o caminho real (`T002` → `T004` → `T008` → `T009` → `T011` → `T012` → `T013` → `T014` → `T016` → `T018` → `T020` → `T021` → `T022` → `T023` → `T025` → `T027` → `T029`) |
| A002 | ✅ **Corrigido** | `roadmap.md` `D-02`: passa a declarar que descreve o **estado final**, e que durante a migração a mutação continua pela `D-11` |
| A003 | ✅ **Corrigido** | `actions.md` `T029`: `T028` acrescentado às dependências |
| A004 | ✅ **Resolvido** | Decisão do usuário em 2026-10-06: o cenário **permanece** e nasce a ação `T030`, que prova o bloqueio por divergência — alimenta o comparador com duas observações que diferem em um valor e confirma que o resultado é divergência reportada, não paridade |
| A005 | ✅ **Corrigido** | `requirements.md` `RF-13`: critério de aceite qualificado como estado final, com remissão à ordem de execução |
| A006 | ✅ **Corrigido** | `roadmap.md` delta de `gedcom_state`: reclassificado como `componente-extinto ao final`, com o nome explicitamente não sobrevivendo |
| A007 | ✅ **Resolvido** | Decisão do usuário em 2026-10-06: `are_spouses` entra no escopo do probe de `T002`, junto com `split_path_by_marriage` |
| A008 | ✅ **Resolvido** | Decisão do usuário em 2026-10-06: registrar o estado esperado. `actions.md` passa a declarar que a suíte fica em **163 aprovados + 1 falha intencional** entre `T007` e `T025`, e volta a 164 ao final |
| A009 | ✅ **Resolvido** | Decisão do usuário em 2026-10-06: a portabilidade entra como afirmação do teste de dependências de `T006` (`errno`, `SO_EXCLUSIVEADDRUSE`), em vez de sair do requisito |
| A010 | ✅ **Corrigido** | `roadmap.md` delta de `csv_ingest`: reclassificado como `contrato-alterado` |
| A011 | ✅ **Corrigido** | `actions.md` `T029`: alvo passa a ser `evidence/`, com o registro da saída exigido na própria descrição |

**11 de 11 resolvidos ou corrigidos; o `A012` foi acrescentado e corrigido no mesmo movimento.**

### A012 — finding novo, revelado pela correção de `A011` (MEDIUM)

**Descrição.** O escopo de `T021` estava **incompleto**. O roadmap afirmava 7 arquivos de teste dependentes de `gedcom_state`; a contagem real é **8**, porque `tests/test_confrontacao_gedcom_dna.py:384` também chama `gedcom_parser.load_gedcom_and_build_graph(caminho)` e depende do mesmo retorno.

**Verificação.** Busca por `gedcom_state` e `load_gedcom_and_build_graph` em `tests/`:

| Arquivo | Como depende |
|---|---|
| `test_upload.py` | importa `from core import gedcom_state` **e** `from core.gedcom_state import get_name, ref_id` |
| `test_dna_analysis.py` | importa o módulo; fixture devolve `gedcom_state` |
| `test_path_search.py` | importa o módulo; fixture devolve `gedcom_state` |
| `test_characterization_matching.py` | importa o módulo; fixture devolve `gedcom_state` |
| `test_characterization_mermaid.py` | importa o módulo; fixture devolve `gedcom_state` |
| `test_formatacao_cm.py` | chama `load_gedcom_and_build_graph` |
| `test_mermaid_escape.py` | chama `load_gedcom_and_build_graph` |
| **`test_confrontacao_gedcom_dna.py`** | chama `gedcom_parser.load_gedcom_and_build_graph` — **estava fora da lista** |

**Impacto.** `T021` era a ação que atualiza o encanamento dos testes. Executada como escrita, deixaria `test_confrontacao_gedcom_dna.py` — que tem **922 linhas** e cobre o confronto GEDCOM × DNA — quebrado, e a suíte não fecharia em 164 aprovados. A mitigação de `A004` no plano (o cenário da suíte que não pode encolher) seria acionada justamente por um escopo incompleto.

**Correção aplicada.** `T021` passou a nomear os oito arquivos; `roadmap.md` §1, `D-09` e o passo 7 do plano de migração passaram de 7 para 8.

### Re-verificação: não executada

Esta seção registra as correções, mas **não** re-verifica o conjunto. Uma segunda passada de auditoria sobre os artefatos já corrigidos é o que fecharia essa conta, e ela **não** foi feita — declarar "corrigido e re-verificado" sem uma segunda leitura seria afirmar mais do que foi medido. O `A012` é a evidência de que uma segunda passada tem valor: ele apareceu **durante** a correção, não apesar dela.

## Notas do auditor

1. **Duas das correções feitas durante a decomposição estão corretas e foram confirmadas por esta auditoria:** `T002` depende de `T001` e `T007` depende de `T006` — as duas por compartilharem arquivo alvo, que é a regra. A nota explicativa em `actions.md:28` também está correta.
2. **O `A001` tem valor além do cosmético.** A cadeia declarada não é apenas curta demais: ela é inválida como caminho, porque assume uma sequência que o grafo não contém. Vale corrigir antes de usar o número para dimensionar a onda.
3. **Uma lacuna de registro que não é finding** porque não pertence a esta feature: a contagem de linhas de `src/` medida é **2.969**, e o `_reversa_sdd/architecture.md#20` registra **3.489** — diferença de 520 linhas, não reconciliada. O `roadmap.md:10` cita 258 para `app.py`, e o `architecture.md:19` registra **267**. A `investigation.md` §2.6 já declarou essa lacuna, então ela está visível; está aqui apenas para que o humano saiba que a auditoria a viu e não a tratou como finding desta feature.

---

*Relatório gerado por `/reversa-audit` em 2026-10-06. Esta auditoria é estritamente leitora: nenhum dos três artefatos auditados foi alterado.*
