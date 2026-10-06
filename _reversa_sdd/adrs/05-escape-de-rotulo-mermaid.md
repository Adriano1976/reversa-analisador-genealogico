# ADR-05 — Escape do rótulo Mermaid: lista branca, e entidades DEPOIS do filtro

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-09-30 (J6PQ) e 2026-10-02 (T4ZM)
- **Commit(s):** `c709ea0` (fecha o `BUG-20260929-J6PQ`), `13d821e` (corrige o rótulo e encurta a ponte)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Com a renderização migrada para Mermaid (ADR-03), o **texto do nó passou a ser interpretado pela gramática do Mermaid**. O gatilho confirmado em navegador é a sequência **aspa dupla seguida de crase** em um nome vindo do GEDCOM: o lexer do Mermaid desvia para *markdown-string*, o fecha-colchete nunca vira o token que a gramática exige, e o **diagrama inteiro cai**.

A primeira defesa foi uma **lista negra**, e ela era **furada pela crase** — o caractere que causava o defeito não estava na lista.

## Decisão

1. Substituir a lista negra por uma **lista branca**: o que não está nela é **removido**.
2. Inverter a ordem para que a conversão de `&`, `<` e `>` em **entidades HTML rode DEPOIS do filtro**.

## Evidência

- `src/reporting/mermaid_render.py:47` — `_LABEL_SEGURO`, lista branca por regex negada, **documentada no próprio código com os dois bugs que a moldaram**.
- `src/reporting/mermaid_render.py:50-58` — normalização NFC, espaço inquebrável, travessões, aspas curvas, aspa dupla → apóstrofo, quebras de linha achatadas.
- `_reversa_bugs/busca-caminho/bugs/BUG-20260929-J6PQ-escape-incompleto-mermaid/` — análise da gramática, reprodução e verificação de código.
- `_reversa_bugs/busca-caminho/bugs/BUG-20261002-T4ZM-rotulo-descarta-caracteres-inertes/` — 14 caracteres descartados sem intenção pela versão seguinte.
- `tests/test_mermaid_escape.py` e `tests/test_characterization_mermaid.py`.

## Justificativa

Uma lista negra depende de **enumerar o perigo**, e o perigo é a gramática de um parser de terceiro — enumerar é sempre um passo atrás. Uma lista branca **define o que é seguro** e torna a falha conservadora: o pior caso passa a ser perder um caractere, e não derrubar o diagrama.

A ordem `filtro → entidades` é o outro lado do contrato: se as entidades fossem geradas antes do filtro, o **filtro poderia remover pedaços da própria entidade** já escapada.

## Consequências

- **Resultado medido:** 19 testes novos; **fuzz independente não encontrou vazamento** em **288 payloads** combinados nem linha de nó inválida em **30.000 nomes**.
- 🟢 **A ordem `filtro → entidades` é agora invariante de contrato**, e não detalhe de implementação. Quem reimplementar precisa preservá-la.
- ⚠️ **A primeira correção da lista branca foi estreita demais** e descartava 14 caracteres inertes (`T4ZM`). A lição registrada: uma lista branca erra **para o lado de perder informação**, e por isso precisa de teste de caracteres legítimos, não só de payloads hostis.
- ⚠️ **O mesmo vetor existe fora do rótulo:** o **id do nó** também é derivado de dado do GEDCOM e passou a ter sanitização própria (`[A-Za-z0-9_]`, prefixo `N_`). Duas superfícies, dois contratos.
- 🟢 **Fechamento de `subgraph` é garantido por `contextmanager`** (`:160-175`) pelo mesmo motivo: um `end` a mais ou a menos muda a árvore do diagrama **sem levantar erro nenhum** (`OPP-20260929-H2YY`). Falha silenciosa em gramática exige garantia estrutural, não disciplina de quem edita.

## Alternativas consideradas

- **Lista negra ampliada** (a versão inicial). Descartada empiricamente: era furada pela crase.
- **Escape genérico de HTML no rótulo inteiro.** Descartada: o alvo é a **gramática do Mermaid**, não HTML; escapar tudo produziria rótulo ilegível e não impediria o desvio do lexer.
