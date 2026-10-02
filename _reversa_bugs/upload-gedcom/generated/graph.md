<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-02T16:28:42-03:00 a partir de 1 bugs -->

# Grafo de bugs · upload-gedcom

```mermaid
graph LR
  BUG-20260929-QMLY["#2 QMLY<br/>restrito<br/>high · upload"]
  style BUG-20260929-QMLY fill:#2b1b1b,stroke:#e05252,color:#f5f5f5
  BUG-20260929-BJJH["#1 BJJH<br/>restrito<br/>critical · upload<br/>contexto: busca-caminho"]
  style BUG-20260929-BJJH fill:#1b1b22,stroke:#5a5a7a,color:#c9c9c9,stroke-dasharray:4 3
  BUG-20260929-QMLY -.->|related-to proposed| BUG-20260929-BJJH
```

## Clusters

1 aresta(s) tocam este contexto, todas pelo mesmo endereço de arquivo compartilhado; nenhuma outra convergência foi observada.

## Impact score

Heurística de triagem (`causados*3 + bloqueados*2 + regressões*4 + relacionados*1`), contando apenas arestas `supported`/`confirmed`. Não substitui `priority` nem `severity`.

| Bug | Impact score |
|-----|--------------|
| `BUG-20260929-QMLY` | 0 |
