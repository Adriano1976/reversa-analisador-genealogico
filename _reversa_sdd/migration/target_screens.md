---
schemaVersion: 1
generatedAt: 2026-09-28T03:20:10Z
reversa:
  version: "1.2.58"
kind: target_screens
producedBy: screen-translator
mode: hybrid
sourcePlatform: server-rendered-jinja2-bootstrap
targetPlatform: web-spa
adapter: html_legacy__spa
screenCount: 13
hash: "sha256:4eca6b9e29689f86bc890c4eab124ca36271c36c3873b849fc3e9f85a4cdb213"
---

# Target Screens

> Especificação executável de cada tela do sistema novo, derivada do legado segundo o modo aprovado em `screen_modernization_decision.md`. Conteúdo textual preservado literalmente, salvo aprovação explícita de revisão linguística.
> Leitura primária para o codificador. Cada seção é um contrato.

## Resumo

- **Modo aplicado**: **híbrido** — 8 entradas em **literal** (as telas legadas) + 5 em **modernizado** (as telas novas).
- **Telas geradas**: **13** entradas em 2 grupos.
  - **Literal (legado, 8)**: SCR-001, SCR-002, SCR-003, SCR-004, SCR-005, SCR-G01, SCR-G02, SCR-G03.
  - **Modernizado (novas, 5)**: SCR-006, SCR-007, SCR-008, SCR-009, SCR-010.
- **Adapter**: `html_legacy__spa` (formato `route-component`) — ⚠️ usado como **proxy**; ver DEV-001.
- **Tokens consumidos**: `_reversa_sdd/design-system/tokens-derived.md` (o `tokens.md` catalogado **não existe**; ver DEV-006).
- **Golden files**: **0 capturados** — manifesto emitido em `_reversa_sdd/screens/golden/manifest.yaml` com os comandos sugeridos. O oráculo legado **é executável** (Flask local), mas a captura é manual em v1 (OQ-02).
- **Deviations registradas**: **10** em `screen_deviation_log.md` (**0 pendentes; 10 aprovadas**). Handoff ao Inspector desbloqueado.

> **Reconciliação de contagem**: a decisão aprovada lista **5 telas** em modo literal; esta spec tem **8 entradas** literais porque inclui **3 componentes globais** de chrome compartilhada que não estavam no inventário da Fase 1 (que catalogou telas e estados). São eles: SCR-G01/G02 (bloco de alerta nos dois estados) e SCR-G03 (indicador de carregamento, que se comporta de forma diferente nos dois estados do legado). Nenhuma tela foi adicionada ou removida — apenas detalhada.

> **Invariante textual**: todo literal de `inventory.json § textInventory.strings` (29 strings) e `§ textInventory.serverMessages` (9 mensagens) deve aparecer **sem alteração** nas telas literais. A **única** exceção autorizada é DEV-005 (`aria-label="Close"` → `"Fechar"`).

---

# Grupo A — Telas legadas em modo LITERAL

## Tela: SCR-001 — Estado inicial: upload GEDCOM

**Origem**: `analisador-genealogico/templates/index.html:41-52`
**Modo aplicado**: literal
**Componentes do design-system**: [`PageLayout`, `Card`, `CardBody`, `FormField`, `Button`, `Alert` (opcional)]
**Pontos de interpolação**: `{{message}}`, `{{success}}`
**Transições de saída**: [submit → SCR-002 (sucesso), submit → SCR-001 (erro com alerta)]
**Tela crítica?**: não

### Especificação

```yaml
spec.kind: route-component
spec.route: /
spec.layout: AppLayout
spec.states: [idle, loading, error]
spec.legacy_origin: "analisador-genealogico/templates/index.html:41-52"
spec.render_condition:
  # O legado decide este estado NO SERVIDOR: {% if not gedcom_filename %}
  # No alvo, a condicao vem do backend (existe arvore carregada para a sessao?)
  # NAO tratar SCR-001 e SCR-002 como rotas independentes sem esta fonte de estado.
  source: "backend: has_loaded_tree == false"
  legacy_expression: "{% if not gedcom_filename %}"
spec.component:
  component: GedcomUploadPage
  legacy_origin: "analisador-genealogico/templates/index.html:41-52"
  children:
    - component: PageTitle
      tokens: [typography.h1]
      content:
        text: "Analisador Genealógico e de DNA"
      legacy_origin: "index.html:32"
    - component: Paragraph
      tokens: [typography.body, color.text-muted]
      content:
        text: "Para começar, carregue a sua árvore genealógica em formato GEDCOM."
      legacy_origin: "index.html:42"
    - component: Form
      id: gedcom-upload-form
      method: POST
      enctype: multipart/form-data
      action_target: "POST /api/trees"
      submit_event: tree.upload
      legacy_origin: "index.html:43-52"
      children:
        - component: FormField
          kind: file
          name: gedcom
          label: "Arquivo GEDCOM"
          required: true
          accept: ".ged"
          legacy_origin: "index.html:45-48"
          validation:
            required: true
        - component: ButtonRow
          children:
            - component: Button
              variant: primary
              size: lg
              layout: grid
              label: "Carregar e Analisar"
              action: form.submit
              legacy_origin: "index.html:49-51"
spec.api_changes:
  - legacy: "POST / (form-urlencoded com action=upload_gedcom, multipart com campo 'gedcom')"
    target: "POST /api/trees (multipart, campo 'file')"
    deviation: DEV-009
spec.deviations: [DEV-005, DEV-009]
spec.normalize:
  - trim_trailing_spaces: true
  - line_endings: "\n"
  - normalize_utf8: true
```

