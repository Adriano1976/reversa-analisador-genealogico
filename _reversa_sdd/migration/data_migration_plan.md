---
schemaVersion: 1
generatedAt: 2026-09-28T03:12:20Z
reversa:
  version: "1.2.58"
kind: data_migration_plan
producedBy: designer
hash: "sha256:e21c76e18bb5d5451f0abb18d9f76070e2900274de22228cd9a351b96e8cb045"
---

# Data Migration Plan

> Plano de migração dos dados do legado para o sistema novo: mapeamento, transformações, ETL, cutover de dados e validação.

## ⚠️ Resumo executivo: não há dados a migrar

**Este artefato documenta uma ausência, não um pipeline.** O legado **não possui banco de dados, schema, nem dado persistido de usuário**. Todo o estado era mantido em memória (dicionários `people`/`families` + grafo `networkx`) e destruído ao fim de cada requisição — `architecture.md` §1 e §5, `inventory.md` §5, `upload-gedcom/design.md` § Estado Interno (*"Esses globais são sobrescritos a cada novo parse"*).

Consequências diretas, que anulam seções inteiras do template:

| Seção clássica de migração de dados | Aplicabilidade aqui |
|---|---|
| Volume estimado por entidade | **Zero.** Nenhuma linha existente. |
| Mapeamento legado → novo | **Conceitual apenas** — não há instância de dado a mover (ver abaixo). |
| Transformações por coluna | **Nenhuma.** Não há coluna legada. |
| Estratégia de ETL | **Não aplicável.** Não há extração, nem carga. |
| Backfill e captura de delta | **Não aplicável.** Não há histórico nem sistema em operação escrevendo. |
| Reconciliação contínua | **Não aplicável.** |
| Validação de qualidade pós-carga | **Não aplicável a dados legados.** Substituída por validação de *paridade comportamental* (ver § Validação). |

- **Volume estimado**: **0 linhas** em todas as entidades alvo. O sistema novo nasce com banco vazio.
- **Janela de migração**: **não existe janela de dados.** A janela do `cutover_plan.md` (2–4h) cobre apenas provisionamento e publicação — o passo 3 daquele plano (*"aplicar migrations do schema novo"*) opera sobre banco vazio e é, por isso, totalmente reversível.
- **Estratégia**: **nenhuma** (nem `backfill + delta`, nem `bulk único`, nem `replicação contínua`). A estratégia correta é **criação de schema vazio** e uso a partir do primeiro upload real.

> **Por que este artefato existe então?** Porque há uma migração real a fazer, só que ela é **conceitual e comportamental**, não de dados: o **estado em memória vira modelo persistido** (BR-DESCARTAR-001) e o **comportamento do núcleo precisa ser provado igual ao do legado** (métrica primária do brief). As seções abaixo registram isso.

## Mapeamento legado → novo

> Este mapeamento é **conceitual**: descreve de onde cada tabela nova deriva em termos de *entidade do legado*, não de *linhas a copiar*. Não há `SELECT` de origem.

| Origem (legado) | Destino (novo) | Tipo | Notas |
|---|---|---|---|
| — | `app_user` | **novo** | Sem origem. Legado não tinha usuário (`domain.md` §4). |
| — | `consent_record` | **novo** | Sem origem (BR-HUMANA-007). |
| — | `data_retention_policy` | **novo** | Sem origem (BR-HUMANA-007). |
| — | `access_audit` | **novo** | Sem origem (`analise-dna/design.md` § Observabilidade: nenhum log). |
| Arquivos em `uploads/` (no disco, voláteis) | `uploaded_file` | **nova estrutura** | Os arquivos físicos existentes no diretório são **artefatos de execuções locais de desenvolvimento**, não dados de produção. **Não migrar.** Nome original passa de chave a metadado (BR-DESCARTAR-003; BR-HUMANA-001). |
| Globais `people`, `families`, `graph`, `child_to_family` | `gedcom_tree` + `person` + `family` + `person_famc` + `person_fams` | **nova estrutura** | Não há instância a migrar — os globais existiam apenas durante a vida do processo. A origem é **o arquivo `.ged`**, que o usuário reenviará. |
| `Person`/`INDI` (dicionário) | `person` | mesma semântica, novo schema | Adiciona `source_ordinal` e campos normalizados. |
| `Family`/`FAM` com `HUSB`/`WIFE`/`CHIL` | `family` + `person_famc` | **normalização** | `CHIL` era lista dentro de `Family` **e** índice derivado `child_to_family`; no alvo há **uma** representação. Fusão de duas representações redundantes. |
| `FAMS` de `Person` | `person_fams` | **normalização** | |
| `results_list` e `skipped_matches` (locais à requisição) | `dna_analysis` + `match_result` + `skipped_match` + `match_path_node` | **nova estrutura** | Não havia persistência (BR-DESCARTAR-002). Resultados de análises antigas **não existem** e não são recuperáveis — se o usuário tinha resultados que importam, eles só existem na tela/em capturas. |
| `SHARED_CM_DATA` (tabela de cM em código) | *(código, não dados)* | **não é dado** | É regra de negócio congelada em `core/relationship.py` (BR-MIGRAR-020), não tabela de banco. Não confundir com dado a migrar. |
| `HARD_MIN` / `GIVEN_MIN` (código morto) | — | **não migrar** | Código morto confirmado. |

