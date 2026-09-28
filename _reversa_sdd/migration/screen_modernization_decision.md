---
schemaVersion: 1
generatedAt: 2026-09-28T03:16:40Z
reversa:
  version: "1.2.58"
kind: screen_modernization_decision
producedBy: screen-translator
decidedBy: Adriano
decidedAt: 2026-09-28T03:20:10Z
mode: hybrid
sourcePlatform: server-rendered-jinja2-bootstrap
targetPlatform: web-spa
hash: "sha256:d2e5e382eb1d1f0f48726bcc4047a428e77315cb27168bf79ec7894d29389a5f"
---

# Decisão de Modernização de Telas

> Decisão consciente sobre como traduzir as telas do sistema legado: paridade observável byte-a-byte, redesign idiomático para a plataforma alvo, ou combinação tela-a-tela.
> Este artefato é leitura obrigatória do próprio Screen Translator (para gerar `target_screens.md`), do Inspector (para construir parity tests adequados ao modo) e do agente de codificação.

## Contexto

- **Plataforma origem detectada**: `server-rendered-jinja2-bootstrap`
- **Confiança**: 🟢 CONFIRMADO
  - **Evidências**: `inventory.md` §3 e §4 (`templates/index.html` — "Interface do usuário (Upload de GEDCOM/CSV, seletor de pessoa raiz, formulário de busca de caminho direta/indireta, exibição de resultados e alertas)" com **HTML5, Bootstrap 5, Mermaid.js**); `architecture.md` §1 (*"renderização server-side (Jinja2 + Bootstrap 5)"*); `dependencies.md` §2 (Flask, com "renderização de templates Jinja2").
  - **Leitura direta do fonte legado** (read-only): `analisador-genealogico/templates/index.html`, 200 linhas. Bootstrap **5.3.3** e Mermaid **10** carregados por CDN (`index.html:7-8`), `{% %}`/`{{ }}` de Jinja2, tags `<form method="POST">` com `<input type="hidden" name="action">`.
  - **Sem jQuery e sem AJAX**: a única busca no arquivo retorna dois `addEventListener` (`index.html:181` e `:192`) — um para inicializar Mermaid e outro para exibir o spinner no `submit`. **Não há `$.ajax`, `fetch`, `XMLHttpRequest` nem `onclick` inline.** Isso é relevante: o legado **não é** `html-legacy-jquery`; é server-rendered clássico com *progressive enhancement* mínimo.
- **Plataforma alvo**: `web-spa` (React + TypeScript), conforme `migration_brief.md` § Stack alvo e `target_architecture.md` (`presentation/ — SPA React + TypeScript`).
- **Telas inventariadas**: **5** (SCR-001 a SCR-005) — origem `_reversa_sdd/screens/inventory.json`.
- **Origem do inventário**: construído a partir do **código-fonte legado** (`templates/index.html`), porque `_reversa_sdd/ui/inventory.md` **está ausente** (caso de borda EC-18). `_reversa_sdd/design-system/` também **está ausente** (caso de borda EC-17), portanto os tokens serão derivados do próprio template em `tokens-derived.md` na Fase 2, e não de um design system catalogado.
- **Adapter aplicado**: `html_legacy__spa` — ⚠️ **usado como proxy**. Ver § Notas.
- **Formato de spec resultante**: `route-component` (conforme `adapter-pairs.md` § Formato de spec por kind: `route-component` é o formato de "web modernizado a partir de server-rendered").

> **Nota sobre a contagem de telas.** O legado tem **uma única rota** (`GET /` e `POST /`), mas ela materializa **5 unidades de interface distintas**: 2 estados mutuamente exclusivos (antes e depois do GEDCOM carregado), 2 painéis de aba e 1 região de resultados com 3 blocos independentes. Inventariar como 1 tela perderia a informação de que SCR-001 e SCR-002 são estados exclusivos e que SCR-005 tem três blocos condicionalmente independentes. Também **não** foi inventariada `static/graph_path_search.html` (pyvis) como tela: é um **artefato de saída gerado**, não uma interface com entrada de usuário — está coberto por SCR-005 (bloco de grafo).

## Modos avaliados

