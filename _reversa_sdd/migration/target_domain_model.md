---
schemaVersion: 1
generatedAt: 2026-09-28T03:12:20Z
reversa:
  version: "1.2.58"
kind: target_domain_model
producedBy: designer
hash: "sha256:24a92255e20db7b1a04d2924dbbbf0ba6684723fe4257d347437bd58faed71f8"
---

# Target Domain Model

> Modelo de domínio do sistema novo. Rastreabilidade explícita para o legado (em `_reversa_sdd/domain.md` ou equivalente).
> Paradigma alvo: **OO com DI sobre funções puras**. Aggregates existem **apenas onde há ciclo de vida persistido** (árvore, análise, conta). Os **cálculos** são funções puras, não objetos com estado.

## Aggregates

### AGG-01: GedcomTree
- **Aggregate root**: `GedcomTree` (identificada por `tree_id`)
- **Invariantes**:
  - **I-1 — Propriedade**: toda árvore tem exatamente um `owner_id`. Não existe árvore sem dono. *(novo; mitiga RISK-005)*
  - **I-2 — Integridade referencial GEDCOM**: toda referência em `HUSB`, `WIFE`, `CHIL`, `FAMC` e `FAMS` aponta para um `xref_id` existente **dentro da mesma árvore**. Um GEDCOM com referência pendente é rejeitado no parse, não silenciosamente aceito.
  - **I-3 — Unicidade de xref**: os `xref_id` de pessoas e de famílias são únicos dentro da árvore.
  - **I-4 — Imutabilidade após o parse**: uma vez construída, a árvore não é mutada. Não há "recarregar" sobre a mesma instância — o legado sobrescrevia globais a cada POST (`upload-gedcom/design.md` § Estado Interno); aqui uma árvore é substituída por outra, nunca mutada in-place.
  - **I-5 — Ordem de inserção preservada**: as arestas do grafo de relacionamento são inseridas na ordem derivada da ordem dos registros no arquivo. *(preserva BR-MIGRAR-024: `nx.shortest_path` com caminhos de mesmo comprimento retorna aquele determinado pela ordem de inserção)*
  - **I-6 — Nome de exibição sempre presente, podendo ser VAZIO**: toda pessoa tem um campo de nome de exibição. Quando o objeto de nome é **ausente**, o literal é **"Sem Nome"**; quando o objeto existe mas seu formato resulta vazio, o valor é **string vazia** (`''`). *(BR-MIGRAR-003 — comportamento congelado; ver correção factual: 318 nomes vazios reais contra 0 ocorrências do literal)*
- **Comandos aceitos**: `ImportGedcom(owner_id, bytes, original_filename)`, `ReplaceTree(tree_id, owner_id, bytes)`, `DeleteTree(tree_id, owner_id)`
- **Eventos publicados**: **nenhum** (AD-05 — o paradigma não é event-driven; não há consumidor)
- **Origem no legado**: `_reversa_sdd/upload-gedcom/design.md` (§ Detalhe do fluxo de parsing, § Detalhe do grafo, § Estado Interno); `code-analysis.md` §3 (`load_gedcom_and_build_graph`, `build_graph_from_parser`); globais `people`, `families`, `graph`, `child_to_family` — **descartados** conforme `discard_log.md` BR-DESCARTAR-001.

### AGG-02: DnaAnalysis
- **Aggregate root**: `DnaAnalysis` (identificada por `analysis_id`)
- **Invariantes**:
  - **I-1 — Propriedade**: toda análise tem `owner_id`, **igual ao `owner_id` da árvore analisada**. Uma análise não pode referenciar árvore de outro dono. *(novo; mitiga RISK-005)*
  - **I-2 — Raiz resolvida**: uma análise só existe concluída se a pessoa-raiz foi resolvida na árvore. `root_name` não localizado produz erro de domínio, não uma análise vazia. *(BR-MIGRAR-032, BR-MIGRAR-033)*
  - **I-3 — Rastreabilidade da origem**: a análise referencia a árvore (`tree_id`) e o arquivo de matches (`match_file_ref`) que a originaram. Resultados não existem soltos.
  - **I-4 — Completude da auditoria**: todo match lido do CSV aparece **exatamente uma vez** no resultado — ou em `accepted_matches`, ou em `skipped_matches` com motivo tipado. Não há descarte silencioso. *(BR-MIGRAR-029, BR-MIGRAR-030 — RF-07)*
  - **I-5 — Ordenação estável**: `accepted_matches` é ordenado por cM decrescente; empates mantêm ordem determinística e reproduzível. *(BR-MIGRAR-031)*
  - **I-6 — cM é valor calculado e persistido**: o `total_cm` de cada match é o resultado da agregação do núcleo, persistido como está. O banco não recalcula. *(AD-03; BR-MIGRAR-016)*
