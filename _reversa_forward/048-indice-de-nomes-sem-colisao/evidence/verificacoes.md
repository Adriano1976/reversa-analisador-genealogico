# Verificações: estado, custo e contaminação

> Feature: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`

## 1. O estado de módulo desapareceu

Varredura do fonte de `src/core/homonimos.py`:

| Símbolo | Ocorrências |
|---|---:|
| `_INDICE_DE_NOMES` | **0** |
| `_chave_de` | **0** |
| `global ` | **0** |

Não há cache de módulo, não há chave, não há escrita em global.

## 2. O custo é uma construção por árvore

Árvore nova de 3 pessoas, três consultas seguidas:

```json
{"pessoas": 3, "consultas": 3, "get_name_total": 3, "por_consulta": 1.0, "mesmo_objeto": true}
```

Três consultas percorreram as pessoas **uma vez** (3 chamadas de `get_name`, uma por pessoa), e
devolveram o **mesmo objeto**. O custo por consulta depois da primeira é O(1).

## 3. A contaminação entre árvores não acontece mais

Duas árvores de 3 pessoas com os mesmos xrefs extremos (`@I1@`, `@I3@`) e um `xref` interior
diferente:

```json
{"mapa_b_tem_bia": false, "mapa_a_tem_dora": false, "mesmo_objeto": false}
```

Cada árvore tem o seu mapa, e nenhuma enxerga o nome exclusivo da outra.