### Modo: literal
- **Definição**: paridade observável entre legado e novo — mesmos textos, mesma estrutura, mesma hierarquia; o CSS de origem é substituído por tokens de layout, mas o conteúdo textual é **idêntico** (`adapter-pairs.md` § `component-tree`: *"Conteúdo textual é preservado literalmente. Diff de strings deve ser zero, ignorando espaços trailing."*).
- **Trade-offs**:
  - **Custo de implementação: MÉDIO.** Não é cópia trivial: a origem é Jinja2 server-rendered e o alvo é React com dados vindos de API, então toda a estrutura precisa ser re-expressa em JSX e ligada a estado — mas a *decisão de design* é zero (tudo já está decidido no legado).
  - **Fidelidade visual: ALTA** para conteúdo e estrutura; **MÉDIA** para estilo (Bootstrap 5 semântico → tokens do alvo).
  - **Viabilidade de parity tests construtivos: SIM, e é o modo com melhor viabilidade.** A comparação é objetiva: diff textual por tela (deve ser zero) + mesmos campos + mesmas mensagens de erro.
  - **Aceitação esperada do usuário final: MÉDIA.** O usuário recebe uma UI que funciona, mas que carrega todas as limitações de UX do legado.
  - **Débito técnico futuro: MÉDIO.** O React herdará decisões de layout server-side (abas, spinner global, `datalist`) que não são idiomáticas em SPA.
- **Recomendado**: **não**
- **Justificativa**: o modo literal **congela defeitos de UX que a migração tem a oportunidade de corrigir** — e, no caso deste legado, alguns desses "defeitos" são **vazamentos de detalhe interno na interface**. Exemplos concretos e verificáveis, todos do código lido:
  - `index.html:68` e `:87` — o campo `gedcom_filename` é injetado como `<input type="hidden">`. O **nome do arquivo do cliente** é o identificador da árvore na UI. Isso é consequência direta de BR-DESCARTAR-003 (nome do cliente como chave), **já descartado** por decisão sua. Replicar isso literalmente reintroduziria na UI um mecanismo que o backend abandonou.
  - `index.html:102-106` — a `datalist` com **todos** os nomes do GEDCOM é embutida no HTML a cada render. Com árvores grandes isso degrada a página; e em contexto multiusuário é uma lista de nomes de pessoas que trafega por completo.
  - `index.html:37` — o botão de fechar alerta tem `aria-label="Close"` **em inglês** num produto pt-BR.
  - `index.html:130,133-135,158` — a região de *matches descartados* aparece com **indentação por tabs** misturada ao restante do arquivo (por espaços), sinal de edição manual posterior. Em modo literal, essa estrutura seria preservada por fidelidade — fidelidade a um acidente.
  - O **spinner global** (`index.html:109-112`, `:191-196`) oculta a `#results-area` inteira no submit: o usuário perde os resultados anteriores ao submeter um novo formulário. É comportamento questionável que o modo literal obrigaria a reproduzir.
- **Consequência de escolher literal**: a métrica primária do brief (paridade) ganharia um instrumento de comparação mais forte na UI, **mas** o produto nasceria com os vazamentos acima. E o brief já registra que **as necessidades dos usuários externos não foram validadas** (AMB-002) — apostar em congelar a UI atual como "a UI certa" seria assumir que o não-validado está correto.

### Modo: modernizado
- **Definição**: redesign idiomático para React, preservando **informação, fluxo e – obrigatoriamente – todo o conteúdo textual**; re-expressando hierarquia, layout e interação.
- **Trade-offs**:
  - **Custo de implementação: ALTO.** Cada uma das 5 unidades precisa ser redesenhada; a Fase 2 deve declarar explicitamente os 4 estados (idle, loading, error, success) por tela, o que o legado não tem.
  - **Fidelidade visual: BAIXA** (por definição). Fidelidade **semântica e textual: ALTA** — e é a que sustenta a paridade de negócio.
  - **Viabilidade de parity tests construtivos: PARCIAL.** A comparação deixa de ser byte-a-byte e passa a ser **contrato semântico**: mesmos textos, mesmos campos, mesmas mensagens de erro, mesmas transições. É verificável, mas exige que o Inspector escreva asserções sobre conteúdo e eventos em vez de sobre bytes — e **não** cobre regressão visual.
  - **Aceitação esperada do usuário final: ALTA** (é o objetivo do redesign).
  - **Débito técnico futuro: BAIXO.**
