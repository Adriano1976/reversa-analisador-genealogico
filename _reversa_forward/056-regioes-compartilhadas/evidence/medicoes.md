# Medições da feature 056

> Medido em `2026-11-09`, sobre o `DNA_Nordestino.csv` (783 linhas de segmento), que
> permanece fora do repositório (`.reversa/principles.md#I`).

## O piso de 10 cM, medido

| Critério | Regiões | Maximais | Kits cobertos | Maior região |
|---|---:|---:|---:|---:|
| Sem piso | 535 | 158 | **553 de 606** | 45 kits |
| Com piso de 10 cM | 70 | **32** | **108 de 606** | 12 kits |

Sem o piso, **91 % dos kits** entram em alguma região. Com o piso, 18 %. É a razão pela qual
o piso virou **filtro** nesta feature.

## Desempenho do agrupamento

| Etapa | Tempo |
|---|---:|
| 783 segmentos → 32 regiões | **0,005 s** |

O custo é dominado pela leitura do CSV, que já existia na análise; o agrupamento é a parte
nova e custa milissegundos.

## Resultado

| Métrica | Valor |
|---|---:|
| Segmentos lidos | 783 |
| Regiões | **32** |
| Tamanhos | 3 a 12 kits |
| Regiões com alerta de acúmulo | 1 |

## O que foi removido da 055

- O adaptador do CSV de pares (`parsers/triangulacao_gedmatch.py`).
- O agrupamento por pares fechados (`core/triangulacao.py`), substituído por
  `core/regioes.py`.
- A ação `triangulacao_analysis`, o formulário da Fase 3 e o campo opcional na ação de DNA.
- A rota `/grupos.csv`, substituída por `/regioes.csv`.

O `SHA_DA_TELA` voltou ao valor de antes da 055 — a prova de que a remoção não deixou resíduo.
