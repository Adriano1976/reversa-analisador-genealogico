# Roadmap: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Requirements: `_reversa_forward/050-imprimir-resultado-por-pessoa/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A análise já chega inteira ao navegador: o documento de resultado é a única cópia que existe, e é
sobre ele que a impressão trabalha. **Nenhuma rota, `action` ou variável de contexto nova** — a
feature vive em dois arquivos de apresentação (`src/templates/index.html` e `src/assets/app.css`) mais
os testes.

O comando nasce no cabeçalho de cada cartão, ao lado do "Voltar", dentro do `summary`, com a mesma
guarda de propagação que o link já usa. Ao ser acionado, o cartão é **aberto** (para o desenho ser
medido e renderizado), **clonado** para um contêiner de impressão no fim do `<body>`, com todos os
`details` abertos e os diagramas movidos para o fim, cada um em folha própria. O `<body>` recebe a
classe `imprimindo` e a folha de estilo, em `@media print`, esconde tudo que não é o contêiner. O
diálogo do navegador abre; o `afterprint` remove o clone e devolve o cartão ao estado anterior.

A identificação da folha **já existe no contexto do resultado**: a árvore e o CSV são as referências
(`chave__rótulo.ext`) e a raiz é o que o operador digitou. É a mesma chave de conteúdo que a auditoria
da 049 usa, então a folha e a trilha falam a mesma língua — sem divergência de privacidade a declarar.

Uma coisa **não** é possível, e está registrada em `D-07`: a numeração "página N de M".

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca entram no versionamento | Os testes usam `tests/fixtures/sample_dna.py` e `sample_gedcom.py`; a impressão não grava artefato, e a verificação manual só usa fixture sintética. Nenhum PDF ou captura de dado real entra em `evidence/` | respeita |
| II. Comportamento observável preservado em refatoração | A tela ganha um controle visível: é **mudança observável declarada**, não refactor. O fluxo é o de requisito, e os literais existentes não mudam (`RF-11`) | respeita |
| III. Nenhuma mudança sem teste que a cubra | Marcação, folha e a ligação do script são presas por teste. O **comportamento de script** (o clique não recolher o cartão, a quebra de página, a repetição do rodapé) só se verifica em navegador: a suíte não executa JavaScript. **Cobertura parcial declarada** | conflita (parcial) |
| IV. Arestas do grafo são tipadas | A feature não atravessa o grafo: imprime o que a análise já decidiu | respeita (não se aplica) |
| V. Toda suposição de genealogia cita a fonte | Nenhum número de domínio novo é introduzido; o cM impresso é o que veio do CSV e da tabela do SCP 4.0 | respeita (não se aplica) |

