---
schemaVersion: 1
generatedAt: 2026-09-28T03:12:20Z
reversa:
  version: "1.2.58"
kind: target_data_model
producedBy: designer
hash: "sha256:73a186dba506dc291099b867f7a4d38f4c8ebd8653534199aa0e84e1f2c6134f"
---

# Target Data Model

> Modelo de dados do sistema novo. Schema, relacionamentos e restrições.

## Visão geral

O sistema novo usa **PostgreSQL** como único armazenamento relacional (OLTP), complementado por **object storage** para os arquivos brutos enviados (`.ged`, `.csv`). Não há data warehouse, cache externo, event store nem tabela de outbox — o paradigma é `OO com DI sobre funções puras` com processamento síncrono (AD-05), não event-driven.

**Este modelo é integralmente novo.** O legado **não tem banco de dados**: `architecture.md` §1 e §5 e `inventory.md` §5 registram que todo o estado era mantido em memória (dicionários + grafo `networkx`), com armazenamento temporário apenas dos arquivos em `uploads/`. Consequentemente, **não há schema legado, não há `data-dictionary.md` e não há conversão de dados** — ver `data_migration_plan.md`.

Duas restrições estruturais herdadas do processo de decisão moldam todo o schema:
1. **`owner_id` é invariante, não filtro** (AD-02, RISK-005): está em `NOT NULL` e nas chaves de acesso de toda tabela que carrega dado genético.
2. **cM não é recalculado pelo banco** (AD-03, RISK-004): o valor agregado é calculado no núcleo puro e persistido já calculado. Nenhum `SUM` sobre `match_result` é autoridade.

Divisão por bounded context: `BC-01` (Identidade e Tenancy) possui `app_user`; `BC-02` (Árvore) possui `gedcom_tree`, `person`, `family`; `BC-03` (Análise de DNA) possui `dna_analysis`, `match_result`, `skipped_match`; `BC-05` (Conformidade) possui `consent_record` e `data_retention_policy`, e **atravessa** as demais via `owner_id`.

## Entidades de dados

| Entidade | Tabela | Aggregate dono | PK | Bounded context |
|---|---|---|---|---|
| Conta de usuário | `app_user` | AGG-03 | `user_id` | BC-01 |
| Consentimento | `consent_record` | AGG-03 | `consent_id` | BC-05 |
| Política de retenção | `data_retention_policy` | AGG-03 | `policy_id` | BC-05 |
| Árvore GEDCOM | `gedcom_tree` | AGG-01 | `tree_id` | BC-02 |
| Arquivo enviado | `uploaded_file` | AGG-01 / AGG-02 | `file_ref` | BC-02 / BC-03 |
| Pessoa (INDI) | `person` | AGG-01 | (`tree_id`, `xref_id`) | BC-02 |
| Família (FAM) | `family` | AGG-01 | (`tree_id`, `xref_id`) | BC-02 |
| Vínculo filho→família | `person_famc` | AGG-01 | (`tree_id`, `person_xref`, `family_xref`) | BC-02 |
| Vínculo cônjuge→família | `person_fams` | AGG-01 | (`tree_id`, `person_xref`, `family_xref`) | BC-02 |
| Análise de DNA | `dna_analysis` | AGG-02 | `analysis_id` | BC-03 |
| Match aceito | `match_result` | AGG-02 | `match_id` | BC-03 |
| Match descartado | `skipped_match` | AGG-02 | `skipped_id` | BC-03 |
| Nó do caminho | `match_path_node` | AGG-02 | (`match_id`, `ordinal`) | BC-03 |
| Registro de acesso | `access_audit` | AGG-03 | `audit_id` | BC-05 |

## Schema (DDL)

