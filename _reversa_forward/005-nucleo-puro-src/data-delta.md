# Data Delta: núcleo puro em `src/core/`

> Identificador: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Requirements: `_reversa_forward/005-nucleo-puro-src/requirements.md`

## 1. Natureza deste delta

**Não há banco de dados, schema, DDL, ORM nem migration neste sistema.** O `_reversa_sdd/architecture.md#4` registra: "Sem banco de dados. Não há DDL, migration, schema, ORM nem arquivo de configuração de persistência", com o ERD de 27 estruturas sendo **lógico** (`erd-complete.md`) e o `data_migration_plan.md` registrando **volume zero** em todas as entidades.

Portanto este documento **não descreve migração de dados**. Ele descreve o delta no **modelo conceitual em memória** — quais estruturas mudam de papel, de dono ou de tempo de vida. É a leitura correta do template para um sistema sem persistência, e está alinhada com o `migration_strategy.md`, que registra que a "migração de dados" aqui é **modelagem nova**, não conversão.

## 2. Estruturas afetadas

As estruturas do modelo **não mudam de forma**. Nenhum campo é acrescentado, removido, renomeado ou retipado. O que muda é **quem as possui e por quanto tempo**.

| Estrutura | Forma | Onde vive hoje | Onde passa a viver | Mudança |
|---|---|---|---|---|
| `people` | `dict[str, registro ged4py]` | `core.gedcom_state` (global de módulo) | valor devolvido pelo parse, recebido por parâmetro | **papel** |
| `families` | `dict[str, registro ged4py]` | `core.gedcom_state` (global de módulo) | idem | **papel** |
| `child_to_family` | `dict[str, list[str]]` | `core.gedcom_state` (global de módulo) | idem | **papel** |
| `graph` | `nx.Graph` não direcionado, **sem tipo de aresta** | `core.gedcom_state` (global reatribuído) | idem, e sem reatribuição | **papel** e **tempo de vida** |
| `versao` | `int`, contador de cargas | `core.gedcom_state` | **deixa de existir** | **removida** |
| `_INDICE_DE_NOMES` | `{"versao": int, "mapa": dict}` | `core.documentary_relationship` (cache de módulo) | cache por execução, chaveado pela identidade da árvore recebida | **mecanismo de invalidação** |

### 2.1 Por que a forma não muda

A `RF-01` e a `RF-03` a `RF-07` exigem paridade exata contra o oráculo congelado. Trocar a forma das estruturas — um `dataclass` no lugar do `dict`, um grafo tipado no lugar do `nx.Graph` misto — mudaria o valor comparado e quebraria a paridade sem necessidade. O `paradigm_decision.md#Notas` já registra que o núcleo **não** deve ganhar objetos com estado, e o `topology_decision.md` proíbe criar aggregates dentro do núcleo de cálculo.

### 2.2 O grafo continua sem tipo de aresta

O grafo é um `nx.Graph` **não direcionado e não tipado**: filiação e casamento são a mesma aresta. Isso é o que faz o **Princípio IV** conflitar com esta feature, conforme registrado no `roadmap.md#2` e no `requirements.md#4`. **A tipagem das arestas não é feita aqui.** Ela é mudança de comportamento e exige feature própria.

## 3. Campos e valores: nenhuma alteração

| Aspecto | Antes | Depois | Muda? |
|---|---|---|---|
| Chaves de `people` | `@I1@`, `@I2@`, … (xref do GEDCOM) | idem | não |
| Chaves de `families` | `@F1@`, `@F2@`, … | idem | não |
| Chaves de `child_to_family` | xref de pessoa | idem | não |
| Ordem de inserção de `people` | ordem de leitura do GEDCOM | idem — **é contrato** | não |
| Ordem de inserção das arestas do grafo | ordem de leitura das `FAM` | idem — **é contrato** | não |
| Tipo do grafo | `nx.Graph`, não direcionado, sem tipo de aresta | idem | não |
| Sentinela de ausência | `None` = "não sei / não existe", nunca zero | idem | não |

> ⚠️ **A ordem de inserção é contrato de paridade, não detalhe.** `_reversa_sdd/migration/parity_specs.md#4` reutiliza a tag `@ordem` para isso: a ordem de `people` define qual ID o "primeiro ID" escolhe, e a ordem das arestas define qual caminho o `nx.shortest_path` devolve entre caminhos de mesmo comprimento. Trocar a estrutura por uma cujo percurso não preserve a ordem — um `set`, um índice ordenado, um grafo tipado construído em outra ordem — quebra a paridade **sem levantar erro**.