- **Comandos aceitos**: `RunDnaAnalysis(owner_id, tree_id, match_file_ref, root_name)`, `DeleteAnalysis(analysis_id, owner_id)`
- **Eventos publicados**: **nenhum** (AD-05)
- **Origem no legado**: `_reversa_sdd/analise-dna/design.md` (§ Fluxo Principal, § Estado Interno); `code-analysis.md` §3 (`process_dna_action`). A entidade `DNA_MATCH` do ERD legado (`architecture.md` §3) é **absorvida** como `MatchResult` dentro deste aggregate — ela era "derivada do CSV agregado em memória, s/ persistência".

### AGG-03: AppUser
- **Aggregate root**: `AppUser` (identificada por `user_id`)
- **Invariantes**:
  - **I-1 — Identidade única**: e-mail (ou identificador de login) único no sistema.
  - **I-2 — Consentimento rastreável**: quando exigido (Onda 5), o consentimento para tratamento de dado genético é registrado com timestamp, versão do texto e finalidade. Sem consentimento registrado, nenhuma árvore ou análise pode ser criada.
  - **I-3 — Exclusão exequível**: a exclusão do usuário remove ou anonimiza **todas** as suas árvores, arquivos e análises. Não pode restar dado genético órfão. *(BR-HUMANA-007)*
- **Comandos aceitos**: `RegisterUser`, `RecordConsent(user_id, purpose, text_version)`, `RequestDeletion(user_id)`
- **Eventos publicados**: **nenhum** (AD-05)
- **Origem no legado**: **nova** — `domain.md` §4 registra a ausência como lacuna: *"Sem autenticação/autorização: sistema não possui RBAC — qualquer acesso via web possui todas funcionalidades."*

> **Não existe aggregate para "Match", "Path" ou "Score".** Justificativa: são **cálculo puro** sem ciclo de vida próprio. `MatchResult` é entidade interna de `DnaAnalysis`; o caminho é um value object produzido a cada consulta. Reificá-los como aggregates criaria objetos com estado sobre algoritmos congelados — exatamente o risco que o `paradigm_decision.md` § Alternativas registrou ao rejeitar a opção transformacional.

## Entidades

| Entidade | Aggregate dono | Atributos principais | Origem no legado |
|---|---|---|---|
| `Person` | AGG-01 GedcomTree | `xref_id`, `name` (exibição: "Sem Nome" se o nome for ausente, `''` se o formato for vazio), `given_name`, `surnames`, `suffixes`, `famc` (família como filho), `fams` (famílias como cônjuge) | `code-analysis.md` §5 (Person/INDI); `upload-gedcom/design.md` § Estado Interno (`people`) |
| `Family` | AGG-01 GedcomTree | `xref_id`, `husb`, `wife`, `chil[]` | `code-analysis.md` §5 (Family/FAM); `upload-gedcom/design.md` § Estado Interno (`families`) |
| `MatchResult` | AGG-02 DnaAnalysis | `group_key`, `matched_name` (original do CSV), `total_cm`, `matched_person_xref` (da árvore), `relationship_label`, `path` (value object), `accepted` | `architecture.md` §3 (DNA_MATCH); `code-analysis.md` §5 (DnaMatchRecord) |
| `SkippedMatch` | AGG-02 DnaAnalysis | `group_key`, `matched_name`, `total_cm`, `reason_code` (tipado), `reason_detail` | `analise-dna/requirements.md` RF-07; `analise-dna/design.md` § Fluxos Alternativos (`skipped_matches`) |
| `UploadedFile` | AGG-01 / AGG-02 (por uso) | `file_ref` (chave gerada pelo servidor), `original_filename` (**metadado**), `owner_id`, `content_type`, `size_bytes`, `checksum` | **novo** — substitui `uploads/` com nome do cliente (`discard_log.md` BR-DESCARTAR-003) |

## Value objects

