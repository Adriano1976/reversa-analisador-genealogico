# Data Delta: persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md` (27 estruturas) e
> `_reversa_sdd/migration/target_data_model.md` (DDL do alvo, congelado em 2026-09-28)
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Ponto de partida

O modelo extraído tem **27 estruturas e nenhuma tabela**: 21 vivem em memória do processo,
2 em disco (`src/uploads/`, sob chave de conteúdo) e 4 duram uma requisição
(`_reversa_sdd/architecture.md#4`). Não existe DDL, schema, ORM nem migração, e os `PK`/`FK`
do ERD são **lógicos** — "não existe constraint: uma referência GEDCOM pendente é **aceita**
e a aresta simplesmente não é criada" (`_reversa_sdd/erd-complete.md#7`).

**Nada é removido por esta feature.** O delta é puramente aditivo, e o único estado que
muda de natureza é o resultado da análise, que deixa de morrer com a requisição.

## 2. Estruturas do legado que passam a ter destino

| Estrutura extraída (`erd-complete.md#6`) | Onde vive hoje | Vai para | Como |
|---|---|---|---|
| `RESULTADO_ANALISE` (24) | item de `results_sorted`, memória | `match_result` + `match_path_node` | Projeção direta: nada é recalculado |
| `EVIDENCIA_KIT` (11) | bloco de `evidencias[nome][kit]` | `match_kit` | Um registro por **(nome do CSV, kit)** — a mesma chave do núcleo, nunca somada entre kits |
| `FICHA_PESSOA` (19) | `person_summary(pid)` | `analysis_person` | Completa para a raiz e para o match (já vêm prontas em `person_a`/`person_b`); mínima para os nós do caminho |
| `CONFRONTO` (17) | `compare(...)` | colunas de veredito em `match_result` + `match_kit` | **Extensão:** não existe no DDL do alvo |
| `DESCARTADO` (25) | item de `skipped_matches` | `skipped_match` | Projeção direta |
| `MENSAGEM_FINAL` (26) | `message` de `dna_analysis` | `dna_analysis.message` | Texto, sem reinterpretação |
| `AVISO` (13) | `{code, message}` | `match_result.observations` (texto) | O código não é persistido — ver §5 |
| `SEGMENTO` (12) | item de `evidencia["segments"]` | **nada** | Dado bruto; ver §5 |
| `HIPOTESE_KIT` (14) | bloco de `possible_relationships` | **nada** | Recomputável das faixas publicadas; ver §5 |
| `LINHA_SCP40` (15) / `SCP40_META` (16) | constantes do módulo | `match_result.comparison_method` | Só o **método** e a janela usada; a tabela publicada não é copiada |

## 3. Tabelas novas

**Seis tabelas.** Três são **herdadas** do DDL do alvo com nomes e colunas preservados, uma
é herdada e **estendida**, e duas são **extensão declarada** (`D-06` do `roadmap.md`).

| # | Tabela | Origem | Papel |
|---|---|---|---|
| 1 | `dna_analysis` | herdada do alvo | A execução: contexto, chaves de conteúdo das duas entradas, raiz, contagens e a mensagem de contrato |
| 2 | `match_result` | herdada do alvo, **estendida** | A conexão: pessoa casada, cM, parentesco documental, ordem, e o **bloco do veredito** |
| 3 | `match_path_node` | herdada do alvo | Os nós do caminho documental, com papel e ordinal |
| 4 | `skipped_match` | herdada do alvo | O descarte auditável: nome, kit, cM e motivo |
| 5 | `match_kit` | **extensão** | Metadados de cada kit **e** o veredito por kit — que o alvo não modela |
| 6 | `analysis_person` | **extensão** | Snapshot das pessoas que a análise usou e exibiu |

### 3.1 `dna_analysis`