**Estados**

> Em modo literal, preservam-se os estados que o legado possui. O legado **não** tem estado de sucesso próprio para este formulário (o sucesso transita para SCR-002) e **não** tem loading local (usa o spinner global SCR-G03).

| Estado | Descrição | Conteúdo / mensagem |
|---|---|---|
| Idle | Formulário exibido, nada submetido | Conteúdo acima |
| Loading | **Global**, não local — ver SCR-G03 | `Analisando... Isso pode levar alguns segundos.` |
| Error | Falha no upload ou no parse | `{{message}}` no bloco de alerta (SCR-G01) — ex.: `Nenhum arquivo GEDCOM enviado.`, `Nenhum arquivo selecionado.` |

### Pontos de divergência aceitos

- DEV-005: `aria-label="Close"` corrigido para `"Fechar"` — **aprovado**.
- DEV-009: contrato HTTP (endpoint e nome do campo de arquivo) re-expresso para a API alvo.

---

## Tela: SCR-002 — Estado carregado: hub de abas

**Origem**: `analisador-genealogico/templates/index.html:53-61`
**Modo aplicado**: literal
**Componentes do design-system**: [`PageLayout`, `Card`, `CardBody`, `Tabs`, `Alert` (opcional)]
**Pontos de interpolação**: `{{gedcom_filename}}` *(substituído por `{{tree_id}}` — ver DEV-002)*, `{{all_names}}`, `{{message}}`, `{{success}}`
**Transições de saída**: [selecionar aba → SCR-003 | SCR-004]
**Tela crítica?**: sim (é o hub do fluxo de análise)

### Especificação

```yaml
spec.kind: route-component
spec.route: /
spec.layout: AppLayout
spec.states: [idle, loading, error]
spec.legacy_origin: "analisador-genealogico/templates/index.html:53-61"
spec.render_condition:
  source: "backend: has_loaded_tree == true"
  legacy_expression: "{% else %} (de gedcom_filename)"
spec.component:
  component: AnalysisHubPage
  legacy_origin: "analisador-genealogico/templates/index.html:53-61"
  children:
    - component: PageTitle
      tokens: [typography.h1]
      content:
        text: "Analisador Genealógico e de DNA"
      legacy_origin: "index.html:32"
    - component: Tabs
      id: analysisTabs
      tokens: [spacing.tabs-margin-bottom]
      legacy_origin: "index.html:54-61"
      tabs:
        - id: path-tab
          label: "Buscar Conexão no GEDCOM"
          target_panel: path-panel
          default_active: true
          component_ref: SCR-003
        - id: dna-tab
          label: "Analisador de DNA"
          target_panel: dna-panel
          default_active: false
          component_ref: SCR-004
    # A datalist de nomes do legado (index.html:102-106) NAO e reproduzida como
    # <datalist> embutida no HTML. Ver DEV-003: passa a ser busca paginada.
    - component: NameAutocompleteSource
      legacy_origin: "index.html:102-106"
      legacy_mechanism: "<datalist id='gedcom_names'> com todas as opcoes embutidas no HTML"
      target_mechanism: "endpoint de busca paginada"
      endpoint: "GET /api/trees/{tree_id}/names?q={query}&limit=20"
      ordered: alphabetical
      deviation: DEV-003
spec.api_changes:
  - legacy: "campo oculto gedcom_filename (index.html:68,87) identifica a arvore"
    target: "tree_id resolvido pela sessao/rota (GET /api/trees/{tree_id})"
    deviation: DEV-002
spec.deviations: [DEV-002, DEV-003]
```

### Pontos de divergência aceitos

- DEV-002: `gedcom_filename` (nome do arquivo do cliente) como identificador → `tree_id` resolvido por sessão. **Consequência direta de `discard_log.md` BR-DESCARTAR-003**, que o backend já abandonou.
- DEV-003: `datalist` com todos os nomes → busca paginada.

---

## Tela: SCR-003 — Aba "Buscar Conexão no GEDCOM"

**Origem**: `analisador-genealogico/templates/index.html:64-81`
**Modo aplicado**: literal
**Componentes do design-system**: [`Card`, `FormField`, `Button`, `Paragraph`]
**Pontos de interpolação**: `{{gedcom_filename}}` → `{{tree_id}}`, `{{all_names}}`
**Transições de saída**: [submit → SCR-005 (conexão direta), submit → SCR-005 (conexão indireta), submit → SCR-003 (erro com alerta)]
**Tela crítica?**: sim (produz as mensagens congeladas de conexão)

### Especificação