```sql
-- ============================================================
-- BC-01: Identidade e Tenancy
-- ============================================================

CREATE TABLE app_user (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT NOT NULL,
    display_name    TEXT,
    password_hash   TEXT NOT NULL,          -- nunca senha em claro
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletion_requested_at TIMESTAMPTZ,      -- direito de exclusao (BR-HUMANA-007)
    CONSTRAINT uq_app_user_email UNIQUE (email)
);

-- ============================================================
-- BC-05: Conformidade e Ciclo de Vida do Dado
-- ============================================================

CREATE TABLE consent_record (
    consent_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    purpose         TEXT NOT NULL,          -- finalidade do tratamento
    text_version    TEXT NOT NULL,          -- versao do texto aceito (auditoria)
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ,
    CONSTRAINT ck_consent_revoked_after_granted
        CHECK (revoked_at IS NULL OR revoked_at >= granted_at)
);

CREATE TABLE data_retention_policy (
    policy_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES app_user(user_id) ON DELETE CASCADE,  -- NULL = politica global
    data_kind       TEXT NOT NULL,          -- 'raw_upload' | 'tree' | 'analysis'
    retention_days  INTEGER NOT NULL,
    purge_enabled   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_retention_days_positive CHECK (retention_days > 0)
);

-- Trilha de auditoria de acesso a dado genetico
CREATE TABLE access_audit (
    audit_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES app_user(user_id) ON DELETE SET NULL,
    resource_kind   TEXT NOT NULL,          -- 'gedcom_tree' | 'dna_analysis' | 'uploaded_file'
    resource_id     TEXT NOT NULL,
    action          TEXT NOT NULL,          -- 'read' | 'create' | 'delete' | 'export'
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- BC-02: Arvore Genealogica (GEDCOM)
-- ============================================================

CREATE TABLE uploaded_file (
    file_ref         UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- chave GERADA PELO SERVIDOR
    owner_id         UUID NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,        -- apenas METADADO (nunca caminho)
    content_type     TEXT NOT NULL,
    size_bytes       BIGINT NOT NULL,
    checksum_sha256  TEXT NOT NULL,
    storage_key      TEXT NOT NULL,         -- chave no object storage, nao derivada do cliente
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    purge_after      TIMESTAMPTZ,           -- retencao (Onda 5)
    CONSTRAINT ck_uploaded_file_size_positive CHECK (size_bytes > 0)
);

CREATE TABLE gedcom_tree (
    tree_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id         UUID NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    source_file_ref  UUID NOT NULL REFERENCES uploaded_file(file_ref) ON DELETE RESTRICT,
    display_name     TEXT,
    person_count     INTEGER NOT NULL DEFAULT 0,
    family_count     INTEGER NOT NULL DEFAULT 0,
    -- ordem de insercao das arestas DO ARQUIVO (invariante I-5 de AGG-01):
    -- preservada para determinismo de shortest_path (BR-MIGRAR-024)
    graph_edge_order_version INTEGER NOT NULL DEFAULT 1,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Leitura SEMPRE escopada por owner_id (AD-02 / RISK-005)
CREATE INDEX ix_gedcom_tree_owner ON gedcom_tree (owner_id, created_at DESC);

CREATE TABLE person (
    tree_id      UUID NOT NULL REFERENCES gedcom_tree(tree_id) ON DELETE CASCADE,
    xref_id      TEXT NOT NULL,             -- formato GEDCOM: @I0001@
    display_name TEXT NOT NULL,             -- '' (string vazia) e valor LEGITIMO e ocorre em dado real;
                                            -- literal 'Sem Nome' apenas se o objeto de nome for ausente
                                            -- (BR-MIGRAR-003, corrigido contra o oraculo)
    given_name   TEXT,
    surnames     TEXT[],
    suffixes     TEXT[],
    -- posicao de leitura no arquivo: preserva a ORDEM da lista de find_person_by_name
    -- (BR-MIGRAR-027) e o desempate estavel de resultados
    source_ordinal INTEGER NOT NULL,
    PRIMARY KEY (tree_id, xref_id)
);

CREATE INDEX ix_person_display_name ON person (tree_id, display_name);
CREATE INDEX ix_person_source_ordinal ON person (tree_id, source_ordinal);

CREATE TABLE family (
    tree_id  UUID NOT NULL REFERENCES gedcom_tree(tree_id) ON DELETE CASCADE,
    xref_id  TEXT NOT NULL,                 -- formato GEDCOM: @F1@
    husb     TEXT,
    wife     TEXT,
    source_ordinal INTEGER NOT NULL,
    PRIMARY KEY (tree_id, xref_id),
    CONSTRAINT fk_family_husb FOREIGN KEY (tree_id, husb)
        REFERENCES person(tree_id, xref_id) ON DELETE SET NULL,
    CONSTRAINT fk_family_wife FOREIGN KEY (tree_id, wife)
        REFERENCES person(tree_id, xref_id) ON DELETE SET NULL
);

-- Indice filho->familia (o 'child_to_family' do legado)
CREATE TABLE person_famc (
    tree_id      UUID NOT NULL,
    person_xref  TEXT NOT NULL,
    family_xref  TEXT NOT NULL,
    PRIMARY KEY (tree_id, person_xref, family_xref),
    CONSTRAINT fk_famc_person FOREIGN KEY (tree_id, person_xref)
        REFERENCES person(tree_id, xref_id) ON DELETE CASCADE,
    CONSTRAINT fk_famc_family FOREIGN KEY (tree_id, family_xref)
        REFERENCES family(tree_id, xref_id) ON DELETE CASCADE
);

CREATE INDEX ix_person_famc_person ON person_famc (tree_id, person_xref);

-- Vinculo conjuge->familia (o 'FAMS' do legado)
CREATE TABLE person_fams (
    tree_id      UUID NOT NULL,
    person_xref  TEXT NOT NULL,
    family_xref  TEXT NOT NULL,
    PRIMARY KEY (tree_id, person_xref, family_xref),
    CONSTRAINT fk_fams_person FOREIGN KEY (tree_id, person_xref)
        REFERENCES person(tree_id, xref_id) ON DELETE CASCADE,
    CONSTRAINT fk_fams_family FOREIGN KEY (tree_id, family_xref)
        REFERENCES family(tree_id, xref_id) ON DELETE CASCADE
);

CREATE INDEX ix_person_fams_person ON person_fams (tree_id, person_xref);

-- ============================================================
-- BC-03: Analise de DNA
-- ============================================================

CREATE TABLE dna_analysis (
    analysis_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id         UUID NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    tree_id          UUID NOT NULL REFERENCES gedcom_tree(tree_id) ON DELETE CASCADE,
    match_file_ref   UUID NOT NULL REFERENCES uploaded_file(file_ref) ON DELETE RESTRICT,
    root_person_xref TEXT NOT NULL,         -- raiz resolvida (invariante I-2 de AGG-02)
    root_name_input  TEXT NOT NULL,         -- o que o usuario digitou (auditoria)
    root_was_ambiguous BOOLEAN NOT NULL DEFAULT FALSE,  -- BR-HUMANA-003: sinaliza, nao bloqueia
    accepted_count   INTEGER NOT NULL DEFAULT 0,
    skipped_count    INTEGER NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_analysis_root FOREIGN KEY (tree_id, root_person_xref)
        REFERENCES person(tree_id, xref_id) ON DELETE RESTRICT
);

CREATE INDEX ix_dna_analysis_owner ON dna_analysis (owner_id, created_at DESC);

CREATE TABLE match_result (
    match_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id        UUID NOT NULL REFERENCES dna_analysis(analysis_id) ON DELETE CASCADE,
    group_key          TEXT NOT NULL,       -- nome normalizado + ID/email (BR-MIGRAR-016)
    matched_name       TEXT NOT NULL,       -- nome ORIGINAL do CSV (BR-MIGRAR-028)
    total_cm           NUMERIC(12,4) NOT NULL,  -- CALCULADO NO NUCLEO e persistido (AD-03)
    relationship_label TEXT,                 -- uma das 9 faixas, ou 'Relação distante ou indeterminada'
                                             -- (cM > 0 fora de todas as faixas); NULL quando cM <= 0
                                             -- ou nao numerico (BR-MIGRAR-021, corrigido vs. oraculo)
    matched_person_xref TEXT NOT NULL,      -- sempre preenchido (I-4 de AGG-02)
    connection_type    TEXT NOT NULL,       -- 'direta' | 'indireta'
    mrca_xref          TEXT,                -- obrigatorio se connection_type = 'direta'
    affinity_left_xref TEXT,                -- par de conjuges (BR-HUMANA-008)
    affinity_right_xref TEXT,
    result_ordinal     INTEGER NOT NULL,    -- ordem estavel por cM decrescente (I-5)
    CONSTRAINT fk_match_person FOREIGN KEY (analysis_id)
        REFERENCES dna_analysis(analysis_id) ON DELETE CASCADE,
    CONSTRAINT ck_match_connection
        CHECK (
            (connection_type = 'direta'   AND mrca_xref IS NOT NULL)
         OR (connection_type = 'indireta' AND affinity_left_xref IS NOT NULL
                                          AND affinity_right_xref IS NOT NULL)
        )
);

CREATE INDEX ix_match_analysis_cm ON match_result (analysis_id, total_cm DESC, result_ordinal);

CREATE TABLE skipped_match (
    skipped_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id   UUID NOT NULL REFERENCES dna_analysis(analysis_id) ON DELETE CASCADE,
    group_key     TEXT NOT NULL,
    matched_name  TEXT NOT NULL,
    total_cm      NUMERIC(12,4),
    reason_code   TEXT NOT NULL,            -- ENUM fechado (BR-MIGRAR-029/030)
    reason_detail TEXT,
    CONSTRAINT ck_skipped_reason CHECK (reason_code IN (
        'no_candidate_in_tree',
        'no_ancestral_path',
        'rejected_false_positive',
        'rejected_min_intersection',
        'unresolved_root'
    ))
);

CREATE INDEX ix_skipped_analysis ON skipped_match (analysis_id, reason_code);

-- Nos do caminho, preservando a decomposicao (BR-HUMANA-008):
-- substitui a emissao de Mermaid no servidor (discard_log BR-DESCARTAR-005)
CREATE TABLE match_path_node (
    match_id     UUID NOT NULL REFERENCES match_result(match_id) ON DELETE CASCADE,
    ordinal      INTEGER NOT NULL,
    person_xref  TEXT NOT NULL,
    role         TEXT NOT NULL,             -- 'ascendente' | 'descendente' | 'afinidade'
    is_affinity_anchor BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (match_id, ordinal),
    CONSTRAINT ck_path_role CHECK (role IN ('ascendente', 'descendente', 'afinidade'))
);
```