| Coluna | Tipo | Nota |
|---|---|---|
| `analysis_id` | `UUID PK DEFAULT gen_random_uuid()` | Herdado do alvo. Sem `serial`: UUID evita inferir volume por enumeração |
| `owner_id` | `TEXT NOT NULL` | O `dono`. **Sem FK e sem índice de escopo**: a `RN-10` diz que ele não filtra nada. Divergência consciente do alvo, que tem FK para `app_user` |
| `tree_ref` | `TEXT NOT NULL` | Chave de conteúdo + nome visível do GEDCOM (`<sha256 truncado>__<nome>`). É a **referência**, não o arquivo (`RN-04`) |
| `match_file_ref` | `TEXT NOT NULL` | Idem, para o CSV |
| `root_name_input` | `TEXT NOT NULL` | O que o operador digitou — auditoria |
| `root_person_xref` | `TEXT` | Resolvido de `documentary.person_a.id`. **Nulo** quando a análise não produziu nenhum resultado aceito — ver §5 |
| `accepted_count` | `INTEGER NOT NULL DEFAULT 0` | Coerente com a mensagem exibida |
| `skipped_count` | `INTEGER NOT NULL DEFAULT 0` | Idem |
| `message` | `TEXT NOT NULL` | A mensagem de contrato, ao caractere |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | Ordena o histórico |

### 3.2 `match_result`

Herdadas do alvo: `match_id`, `analysis_id`, `matched_name`, `matched_person_xref`,
`total_cm NUMERIC(12,4)`, `relationship_label`, `result_ordinal`.

Do legado, acrescentadas por fidelidade ao núcleo: `csv_name`, `relationship_key`,
`meioses`, `documentary_status`, `mrca_xref`, `causes TEXT[]`, `observations TEXT[]`,
`detail`.

**Extensão — o bloco do veredito**, que o DDL congelado não tem:

| Coluna | Tipo | Nota |
|---|---|---|
| `comparison_status` | `TEXT NOT NULL` + `CHECK IN ('COMPATIVEL','POSSIVEL','CONFLITANTE','INCONCLUSIVO')` | Os quatro estados de `state-machines.md#3` |
| `comparison_label` | `TEXT NOT NULL` | O rótulo em português que a tela mostra (`Compatível`, …) |
| `comparison_method` | `TEXT` | `scp40:<relação>` ou `scp40:meioses=<n>`. **Nulo** é legítimo (INCONCLUSIVO sem janela) |
| `expected_low` / `expected_high` / `expected_average` | `NUMERIC(12,4)` | A janela esperada e de onde ela veio |
| `comparison_detail` | `TEXT NOT NULL` | O **porquê** que o operador lê — `RF-07` |

> O `CHECK` do estado é **guarda contra defeito, não autoridade**. A autoridade da regra
> continua sendo `core/evidence_comparison.py`; o banco só recusa lixo. Registrado porque o
> projeto trata "autoridade única" como regra de primeira classe.

### 3.3 `match_kit` — a extensão que o alvo não previu

`kit_id UUID PK`, `match_id UUID FK`, `ordinal INTEGER NOT NULL`, `kit TEXT` (nulo é
legítimo: o núcleo usa o marcador `SEM-KIT`), `source TEXT`, `total_cm NUMERIC(12,4)`,
`segment_count INTEGER`, `largest_segment_cm NUMERIC(12,4)`, `status TEXT` com o **mesmo**
`CHECK` de quatro estados, `status_note TEXT`.

**Por que existe.** O DDL do alvo só tem `match_result.total_cm`. Medido (M-13): nenhuma
tabela de kit, e nenhuma coluna para o veredito **por kit**. E o veredito por kit não é
detalhe: `comparison.per_kit` é o que explica por que dois kits do mesmo nome chegaram a
estados diferentes, e a junção é conservadora. Sem esta tabela, metade da máquina de
decisão do `state-machines.md#3` ficaria sem destino.

### 3.4 `analysis_person` — o snapshot das pessoas