```yaml
spec.kind: route-component
spec.route: / (aba ativa por padrao)
spec.layout: AppLayout
spec.parent: SCR-002
spec.states: [idle, loading, error]
spec.legacy_origin: "analisador-genealogico/templates/index.html:64-81"
spec.component:
  component: PathSearchPanel
  legacy_origin: "analisador-genealogico/templates/index.html:64-81"
  children:
    - component: Paragraph
      tokens: [typography.body, color.text-muted]
      content:
        text: "Escolha duas pessoas do arquivo GEDCOM carregado para encontrar o caminho genealógico entre elas."
      legacy_origin: "index.html:65"
    - component: Form
      id: path-form
      method: POST
      action_target: "POST /api/trees/{tree_id}/path-searches"
      submit_event: path.search
      legacy_origin: "index.html:66-80"
      children:
        - component: FormField
          kind: text
          name: person1_name
          label: "Pessoa 1"
          required: true
          placeholder: "Comece a digitar um nome..."
          autocomplete_source: NameAutocompleteSource
          legacy_origin: "index.html:69-72"
          validation:
            required: true
        - component: FormField
          kind: text
          name: person2_name
          label: "Pessoa 2"
          required: true
          placeholder: "Comece a digitar um nome..."
          autocomplete_source: NameAutocompleteSource
          legacy_origin: "index.html:73-76"
          validation:
            required: true
        - component: ButtonRow
          children:
            - component: Button
              variant: info
              layout: grid
              label: "Encontrar Conexão"
              action: form.submit
              legacy_origin: "index.html:77-79"
spec.interpolations:
  person1_name:
    type: string
    source: "input do usuario"
  person2_name:
    type: string
    source: "input do usuario"
spec.api_changes:
  - legacy: "POST / (form-urlencoded, action=path_search, gedcom_filename, person1_name, person2_name) -> render HTML com status 200 sempre"
    target: "POST /api/trees/{tree_id}/path-searches -> JSON + status HTTP semantico"
    deviation: DEV-009
spec.transitions:
  - event: submit
    to: SCR-005
    condition: "conexao direta ou indireta encontrada"
  - event: submit
    to: SCR-003
    condition: "pessoa nao encontrada ou sem conexao (alerta de perigo)"
spec.deviations: [DEV-002, DEV-003, DEV-009]
```

### Pontos de divergência aceitos

- DEV-002, DEV-003, DEV-009 (ver `screen_deviation_log.md`).

> ⚠️ **Mensagens que este formulário deve exibir sem alteração** (produzidas pelo backend, BR-MIGRAR-028): `Pessoa 1 'X' não encontrada.` · `Pessoa 2 'X' não encontrada.` · `Nenhuma conexão encontrada entre 'X' e 'Y'.` · `Conexão direta encontrada (ancestral comum).` · `Conexão indireta encontrada (via casamento/afinidade).`

---

## Tela: SCR-004 — Aba "Analisador de DNA"

**Origem**: `analisador-genealogico/templates/index.html:83-100`
**Modo aplicado**: literal
**Componentes do design-system**: [`Card`, `FormField`, `Button`, `Paragraph`]
**Pontos de interpolação**: `{{gedcom_filename}}` → `{{tree_id}}`, `{{all_names}}`
**Transições de saída**: [submit → SCR-005 (análise concluída), submit → SCR-004 (erro com alerta)]
**Tela crítica?**: sim (é o fluxo principal do produto)

### Especificação

```yaml
spec.kind: route-component
spec.route: / (aba)
spec.layout: AppLayout
spec.parent: SCR-002
spec.states: [idle, loading, error]
spec.legacy_origin: "analisador-genealogico/templates/index.html:83-100"
spec.component:
  component: DnaAnalysisPanel
  legacy_origin: "analisador-genealogico/templates/index.html:83-100"
  children:
    - component: Paragraph
      tokens: [typography.body, color.text-muted]
      content:
        text: "Carregue sua lista de matches (CSV) e insira o seu nome para encontrar as conexões confirmadas por DNA."
      legacy_origin: "index.html:84"
    - component: Form
      id: dna-form
      method: POST
      enctype: multipart/form-data
      action_target: "POST /api/trees/{tree_id}/dna-analyses"
      submit_event: dna.analyze
      legacy_origin: "index.html:85-99"
      children:
        - component: FormField
          kind: file
          name: matches_csv
          label: "1. Lista de Matches (CSV)"
          required: true
          accept: ".csv"
          legacy_origin: "index.html:88-91"
          validation:
            required: true
        - component: FormField
          kind: text
          name: root_name
          label: "2. Seu Nome (como está no GEDCOM)"
          required: true
          placeholder: "Ex: João da Silva"
          autocomplete_source: NameAutocompleteSource
          legacy_origin: "index.html:92-95"
          validation:
            required: true
        - component: ButtonRow
          children:
            - component: Button
              variant: success
              layout: grid
              label: "Analisar Matches de DNA"
              action: form.submit
              legacy_origin: "index.html:96-98"
spec.interpolations:
  root_name:
    type: string
    source: "input do usuario"
    note: "Resolvido pelo PRIMEIRO ID em caso de homonimos (BR-MIGRAR-032). O default NAO muda; a ambiguidade e apenas sinalizada no payload (BR-HUMANA-003)."
spec.api_changes:
  - legacy: "POST / (form-urlencoded, action=dna_analysis, gedcom_filename, root_name, multipart matches_csv) -> render HTML, status 200 sempre"
    target: "POST /api/trees/{tree_id}/dna-analyses -> JSON + status HTTP semantico"
    deviation: DEV-009
spec.transitions:
  - event: submit
    to: SCR-005
    condition: "analise concluida"
  - event: submit
    to: SCR-004
    condition: "erro (alerta de perigo)"
spec.deviations: [DEV-002, DEV-003, DEV-009]
```