## Relacionamentos

| Origem | Destino | Cardinalidade | Integridade | Notas |
|---|---|---|---|---|
| `consent_record.user_id` | `app_user.user_id` | N:1 | FK ON DELETE CASCADE | Consentimento morre com a conta |
| `data_retention_policy.user_id` | `app_user.user_id` | N:1 | FK ON DELETE CASCADE, **nullable** | `NULL` = política global |
| `access_audit.user_id` | `app_user.user_id` | N:1 | FK ON DELETE **SET NULL** | **Auditoria sobrevive à exclusão do usuário** — deliberado |
| `uploaded_file.owner_id` | `app_user.user_id` | N:1 | FK ON DELETE CASCADE | Isolamento por dono (AD-02) |
| `gedcom_tree.owner_id` | `app_user.user_id` | N:1 | FK ON DELETE CASCADE | |
| `gedcom_tree.source_file_ref` | `uploaded_file.file_ref` | N:1 | FK ON DELETE **RESTRICT** | Não se apaga o arquivo de origem com árvore viva |
| `person.tree_id` | `gedcom_tree.tree_id` | N:1 | FK ON DELETE CASCADE | |
| `family.husb` / `family.wife` | `person` | N:1 (composta) | FK ON DELETE SET NULL | Integridade referencial GEDCOM (I-2 de AGG-01) |
| `person_famc` / `person_fams` | `person`, `family` | N:1 | FK ON DELETE CASCADE | Índices de vínculo do legado |
| `dna_analysis.owner_id` | `app_user.user_id` | N:1 | FK ON DELETE CASCADE | |
| `dna_analysis.tree_id` | `gedcom_tree.tree_id` | N:1 | FK ON DELETE CASCADE | |
| `dna_analysis.root_person_xref` | `person` | N:1 (composta) | FK ON DELETE RESTRICT | Raiz sempre resolvida (I-2 de AGG-02) |
| `match_result.analysis_id` | `dna_analysis.analysis_id` | N:1 | FK ON DELETE CASCADE | |
| `skipped_match.analysis_id` | `dna_analysis.analysis_id` | N:1 | FK ON DELETE CASCADE | |
| `match_path_node.match_id` | `match_result.match_id` | N:1 | FK ON DELETE CASCADE | |

