# Roadmap: paginação dos Resultados das Análises de Conexão

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Requirements: `_reversa_forward/046-paginacao-dos-resultados/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A paginação é uma **camada de apresentação sobre a lista que já está no documento**. Nada é
recriado, nada é recarregado: o script marca `hidden` nos cartões que não pertencem à página
corrente e desmarca nos que pertencem. Os 68 cartões continuam no HTML, o estado de cada um
(aberto/fechado, diagrama já desenhado) continua intacto, e trocar de página não dispara
requisição nenhuma.

**Nenhuma linha de Python muda.** O template, a folha de estilo e o script são os únicos arquivos de
produção tocados — `src/app.py`, `src/application/`, `src/core/` e `src/ports/` ficam idênticos. É a
consequência direta da decisão: paginar no servidor custaria uma análise inteira por clique, porque
a arquitetura declara **não haver cache entre requisições** (`_reversa_sdd/architecture.md#1`).

O controle nasce no **HTML**, calculado pelo Jinja para o tamanho padrão (10). Ele não nasce no
script por uma razão de testabilidade, não de elegância: a suíte deste projeto lê a marcação
renderizada, e um controle criado só em tempo de execução não teria como ser preso por teste — o
que violaria o princípio III.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A verificação manual usa `src/uploads/`; a suíte usa as fixtures sintéticas de `tests/fixtures/`. Nenhum dado real entra em mock, documento ou teste | respeita |
| II. Comportamento observável é preservado em refatoração | Declarado no `requirements.md` §1: **é mudança de comportamento** (o padrão passa de "tudo" para "as 10 primeiras"), e por isso percorre o fluxo de requisito, não se disfarça de refactor | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cada regra `RN-*` tem teste em `tests/test_paginacao_na_tela.py`; a atualização de `SHA_DA_TELA` é decisão registrada, não descoberta | respeita |
| IV. Arestas do grafo são tipadas | A feature não percorre o grafo e não calcula parentesco | respeita (não se aplica) |
| V. Toda suposição de genealogia genética cita a fonte | A feature não produz número de domínio: o `10` é escolha de leitura do operador, não faixa de cM | respeita (não se aplica) |

Nenhum conflito com princípio ativo. **Um conflito com um adendo, e ele fica declarado**: o adendo
`018` recusa remover conteúdo do HTML ("nada sai do documento"), e a paginação esconde conteúdo —
a diferença é que **esconder não é remover**, e a consequência de esconder (a busca do navegador
não alcançar as outras páginas) está registrada em §9.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Paginar **no cliente**, sobre os cartões que já estão no DOM | A análise não é cacheada entre requisições (`architecture.md#1`): cada `POST` reparseia o GEDCOM inteiro. No arquivo real, uma análise leva de 12 a 31 s — por clique | a) paginar no servidor com `POST` por página; b) guardar o resultado em sessão/cache | 🟢 |
| D-02 | Esconder com o **atributo `hidden`** do cartão, mais uma regra própria na folha | `hidden` sai do fluxo de foco e da árvore de acessibilidade, ao contrário de opacidade ou posicionamento. A regra própria (`!important`) impede que um `display` de biblioteca vença o atributo | a) classe `.fora-da-pagina`; b) `visibility`/`opacity`; c) `clip` | 🟢 |
| D-03 | O controle **nasce no HTML**, com as páginas calculadas pelo Jinja para o tamanho padrão | A suíte prende marcação, não execução de script. Um controle criado só no `DOMContentLoaded` seria invisível para os testes | a) controle montado inteiro no script; b) controle estático com um número fixo de botões | 🟢 |
| D-04 | O estado da página vive em **duas variáveis de closure** dentro do IIFE que já existe | O script não tem estado global hoje, e não é esta feature que vai introduzir um. Fecha junto com a aba: `RN-14` | a) `data-` no `<body>`; b) `localStorage`; c) querystring | 🟢 |
| D-05 | Trocar de página **marca e desmarca** `hidden`; não re-renderiza nada | O cartão carrega estado que um re-render destruiria — `open`, `data-processed` do Mermaid, posição de rolagem interna | a) `innerHTML` com a página nova; b) clonar nós | 🟢 |
| D-06 | Fonte única do padrão: o `<option selected>`; o script lê `select.value` | `RN-03`/RNF de manutenibilidade. Um `10` repetido em três lugares é como o padrão se perde | a) constante no script; b) `data-padrao` no `<nav>` | 🟢 |
| D-07 | `abrirCartaoDoAlvo` **mostra a página do cartão antes de abrir** | Abrir com o cartão escondido dispara `toggle` e o Mermaid mede um container de tamanho zero (o problema que o `018` já documentou). O par é preso por teste | a) abrir e depois mostrar; b) não suportar `#resultado-N` | 🟢 |
| D-08 | "Expandir todas" e "Recolher todas" passam a operar sobre a **fatia visível** | `RN-10`. O helper `todosOsCartoes()` continua existindo para a paginação; quem muda é o consumidor dos botões | a) manter nos 68; b) remover os botões | 🟢 |
| D-09 | Trocar de página rola até `#resultados`, **sem mexer no hash** | `RF-13`. `scrollIntoView` não dispara `hashchange`, então não reabre cartão nenhum; e `#resultados` é o alvo que o "Voltar" já usa (`019`) | a) rolar para o primeiro cartão da página; b) não rolar | 🟡 |
| D-10 | **Nenhuma linha de Python muda** | O template consome a mesma lista `dna_results`; nenhum contexto novo é necessário, porque o total de páginas sai de `dna_results \| length` | a) calcular a paginação na borda e passar pronta | 🟢 |