- **Recomendado**: **não como modo único** (ver justificativa em híbrido).
- **Justificativa**: é o modo correto para as telas **novas** que a arquitetura alvo exige e que **não existem no legado** — e essa é a descoberta central da Fase 1. Contando pelas waves do `cutover_plan.md`, a arquitetura aprovada precisa de telas que o inventário legado **não contém**: autenticação e cadastro (Onda 3), listagem e seleção de árvores (Onda 3, substituindo o `gedcom_filename` escondido), consentimento e finalidade (Onda 5), retenção e exclusão de conta (Onda 5). **Essas telas não têm legado a copiar** — o modo literal é inaplicável a elas por construção. Como o escopo é "integral" e o objetivo é SaaS multiusuário, o produto final é majoritariamente modernizado de qualquer forma.

### Modo: híbrido
- **Definição**: parte das telas em literal, parte em modernizado, com **listas explícitas** (obrigatórias, conforme EC-12).
- **Trade-offs**:
  - **Custo de implementação: ALTO** (é o custo do modernizado + o custo de manter duas convenções de UI no mesmo produto).
  - **Fidelidade visual mista**: as telas de análise ficam próximas do legado; as novas seguem o design do produto. Exige disciplina para que a mistura não pareça dois produtos colados.
  - **Viabilidade de parity tests**: **mista e declarada por tela** — as telas literais admitem comparação textual estrita; as modernizadas, apenas contrato semântico. O Inspector precisa de estratégia por tela em `parity_specs.md`.
  - **Custo de manutenção da separação: MÉDIO** — duas convenções coexistem permanentemente, não é transitório.
- **Recomendado**: **SIM — esta é a recomendação do agente.**
- **Justificativa**: é a única opção que separa corretamente **duas populações de tela com naturezas diferentes**, e essa separação é factual, não estética:
  1. **As 5 telas do legado (SCR-001 a SCR-005) são a superfície onde a paridade precisa ser demonstrável.** São elas que produzem as mensagens congeladas (BR-MIGRAR-028), os campos de entrada e as transições que os `parity_tests/` podem asserir. Manter essas 5 em **literal** dá ao Inspector um alvo de comparação **objetivo** — diff textual zero — na exata superfície onde a métrica primária do brief se aplica.
  2. **As telas novas (auth, seleção de árvore, consentimento, retenção) não têm legado.** Literal é impossível; modernizado é a única opção. Listá-las como "modernizado" não é uma escolha de design, é a constatação de que elas não existem no legado.
  3. O híbrido também resolve a tensão da AMB-002 (usuários externos não ouvidos): a superfície **já validada pelo uso real** (as telas de análise, que o usuário usa há tempo) é preservada; a superfície **sem validação nenhuma** (telas de produto que nunca existiram) é onde o redesign acontece — e onde errar é reversível, porque não havia nada antes.
  4. Custo: o "custo de manutenção da separação" é real, mas menor do que parece — as telas literais são **5 unidades de um único fluxo** e tendem a ser estáveis (o núcleo que as alimenta está congelado).

## Decisão

- **Modo escolhido**: **híbrido**
- **Justificativa do humano**: selecionou a opção recomendada pelo agente (5 telas legadas em literal + 5 telas novas em modernizado), sem texto adicional. Justificativa reconstruída pelo orquestrador a partir da análise apresentada, sujeita a correção:
  - Preserva a superfície de paridade onde a métrica primária do brief se aplica (as 5 telas legadas), dando ao Inspector um alvo de comparação **objetivo** — diff textual zero.
  - Reconhece o fato de que as telas novas (auth, árvores, consentimento, conta, histórico) **não existem no legado** e portanto não admitem modo literal — o modernizado não é uma escolha estética nelas, é a única opção possível.
  - Redesenha apenas a superfície **sem validação de usuário** (AMB-002), onde errar é reversível por não haver nada antes; e preserva a superfície já validada pelo uso real.
- **Alternativas descartadas**:
  - **Literal puro** — descartado por congelar na UI defeitos verificáveis no código legado: o `gedcom_filename` como `<input type="hidden">` (identificador de árvore exposto ao cliente, consequência de BR-DESCARTAR-003 já descartado no backend), a `datalist` embutindo todos os nomes do GEDCOM no HTML, e o spinner global que oculta os resultados anteriores (`index.html:109-112,191-196`).
  - **Modernizado puro** — descartado por remover a superfície de comparação objetiva da UI e por redesenhar áreas já validadas pelo uso, sem que usuários externos tenham sido ouvidos (AMB-002).