## Transformações

> Não há transformação **de dados legados** (não há dado legado). As entradas abaixo são as transformações que ocorrem **em tempo de execução, no fluxo de ingestão**, e por isso são relevantes para a implementação. Todas são `core/` puro.

### Transformação T-01: bytes do GEDCOM → `GedcomTree`
- **Aplica em**: ingestão de arquivo `.ged` (runtime, não migração)
- **Regra**: parse com `ged4py`; leitura de `INDI` → `person`, `FAM` → `family`; **ordem de leitura preservada** em `source_ordinal`; nome de exibição **`''` (string vazia)** quando o formato do nome resulta vazio, e literal `'Sem Nome'` **apenas** quando o objeto de nome é ausente (⚠️ BR-MIGRAR-003, corrigido contra o oráculo — ver a correção factual lá: 318 nomes vazios reais contra 0 ocorrências do literal).
- **Tratamento de inválidos**: arquivo malformado → **rejeitar** a importação com exceção de domínio tipada (`UnsupportedGedcom`). Referência pendente (`HUSB`/`WIFE`/`CHIL`/`FAMC`/`FAMS` apontando para xref inexistente) → **rejeitar** (invariante I-2 de AGG-01). ⚠️ **Atenção de paridade**: o legado **não** validava isso — um GEDCOM com referência pendente era aceito e o grafo simplesmente não tinha a aresta. Rejeitar é uma **melhoria**, e melhoria de comportamento **quebra paridade**. Decisão necessária na implementação: ver § Notas.
- **Origem da regra**: BR-MIGRAR-001, 002, 003; `upload-gedcom/design.md` § Detalhe do fluxo de parsing.

### Transformação T-02: bytes do CSV de DNA → matches agregados
- **Aplica em**: ingestão de arquivo `.csv` (runtime)
- **Regra**: ler tentando **UTF-8 e caindo para Latin-1** na falha; detectar colunas tolerante (`Name`/`MatchedName`/`Nome`; `cM`/`TotalCM`/`Total cM`); montar `_group_key` (nome normalizado + ID/email, ID por regex `[A-Z]{2}\d{7}`); agrupar e **somar cM preservando a ordem de origem**.
- **Tratamento de inválidos**: cM não numérico ou ≤ 0 → **lista vazia de relações** (não descartar a linha, mas o match fica **sem relação prevista**); colunas obrigatórias ausentes → rejeitar com `DnaCsvMissingColumns`. ⚠️ Ver a correção factual de BR-MIGRAR-021: este é o **Caso A**, distinto do Caso B (cM > 0 fora de todas as faixas → `"Relação distante ou indeterminada"`).
- **Origem da regra**: BR-MIGRAR-016, 017, 018, 019, 021.

### Transformação T-03: normalização de nomes na ingestão
- **Aplica em**: `person.given_name`, `person.surnames`, `person.suffixes` (pré-calculados no parse)
- **Regra**: `demojibake` → `strip_bad_utf` → `norm_name` (NFKD, sem acentos, minúsculas) → `split_name_pt` → `surnames_set`.
- **Tratamento de inválidos**: string não-Latin-1 em `demojibake` → **não abortar**; preservar o valor original e seguir. O legado lançava e capturava no controller; no alvo a função pura deve ser **total** (nunca lançar sobre entrada de usuário) e a estratégia de fallback deve reproduzir o comportamento observável do legado.
- **Origem da regra**: BR-MIGRAR-006, 007, 012 ⚠️ tabela de equivalentes **transcrita de `app.py`** (RISK-003).

### Transformação T-04: agregação de cM — ordem preservada
- **Aplica em**: `match_result.total_cm`
- **Regra**: soma dos segmentos agrupados por `_group_key`, **na ordem em que aparecem no CSV**, em ponto flutuante de dupla precisão. Persistir o resultado **já calculado**; o banco não recalcula (AD-03).
- **Tratamento de inválidos**: n/a (cM inválido já tratado em T-02).
- **Origem da regra**: BR-MIGRAR-016; `risk_register.md` RISK-004.