## 4. Premissas

Nenhuma. As cinco perguntas da sessão de esclarecimentos de 2026-10-22 foram respondidas, e o
`requirements.md` está com **zero** marcadores `[DÚVIDA]`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| **Apresentação** — marcação | `_reversa_sdd/architecture.md#3` (camada Apresentação) | contrato-alterado | O bloco `nav.paginacao-das-conexoes` nasce entre o parágrafo de contagem e o primeiro cartão |
| **Apresentação** — script | `_reversa_sdd/architecture.md#3` | contrato-alterado | Ganha o estado da página, quatro ouvintes e a chamada que revela a página do alvo |
| **Apresentação** — folha | `_reversa_sdd/architecture.md#1` (Apresentação) | contrato-alterado | Sete classes novas e a guarda `details.cartao-do-resultado[hidden]` |
| **Borda HTTP** — `src/app.py` | `_reversa_sdd/architecture.md#3` (raiz) | **sem-mudança** | Nenhuma rota, `action` ou variável de contexto nova |
| **Borda HTTP** — corpo da resposta | `_reversa_sdd/analise-dna/contracts.md` | contrato-alterado | O HTML da análise ganha o bloco; `request` e `status` idênticos |
| **Núcleo, aplicação e portas** | `_reversa_sdd/architecture.md#3` | **sem-mudança** | Nenhuma regra de domínio, nenhum payload, nenhuma tabela |
| **Instrumentação de tela** | `tests/test_icone_de_atalho.py` | contrato-alterado | `SHA_DA_TELA` e `TAMANHO_ESPERADO` mudam por causa do `<script>` — declarado, não descoberto |

## 6. Delta no modelo de dados

- **Resumo:** nenhuma estrutura nova, nenhum campo novo, nenhuma migração. O estado da paginação são
  **dois inteiros no DOM** (`página`, `tamanho`), que morrem com a página e não chegam ao servidor.
- O contrato do campo persistido `match_result.ordinal` **não muda**: ele continua sendo a posição na
  ordem apresentada da **lista inteira**, nunca "a posição na página" (`BR-D-74`).
- Detalhe completo em: `_reversa_forward/046-paginacao-dos-resultados/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Corpo HTML de `POST /` com `action=dna_analysis` | HTML (resposta) | `_reversa_forward/046-paginacao-dos-resultados/interfaces/bloco-de-paginacao.html` |

O **request não muda**: o tamanho da página não viaja no formulário (é escolha de leitura, `D-01`).
Nenhuma rota nova, nenhum campo novo, nenhum código de erro novo.

## 8. Plano de migração

Não há dado a migrar: não há banco, arquivo ou configuração envolvidos. Há, porém, um invariante
mantido à mão que **precisa** ser movido junto:

1. Implementar marcação, folha e script.
2. Rodar a suíte completa e ler a falha de `test_icone_de_atalho.py`, que informa o tamanho real e o
   hash real da tela.
3. Atualizar `TAMANHO_ESPERADO` e `SHA_DA_TELA` com os valores **medidos**, nunca estimados.
4. Registrar a mudança em `legacy-impact.md` e no adendo da feature, com a frase que o próprio teste
   exige: o hash mede "a tela não mudou desde a última mudança declarada".

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Diagrama do Mermaid medindo container escondido | alto — diagrama desenhado com tamanho zero, sem erro visível | média | `D-07`: mostrar a página antes de abrir; teste prende a ordem no script |
| A busca do navegador (Ctrl+F) só alcança a página corrente | médio — o operador procura um nome e conclui que ele não está na análise | **alta** (é consequência de `hidden`) | Declarado em §9 e no adendo: a contagem do topo diz que existem 68, e a resposta definitiva é busca/filtro, não paginação |
| `SHA_DA_TELA` atualizado "para o teste passar" sem decisão | alto — o invariante deixa de prender o que promete | média | `D-10` não se aplica: a mudança de script é declarada e registrada no adendo; valor lido da falha, nunca chutado |
| Um `display` de biblioteca vencer o atributo `hidden` | alto — cartões aparecendo fora da página | média | Regra própria `details.cartao-do-resultado[hidden] { display: none !important; }` + teste que a exige na folha |
| Teste que conta cartões quebrar | médio — 68 asserções de estrutura | baixa | `RN-04`: nenhum cartão é removido; o teste `test_estado_do_resultado.py` roda sem alteração |
| Última página com o resto (68 → 8) calculada errado | médio — cartão inalcançável ou página vazia | baixa | `Math.ceil` no script e teste do caso 11 cartões → 2 páginas |
| Densidade do controle em análise grande (142 cartões → 15 números) | baixo — uma linha comprida | média | Resíduo registrado em `requirements.md` §10; o corte é a lista de números |
| Nenhuma verificação em navegador real | médio — o clique não é provado, só a ligação | **alta** | Mesmo limite declarado no adendo `018`, resíduo 1; `onboarding.md` dá o passo a passo manual |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Suíte verde com a baseline de **1585 passou / 9 pulados** mais os testes novos
- [ ] `SHA_DA_TELA` e `TAMANHO_ESPERADO` atualizados com o valor medido e a mudança declarada
- [ ] Os 68 cartões ainda no documento em todas as páginas (verificado por teste e no arquivo real)
- [ ] Contagem do topo intacta: "68 conexões analisadas" em qualquer página
- [ ] `#resultado-N` abre a página certa **e** o cartão, nessa ordem
- [ ] Com JavaScript desligado, a lista inteira aparece
- [ ] Nenhum arquivo de `src/app.py`, `src/application/`, `src/core/` ou `src/ports/` alterado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-plan` | reversa |
