-- init.sql — esquema da persistencia historica das analises (feature 008).
--
-- Executado pelo entrypoint do PostgreSQL, montado em /docker-entrypoint-initdb.d/ (D-07).
--
-- IDEMPOTENTE, E ISSO E REQUISITO (RF-12), NAO CONSEQUENCIA. O entrypoint so roda os scripts
-- quando o diretorio de dados esta vazio, o que cobre a primeira subida mas NAO uma
-- reexecucao manual. Por isso tudo usa `IF NOT EXISTS` e NAO existe nenhum `DROP` neste
-- arquivo: um `DROP` no topo apagaria o historico, que e o proposito da feature.
--
-- `gen_random_uuid()` e nativo desde o PostgreSQL 13, entao nao ha `CREATE EXTENSION
-- pgcrypto`. O DDL do alvo ja o usava literalmente.
--
-- HERANCA E EXTENSAO (D-06). O DDL do alvo (_reversa_sdd/migration/target_data_model.md,
-- congelado em 2026-09-28) e ANTERIOR ao nascimento do confronto (2026-10-05): varredura no
-- diretorio `migration/` encontra ZERO ocorrencias de COMPATIVEL, POSSIVEL, CONFLITANTE,
-- INCONCLUSIVO, `confronto` ou `veredito`, e nenhuma tabela de metadados de kit. O alvo,
-- portanto, nao tem onde guardar o veredito. As duas extensoes estao marcadas com
-- `-- EXTENSAO` e sao nomeadas para a onda seguinte reconciliar em vez de descobrir.

-- ============================================================
-- Herdadas do alvo: nomes e colunas preservados
-- ============================================================