> O conflito com o Princípio III é **declarado, não atenuado**: fechá-lo exigiria executar JavaScript
> na suíte, o que o projeto não faz desde a `046`. A mitigação é o par marcação ↔ folha mais o roteiro
> manual de `onboarding.md`, com o mesmo tratamento que a `030` deu ao binário `dot`.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A impressão é **100% no cliente**, sem rota, `action` ou requisição | O documento já está no navegador; o servidor não guarda a análise (`architecture.md#1`), e um endpoint de impressão teria de reexecutar o núcleo (12 a 31 s, `046`) ou receber o payload inteiro de volta | (a) `POST /` com `action=imprimir`; (b) página de impressão própria; (c) PDF gerado no servidor | 🟢 |
| D-02 | O comando é um `<button type="button">` **no cabeçalho do cartão**, ao lado do "Voltar", com `preventDefault` + `stopPropagation` | É o único lugar visível com o cartão fechado (decisão de 2026-10-26). O `summary` é o gatilho do recolhimento: sem a guarda, o clique fecharia o cartão. O projeto já usa a guarda para o link (`index.html#L2022`) | (a) no corpo do cartão (exigiria abrir antes); (b) barra fixa no topo (não diz de quem é); (c) ícone sem texto (não há conjunto de ícones no projeto) | 🟢 |
| D-03 | O isolamento é feito **clonando o cartão** para `#area-de-impressao` no fim do `<body>`, com `body.imprimindo` e `@media print` escondendo `body > *` exceto o contêiner | A regra de ocultação fica trivial e robusta (um seletor), sem depender de `:has()` nem de esconder a cadeia de ancestrais. O documento original não é movido | (a) esconder ancestrais por CSS (frágil a cada mudança de layout); (b) `visibility:hidden` (deixa folhas em branco); (c) abrir janela nova com `document.write` (perde a folha e o SVG); (d) `:has()` (cobertura de navegador) | 🟡 |
| D-04 | **Abrir o cartão antes de clonar**, e restaurar o estado no fim | O Mermaid mede o contêiner: dentro de `details` fechado o tamanho é zero e o desenho sai quebrado — a `046` já registra a ordem como contrato | Clonar fechado e abrir no clone (o clone fora da tela também mede zero) | 🟢 |
| D-05 | A espera do desenho é um **`MutationObserver`** no cartão até todo `.mermaid` ter `svg`, com **teto de 2 s**; estourou, imprime sem o desenho | `mermaid.run` é assíncrono e o `toggle` existente não devolve promessa. O teto impede o diálogo de nunca abrir | (a) `setTimeout` fixo (arbitrário); (b) promessa explícita no `toggle` (mexe no caminho quente da tela) | 🟡 |
| D-06 | Os diagramas do cartão (`.grafo-do-registro` e `.arvore-sugerida`) vão para o **fim do documento clonado**, cada um precedido de título e abrindo folha (`break-before: page`) | Decisão de 2026-10-26 (folha própria para o caminho). A árvore sugerida recebe o mesmo tratamento porque sofreria o mesmo corte no meio de uma seção | (a) deixar o desenho no lugar e aceitar o corte; (b) imprimir só o caminho textual | 🟢 |
| D-07 | **Não haverá "página N de M" no documento.** O rodapé repetido traz a origem e a identificação; a numeração fica com o cabeçalho/rodapé nativo do navegador | O modelo de impressão dos navegadores-alvo não expõe contadores de página ao documento: caixas de margem de `@page` (`counter(page)`) não são implementadas por Chrome, Edge, Firefox nem Safari | (a) paginar o conteúdo à mão (quebraria com qualquer mudança de conteúdo); (b) gerar PDF no servidor (novo runtime, `D-01`); (c) prometer e não entregar | 🟢 |
| D-08 | A identificação usa as **referências já recebidas** (`gedcom_filename`, `csv_filename_usado`, `root_name_usado`), sem variável de contexto nova | Os três campos já estão no render do resultado (`src/app.py#L566-L576`). A referência é `chave__rótulo.ext`: identifica o arquivo sem ambiguidade e carrega a **mesma chave de conteúdo** da auditoria (`049`) | (a) rótulo visível (exigiria decompor no Python e mexer no contexto); (b) só o nome da árvore (ambíguo entre envios) | 🟢 |
| D-09 | A impressão é **sempre no tema claro**, mesmo com a tela no escuro | O papel não tem tema, e o cartão no escuro imprime fundo escuro (tinta e legibilidade). Os tokens (`--bg`, `--surface`, `--ink`, `--line`, `--primary`) são redeclarados em `body.imprimindo`, que cobre o contêiner de impressão | (a) respeitar o tema da tela; (b) inverter cores por filtro | 🟢 |
| D-10 | O estado é restaurado no **`afterprint`**, com `setTimeout` de segurança e **guarda de reentrância** | O cartão foi aberto para o desenho medir; deixá-lo aberto cobraria do operador uma ação que ele não pediu. O `afterprint` não é uniforme entre navegadores | (a) deixar aberto; (b) recarregar a página | 🟡 |
| D-11 | Os testes novos prendem **marcação, folha e ligação do script**, e o `SHA_DA_TELA` é atualizado com a nona medição declarada | É o padrão do projeto desde a `046` e a única forma de prender a feature numa suíte que não executa JavaScript | (a) teste de navegador (não há infraestrutura); (b) confiar em verificação manual | 🟢 |
| D-12 | **Nenhuma dependência nova e nenhuma linha de Python de produção** | O que falta já está no navegador e no contexto; `requirements.txt` é lista de runtime e a `049` consolidou a regra | (a) biblioteca de PDF; (b) filtro Jinja novo para decompor a referência | 🟢 |
| D-13 | Os **selos de estado são reestilizados para papel**: borda na cor do estado e tinta escura sobre branco, em vez de texto branco sobre cor cheia | O navegador **não imprime fundos por padrão** (`print-color-adjust: economy`), e os selos usam texto branco sobre cor cheia — sem o fundo, o texto desaparece no papel. A reestilização também garante legibilidade em preto e branco, como o `RNF Papel` exige | (a) `print-color-adjust: exact` (não resolve impressora preto e branco e não é uniforme entre navegadores); (b) deixar como está (selo invisível) | 🟢 |

## 4. Premissas