- **Decidido em**: 2026-09-28T03:20:10Z
- **Decidido por**: Adriano

### Revisão linguística autorizada

- **Autorizada**: **parcial** — especificamente a correção do `aria-label="Close"` para **"Fechar"** (DEV-005, `tipo=correcao`). Registro explícito conforme exigido pela regra absoluta do agente (*"Revisão linguística só com aprovação explícita registrada na decisão"*).
- **Não autorizada**: qualquer outra revisão de texto. Todo o restante do conteúdo textual permanece **literal**, incluindo acentuação, pontuação e eventuais imprecisões. O diff de strings deve ser zero fora do item acima.

### Em modo híbrido, listas explícitas (obrigatórias)

> Conforme EC-12, listas vazias bloqueiam a Fase 2. As listas abaixo são a **proposta do agente** para o modo híbrido; se você escolher híbrido, confirme-as ou ajuste-as.

**Telas em modo literal** (as 5 do legado — superfície de paridade):
- **SCR-001** — Estado inicial: upload GEDCOM (`index.html:41-52`)
- **SCR-002** — Estado carregado: hub com 2 abas (`index.html:53-61`)
- **SCR-003** — Aba "Buscar Conexão no GEDCOM" (`index.html:64-81`)
- **SCR-004** — Aba "Analisador de DNA" (`index.html:83-100`)
- **SCR-005** — Áreas de resultado: DNA + descartados + caminho (`index.html:116-174`)

**Telas em modo modernizado** (novas, exigidas pela arquitetura alvo — sem legado correspondente):
- **SCR-006** *(nova)* — Autenticação: login e cadastro *(Onda 3; BC-01)*
- **SCR-007** *(nova)* — Minhas árvores: listagem, seleção e reenvio *(Onda 3; substitui o `gedcom_filename` oculto)*
- **SCR-008** *(nova)* — Consentimento e finalidade do tratamento *(Onda 5; BC-05; BR-HUMANA-007)*
- **SCR-009** *(nova)* — Conta e dados: retenção, exportação e exclusão *(Onda 5; BC-05; direito de exclusão)*
- **SCR-010** *(nova)* — Histórico de análises *(Onda 3; substitui `results_list` volátil — BR-DESCARTAR-002)*

> **As telas SCR-006 a SCR-010 não estão inventariadas em `inventory.json`** porque o inventário cobre **o legado**. Elas são registradas aqui como a contraparte moderna obrigatória da arquitetura aprovada e devem ser criadas na Fase 2. Se você escolher **modernizado puro**, SCR-001 a SCR-005 também passam para o desenho novo e as listas acima deixam de ter função.

> **Reconciliação de contagem (Fase 1 → Fase 2)**: a lista "literal" acima contém as **5 telas lógicas** do legado. Na Fase 2, a especificação executável dessas 5 telas produziu **8 entradas** (4 páginas: SCR-001, SCR-002, SCR-003+004 como o hub de abas, SCR-005; mais **4 componentes globais**: o bloco de alerta em dois estados e o indicador de carregamento em dois estados — `index.html:34-39` e `:109-112`). Componentes globais **não estavam no inventário da Fase 1** porque o inventário catalogou telas e estados, não a chrome compartilhada. A contagem final é **8 literais + 5 modernizadas = 13 entradas** em `target_screens.md`. Registrado para que a diferença não seja lida como inconsistência.

## Implicações pendentes para a Fase 2

