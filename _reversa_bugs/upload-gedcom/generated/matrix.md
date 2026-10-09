<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-09T15:30:33-03:00 a partir de 2 bugs -->

# Matriz de relações · upload-gedcom

Lista esparsa de arestas. Arestas simétricas são gravadas uma única vez, no bug de menor `display_number`.

| Origem | Tipo | Destino | State | Evidência |
|--------|------|---------|-------|-----------|
| `BUG-20260929-QMLY` | related-to | `BUG-20260929-BJJH` (contexto `busca-caminho`) | confirmed | aresta gravada no bug de origem |
| `BUG-20261009-6RKP` | related-to | `BUG-20260929-QMLY` (contexto `upload-gedcom`) | proposed | aresta gravada no bug de origem |

## Notas

- Duas arestas nascem neste contexto. Uma **cruza contexto** (`QMLY` para `BJJH`, que vive em
  `busca-caminho`) e uma fica **dentro** dele (`6RKP` para `QMLY`).
- `related-to` é relação **simétrica**, e os dois bugs a gravam. Cada contexto projeta a aresta que
  está gravada nos bugs dele, e é por isso que a primeira aparece nos dois lados. Não há linha derivada
  a exibir nesta tabela.
- A aresta `6RKP -> QMLY` está em estado **`proposed`**: é hipótese de leitura, não fato apurado, e por
  isso **não** entra no impact score nem em priorização automática. Ela existe porque os dois defeitos
  tocam a mesma região de código, e não porque a causalidade tenha sido demonstrada.
- A aresta interna é a que sustenta o cluster do `graph.md`: os dois bugs do contexto convergem na
  composição do nome armazenado.