> ⚠️ **Mensagens congeladas deste fluxo** (BR-MIGRAR-028): `Por favor, carregue o arquivo CSV de matches.` · `Seu nome 'X' não foi encontrado no GEDCOM.`

---

## Tela: SCR-005 — Áreas de resultado (DNA, descartados e caminho)

**Origem**: `analisador-genealogico/templates/index.html:116-174`
**Modo aplicado**: literal
**Componentes do design-system**: [`Card`, `CardHeader`, `Badge`, `Table`, `GraphContainer`, `Paragraph`]
**Pontos de interpolação**: `{{result.match_name}}`, `{{result.cm}}`, `{{result.text_path}}`, `{{result.relationships}}`, `{{result.mermaid_data}}`, `{{path_result.person1_name}}`, `{{path_result.person2_name}}`, `{{item.csv_name}}`, `{{item.motivo}}`, `{{skipped_matches | length}}`
**Transições de saída**: [nenhuma — região terminal]
**Tela crítica?**: sim (é a saída principal do produto)

### Especificação

```yaml
spec.kind: route-component
spec.route: / (regiao pos-submit)
spec.layout: AppLayout
spec.states: [idle, loading, success, error]
spec.legacy_origin: "analisador-genealogico/templates/index.html:116-174"
spec.render_condition:
  note: "TRES blocos condicionalmente INDEPENDENTES. Cada um aparece por conta propria."
  blocks:
    - id: dna_results
      legacy_expression: "{% if dna_results %}"
      legacy_origin: "index.html:117-129"
    - id: skipped_matches
      legacy_expression: "{% if skipped_matches %}"
      legacy_origin: "index.html:131-161"
    - id: path_result
      legacy_expression: "{% if path_result %}"
      legacy_origin: "index.html:164-173"
spec.component:
  component: ResultsRegion
  legacy_origin: "analisador-genealogico/templates/index.html:116-174"
  children:
    # ---- Bloco 1: Resultados da Analise de DNA ----
    - component: Section
      id: dna_results
      condition: dna_results is not empty
      legacy_origin: "index.html:117-129"
      children:
        - component: Heading
          level: 2
          tokens: [typography.h2]
          layout: text-center mt-5
          content:
            text: "Resultados da Análise de DNA"
          legacy_origin: "index.html:118"
        - component: RepeatedCard
          for_each: dna_results
          legacy_origin: "index.html:119-128"
          children:
            - component: CardHeader
              children:
                - component: Text
                  content:
                    prefix: "Conexão com: "
                    strong: "{{result.match_name}}"
                  legacy_origin: "index.html:121"
                - component: Badge
                  variant: success
                  content: "{{result.cm}} cM"
                  legacy_origin: "index.html:121"
            - component: CardBody
              children:
                - component: Paragraph
                  content:
                    strong: "Caminho:"
                    value: "{{result.text_path}}"
                  legacy_origin: "index.html:123"
                - component: Paragraph
                  content:
                    strong: "Relacionamento Provável (DNA):"
                    value: "{{result.relationships}}"
                    tokens: [color.text-primary]
                  legacy_origin: "index.html:124"
                - component: GraphContainer
                  legacy_origin: "index.html:125"
                  legacy_mechanism: "<div class='mermaid'>{{result.mermaid_data | safe}}</div> renderizado por mermaid.run()"
                  target_mechanism: "componente de grafo consumindo KinshipPath estruturado (AD-04)"
                  deviation: DEV-004
    # ---- Bloco 2: Matches descartados ----
    - component: Section
      id: skipped_matches
      condition: skipped_matches is not empty
      legacy_origin: "index.html:131-161"
      children:
        - component: Heading
          level: 2
          tokens: [typography.h2]
          layout: text-center mt-5
          content:
            text: "Matches descartados"
            suffix: "({{skipped_matches | length}})"
          legacy_origin: "index.html:132"
        - component: Card
          children:
            - component: CardBody
              children:
                - component: Paragraph
                  tokens: [color.text-muted]
                  content:
                    text: "Estes nomes estavam no CSV, mas foram rejeitados pelas regras de validação. O motivo aparece abaixo."
                  legacy_origin: "index.html:136-138"
                - component: Table
                  variant: table-sm align-middle
                  responsive: true
                  legacy_origin: "index.html:140-156"
                  columns:
                    - header: "Nome no CSV"
                      width: "45%"
                      cell:
                        strong: "{{item.csv_name}}"
                    - header: "Motivo"
                      cell: "{{item.motivo}}"
                  for_each: skipped_matches
    # ---- Bloco 3: Resultado da Busca de Conexao ----
    - component: Section
      id: path_result
      condition: path_result is not empty
      legacy_origin: "index.html:164-173"
      children:
        - component: Heading
          level: 2
          tokens: [typography.h2]
          layout: text-center mt-5
          content:
            text: "Resultado da Busca de Conexão"
          legacy_origin: "index.html:165"
        - component: Card
          children:
            - component: CardHeader
              children:
                - component: Text
                  content:
                    prefix: "Conexão entre: "
                    strong: "{{path_result.person1_name}}"
                    middle: " e "
                    strong2: "{{path_result.person2_name}}"
                  legacy_origin: "index.html:167"
            - component: CardBody
              children:
                - component: Paragraph
                  content:
                    strong: "Caminho:"
                    value: "{{path_result.text_path}}"
                  legacy_origin: "index.html:169"
                - component: GraphContainer
                  legacy_origin: "index.html:170"
                  legacy_mechanism: "<div class='mermaid'>{{path_result.mermaid_data | safe}}</div>"
                  target_mechanism: "componente de grafo consumindo KinshipPath estruturado (AD-04)"
                  deviation: DEV-004
spec.interpolations:
  "result.cm":
    type: decimal
    note: "Valor calculado pelo nucleo e persistido; NAO recalculado no cliente (AD-03)"
  "result.relationships":
    type: string
    note: "VO RelationshipLabel — uma das 9 faixas, ou 'Relação distante ou indeterminada' quando cM > 0 fora de todas as faixas; AUSENTE quando cM <= 0 ou nao numerico (BR-MIGRAR-020/021, corrigido vs. oraculo)"
  "item.motivo":
    type: string
    note: "Texto humano do motivo; no alvo vem de MatchSkippedReason (codigo tipado + mensagem) — BR-MIGRAR-029/030"
spec.deviations: [DEV-003, DEV-004, DEV-009]
```