`analysis_id UUID`, `xref TEXT`, `nome TEXT`, `sexo TEXT`, `nascimento TEXT`,
`local_nascimento TEXT`, `falecimento TEXT`, `completa BOOLEAN NOT NULL`, com
`PRIMARY KEY (analysis_id, xref)` e FK composta a partir de `match_result` e de
`match_path_node`.

**Por que é snapshot e não a tabela `person` do alvo.** O alvo guarda a **árvore** em
`person`, ligada a `gedcom_tree`. A `RN-04` decidiu o oposto: a árvore **não** é duplicada
no banco — ela continua sendo o arquivo imutável de `src/uploads/`, referenciado por
`tree_ref`. O que se guarda aqui é o retrato das pessoas que **esta análise** usou, e ele
não muda quando a árvore for reimportada (`RN-03`).

### 3.5 `match_path_node` e `skipped_match`

`match_path_node` é **herdada literalmente** do alvo: `(match_id, ordinal)` como PK,
`person_xref`, `role` e `is_affinity_anchor`. O `role` aceita `ascendente`, `descendente` e
`afinidade`, como no alvo; **no fluxo de DNA o valor `afinidade` não ocorre**, porque quem
o atribui é `path_search.py` e não a análise de DNA (`state-machines.md#4`). Isso é
registrado para que a coluna não seja lida como "a análise de DNA produz afinidade".

`skipped_match` herda `skipped_id`, `analysis_id`, `matched_name` e `total_cm`. O
`reason_code` do alvo é um **enum fechado de cinco valores**; o núcleo produz **texto
livre** ("não encontrado", ou a razão do matching). Decisão: coluna `reason TEXT NOT NULL`
com o texto do núcleo, e a divergência fica declarada — fechar o enum exigiria mapear
texto em código, que é a inferência a partir de mensagem que o projeto recusa desde a
feature 006.

## 4. Índices

| Índice | Serve a |
|---|---|
| `ix_dna_analysis_created (created_at DESC)` | O `RF-14`: "a última análise" |
| `ix_match_result_ordinal (analysis_id, result_ordinal)` | **A releitura na ordem exibida** (`RN-08`, `E-01`) |
| `ix_match_kit_match (match_id)` | Os kits de uma conexão |
| `ix_skipped_match_analysis (analysis_id)` | A auditoria dos descartes (`RN-07`) |
| `PK (match_id, ordinal)` em `match_path_node` | Herdado do alvo |
| `PK (analysis_id, xref)` em `analysis_person` | O snapshot por pessoa |

> ⚠️ **Achado, e ele muda a herança do `D-06`.** O alvo indexa
> `ix_match_analysis_cm (analysis_id, total_cm DESC, result_ordinal)` para "servir a
> ordenação por cM decrescente já no banco, **sem alterar a ordem** definida pelo núcleo".
> **A ordem do núcleo não é cM decrescente puro**: ela é `(tem_caminho primeiro,
> −cM depois)` — `core/dna_analysis.py:266-270`. Portanto o índice do alvo **não** serve
> para reproduzir a ordem exibida, e o único campo que a reproduz é `result_ordinal`.
> O índice herdado é mantido apenas como nome histórico? **Não** — manter um índice que não
> serve a nenhuma consulta desta feature seria peso sem leitura. Ele **não** é criado, e a
> divergência fica declarada aqui para a onda seguinte reconciliar.
>
> **Nenhum índice começa por `owner_id`**, ao contrário do alvo: a `RN-10` diz que nenhuma
> consulta filtra por dono, e um índice que sugere escopo seria a única coisa nesta feature
> a insinuar isolamento.

## 5. O que deliberadamente **não** é persistido

