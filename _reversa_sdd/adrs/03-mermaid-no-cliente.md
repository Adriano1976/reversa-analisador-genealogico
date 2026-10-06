# ADR-03 — Migrar a visualização de grafo de Pyvis (servidor) para Mermaid (cliente)

- **Status:** Aceito e vigente
- **Data da decisão:** entre 2026-09-28 e 2026-09-29
- **Confiança:** 🟡 INFERIDO para a motivação; 🟢 CONFIRMADO para a decisão e o efeito

## Contexto

O legado gerava a visualização do caminho genealógico como **página HTML estática escrita no servidor com Pyvis** (e `matplotlib` no ambiente), gravada em `static/graph_path_search.html` — um caminho fixo, único para todos.

## Decisão

Renderizar o diagrama **no navegador**, com **Mermaid 10 via CDN**, a partir de uma string gerada pelo servidor. A visualização deixa de ser um artefato em disco.

## Evidência

- `requirements.txt` — **nem `pyvis` nem `matplotlib` constam**, e não há nenhum `import` de ambos em `src/`.
- A pasta `static/` **não existe** e `STATIC_FOLDER` foi removido de `app.py` pela `OPP-20260929-SEQO`.
- O diagrama hoje é string Mermaid produzida por `src/reporting/mermaid_render.py` e entregue ao template, que a renderiza no cliente (`securityLevel: 'strict'`, Bootstrap 5.3.3 e Mermaid 10 por CDN).
- Não há `Dockerfile`, e nenhuma dependência de sistema foi adicionada para a renderização.

## Justificativa

🟡 Inferida do conjunto de evidências, não registrada em prosa: **reduzir dependências pesadas** (Pyvis arrasta `matplotlib`/`numpy` para gerar HTML) e **eliminar a escrita de arquivo no servidor** — que era justamente o vetor de um caminho fixo e compartilhado.

## Consequências

- ✅ O servidor deixou de produzir artefato em disco, e o vetor de "HTML de grafo em caminho fixo" **deixou de existir** (registrado no `BUG-20260929-BJJH` como Problema 1, encerrado).
- ⚠️ **Abriu um vetor novo de defeito, e ele se materializou duas vezes.** O texto do nó passou a ser interpretado pela **gramática do Mermaid**, e nomes vindos do GEDCOM passaram a poder **derrubar o diagrama inteiro**. Gerou o `BUG-20260929-J6PQ` (escape incompleto) e o `BUG-20261002-T4ZM` (rótulo descartando caracteres inertes) — ambos tratados no ADR-05.
- O diagrama passou a **depender de JavaScript no navegador**. Consequência operacional direta: o último golden file pendente (`SCR-G03`, indicador de carregamento) **não pode** ser capturado por `curl`, porque exige navegador headless.

## Alternativas consideradas

Não registradas. O ADR é reconstruído de evidência de código e de registro de bug, não de prosa de decisão.