**Estados**

| Estado | Descrição | Conteúdo / mensagem |
|---|---|---|
| Idle | Nenhum resultado ainda | Região vazia (nenhum bloco renderiza) |
| Loading | **Global** — ver SCR-G03 | `Analisando... Isso pode levar alguns segundos.` |
| Error | Falha na análise ou na busca | `{{message}}` no bloco de alerta (SCR-G01/G02) |
| Success | Um ou mais blocos de resultado renderizados | Conteúdo acima |

### Pontos de divergência aceitos

- **DEV-004** ⚠️ **a deviation mais importante deste artefato**: o legado emite **sintaxe Mermaid como string** no servidor (`{{result.mermaid_data | safe}}`, `index.html:125,170`) e a renderiza no cliente com `mermaid.run()` (fala do bloco `<script>`, `index.html:181-189`). O alvo **não** emite Mermaid: emite `KinshipPath` estruturado (ramos, MRCA, par de cônjuges) — AD-04 e `discard_log.md` BR-DESCARTAR-005. **As regras de decomposição migram** (`split_path_by_marriage`, `are_spouses`), a tecnologia de desenho não. Ver RISK-011.
- DEV-003: nomes do CSV e motivos exibidos como antes; a fonte dos nomes é a API, não a `datalist`.
- DEV-009: contrato HTTP.

---

## Componente global: SCR-G01 — Bloco de alerta (estado de sucesso)

**Origem**: `analisador-genealogico/templates/index.html:34-39`
**Modo aplicado**: literal
**Componentes do design-system**: [`Alert` (variante success)]
**Pontos de interpolação**: `{{message}}`
**Transições de saída**: [dispensar → mesma tela]
**Tela crítica?**: não

### Especificação

```yaml
spec.kind: route-component
spec.scope: global (aparece em SCR-001..SCR-005)
spec.states: [success]
spec.legacy_origin: "analisador-genealogico/templates/index.html:34-39"
spec.render_condition:
  legacy_expression: "{% if message %} com success == true"
  source: "payload de resposta do backend"
spec.component:
  component: Alert
  variant: success
  dismissible: true
  legacy_origin: "index.html:35-38"
  content:
    text: "{{message}}"
  dismiss_control:
    component: Button
    kind: close
    aria_label: "Fechar"
    legacy_aria_label: "Close"
    deviation: DEV-005
spec.state_messages:
  success: "{{message}}"
spec.deviations: [DEV-005]
```

> ⚠️ **DEV-005 — revisão linguística autorizada.** O legado usa `aria-label="Close"`, em inglês, num produto pt-BR (`index.html:37`). A decisão `screen_modernization_decision.md` § Revisão linguística autorizada registra aprovação explícita do usuário para corrigir para **"Fechar"**. É a **única** alteração de texto permitida em todo o modo literal.

---

## Componente global: SCR-G02 — Bloco de alerta (estado de erro)

**Origem**: `analisador-genealogico/templates/index.html:34-39`
**Modo aplicado**: literal
**Componentes do design-system**: [`Alert` (variante danger)]
**Pontos de interpolação**: `{{message}}`
**Transições de saída**: [dispensar → mesma tela]
**Tela crítica?**: sim (é o canal de todas as mensagens de erro congeladas)

### Especificação

```yaml
spec.kind: route-component
spec.scope: global (aparece em SCR-001..SCR-005)
spec.states: [error]
spec.legacy_origin: "analisador-genealogico/templates/index.html:34-39"
spec.render_condition:
  legacy_expression: "{% if message %} com success == false (else da expressao ternaria)"
  source: "payload de resposta do backend / exception handler"
spec.component:
  component: Alert
  variant: danger
  dismissible: true
  legacy_origin: "index.html:35-38"
  content:
    text: "{{message}}"
  dismiss_control:
    component: Button
    kind: close
    aria_label: "Fechar"
    legacy_aria_label: "Close"
    deviation: DEV-005
spec.state_messages:
  error: "{{message}}"
spec.known_messages:
  # Todas as mensagens de servidor (BR-MIGRAR-028). Preservar literais.
  - "Nenhum arquivo GEDCOM enviado."
  - "Nenhum arquivo selecionado."
  - "Seu nome 'X' não foi encontrado no GEDCOM."
  - "Por favor, carregue o arquivo CSV de matches."
  - "Pessoa 1 'X' não encontrada."
  - "Pessoa 2 'X' não encontrada."
  - "Nenhuma conexão encontrada entre 'X' e 'Y'."
  - "{{mensagem de exceção de parsing}}"
spec.deviations: [DEV-005, DEV-009]
```