## Restrições

- **Unicidade**: `app_user.email`; `(tree_id, xref_id)` em `person` e `family`; `(tree_id, person_xref, family_xref)` em `person_famc` e `person_fams`; `(match_id, ordinal)` em `match_path_node`.
- **Integridade referencial**: **ativada e obrigatória**. Ao contrário do legado — que não tinha banco —, o alvo usa FKs para materializar o **invariante I-2 de AGG-01** (toda referência GEDCOM aponta para xref existente). Um GEDCOM com referência pendente deve ser rejeitado no parse (camada de aplicação), e a FK é a segunda linha de defesa.
- **Coerência de conexão de caminho**: `CHECK` garante que conexão direta tem `mrca_xref` e conexão indireta tem o par de afinidade. Impede uma decomposição incompleta de chegar ao banco — proteção direta contra RISK-011.
- **Vocabulário fechado de motivos**: `CHECK` sobre `skipped_match.reason_code` transforma a string livre do legado em enum auditável e asserível nos `parity_tests/`.
- **Particionamento / sharding**: **não aplicável** nesta escala (uso analítico, árvores de milhares de pessoas, nenhum tenant com volume extremo). Reavaliar apenas se o volume por tenant crescer ordens de magnitude. Evitou-se deliberadamente o particionamento por `owner_id` — é complexidade sem demanda comprovada.
- **Índices críticos**:
  - `ix_gedcom_tree_owner (owner_id, created_at DESC)` — toda listagem de árvores é escopada por dono.
  - `ix_match_analysis_cm (analysis_id, total_cm DESC, result_ordinal)` — serve a ordenação por cM decrescente (I-5 de AGG-02) já no banco, **sem alterar a ordem** definida pelo núcleo.
  - `ix_person_source_ordinal (tree_id, source_ordinal)` — preserva a ordem de leitura do arquivo, que é significativa (BR-MIGRAR-027).
  - `ix_skipped_analysis (analysis_id, reason_code)` — serve a auditoria de descartados (RF-07).
