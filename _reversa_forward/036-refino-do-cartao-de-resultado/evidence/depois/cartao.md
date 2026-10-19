# Medição do cartão depois da mudança (T016)

> Data: `2026-10-19` · Feature `036-refino-do-cartao-de-resultado`
> Método: `render_template("index.html", dna_results=[resultado sintético])` — sem servidor e sem
> dado real (princípio I). O recorte é o `card-header` do `details.card.cartao-do-resultado`.

## 1. O arranjo no HTML servido

| Medição | Resultado |
|---------|-----------|
| Ordem das faixas no cabeçalho | `titulo-da-conexao` (posição 185) → `selos-do-cabecalho` (320) → `cabecalho-sinais` (1792) |
| `div` dentro do `card-header` | **0** — os extratores não são truncados |
| Selos dentro da faixa própria | `bg-secondary`, `estado-CONFLITANTE`, `validacao-conflito` |
| Link do retorno | `<a class="voltar-ao-indice" href="#resultados">Voltar<span class="visually-hidden">` — intacto |
| Título renderizado | `Análise de conexão com <strong>Primo Sintetico</strong>` |

## 2. As regras que sustentam o arranjo

| Regra | Trecho medido |
|-------|---------------|
| Áreas do desktop | `grid-template-areas:"titulo acao" "selos acao" "sinais acao"` |
| Áreas do telefone | `grid-template-areas:"titulo" "selos" "sinais" "acao"` |
| Título | `grid-area:titulo;display:block;font-size:1.4rem;line-height:1.2` |
| Casco | `details.card.cartao-do-resultado{border-radius:16px;background:linear-gradient(...);position:relative}` |
| Barra | `.cartao-do-resultado::before{inset:0 auto 0 0;width:5px;background:linear-gradient(180deg,var(--muted),var(--head))}` |
| Hover | `.cartao-do-resultado > summary.sumario-do-cartao:hover{text-decoration:none}` |
| Indicador | `::before` de 2rem com `border-radius:.6rem`; `::after` (chevron) absoluto por cima |

## 3. Contraste dos elementos (WCAG 2.1, superfície `--surface`)

| Par | Claro | Escuro |
|-----|-------|--------|
| Título `--head` | 10,87:1 | 12,14:1 |
| Sinais `--muted` | 6,11:1 | 6,48:1 |
| "Voltar" `--primary` | 6,26:1 | 7,67:1 |
| Chevron `--muted` | 6,11:1 | 6,48:1 |
| Barra `--muted → --head` | 6,11 → 10,87:1 | 6,48 → 12,14:1 |

Todo texto ≥ 4,5:1; os elementos não textuais com significado ≥ 3:1. A borda da caixa do indicador
(`--line`, 1,47:1 / 1,38:1) é decoração — a pista é o chevron.

## 4. O que não mudou

- O bloco "Matches descartados" e o bloco "Observações do arquivo" continuam com o losango e a
  superfície antiga (`RN-07`).
- O selo de cM continua em `bg-secondary` (4,69:1).
- Nenhum texto visível ou escondido mudou.
- `GET /` vazio continua com 30.781 bytes e `c4a34f7b…`.