| Etapa | Implicação | Como honrar |
|---|---|---|
| Geração de `target_screens.md` | O formato de spec é `route-component` (web modernizado a partir de server-rendered), com `spec.route`, `spec.layout` e `spec.api_changes`. | Uma seção por tela (SCR-001..SCR-005 no modo literal; SCR-006..SCR-010 no modernizado). Declarar `spec.legacy_origin` como `templates/index.html:<linha>` em todas. |
| Geração de `target_screens.md` | **A superfície de API substitui o `gedcom_filename` oculto.** No legado, o identificador da árvore viaja como `<input type="hidden">` (`index.html:68,87`). No alvo, o contrato é por `tree_id` e escopo por sessão. | Registrar em `spec.api_changes` a mudança de contrato (campo oculto → `tree_id` resolvido por sessão/rota). É mudança de contrato HTTP e deve ser asserível pelo Inspector. |
| Geração de `target_screens.md` | **A `datalist` de todos os nomes não deve ser embutida no HTML.** | Prever endpoint de busca/autocomplete com paginação para SCR-003 e SCR-004. Registrar como deviation `tipo=modernizacao` se o modo for literal (é divergência consciente de mecanismo). |
| Geração de `target_screens.md` | **Estados por tela são obrigatórios em modo modernizado** (idle, loading, error, success), e o legado só tem `idle` + um spinner global. | Declarar os 4 estados para SCR-006..SCR-010. Para SCR-001..SCR-005 em literal, preservar os estados que o legado tem e registrar como deviation a ausência dos demais. |
| Captura de golden files | **O oráculo legado é executável** (Flask local) — diferente dos casos usuais de TUI/desktop. É possível capturar HTML renderizado por tela. | Emitir `manifest.yaml` com o comando sugerido por tela. ⚠️ A captura exige um GEDCOM de fixture e, para SCR-002..SCR-005, um arquivo carregado — o determinismo depende de fixtures fixos. Ver § Notas. |
| Tokens do design-system | `_reversa_sdd/design-system/` **ausente** (EC-17). Não há `tokens.md` para mapear. | Criar `_reversa_sdd/design-system/tokens-derived.md` a partir do próprio `index.html` (cores `#f8f9fa`, `#dee2e6`, `#fafafa`; `.375rem`; escala tipográfica do Bootstrap 5) e marcar cada token como derivado. |
| Conteúdo textual | Preservar literal salvo aprovação explícita de revisão linguística. | **Invariante em qualquer modo.** O inventário textual está em `inventory.json` § `textInventory` (29 strings de UI + 9 mensagens de servidor). O diff deve ser zero. Inclui o `aria-label="Close"` em inglês — corrigir só com aprovação explícita registrada aqui (seria `tipo=correcao`, EC-11). |

## Implicações para o Inspector

- **Estratégia de paridade**:
  - **Modo literal (SCR-001..SCR-005, se híbrido ou literal)**: paridade **textual estrita** — todo literal de `inventory.json § textInventory.strings` e `§ textInventory.serverMessages` deve aparecer sem alteração; mesmos campos, mesmas validações `required`, mesmas transições. Comparação contra os golden files quando capturados.
  - **Modo modernizado (SCR-006..SCR-010, ou todas se modernizado puro)**: **contrato semântico** — presença e semântica dos campos, mensagens por estado, transições e endpoints. **Sem** comparação visual.
  - **Modo híbrido**: estratégia **mista, declarada por tela** em `parity_specs.md`, exatamente como acima.
- **Deviations conhecidas a propagar**: ver `screen_deviation_log.md` — **10 registradas** (todas **aprovadas**; **0 pendentes**). As pré-identificadas nesta Fase 1 foram:
  - **DEV-001** `tipo=plataforma` — adapter `html_legacy__spa` aplicado como proxy para o par real `server-rendered-jinja2-bootstrap` → `web-spa`, ausente da tabela v1.
  - **DEV-002** `tipo=modernizacao` — `gedcom_filename` como `<input type="hidden">` substituído por `tree_id` resolvido por sessão (consequência de BR-DESCARTAR-003).
  - **DEV-003** `tipo=modernizacao` — `datalist` com todos os nomes substituída por busca paginada.
  - **DEV-004** `tipo=modernizacao` — ⚠️ **reclassificada na Fase 2**: passou a designar a substituição da **string Mermaid gerada no servidor** por `KinshipPath` estruturado (AD-04 / BR-DESCARTAR-005). É a deviation de maior risco (RISK-011).
  - **DEV-005** `tipo=correcao` — `aria-label="Close"` em inglês corrigido para **"Fechar"**. Revisão linguística **autorizada explicitamente** pelo usuário (ver § Revisão linguística autorizada). Status: **aprovada**.
  - **DEV-006** `tipo=tecnica` — tokens derivados de `index.html` por ausência de `design-system/` (EC-17).
  - **DEV-007** `tipo=tecnica` — inventário construído do código-fonte por ausência de `ui/inventory.md` (EC-18).
  - **DEV-008** `tipo=tecnica` — o legado **não define família tipográfica**; qualquer fonte no alvo é decisão nova, não tradução.
  - **DEV-009** `tipo=plataforma` — `POST /` com campo `action` e `status 200 (sempre)` substituído por endpoints REST com status semântico (BR-DESCARTAR-004).
  - **DEV-010** ✅ **APROVADA** (2026-09-28T03:24:30Z) — o spinner global do legado **ocultava a região de resultados inteira** a cada submit (`index.html:191-196`), fazendo o usuário perder resultados anteriores. **Decisão**: loading **local** ao formulário submetido, preservando os resultados anteriores. A paridade de SCR-G03 passa a asserir sobre a presença do loading, não sobre a ocultação.