| Não persistido | Por quê |
|---|---|
| A **árvore completa** (pessoas e famílias do GEDCOM) | `RN-04`: já é arquivo imutável sob chave de conteúdo em `src/uploads/`, e duplicá-la criaria duas verdades |
| Os **segmentos** por linha do CSV (`SEGMENTO`, 12) | É dado bruto que o CSV armazenado já contém, e a agregação é do núcleo. Persistir segmento a segmento multiplicaria as linhas por dezenas sem responder nenhuma pergunta de auditoria |
| As **hipóteses** por kit (`HIPOTESE_KIT`, 14) | Recomputáveis das faixas publicadas do Shared cM Project 4.0; persistir seria copiar uma tabela publicada, e a fonte citada é o módulo (`Princípio V`) |
| A tabela **SCP40** inteira (`LINHA_SCP40`, `SCP40_META`) | Só o **método** e a janela usada importam para o veredito (`RF-07`) |
| O **texto do Mermaid** | É apresentação, e ela é gerada no cliente desde o ADR-03 |
| A **lista completa de nomes** da tela | É a exposição que o `gaps.md#6` já encaminhou à Onda 4, e persistiria dado pessoal sem consumidor |
| O **código** dos avisos (`AVISO.code`) | O núcleo expõe `code` e `message`, mas a análise já entrega a lista **deduplicada de textos** (`observations`). Persistir o código exigiria correlacionar avisos a resultados, que o núcleo não faz. O texto é preservado; o código é lacuna declarada |
| O **`root_was_ambiguous` estruturado** | `RF-03` pede "se a raiz era ambígua". O sinal existe no núcleo **apenas como texto** dentro de `observations` — ver §6 |
| O **sexo e as datas dos nós do caminho** | `RF-04` os pede, mas o resultado carrega apenas `id` e `nome` para os nós intermediários — ver §6 |

## 6. Desvios declarados do `requirements.md`, e por quê

Dois campos do `RF-03`/`RF-04` **não são entregues como escritos**, e a razão é medida, não
estética. Nenhum dos dois é resolvido mudando o núcleo.

1. **`RF-03`, "se a raiz era ambígua".** Em `core/dna_analysis.py:182-189`, a ambiguidade da
   raiz vira **texto** e entra em `observations`. O sinal estruturado não sai do núcleo. O
   que se persiste é o **texto**, que preserva a informação.
2. **`RF-04`, sexo e datas para os nós do caminho.** Em `core/dna_analysis.py:243-249`, o
   resultado carrega `documentary.path.ids` e `.names` — apenas. As fichas completas
   (`person_summary`) existem **só** para a raiz e para o match, em `documentary.person_a` e
   `.person_b`, e são essas duas que entram completas em `analysis_person`
   (`completa = TRUE`). Os nós do caminho entram com identificador e nome
   (`completa = FALSE`).

As três saídas foram avaliadas e descartadas no `roadmap.md` (`D-15`): mudar a saída do
núcleo (quebraria o `W016` e a paridade), chamar `person_summary` no caminho de gravação
(recalcularia o que o núcleo já decidiu, e acoplaria a persistência ao domínio), e derivar
o booleano do texto (inferência a partir de mensagem de contrato, que a feature 006
abandonou de propósito ao criar o campo de desfecho).

## 7. Integridade, precisão e migrações

**Integridade.** As seis tabelas nascem com **`FK` real** entre si e são escritas em **uma
transação** (`D-05`). É o inverso do legado, onde a referência pendente é aceita e a aresta
não é criada (`erd-complete.md#7`), e é o lado que o alvo quer. Não há risco para o legado:
nenhuma dessas tabelas é lida por código existente.

**Precisão do cM.** `NUMERIC(12,4)`, herdado do alvo. O valor é **transportado** do núcleo,
nunca reagregado (`RN-05`): `RISK-004` registra que somar no banco em ordem diferente da
leitura do `groupby.agg` do pandas pode alterar o último dígito e **cruzar um limite de
faixa** — e as fronteiras relevantes são 46, 200, 553, 1317, 2200 e 3300 cM. O teste de
ida e volta é requisito, não zelo.