| Value object | Atributos | Validações | Origem |
|---|---|---|---|
| `XrefId` | `value` (formato `@I0001@` / `@F1@`) | Não vazio; preserva o formato GEDCOM literal | `domain.md` §1 (INDI/FAM) |
| `DisplayName` | `value` | Pode ser **string vazia**; literal **"Sem Nome"** apenas quando o objeto de nome é ausente | `upload-gedcom/requirements.md` § Regras ⚠️ **corrigido** contra o oráculo (BR-MIGRAR-003) |
| `NormalizedName` | `value` | Resultado de NFKD + remoção de acentos + minúsculas | `analise-dna/design.md` § Interface (`norm_name`) (BR-MIGRAR-007) |
| `GroupKey` | `value` | Composição de nome normalizado + ID/email; ID reconhecido por regex `[A-Z]{2}\d{7}` | BR-MIGRAR-016, BR-MIGRAR-019 |
| `Centimorgans` | `value` (decimal) | ≥ 0; **não recalculado pela persistência** (AD-03) | `domain.md` §2.1 (cM) |
| `RelationshipLabel` | `value` (**anulável**) | Uma das 9 faixas de relação; **"Relação distante ou indeterminada"** quando cM > 0 não cai em nenhuma faixa; **ausente/nulo** quando cM ≤ 0 ou não numérico | `domain.md` §2.1; BR-MIGRAR-020, BR-MIGRAR-021 ⚠️ **corrigido por verificação contra o oráculo** — ver BR-MIGRAR-021 § Correção factual |
| `PathNode` | `person_xref`, `role` (ancestral / descendente / afinidade) | Deve referenciar pessoa da árvore | BR-HUMANA-008 |
| `KinshipPath` | `ascending[]`, `descending[]`, `mrca_xref`, `connection_type` (direta/indireta), `affinity_pair` (par de cônjuges, quando indireta) | Se `connection_type = direta`, `mrca_xref` obrigatório; se `indireta`, `affinity_pair` obrigatório | **novo** — estrutura tipada que substitui a emissão de Mermaid no servidor (AD-04) |
| `MatchSkippedReason` | `code` (enum), `detail` | Vocabulário fechado de motivos | BR-MIGRAR-029, BR-MIGRAR-030 |
| `OwnerId` | `value` | Obrigatório em toda operação de leitura/escrita de árvore ou análise | **novo** (AD-02, RISK-005) |
| `ConsentRecord` | `purpose`, `text_version`, `granted_at` | Obrigatório antes de persistir dado genético (a partir da Onda 5) | **novo** (BR-HUMANA-007) |

## Eventos de domínio

> ⚠️ **Seção deliberadamente vazia.** O paradigma alvo é `OO com DI sobre funções puras`, **não** event-driven — o catálogo do Designer exige eventos apenas para event-driven/híbrido-eventos, e o `paradigm_decision.md` classificou o gap como `procedural → OO com DI`. O brief não define mensageria. Ver AD-05 em `target_architecture.md`.

| Evento | Publicado por | Consumido por | Schema (resumido) |
|---|---|---|---|
| _(nenhum)_ | — | — | — |

## Funções puras do núcleo (não são objetos — são o domínio de cálculo)

> Registradas aqui porque **são** o domínio, ainda que não sejam aggregates. Todas vivem em `core/`, sem I/O e sem framework (AD-01). Cada uma mapeia regras congeladas.

