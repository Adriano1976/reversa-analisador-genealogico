# ADR-22 — Ordem de apresentação: documental primeiro, cM decrescente depois

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-10 (junto da apresentação das quatro seções)
- **Commit(s):** `a4d24df`, `cd8d7f3`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A análise de DNA pode devolver dezenas de conexões. A ordem "natural" seria **cM decrescente** — a ordem que o fluxo sempre usou, e a que o usuário reconhece de outros sistemas. Mas o fluxo mudou no ADR-14: as conexões **sem caminho documental deixaram de ser descartadas** e passaram a aparecer com as quatro seções.

Isso alterou a distribuição de forma dramática, e **medida**: no GEDCOM real, são **71 conexões, das quais 64 sem caminho no GEDCOM**. Ordenar por cM global colocaria as **7 conexões documentais** no meio das 64.

## Decisão

Ordenar por **dois critérios, nesta ordem**: primeiro as conexões **que têm caminho documental**, depois **cM decrescente** dentro de cada grupo.

## Evidência

- `src/core/dna_analysis.py:220-230` — a função `_ordem`, com o comentário que **registra a medição** ("71 conexões, das quais 64 sem caminho no GEDCOM") e a justificativa ("ordenar só por cM enterraria as 7 conexões documentais no meio das 64").
- O comentário declara ainda: *"Ordem de apresentação (não é ordem de confiança)"*.

## Justificativa

O que o operador procura primeiro é **o que a árvore sustenta**. Uma conexão com caminho documental é **acionável** (permite conferir os registros, ver a evidência de cada salto, identificar homônimos); uma conexão só com DNA é **uma pista**. Misturar as duas em uma ordem única de cM faz a pista mais forte esconder o achado mais sólido.

## Consequências

- ✅ **As 7 conexões documentais ficam no topo**, e as 64 que só têm DNA continuam visíveis logo abaixo — nenhuma foi descartada, o que é a conquista do ADR-14.
- ✅ **A declaração "não é ordem de confiança" é parte do contrato**, e evita que a posição na lista seja lida como veredito. Confiança, aqui, é o **estado do confronto** — não a posição.
- ⚠️ **A ordem depende de um valor medido em um GEDCOM específico (71/64).** Em uma árvore com maioria de conexões documentais, o primeiro critério perde efeito prático e a lista fica essencialmente por cM — o que é o comportamento desejado, mas a justificativa registrada deixa de descrever o caso.
- 🟢 **A função de ordenação é determinística:** a chave é uma tupla `(0|1, -cM)` sobre uma lista construída em ordem estável de iteração do CSV. Empates em cM mantêm a ordem de entrada — diferente do desempate do matching (ADR-23), **aqui não há dependência de `set`**.

## Alternativas consideradas

- **Manter cM decrescente global.** Descartada pela medição: enterraria as conexões documentais.
- **Ordenar por estado do confronto** (`CONFLITANTE` primeiro, por exemplo). Descartada: colocaria o **conflito** no topo da lista, quando o que o operador precisa primeiro é o que a árvore sustenta. Além disso, `INCONCLUSIVO` — o estado mais comum quando não há caminho — iria para o fim, escondendo as 64 conexões.
- **Duas listas separadas na tela.** Descartada: fragmentaria a leitura e exigiria decisão de interface que não existe.
