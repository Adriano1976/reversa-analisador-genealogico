# Medições — feature 058

> Medido em `2026-11-11`, nos testes de contrato (HTTP real com fixture sintética) e no harness
> estático (o markup da tabela + `app.css` + `bootstrap`, Chrome headless a 1114 px).

## 1. Da fixture à tabela

`DNA_CSV_SEGMENTOS_DISTRIBUICAO` — 11 segmentos em 3 cromossomos, um segmento por kit por região:

| Cromossomo | Linhas | cM das linhas |
|---|---:|---|
| 1 | 4 | 22 · 18 · 15 · 12 |
| 7 | 4 | 45 · 40 · 35 · 30 |
| 16 | 3 | 11 · 13 · 14 |
| **Total** | **11** | |

O kit `A111111` aparece **duas vezes** (cromossomo 7 com 45 cM e cromossomo 1 com 12 cM): são dois
segmentos, em duas regiões — a tabela é por par (região, kit), não por kit.

Conferido no HTML servido: 11 `<tr data-busca=…>`, contador "11 segmentos" e as sete colunas.

## 2. Filtros (o que o script deve produzir)

| Ação | Linhas visíveis | Contador |
|---|---:|---|
| Sem filtro, página de 20 | 11 | "11 segmentos" |
| Filtro de cromossomo = 7 | 4 | "4 de 11 segmentos" |
| Busca `ana` | 2 | "2 de 11 segmentos" |
| Busca `zzz` | 0 | "0 de 11 segmentos" + frase de estado vazio |
| Página de 10 | 10 na primeira página | "Página 1 de 2" |

## 3. O par linha ↔ faixa

A âncora nasce do `indice` da região, na ordem da projeção. Na fixture as regiões saem como
cromossomo 1, 7 e 16, então `regiao-1`, `regiao-2` e `regiao-3`. O teste de contrato compara o
conjunto de `href="#regiao-N"` com o conjunto de `id="regiao-N"` e exige que o primeiro esteja
contido no segundo.

No harness, abrir a página com `#regiao-2` no endereço pinta a faixa do cromossomo 7 com o contorno
de `:target` — sem JavaScript.

## 4. Ajuste de alinhamento

A primeira medição mostrou o cabeçalho "Posição" alinhado à esquerda e os valores à direita. O
cabeçalho passou a `class="numerico"`, como "Tamanho" e "cM".

## 5. Custo

A tabela é marcação: uma linha por par (região, kit), montada a partir das regiões que já estão em
memória. Não há leitura de arquivo, segundo matching nem formatação no servidor. O filtro e a
paginação não fazem requisição: o script esconde linhas do documento já servido (precedente da 046,
onde paginar no servidor custaria o parse inteiro do GEDCOM).
