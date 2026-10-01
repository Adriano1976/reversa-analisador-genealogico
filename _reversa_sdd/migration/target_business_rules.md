---
schemaVersion: 1
generatedAt: 2026-09-28T02:52:40Z
reversa:
  version: "1.2.58"
kind: target_business_rules
producedBy: curator
hash: "sha256:2a42d1b6a9e6bc49923151e77c897f027becd994028af2a6e629d05fccb9d601"
---

# Target Business Rules

> Catálogo das regras de negócio do legado com decisão de migração: MIGRAR, DESCARTAR ou DECISÃO HUMANA.
> Cada item rastreia para a origem em `_reversa_sdd/` e respeita o `paradigm_decision.md`.

## Resumo
- Total de regras analisadas: 49
- MIGRAR: 34
- DESCARTAR: 7 (detalhe em `discard_log.md`)
- DECISÃO HUMANA: 8 — **todas RESOLVIDAS** em 2026-09-28T02:56:00Z pelo usuário, aceitando as recomendações do Curator

> Nota de reconciliação: a contagem inicial era 6 DESCARTAR / 9 DECISÃO HUMANA. Após a decisão do usuário, **BR-HUMANA-002** (remoção do `secret_key` hardcoded) foi resolvida como **descarte de fronteira**, saindo da seção DECISÃO HUMANA e entrando em `discard_log.md` como **BR-DESCARTAR-007**. O total de 49 regras não muda.

**Critério aplicado**: `derived_appetite = balanced` (opção 3 — híbrido) do `paradigm_decision.md`. Regra de fronteira: **algoritmo de negócio → MIGRAR com fidelidade**; **mecanismo de plumbing do paradigma procedural → DESCARTAR**; **lacuna/ambiguidade → DECISÃO HUMANA**, sempre.

## Regras MIGRAR

### BR-MIGRAR-001 — Parsing GEDCOM: registros INDI e FAM
- **Origem**: `_reversa_sdd/upload-gedcom/design.md` § "Detalhe do fluxo de parsing"
- **Confiança original**: 🟢
- **Descrição**: Abrir o arquivo com `GedcomReader`, ler registros `INDI` para o dicionário `people` e `FAM` para `families`.
- **Justificativa de migração**: É a porta de entrada do domínio. O formato GEDCOM é restrição inegociável do brief. `ged4py` é biblioteca de parsing, não mecanismo de paradigma.
- **Compatibilidade com paradigma alvo**: Função pura de parsing sem I/O implícito — recebe caminho/bytes, devolve `GedcomTree`. Note que o alvo persiste a árvore (o legado descartava a cada requisição): o **parsing** é idêntico, o **ciclo de vida** muda (ver BR-DESCARTAR-001).

### BR-MIGRAR-002 — Grafo bidirecional pessoa ↔ família e índice filho→família
- **Origem**: `_reversa_sdd/upload-gedcom/design.md` § "Detalhe do grafo"; `code-analysis.md` §3 (`build_graph_from_parser`)
- **Confiança original**: 🟢
- **Descrição**: Criar nó por pessoa e nó por família; ler `HUSB`, `WIFE`, `CHIL`; conectar cônjuges e filhos ao nó da família; preencher `c2f` (filho → famílias).
- **Justificativa de migração**: Estrutura de relacionamento que sustenta 100% dos algoritmos de caminho. É invariante de domínio, não mecanismo.
- **Compatibilidade com paradigma alvo**: `networkx` pode permanecer como detalhe de implementação interno do aggregate `GedcomTree`, desde que não vaze para a API. Alternativa: índice próprio. Decisão do Designer.

### BR-MIGRAR-003 — Nome formatado; fallback "Sem Nome" é **incompleto na prática**
- **Origem**: `_reversa_sdd/upload-gedcom/requirements.md` § Regras de Negócio; `design.md` § Fluxos Alternativos (`get_name`, `app.py:42`)
- **Confiança original**: 🟢
- **Descrição**: Nomes são formatados em formato GEDCOM. O fallback **"Sem Nome"** existe, mas é **mais estreito do que a spec afirma**: `get_name` é `return person.name.format() if person and person.name else "Sem Nome"`. O literal só é produzido quando `person.name` é **ausente/falsy**; quando `person.name` **existe mas seu formato é vazio**, a função retorna **string vazia**.
- **Justificativa de migração**: Regra de apresentação de domínio; afeta a lista de nomes oferecida ao usuário.
- **Compatibilidade com paradigma alvo**: ⚠️ **Comportamento congelado e não intuitivo.** Migrar `get_name` **literalmente**, incluindo o caminho que retorna string vazia. Não "corrigir" para sempre retornar "Sem Nome" — isso quebraria paridade em 318 nomes reais (ver correção factual).
- **⚠️ CORREÇÃO FACTUAL (2026-09-28T04:40Z, verificada executando o oráculo sobre os dados reais)**: a spec afirma que *"Pessoas sem nome são listadas como 'Sem Nome'"* (`upload-gedcom/requirements.md` § Regras de Negócio). **Isso é impreciso.** Medição sobre as 6 árvores GEDCOM reais do usuário (**55.523 nomes**):

  | Árvore | Total de nomes | String **vazia** | Literal `"Sem Nome"` |
  |---|---|---|---|
  | `Arvore_Unificada_Oficial_V1_2.ged` | 35.460 | **301** | **0** |
  | `sssazevedo_2025-10-07.ged` | 4.420 | 0 | 0 |
  | `Backup-Arvore-Sandro-12-11-2024.ged` | 4.313 | 0 | 0 |
  | `Gedcom_Sandro.ged` | 4.313 | 0 | 0 |
  | `SandroTree.ged` | 3.961 | 0 | 0 |
  | `Adriano_Santos.ged` | 3.056 | **17** | **0** |
  | **TOTAL** | **55.523** | **318** | **0** |

  **Conclusão**: o literal `"Sem Nome"` **nunca foi observado em dado real** (0 ocorrências); o que ocorre é **string vazia**, em **318 pessoas (0,57%)**. O caminho do fallback provavelmente só dispara em casos que os dados reais não exercitam (pessoa sem o objeto `name`).
  - **Impacto na UI**: a string vazia entra na lista de nomes como uma **opção em branco**, visível e selecionável na `datalist`. O usuário pode escolher um valor vazio e submeter — comportamento que a spec não descreve.
  - **Impacto no schema**: `target_data_model.md` declara `display_name TEXT NOT NULL`. **String vazia satisfaz `NOT NULL`** — então não há conflito de schema aqui (diferente do caso do cM em BR-MIGRAR-021), mas a decodificação precisa aceitar `''` como valor legítimo, não tratar como ausente.
  - **Impacto nos testes**: o cenário de `01-carregar-gedcom.feature` foi **reescrito** para cobrir os **dois** caminhos (nome ausente → `"Sem Nome"`; nome presente com formato vazio → `""`), em vez de afirmar apenas o literal.
  - **Por que sobreviveu ao pipeline**: é o **mesmo modo de falha do AMB-023**. A spec de origem afirmava o comportamento "correto e intuitivo"; o código implementa algo mais estreito; nenhum dado real havia sido confrontado. Descoberto na primeira execução sobre dados reais.