> ⚠️ **Este componente é o ponto onde a paridade textual é mais crítica.** O legado concentra **todas** as mensagens de erro aqui, renderizadas no servidor com status HTTP `200` sempre. No alvo o **status passa a ser semântico** (DEV-009), mas o **texto** precisa ser idêntico — são os literais que os `parity_tests/` vão asserir.

---

## Componente global: SCR-G03 — Indicador de carregamento

**Origem**: `analisador-genealogico/templates/index.html:109-112` (markup) e `:191-196` (comportamento)
**Modo aplicado**: literal (comportamento parcialmente modernizado — ver DEV-010)
**Componentes do design-system**: [`Spinner`]
**Pontos de interpolação**: nenhum (texto fixo)
**Transições de saída**: [ocultar ao concluir a operação]
**Tela crítica?**: não

### Especificação

```yaml
spec.kind: route-component
spec.scope: global
spec.states: [loading]
spec.legacy_origin: "analisador-genealogico/templates/index.html:109-112 (markup), :191-196 (comportamento)"
spec.component:
  component: LoadingIndicator
  tokens: [size.spinner]
  legacy_origin: "index.html:109-112"
  children:
    - component: Spinner
      variant: border
      tokens: [color.btn-primary]
      legacy_origin: "index.html:110"
      accessibility:
        visually_hidden_text: "Analisando..."
        note: "texto real do legado; preservar"
    - component: Paragraph
      content:
        text: "Analisando... Isso pode levar alguns segundos."
      legacy_origin: "index.html:111"
spec.legacy_behavior:
  trigger: "submit de QUALQUER formulario (index.html:191-196)"
  effect:
    - "exibe #loading (display: block)"
    - "OCULTA #results-area inteira (display: none)"
  note: "Consequencia: submeter um novo formulario apaga os resultados anteriores da tela."
spec.target_behavior:
  # O comportamento de ocultar TODA a regiao de resultados e um defeito: o usuario
  # perde os resultados anteriores. Ver DEV-010 (proposto como modernizacao).
  proposal: "loading local ao formulario submetido; resultados anteriores permanecem visiveis"
  deviation: DEV-010
spec.deviations: [DEV-010]
```

### Pontos de divergência aceitos

- **DEV-010** ✅ **APROVADA** (2026-09-28T03:24:30Z) — o comportamento do legado (`index.html:191-196`) **ocultava a região de resultados inteira** a cada submit, fazendo o usuário perder a análise anterior. **Decisão**: loading **local** ao formulário submetido, preservando os resultados anteriores visíveis. O legado usa um `querySelectorAll('form')` global; no alvo o loading é escopado ao formulário submetido. Passa a ser divergência aceita; o Inspector deve asserir sobre a **presença do estado de loading**, **não** sobre a ocultação de `#results-area`.

---

# Grupo B — Telas novas em modo MODERNIZADO

> **Estas telas não existem no legado.** O modo literal é impossível para elas por construção — não há origem a copiar. Foram derivadas da arquitetura aprovada (`target_architecture.md`) e das waves do `cutover_plan.md`. Todas declaram explicitamente os 4 estados (idle, loading, error, success), conforme exigido pelo modo modernizado.

## Tela: SCR-006 — Autenticação (login e cadastro)

**Origem**: *(nova — não existe no legado)*
**Modo aplicado**: modernizado
**Componentes do design-system**: [`PageLayout`, `Card`, `FormField`, `Button`, `Alert`]
**Pontos de interpolação**: `{{email}}`, `{{error_message}}`
**Transições de saída**: [login bem-sucedido → SCR-007; cadastro → SCR-008 (consentimento)]
**Tela crítica?**: sim (fronteira de isolamento — BC-01)

### Especificação

```yaml
spec.kind: route-component
spec.route: /login, /register
spec.layout: PublicLayout
spec.states: [idle, loading, error, success]
spec.origin: "nova — exigida por BC-01 (Identidade e Tenancy); cutover_plan.md Onda 3"
spec.legacy_origin: null
spec.component:
  component: AuthPage
  children:
    - component: PageTitle
      content: "Entrar"        # texto NOVO — nao ha legado
    - component: AuthForm
      submit_event: auth.login
      api: "POST /api/auth/sessions"
      children:
        - component: FormField
          kind: email
          name: email
          label: "E-mail"
          required: true
        - component: FormField
          kind: password
          name: password
          label: "Senha"
          required: true
    - component: Link
      label: "Criar conta"
      target: /register
spec.state_messages:
  loading: "Entrando..."
  error: "{{error_message}}"
  success: "Autenticado."
spec.notes:
  - "Esta tela NAO tem texto congelado a preservar — nao havia autenticacao no legado (domain.md §4)."
  - "Apos autenticar, o estado de SCR-001 vs SCR-002 passa a depender do usuario autenticado."
```

---

## Tela: SCR-007 — Minhas árvores (listagem, seleção e reenvio)