- **Ausência deliberada de índice em `match_result.total_cm` isolado**: a consulta é sempre dentro de uma análise.

## Considerações específicas do paradigma alvo

> O paradigma é **`OO com DI sobre funções puras`** — e não event-driven, funcional nem event sourcing. Portanto **não há outbox, event store nem projeções derivadas** (AD-05). As implicações diretas no modelo de dados são outras:

- **O banco não é autoridade aritmética.** `match_result.total_cm` é calculado pelo núcleo puro e persistido já calculado; **nenhum `SUM` sobre `match_result` é fonte de verdade** para relação de parentesco (AD-03, RISK-004). Isso é uma inversão consciente do uso comum de banco: aqui o banco **armazena**, o núcleo **decide**.
- **Ordem é dado, não consequência.** Três colunas existem exclusivamente para preservar ordens que afetam o resultado: `person.source_ordinal` (ordem da lista de resolução de nome e desempate estável), `gedcom_tree.graph_edge_order_version` (determinismo de `shortest_path` — BR-MIGRAR-024) e `match_result.result_ordinal` (ordenação estável com empates — BR-MIGRAR-031). Em um banco relacional, ordem **não** é garantida por padrão; torná-la coluna é a única forma de assegurar paridade.
- **`owner_id` como invariante** (AD-02): presente em `NOT NULL` em `uploaded_file`, `gedcom_tree`, `dna_analysis` e `access_audit`, e propagado por FK. Adicionalmente, os índices de leitura começam por `owner_id`, de modo que uma consulta sem escopo fica evidente por não usar índice.
- **Imutabilidade parcial**: `gedcom_tree` tem `updated_at` mas é tratada como **imutável após o parse** (I-4 de AGG-01). Não existe "recarregar na mesma árvore" — uma nova importação cria uma nova árvore. As tabelas `person`, `family`, `person_famc`, `person_fams` são **write-once** (só recebem escrita no parse; nunca `UPDATE`). Isso espelha o paradigma do núcleo puro (nada é mutado in-place, tudo é reconstruído).
- **Sem colunas de estado mutável em `match_result`**: o resultado de uma análise não muda. Se a árvore for reimportada, cria-se **nova** análise. Isso elimina a classe de bugs em que um resultado antigo é recalculado com dados novos — o legado tinha exatamente esse comportamento ao re-parsear o GEDCOM a cada POST.

## Origem no legado

