# Roadmap: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`
> Requirements: `_reversa_forward/036-refino-do-cartao-de-resultado/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A mudança é de **apresentação** e vive em duas superfícies: o `h5` do cartão de resultado, no template
(`src/templates/index.html:583-683`), e um bloco novo de regras escopadas em `.cartao-do-resultado`, na
folha servida por `GET /app.css` (`src/assets/app.css`).

O `h5` passa a ter três faixas — título, selos e sinais — dentro de um `span.conteudo-do-cabecalho`;
o link "Voltar" sai de `float:right` e vira item de um `h5` em `flex`, alinhado ao centro. A caixa do
indicador de abrir é um `::before` do `summary` e o chevron continua sendo o `::after`, agora
posicionado por cima da caixa. O cartão ganha barra lateral, raio e sombra com tokens que já existem.

**Nada é renomeado, nada é removido e nenhum texto muda.** As regras genéricas de `summary` que os
blocos irmãos usam ficam intactas — o refino é escopado por `.cartao-do-resultado`, e é isso que
preserva "Matches descartados" e "Observações do arquivo" como apêndice e aviso (`RN-07`).

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | O onboarding usa GEDCOM e CSV sintéticos; o mockup do operador (que tem nome de pessoa) fica fora do repositório e não é transcrito | respeita |
| II. Comportamento observável é preservado em refatoração | A feature é de apresentação: nenhuma saída de domínio, rota, payload ou mensagem muda; o recolhimento e a âncora continuam iguais | respeita |
| III. Nenhuma mudança sem teste que a cubra | As mudanças de markup são cobertas pelas guardas existentes (estrutura do cartão, contraste dos selos, hash da tela); a folha ganha teste de contrato de classe e o contraste é medido | respeita |
| IV. Arestas do grafo são tipadas | Não há travessia de grafo nesta feature | respeita (não se aplica) |
| V. Toda suposição de genealogia genética cita a fonte | Nenhum número de domínio (cM, faixa, MRCA) é criado ou alterado | respeita (não se aplica) |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Manter a árvore `details.card.cartao-do-resultado` → `summary.sumario-do-cartao` → `div.card-header` → `h5` e agrupar as três faixas em `span`s dentro do `h5` | Os extratores dos testes cortam o cabeçalho no **primeiro `</div>`** (`test_cartoes_recolhiveis.py:181`, `test_estado_do_resultado.py:139`); um `div` novo dentro do `card-header` truncaria a extração e derrubaria guardas | `div.conteudo-do-cabecalho`, `section`, `header` | 🟢 |
| D-02 | `h5` em `display:flex; align-items:center; gap:1rem`, com `.conteudo-do-cabecalho{flex:1 1 auto;min-width:0}` e o "Voltar" como segundo item | Centra a ação verticalmente nas três faixas sem posicionamento absoluto e permite `min-width:0` para o nome longo quebrar dentro da faixa | `grid` com `grid-row:1/-1` (frágil com linhas implícitas), `float:right` mantido (não centraliza) | 🟢 |
| D-03 | O "Voltar" continua sendo `<a class="voltar-ao-indice" href="#resultados">Voltar<span class="visually-hidden">…</span></a>`, sem markup novo; o chevron à esquerda é um `::before` com bordas giradas | O regex de `test_estado_do_resultado.py:222-229` exige texto puro entre `>` e o `span.visually-hidden`; um `<svg>` ou `<span>` de ícone quebraria o teste com a tela certa | `<svg>` inline, `<i>` de ícone, trocar o texto por "← Voltar" | 🟢 |
| D-04 | A caixa do indicador é um `::before` absoluto do `summary`, e o chevron (`::after`) ganha `position:absolute` **escopado** em `.cartao-do-resultado`; as regras genéricas de `details.card > summary…::after` ficam intactas | `test_cartoes_recolhiveis.py:432-446` exige os literais das regras genéricas e as duas rotações; os blocos irmãos continuam com o losango atual (`RN-07`) | Trocar o losango por SVG em `background-image` (perde o giro comprovado por teste), animar `::after` com `translate` (o teste exige `transform:rotate(...)` literal) | 🟢 |
| D-05 | A barra lateral usa `linear-gradient(180deg, var(--muted), var(--head))` | São tokens dos dois temas; a barra mede 6,11→10,87:1 no claro e 6,48→12,14:1 no escuro contra a superfície. Não usa cor de veredito, aviso ou ação (`RN-04`) | `--aviso-line` (dourado de aviso), `--primary` (cor de ação), literal `#8a7759` do mockup | 🟢 |
| D-06 | A superfície do cartão é `linear-gradient(180deg, var(--surface), var(--surface-2))`, com sombra só no claro e borda no escuro; o `details` ganha `position:relative` para ancorar a barra | Dá o painel do mockup dentro da paleta; no escuro a sombra não separa, então a separação fica na borda e no degradê | `background: var(--surface)` plano (mantém a chapa lisa), `--surface-2` inteiro (perde o branco do topo) | 🟢 |
| D-07 | Todas as regras novas são escopadas em `.cartao-do-resultado` | `RN-07`: os blocos `bloco-descartados` e `observacoes-do-arquivo` compartilham `details.card > summary.sumario-do-cartao` e não podem mudar | Aplicar a todos os `summary.sumario-do-cartao` (muda os irmãos), classe nova no `<details>` (muda o marcador que os testes procuram) | 🟢 |
| D-08 | `.cartao-do-resultado > summary.sumario-do-cartao:hover{text-decoration:none}` | A regra global `details>summary:hover` (0,1,2) sublinha o cabeçalho inteiro; o seletor escopado (0,2,1) vence sem `!important` | Remover a regra global (muda os outros `summary` da tela) | 🟢 |
| D-09 | Título em `.titulo-da-conexao{display:block;font-size:1.4rem;line-height:1.2}` | Fixa o valor decidido na sessão de 2026-10-19 (opção 2a) e mantém o `h2` (1,6 rem) acima | alterar `.card-header h5` (alcançaria o bloco dos descartados) | 🟢 |
| D-10 | Abaixo de 575,98 px o `h5` ganha `flex-wrap:wrap` e o conteúdo `flex-basis:100%`, jogando o "Voltar" para a própria linha | `RF-08`: em 320 px o título e a pílula não cabem lado a lado; o breakpoint já existe na folha | esconder o "Voltar" no telefone (perde a ação), reduzir a pílula (colide com o chevron) | 🟢 |
| D-11 | Nenhuma animação de entrada; transições de `150ms` já usadas no indicador | `RN-10` (opção 3a): numa lista de 142 cartões, animação de entrada é custo sem ganho; `prefers-reduced-motion` já zera transições | `IntersectionObserver` por cartão (JS novo), `@keyframes` no carregamento | 🟢 |