**Origem**: *(nova — substitui o `gedcom_filename` oculto do legado)*
**Modo aplicado**: modernizado
**Componentes do design-system**: [`PageLayout`, `Card`, `Table` ou `List`, `Button`, `Alert`, `EmptyState`]
**Pontos de interpolação**: `{{tree.display_name}}`, `{{tree.person_count}}`, `{{tree.created_at}}`
**Transições de saída**: [selecionar árvore → SCR-002; enviar nova → SCR-001; ver análises → SCR-010]
**Tela crítica?**: sim (substitui o mecanismo de identificação de árvore da UI legada)

### Especificação

```yaml
spec.kind: route-component
spec.route: /trees
spec.layout: AppLayout
spec.states: [idle, loading, error, success]
spec.origin: "nova — resolve DEV-002 (gedcom_filename oculto) e o requisito de multiusuario (BC-02)"
spec.legacy_origin: null
spec.component:
  component: MyTreesPage
  children:
    - component: PageTitle
      content: "Minhas árvores"
    - component: TreeList
      empty_state:
        component: EmptyState
        message: "Você ainda não carregou nenhuma árvore."
        action:
          label: "Carregar árvore GEDCOM"
          target: SCR-001
      columns:
        - header: "Nome"
          cell: "{{tree.display_name}}"
        - header: "Pessoas"
          cell: "{{tree.person_count}}"
        - header: "Carregada em"
          cell: "{{tree.created_at}}"
      row_actions:
        - label: "Analisar"
          action: "select_tree -> SCR-002"
        - label: "Ver análises"
          action: "SCR-010"
        - label: "Excluir"
          action: "DELETE /api/trees/{tree_id}"
      api: "GET /api/trees"
spec.state_messages:
  loading: "Carregando suas árvores..."
  error: "{{error_message}}"
  success: null
spec.notes:
  - "Toda listagem e escopada por owner_id (AD-02). Um recurso de outro usuario deve retornar 404, nao 403."
```

---

## Tela: SCR-008 — Consentimento e finalidade do tratamento

**Origem**: *(nova — não existe no legado)*
**Modo aplicado**: modernizado
**Componentes do design-system**: [`PageLayout`, `Card`, `Checkbox`, `Button`, `Alert`, `Disclosure`]
**Pontos de interpolação**: `{{consent.text_version}}`
**Transições de saída**: [conceder → SCR-007; recusar → logout]
**Tela crítica?**: **sim — bloqueante** (sem consentimento registrado, nenhuma árvore pode ser criada)

### Especificação

```yaml
spec.kind: route-component
spec.route: /consent
spec.layout: PublicLayout
spec.states: [idle, loading, error, success]
spec.origin: "nova — BC-05; BR-HUMANA-007 (opcao 2); cutover_plan.md Onda 5 (PRE-REQUISITO DE GO-LIVE)"
spec.legacy_origin: null
spec.component:
  component: ConsentPage
  children:
    - component: PageTitle
      content: "Consentimento para tratamento de dados genéticos"
    - component: ConsentText
      interpolation: "{{consent.text_version}}"
      note: "Conteudo juridico a ser definido pelo usuario — NAO inventar aqui"
    - component: Checkbox
      name: consent_granted
      label: "Li e concordo com o tratamento dos meus dados genéticos para as finalidades descritas."
      required: true
    - component: Button
      label: "Continuar"
      action: "POST /api/consent"
      disabled_until: consent_granted
spec.state_messages:
  loading: "Registrando consentimento..."
  error: "{{error_message}}"
  success: "Consentimento registrado."
spec.blocking_rule:
  description: "Sem consent_record, nenhuma arvore ou analise pode ser criada (invariante I-2 de AGG-03)."
  enforced_at: "backend — a UI apenas orienta"
spec.notes:
  - "⚠️ O TEXTO do consentimento e uma decisao de negocio que o usuario ainda NAO declarou (base legal, finalidade, prazo de retencao). Esta spec define a ESTRUTURA da tela, nao o conteudo juridico."
```

---

## Tela: SCR-009 — Conta e dados (retenção, exportação e exclusão)

**Origem**: *(nova — não existe no legado)*
**Modo aplicado**: modernizado
**Componentes do design-system**: [`PageLayout`, `Card`, `Button`, `Alert`, `ConfirmDialog`, `DangerZone`]
**Pontos de interpolação**: `{{retention.days}}`, `{{account.email}}`
**Transições de saída**: [excluir → logout; exportar → download]
**Tela crítica?**: sim (direito de exclusão — obrigação LGPD/GDPR)

### Especificação

```yaml
spec.kind: route-component
spec.route: /account
spec.layout: AppLayout
spec.states: [idle, loading, error, success]
spec.origin: "nova — BC-05; BR-HUMANA-007 (direito de exclusao); cutover_plan.md Onda 5"
spec.legacy_origin: null
spec.component:
  component: AccountPage
  children:
    - component: PageTitle
      content: "Conta e dados"
    - component: Section
      title: "Retenção"
      children:
        - component: Text
          content: "Suas árvores e análises são mantidas por {{retention.days}} dias."
        - component: FormField
          kind: select
          name: retention_days
          label: "Prazo de retenção"
          options: ["30", "90", "180", "365"]
    - component: Section
      title: "Exportação"
      children:
        - component: Button
          label: "Exportar meus dados"
          action: "GET /api/account/export"
    - component: Section
      title: "Exclusão"
      variant: danger
      children:
        - component: Text
          content: "A exclusão remove permanentemente suas árvores, arquivos e análises. Esta ação não pode ser desfeita."
        - component: Button
          variant: danger
          label: "Excluir minha conta e meus dados"
          action: "opens ConfirmDialog"
        - component: ConfirmDialog
          event: "DELETE /api/account"
          requires: "confirmacao explicita do usuario"
spec.state_messages:
  loading: "Processando..."
  error: "{{error_message}}"
  success: "Solicitação registrada."
spec.notes:
  - "A exclusao precisa remover TODAS as arvores, arquivos e analises do usuario (invariante I-3 de AGG-03). Nao pode restar dado genetico orfao."
  - "access_audit sobrevive a exclusao por design (ON DELETE SET NULL) — ver target_data_model.md."
```

