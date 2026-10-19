# 034 — Medições

Data: `2026-10-19`. Sondas: `evidence/_medir_caminhos.py`. CSV: `Famílias_Sergipanas.csv`
(56 KB, 454 nomes). Raiz `adriano`.

## 1. Onde param os nomes do CSV

| | Tratado (35.470 pessoas) | Adriano V2 (13.716 pessoas) |
|---|---:|---:|
| Nomes no CSV | 454 | 454 |
| Viram cartão | 90 | 8 |
| Descartados | **364** | **446** |

## 2. Dos descartados, quantos têm alguém compatível na árvore

Critério de "compatível" (necessário, não suficiente): prenome com similaridade ≥ 85 **e** ao
menos um sobrenome em comum.

| | Tratado | Adriano V2 |
|---|---:|---:|
| Com candidato compatível | **76** | **15** |
| O melhor escolhido era esse candidato (corte barrou) | 40 | 14 |
| O melhor escolhido era outro (ranking preteriu) | 36 | 1 |
| Sem nenhum candidato compatível | 288 | 431 |

## 3. Dos compatíveis, quantos acrescentariam "com caminho"

| | Tratado | Adriano V2 |
|---|---:|---:|
| Compatível **e** com caminho até o doador | 10 | 8 |
| … **e** com janela de vida viável | **7** | **1** |

Nascimentos dos 7 da Tratado: 1911, 1931, 1942, 1947, 1950, 1995 e um "after 1954" — gente
contemporânea, o que é coerente com uma linha de DNA.

**Leitura:** o teto medido é 6 → 13 caminhos na Tratado e 1 → 2 na Adriano V2, **se** os 7 (e o
1) forem de fato as mesmas pessoas. Cada promoção passa de novo pela janela de vida e pelo
veredito, então o número pode ser menor.

## 4. Os dois becos sem saída, medidos

- **Caso real (kit TG8027863, "Manoel Vieira da Silva", 7,9 + 17,5 = 25,4 cM):** na árvore
  Sandro o melhor candidato foi **Adelina da Silva Vieira** (`given` 46, `final` 81,5,
  `jacc` 1,00) — sobrenome idêntico, pessoa errada. Recusar foi correto. Na Tratado e na
  Adriano V2 o mesmo nome casa com **Manoel da Silva Vieira** (`given` 100, `final` 107,25).
- **Homônimos não consertam:** há **4** registros exatos "Manoel da Silva Vieira" na Tratado,
  nascidos em 1720, 1790, 1793 e 1845. Todos com caminho (10 a 13 pessoas) e **todos** com
  janela impossível (306, 236, 233 e 181 anos em 2026). Escolher outro homônimo não recupera
  esse cartão.