| Função / módulo | Responsabilidade | Regras | Arquivo alvo |
|---|---|---|---|
| `strip_bad_utf`, `demojibake` | Correção de encoding corrompido; re-encoding Latin-1→UTF-8 | BR-MIGRAR-006 | `core/mojibake.py` |
| `norm_name`, `split_name_pt`, `surnames_set` | Normalização NFKD, decomposição pt-BR, conjunto de sobrenomes | BR-MIGRAR-007 | `core/normalization.py` |
| `apply_spelling_equivalents` | Equivalentes de grafia (`netto→neto`, `gouvea→gouveia`) e prefixos de sobrenome (mín. 3) | BR-MIGRAR-012 | `core/normalization.py` |
| `build_name_index`, `build_surname_index`, `build_prefix_index` | Índices para o pool de candidatos (exact → sobrenome → prefixo) | BR-MIGRAR-008 | `core/matching.py` |
| `fuzzy_score` | `0.55×token_sort + 0.25×partial + 0.20×given + InterBonus` | BR-MIGRAR-009 | `core/matching.py` |
| `reject_false_positive` | Interseção 0 sem sufixo salvador → rejeita | BR-MIGRAR-010 | `core/matching.py` |
| `adaptive_min_intersection` | Primeiro nome genérico + 2 sobrenomes → exige 2 em comum | BR-MIGRAR-011 | `core/matching.py` |
| `accept_match` (regras A/B/C/D) | Árvore de decisão de aceitação, ordem preservada | BR-MIGRAR-013 | `core/matching.py` |
| `jaccard_threshold` | 0.5 default; 0.33 se cM ≥ 150 e não-genérico | BR-MIGRAR-014 | `core/matching.py` |
| `break_tie` | Interseção → given → score, ordenação estável | BR-MIGRAR-015 | `core/matching.py` |
| `relationship_by_cm` | 9 faixas, **ordem de avaliação preservada** (faixas se sobrepõem) | BR-MIGRAR-020, BR-MIGRAR-021 | `core/relationship.py` |
| `parse_gedcom` | bytes → `GedcomTree` (função pura) | BR-MIGRAR-001, BR-MIGRAR-002, BR-MIGRAR-003 | `core/parser.py` |
| `find_ancestral_path` | BFS bidirecional por pais, `max_depth=20` | BR-MIGRAR-022, BR-MIGRAR-023 | `core/pathfinding.py` |
| `find_indirect_path` | `shortest_path` + compressão de famílias, `max_hops=40` medido antes da compressão | BR-MIGRAR-024, BR-MIGRAR-025 | `core/pathfinding.py` |
| `find_person_by_name` | Exact match e depois substring; **ordem da lista significativa** | BR-MIGRAR-027 | `core/tree.py` |
| `split_path_by_marriage`, `are_spouses` | Decomposição do caminho no **1º par de cônjuges adjacentes** | BR-HUMANA-008 | `core/decomposition.py` |
| `read_dna_csv` | Fallback UTF-8→Latin-1; detecção tolerante de colunas | BR-MIGRAR-017, BR-MIGRAR-018 | `core/dna.py` |
| `build_group_key`, `aggregate_segments` | Agrupamento por `_group_key` e soma de cM **na ordem de origem** | BR-MIGRAR-016 | `core/dna.py` |

## Regras de domínio

> Mapeamento de **todas** as 34 regras MIGRAR de `target_business_rules.md` para o local onde vivem no domínio novo.