## 4. Premissas

Nenhuma. As três decisões que estavam em aberto foram respondidas na sessão de 2026-10-19
(`requirements.md` §9) e viraram regras fechadas (`RN-07`, `RF-01`, `RN-10`).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Template da tela (borda de apresentação) | `_reversa_sdd/architecture.md#3`; `src/templates/index.html` | regra-alterada | O `h5` do cartão de resultado agrupa título, selos e sinais em `span`s e recebe o "Voltar" como item flex; nenhum elemento, rota ou dado novo |
| Folha de estilo da tela (rota `GET /app.css`) | `_reversa_sdd/architecture.md#3`; adendo `013` | regra-alterada | Bloco novo escopado em `.cartao-do-resultado` (superfície, barra, faixas, pílula, indicador, hover e telefone); as regras genéricas de `summary` ficam intactas |

Nenhum componente novo, extinto, contrato novo ou removido. O contrato de `GET /app.css` (método,
`Content-Type`, `ETag`, `304`, `404`) não muda.

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma**. A feature lê os mesmos campos do payload de resultado
  (`match_name`, `cm`, `comparison`, `identidade`, `validacao_*`, `documentary`, `janela_de_vida`,
  `profundidade_*`) e não grava nada.
- Detalhe completo em: `_reversa_forward/036-refino-do-cartao-de-resultado/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `GET /` (tela vazia) | HTTP | n/a — o HTML não muda (a alteração vive sob `{% if dna_results %}`) |
| `GET /app.css` | HTTP | n/a — mesmo arquivo, mesmo contrato; só o conteúdo muda |

Nenhum diretório `interfaces/` é criado.

## 8. Plano de migração

n/a. Não há dado persistido, schema, payload ou configuração a migrar.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Um `div` novo dentro do `card-header` trunca os extratores de teste | alto | baixa | `RN-05` + rodar `tests/test_cartoes_recolhiveis.py` e `tests/test_estado_do_resultado.py` antes de fechar a ação |
| A especificidade do Bootstrap (`.card-header`, `.badge`) vence as regras novas | médio | média | Escopar com `.cartao-do-resultado .card-header` (0,2,0) e conferir no DevTools; sem `!important` |
| A sombra não separa o cartão no tema escuro | médio | alta | Borda + degradê + barra carregam a separação no escuro (`RF-06`); medir os pares |
| O cabeçalho de 3 faixas aumenta muito a lista de 142 cartões | médio | alta | Resíduo declarado no requirements §10; o recolhimento e o HTML não mudam |
| Em 320 px o "Voltar" colide com o chevron | alto | média | `flex-wrap` + `flex-basis:100%` abaixo de 575,98 px (`D-10`); conferir no modo responsivo |
| O sublinhado global do `summary` volta a vencer | baixo | baixa | `D-08` com seletor mais específico; teste manual de hover no onboarding |
| O `SHA_DA_TELA` muda sem intenção | alto | baixa | Medir `GET /` antes e depois; a mudança está sob `{% if dna_results %}`, fora da tela vazia (`RF-10`) |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `requirements.md` sem marcador `[DÚVIDA]`
- [ ] Suíte com ≥ 1.282 passam e 11 pulados, 0 falhas; nenhum teste removido
- [ ] Guardas do cartão (`test_cartoes_recolhiveis.py`, `test_estado_do_resultado.py`, `test_estilo_da_tela.py`) verdes
- [ ] `GET /` medido antes e depois; hash inalterado ou atualizado com bloco datado
- [ ] Contraste dos elementos novos medido e registrado no comentário da folha
- [ ] `regression-watch.md` gerado no coding
- [ ] `git diff --stat -- src/` listando apenas `src/templates/index.html` e `src/assets/app.css`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-19 | Versão inicial gerada por `/reversa-plan` | reversa |
