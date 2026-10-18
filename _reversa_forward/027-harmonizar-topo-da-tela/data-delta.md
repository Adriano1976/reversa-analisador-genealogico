# Data Delta: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/027-harmonizar-topo-da-tela/requirements.md`

## 1. Veredito

**Nenhum dado de domínio, payload, tabela ou migração.** O delta é de apresentação: quatro tokens de
alerta entram, duas regras de escala mudam e um comentário do template é corrigido. As cores dos
cartões de resultado e do selo de cM ficam idênticas.

## 2. O que não muda

| Camada | Situação |
|--------|----------|
| Modelo de domínio e esquema PostgreSQL | intocados |
| Payloads das portas | intocados |
| Rotas, formulários, mensagens e redirecionamentos | intocados |
| Texto visível das 8 telas literais | intocado |
| Cartões de resultado (cores, selos, espaçamentos) | intocados (`RN-08`) |
| `--st-*` e o selo de cM | intocados |

## 3. Tokens novos

| Token | Tema claro | Tema escuro | Uso |
|-------|------------|-------------|-----|
| `--sucesso-bg` | `#EDF4E6` | `#1E2A17` | fundo do `.alert-success` |
| `--sucesso-line` | `#3F6B2E` | `#8DBB6E` | borda do `.alert-success` |
| `--perigo-bg` | `#FBEDEA` | `#2E1B18` | fundo do `.alert-danger` |
| `--perigo-line` | `#A8321F` | `#EE9A88` | borda do `.alert-danger` |

O texto dos dois alertas usa `--ink`, que os dois temas já redefinem.

## 4. Contraste medido

| Par | Razão |
|-----|-------|
| `--ink` sobre `--sucesso-bg` claro | 13,70:1 |
| `--sucesso-line` sobre `--sucesso-bg` claro | 5,57:1 |
| `--ink` sobre `--perigo-bg` claro | 13,49:1 |
| `--perigo-line` sobre `--perigo-bg` claro | 5,86:1 |
| `--ink` sobre `--sucesso-bg` escuro | 12,16:1 |
| `--sucesso-line` sobre `--sucesso-bg` escuro | 6,77:1 |
| `--ink` sobre `--perigo-bg` escuro | 13,22:1 |
| `--perigo-line` sobre `--perigo-bg` escuro | 7,47:1 |

Referência do estado atual: texto 10,35:1 (passa) e borda **1,15:1** (imperceptível).

## 5. Regras alteradas na folha

| Regra | Antes | Depois |
|-------|-------|--------|
| `.alert-success` | sem regra; cor padrão do framework | fundo, borda e texto da paleta; padding compacto |
| `.alert-danger` | sem regra; cor padrão do framework | mesma forma, com `--perigo-*` |
| `.alert .btn-close` | padrão do framework | opacidade e tamanho ajustados; ícone preservado |
| `.d-grid > .btn` | largura total em qualquer tela | natural acima de 576 px; total abaixo |
| `h1` | `clamp(1.9rem, 4vw, 2.5rem)` | `clamp(1.8rem, 3.2vw, 2.2rem)` |
| arte do topo | `min(50%, 320px)` | `min(50%, 280px)` |

Nenhuma regra de `.estado-*`, `.badge`, `.cartao-do-resultado` ou `bg-secondary` é tocada.

## 6. Migração e reversão

- **Migração de dados:** n/a.
- **Migração de configuração:** n/a.
- **Reversão:** `git revert` do commit. O hash da tela volta ao valor anterior junto com o comentário;
  o `ETag` de `/app.css` muda sozinho e o navegador revalida.

## 7. Rastreabilidade

| Requisito | Onde o delta aparece |
|-----------|----------------------|
| `RF-01` | comentário da masthead em `index.html` |
| `RF-02`, `RF-10` | tokens e regras de alerta, com os números no comentário |
| `RF-03` | regra de `.d-grid > .btn` |
| `RF-04` | `h1` e arte |
| `RF-05` | medição de ritmo (sem mudança se os degraus estiverem consistentes) |
| `RF-06` | nenhum seletor dos cartões ou do selo de cM |
| `RF-08` | novo `SHA_DA_TELA` e adendo |
