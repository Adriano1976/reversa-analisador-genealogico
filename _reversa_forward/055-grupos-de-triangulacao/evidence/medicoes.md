# Medições da feature 055

> Medido em `2026-11-09`, sobre a amostra real `SY3230889_triangulation_v2.csv`
> (1.650 linhas), que **não** entra no repositório (`.reversa/principles.md#I`).
> Ambiente: `.venv`, Python 3.13.17.

## Desempenho

| Etapa | Tempo |
|---|---:|
| Leitura do CSV (1.650 linhas → 1.650 pares) | 0,464 s |
| Agrupamento (varredura + fechamento) | 0,113 s |
| **Total do bloco** | **0,577 s** |

O tempo de leitura é dominado pelo `pandas`; o agrupamento é a parte nova e custa
um quinto do total. Não foi medido arquivo de 100 mil linhas — **não há amostra
nesse tamanho**, e estimar seria inventar número (`RN-05` / princípio V).

## Resultado do agrupamento

| Métrica | Valor |
|---|---:|
| Pares lidos | 1.650 |
| Pares descartados | 0 |
| Grupos fechados e maximais | **28** |
| Kits cobertos por algum grupo | **116** de 351 |
| Tamanhos de grupo | 3 a 7 kits |
| Regiões marcadas como acúmulo | 0 |

Os 28 grupos e os 116 kits são a **linha de base declarada** no `roadmap.md` e no
`onboarding.md`. Divergência grande aqui é sinal de mudança de regra, não de
melhoria.

## O que foi descartado, e por quê

- **Reparo guloso de conjunto mascarado.** Recuperava trios escondidos por um kit
  de fora, mas também fabricava trios fechados dentro da região de acúmulo do
  chr20 (0,40 Mb, cM 5–10): 46 grupos em vez de 28. Removido — um grupo a menos é
  uma negativa visível; um grupo fabricado é um parentesco inventado.
- **Interseção sem janela.** Os 18 pares com dois segmentos no mesmo cromossomo
  faziam a interseção vazar para o outro segmento e derrubavam um grupo (27 em
  vez de 28). Corrigido com a janela.
