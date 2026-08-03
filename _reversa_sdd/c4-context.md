# Diagrama C4 — Contexto — analisador-genealogico

> Gerado pelo **Architect** em 2026-08-03
> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO

---

## Nível 1 — Contexto (sistema no centro)

```mermaid
flowchart LR
    subgraph Usuario["Usuários"]
        U1["Genealogista Genético<br/>(usuário humano)"]:::person
    end

    S(["<b>analisador-genealogico</b><br/>Aplicação Web Flask<br/>monolito SSR"]):::system

    subgraph Externos["Sistemas Externos / Fontes"]
        C1["Arquivos GEDCOM (.ged)<br/>Árvore genealógica"]:::ext
        C2["CSV de DNA matches<br/>GEDmatch (.csv)"]:::ext
        C3["CDN Web<br/>Bootstrap 5 + Mermaid.js"]:::ext
    end

    U1 -->|"upload de GEDCOM e CSV,<br/>nome da pessoa-raiz,<br/>busca de caminho"| S
    S -->|"leitura e parsing (ged4py)"| C1
    S -->|"leitura e agregação de<br/>segmentos cM (pandas)"| C2
    S -.->|"carrega assets via navegador<br/>(Bootstrap, Mermaid)"| C3

    classDef person fill:#08427B,color:#fff,stroke:#052e56,stroke-width:1px
    classDef system fill:#1168BD,color:#fff,stroke:#0b53a1,stroke-width:2px
    classDef ext fill:#85BBF0,stroke:#1168BD,stroke-width:1px
```

## Legenda

| Símbolo | Descrição | Confiança |
| --- | --- | --- |
| **Genealogista Genético** | Única persona de usuário (sem autenticação/RBAC). | 🟢 |
| **Aplicação Web Flask** | Monolito SSR com rotas `GET /` e `POST /` (ações `dna_analysis`, `path_search`). | 🟢 |
| **GEDCOM (.ged)** | Entrada de árvore genealógica, parseada a cada requisição. | 🟢 |
| **CSV DNA** | Entrada de matches de DNA; colunas Nome/cM/ID/Email. | 🟢 |
| **CDN Web** | Bootstrap 5 e Mermaid.js via navegador — 🟡 INFERIDO do template. | 🟡 |

## Notas

- Não há banco de dados, fila, cache ou API externa consumida/produzida. 🟢
- Todas as interações externas de dados são **entrada de arquivos locais**. 🟢