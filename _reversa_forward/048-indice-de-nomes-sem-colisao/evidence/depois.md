# Depois: o dossiê não mudou

> Feature: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Mesma árvore sintética e mesma consulta da linha de base

## Comparação

| Campo | Antes | Depois |
|---|---|---|
| `exact_count` | 2 | **2** |
| ids | `["@I1@", "@I2@"]` | **`["@I1@", "@I2@"]`** |
| nomes | `["Joao Silva", "Joao Silva"]` | **idênticos** |
| ordem das chaves da ficha | 13 campos | **os mesmos 13** |

O dossiê é indistinguível. A mudança foi de **onde o índice mora**, não do que ele produz.

## Suíte

`1656 passed, 9 skipped` (baseline 1655/9; o arquivo de testes foi reescrito: 6 testes antigos
saíram, 7 novos entraram).
