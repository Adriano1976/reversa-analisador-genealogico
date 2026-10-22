# Adendo: a lista de conexões passou a ser paginada

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

A tela de resultados entregava a análise inteira numa rolagem só — **68 cartões e ≈ 3,9 MB** de HTML
na análise medida neste repositório. A feature põe **paginação sobre a lista de cartões**: 10 por
página como padrão, com escolha entre **10, 20 e 30**, posição ("Página 1 de 7"), anterior/próxima e
os números das páginas.

A decisão que define a feature é **onde** paginar. Não é no servidor: a análise não é cacheada entre
requisições (`architecture.md#1`), e cada `POST` reparseia o GEDCOM inteiro — de 12 a 31 s no arquivo
real. A paginação é uma **camada de apresentação sobre o documento**: os 68 cartões continuam no HTML,
e o script marca e desmarca `hidden` nos que não pertencem à página corrente. Nada é re-renderizado,
nada é recarregado, nenhum cálculo é refeito.

**Nenhuma linha de Python de produção mudou.** `src/app.py`, `src/application/`, `src/core/` e
`src/ports/` estão idênticos; o delta é de template, folha de estilo e testes.

**14 de 14 ações concluídas.** Suíte: **1615 passed, 9 skipped** (baseline 1585/9).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §1 (camada Apresentação) | `componente-novo` | A tela de resultados ganhou uma superfície nova: o controle de paginação (`nav.paginacao-das-conexoes`), com seletor de tamanho, posição e navegação |
| `_reversa_sdd/architecture.md` | §1 (camada Apresentação) | `delta-de-contrato-externo` | O **corpo HTML** de `POST /` com `action=dna_analysis` mudou; o request, o status e os erros **não**. O tamanho da página não viaja no formulário |
| `_reversa_sdd/architecture.md` | §3 (Apresentação, script) | `regra-alterada` | O script da tela passou a manter o estado da página em closure e a **revelar a página de um cartão antes de abri-lo** — a ordem é contrato, porque abrir um cartão escondido faz o Mermaid medir um container de tamanho zero |
| `_reversa_sdd/domain.md` | §3.9 (Ordem de apresentação dos resultados) | `regra-alterada` | A **ordem não mudou** (documental primeiro, cM decrescente). O que mudou é que a lista passou a ser lida em páginas de 10, 20 ou 30, e só a página corrente é exibida |
| `_reversa_sdd/analise-dna/requirements.md` | §Regras de Negócio (Apresentação) | `regra-alterada` | `BR-D-41` e `BR-D-42` continuam valendo. A leitura precisa acrescentar: a contagem do topo é a da **análise** (68), nunca a da página (10) — é a "correção" que alguém faria de boa-fé |
| `_reversa_sdd/analise-dna/requirements.md` | §Regras de Negócio (`BR-D-74`) | `delta-de-dados` | `ordinal` continua sendo a posição na **lista inteira**. A página é uma janela sobre a ordem, não uma reordenação — redefini-la por página faria o histórico do banco guardar números repetidos |
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` | "Nada sai do documento" e os dois botões | `regra-alterada` | Nada é removido: os 68 cartões seguem no HTML e nascem **todos visíveis**. Entrou uma camada de visibilidade (`hidden`) aplicada pelo script, e "Expandir todas"/"Recolher todas" passaram a agir nos cartões da **página corrente** |
| `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md` | "O acoplamento que sobrou" | `regra-alterada` | O "Voltar" continua apontando para `#resultados` e não troca a página corrente. Um `#resultado-N` passou a mostrar a página que contém N **e depois** abrir o cartão |
| `_reversa_sdd/architecture.md` | §7 (dívidas, #21) | `regra-alterada` | O `sha256` da tela mantido à mão teve a **quarta** atualização declarada: 42.290 → **46.264 bytes** (+3.974, todos de script). O adendo `018` registrou a primeira |

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004`, `W005`, `W006`, `W007`, `W008` — em
`_reversa_forward/046-paginacao-dos-resultados/regression-watch.md`.

## Fontes

- `_reversa_forward/046-paginacao-dos-resultados/requirements.md`
- `_reversa_forward/046-paginacao-dos-resultados/roadmap.md`
- `_reversa_forward/046-paginacao-dos-resultados/legacy-impact.md`
- `_reversa_forward/046-paginacao-dos-resultados/regression-watch.md`
- `_reversa_forward/046-paginacao-dos-resultados/progress.jsonl`
- `_reversa_forward/046-paginacao-dos-resultados/data-delta.md`
- `_reversa_forward/046-paginacao-dos-resultados/interfaces/bloco-de-paginacao.html`