---

## Tela: SCR-010 — Histórico de análises

**Origem**: *(nova — substitui `results_list` volátil do legado)*
**Modo aplicado**: modernizado
**Componentes do design-system**: [`PageLayout`, `Card`, `Table`, `Badge`, `Button`, `EmptyState`]
**Pontos de interpolação**: `{{analysis.created_at}}`, `{{analysis.accepted_count}}`, `{{analysis.skipped_count}}`
**Transições de saída**: [abrir análise → SCR-005 (resultados persistidos)]
**Tela crítica?**: não

### Especificação

```yaml
spec.kind: route-component
spec.route: /trees/{tree_id}/analyses
spec.layout: AppLayout
spec.states: [idle, loading, error, success]
spec.origin: "nova — resolve BR-DESCARTAR-002 (resultados eram locais a requisicao e nao persistiam)"
spec.legacy_origin: null
spec.component:
  component: AnalysisHistoryPage
  children:
    - component: PageTitle
      content: "Histórico de análises"
    - component: AnalysisList
      empty_state:
        component: EmptyState
        message: "Nenhuma análise realizada para esta árvore."
      columns:
        - header: "Data"
          cell: "{{analysis.created_at}}"
        - header: "Pessoa-raiz"
          cell: "{{analysis.root_name_input}}"
        - header: "Conexões"
          cell:
            component: Badge
            variant: success
            content: "{{analysis.accepted_count}}"
        - header: "Descartados"
          cell:
            component: Badge
            variant: secondary
            content: "{{analysis.skipped_count}}"
      row_actions:
        - label: "Abrir resultados"
          action: "SCR-005 com analysis_id"
      api: "GET /api/trees/{tree_id}/dna-analyses"
spec.state_messages:
  loading: "Carregando histórico..."
  error: "{{error_message}}"
  success: null
spec.notes:
  - "Reabrir uma analise antiga deve renderizar os resultados PERSISTIDOS, nao recalcular. O total_cm persistido e a autoridade (AD-03)."
```

---

## Apêndice: rastreabilidade ao inventário

| Tela do `target_screens.md` | Origem em `_reversa_sdd/ui/inventory.md` | Origem em `_reversa_sdd/screens/inventory.json` |
|---|---|---|
| SCR-001 | **ausente** — `ui/inventory.md` não existe (DEV-007) | `SCR-001` |
| SCR-002 | **ausente** — idem | `SCR-002` |
| SCR-003 | **ausente** — idem | `SCR-003` |
| SCR-004 | **ausente** — idem | `SCR-004` |
| SCR-005 | **ausente** — idem | `SCR-005` |
| SCR-G01 | **ausente** — não catalogado na Fase 1 (chrome compartilhada) | `globalElements[0]` (variante success) |
| SCR-G02 | **ausente** — idem | `globalElements[0]` (variante danger) |
| SCR-G03 | **ausente** — idem | `globalElements[1]` |
| SCR-006 | **não aplicável** — tela nova, não existe no legado | **não aplicável** |
| SCR-007 | **não aplicável** — tela nova | **não aplicável** |
| SCR-008 | **não aplicável** — tela nova | **não aplicável** |
| SCR-009 | **não aplicável** — tela nova | **não aplicável** |
| SCR-010 | **não aplicável** — tela nova | **não aplicável** |

> ⚠️ A coluna `ui/inventory.md` está integralmente "ausente" porque o artefato **não existe** no projeto (EC-18). O inventário de referência é `_reversa_sdd/screens/inventory.json`, construído a partir do código-fonte legado e registrado como DEV-007.

## Notas

- **Nenhum texto foi inventado nas telas literais.** Todos os literais vêm de `inventory.json § textInventory`. A única alteração autorizada é DEV-005.
- **Nas telas modernizadas, o texto É novo** — porque não havia texto antes. Elas não estão sujeitas à invariante de paridade textual, e isso está declarado em cada seção.
- **A invariante de dependência do núcleo vale para este artefato indiretamente**: o componente de grafo (SCR-005) consome `KinshipPath` estruturado, que é produzido por `core/decomposition.py`. **Se a implementação do grafo recalcular a decomposição no cliente em vez de consumir a estrutura do domínio, RISK-011 se materializa** (perda da regra de negócio junto com a tecnologia). Esta é a instrução mais importante deste documento para o codificador de front-end.
- **Bloqueio de handoff**: **nenhum**. Todas as 10 deviations estão `aprovado` — as 9 primeiras derivam de decisões humanas de gates anteriores, e DEV-010 foi decidida em 2026-09-28T03:24:30Z.