**Migrações necessárias: nenhuma.** Não existe dado persistido a converter. A única
migração é a **primeira criação** do esquema, idempotente (`D-07`).

> 🔴 **Limite declarado.** `CREATE TABLE IF NOT EXISTS` não altera tabela existente: uma
> mudança de esquema **depois** da primeira subida não é coberta por esta feature, e exigiria
> `docker compose down -v` (perdendo o histórico) ou `ALTER TABLE` manual. Não há runner de
> migração aqui — Alembic é decisão do alvo (`AMB-019`), não desta feature.

## 8. Herança e divergência em relação ao alvo

| Aspecto | Alvo (`target_data_model.md`) | Esta feature | Natureza |
|---|---|---|---|
| Nomes de `dna_analysis`, `match_result`, `skipped_match`, `match_path_node` | ✅ | ✅ **herdados** | conformidade |
| `gen_random_uuid()` nas chaves | ✅ | ✅ **herdado** | conformidade |
| `person` / `gedcom_tree` / `family` | árvore normalizada no banco | ❌ **não criadas** | divergência por `RN-04` |
| `app_user`, `consent_record`, `data_retention_policy`, `access_audit`, `uploaded_file` | ✅ | ❌ **não criadas** | divergência declarada: pertencem às Ondas 3 e 5 |
| `owner_id` com `FK` para `app_user` e índices de escopo | ✅ | `TEXT NOT NULL`, sem FK e sem índice | divergência por `RN-10` |
| Veredito de quatro estados | ❌ **não existe** | ✅ `comparison_*` em `match_result` | **extensão nomeada** |
| Metadados de kit e veredito por kit | ❌ **não existe** | ✅ `match_kit` | **extensão nomeada** |
| `connection_type` com enum `direta`/`indireta` e `CHECK` de MRCA/afinidade | ✅ | ❌ **não adotado**: o fluxo de DNA produz `documentary_status` (`found`/`not_found`/`ambiguous`), e a afinidade é atribuída por `path_search.py`, não por ele | divergência declarada |
| `reason_code` como enum fechado em `skipped_match` | ✅ | `reason TEXT` com o motivo do núcleo | divergência declarada (evita mapear texto em código) |
| `ix_match_analysis_cm (analysis_id, total_cm DESC, result_ordinal)` | ✅ | ❌ **não criado**: a ordem do núcleo é `(tem_caminho, −cM)`, e o índice do alvo não a reproduz | divergência declarada |
| `schema_version` / runner de migração | ❌ | ❌ **não criado** | conformidade — e é o `AMB-019` do alvo |

## 9. Lacunas de dados

| ID | Lacuna | Conf. |
|---|---|---|
| `DD-01` | O **código** dos avisos (`AVISO.code`) não é persistido — só o texto. Reconstruir "qual regra disparou" a partir do histórico exige leitura humana da mensagem | 🟡 |
| `DD-02` | O **`root_was_ambiguous` estruturado** e as **datas dos nós do caminho** dependem de a saída do núcleo carregar mais do que carrega hoje. Enquanto ela estiver congelada (`W016`), os dois ficam como texto e como identificador-e-nome | 🟢 |
| `DD-03` | Não há **migração** de esquema depois da primeira subida. `CREATE TABLE IF NOT EXISTS` não evolui tabela existente | 🟢 |
| `DD-04` | O `analysis_person.completa = FALSE` não distingue "o núcleo não expôs o dado" de "o GEDCOM não tinha o dado". As duas causas entram como `null` nas mesmas colunas | 🟡 |
| `DD-05` | A **ordem dos kits** dentro de uma conexão é persistida por `ordinal`, mas o núcleo ordena kits por cM decrescente (`genetic_evidence.py:234`) com desempate não declarado. Empate exato entre kits de mesmo cM pode não ser reproduzível | 🔴 |
