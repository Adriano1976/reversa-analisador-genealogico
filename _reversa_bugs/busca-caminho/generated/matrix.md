<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-04T13:51:03-03:00 a partir de 3 bugs -->

# Matriz de relações · busca-caminho

Lista esparsa de arestas. Arestas simétricas são gravadas uma única vez, no bug de menor `display_number`.

| Origem | Tipo | Destino | State | Evidência |
|--------|------|---------|-------|-----------|
| `BUG-20260929-BJJH` | related-to | `BUG-20260929-QMLY` (contexto `upload-gedcom`) | confirmed | aresta gravada no bug de origem |
| `BUG-20261002-T4ZM` | caused-by | `BUG-20260929-J6PQ` | confirmed | aresta gravada no bug de origem |
| `BUG-20261002-T4ZM` | related-to **(derivada)** | `BUG-20261004-EWSJ` (contexto `analise-dna`) | proposed | aresta gravada no `EWSJ`, e não aqui. Aparece como inversa porque `related-to` é simétrica, e é a única forma de este contexto enxergar que um bug de fora o referencia |

## Notas

- A primeira aresta cruza contexto: o alvo vive em `upload-gedcom`.
- A terceira é **derivada** e **proposta**, ou seja, hipótese. A investigação do `EWSJ` não achou nexo causal, e a aresta não foi promovida.
- O `BUG-20260929-J6PQ` não tem aresta gravada nele. A relação com o `T4ZM` existe porque aquele bug a gravou, e é direcional: `caused-by` aponta do efeito para a causa. Não há tipo inverso no catálogo, então nenhuma linha derivada é criada para ela.
