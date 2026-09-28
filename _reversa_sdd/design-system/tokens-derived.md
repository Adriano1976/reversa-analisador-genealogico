---
schemaVersion: 1
generatedAt: 2026-09-28T03:20:10Z
reversa:
  version: "1.2.58"
kind: design_system_tokens_derived
producedBy: screen-translator
status: derived
hash: "sha256:77d5fe4986bceda2780085f92089afe8864808aade24f4e9d0bf49264f1c4a63"
---

# Tokens Derivados

> ⚠️ **Arquivo derivado, não catalogado.** Foi criado porque `_reversa_sdd/design-system/tokens.md` **não existe** (caso de borda EC-17 do Screen Translator). Os valores abaixo foram extraídos do **código-fonte legado** (`analisador-genealogico/templates/index.html`) e dos defaults do **Bootstrap 5.3.3** que ele carrega por CDN (`index.html:7`).
> Este arquivo é **append-only**: nunca modifica `tokens.md` (que não existe) e nunca deve ser editado para "corrigir" um token catalogado futuro.
> Quando um design system real for definido para o produto, estes tokens devem ser **reconciliados** — não substituídos silenciosamente, para não quebrar a fidelidade das telas em modo literal.

## Origem dos valores

| Fonte | O que forneceu |
|---|---|
| `templates/index.html:9-24` | Bloco `<style>` com 6 regras CSS explícitas (cores e espaçamentos literais) |
| `templates/index.html:7` | Bootstrap 5.3.3 por CDN — classes semânticas (`btn-primary`, `btn-info`, `btn-success`, `alert-success`, `alert-danger`, `card`, `nav-tabs`, `badge bg-success`, `table`) |
| Bootstrap 5.3.3 (defaults) | Valores concretos das cores semânticas referenciadas pelas classes acima |

## Cores

| Token | Valor | Origem | Nota |
|---|---|---|---|
| `color.page-background` | `#f8f9fa` | `index.html:10` (`body { background-color: #f8f9fa; }`) | Literal no legado |
| `color.border-default` | `#dee2e6` | `index.html:15` (`.graph-container { border: 1px solid #dee2e6; }`) | Literal no legado |
| `color.graph-background` | `#fafafa` | `index.html:18` (`.graph-container { background-color: #fafafa; }`) | Literal no legado |
| `color.btn-primary` | Bootstrap default (`#0d6efd`) | `index.html:50,78` (classes `btn-primary`, `btn-info`) | **Herdado**, não literal — depende da versão do Bootstrap |
| `color.btn-info` | Bootstrap default (`#0dcaf0`) | `index.html:78` (classe `btn-info`) | Herdado |
| `color.btn-success` | Bootstrap default (`#198754`) | `index.html:97` (classe `btn-success`) | Herdado |
| `color.alert-success` | Bootstrap default (`#198754` / bg `#d1e7dd`) | `index.html:35` (classe dinâmica `alert-{{ 'success' if success else 'danger' }}`) | Herdado |
| `color.alert-danger` | Bootstrap default (`#dc3545` / bg `#f8d7da`) | `index.html:35` | Herdado |
| `color.text-muted` | Bootstrap default (`#6c757d`) | `index.html:42,65,84,136` (classe `text-muted`) | Herdado |
| `color.text-primary` | Bootstrap default (`#0d6efd`) | `index.html:124` (`<span class="text-primary">`) | Herdado |

> ⚠️ **Distinção importante para a implementação**: as três primeiras cores são **literais no legado** (`#f8f9fa`, `#dee2e6`, `#fafafa`) e portanto fazem parte da fidelidade visual de SCR-005 (`.graph-container`). As demais são **semânticas via Bootstrap** — o valor concreto depende da versão da biblioteca. Se o design system do alvo tiver `color.brand-primary` diferente de `#0d6efd`, as telas legadas **mudam de aparência** em modo literal. Isso é aceitável (modo literal preserva conteúdo/estrutura, não bytes de CSS), mas deve ser registrado como deviation se a diferença for perceptível.

## Espaçamentos e dimensões

| Token | Valor | Origem |
|---|---|---|
| `spacing.card-margin-top` | `1.5rem` | `index.html:11` (`.card { margin-top: 1.5rem; }`) |
| `spacing.tabs-margin-bottom` | `1.5rem` | `index.html:12` (`.nav-tabs { margin-bottom: 1.5rem; }`) |
| `spacing.graph-container-padding` | `1rem` | `index.html:17` (`.graph-container { padding: 1rem; }`) |
| `radius.graph-container` | `.375rem` | `index.html:16` (`.graph-container { border-radius: .375rem; }`) |
| `size.spinner` | `3rem × 3rem` | `index.html:13` (`.spinner-border { width: 3rem; height: 3rem; }`) |

## Tipografia

| Token | Valor | Origem |
|---|---|---|
| `typography.h1` | Bootstrap `h1` (2.5rem, peso 500) | `index.html:32` (`<h1 class="card-title ...">`) |
| `typography.h2` | Bootstrap `h2` (2rem) | `index.html:118,132,165` (`<h2 class="text-center mt-5">`) |
| `typography.h5` | Bootstrap `h5` (1.25rem) | `index.html:121,167` (`<h5>` dentro de `card-header`) |
| `typography.body` | Bootstrap default (1rem, `--bs-body-font-family`) | todo o documento |
| `typography.family` | **Não especificada no legado** — usa o default do Bootstrap (system font stack) | ausência de `font-family` em `index.html:9-24` |

> ⚠️ **Lacuna registrada**: o legado **não define família tipográfica**. Qualquer escolha de fonte no alvo é uma decisão nova, não uma tradução. Marcado como `DEV-008`.

## Componentes do design system referenciados pelas telas em modo literal

| Componente | Uso no legado | Telas |
|---|---|---|
| `PageLayout` | `<div class="container my-5">` + `row justify-content-center` + `col-lg-10` | todas |
| `Card` | `<div class="card shadow-sm">` / `<div class="card">` | SCR-001..SCR-005 |
| `CardBody` / `CardHeader` | `card-body`, `card-header` | SCR-005 especialmente |
| `Alert` | `alert alert-{success\|danger} alert-dismissible fade show` + `btn-close` | global (2 estados) |
| `Tabs` | `nav nav-tabs` + `nav-link` + `tab-content` / `tab-pane` | SCR-002 |
| `FormField` | `mb-3` + `form-label` + `form-control` | SCR-001, SCR-003, SCR-004 |
| `Button` | `btn btn-{primary\|info\|success}` + `d-grid` | SCR-001, SCR-003, SCR-004 |
| `Badge` | `badge bg-success` | SCR-005 (cM) |
| `Table` | `table table-sm align-middle` + `table-responsive` | SCR-005 (descartados) |
| `Spinner` | `spinner-border text-primary` + `visually-hidden` | global (loading) |
| `GraphContainer` | `graph-container` + `mermaid` (classe CSS própria) | SCR-005 |

## Notas

- **Nenhum destes tokens foi inventado.** Todos têm linha de origem no legado ou são explicitamente marcados como herdados do Bootstrap. Onde o legado é silente (família tipográfica), a lacuna está registrada em vez de preenchida com um palpite.
- **Este arquivo é a única fonte de tokens do projeto** até que um `design-system/` real exista. O agente de codificação deve consumi-lo, e o `screen_deviation_log.md` registra que ele é derivado (DEV-006) e que a tipografia é uma lacuna (DEV-008).
