# Roadmap: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Requirements: `_reversa_forward/037-redesenho-das-tres-fases/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A tela de entrada é reorganizada em **um único esqueleto de três fases**, renderizado nos dois estados (sem árvore e com árvore aberta), com a navegação numa barra lateral que **reusa o componente de abas já carregado na página** — o mesmo `data-bs-toggle="tab"` que hoje veste a fileira horizontal, apenas desenhado em coluna. Não nasce um segundo mecanismo de troca de painel.

Cada fase ganha cabeçalho, caixa de status e blocos próprios. A fase 1 recebe a lista e o envio que hoje moram dentro da aba de busca, mais dois contadores calculados em Jinja sobre `arvores_da_lista`. A tabela continua a mesma em contrato — mesmas colunas, mesmos formulários, mesmos literais — e muda só a leitura.

A única frente com código novo de verdade é o **combobox de nomes**: a `<datalist>` sai e os nomes passam a ser entregues como **um bloco JSON**, do qual um script pequeno monta a lista filtrada, com ARIA próprio, teclado e degradação para campo de texto comum.

Quatro frentes de trabalho: esqueleto de fases, conteúdo das fases, combobox, e fecho (CSS, contraste, testes, hash).

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca entram no versionamento | Testes usam `tests/fixtures/sample_gedcom.py` e `sample_dna.py`; nenhuma captura, nome ou cM real entra em evidência | respeita |
| II. Comportamento observável preservado em refatoração | **A feature não é refactor**: ela muda o que o operador vê. O que ela não pode mudar é o resultado de qualquer análise — mesmos caminhos, mesmos matches, mesmos cM. Está declarado no `requirements.md` §2.3 e precisa ser conferido no fecho | respeita, com declaração |
| III. Nenhuma mudança sem teste que a cubra | Cada frente entra com teste que falha antes; a frente do combobox é a que mais precisa, e é também a de cobertura mais fraca (ver `D-14`) | respeita, com limite declarado |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhuma travessia de grafo é tocada | não se aplica |
| V. Toda suposição de genealogia cita a fonte | Não se aplica: nenhuma faixa de cM, MRCA ou heurística de domínio é criada. Os contadores são contagens, não inferência | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A barra lateral é um `.nav` em coluna com `role="tablist"`, e cada fase é um botão `data-bs-toggle="tab"` ligado ao seu painel | O plugin de abas já é carregado (`bootstrap.bundle.min.js`, `index.html:1444`) e já entrega clique, `.active` e `aria-selected`; trocar só o desenho evita um segundo mecanismo | (a) JS próprio de painéis; (b) links com âncora e `:target`; (c) manter as abas e só estilizá-las | 🟢 |
| D-02 | Um **esqueleto único** de três painéis, com `{% if gedcom_filename %}` **dentro** de cada painel; os dois ramos atuais deixam de duplicar a navegação | A `RN-01` exige as três fases nos dois estados; dois esqueletos divergem na primeira manutenção | (a) duplicar o esqueleto nos dois ramos; (b) renderizar as fases por inclusão de template | 🟢 |
| D-03 | A fase 1 aparece nos dois estados, com a lista e o envio sempre visíveis | As duas listas vêm do processador de contexto em toda renderização (`tela-de-entrada/contracts.md#1.2`); não há custo de servidor em mostrá-las sempre | (a) esconder a fase 1 com árvore aberta | 🟢 |
| D-04 | Fases 2 e 3 sem árvore exibem texto curto e um botão que leva à fase 1, sem nenhum campo de formulário | `RN-03`: a ausência hoje é silenciosa; o estado vazio explica em vez de deixar a fase em branco | (a) desabilitar os botões da barra; (b) esconder as fases | 🟢 |
| D-05 | As setas dentro da barra usam o que o plugin de abas já faz; se ele só tratar ←/→, um handler de ~15 linhas mapeia ↑/↓ para a mesma ativação | O plugin trata setas horizontais; navegação vertical é o caso desta tela. **Verificar em execução antes de escrever o handler** | (a) aceitar só ←/→; (b) escrever o handler desde o início | 🟡 |
| D-06 | Os contadores são calculados no template: `arvores_da_lista\|length` e `arvores_da_lista\|selectattr('disponivel')\|list\|length` | `ItemDaLista` é dataclass congelada com atributo `disponivel`; nenhuma variável de contexto nova e portanto nenhuma mudança na borda | (a) publicar contadores no processador de contexto; (b) contar no JavaScript | 🟢 |
| D-07 | `all_names` passa a ser renderizado **uma vez** como JSON num `<script type="application/json">`, e o script monta a lista | Hoje cada nome vira um `<option>` no documento; um GEDCOM real tem dezenas de milhares de nomes. O filtro `tojson` do Flask escapa `<`, `>` e `&`, então o bloco é seguro | (a) manter a `<datalist>` e ler dela; (b) embutir o array numa chamada JS | 🟢 |
| D-08 | O filtro do combobox é **insensível a acento e a caixa** (`normalize('NFD')` + remoção de diacríticos), feito no cliente | Nomes de GEDCOM têm acento; digitar `joao` precisa encontrar `João`. É conveniência de tela e **não** altera a normalização do servidor (`core/name_normalization.py`) | (a) `toLowerCase().includes` puro | 🟡 |
| D-09 | No máximo **50 opções** renderizadas, com uma linha de rodapé dizendo quantos nomes existem quando o corte acontece | Sem teto, uma letra digitada montaria milhares de nós numa lista que já vem inteira no documento | (a) renderizar tudo; (b) paginar | 🟡 |
| D-10 | O comportamento do combobox mora num `<script>` embutido no fim do documento, como o do tema e o do envio | Criar rota de JS repetiria o desenho de `GET /app.css` e **mudaria a superfície HTTP**, o que a `RN-05` proíbe; `src/static/` continua proibida (`W004`) | (a) rota `/app.js`; (b) `src/static/` | 🟢 |
| D-11 | A tabela recebe listramento e mais respiro; os dois botões de ação passam a ficar empilhados na coluna de gerenciamento | O mockup empilha; com dois formulários por linha, lado a lado eles competem pelo clique | (a) manter lado a lado e só aumentar o `gap` | 🟢 |
| D-12 | A linha "Árvore aberta: … — escolher outra árvore" sai de cima das fases e vira a caixa de status da fase 1 | Com a fase 1 existindo, a frase duplicava a informação da caixa de status | (a) manter a linha e a caixa | 🟢 |
| D-13 | O botão de tema perde um pouco de escala, mantendo posição fixa, rótulo de destino e `aria-pressed` | A `RN-12` pede redução, não mudança de comportamento; a `027` já fixou o piso de legibilidade | (a) manter o tamanho atual | 🟢 |
| D-14 | Os testes novos prendem **estrutura e contrato no HTML servido**, não o comportamento executado do combobox | O projeto não tem navegador headless nem executor de JS (declarado desde a `013`, `D-07`); fingir cobertura de comportamento seria pior do que declarar o limite | (a) montar um runner de JS; (b) testar só manualmente | 🟡 |
| D-15 | Quando há árvore aberta, o painel e o botão da fase 2 nascem com `.active` | O servidor sabe se há árvore (`gedcom_filename`); deixar o JavaScript decidir faria a tela abrir na fase 1 e piscar para a 2 | (a) decidir no JavaScript | 🟢 |

