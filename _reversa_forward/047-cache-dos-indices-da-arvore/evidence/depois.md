# Depois: os dois estados, medidos com o mesmo instrumento

> Feature: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Instrumento: `evidence/medir.py` (upload + seleção + duas análises)
> Cenário: GEDCOM de 19.403 pessoas, 21.528 famílias, 77.346 arestas; CSV de matches de 492 linhas

## Medição pareada (mesma sessão, um estado depois do outro)

| Etapa | Sem cache | Com cache | Ganho |
|---|---:|---:|---:|
| Upload (parse frio) | 54,66 s | 61,13 s | — (o primeiro parse é sempre pago) |
| Selecionar a árvore | 54,81 s | **0,92 s** | **59×** |
| Análise nº 1 (constrói os índices) | 70,70 s | **17,79 s** | 4,0× |
| Análise nº 2 (índices já prontos) | 62,17 s | **4,74 s** | **13×** |
| Índices dentro da análise nº 1 | 13,57 s | 9,85 s | — |
| Índices dentro da análise nº 2 | 4,29 s | **0,00 s** | memo acertou |

## Leitura

- A **análise nº 2** é o número que representa o uso real: 4,74 s contra 62,17 s. A diferença é
  toda parse (`~55 s`) mais reconstrução de índice (`~4,3 s`).
- A **análise nº 1** ainda paga a construção dos índices (9,85 s), porque o processo acabou de
  subir. Ela sai de 70,70 s para 17,79 s, e cai para 4,74 s na seguinte.
- A **seleção** é o ganho mais visível no dia a dia: 54,81 s → 0,92 s.
- O upload continua pagando o parse frio nos dois estados — é o custo de entrada, não o cache.

## Ressalva de ambiente

O parse deste arquivo variou de **41 s a 92 s** entre execuções na mesma máquina. Por isso a
comparação é **pareada** (os dois estados na mesma sessão) e os testes automatizados contam
chamadas em vez de cronometrar. Números absolutos de uma execução isolada não são linha de base.