| Tabela nova | Origem no legado | Transformação |
|---|---|---|
| `app_user` | — | **nova** (`domain.md` §4: ausência de autenticação) |
| `consent_record` | — | **nova** (BR-HUMANA-007) |
| `data_retention_policy` | — | **nova** (BR-HUMANA-007) |
| `access_audit` | — | **nova** (`analise-dna/design.md` § Observabilidade: *"Nenhum log estruturado"*) |
| `uploaded_file` | pasta `uploads/` + nome do cliente | **nova estrutura** — `discard_log.md` BR-DESCARTAR-003 (nome original vira metadado; chave gerada pelo servidor) |
| `gedcom_tree` | globais `people`/`families`/`graph`/`child_to_family` | **nova estrutura** — `discard_log.md` BR-DESCARTAR-001 (estado global → aggregate persistido) |
| `person` | dicionário `people` (`Person`/`INDI`) | mesma semântica; ganha PK composta, `source_ordinal` e campos normalizados pré-calculados |
| `family` | dicionário `families` (`Family`/`FAM` com `HUSB`/`WIFE`/`CHIL`) | mesma semântica; `CHIL` **normalizado** em `person_famc` (ver nota abaixo) |
| `person_famc` | índice `child_to_family` + campo `CHIL` | **normalizado** — o vínculo filho→família existia em duas representações no legado (campo e índice derivado) |
| `person_fams` | campo `FAMS` de `Person` | **normalizado** |
| `dna_analysis` | `results_list` local à requisição | **nova estrutura** — `discard_log.md` BR-DESCARTAR-002 (sem persistência no legado) |
| `match_result` | `DnaMatchRecord` do ERD (`_group_key`, `cM`, `matched_name`) | **preservado e estendido** (ganha caminho tipado, relação e ordenação explícita) |
| `skipped_match` | lista `skipped_matches` (motivo em string livre) | **transformado** — `reason_code` tipado (BR-MIGRAR-029/030), com o texto original preservado em `reason_detail` |
| `match_path_node` | `generate_mermaid_graph*` (string Mermaid) | **transformado** — decomposição estruturada substitui a emissão de diagrama (`discard_log.md` BR-DESCARTAR-005; BR-HUMANA-008) |

> **Nota sobre a normalização de `CHIL`**: o legado representava o vínculo filho→família de **duas** formas — a lista `CHIL` dentro de `Family` e o dicionário derivado `child_to_family` (`upload-gedcom/design.md` § Detalhe do grafo, passo 5). No alvo existe **uma** representação (`person_famc`) e é ela que sustenta tanto a subida por pais (`get_parents`) quanto o índice reverso. Isso não é decomposição 1-para-1: é **fusão de duas representações redundantes** em uma.

## Notas

- **Não há `data-dictionary.md` legado para cruzar.** O único dicionário de dados disponível é o resumo de `code-analysis.md` §5 (Person, Family, DnaMatchRecord), que foi usado como base e está integralmente coberto acima.
- **Nenhuma migração de dados foi especificada porque não existe dado a migrar** — ver `data_migration_plan.md`, que documenta explicitamente a ausência de ETL em vez de inventar um pipeline para preencher template.
- **A coluna `analysis_id`/`match_id` usa UUID** em vez de serial: evita vazamento de informação por enumeração (um atacante não infere volume de uso de outro tenant) e permite geração no cliente/servidor sem coordenação. Pequeno ganho de segurança com custo de 16 bytes por linha, aceitável nesta escala.
- **`access_audit` com `ON DELETE SET NULL` é uma decisão deliberada e merece destaque**: a trilha de auditoria de acesso a dado genético **sobrevive** à exclusão da conta. A alternativa (CASCADE) apagaria a prova de que o dado existiu e foi acessado, o que é indesejável em contexto LGPD/GDPR, onde a capacidade de demonstrar conformidade é parte da obrigação. As linhas de auditoria não contêm dado genético — apenas referências e metadados de acesso.
- **⚠️ `display_name` aceita string vazia como valor LEGÍTIMO** (BR-MIGRAR-003, corrigido contra o oráculo). A medição sobre 55.523 nomes reais mostrou **318 ocorrências de string vazia (0,57%)** e **0 ocorrências** do literal `'Sem Nome'`. `NOT NULL` é satisfeito por `''`, então não há conflito de schema — mas a implementação **não pode** tratar `''` como "ausente" nem substituí-lo por `'Sem Nome'`: isso quebraria paridade. Consequência visível: entradas vazias aparecem **primeiro** na lista de nomes e como **opção em branco** na `datalist` da UI.
- **A tabela `person` guarda `given_name`, `surnames` e `suffixes` pré-calculados.** É uma **desnormalização deliberada**: esses valores são derivados de `display_name` pela função pura `split_name_pt`. Pré-calculá-los acelera o matching (que os usa intensivamente) e, mais importante, **congela** o resultado da decomposição que o legado calculava a cada execução — evitando que uma futura mudança na normalização altere silenciosamente o matching de análises antigas. ⚠️ Custo: se `split_name_pt` for corrigido algum dia, os valores persistidos ficam desatualizados — o que é **desejável** aqui (análises antigas mantêm seu resultado), mas deve ser documentado na implementação.