- ⚠️ **Uma implicação que o Inspector precisa saber e que não é óbvia**: o layout legado de SCR-001 e SCR-002 é **mutuamente exclusivo** (`{% if not gedcom_filename %} ... {% else %}`, `index.html:41` e `:53`) e o estado é decidido **no servidor**, não no cliente. Em uma SPA, esse estado precisa vir do backend (existe árvore?) e ser refletido como **estado de tela**, não como duas telas independentes. Se a implementação tratar SCR-001 e SCR-002 como rotas separadas sem essa origem de estado, o comportamento do usuário muda.

## Notas

- **⚠️ Lacuna de adapter (EC-01 parcial, resolvida por proxy).** O par real detectado — `server-rendered-jinja2-bootstrap` → `web-spa` — **não consta na tabela do `adapter-pairs.md` v1**. O mais próximo é `html-legacy-jquery` → `web-spa` (`html_legacy__spa`, formato `route-component`). Apliquei esse adapter como **proxy**, sem improvisar formato, pelos seguintes motivos: (a) o `html_legacy__spa` foi desenhado exatamente para "web server-rendered → SPA", que é o nosso caso, e o `route-component` cobre `spec.route`, `spec.layout` e `spec.api_changes`, que são precisamente as informações em jogo; (b) o legado **não usa jQuery** (verificado), então o nome do adapter é impreciso mas seu **propósito** é idêntico; (c) travar o pipeline com `EC-01` por uma imprecisão nominal, quando a informação necessária está disponível, seria pior que registrar a lacuna. **Registrado como DEV-001** para que o mantenedor do catálogo possa adicionar o par na v2.
- **Duas ausências de pré-requisito do Discovery** (EC-17 e EC-18): `_reversa_sdd/design-system/` e `_reversa_sdd/ui/inventory.md` não existem. Não bloqueei o pipeline porque **as fontes primárias estão disponíveis em modo read-only** (`templates/index.html`, 200 linhas, e `static/graph_path_search.html`), o que é exatamente a mitigação prevista nos dois casos de borda. Ambas as ausências ficam registradas como deviations técnicas (DEV-006, DEV-007) para que o codificador saiba que os tokens são **derivados**, não catalogados.
- **Sobre a captura de golden files (oráculo legado)**: diferente dos casos típicos do agente (COBOL, Win32, Android), aqui o oráculo é **um servidor Flask que roda localmente**. Isso torna a captura tecnicamente viável para SCR-001 (estado inicial, sem dependência de dados). As telas SCR-002 a SCR-005 exigem um GEDCOM carregado e, para SCR-005, um CSV de matches — o determinismo passa a depender de **fixtures fixos**, que já existem parcialmente (`tests/fixtures/sample_gedcom.py`, `sample_dna.py`; `_reversa_sdd/upload-gedcom/exemplo_familia.ged`). O `manifest.yaml` da Fase 2 deve declarar o comando de captura por tela e as fixtures exigidas. ⚠️ Conforme o SKILL, **não** automatizo o driver de captura em v1 (OQ-02) — emito o manifesto e instruo a execução manual.
- **O legado não foi modificado.** Toda a leitura de `templates/index.html` foi read-only, conforme a regra absoluta do Reversa.
- **Consequência do modo escolhido para o escopo**: se você escolher **híbrido** ou **modernizado**, a Fase 2 produzirá specs para **10 telas** (5 legadas + 5 novas), não para 5. Isso é intencional e reflete o brief (SaaS multiusuário com conformidade) — não é inflação de escopo.
