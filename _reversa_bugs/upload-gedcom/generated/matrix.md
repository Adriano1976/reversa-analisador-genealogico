<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-10T03:28:36-03:00 a partir de 2 bugs -->

# Matriz de relações · upload-gedcom

Lista esparsa de arestas. Arestas simétricas são gravadas uma única vez, no bug de menor `display_number`.

| Origem | Tipo | Destino | State | Evidência |
|--------|------|---------|-------|-----------|
| `BUG-20260929-QMLY` | related-to | `BUG-20260929-BJJH` (contexto `busca-caminho`) | confirmed | aresta gravada no bug de origem |
| `BUG-20261009-6RKP` | related-to | `BUG-20260929-QMLY` (contexto `upload-gedcom`) | confirmed | `root_cause` confirmado no fix: a forma fechada que o `QMLY` criou é a causa raiz deste |

## Notas

- Duas arestas nascem neste contexto. Uma **cruza contexto** (`QMLY` para `BJJH`, que vive em
  `busca-caminho`) e uma fica **dentro** dele (`6RKP` para `QMLY`).
- `related-to` é relação **simétrica**, e os dois bugs a gravam. Cada contexto projeta a aresta que
  está gravada nos bugs dele, e é por isso que a primeira aparece nos dois lados. Não há linha derivada
  a exibir nesta tabela.
- A aresta `6RKP -> QMLY` foi promovida de **`proposed`** para **`confirmed`** no fix de 2026-10-10. A
  hipótese era que os dois defeitos tocam a mesma região de código; o `root_cause` apurou que a forma
  fechada criada pelo `QMLY` é **exatamente** a causa raiz do `6RKP`. Deixou de ser leitura de quem
  escreveu este grafo e passou a ser fato com evidência em `bug.md`.
- A aresta interna é a que sustenta o cluster do `graph.md`: os dois bugs do contexto convergem na
  composição do nome armazenado.
