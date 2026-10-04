<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-04T13:55:34-03:00 a partir de 3 bugs -->

# Grafo de bugs · busca-caminho

```mermaid
graph LR
  BJJH["#1 BJJH<br/>restrito<br/>active · mitigating<br/>critical · upload"]
  style BJJH fill:#2b1b1b,stroke:#e05252,color:#f5f5f5
  J6PQ["#3 J6PQ<br/>restrito<br/>medium · path-search"]
  style J6PQ fill:#2b2416,stroke:#d8a72a,color:#f5f5f5
  T4ZM["#4 T4ZM<br/>Rotulo Mermaid descarta 14 caracteres inertes<br/>low · path-search"]
  style T4ZM fill:#1b2740,stroke:#2a3a55,color:#e6edf7
  QMLY["#2 QMLY<br/>restrito<br/>high · upload<br/>contexto: upload-gedcom"]
  style QMLY fill:#1b1b22,stroke:#5a5a7a,color:#c9c9c9,stroke-dasharray:4 3
  EWSJ["#5 EWSJ<br/>Badge de cM exibe o valor com ruido<br/>de ponto flutuante<br/>low · dna-analysis<br/>contexto: analise-dna"]
  style EWSJ fill:#1b1b22,stroke:#5a5a7a,color:#c9c9c9,stroke-dasharray:4 3
  BJJH -->|related-to confirmed| QMLY
  T4ZM -->|caused-by confirmed| J6PQ
  EWSJ -.->|related-to proposed| T4ZM
```

Estilo: aresta cheia é `supported` ou `confirmed`; aresta tracejada é `proposed`, isto é, hipótese.
Nó com borda vermelha tem severidade `high` ou `critical`; amarela, `medium`. Nós de outros contextos
aparecem com borda tracejada e o contexto declarado.

## Clusters

**Nenhum cluster.** As duas arestas confirmadas que tocam este contexto tratam de mecanismos
diferentes: a exposição de estado e pasta compartilhada (`BJJH` e `QMLY`) e o escape do rótulo
(`T4ZM` e `J6PQ`). Não há convergência de múltiplos defeitos no mesmo componente que indique causa
estrutural.

A terceira aresta, `EWSJ -.-> T4ZM`, está em `proposed`: é hipótese conceitual, não causa.

## Impact score

Heurística de triagem (`causados*3 + bloqueados*2 + regressões*4 + relacionados*1`), contando apenas
arestas `supported`/`confirmed`, e apenas para bug aberto. `related-to` tem peso limitado a 3 no total.
Não substitui `priority` nem `severity`.

| Bug aberto | causados ×3 | bloqueados ×2 | regressões ×4 | relacionados ×1 | Score |
|------------|-------------|---------------|---------------|-----------------|-------|
| `BUG-20260929-BJJH` | 0 | 0 | 0 | 1 | **1** |

O bug aberto está bloqueado por uma **condição** (`blocking` de tipo `external`), e não por uma aresta
de relação. A heurística conta arestas `supported`/`confirmed` do bloco `relationships`, então a
condição de bloqueio **não entra no cálculo**. O score continua sendo o da aresta `related-to` com o
`QMLY`.

O `BUG-20260929-J6PQ` tem score zero por não ter aresta confirmada gravada nele, e a relação com o
`T4ZM` já está contada no lado que a gravou.