### BR-MIGRAR-004 — Lista de nomes ordenada alfabeticamente
- **Origem**: `_reversa_sdd/upload-gedcom/requirements.md` § Regras de Negócio; `design.md` § passo 5
- **Confiança original**: 🟢
- **Descrição**: Após o parse, retornar/expor todos os nomes ordenados alfabeticamente.
- **Justificativa de migração**: Afeta a UX de seleção de pessoa-raiz e a reprodutibilidade dos testes de paridade (ordem é observável).
- **Compatibilidade com paradigma alvo**: Ordenação deve ocorrer antes de virar payload JSON, para preservar paridade observável.

### BR-MIGRAR-005 — Validação de presença do arquivo e do nome do arquivo
- **Origem**: `_reversa_sdd/upload-gedcom/requirements.md` § Regras de Negócio (`app.py:563-567`)
- **Confiança original**: 🟢
- **Descrição**: Campo `gedcom` ausente → "Nenhum arquivo GEDCOM enviado."; `filename` vazio → "Nenhum arquivo selecionado."
- **Justificativa de migração**: São erros de entrada com semântica distinta — a validação é regra, o transporte é que muda.
- **Compatibilidade com paradigma alvo**: Separar em duas exceções de domínio (`MissingGedcomFile`, `EmptyFilename`). As **mensagens** são conteúdo de UI; ver BR-DESCARTAR-004 sobre o transporte. Preservar as mensagens como chaves i18n para paridade de UX.

