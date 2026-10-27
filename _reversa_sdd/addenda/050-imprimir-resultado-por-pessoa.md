# Adendo: o resultado de uma conexão pode ser impresso sozinho

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e
> `_reversa_sdd/analise-dna/requirements.md`)

## Vigência

Vigente desde 2026-10-26.

## Resumo da entrega

O resultado da análise de DNA só existia dentro do navegador: os cartões chegavam na resposta de um
`POST` que reparseia a árvore, e não havia como levar uma conexão para fora da tela. A entrega
acrescenta, no cabeçalho de cada cartão "Análise de conexão com ...", o comando **Imprimir**, que
monta no cliente um documento de **uma pessoa** — as cinco seções, os blocos recolhidos abertos e o
diagrama do caminho numa folha própria no fim —, com a identificação da análise (árvore, CSV e raiz
pela **referência armazenada**) e um rodapé de origem repetido em toda folha.

A impressão é 100 % no cliente: **nenhuma rota, `action`, dependência ou variável de contexto nova**, e
a análise não é reexecutada. O documento é um clone do cartão, isolado por `body.imprimindo` e por uma
regra de `@media print`, com o desenho esperado por `MutationObserver` (teto de 2 s) e o estado da tela
restaurado no `afterprint`.

**16 de 16 ações concluídas.** Suíte: **1717 passam / 9 pulados / 0 falham** (30 testes novos). A
paridade repetiu as **30 divergências** já registradas como pré-existentes pela `049`; a feature não
participa da comparação, porque o harness troca o render por captura de contexto.

**Duas coisas ficam declaradas.** A numeração "página N de M" **não** é entregue: o modelo de
impressão dos navegadores não expõe contadores ao documento, e o `RF-04` foi reescrito em 2026-10-26
para exigir só a origem em toda folha. E a impressão **não é auditada** — não há requisição, então não
há linha na trilha da `049`; é consequência da escolha, não esquecimento.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §1 (visão/apresentação) | `delta-de-contrato-externo` | O **corpo HTML** de `POST /` com `action=dna_analysis` ganha um botão de impressão por cartão, um bloco de identificação oculto e o contêiner `#area-de-impressao`; método, `action`, campos, status e mensagens **não** mudam |
| `_reversa_sdd/architecture.md` | §3 (componentes e estrutura de pacotes) | `regra-nova` | A tela de resultados passa a imprimir no cliente: clona o cartão, isola por `body.imprimindo`, espera o SVG do desenho e restaura o estado no `afterprint`. A folha `src/assets/app.css` ganha o bloco `@media print` (`componente-alterado`, não novo) |
| `_reversa_sdd/domain.md` | §5 (contrato de mensagens ao usuário) | `regra-nova` | Entra **um** texto visível novo — "Imprimir" —, no cabeçalho do cartão; os 29 literais catalogados não mudaram. A identificação da folha é conteúdo de impressão e não aparece na tela |
| `_reversa_sdd/analise-dna/requirements.md` | Apresentação | `regra-nova` | O resultado de uma conexão pode ser impresso sozinho, com a árvore e o CSV identificados pela **referência** (`chave__rótulo.ext`), a raiz digitada e o diagrama em folha própria; nada é recalculado, reordenado ou completado |
| `_reversa_sdd/analise-dna/requirements.md` | RNF Observabilidade | `regra-alterada` | A impressão não gera evento de servidor e não entra na trilha de auditoria da `049`; a RNF de observabilidade do resultado não precisa cobrir impressão |

## Regras sob vigilância

`W001` a `W010` — em `_reversa_forward/050-imprimir-resultado-por-pessoa/regression-watch.md`.

## Fontes

- `_reversa_forward/050-imprimir-resultado-por-pessoa/requirements.md`
- `_reversa_forward/050-imprimir-resultado-por-pessoa/roadmap.md`
- `_reversa_forward/050-imprimir-resultado-por-pessoa/actions.md`
- `_reversa_forward/050-imprimir-resultado-por-pessoa/legacy-impact.md`
- `_reversa_forward/050-imprimir-resultado-por-pessoa/regression-watch.md`
- `_reversa_forward/050-imprimir-resultado-por-pessoa/progress.jsonl`
- `_reversa_forward/050-imprimir-resultado-por-pessoa/interfaces/bloco-de-impressao.md`
