# Medições — feature 057

> Medido em `2026-11-10`, no harness estático (o mesmo markup + `app.css` + `bootstrap`,
> Chrome headless, janela de 1114 px) e nos testes.

## 1. Da fixture sintética ao gráfico

`DNA_CSV_SEGMENTOS_DISTRIBUICAO` (11 segmentos, 3 cromossomos) atravessa o fluxo real e produz:

| Cromossomo | Kits distintos | cM médio | Altura de Matches | Altura de cM |
|---|---:|---:|---:|---:|
| 1 | 4 | 16,75 | 10,0 % (topo 40) | 41,88 % (topo 40) |
| 7 | 4 | 37,5 | 10,0 % | 93,75 % |
| 16 | 3 | 12,666… | 7,5 % | 31,68 % |

O kit `A111111` aparece no cromossomo 1 e no 7 e conta **uma vez em cada** — a deduplicação é por
cromossomo, não global (`RN-02`).

Conferido também no teste de contrato HTTP: o cartão do cromossomo 1 mostra `Matches: 4` e
`cM médio: 16,75` no HTML servido.

## 2. Eixos

Os dois eixos partem de zero (`RN-08`) e o topo é o menor múltiplo do passo que cobre o maior
valor em quatro intervalos:

| Série | Maior valor | Alvo (÷4) | Passo | Topo | Marcas |
|---|---:|---:|---:|---:|---|
| Matches | 4 | 1,0 | 1 | 4 | 0, 1, 2, 3, 4 |
| cM médio | 37,5 | 9,375 | 10 | 40 | 0, 10, 20, 30, 40 |
| Matches (7 no harness) | 7 | 1,75 | 2 | 8 | 0, 2, 4, 6, 8 |

## 3. Alinhamento do eixo dos cromossomos

Primeira medição, com `transform-origin:top right`: o rótulo `Chr 1` caía sob a coluna 2 — o
`getBoundingClientRect` do texto girado mostrava centro em 167,3 px contra 126,2 px da coluna.

Depois da correção (`transform-origin:center` e `justify-self:center`), medido no mesmo harness de
12 colunas:

| Coluna | Centro da coluna | Centro do rótulo |
|---|---:|---:|
| Chr 1 | 126,2 | 126,2 |
| Chr 2 | 203,1 | 203,1 |
| Chr 7 | 587,4 | 587,4 |
| Chr 22 | 971,8 | 971,8 |

Doze colunas de 72,9 px com `.25rem` de vão, em 918,4 px de área.

## 4. Custo

A agregação é uma passada sobre os segmentos das regiões já calculadas: nenhuma leitura de arquivo,
nenhum segundo matching. Não há medição de tempo separada porque a conta é menor que a do
agrupamento da 056, medido em 0,005 s para 783 segmentos.