### BR-MIGRAR-006 — Limpeza de mojibake (`strip_bad_utf`, `demojibake`)
- **Origem**: `_reversa_sdd/domain.md` § 2.3; `code-analysis.md` § 4.1; `analise-dna/design.md` § Interface
- **Confiança original**: 🟢
- **Descrição**: Corrigir encoding corrompido de acentos em nomes portugueses (`Ã§`→`ç`, `JoA�o`→`João`), com tentativa de re-encoding `s.encode("latin1").decode("utf-8")`.
- **Justificativa de migração**: **Núcleo do matching.** Sem isso, nomes acentuados não casam e o resultado muda. É algoritmo de negócio, não plumbing.
- **Compatibilidade com paradigma alvo**: Função pura, preservada com fidelidade literal, inclusive as substituições heurísticas incompletas (`architecture.md` dívida #7). Não "melhorar" — a inconsistência faz parte do comportamento observado. ⚠️ Nota: `demojibake` lança em strings não-Latin-1; o tratamento dessa exceção faz parte do comportamento.

### BR-MIGRAR-007 — Normalização de nome (`norm_name`) e decomposição pt-BR
- **Origem**: `_reversa_sdd/analise-dna/design.md` § Interface (`norm_name`, `split_name_pt`, `surnames_set`)
- **Confiança original**: 🟢
- **Descrição**: Normalizar com NFKD, remover acentos, minúsculas; decompor nome em `(given, surnames, suffixes)`; deduplicar sobrenomes em conjunto.
- **Justificativa de migração**: Pré-requisito determinístico de todo o scoring e das regras A/B/C/D.
- **Compatibilidade com paradigma alvo**: Funções puras. Manter NFKD e a ordem de operações — `unidecode`/NFKD produzem resultados distintos em casos de borda.

### BR-MIGRAR-008 — Índice de nomes e pool de candidatos (exact → sobrenome → prefixo)
- **Origem**: `_reversa_sdd/analise-dna/design.md` § "Detalhe do matching" passos 2-4 (`app.py:667-688`)
- **Confiança original**: 🟢
- **Descrição**: Busca exata normalizada em `ged_index`; se não houver, restringe por `surname_index`; fallback por prefixos de sobrenome (`token_prefixes`, mín. 3 chars).
- **Justificativa de migração**: Define **quem entra no pool de candidatos**. Um pool diferente produz matches diferentes, mesmo com o mesmo score. É algoritmo de negócio.
- **Compatibilidade com paradigma alvo**: Funções puras sobre índices construídos uma vez por árvore. Nota de performance: no alvo os índices podem ser cacheados por árvore (hoje são reconstruídos a cada POST) **sem alterar o conjunto resultante** — cache é permitido, mudança de predicado não.

### BR-MIGRAR-009 — Score de matching difuso: fórmula e pesos
- **Origem**: `_reversa_sdd/domain.md` § 2.3; `code-analysis.md` § 4.2; `analise-dna/requirements.md` § Regras de Negócio
- **Confiança original**: 🟢
- **Descrição**: `Score = 0.55 × token_sort_ratio + 0.25 × partial_ratio + 0.20 × given_ratio + InterBonus`, com `InterBonus = 8.0 × |interseção de sobrenomes| − 4.0 × |sobrenomes comuns|`.
- **Justificativa de migração**: **Núcleo absoluto.** Restrição explícita do brief ("matching congelado"). Os pesos são literais e qualquer alteração muda o ranking e as aceitações.
- **Compatibilidade com paradigma alvo**: Função pura com constantes nomeadas (`W_TOKEN=0.55`, `W_PARTIAL=0.25`, `W_GIVEN=0.20`, `INTER_BONUS_HIT=8.0`, `INTER_BONUS_COMMON=−4.0`). ⚠️ **Nomear não pode alterar valor nem ponto flutuante**: usar os mesmos literais, mesma ordem de soma (soma em ponto flutuante não é associativa — reordenar pode mudar o último dígito e, em empate, o desempate).

### BR-MIGRAR-010 — Filtro anti-falso-positivo por interseção de sobrenomes
- **Origem**: `_reversa_sdd/domain.md` § 2.3; `code-analysis.md` § 4.3; `analise-dna/requirements.md` § Regras de Negócio
- **Confiança original**: 🟢
- **Descrição**: Se ambos os nomes têm sobrenomes e a interseção é 0, o candidato é **rejeitado** — exceto quando há sufixo salvador (`filho`, `neto`).
- **Justificativa de migração**: Regra de rejeição que define falsos negativos/positivos. Núcleo congelado.
- **Compatibilidade com paradigma alvo**: Função pura. Preservar exatamente a lista de sufixos salvadores.

### BR-MIGRAR-011 — Interseção mínima adaptativa para primeiro nome genérico
- **Origem**: `_reversa_sdd/domain.md` § 2.3; `code-analysis.md` § 4.3
- **Confiança original**: 🟡
- **Descrição**: Primeiro nome genérico (ex.: `Maria`, `José`, `João`) com 2+ sobrenomes no CSV exige interseção ≥ 2 sobrenomes.
- **Justificativa de migração**: Política 5 do Curator — 🟡 INFERIDA compatível com o alvo → MIGRAR com aviso.
- **Compatibilidade com paradigma alvo**: ⚠️ **Validar no agente de codificação**: a lista exata de "primeiros nomes genéricos" não está transcrita nas specs — está no código (`app.py`). O implementador deve extraí-la do legado, não inferi-la. Se a lista for inventada, a paridade quebra silenciosamente.

### BR-MIGRAR-012 — Equivalência de grafia e abreviações
- **Origem**: `_reversa_sdd/domain.md` § 2.3
- **Confiança original**: 🟢
- **Descrição**: Equivalentes de grafia (`netto→neto`, `gouvea/gouvêa→gouveia`); prefixos de sobrenome (mín. 3 chars) usados para matches abreviados/corrompidos.
- **Justificativa de migração**: Núcleo do matching. Sem isso, variantes regionais de grafia deixam de casar.
- **Compatibilidade com paradigma alvo**: Função pura. ⚠️ A **tabela de equivalentes** deve ser transcrita do código, não recriada de memória.

### BR-MIGRAR-013 — Regras A/B/C/D de aceitação do matching
- **Origem**: `_reversa_sdd/analise-dna/design.md` § "Detalhe do matching" passo 7 (`app.py:726-793`); `questions.md` Pergunta 1
- **Confiança original**: 🟢 (resposta humana explícita em `questions.md`)
- **Descrição**: Conjunto de regras combinatoriais (dado genérico/não-genérico × interseção de sobrenomes × thresholds de Jaccard/score/given) que decide `candidate_pids`. Limiares literais: 92, 90, 86, 100.
- **Justificativa de migração**: `questions.md` Pergunta 1 — **Resposta: "São comportamentos definitivos — devem ser preservados com fidelidade numa reimplementação."** Restrição "matching congelado" do brief. **Não são lacuna aberta.**
- **Compatibilidade com paradigma alvo**: Expressar cada regra como predicado puro nomeado (`RuleA`, `RuleB`, `RuleC`, `RuleD`), preservando **a ordem de avaliação** — as regras são sequenciais e o primeiro match decide. Reordenar muda o resultado. ⚠️ As regras são descritas como "complexas e silenciosas" (`domain.md` §4) e **sem cobertura de teste no legado**: o implementador precisa extrair a árvore de decisão do código, não reconstruí-la a partir da descrição textual.

### BR-MIGRAR-014 — Relaxamento de Jaccard para cM alto
- **Origem**: `_reversa_sdd/analise-dna/design.md` § Riscos; `questions.md` Pergunta 4 (`app.py:751-753`)
- **Confiança original**: 🟢 (resposta humana explícita)
- **Descrição**: Para cM ≥ 150 e dado não-genérico, o threshold de Jaccard relaxa de 0.5 para 0.33.
- **Justificativa de migração**: `questions.md` Pergunta 4 — **Resposta: "Intencional — mantém-se o relaxamento."** Congelado. Aceita-se o risco de falsos positivos como trade-off deliberado.
- **Compatibilidade com paradigma alvo**: Constantes nomeadas (`JACCARD_DEFAULT=0.5`, `JACCARD_HIGH_CM=0.33`, `HIGH_CM_THRESHOLD=150`).

### BR-MIGRAR-015 — Desempate de candidatos
- **Origem**: `_reversa_sdd/analise-dna/design.md` § "Detalhe do matching" passo 6 (`app.py:721-724`)
- **Confiança original**: 🟢
- **Descrição**: Em empate, desempatar por (1) interseção de sobrenomes, depois (2) `given`, depois (3) score.
- **Justificativa de migração**: A ordem do desempate determina qual pessoa é escolhida quando dois candidatos empatam — resultado observável.
- **Compatibilidade com paradigma alvo**: ⚠️ Ordenação estável obrigatória. Em Python, `sorted` é estável; se o alvo usar outra estrutura ou paralelizar, o desempate precisa ser determinístico e idêntico.

### BR-MIGRAR-016 — Agregação de segmentos: chave `_group_key` e soma de cM
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio; `design.md` § passo 8 (`app.py:617-635`)
- **Confiança original**: 🟢
- **Descrição**: Segmentos duplicados do mesmo match são agrupados pela chave `_group_key` (nome normalizado + ID/email) e os cM são **somados** (`groupby.agg`).
- **Justificativa de migração**: Determina o cM total, que por sua vez determina a relação prevista por faixa. Erro aqui propaga para toda a saída.
- **Compatibilidade com paradigma alvo**: ⚠️ A composição exata de `_group_key` (nome normalizado? qual normalização? ID/email como fallback?) precisa ser transcrita do código. Além disso, **somar em ponto flutuante é não-associativo** — se o alvo agregar com `SUM` do PostgreSQL em vez de acumulação em ordem de leitura, o resultado pode diferir no último dígito e cruzar um limite de faixa de cM. Preservar a ordem de acumulação.

### BR-MIGRAR-017 — Leitura de CSV com fallback de encoding
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio e RF-01; `design.md` § passo 5 (`app.py:598-601`)
- **Confiança original**: 🟢
- **Descrição**: Ler o CSV tentando UTF-8 e caindo para Latin-1 em caso de falha.
- **Justificativa de migração**: RF-01 (Must): "CSV Latin-1 é lido sem erro". Compatibilidade de arquivo real dos usuários — restrição do brief.
- **Compatibilidade com paradigma alvo**: Estratégia explícita de codec nomeada, não `try/except` incidental. ⚠️ Preservar a **ordem** de tentativa (UTF-8 primeiro) e o tipo de exceção que dispara o fallback.

### BR-MIGRAR-018 — Detecção tolerante de colunas Nome / cM / ID-Email
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio e RF-02; `design.md` § passo 6 (`app.py:606-615`)
- **Confiança original**: 🟢
- **Descrição**: Nome aceito como `Name`/`MatchedName`/`Nome`; cM como `cM`/`TotalCM`/`Total cM`.
- **Justificativa de migração**: É o que permite ler CSVs de exportadores diferentes (MyHeritage, FTDNA, GEDmatch) — restrição inegociável do brief.
- **Compatibilidade com paradigma alvo**: Função pura de mapeamento cabeçalho→campo. ⚠️ `design.md` § Riscos registra dependência de **ordem/posição** das colunas como heurística: a resolução por posição, quando os nomes não casam, precisa ser preservada ou explicitamente descartada (ver BR-DESCARTAR-006).

### BR-MIGRAR-019 — Detecção de ID de match por regex `[A-Z]{2}\d{7}`
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio; `reconstruction-report.md` § Decisões de fidelidade
- **Confiança original**: 🟢
- **Descrição**: IDs de match no formato `***` são reconhecidos por regex.
- **Justificativa de migração**: Entra na composição da `_group_key` — muda o agrupamento se alterado. Já houve decisão explícita de preservá-lo durante a reconstrução.
- **Compatibilidade com paradigma alvo**: Constante nomeada. Manter a regex literal, inclusive a limitação de cobertura entre exportadores registrada em `confidence-report.md` § Lacunas.

### BR-MIGRAR-020 — Tabela de relação prevista por faixa de cM
- **Origem**: `_reversa_sdd/domain.md` § 2.1; `code-analysis.md` § 4.4
- **Confiança original**: 🟢
- **Descrição**: 9 faixas de cM (3300–3720, 2200–3400, 1317–2312, 553–1330, 200–850, 46–515, 30–350, 10–220, 0–110) mapeadas para relações prováveis.
- **Justificativa de migração**: Saída principal do produto (RF-06). Regra de negócio pura.
- **Compatibilidade com paradigma alvo**: Tabela como dado de domínio. ⚠️ **Atenção às sobreposições**: as faixas se sobrepõem (ex.: 46–515 e 200–850 contêm 200–515). A ordem de avaliação define qual relação é retornada para um cM em zona de sobreposição — preservar a ordem, não "corrigir" a tabela.

### BR-MIGRAR-021 — cM não numérico ou ≤ 0 → **lista vazia** de relações
- **Origem**: `_reversa_sdd/domain.md` § 2.1 (Observação) ⚠️ **ver correção factual abaixo**
- **Confiança original**: 🟢
- **Descrição**: cM `<= 0` ou não numérico retorna **lista vazia** (`[]`), **não** uma mensagem. Verificado por execução direta do oráculo: `get_relationships_by_cm(0) == []` e `get_relationships_by_cm(-5) == []`.
- **Justificativa de migração**: Caso de borda explícito. O comportamento migra como **lista vazia**, preservado literalmente.
- **Compatibilidade com paradigma alvo**: `RelationshipLabel` deve ser **anulável** no alvo — um match com cM ≤ 0 não tem relação prevista. ⚠️ **Impacto no schema**: `match_result.relationship_label` foi especificado como `NOT NULL` em `target_data_model.md`; precisa aceitar nulo ou o pipeline deve definir um rótulo explícito para "sem relação".
- **⚠️ CORREÇÃO FACTUAL (2026-09-28T04:30Z, verificada contra o oráculo congelado)**: `domain.md` §2.1 registra que *"cM `<= 0` ou não numérico retorna 'Relação distante ou indeterminada'"*. **Isso está incorreto.** O código do oráculo (L…, `get_relationships_by_cm`) retorna **lista vazia** para cM ≤ 0 ou não numérico; o literal **"Relação distante ou indeterminada"** é retornado em uma condição diferente — quando o valor é um número **positivo** que **não cai em nenhuma das 9 faixas**. São dois casos distintos que a spec havia fundido em um.
  - **Caso A** — cM ≤ 0 ou não numérico → `[]` (lista vazia)
  - **Caso B** — cM > 0 fora de todas as faixas → `["Relação distante ou indeterminada"]`
  - **Efeito**: um teste de paridade escrito com base na spec teria **falhado corretamente** no Caso A, revelando o erro. Registrado aqui e propagado para `data_migration_plan.md`, `target_domain_model.md`, `target_screens.md` e os cenários `02` e `09`.

### BR-MIGRAR-022 — Conexão direta por ancestral comum (MRCA) via BFS bidirecional
- **Origem**: `_reversa_sdd/busca-caminho/requirements.md` § Regras de Negócio; `design.md` § "Detalhe da conexão direta" (`app.py:298-318`)
- **Confiança original**: 🟢
- **Descrição**: Duas filas BFS subindo exclusivamente por `get_parents` (`FAMC`), intercalando expansão; ao encontrar interseção, montar caminho ascendente + descendente. `start_id == end_id` → caminho trivial.
- **Justificativa de migração**: Núcleo do produto (RF-02). Busca direta executada **antes** do fallback indireto — a ordem é regra.
- **Compatibilidade com paradigma alvo**: Função pura sobre a árvore. ⚠️ **BFS bidirecional com intercalação** produz resultado diferente de BFS simples quando há múltiplos MRCAs — é escolha de "ancestral de menor profundidade" e deve ser reproduzida, não substituída por `nx.lowest_common_ancestor` (`design.md` registra explicitamente que o legado **não** usa essa função).

### BR-MIGRAR-023 — Limite de profundidade da busca direta: 20
- **Origem**: `_reversa_sdd/domain.md` § 2.4; `busca-caminho/design.md` § passo 4
- **Confiança original**: 🟢
- **Descrição**: `find_ancestral_path(max_depth=20)`; ao estourar, retorna `(None, None)` — o que aciona o fallback indireto.
- **Justificativa de migração**: Não é só performance: estourar o limite **muda o caminho do fluxo** (cai para indireto ou descarta o match). É regra de negócio.
- **Compatibilidade com paradigma alvo**: Constante nomeada `MAX_ANCESTOR_DEPTH=20`. Manter o comportamento de estouro (retorno nulo), não lançar exceção.

### BR-MIGRAR-024 — Conexão indireta por afinidade: `shortest_path` com compressão de famílias
- **Origem**: `_reversa_sdd/busca-caminho/requirements.md` § Regras de Negócio; `design.md` § "Detalhe da conexão indireta" (`app.py:284-292`)
- **Confiança original**: 🟢
- **Descrição**: Fallback quando não há ancestral comum: `nx.shortest_path` no grafo geral; comprimir o caminho mantendo só nós de pessoa; menos de 2 pessoas → `None`.
- **Justificativa de migração**: RF-03. Sem o fallback, conexões por casamento/cunhadismo desaparecem.
- **Compatibilidade com paradigma alvo**: Função pura sobre o grafo. ⚠️ `nx.shortest_path` é BFS não ponderado — com múltiplos caminhos de mesmo comprimento, **qual** caminho é retornado depende da ordem de inserção das arestas no grafo. Para paridade determinística, o implementador deve garantir ordem de inserção idêntica à do legado (que deriva da ordem dos registros no GEDCOM).

### BR-MIGRAR-025 — Limite de hops da busca indireta: 40
- **Origem**: `_reversa_sdd/domain.md` § 2.4; `busca-caminho/design.md` § passo 3 (`app.py:288-289`)
- **Confiança original**: 🟢
- **Descrição**: `len(path) − 1 > max_hops` (40) → `None` → "Nenhuma conexão encontrada".
- **Justificativa de migração**: Define o limite de "conexão plausível"; acima disso o resultado é declarado inexistente.
- **Compatibilidade com paradigma alvo**: `MAX_INDIRECT_HOPS=40`. Nota: o limite é aplicado ao caminho **bruto com nós de família**, antes da compressão — preservar a ordem (medir antes de comprimir).

### BR-MIGRAR-026 — Uso do primeiro ID encontrado para cada nome (homônimos)
- **Origem**: `_reversa_sdd/busca-caminho/requirements.md` § Regras de Negócio; `design.md` § Decisões; `questions.md` Pergunta 2 (`app.py:853`)
- **Confiança original**: 🟢 (resposta humana explícita)
- **Descrição**: Quando há homônimos, usa o **primeiro** ID da lista retornada por `find_person_by_name`.
- **Justificativa de migração**: `questions.md` Pergunta 2 — **Resposta: "Pode manter como está — o comportamento do primeiro ID já foi validado várias vezes."** Congelado. **Não é lacuna aberta.**
- **Compatibilidade com paradigma alvo**: ⚠️ Decisão de produto consciente com risco conhecido (`busca-caminho/design.md` § Riscos: "pode conectar a pessoa errada"). Em SaaS multiusuário, avaliar se a desambiguação deve ser oferecida **como recurso adicional** sem alterar o default (ver BR-HUMANA-003). O default permanece o 1º ID.

### BR-MIGRAR-027 — `find_person_by_name`: exact match e depois substring
- **Origem**: `_reversa_sdd/busca-caminho/design.md` § Interface (`app.py:208-211`)
- **Confiança original**: 🟢
- **Descrição**: Localizar pessoas por exact match e, se não houver, por substring; retorna `list[str]` de IDs.
- **Justificativa de migração**: Determina **quais** candidatos entram na resolução de nome, e a ordem da lista define qual ID o 1º-ID escolhe (BR-MIGRAR-026). Acoplamento direto com resultado observável.
- **Compatibilidade com paradigma alvo**: ⚠️ A ordem da lista é significativa. Preservar a ordem de iteração do GEDCOM.

### BR-MIGRAR-028 — Mensagens de erro e resultado com literais preservados
- **Origem**: `_reversa_sdd/busca-caminho/requirements.md` § Critérios de Aceitação; `upload-gedcom/requirements.md` § Regras; `analise-dna/requirements.md` § Critérios
- **Confiança original**: 🟢
- **Descrição**: "Nenhuma conexão encontrada entre 'X' e 'Y'.", "Pessoa 1 'X' não encontrada.", "Conexão direta encontrada (ancestral comum).", "Conexão indireta encontrada (via casamento/afinidade).", "Seu nome 'X' não foi encontrado no GEDCOM.", "Por favor, carregue o arquivo CSV de matches."
- **Justificativa de migração**: São conteúdo de domínio observável e a base textual dos critérios de aceitação Gherkin. Preservadas como chaves de i18n no alvo (o **transporte** muda — ver BR-DESCARTAR-004).
- **Compatibilidade com paradigma alvo**: Chaves i18n com o literal português como valor padrão. Não reescrever a redação — os `parity_tests/` do Inspector podem asserir sobre ela.

### BR-MIGRAR-029 — Match sem caminho ancestral é listado como descartado
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio e RF-07; `design.md` § Fluxos Alternativos (`app.py:821-822`)
- **Confiança original**: 🟢
- **Descrição**: Candidato aceito pelo matching mas sem caminho até a raiz entra em `skipped_matches` com motivo, em vez de sumir.
- **Justificativa de migração**: RF-07 (Should). Auditoria visível — o usuário precisa ver o que foi descartado e por quê. Fundamental para confiança no matching heurístico.
- **Compatibilidade com paradigma alvo**: ⚠️ Hoje o motivo é uma string para humano. No alvo deve virar **código de motivo tipado + mensagem**, para permitir auditoria programática. A lista `skipped_matches` permanece no payload.

### BR-MIGRAR-030 — Match sem candidato no GEDCOM é listado como descartado
- **Origem**: `_reversa_sdd/analise-dna/design.md` § Fluxos Alternativos (`app.py:799-801`)
- **Confiança original**: 🟢
- **Descrição**: Match cujo nome não corresponde a ninguém entra em `skipped_matches` com motivo.
- **Justificativa de migração**: Mesmo valor de auditoria de BR-MIGRAR-029; critério de aceitação Gherkin explícito.
- **Compatibilidade com paradigma alvo**: Idem BR-MIGRAR-029.

### BR-MIGRAR-031 — Ordenação de resultados por cM decrescente
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio; `design.md` § passo 12
- **Confiança original**: 🟢
- **Descrição**: Resultados exibidos ordenados por cM decrescente.
- **Justificativa de migração**: Ordem observável e critério de aceitação. Preservá-la no payload da API (não delegar a ordenação ao cliente).
- **Compatibilidade com paradigma alvo**: ⚠️ Empates de cM: a ordem relativa deve ser estável e reproduzível para os testes de paridade.

### BR-MIGRAR-032 — Root person: primeiro ID encontrado pelo nome
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio
- **Confiança original**: 🟢
- **Descrição**: `root_name` deve existir no GEDCOM; se houver homônimos, usa o primeiro ID encontrado.
- **Justificativa de migração**: Mesma política de BR-MIGRAR-026 aplicada à raiz. Define o ponto de referência de todos os caminhos.
- **Compatibilidade com paradigma alvo**: Idem BR-MIGRAR-026.

### BR-MIGRAR-033 — Requisitos de entrada da análise de DNA
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Regras de Negócio e § Fluxo
- **Confiança original**: 🟢
- **Descrição**: Exige GEDCOM carregado (`gedcom_filename`), CSV presente (`matches_csv`) e `root_name` localizável; cada ausência tem mensagem específica.
- **Justificativa de migração**: Pré-condições com semântica distinta e mensagens observáveis — critérios de aceitação Gherkin.
- **Compatibilidade com paradigma alvo**: ⚠️ Mudança de contexto real: no legado "GEDCOM carregado" significa "existe no estado global do processo". No alvo multiusuário significa "existe uma árvore persistida pertencente a este usuário" (ou um upload na mesma requisição). A **semântica** deve ser reinterpretada com o Designer — a mensagem e o comportamento visível, preservados.

### BR-MIGRAR-034 — Requisitos funcionais Must de robustez (RF-04, RF-05, RF-08)
- **Origem**: `_reversa_sdd/{upload-gedcom,busca-caminho,analise-dna}/requirements.md` § Requisitos Funcionais
- **Confiança original**: 🟢
- **Descrição**: Responder erros de parsing/execução de forma amigável, sem quebrar a aplicação; erros específicos por tipo de falha.
- **Justificativa de migração**: RF de robustez classificados Must nas três units. A **garantia** (não quebrar, informar o que houve) é invariante de produto e requisito de UX em SaaS.
- **Compatibilidade com paradigma alvo**: A garantia migra; o **mecanismo** (renderizar `index.html` com `message=`) é descartado — ver BR-DESCARTAR-004. No alvo: exception handler → status HTTP + payload de erro tipado.

## Regras DESCARTAR (resumo)

| ID | Origem | Motivo curto | Vínculo a paradigma? |
|---|---|---|---|
| BR-DESCARTAR-001 | `upload-gedcom/design.md` § Estado Interno; `architecture.md` §1 | Estado global mutável compartilhado + re-parse a cada POST. Persistência por usuário substitui. | sim |
| BR-DESCARTAR-002 | `analise-dna/design.md` § Estado Interno | `dna_matches_df` como DataFrame local à requisição, sem persistência. Aggregate + repositório substituem. | sim |
| BR-DESCARTAR-003 | `upload-gedcom/design.md` § Decisões (`app.py:569`) | Salvar arquivo em `uploads/` com o **nome original do cliente**, sem escopo por usuário. Object storage escopado substitui. | sim |
| BR-DESCARTAR-004 | `{upload-gedcom,busca-caminho,analise-dna}/design.md` § Interface | Transporte de resultado/erro por render do `index.html` com `status 200 (sempre)`. API + SPA substituem. | sim |
| BR-DESCARTAR-005 | `busca-caminho/design.md` § Interface; `analise-dna/design.md` § passo 12 | Geração de diagramas Mermaid **no servidor** como string para o template. Payload estruturado + render no cliente substituem. | sim |
| BR-DESCARTAR-006 | `analise-dna/design.md` § Riscos; `questions.md` Pergunta 3 | Aceitação da limitação "sem validação de extensão/tamanho, sobrescrita de nome, sem concorrência". **Incompatível com o brief atual** (multiusuário público + LGPD). **Descartada por decisão do usuário** (BR-HUMANA-001, opção 3). | não |
| BR-DESCARTAR-007 | `architecture.md` §5 dívida #6; `{upload-gedcom,analise-dna}/requirements.md` § Riscos | `secret_key` **hardcoded** (`'f@milyse@rch_dna_edition_v16'`). Sai do código para configuração/secret manager. **Descartada por decisão do usuário** (BR-HUMANA-002, opção 1). | não |

> Detalhe completo em `discard_log.md`.

## Regras DECISÃO HUMANA

### BR-HUMANA-001
- **Origem**: `_reversa_sdd/upload-gedcom/requirements.md` § Requisitos Não Funcionais (🔴); `questions.md` Pergunta 3; `discard_log.md` BR-DESCARTAR-006
- **Tipo de ambiguidade**: 🔴 GAP — e agora **conflito direto com o brief**
- **Descrição**: O legado **não** valida extensão nem tamanho do arquivo enviado e aceita sobrescrita de arquivos de mesmo nome. Na descoberta, isso foi respondido como *"limitação aceita para uso local — manter sem política de segurança"* (`questions.md` Pergunta 3). **Porém esta migração muda o contexto de uso**: o brief declara produto **multiusuário para usuários externos** com **dados genéticos sensíveis** e conformidade **LGPD/GDPR**. A resposta original pressupunha "uso local". Preservar a limitação por paridade significaria publicar um endpoint público sem validação de upload.
- **Opções**:
  1. **Corrigir (recomendado)**: adicionar validação de extensão/MIME e tamanho máximo, nomes de arquivo gerados pelo servidor (UUID) e escopo por usuário. Tratar a resposta de `questions.md` como **superada pela mudança de contexto**.
  2. **Preservar por paridade estrita**: replicar a ausência de validação. Garante paridade byte-a-byte no comportamento de upload, mas publica uma superfície de abuso em produto com dado sensível.
  3. **Meio-termo**: validar extensão/tamanho e escopar por usuário (correções de fronteira), **sem** alterar nenhum comportamento de parsing do conteúdo do arquivo.
- **Recomendação do Curator**: **Opção 3**. É a aplicação literal da regra de fronteira do `paradigm_decision.md`: validação de upload é *plumbing de fronteira* (modernização livre), enquanto o parse do conteúdo é *núcleo* (fidelidade absoluta). Preservar a limitação não é "fidelidade" — é transportar um defeito para um contexto onde ele deixa de ser aceitável. A opção 3 preserva a paridade onde ela importa (nenhum GEDCOM válido passa a ser rejeitado) e corrige onde o contexto mudou.
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: meio-termo (opcao 3) - validar extensao/MIME e tamanho e escopar por usuario na fronteira, sem alterar nenhum comportamento de parsing do conteudo. Justificativa: preservar a limitacao de "uso local" nao e fidelidade, e transportar um defeito para um contexto onde ele deixa de ser aceitavel; nenhum GEDCOM valido passa a ser rejeitado.
### BR-HUMANA-002 — RESOLVIDA COMO DESCARTE
- **Origem**: `_reversa_sdd/architecture.md` §5 (dívida #6); `{upload-gedcom,analise-dna}/requirements.md` § Riscos (🟡)
- **Tipo de ambiguidade**: 🔴 GAP de fronteira com implicação regulatória
- **Descrição**: `app.secret_key = 'f@milyse@rch_dna_edition_v16'` está **hardcoded** no código-fonte. No legado isso é inócuo (sessão local single-user). No alvo, a chave de sessão protege a autenticação de contas que dão acesso a dados genéticos — uma chave pública conhecida permite forjar sessões de qualquer usuário.
- **Opções**:
  1. **Tratar como descartado automaticamente (recomendado)**: a chave é segredo de configuração, não regra de negócio; sai do código e vira variável de ambiente/secret manager. Nenhum impacto em paridade de domínio.
  2. Registrar como decisão humana explícita para rastreabilidade.
- **Recomendação do Curator**: **Opção 1** — descarte trivial e obrigatório, sem trade-off. Mantido aqui apenas porque a dívida é citada nas specs e o implementador não deve gastar uma rodada de decisão com isso.
- **Status**: RESOLVIDA — **reclassificada como descarte** em 2026-09-28T02:56:00Z.
- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendação do Curator. Decisor: Adriano. Escolha: opção 1 — descarte automático. Justificativa: é segredo de configuração, não regra de negócio; nenhum impacto em paridade.
- **Encaminhamento**: registrada em `discard_log.md` como **BR-DESCARTAR-007**. Esta entrada permanece aqui apenas como registro histórico da decisão — a regra vive em `discard_log.md`.

### BR-HUMANA-003
- **Origem**: `_reversa_sdd/busca-caminho/design.md` § Riscos (🔴); `questions.md` Pergunta 2; BR-MIGRAR-026
- **Tipo de ambiguidade**: ⚠️ AMBÍGUA — risco conhecido aceito no contexto antigo
- **Descrição**: Homônimos resolvidos pelo **primeiro ID** podem conectar a pessoa errada. A resposta de `questions.md` Pergunta 2 valida o comportamento *"para uso local"*. Em produto multiusuário, conectar a pessoa errada produz uma árvore de parentesco incorreta — e, pior, pode exibir dados de uma pessoa errada a um usuário. **Não sabemos se o usuário quer manter o default cego ou introduzir desambiguação.**
- **Opções**:
  1. **Manter o 1º ID como default, sem desambiguação (paridade estrita)** — idêntico ao legado.
  2. **Manter o 1º ID por default, mas sinalizar ambiguidade no payload** (ex.: `ambiguous_name: true` com a lista de IDs candidatos) e oferecer desambiguação na UI como recurso **adicional**. Paridade do resultado default preservada; o usuário ganha controle quando quiser.
  3. **Exigir desambiguação explícita** quando houver homônimos. Muda o comportamento: quebra paridade e adiciona um passo obrigatório à UX.
- **Recomendação do Curator**: **Opção 2**. Preserva a paridade (o default não muda, os `parity_tests/` continuam válidos) e resolve o risco real do contexto multiusuário sem impor fricção. A opção 3 é a única que quebraria o critério de paridade #1 declarado no brief.
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - manter o 1o ID como default e sinalizar ambiguidade no payload (ex.: `ambiguous_name: true` + lista de IDs candidatos), oferecendo desambiguacao na UI como recurso adicional. Justificativa: preserva a paridade (o default nao muda; os `parity_tests/` continuam validos) e elimina o risco de exibir a pessoa errada em produto multiusuario.
### BR-HUMANA-004
- **Origem**: `_reversa_sdd/upload-gedcom/requirements.md` § Riscos (🔴); `design.md` § Riscos e § Estado Interno
- **Tipo de ambiguidade**: 🔴 GAP estrutural — **consequência direta de BR-DESCARTAR-001**
- **Descrição**: O legado mantém `people`, `families`, `graph`, `child_to_family` como globais **sobrescritos a cada parse**, sem tratamento de concorrência. Em servidor multi-worker, duas requisições simultâneas corrompem a análise uma da outra. Em multiusuário, a consequência é pior: um usuário vê a árvore de outro. `domain.md` §4 registra como lacuna: *"Sem autenticação/autorização — qualquer acesso possui todas as funcionalidades."*
- **Opções**:
  1. **Resolver por arquitetura (recomendado)**: eliminar o conceito de "GEDCOM carregado" global. Árvore é um aggregate persistido, com `owner_id`, carregado por repositório escopado. O isolamento passa a ser estrutural, não defensivo.
  2. **Escopar por sessão em memória**: um dicionário `{session_id: tree}` com lock. Ainda volátil, ainda não escala por worker, mas isola usuários.
- **Recomendação do Curator**: **Opção 1** — é o que o `paradigm_decision.md` já decidiu como implicação 1 e 4 (estado global vira dependência injetada; `owner_id` vira invariante). Esta entrada existe para dar ao usuário a chance de vetar o custo, não porque a alternativa seja recomendável. ⚠️ **Nota crítica**: a interpretação de `gedcom_filename` no alvo (que arquivo uma requisição de análise referencia?) é decisão de design ainda aberta e será **relitigada no Designer**. Sinalizado aqui para não se perder.
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 1 - eliminar o conceito de "GEDCOM carregado" global; arvore como aggregate persistido com `owner_id`, carregada por repositorio escopado por tenant. Justificativa: torna o isolamento estrutural em vez de defensivo, conforme `paradigm_decision.md` implicacoes 1 e 4. Fica aberta para o Designer a questao do que `gedcom_filename` referencia no alvo.
### BR-HUMANA-005
- **Origem**: `_reversa_sdd/confidence-report.md` § Lacunas Pendentes (analise-dna); `architecture.md` §5 (dívida #7)
- **Tipo de ambiguidade**: ⚠️ AMBÍGUA — heurística incompleta com valor de negócio
- **Descrição**: `strip_bad_utf` usa substituições **manuais e incompletas** de mojibake. A tabela de substituições não está transcrita em nenhuma spec — existe apenas no código (`app.py`). O comportamento é simultaneamente (a) núcleo do matching — sem ele nomes acentuados não casam — e (b) reconhecidamente defeituoso e fragmentado.
- **Opções**:
  1. **Transcrever fielmente do código, inclusive as lacunas (recomendado)**: manter todas as substituições existentes, sem adicionar novas. Paridade garantida.
  2. **Corrigir com estratégia robusta** (ex.: `ftfy` ou detecção de encoding por bytes): melhora a cobertura real, mas **muda resultados** para os GEDCOM que hoje caem nas lacunas — quebra o critério de paridade #1.
  3. **Fiel + extensão opt-in**: manter o comportamento atual como default e oferecer um modo "robusto" explicitamente selecionável.
- **Recomendação do Curator**: **Opção 1** para esta migração. A opção 2 é tentadora mas viola a restrição "matching congelado" do brief. A opção 3 é a evolução correta e pode virar item de `/reversa-forward` depois que a paridade estiver provada.
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 1 - transcrever `strip_bad_utf` fielmente do legado, inclusive as lacunas, sem adicionar substituicoes novas. Justificativa: corrigir com estrategia robusta mudaria resultados para os GEDCOM que hoje caem nas lacunas, violando a restricao "matching congelado" do brief. Modo robusto opt-in fica como candidato a `/reversa-forward` posterior.
### BR-HUMANA-006
- **Origem**: `_reversa_sdd/analise-dna/design.md` § Riscos (🔴); `confidence-report.md` § Lacunas Pendentes (analise-dna)
- **Tipo de ambiguidade**: 🔴 GAP de **verificabilidade** — não de regra
- **Descrição**: As regras A/B/C/D são congeladas e definitivas (Pergunta 1), mas `design.md` § Riscos registra: *"Complexidade das regras A/B/C/D — difícil de validar sem dados reais/amostra."* O `confidence-report.md` confirma: *"sem base de teste"*. Ou seja: existe uma regra que **deve** ser preservada e **não existe oráculo** para provar que foi preservada. Os 47 testes de `tests/` testam a *reconstrução*, não o legado.
- **Opções**:
  1. **Aceitar paridade estrutural**: transcrever as regras do código do legado com revisão linha-a-linha e considerar isso suficiente. Rápido, sem oráculo executável.
  2. **Construir oráculo pelo legado (recomendado)**: executar o `app.py` original contra fixtures sintéticos de GEDCOM/CSV (já existem em `tests/fixtures/`) e congelar as **saídas** como golden files. Passa a existir prova executável de paridade. Requer rodar o legado — que é somente leitura e não o modifica.
  3. **Tratar como risco aceito e seguir sem oráculo**: registrar no `risk_register.md` que a fidelidade do núcleo mais complexo do sistema não é verificável.
- **Recomendação do Curator**: **Opção 2**. O brief declara explicitamente *"Paridade de matching ≥ 100% nos casos de teste"* como métrica primária. Sem oráculo derivado do legado, essa métrica é **inverificável** — os 47 testes existentes validam a reconstrução contra si mesma. Os fixtures sintéticos já existem, o custo é baixo e o legado está disponível localmente. Esta é a decisão de maior alavancagem de todo o pipeline.
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - construir oraculo a partir do proprio legado, executando `app.py` contra fixtures sinteticos e congelando as saidas como golden files. Justificativa: o brief elege "paridade de matching >= 100% nos casos de teste" como metrica primaria; sem oraculo derivado do legado essa metrica e inverificavel, pois os 47 testes existentes validam a reconstrucao contra si mesma. O legado e apenas lido, nunca modificado.
### BR-HUMANA-007
- **Origem**: `_reversa_sdd/domain.md` § 4 (🔴); `architecture.md` §5 (dívidas #1, #3); brief § Restrições (LGPD/GDPR)
- **Tipo de ambiguidade**: 🔴 GAP de escopo regulatório — **não existe no legado**
- **Descrição**: O brief exige conformidade **LGPD/GDPR para dados genéticos** (consentimento, retenção/expurgo, criptografia, direito de exclusão). O legado **não possui nenhum** desses elementos — não há usuário, não há persistência, não há endpoint de exclusão, não há log de consentimento. Não há spec de origem para migrar: isto é **construção nova**, não curadoria. O Curator não pode decidir o conteúdo desses requisitos sem o usuário, e o Designer não deve inventá-los.
- **Opções**:
  1. **Escopo completo agora (recomendado pelo brief)**: consentimento explícito no cadastro, política de retenção com expurgo automático, criptografia em repouso/trânsito, endpoint de exclusão de conta e dados, minimização e log de auditoria de acesso.
  2. **Escopo mínimo viável agora, conformidade completa antes do go-live**: implementar criptografia e isolamento já (estruturais), deixar consentimento/retenção/expurgo para uma onda dedicada antes de qualquer usuário externo real.
  3. **Adiar toda a conformidade** para um `/reversa-forward` posterior.
- **Recomendação do Curator**: **Opção 2**. Criptografia e isolamento são estruturais — retrofitar depois é caro e arriscado. Consentimento, retenção e expurgo são fluxos de produto que dependem de decisões de negócio (qual base legal? qual prazo de retenção?) que **você ainda não declarou**. A opção 1 exige respostas que não existem; a opção 3 deixa dado genético desprotegido. ⚠️ Combinada com AMB-002 (usuários externos não ouvidos), esta é a lacuna de maior risco regulatório do projeto.
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - criptografia e isolamento ja (estruturais); consentimento, retencao e expurgo em onda dedicada antes de qualquer usuario externo real. Justificativa: retrofitar criptografia e isolamento e caro e arriscado; consentimento/retencao dependem de decisoes de negocio ainda nao declaradas (base legal, prazo de retencao).
### BR-HUMANA-008
- **Origem**: brief § Escopo (visualização mantida); `_reversa_sdd/inventory.md` §3; `busca-caminho/design.md` § Interface; `analise-dna/design.md` § passo 12
- **Tipo de ambiguidade**: ⚠️ AMBÍGUA — paridade de UX vs paridade de domínio
- **Descrição**: O legado gera **Mermaid no servidor** como string (`generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge`) e também uma página pyvis (`static/graph_path_search.html`). Com React, o grafo passa a ser renderizado no cliente. A dúvida: **o que exatamente precisa ser idêntico?** As funções Mermaid contêm decisões de negócio (ex.: `split_path_by_marriage` divide o caminho no 1º par de cônjuges adjacentes; âncoras `--- |Casamento| ---`; `are_spouses` verifica casamento) que determinam **como a relação é apresentada**. Se o cliente redesenhar o grafo livremente, essas regras de apresentação se perdem — mas exigir Mermaid idêntico no cliente é um objetivo ruim de engenharia.
- **Opções**:
  1. **Preservar a lógica, redesenhar a apresentação (recomendado)**: `split_path_by_marriage`, `are_spouses` e a identificação de cônjuges migram como **funções puras de domínio** que produzem uma estrutura de caminho tipada (ramos, MRCA, par de casamento); o React renderiza essa estrutura com a tecnologia que preferir. Nada de Mermaid no servidor.
  2. **Emitir Mermaid no servidor e renderizar no cliente**: paridade visual alta, mas mantém acoplamento a uma tecnologia de diagramação e não aproveita o SPA.
  3. **Substituir por biblioteca de grafo no cliente** (ex.: D3/vis.js) e **descartar** as regras de divisão por casamento.
- **Recomendação do Curator**: **Opção 1**. Ela separa corretamente *regra de negócio* (como o parentesco é decomposto — precisa de paridade) de *tecnologia de desenho* (como o grafo é pintado — livre). A opção 3 descartaria regras de negócio junto com a tecnologia, que é exatamente o que o `decision-rubric.md` proíbe: *"O que NUNCA descartar por paradigma: regras de negócio puras, cálculos, condições, derivações."*
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 1 - preservar a logica e redesenhar a apresentacao. `split_path_by_marriage`, `are_spouses` e a identificacao de conjuge migram como funcoes puras de dominio que produzem estrutura de caminho tipada; o React renderiza com a tecnologia que preferir, sem Mermaid no servidor. Justificativa: separa regra de negocio (precisa de paridade) de tecnologia de desenho (livre); descartar as funcoes junto com o Mermaid violaria o `decision-rubric.md`.
### BR-HUMANA-009
- **Origem**: `_reversa_sdd/analise-dna/requirements.md` § Riscos (🔴); `design.md` § Riscos (🟢); BR-MIGRAR-018; BR-DESCARTAR-006
- **Tipo de ambiguidade**: ⚠️ AMBÍGUA — trade-off explícito entre paridade e robustez
- **Descrição**: `design.md` § Riscos registra como 🟢 CONFIRMADO que a detecção de colunas depende de **ordem/posição** das colunas como heurística, o que *"pode variar entre exportadores"*. E `requirements.md` § Riscos registra 🔴 que a detecção de ID por regex `[A-Z]{2}\d{7}` tem *"cobertura entre exportadores não comprovada"* (`confidence-report.md`). Ou seja: existem dois pontos onde o legado é reconhecidamente frágil face a exportadores reais — e o brief declara compatibilidade com MyHeritage/FTDNA/GEDmatch como **inegociável**.
- **Opções**:
  1. **Preservar exatamente (paridade estrita)**: mesma heurística de posição, mesma regex. Paridade garantida; a fragilidade declarada no brief ("compatibilidade inegociável") permanece não resolvida.
  2. **Preservar por default + ampliar cobertura de forma aditiva (recomendado)**: manter a heurística atual como primeiro caminho e **acrescentar** reconhecimento de mais variações de cabeçalho e de formatos de ID como fallback *depois* de a heurística atual falhar. Aditivo: não altera nenhum resultado que hoje funciona; só passa a funcionar onde hoje falha.
  3. **Reescrever a detecção com parser robusto de cabeçalho**: melhor engenharia, mas pode alterar qual coluna é escolhida em CSVs ambíguos → quebra paridade.
- **Recomendação do Curator**: **Opção 2**. É a única que atende simultaneamente as duas restrições do brief: paridade de matching (nada que hoje funciona muda) **e** compatibilidade de exportadores (o que hoje falha passa a funcionar). A opção 1 deixa uma restrição inegociável sem solução; a opção 3 arrisca a métrica primária. ⚠️ Exige que o Inspector prove que a extensão é **aditiva** — nenhum caso de teste existente pode mudar de resultado.
- **Status**: RESOLVIDA

- **Decisão (2026-09-28T02:56:00Z)**: Aprovada a recomendacao do Curator. Decisor: Adriano. Quando: 2026-09-28T02:56:00Z. Escolha: opcao 2 - preservar a heuristica atual como primeiro caminho e acrescentar reconhecimento de mais variacoes de cabecalho e formatos de ID como fallback aditivo. Justificativa: unica opcao que atende paridade (nada que hoje funciona muda) e compatibilidade de exportadores (o que hoje falha passa a funcionar). Exige que o Inspector prove que a extensao e aditiva.
## Notas

- **Correção factual registrada**: o log de ambiguidades (AMB-004) afirmava que as respostas de `questions.md` estavam "apenas em prosa no `reconstruction-plan.md`". **Está errado** — as 4 respostas estão dentro do próprio `questions.md`, com marcação `**Resposta:**`. A conclusão (são comportamento congelado → MIGRAR) permanece; AMB-004 foi corrigido.
- **8 itens DECISÃO HUMANA foi um número alto — e esperado.** O legado tem 17 lacunas 🔴 registradas (`confidence-report.md`), e a migração muda o contexto de uso (local single-user → SaaS público com dado sensível), o que **reativa** decisões que estavam fechadas no contexto antigo. BR-HUMANA-001 e BR-HUMANA-003 são exatamente desse tipo: respostas válidas para "uso local" que precisavam ser revalidadas. **Todas foram resolvidas em 2026-09-28T02:56:00Z.**
- **Nenhuma regra de negócio pura foi descartada.** Os 7 descartes são: estado global/re-parse (2), armazenamento de arquivo por nome do cliente (1), transporte HTTP/SSR (1), geração de diagrama no servidor (1), uma limitação de segurança reaberta e descartada pelo usuário (1, BR-DESCARTAR-006) e um segredo hardcoded (1, BR-DESCARTAR-007). Nenhum cálculo, condição ou derivação foi perdido — conforme a proibição explícita do `decision-rubric.md`.
- **Duas regras MIGRAR carregam aviso de que o dado necessário não está nas specs**: BR-MIGRAR-011 (lista de primeiros nomes genéricos) e BR-MIGRAR-012 (tabela de equivalentes de grafia). Elas só existem no código `app.py`. **O agente de codificação deve transcrevê-las do legado, nunca reconstruí-las de memória** — é o modo mais provável de quebrar paridade silenciosamente.
- **Ponto de maior alavancagem identificado**: BR-HUMANA-006. Sem oráculo derivado do próprio legado, a métrica primária do brief ("paridade de matching ≥ 100%") é inverificável, porque os 47 testes existentes validam a reconstrução contra si mesma.
- Itens replicados em `ambiguity_log.md`: BR-HUMANA-001 a BR-HUMANA-009 → AMB-006 a AMB-014. **Todos RESOLVIDOS** em 2026-09-28T02:56:00Z; nenhum PENDENTE. BR-HUMANA-002 foi reclassificada como descarte (`discard_log.md` BR-DESCARTAR-007).

---
*Gerado pelo Reversa-Curator em 2026-09-28.*
