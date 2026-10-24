# Memória: o que a árvore e os índices custam

> Feature: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Processo: Python 3.14 do `.venv`, medido com `psutil` (`RSS`)

## Medição

| Estado | RSS | Delta |
|---|---:|---:|
| processo vazio | 45 MB | — |
| após o parse (árvore viva) | 381 MB | **+336 MB** |
| após construir os índices | 412 MB | **+31 MB** |
| após a segunda chamada de índices | 412 MB | **0 MB** |

A segunda chamada de `build_ged_indexes` custou **0,0000 s** e não moveu o RSS: o memo devolveu o
mesmo trio preso ao grafo.

## Leitura

- Com teto 1, o processo estabiliza em **~412 MB** quando uma árvore está no cache.
- Duas árvores levariam a ~750 MB — por isso o teto padrão é 1 (decisão D-05 do `roadmap.md`).
- O índice é 7,5 % do custo total; a árvore é o resto.
- Não há crescimento entre requisições com a mesma árvore: a segunda chamada devolve o mesmo
  objeto, sem alocar de novo.