| Regra (ID) | Local no domínio novo | Origem (`target_business_rules.md`) |
|---|---|---|
| BR-MIGRAR-001 | `core/parser.py` — `parse_gedcom` (AGG-01) | BR-MIGRAR-001 |
| BR-MIGRAR-002 | `core/tree.py` — `GedcomTree` (I-2, I-3, I-5) | BR-MIGRAR-002 |
| BR-MIGRAR-003 | VO `DisplayName` — pode ser vazio; literal "Sem Nome" só se o nome for ausente (I-6) | BR-MIGRAR-003 |
| BR-MIGRAR-004 | `core/tree.py` — `ordered_display_names()` (ordenação antes do payload) | BR-MIGRAR-004 |
| BR-MIGRAR-005 | `api/schemas` + exceções `MissingGedcomFile`, `EmptyFilename` | BR-MIGRAR-005 |
| BR-MIGRAR-006 | `core/mojibake.py` — `strip_bad_utf`, `demojibake` | BR-MIGRAR-006 |
| BR-MIGRAR-007 | `core/normalization.py` — `norm_name`, `split_name_pt`, `surnames_set` | BR-MIGRAR-007 |
| BR-MIGRAR-008 | `core/matching.py` — índices e pool de candidatos | BR-MIGRAR-008 |
| BR-MIGRAR-009 | `core/matching.py` — `fuzzy_score` (+ `core/constants.py`) | BR-MIGRAR-009 |
| BR-MIGRAR-010 | `core/matching.py` — `reject_false_positive` | BR-MIGRAR-010 |
| BR-MIGRAR-011 | `core/matching.py` — `adaptive_min_intersection` ⚠️ lista transcrita de `app.py` | BR-MIGRAR-011 |
| BR-MIGRAR-012 | `core/normalization.py` — `apply_spelling_equivalents` ⚠️ tabela transcrita de `app.py` | BR-MIGRAR-012 |
| BR-MIGRAR-013 | `core/matching.py` — `accept_match` (A/B/C/D), ordem de avaliação preservada | BR-MIGRAR-013 |
| BR-MIGRAR-014 | `core/matching.py` — `jaccard_threshold` | BR-MIGRAR-014 |
| BR-MIGRAR-015 | `core/matching.py` — `break_tie` (ordenação estável) | BR-MIGRAR-015 |
| BR-MIGRAR-016 | `core/dna.py` — `build_group_key`, `aggregate_segments`; VO `Centimorgans`; I-6 de AGG-02 | BR-MIGRAR-016 |
| BR-MIGRAR-017 | `core/dna.py` — `read_dna_csv` (estratégia explícita de codec) | BR-MIGRAR-017 |
| BR-MIGRAR-018 | `core/dna.py` — resolução de cabeçalho (com extensão aditiva — BR-HUMANA-009) | BR-MIGRAR-018 |
| BR-MIGRAR-019 | VO `GroupKey` — regex `[A-Z]{2}\d{7}` | BR-MIGRAR-019 |
| BR-MIGRAR-020 | `core/relationship.py` — `relationship_by_cm` (9 faixas, ordem preservada) | BR-MIGRAR-020 |
| BR-MIGRAR-021 | `core/relationship.py` — VO `RelationshipLabel` (literal indeterminada) | BR-MIGRAR-021 |
| BR-MIGRAR-022 | `core/pathfinding.py` — `find_ancestral_path` (BUSCA DIRETA ANTES DA INDIRETA) | BR-MIGRAR-022 |
| BR-MIGRAR-023 | `core/pathfinding.py` + `core/constants.py` — `MAX_ANCESTOR_DEPTH = 20` | BR-MIGRAR-023 |
| BR-MIGRAR-024 | `core/pathfinding.py` — `find_indirect_path`; `GedcomTree` I-5 (ordem das arestas) | BR-MIGRAR-024 |
| BR-MIGRAR-025 | `core/pathfinding.py` + `core/constants.py` — `MAX_INDIRECT_HOPS = 40` (medido **antes** da compressão) | BR-MIGRAR-025 |
| BR-MIGRAR-026 | `application/*` — política de 1º ID (default) + sinalização de ambiguidade no payload | BR-MIGRAR-026 / BR-HUMANA-003 |
| BR-MIGRAR-027 | `core/tree.py` — `find_person_by_name` (ordem da lista significativa) | BR-MIGRAR-027 |
| BR-MIGRAR-028 | `api/errors.py` + catálogo i18n — literais das mensagens preservados | BR-MIGRAR-028 |
| BR-MIGRAR-029 | AGG-02 I-4; entidade `SkippedMatch` (motivo tipado) | BR-MIGRAR-029 |
| BR-MIGRAR-030 | AGG-02 I-4; entidade `SkippedMatch` | BR-MIGRAR-030 |
| BR-MIGRAR-031 | AGG-02 I-5 — ordenação por cM decrescente, com desempate estável | BR-MIGRAR-031 |
| BR-MIGRAR-032 | AGG-02 I-2; `application/analyze_dna.py` — resolução da raiz (1º ID) | BR-MIGRAR-032 |
| BR-MIGRAR-033 | `application/*` — pré-condições reinterpretadas: `tree_id` do usuário em vez de "GEDCOM carregado" global ⚠️ **ponto de atenção** | BR-MIGRAR-033 |
| BR-MIGRAR-034 | `api/errors.py` — garantia de não quebrar + distinção tipada de erros | BR-MIGRAR-034 |
| BR-HUMANA-008 (migra) | `core/decomposition.py` — `split_path_by_marriage`, `are_spouses` | BR-HUMANA-008 |
| BR-HUMANA-009 (aditivo) | `core/dna.py` — extensão de cabeçalhos/formatos de ID como fallback **após** a heurística atual | BR-HUMANA-009 |

> **Cobertura**: as 34 regras MIGRAR estão mapeadas, mais os 2 itens de decisão humana que resultaram em migração (BR-HUMANA-008 e o caráter aditivo de BR-HUMANA-009). Nenhuma regra MIGRAR ficou órfã.

## Rastreabilidade para o legado