CREATE TABLE IF NOT EXISTS dna_analysis (
    analysis_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id         TEXT NOT NULL,        -- o `dono`. SEM FK e SEM indice de escopo (RN-10)
    tree_ref         TEXT NOT NULL,        -- chave de conteudo + nome visivel do GEDCOM
    match_file_ref   TEXT NOT NULL,        -- idem, para o CSV
    root_name_input  TEXT NOT NULL,        -- o que o operador digitou (auditoria)
    root_person_xref TEXT,                 -- nulo quando nenhum resultado foi aceito (D-15)
    accepted_count   INTEGER NOT NULL DEFAULT 0,
    skipped_count    INTEGER NOT NULL DEFAULT 0,
    message          TEXT NOT NULL,        -- a mensagem de contrato, ao caractere
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_dna_analysis_created ON dna_analysis (created_at DESC);

-- EXTENSAO: snapshot das pessoas que a analise usou e exibiu.
--
-- Nao e a tabela `person` do alvo. A RN-04 decidiu o oposto: a ARVORE NAO E DUPLICADA no
-- banco, ela continua sendo o arquivo imutavel de `src/uploads/`, referenciado por
-- `tree_ref`. O que se guarda aqui e o retrato das pessoas desta analise, e ele nao muda
-- quando a arvore for reimportada (RN-03).
--
-- `completa` distingue a ficha inteira (raiz e match, que vem prontas de `person_a` e
-- `person_b` no resultado) da mera identificacao (os nos intermediarios do caminho, que o
-- resultado carrega so com `id` e `nome`) — D-15.
CREATE TABLE IF NOT EXISTS analysis_person (
    analysis_id      UUID NOT NULL REFERENCES dna_analysis (analysis_id) ON DELETE CASCADE,
    xref             TEXT NOT NULL,
    nome             TEXT,
    sexo             TEXT,
    nascimento       TEXT,
    local_nascimento TEXT,
    falecimento      TEXT,
    completa         BOOLEAN NOT NULL,
    PRIMARY KEY (analysis_id, xref)
);

CREATE TABLE IF NOT EXISTS match_result (
    match_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id         UUID NOT NULL REFERENCES dna_analysis (analysis_id) ON DELETE CASCADE,
    result_ordinal      INTEGER NOT NULL,   -- A ORDEM E DADO (RN-08, E-01)
    csv_name            TEXT NOT NULL,
    matched_name        TEXT NOT NULL,
    matched_person_xref TEXT NOT NULL,
    total_cm            NUMERIC(12,4),      -- transportado do nucleo, NUNCA reagregado (RN-05)
    relationship_key    TEXT,
    relationship_label  TEXT,
    meioses             INTEGER,
    documentary_status  TEXT NOT NULL,
    mrca_xref           TEXT,
    causes              TEXT[],
    observations        TEXT[],

    -- EXTENSAO: o bloco do veredito, que o DDL congelado do alvo nao tem.
    comparison_status   TEXT NOT NULL,
    comparison_label    TEXT NOT NULL,
    comparison_method   TEXT,               -- nulo e legitimo: INCONCLUSIVO sem janela
    expected_low        NUMERIC(12,4),
    expected_high       NUMERIC(12,4),
    expected_average    NUMERIC(12,4),
    comparison_detail   TEXT NOT NULL,

    -- Integridade real, ao contrario do legado, onde a referencia pendente era aceita e a
    -- aresta simplesmente nao era criada. Nao ha risco para o legado: nenhuma destas tabelas
    -- e lida por codigo existente.
    --
    -- `ON DELETE CASCADE`, e nao `RESTRICT`: a garantia que interessa e a de que NAO SE
    -- GRAVA referencia a pessoa inexistente, e essa o proprio FK ja da no INSERT. O
    -- `RESTRICT` so agiria na hora de APAGAR — e ali ele quebrava a exclusao da analise,
    -- porque `analysis_person` cascateia de `dna_analysis` e o filho ainda o referenciava.
    -- Medido no `T020`: `DELETE FROM dna_analysis` falhava com
    -- `ForeignKeyViolation: fk_path_person ... is still referenced`. Apagar uma analise e
    -- operacao legitima (expurgo, limpeza de teste) e nao pode ser impossivel por desenho.
    CONSTRAINT fk_match_person FOREIGN KEY (analysis_id, matched_person_xref)
        REFERENCES analysis_person (analysis_id, xref) ON DELETE CASCADE,

    -- Guarda contra defeito, NAO autoridade. A autoridade da regra continua sendo
    -- `core/evidence_comparison.py`; o banco so recusa lixo.
    CONSTRAINT ck_comparison_status CHECK (comparison_status IN
        ('COMPATIVEL', 'POSSIVEL', 'CONFLITANTE', 'INCONCLUSIVO')),
    -- `affinity` e atribuido por `path_search.py`, e nao pela analise de DNA, que produz tres
    -- dos quatro valores. O quarto fica aceito para reconciliar com o alvo.
    CONSTRAINT ck_documentary_status CHECK (documentary_status IN
        ('found', 'not_found', 'ambiguous', 'affinity'))
);

-- A releitura na ordem exibida. O alvo indexa `(analysis_id, total_cm DESC, result_ordinal)`,
-- e esse indice NAO reproduz a ordem do nucleo, que e `(tem_caminho, -cM)` e nao cM
-- decrescente puro (`core/dna_analysis.py`, funcao `_ordem`). O unico campo que a reproduz e
-- `result_ordinal`, e e ele que o indice serve.
CREATE INDEX IF NOT EXISTS ix_match_result_ordinal
    ON match_result (analysis_id, result_ordinal);

CREATE TABLE IF NOT EXISTS match_path_node (
    match_id           UUID NOT NULL REFERENCES match_result (match_id) ON DELETE CASCADE,
    ordinal            INTEGER NOT NULL,
    person_xref        TEXT NOT NULL,
    role               TEXT NOT NULL,
    is_affinity_anchor BOOLEAN NOT NULL DEFAULT FALSE,
    -- EXTENSAO: coluna redundante, e ela existe por um motivo so — permitir a FK composta
    -- com `analysis_person`, que garante que todo no do caminho tem retrato no snapshot.
    analysis_id        UUID NOT NULL,
    PRIMARY KEY (match_id, ordinal),
    CONSTRAINT fk_path_person FOREIGN KEY (analysis_id, person_xref)
        REFERENCES analysis_person (analysis_id, xref) ON DELETE CASCADE,
    CONSTRAINT ck_path_role CHECK (role IN ('ascendente', 'descendente', 'afinidade'))
);

-- EXTENSAO: metadados de cada kit E o veredito POR KIT, que o alvo nao modela.
--
-- Nao e detalhe: o veredito por kit e o que explica por que dois kits do mesmo nome chegaram
-- a estados diferentes, e a juncao e conservadora. Sem esta tabela, metade da maquina de
-- decisao do `state-machines.md` §3 ficaria sem destino.
CREATE TABLE IF NOT EXISTS match_kit (
    match_kit_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id           UUID NOT NULL REFERENCES match_result (match_id) ON DELETE CASCADE,
    ordinal            INTEGER NOT NULL,
    kit                TEXT,                -- nulo e legitimo: o nucleo usa o marcador SEM-KIT
    source             TEXT,
    total_cm           NUMERIC(12,4),       -- o cM DESTE kit, nunca a soma entre kits (RF-05)
    segment_count      INTEGER,
    largest_segment_cm NUMERIC(12,4),
    status             TEXT NOT NULL,
    status_note        TEXT,
    CONSTRAINT uq_match_kit_ordinal UNIQUE (match_id, ordinal),
    CONSTRAINT ck_kit_status CHECK (status IN
        ('COMPATIVEL', 'POSSIVEL', 'CONFLITANTE', 'INCONCLUSIVO'))
);

CREATE INDEX IF NOT EXISTS ix_match_kit_match ON match_kit (match_id);

CREATE TABLE IF NOT EXISTS skipped_match (
    skipped_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES dna_analysis (analysis_id) ON DELETE CASCADE,
    ordinal     INTEGER NOT NULL,
    csv_name    TEXT NOT NULL,
    kit         TEXT,
    total_cm    NUMERIC(12,4),
    -- O alvo tem `reason_code` como enum fechado de cinco valores; o nucleo produz TEXTO
    -- LIVRE. Fechar o enum exigiria mapear texto em codigo, que e a inferencia a partir de
    -- mensagem de contrato que o projeto recusa desde a feature 006.
    reason      TEXT NOT NULL,
    CONSTRAINT uq_skipped_ordinal UNIQUE (analysis_id, ordinal)
);

CREATE INDEX IF NOT EXISTS ix_skipped_match_analysis ON skipped_match (analysis_id);

-- ============================================================
-- O que NAO existe aqui, e por que
-- ============================================================
--
-- `app_user`, `consent_record`, `data_retention_policy`, `access_audit` e `uploaded_file`
-- existem no DDL do alvo e NAO sao criadas: pertencem as Ondas 3 e 5, e nenhuma tem
-- consumidor nesta feature.
--
-- `person`, `family`, `gedcom_tree` NAO sao criadas: a arvore nao e duplicada no banco
-- (RN-04), ela continua sendo o arquivo imutavel de `src/uploads/`.
--
-- NENHUM indice comeca por `owner_id`, ao contrario do alvo. A RN-10 diz que nenhuma
-- consulta filtra por dono, e um indice que sugere escopo seria a unica coisa neste esquema a
-- insinuar isolamento — que segue ABERTO como divida #4.
--
-- Nao ha tabela de versao de esquema nem runner de migracao: sem migracao para aplicar, ela
-- seria decoracao, e o alvo tambem nao a tem. LIMITE DECLARADO: `CREATE TABLE IF NOT EXISTS`
-- nao altera tabela existente, entao uma mudanca de esquema depois da primeira subida exige
-- `docker compose down -v` (perdendo o historico) ou `ALTER TABLE` manual.