### Transformação T-05: decomposição do caminho em estrutura tipada
- **Aplica em**: `match_result` + `match_path_node` (substitui a string Mermaid do legado)
- **Regra**: executar `find_ancestral_path` (direto, `max_depth=20`); se falhar, `find_indirect_path` (`max_hops=40`); decompor em ramos ascendente/descendente, identificar o MRCA, e — na conexão indireta — dividir no **1º par de cônjuges adjacentes**, usando `are_spouses`.
- **Tratamento de inválidos**: sem caminho → o match vai para `skipped_match` com `reason_code = 'no_ancestral_path'`; **não** gera `match_result` parcial (invariante I-4 de AGG-02).
- **Origem da regra**: BR-MIGRAR-022 a 025; BR-HUMANA-008 ⚠️ **ponto de maior risco de perda silenciosa** (RISK-011).

### Transformação T-06: cM → relação prevista
- **Aplica em**: `match_result.relationship_label`
- **Regra**: avaliar as **9 faixas em ordem**, retornando a primeira que contém o valor. As faixas **se sobrepõem** (ex.: 46–515 e 200–850 contêm 200–515) — a ordem decide.
- **Tratamento de inválidos**: **dois casos distintos** (ver correção factual de BR-MIGRAR-021): cM ≤ 0 ou não numérico → **lista vazia** (sem relação prevista); cM > 0 que não cai em nenhuma das 9 faixas → literal `'Relação distante ou indeterminada'`.
- **Origem da regra**: BR-MIGRAR-020, 021 ⚠️ não converter para busca binária nem para intervalo de banco.

## Estratégia de ETL

- **Ferramenta**: **nenhuma.** Não há ETL.
- **Fluxo**: não aplicável. O schema é criado vazio por migrations (`migrations/`), e o dado passa a existir a partir do primeiro upload real do usuário.
- **Idempotência**: aplicável às **migrations**, não a um ETL. As migrations devem ser idempotentes e versionadas (ferramenta a escolher na implementação — ex.: Alembic, padrão do ecossistema FastAPI/SQLAlchemy).
- **Throughput esperado**: não aplicável.