## 4. Migração de dados

**n/a.** Não há dados a migrar, backfill, captura de delta, janela de congelamento nem reconciliação. O `_reversa_sdd/migration/data_migration_plan.md` registra volume zero em todas as entidades, e o `cutover_plan.md` §"três características atípicas" confirma: a "migração de dados" deste projeto é **modelagem nova**.

O que existe é a migração **dentro do processo**, descrita no `roadmap.md#8` como ordem de execução.

## 5. Impacto em índices e caches

Um único ponto merece atenção, porque é onde o dado e o mecanismo se encontram:

`core/documentary_relationship.py` mantém `_INDICE_DE_NOMES` (`{"versao": int, "mapa": dict}`), reconstruído apenas quando `gedcom_state.versao` muda (linhas 193-201). O comentário do próprio código explica a razão: `people` é mutado in place, então o `id()` do dicionário **não** muda quando outro GEDCOM entra, e sem um sinal explícito o índice ficaria velho.

Com a árvore como parâmetro, o problema desaparece na raiz (`D-03`): uma árvore nova é um valor novo. **Duas formas de honrar isso, e a escolha é do `/reversa-to-do`:**

1. **Cache por execução, chaveado pela identidade do valor recebido** — preserva a otimização que existe hoje (o índice é usado muitas vezes dentro de uma mesma análise).
2. **Sem cache, reconstruído a cada chamada** — mais simples e obviamente correto, ao custo de reconstruir o índice repetidamente.

O critério de desempate é medido, não estético: o `parity_harness.md` §5 registra que o custo dominante do harness é o **parse** (`load_gedcom_and_build_graph`), e que os probes de nome custam ~12 s sobre 35.460 nomes, enquanto o parse custa 21-33 s. Reconstruir o índice a cada chamada só é aceitável se não piorar a ordem de grandeza de um `dna_analysis` completo, que é o caso de uso real.

> ⚠️ **CORREÇÃO DE 2026-10-06, medida ao executar o `T014`.** A versão inicial desta seção supunha que "uma árvore nova é um valor novo", e portanto que a **identidade** do dicionário de pessoas serviria de chave de invalidação. **A suposição é falsa enquanto o parse mutar in-place:** `load_gedcom_and_build_graph` faz `clear()` + `update()` em `gedcom_state.people`, então o `id()` do dicionário é o **mesmo em todo o processo**. Um cache chaveado por identidade nunca invalida — e é isso que o `test_6d` do `test_confrontacao_gedcom_dna.py` cobra. A chave implementada é derivada do **conteúdo**: contagem de pessoas e de famílias, mais a primeira e a última chave de `people`. Quando o `T023` remover o estado e `carregar_arvore` passar a devolver dicionários novos, a identidade volta a ser chave válida — mas o conteúdo continua sendo a chave correta, e não há razão para trocar.

## 6. Impacto em persistência

**Nenhum.** `src/uploads/` continua sendo o único estado persistente, com arquivos imutáveis sob chave de conteúdo, escrito por `src/app.py` e não pelo núcleo. A chave de armazenamento (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`, `utils/validate.py`) e o teto de 16 MB não mudam. Nenhum arquivo em disco é criado, movido, renomeado ou removido por esta feature.

## 7. Resíduo de dados que já existe e não pertence a esta feature

Durante a verificação de 2026-10-06 a árvore de trabalho continha, **não rastreados e não criados por esta feature**:

| Caminho | Origem provável | Ação nesta feature |
|---|---|---|
| `tmpb90r4grj.ged`, `tmps3gjzcaj.ged` (raiz) | arquivos temporários de execução que ficaram para trás | nenhuma — fora do escopo; registrado |
| `_reversa_sdd/parity/_collect_oracle.py`, `_collect_cand.py` | resíduo do harness, que o `parity_harness.md` §7 manda limpar | limpar com `_clean_residue.py` no passo 2 do plano |
| `.parity-run-oracle/`, `.parity-run-cand/`, `.pytest-tmp/` | diretórios de execução de sessões anteriores | nenhuma — fora do escopo; registrado |

> Registrado por honestidade: nada disso é dado de domínio nem dado pessoal, e nada disso é produzido pela feature. Está aqui para que uma leitura futura do `git status` não atribua o resíduo a esta mudança.

## 8. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-plan` | reversa |