| Elemento novo | Origem no legado | Tipo de mapeamento |
|---|---|---|
| AGG-01 `GedcomTree` | globais `people`, `families`, `graph`, `child_to_family` + `load_gedcom_and_build_graph` + `build_graph_from_parser` | **dividido** (parse → `core/parser.py`; modelo → aggregate; persistência → `ports/`) |
| AGG-02 `DnaAnalysis` | bloco `dna_analysis` de `app.py` + entidade `DNA_MATCH` do ERD | **dividido** (leitura/agregação → `core/dna`; pontuação → `core/matching`; orquestração → `application`) |
| AGG-03 `AppUser` | — | **novo** (`domain.md` §4: ausência de autenticação) |
| `Person`, `Family` | `Person`/`INDI` e `Family`/`FAM` de `code-analysis.md` §5 | **preservado** (mesma semântica, agora com invariantes) |
| `MatchResult` | `DnaMatchRecord` (`_group_key`, `cM`, `matched_name`) | **preservado e estendido** (ganha `path`, `relationship_label`, `accepted`) |
| `SkippedMatch` | lista `skipped_matches` (string livre de motivo) | **fundido/transformado** (motivo vira `MatchSkippedReason` tipado — BR-MIGRAR-029) |
| `KinshipPath` | `generate_mermaid_graph` + `generate_mermaid_graph_indirect_bridge` + `split_path_by_marriage` | **dividido** (decomposição → VO; emissão de diagrama → descartada, `discard_log.md` BR-DESCARTAR-005) |
| `Centimorgans` | coluna de cM agregada no DataFrame | **preservado** (a agregação muda de container, não de semântica) |
| `ConsentRecord` | — | **novo** (BR-HUMANA-007) |
| `UploadedFile` | arquivo em `uploads/` com nome do cliente | **dividido/transformado** (`discard_log.md` BR-DESCARTAR-003) |
| Funções de `core/matching.py` | bloco de scoring dentro de `process_dna_action` (`app.py:667-793`) | **dividido** (extraído do controller — implicação 3 do `paradigm_decision.md`) |
| Funções de `core/normalization.py` | `norm_name`, `split_name_pt`, `surnames_set`, `demojibake`, `strip_bad_utf` | **preservado** (único mapeamento sem divisão) |
| Funções de `core/pathfinding.py` | `find_ancestral_path` (usado por **2** units), `find_indirect_path` | **fundido** (duas units → uma capacidade de núcleo) |
| `find_person_by_name` em `core/tree.py` | `find_person_by_name` | **movido** (era do domínio de caminho; passa a ser do índice da árvore) |
| `core/constants.py` | limiares literais espalhados em `app.py` | **novo** (extração deliberada; defesa contra RISK-003) |

## Notas

- **⚠️ Ponto de atenção explícito para o agente de codificação (BR-MIGRAR-033)**: no legado, "GEDCOM carregado" significava "existe no estado global do processo" — uma condição implícita que persistia entre requisições. No alvo, a mesma pré-condição passa a significar "existe uma árvore **persistida** pertencente a **este** usuário" (ou um upload na mesma requisição). A **mensagem** e o comportamento visível ao usuário devem ser preservados (BR-MIGRAR-028), mas o **mecanismo** muda. Esta é a tradução semântica mais delicada da Fase 2 e foi sinalizada em AMB-009.
- **Dois itens dependem de transcrição literal de `app.py` e não podem ser reconstruídos a partir das specs** (RISK-003): a lista de primeiros nomes genéricos (BR-MIGRAR-011) e a tabela de equivalentes de grafia + sobrenomes comuns + sufixos salvadores (BR-MIGRAR-012). Devem ser **extraídos mecanicamente** do legado, com referência de linha.
- **A ordem de avaliação das 9 faixas de cM importa** (BR-MIGRAR-020): as faixas **se sobrepõem** (ex.: 46–515 e 200–850 contêm 200–515). A primeira faixa que casa decide. Reordenar a tabela — ou convertê-la em busca binária ou em intervalo de banco — muda o resultado. Manter avaliação sequencial na ordem do legado.
- **A lista de motivos de `SkippedMatch` deve ser fechada (enum)**, não string livre como no legado. Isso transforma a auditoria visual (`skipped_matches`) em auditoria programática e é o que permite asserção nos `parity_tests/`. ⚠️ Ao mesmo tempo, o **texto** apresentado ao usuário deve continuar correspondendo ao que o legado mostrava (BR-MIGRAR-028), então cada código carrega sua mensagem.
- **`MatchResult.matched_person_xref` pode ser nulo?** Não. Pela I-4 de AGG-02 e pelo fluxo do legado (`analise-dna/design.md` § Fluxos Alternativos), um match sem candidato no GEDCOM **não** vira `MatchResult` — vira `SkippedMatch`. Um `MatchResult` sempre tem pessoa correspondente na árvore.
- **Nenhum evento de domínio foi definido** (AD-05). Ausência consciente, não omissão.
