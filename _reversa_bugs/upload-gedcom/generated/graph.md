<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em 2026-10-10T03:28:36-03:00 a partir de 2 bugs -->

# Grafo de bugs · upload-gedcom

```mermaid
graph LR
  SIX["#6 6RKP<br/>nome com acento nao resolve<br/>high · upload"]
  style SIX fill:#2b1b1b,stroke:#e05252,color:#f5f5f5
  QMLY["#2 QMLY<br/>restrito<br/>high · upload"]
  style QMLY fill:#2b1b1b,stroke:#e05252,color:#f5f5f5
  BJJH["#1 BJJH<br/>restrito<br/>critical · upload<br/>contexto: busca-caminho"]
  style BJJH fill:#1b1b22,stroke:#5a5a7a,color:#c9c9c9,stroke-dasharray:4 3
  SIX -->|related-to confirmed| QMLY
  QMLY -->|related-to confirmed| BJJH
```

Estilo: aresta cheia é `supported` ou `confirmed`; aresta tracejada é `proposed`, isto é, hipótese.
Nó com borda vermelha tem severidade `high` ou `critical`; amarela, `medium`. Nós de outros contextos
aparecem com borda tracejada e o contexto declarado.

**As duas arestas deste grafo estão cheias.** A única que era tracejada — `6RKP -> QMLY` — foi
confirmada pelo fix de 2026-10-10 e deixou de ser hipótese.

## Clusters

**Um cluster, e ele é o que esta regeneração passou a enxergar.** Enquanto o contexto tinha um único bug,
não havia convergência a medir. Agora há dois, e os dois tocam a **mesma região de código**: a composição
do nome armazenado.

O `BUG-20260929-QMLY` é quem **criou** essa forma. Antes dele o legado gravava com o nome enviado pelo
cliente (`os.path.join(UPLOAD_FOLDER, gedcom_file.filename)`), o que permitia escrita fora da pasta; a
correção tirou do cliente o controle do caminho e passou a compor
`<16 hex do sha256 do conteúdo>__<nome visível>`, com a forma fechada
`^[0-9a-f]{16}__[A-Za-z0-9._-]+$` como defesa, sem lista negra.

O `BUG-20261009-6RKP` é uma **contradição dentro** dessa forma: a metade que grava preserva acento e
espaço no nome visível, e a metade que lê recusava os dois. As duas metades vivem no mesmo arquivo
(`src/utils/validate.py`), e a spec que as manda conviver (`_reversa_sdd/upload-gedcom/contracts.md`,
linhas 51 e 53) se contradizia nas duas linhas vizinhas.

Leitura de triagem, **confirmada pelo fix**: não são dois defeitos independentes, são duas camadas do
mesmo movimento. Quem corrigiu o `6RKP` mexeu exatamente no contrato que o `QMLY` estabeleceu, e a
decisão de qual lado cede foi uma revisão daquele contrato, e não um conserto local. O operador decidiu
que **o código cede** — o resolvedor passa a aceitar o que o gravador produz —, e isso virou a `RN-20`.

A aresta para `busca-caminho` continua sendo outra história: ela liga os dois bugs pelo mecanismo da
pasta de upload única com o nome controlado pelo cliente.

## Impact score

Heurística de triagem (`causados*3 + bloqueados*2 + regressões*4 + relacionados*1`), contando apenas
arestas `supported`/`confirmed`, e apenas para bug aberto. `related-to` tem peso limitado a 3 no total.
Não substitui `priority` nem `severity`.

| Bug aberto | causados ×3 | bloqueados ×2 | regressões ×4 | relacionados ×1 | Score |
|------------|-------------|---------------|---------------|-----------------|-------|
| (nenhum) | 0 | 0 | 0 | 0 | — |

**Nenhum bug aberto neste contexto**, então não há impacto a pontuar: os 2 bugs estão `resolved`. Enquanto
o `6RKP` estava aberto o score dele era **0**, porque a única aresta estava em `proposed`; o fix
confirmou essa aresta, e ela teria levado o score a 1.

O `BUG-20260929-QMLY` está `resolved`, e a aresta dele já está contada no lado que a gravou.
