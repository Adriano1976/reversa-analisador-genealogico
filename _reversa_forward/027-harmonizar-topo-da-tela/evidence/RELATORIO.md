# Relatório da feature: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Execução: `/reversa-coding`, ações `T001` a `T017` (a `T018` é do estágio `/reversa-sync`)

## 1. O que mudou

- **Alertas de retorno na paleta:** quatro tokens novos (`--sucesso-bg`, `--sucesso-line`,
  `--perigo-bg`, `--perigo-line`), regras `.alert-success` e `.alert-danger` compactas, borda visível
  e o X preservado com opacidade e foco ajustados.
- **Ação principal:** largura natural acima de 576 px, largura total abaixo, via
  `@media (min-width:576px){ .d-grid > .btn{…} }`.
- **Escala do topo:** `h1` de `clamp(1.9rem,4vw,2.5rem)` para `clamp(1.8rem,3.2vw,2.2rem)`; arte de
  320 px para 280 px.
- **Comentário da masthead:** passou a descrever a `RN-24` (texto centralizado e estreito).

## 2. Antes e depois

| Métrica | Antes | Depois |
|---------|-------|--------|
| Bytes de `src/assets/app.css` | 23.242 | 25.490 |
| Linhas de `src/assets/app.css` | 399 | 438 |
| Tokens de alerta | 0 | 8 (4 por tema) |
| Contraste do alerta (texto) | 10,35:1 | 12,16 a 13,70:1 |
| Contraste do alerta (borda) | **1,15:1** | 5,57 a 7,47:1 |
| `h1` máximo | 2,5 rem | **2,2 rem** |
| Arte do topo | 320 px | **280 px** |
| `SHA_DA_TELA` | `c4a34f7b…` (30.781 bytes) | `c4a34f7b…` (30.781 bytes) |
| Guardas da tela | 90 passam | 90 passam |
| Suíte completa | 1.048 / 9 | 1.048 / 9 |

Delta só da 027 (contra as cópias do baseline): `app.css` **+41/−2**; `index.html` **+5/−3**.

## 3. Contrastes medidos

| Par | Razão |
|-----|-------|
| texto `--ink` sobre `--sucesso-bg` claro | 13,70:1 |
| borda `--sucesso-line` sobre `--sucesso-bg` claro | 5,57:1 |
| texto `--ink` sobre `--perigo-bg` claro | 13,49:1 |
| borda `--perigo-line` sobre `--perigo-bg` claro | 5,86:1 |
| texto `--ink` sobre `--sucesso-bg` escuro | 12,16:1 |
| borda `--sucesso-line` sobre `--sucesso-bg` escuro | 6,77:1 |
| texto `--ink` sobre `--perigo-bg` escuro | 13,22:1 |
| borda `--perigo-line` sobre `--perigo-bg` escuro | 7,47:1 |

Todos acima de 4,5:1 para texto e de 3:1 para a borda, nos dois temas.

## 4. O que **não** mudou

- A `RN-24`: o texto de introdução continua centralizado e estreito; `text-start` continua ausente do
  HTML servido, e o teste da introdução está verde.
- O rodapé: nenhuma regra de cartão, selo de cM (`bg-secondary`) ou espaçamento do resultado mudou.
- O `alert-warning` dentro do cartão de DNA continua com a cor padrão.
- Textos, `aria-pressed`, `visually-hidden` e `focus-visible`.
- O `SHA_DA_TELA` — o comentário é Jinja e não chega ao HTML.

## 5. Correções durante a execução

1. **`RN-24`**: o alinhamento centralizado da introdução não é defeito; é decisão presa por teste. A
   feature não o toca, e o `RF-01` virou a correção do comentário.
2. **Hash**: o comentário da masthead é um comentário **Jinja**, removido na renderização. O HTML
   servido continua byte a byte, e o `SHA_DA_TELA` não se move. O `RF-08` passou a exigir a
   verificação, não a mudança.

## 6. Prova por execução

| Prova | Arquivo |
|-------|---------|
| Linha de base (HEAD, status, suíte, hash) | `evidence/antes/suite.txt` |
| Recorte do topo e cópias do baseline | `evidence/antes/topo.txt`, `app.css`, `index.html`, `diff-baseline.txt` |
| Guardas antes | `evidence/antes/testes-da-tela.txt` |
| Guardas depois | `evidence/depois/testes-da-tela.txt` |
| Suíte depois | `evidence/depois/suite.txt` |
| Ritmo medido | `evidence/depois/ritmo.txt` |
| Hash verificado | `evidence/depois/hash.txt` |
| Escopo | `evidence/depois/escopo.txt` |
| Conferência da tela | `evidence/depois/tela.md` |

## 7. Conclusão

O topo passa a falar a mesma língua dos cartões nos três pontos que eram defeito: cor de alerta na
paleta, ação sem peso de barra e escala compacta. O quarto ponto — o alinhamento — era decisão, não
defeito, e ficou como estava; o comentário que dizia o contrário foi corrigido. O rodapé que o
operador elogiou não foi tocado.

A `T018` (adendo `027` em `_reversa_sdd/addenda/`) fica para o `/reversa-sync`.