Nenhuma premissa herdada de `[DÚVIDA]`: as três foram resolvidas na sessão de 2026-10-26
(`requirements.md#9`). A única decisão que **se afasta de um requisito** é a `D-07`, que deixa o
`RF-04` parcialmente não cumprido; ela está registrada como risco `R-01` e deve voltar ao
`/reversa-audit` para decidir se o `RF-04` é reescrito — este plano não altera o `requirements.md`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Tela de resultados (`index.html`) | `_reversa_sdd/architecture.md#3` | contrato-alterado | Ganha o botão por cartão, o bloco de identificação por cartão, o contêiner `#area-de-impressao` e o bloco de script de impressão |
| Folha de estilo (`app.css`) | `_reversa_sdd/architecture.md#3` | componente-alterado | Ganha o bloco `@media print`, a classe do comando e a da identificação; as regras de tela não mudam |
| Script da tela | `_reversa_sdd/architecture.md#3` | regra-nova | Entra a rotina de impressão (clone, abertura, espera, restauração), ao lado da paginação e do recolhimento existentes |
| Caso de uso `analise-dna`, núcleo, portas, `reporting/` | `_reversa_sdd/analise-dna/design.md` | sem mudança | Nenhuma linha de Python muda; nenhum payload, tabela ou regra de domínio é tocado |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma** estrutura de domínio, payload, tabela ou migração. O delta é de
  DOM — um contêiner, um botão e um bloco de identificação por cartão.
- Detalhe completo em: `_reversa_forward/050-imprimir-resultado-por-pessoa/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Corpo HTML de `POST /` com `action=dna_analysis` | HTTP (corpo) | `_reversa_forward/050-imprimir-resultado-por-pessoa/interfaces/bloco-de-impressao.md` |

O contrato HTTP **não muda**: mesmo método, mesma `action`, mesmos campos, mesmos status e mesmas
mensagens. O que muda é o documento entregue no corpo, e o detalhe está no arquivo acima.

## 8. Plano de migração

**n/a** — nenhum dado migra. A única "migração" é de bytes renderizados, e ela tem dono declarado:

1. Atualizar o template (`index.html`) e a folha (`app.css`).
2. Escrever os testes novos e atualizar o `SHA_DA_TELA` com a nona medição, declarando a origem do
   delta no próprio comentário do teste.
3. Medir a suíte e a paridade; a paridade deve continuar 100 %, porque o contexto não muda.
4. Verificar a impressão nos quatro navegadores com fixture sintética e registrar em `evidence/`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `R-01` O `RF-04` pedia "página N de M", e o documento impresso não consegue numerar folhas (`D-07`) | alto | alta (certeza) | Rodapé fixo repetido com origem e identificação; a numeração fica com o diálogo do navegador. **Resolvido em 2026-10-26:** o `RF-04` foi reescrito sem a numeração, na segunda sessão de esclarecimentos |
| `R-02` Quebra de página e margens variam entre navegadores | alto | média | Regras conservadoras (`break-before` na folha do desenho, `break-inside: avoid` em linhas de tabela), sem depender de `@page`; verificação manual nos quatro navegadores |
| `R-03` O desenho não fica pronto antes do diálogo | médio | média | `MutationObserver` com teto de 2 s (`D-05`); sem SVG, imprime sem ele — o caminho textual continua na seção 1 |
| `R-04` O clone duplica `id`s e âncoras | baixo | média | Remover o `id` do cartão clonado; o clone é descartado no `afterprint`. Os `id`s internos do SVG ficam, porque os `url(#…)` apontam para o original idêntico |
| `R-05` O rodapé fixo pode não repetir em algum navegador | médio | média | Verificação manual; fallback é um rodapé no fim do documento clonado |
| `R-06` Cobertura parcial do Princípio III: a suíte não executa o comportamento de script | médio | alta (certeza) | Testes de marcação/folha/script + roteiro manual com checkboxes em `onboarding.md` |
| `R-07` Crescimento do HTML: um bloco de identificação por cartão | baixo | alta (certeza) | Medir o HTML da análise e o bloco de identificação; se o acréscimo passar de ~25 KB, avaliar outra forma de montar a identificação |
| `R-08` Tema escuro vazando para o papel | baixo | média | `D-09`: tokens redeclarados em `body.imprimindo`; verificação com o tema escuro ligado |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Suíte verde, sem ajustar teste existente para passar (marco medido no início da execução)
- [ ] Paridade sem divergência nova: o contexto de render não muda e as 30 divergências pré-existentes em `ancestral` (medidas na `049`) são a linha de base — nenhuma delas pode crescer
- [ ] `SHA_DA_TELA` atualizado com a nona medição declarada no comentário
- [ ] Impressão verificada nos quatro navegadores com fixture sintética, com evidência em `evidence/`
- [ ] `RF-04` cumprido na forma reescrita: identificação no topo e origem em toda folha
- [ ] Nenhuma dependência nova, nenhuma linha de Python de produção, `git status` sem arquivo de `src/uploads/`
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-26 | Versão inicial gerada por `/reversa-plan` | reversa |
| 2026-10-26 | Correção pós-auditoria: `R-01` marcado como resolvido pela reescrita do `RF-04`; critério de paridade alinhado à linha de base da `049`; `D-09`/`R-08` alinhados a `body.imprimindo`; mitigação de `R-07` ajustada à medição possível | reversa |