> **A única "carga" que existe é a ingestão em runtime**, cujo desempenho é relevante mas não é migração: o parse de um GEDCOM de milhares de pessoas ocorre **uma vez por importação** (não a cada requisição, como no legado — resolve a dívida #4 de `architecture.md` §5).

## Backfill e delta

- **Backfill**: **não aplicável.** Não há histórico a carregar.
- **Captura de delta**: **não aplicável.** Não existe sistema legado em operação escrevendo dados concorrentemente — o legado nunca foi deployado (`architecture.md` §5 dívida #3). Não há CDC, log mining, timestamps nem triggers a considerar.
- **Reconciliação periódica**: **não aplicável.**
- ⚠️ **Consequência que merece atenção**: como não há delta nem janela, **não existe a clássica "última milha"** de uma migração de dados. Isso remove a maior fonte de risco operacional de cutovers tradicionais — e é exatamente o que torna viável a janela curta de 2–4h do `cutover_plan.md`.

## Cutover de dados

> Ver também `cutover_plan.md`. Aqui apenas a parte específica de dados.

- **Janela**: a mesma do `cutover_plan.md` (data indefinida — o brief declara *"sem prazo"*).
- **Sequência de corte (parte de dados)**:
  1. Aplicar migrations do schema novo em banco **vazio**. *(Passo 3 do `cutover_plan.md`.)*
  2. Verificar que o schema está íntegro (migrations aplicadas, FKs e CHECKs ativos) — consulta ao catálogo do banco.
  3. **Nenhum passo de cópia, transformação ou reconciliação de dados.** Não há dado a mover.
  4. Confirmar que os diretórios de `uploads/` do legado **não** foram copiados nem referenciados pelo sistema novo.
- **Verificação pós-corte**:
  - **Contagens**: todas as tabelas em **0 linhas** no momento do cutover. Qualquer contagem não-zero antes do go-live indica carga indevida — investigar.
  - **Checksums**: não aplicável a dados. Substituídos por **checksum de schema** (hash das migrations aplicadas) para garantir que produção e staging têm o mesmo schema.

> **Rollback de dados é trivial nesta fase**: o banco está vazio. Recriá-lo não perde nada. ⚠️ **Esta premissa deixa de valer após o go-live com usuários reais** — a partir daí existe dado genético persistido e o rollback não pode descartá-lo (registrado em `cutover_plan.md` § Plano de rollback).

## Validação de qualidade

> As métricas clássicas de migração de dados (contagem, soma monetária, integridade referencial) **não se aplicam** — não há dado de origem. A validação que importa aqui é **comportamental**: provar que o núcleo novo reproduz o comportamento do legado. É a métrica primária do brief.

| Métrica | Alvo | Fonte de medição |
|---|---|---|
| **Paridade de matching** | **100%** de igualdade exata | `tests/parity/` — harness diferencial executando `analisador-genealogico/app.py` e o núcleo novo sobre as mesmas fixtures (Onda 0/1) |
| Paridade de relação por cM | 100%, incluindo fronteiras de faixa | Fixtures com cM exatamente em 46, 200, 553, 1317, 2200, 3300 |
| Paridade de caminho indireto | 100%, incluindo decomposição por cônjuges | Fixtures com múltiplas afinidades (cobre RISK-011) |
| Paridade de agregação de cM | igualdade **exata** (sem tolerância) | Fixtures com segmentos duplicados e valores de ponto flutuante sensíveis à ordem |
| Isolamento entre usuários | **0 vazamentos** | Teste negativo: usuário A → recurso de B deve retornar `404` |
| Integridade referencial GEDCOM | 0 referências pendentes aceitas | Teste de parse com GEDCOM malformado |
| Cobertura da auditoria de descartados | todo match do CSV em `match_result` **ou** `skipped_match` | Asserção de completude (invariante I-4 de AGG-02) |

## Riscos específicos de dados

- **RISK-004** (crítico/alto): divergência aritmética por ponto flutuante na agregação de cM e no desempate. Ver `risk_register.md`.
- **RISK-002** (crítico): oráculo circular. Se a validação de paridade usar a reconstrução em vez do `app.py` do legado, todo este plano de validação perde valor.
- **RISK-009** (alto): divergência entre versões de `thefuzz`/`pandas`/`ged4py` entre o ambiente do oráculo e o do alvo pode produzir divergência que não é erro do port.
- **RISK-005** (crítico): vazamento entre usuários — em termos de dados, significa que uma consulta pode retornar `person`/`match_result` de outro `owner_id`.
- **Risco específico e novo, não catalogado no `risk_register.md`**: a desnormalização de `person.given_name`/`surnames`/`suffixes` (ver `target_data_model.md` § Notas) cria dados derivados persistidos. Se a função `split_name_pt` evoluir, dados antigos e novos divergem. **Aceito deliberadamente** (preserva o resultado de análises antigas), mas o agente de codificação deve registrar isso na implementação — é uma decisão de design, não um descuido.

## Notas

- **Decisão de implementação em aberto, sinalizada deliberadamente (ligada a T-01)**: o legado **aceitava** GEDCOM com referência pendente (o grafo simplesmente não ganhava a aresta); o alvo, pela invariante I-2 de AGG-01, tende a **rejeitar**. Rejeitar é melhor engenharia, mas é **mudança de comportamento observável** e, portanto, **quebra paridade** — o critério nº 1 do brief. Caminhos possíveis: (a) aceitar como o legado e apenas **sinalizar** as referências pendentes no resultado da importação (preserva paridade integralmente); (b) rejeitar, aceitando a divergência e registrando-a como melhoria deliberada; (c) aceitar por default e oferecer validação estrita como opção. **Recomendação do Designer: (a)** — coerente com a decisão BR-HUMANA-003 (sinalizar em vez de bloquear) e com a métrica de paridade. Como envolve uma escolha de comportamento visível, fica registrada para validação na implementação e **não** foi decidida em silêncio.
- **Nenhum dado do legado é perdido por este plano, porque nenhum dado do legado existe.** Se o usuário tiver resultados de análises anteriores que precise preservar, eles existem apenas em capturas de tela ou exportações manuais — e essa é a única "migração de dados" concebível neste projeto. Vale confirmar: **se houver algum resultado histórico que importe, ele deve ser capturado antes do cutover**, porque não há mecanismo de recuperação.
- **O `cutover_plan.md` depende deste artefato de forma incomum**: normalmente o plano de dados é o mais arriscado do cutover; aqui ele é o **menos** arriscado (banco vazio, sem ETL, rollback trivial). O risco do cutover migrou integralmente para os **pré-requisitos de paridade** e para a **decisão de abrir cadastro** — e é lá que o `cutover_plan.md` concentra os portões.

---
*Gerado pelo Reversa-Designer em 2026-09-28.*
