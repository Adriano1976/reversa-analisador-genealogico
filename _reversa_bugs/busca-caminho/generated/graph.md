<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-09-30T11:11:31-03:00 a partir de 2 bugs -->

# Grafo de bugs · busca-caminho

```mermaid
graph LR
  BUG-20260929-BJJH["#1 BJJH<br/>restrito<br/>critical · upload"]
  style BUG-20260929-BJJH fill:#2b1b1b,stroke:#e05252,color:#f5f5f5
  BUG-20260929-J6PQ["#3 J6PQ<br/>restrito<br/>medium · path-search"]
  style BUG-20260929-J6PQ fill:#2b1b1b,stroke:#e05252,color:#f5f5f5
  BUG-20260929-QMLY["#2 QMLY<br/>restrito<br/>high · upload<br/>contexto: upload-gedcom"]
  style BUG-20260929-QMLY fill:#1b1b22,stroke:#5a5a7a,color:#c9c9c9,stroke-dasharray:4 3
  BUG-20260929-BJJH -.->|related-to proposed| BUG-20260929-QMLY
```

## Clusters

1 aresta(s) tocam este contexto, todas pelo mesmo endereço de arquivo compartilhado; nenhuma outra convergência foi observada.

## Impact score

Heurística de triagem (`causados*3 + bloqueados*2 + regressões*4 + relacionados*1`), contando apenas arestas `supported`/`confirmed`. Não substitui `priority` nem `severity`.

| Bug | Impact score |
|-----|--------------|
| `BUG-20260929-BJJH` | 0 |
| `BUG-20260929-J6PQ` | 0 |

---
*Gerado pelo Reversa-Debugger-Graph em 2026-09-30.*
