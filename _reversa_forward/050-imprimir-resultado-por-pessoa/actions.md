# Actions: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Roadmap: `_reversa_forward/050-imprimir-resultado-por-pessoa/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 16 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 7 (T003 → T010 → T011 → T012 → T014 → T015 → T016) |

> **T017 e T018 foram retiradas** na correção pós-auditoria de 2026-10-26: eram verificações humanas
> (quatro navegadores, julgamento visual), não ações atômicas de agente. Os IDs ficam reservados e
> **não são reciclados**. O roteiro delas vive em `onboarding.md#8` e `#9`, e o gate continua no
> critério de pronto do `roadmap.md#10`.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Inserir o contêiner vazio `#area-de-impressao` com `aria-hidden="true"` no fim do ramo dos resultados, antes dos scripts, para que a tela de entrada vazia não ganhe marcação nova | - | - | `src/templates/index.html` | 🟢 | `[X]` |
| T002 | Inserir o botão `.imprimir-conexao` dentro de `.controles-do-cabecalho`, depois do link "Voltar", com `type="button"`, `data-imprimir="resultado-N"` e nome acessível que identifica a pessoa do cartão | - | - | `src/templates/index.html` | 🟢 | `[X]` |
| T003 | Inserir o bloco `.identificacao-da-impressao` no início do corpo de cada cartão, com árvore, CSV e raiz vindos do contexto e o `<time class="quando-da-impressao">` vazio | - | - | `src/templates/index.html` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Criar o arquivo de teste e prender a marcação: um botão por cartão com nome acessível e `data-imprimir`, a identificação com os três campos e o contêiner `#area-de-impressao` | T001, T002, T003 | - | `tests/test_impressao_do_resultado.py` | 🟢 | `[X]` |
| T005 | Acrescentar ao mesmo arquivo os pares classe ↔ folha e as regras de impressão: isolação do documento, controles fora da folha, identificação visível, folha do desenho, rodapé, selos de papel e tema claro | T004 | - | `tests/test_impressao_do_resultado.py` | 🟢 | `[X]` |
| T006 | Acrescentar ao mesmo arquivo as asserções de ligação do script: nomes da rotina, guarda `preventDefault`/`stopPropagation`, espera do desenho e restauração no `afterprint` | T005 | - | `tests/test_impressao_do_resultado.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Criar o bloco `@media print` de isolação — `body.imprimindo > *:not(#area-de-impressao){display:none}`, exibição do contêiner — e manter `#area-de-impressao{display:none}` na tela | T001 | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |
| T008 | Estilizar o comando e a identificação na tela e ocultá-los no papel (`.controles-do-cabecalho`, `.imprimir-conexao`, `.identificacao-da-impressao`) | T002, T003, T007 | - | `src/assets/app.css` | 🟢 | `[X]` |
| T009 | Escrever as regras de papel: `.folha-do-diagrama{break-before:page}`, `tr{break-inside:avoid}`, rodapé fixo `.origem-da-impressao`, tokens do tema claro e selos com borda e tinta escura | T007 | - | `src/assets/app.css` | 🟡 | `[X]` |
| T010 | Implementar o preenchimento do `<time>` no clique e a espera do desenho (`MutationObserver` até todo `.mermaid` do cartão ter `svg`, com teto de 2 s) | T003 | `[//]` | `src/templates/index.html` | 🟡 | `[X]` |
| T011 | Implementar a montagem do clone — `id` e `hidden` removidos, `details` abertos, classe `cartao-em-impressao` e o rodapé `.origem-da-impressao` criado — e mover os diagramas do cartão para `.folha-do-diagrama` com título | T003, T010 | - | `src/templates/index.html` | 🟡 | `[X]` |
| T012 | Implementar o disparo: guarda de reentrância, snapshot do estado, abertura do cartão, espera do desenho, montagem, classe `imprimindo` e `window.print()` | T010, T011 | - | `src/templates/index.html` | 🟡 | `[X]` |
| T013 | Implementar a restauração: `afterprint` mais temporizador de segurança, esvaziar o contêiner, devolver o `open` do cartão e a rolagem | T012 | - | `src/templates/index.html` | 🟡 | `[X]` |
| T014 | Ligar o clique do botão no `DOMContentLoaded` com `preventDefault` e `stopPropagation`, para o `summary` não abrir nem recolher o cartão | T012 | - | `src/templates/index.html` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Atualizar `SHA_DA_TELA` com a nona medição, declarando no comentário os bytes antes e depois e a origem do delta | T007, T008, T009, T012, T013, T014 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |
| T016 | Rodar a suíte completa e a paridade, medir o HTML da análise com a fixture de 68 conexões, conferir que nenhum arquivo de `src/` e o `requirements.txt` foram tocados pela feature, e registrar passam/pulados/falham e o veredito da paridade, sem ajustar teste para passar | T015 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

1. **A Fase 2 escreveu os testes antes da folha e do script.** T005 e T006 nasceram vermelhos (30
   falhas, 1 passe) e ficaram verdes quando T007–T014 entraram. É o Princípio III em prática.
2. **Só os inícios das duas correntes da Fase 3 carregam `[//]`** — `T007` (folha) e `T010` (script) —,
   porque são os únicos dois que não compartilham arquivo alvo. As correntes andaram em paralelo, mas
   cada passo seguinte dentro de uma corrente é sequencial: `T008`/`T009` no mesmo `app.css`,
   `T011`/`T012` no mesmo `index.html`.
3. **T015 é a única ação que mexeu num invariante mantido à mão.** O valor veio de medição, não de
   palpite: `5fc0b929…` (46.477 bytes) → `f49dd6da…` (51.117, **+4.640**), declarado no comentário.
4. **A verificação em navegador não é ação de agente.** `T017` e `T018` saíram: exigiam quatro
   navegadores e julgamento visual. O roteiro está em `onboarding.md#8` e `#9`, só com fixture
   sintética, e o resultado entra como gate do critério de pronto — o agente não pode declarar a
   feature fechada sem ele, mas também não pode executá-lo.

### Registros da execução

- **Suíte:** `1717 passed, 9 skipped, 0 failed` em **134,98 s**. São **30 testes novos** (o arquivo
  `tests/test_impressao_do_resultado.py`), então o marco anterior era 1687/9.
- **Paridade:** **30 divergências**, a mesma contagem da linha de base registrada pela `049` em
  checkout limpo do `HEAD`. A feature não participa da comparação — o harness troca o render por
  captura de contexto (`parity/harness.py#L191`) e a folha de estilo nem é buscada. O `exit 1` é o
  harness sinalizando divergência, não regressão desta feature.
- **HTML da análise** (fixture de 68 conexões): **3.571.080 bytes**, com **68 botões** e **68 blocos
  de identificação**. O bloco tem **652 bytes**, então o acréscimo é **44.336 bytes (~43 KB, 1,2 %)**
  — acima dos ~25 KB que a mitigação de `R-07` usou como gatilho. Mantido: a alternativa (bloco único
  preenchido por script) colidiria com o `RF-10` (marcação no HTML) e com o clone, que precisa da
  identificação **dentro** do cartão.
- **Nenhum arquivo `.py` de `src/` foi tocado** e o `requirements.txt` está intacto: o delta de
  produção são os dois arquivos de apresentação (`src/templates/index.html` e `src/assets/app.css`).

### Desvios de execução

- **O seletor dos diagramas mudou por causa de testes existentes.** O script não podia conter o
  literal `arvore-sugerida`: `tests/test_arvore_sugerida_na_tela.py` afirma que ele **não** aparece
  na página quando o bloco não existe, e a menção no script quebrava a asserção. A rotina passou a
  selecionar `details[class*='sugerida']` e `details[class*='grafo']`, e o título da folha sai de
  `className.includes("sugerida")`. Mesmo efeito, sem o literal.
- **O contêiner é movido para o fim do `<body>` no primeiro uso.** Ele nasce no ramo dos resultados
  (`RF-11`), mas a regra de isolação esconde tudo que não é filho direto do body; a mudança de pai
  acontece no clique, antes de montar o clone.
- **O temporizador de segurança da restauração é de 60 s**, e não de poucos segundos: em navegador
  que não bloqueia no `print()`, um prazo curto limparia o documento com a pré-visualização aberta.

## Emendas

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| E001 | O script da impressão troca o `document.title` para "Análise de conexão com <nome>" enquanto o diálogo está aberto, para o PDF sair com o nome da pessoa, e devolve o título original no `afterprint` | - | - | `src/templates/index.html` | 🟢 | `[X]` |

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-26 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-26 | Correção pós-auditoria: coluna `Status` restaurada nas 16 linhas; `[//]` restrito a `T007` e `T010`; `T017`/`T018` retiradas (verificação humana) e IDs reservados; nó `.origem-da-impressao` explicitado em `T011`; contêiner da `T001` movido para o ramo dos resultados | reversa |
| 2026-10-26 | Fechamento de `A010`/`A011`: `T016` passa a medir o HTML da análise e a conferir que `src/` e `requirements.txt` não foram tocados | reversa |
| 2026-10-26 | Execução do `/reversa-coding`: 16 de 16 ações concluídas; suíte 1717/9/0 e paridade na linha de base | reversa |