## 4. Premissas

Nenhuma. As três dúvidas do `requirements.md` foram resolvidas em `/reversa-clarify` (sessão de 2026-10-20).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Tela de entrada (template `index.html`) | `_reversa_sdd/architecture.md#3` | `regra-alterada` | A navegação passa de duas abas horizontais para três fases numa barra lateral; a lista e o envio migram para a fase 1; ganha cabeçalho e caixa de status por fase |
| Folha de estilo (`src/assets/app.css`, servida por `GET /app.css`) | `_reversa_sdd/architecture.md#3` e `addenda/013` | `regra-alterada` | Bloco novo para barra de fases, caixa de status, contadores, blocos, estado vazio, tabela e combobox; nenhum token de estado (`--st-*`) é tocado |
| Processador de contexto `_listas_da_tela` (`src/app.py`) | `_reversa_sdd/tela-de-entrada/contracts.md#1.2` | `presença` | Sem mudança: os contadores derivam das listas já publicadas |
| Borda, aplicação, portas e núcleo | `_reversa_sdd/architecture.md#3` | sem mudança | Nenhum arquivo de `src/application`, `src/ports` ou `src/core` é tocado |
| `all_names` como variável de template | `_reversa_sdd/tela-de-entrada/contracts.md#1.2` | `presença` | Continua `list[str]` vinda do envio e de `selecionar_arvore`; muda apenas a forma de renderizar (JSON em vez de `<option>` por nome) |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma**. Não há campo, tabela, payload, migração ou chave nova. O banco opcional e as seis tabelas da extração ficam intactos.
- Detalhe completo em: `_reversa_forward/037-redesenho-das-tres-fases/data-delta.md`

## 7. Delta de contratos externos

**n/a.** Nenhuma rota nasce, morre ou muda de contrato: `GET /`, as cinco `action` de `POST`, `GET /app.css`, `GET /banner.png` e `GET /apple-touch-icon.png` mantêm método, corpo e códigos. O documento de `GET /` muda de conteúdo, mas o contrato HTTP não. Por isso o diretório `interfaces/` não é criado.

O `SHA_DA_TELA` de `tests/test_icone_de_atalho.py` **não** é contrato externo: é invariante de teste mantido à mão, e será atualizado com decisão registrada (ver risco R-02).

## 8. Plano de migração

n/a — não há dado a migrar. O que existe é **transição de documento**: a tela nova substitui a antiga de uma vez, sem estado intermediário persistido.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01 — O combobox próprio introduz defeito de acessibilidade silencioso (foco perdido, `aria-activedescendant` apontando para opção inexistente, lista que não fecha) | alto | média | Seguir o padrão de combobox da especificação ARIA; prender cada atributo por teste; checklist manual no `onboarding.md`; declarar em `D-14` o que o teste **não** cobre |
| R-02 — `SHA_DA_TELA` muda e o teste é "consertado" sem decisão | médio | alta | Registrar hash antigo e novo no `evidence/` e no `legacy-impact.md`, com a razão da mudança, como a `021` fez; nunca trocar o valor sem medição |
| R-03 — Reestruturar o template quebra teste que dependia da posição do bloco (lista dentro da aba de busca) | médio | média | Rodar a suíte de guardas da tela antes de mover; estreitar o teste que reclamar em vez de apagá-lo |
| R-04 — A barra lateral espreme a tabela de seis colunas entre 992 e 1200 px | médio | média | Empilhar a barra abaixo de 992 px; manter `table-responsive`; medir em 992, 1024 e 1200 |
| R-05 — `<datalist>` removida deixa algum teste antigo sem alvo | baixo | baixa | Verificado: nenhum teste cita `gedcom_names` ou `datalist` hoje |
| R-06 — O bloco JSON com dezenas de milhares de nomes aumenta a página com árvore aberta | médio | média | Medir o tamanho antes e depois; o JSON ocupa menos que um `<option>` por nome, então a expectativa é **reduzir** |
| R-07 — O plugin de abas não trata ↑/↓ e a barra fica sem navegação vertical | baixo | média | `D-05` manda verificar em execução; se faltar, o handler é pequeno e testável |
| R-08 — A regra nova de contador usa `selectattr` e quebra se `ItemDaLista` deixar de ser dataclass | baixo | baixa | O tipo é `@dataclass(frozen=True)` hoje; o teste do contador falha se mudar |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Os 16 RFs do `requirements.md` cobertos por teste ou por checklist manual declarado (só o comportamento executado do combobox fica no checklist)
- [ ] Suíte verde, sem teste removido nem desabilitado
- [ ] `SHA_DA_TELA` atualizado com hash antigo e novo registrados em `evidence/`
- [ ] Contrastes medidos nos dois temas e anotados na folha
- [ ] Nenhuma rota, `action`, nome de campo ou literal congelado alterado — conferido por diff
- [ ] Área de resultados intacta — conferido por diff
- [ ] `regression-watch.md` gerado
- [ ] `legacy-impact.md` com os componentes tocados

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-20 | Versão inicial gerada por `/reversa-plan` | reversa |
