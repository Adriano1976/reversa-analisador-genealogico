# Requirements: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A tela de entrada do Analisador de Conexões Genealógicas passa a apresentar as **três fases do trabalho** — Árvores GEDCOM (o formato padrão de árvore genealógica), Busca documental e Analisador de DNA — numa **barra lateral de fases**, em vez das duas abas atuais, que misturam a escolha da árvore com a busca documental e não nomeiam a primeira etapa.

A entrega é de **apresentação e organização**, com duas entregas funcionais localizadas: os três campos de nome ganham **autocomplete próprio**, com lista filtrada e navegação por teclado, e a fase 1 ganha **dois contadores verificáveis** (árvores armazenadas e árvores disponíveis). O resto é hierarquia tipográfica, ação principal junto do campo que a dispara, tabela mais legível, blocos agrupados por intenção e a fase ativa evidente. Nenhuma regra de domínio, rota, `action`, nome de campo ou variável de template muda — a tela continua sendo a mesma superfície de contrato, reorganizada.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#3` | A borda (`src/app.py`) renderiza `index.html`; a folha de estilo é servida por rota (`GET /app.css`) a partir de `src/assets/app.css`, nunca por pasta estática | 🟢 |
| `_reversa_sdd/domain.md#3.6` | A tela de entrada: listar, escolher e aposentar. A listagem **não filtra nada** — a pasta é a superfície de confiança | 🟢 |
| `_reversa_sdd/domain.md#3.1` e `#3.2` | Parentesco documental e evidência genética são eixos que não se contaminam: o DNA **não altera** o parentesco do GEDCOM e o cM (centimorgan) não afirma parentesco sozinho | 🟢 |
| `_reversa_sdd/tela-de-entrada/contracts.md#1.2` | `arvores_da_lista` e `relatorios_da_lista` vêm do **processador de contexto** em toda renderização; `gedcom_filename` e `all_names` vêm só do envio e de `selecionar_arvore` | 🟢 |
| `_reversa_sdd/tela-de-entrada/contracts.md#2.2` | A aba de cada arquivo é decidida pela extensão do nome cru; a ordem é `mtime` decrescente com empate pelo nome exibido | 🟢 |
| `_reversa_sdd/tela-de-entrada/contracts.md#2.4` | Disponibilidade e os dois motivos de indisponibilidade — exibidos ao lado do item, nunca escondidos | 🟢 |
| `_reversa_sdd/tela-de-entrada/requirements.md#requisitos-funcionais` | `RF-19` (Abrir só no disponível da aba de árvores), `RF-20` (Apagar em todo item, com confirmação), `RF-21` (estado vazio por aba), `RF-22` (abas e rótulos idênticos nos dois ramos) | 🟢 |
| `_reversa_sdd/recursos-da-tela/requirements.md#a-masthead` | A masthead: arte, subtítulo, `<h1>` sempre visível e texto de apresentação centralizado em coluna estreita (`RN-24`) | 🟢 |
| `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` | Folha servida por rota, tema claro como padrão com escolha em `localStorage`, botão de tema fixo e o par `aria-controls`/`aria-selected` nas abas | 🟢 |
| `_reversa_sdd/addenda/021-seletor-de-arquivos-por-formato.md` | `accept` **filtra o seletor e não valida**; a barreira real é a de conteúdo | 🟢 |
| `_reversa_sdd/addenda/026-polimento-visual-da-tela.md` e `027-harmonizar-topo-da-tela.md` | Tokens de cor e de alerta, escala do `h1` (≤ 2,2 rem) e arte (≤ 280 px), e a regra de que a ação principal tem largura natural acima de 576 px | 🟢 |
| `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` | O cartão de resultado já foi refinado (três faixas, barra, superfície). **Fora do escopo desta feature** | 🟢 |
| `_reversa_sdd/inventory.md#3.2` | As unidades funcionais que o operador enxerga — `tela-de-entrada`, `analise-dna`, `busca-caminho` | 🟢 |
| `_reversa_sdd/screens/golden/manifest.yaml` | As 8 telas literais e o invariante `SHA_DA_TELA` (mede a tela **vazia**, `GET /` com pasta vazia) | 🟢 |

### 2.1 O que o pedido já encontra pronto no legado

Quatro dos itens pedidos já existem e **não devem ser reimplementados** — só ajustados:

| Item pedido | Situação no legado | Ação nesta feature |
|---|---|---|
| Botão de tema escuro fixo no topo direito, com ícone | Já existe desde a `013`, com `aria-pressed`, rótulo de **destino** e preferência em `localStorage`; a `027` fixou a escala | Reduzir e alinhar, sem mexer no comportamento nem no rótulo |
| Filtro de formato no seletor de arquivos | Já existe desde a `021` (`accept=".ged"`, `accept=".csv"`), com teste que proíbe virar validação de extensão | Preservar literalmente |
| Tabela com botões "Abrir" e "Apagar" funcionais | Já existe desde a `011`: `Abrir` só no item disponível, `Apagar` em todo item, ambos com formulário próprio e confirmação | Manter colunas, formulários e literais; mudar só a leitura visual |
| Autocomplete nos campos de nome | Existe o `<datalist id="gedcom_names">`, alimentado por `all_names` e usado nos três campos — mas sem lista filtrada, sem destaque da correspondência e sem navegação por setas | **Evoluir para combobox próprio** (§9, `Q-02`): o dado já está no documento, o componente é que muda |

### 2.2 O que não existe hoje

- **A fase 1 não existe como fase.** A lista de árvores e o envio moram **dentro** da aba "Buscar Conexão no GEDCOM"; só existem duas abas, e a primeira acumula escolha de árvore, envio e busca.
- **Não há cabeçalho de fase** (título + objetivo) nem caixa de status (árvore aberta / modo de análise).
- **Não há retorno visual do arquivo escolhido** no bloco de envio.
- **A tabela não é listrada** e a ação principal é um botão de largura total em cada formulário.

> O mockup desenha **duas** navegações para os mesmos três painéis — barra lateral e fileira de abas. A decisão de 2026-10-20 (§9, `Q-01`) fica com a **barra lateral como controle único**: as abas saem, para não haver dois controles anunciando os mesmos três destinos.

### 2.4 A referência visual: o que se aproveita e o que não se copia

As três imagens recebidas são o **mesmo documento de referência**, cada uma com uma fase ativa. Elas confirmam o que o HTML já mostrava e acrescentam detalhes que só se veem renderizados.

**Transferível — linguagem visual e organização:**

- Cabeçalho de fase no formato `Fase N — <nome da fase>`, em serifa e corpo grande.
- Caixa de status à direita do cabeçalho, com um rótulo curto em maiúsculas, o valor em destaque e um link de ação.
- Cada bloco de conteúdo (tabela, envio, seleção de CSV, nome) emoldurado por conta própria, com título e uma linha de apoio.
- Campos de formulário em **duas colunas** quando há dois, com a ação principal **na mesma linha**, à direita.
- Tabela com linhas alternadas e ações empilhadas na vertical na coluna de gerenciamento.
- Bloco de envio com ícone, nome do arquivo e as duas ações no mesmo agrupamento.

**Não transferível — é texto sobre a proposta, não interface:**

- O texto do herói ("Uma proposta de reorganização visual…"), os três chips sob ele, o quadro "O que muda nesta proposta" da barra lateral e a nota de rodapé.
- As linhas de argumentação dentro dos blocos ("Sugestão: destacar a tabela…", "Sugestão importante para a implementação real…", "Em vez do input de arquivo 'solto'…").
- O bloco "Melhorias de UX recomendadas para a versão real", que é uma **lista de recomendação ao desenvolvedor**, e não conteúdo de tela.
- O rótulo "Processada" e a segunda linha sob o nome de cada arquivo ("Versão processada e pronta para busca"): a aplicação **não tem estado de processamento** e não tem esse texto por item; o que ela sabe é **disponível** ou **indisponível**, com o motivo. Copiar "Processada" inventaria um estado que não existe.
- O número "100% com status processado" da faixa de estatísticas, pelo mesmo motivo.

**Inconsistência de vocabulário na referência:** cada fase aparece com **três nomes** diferentes — na barra lateral ("1. Árvores GEDCOM"), na aba ("Buscar Conexão no GEDCOM") e no título ("Fase 1 — Árvores disponíveis"). A aplicação tem dois desses nomes **congelados por teste**, então a barra lateral e o título da fase adotam esses mesmos nomes, e não um terceiro: `1. Árvores GEDCOM`, `2. Buscar Conexão no GEDCOM`, `3. Analisador de DNA`.

### 2.3 Fixtures sintéticas (Princípio I)

Nada nesta feature lê dado real. Os testes de tela usam as fixtures já existentes — `tests/fixtures/sample_gedcom.py` e `tests/fixtures/sample_dna.py` — e, quando precisam de um arquivo armazenado, o gravam em pasta temporária. Nenhum GEDCOM, CSV, nome ou cM real entra em teste, evidência, captura ou documentação.

Sob o Princípio II, esta feature **não é refactor**: ela muda o que o operador vê. O que ela não pode mudar é o **resultado** de qualquer análise — mesmos caminhos, mesmos matches aceitos e descartados, mesmos cM. O Princípio III vale integralmente: cada requisito funcional novo chega com teste que falha antes e passa depois.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador-genealogista (Adriano) | Retomar o trabalho com uma árvore já armazenada, ou enviar uma nova, e seguir para a busca | Abre a tela, encontra as três fases nomeadas, escolhe a árvore na fase 1 e cai na fase 2 pronta para digitar os dois nomes |
| Operador eventual | Entender o que o aplicativo faz e em que ordem fazer | Lê o texto de apresentação, vê que existem três fases numeradas e que a fase 3 cruza duas evidências — sem precisar adivinhar |
| Operador em telefone | Executar o mesmo fluxo numa tela de 320 px | As fases continuam navegáveis, os campos ocupam a largura e nenhum bloco exige rolagem horizontal |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A tela de entrada tem **três fases**, sempre as mesmas e nesta ordem: `1. Árvores GEDCOM`, `2. Buscar Conexão no GEDCOM`, `3. Analisador de DNA`. A navegação entre elas é uma **barra lateral única**, e as abas superiores deixam de existir. 🟢
   - Origem no legado: `_reversa_sdd/tela-de-entrada/requirements.md#RF-22` (simetria das abas entre os dois ramos), hoje com **duas** abas.
   - Tipo: **alterada** — o conjunto passa de duas abas para três fases numa barra lateral; a simetria entre os dois estados da tela é preservada.
   - Abaixo de 992 px a barra lateral vira uma **faixa horizontal** de três botões, com a fase ativa marcada do mesmo jeito; nenhuma fase fica inalcançável no telefone.

2. **RN-02:** O conteúdo de cada fase é fixo: a **fase 1** traz a lista de árvores armazenadas e o envio de nova árvore; a **fase 2**, os dois campos de pessoa e a ação de busca; a **fase 3**, a escolha do CSV e o nome no GEDCOM. 🟢
   - Origem no legado: `_reversa_sdd/tela-de-entrada/contracts.md#2.2` e o template atual, onde lista e envio vivem na aba de busca.
   - Tipo: **alterada** — o bloco de lista + envio **sai** da aba de busca e vira a fase 1.

3. **RN-03:** As fases 2 e 3 **só têm formulário com uma árvore aberta**. Sem árvore, cada uma exibe um estado vazio curto que nomeia a fase 1 como o lugar de abrir a árvore, e **nenhum campo de entrada** é renderizado. 🟢
   - Origem no legado: o ramo `{% if not gedcom_filename %}` atual, que simplesmente não renderiza os formulários.
   - Tipo: **nova** — hoje a ausência é silenciosa; passa a ser explicada.

4. **RN-04:** Ao enviar uma árvore ou escolher uma da lista, a tela volta com a **fase 2 ativa**. 🟢
   - Origem no legado: `tela-de-entrada/requirements.md#RF-14` (`selecionar_arvore` renderiza o mesmo estado do envio).
   - Tipo: **nova** — o destino do operador é a busca, não a lista.

5. **RN-05:** A feature **não cria nem altera** rota, `action`, campo de formulário, nome de campo, variável de template, tabela ou regra de domínio. A superfície HTTP continua com as mesmas rotas e o mesmo contrato. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#3` e `tela-de-entrada/contracts.md#1.2`.
   - Tipo: **nova** (restrição de escopo).

6. **RN-06:** Cada fase tem **cabeçalho próprio** — título da fase e uma linha de objetivo — e uma **caixa de status**: na fase 1, a árvore em uso (ou a ausência dela); na fase 2, a árvore sobre a qual a consulta roda; na fase 3, a natureza do modo de análise. 🟢
   - Tipo: **nova**.

7. **RN-07:** A **ação principal de cada fase fica junto do campo que a dispara**, na mesma linha em tela larga e empilhada abaixo em tela estreita. Há **uma** ação principal por fase. 🟢
   - Origem no legado: `_reversa_sdd/addenda/027-harmonizar-topo-da-tela.md` (largura natural acima de 576 px).
   - Tipo: **nova**.

8. **RN-08:** A lista de arquivos **continua uma tabela**, com as mesmas seis colunas, os mesmos formulários e os mesmos literais `Abrir` e `Apagar`. Mudam apenas a leitura visual: linhas alternadas, mais espaço horizontal entre colunas e botões de ação maiores e separados. 🟢
   - Origem no legado: `_reversa_sdd/tela-de-entrada/requirements.md#RF-19`, `#RF-20` e `contracts.md#2.1`.
   - Tipo: **alterada** (visual).

9. **RN-09:** O envio de arquivo vira um **bloco próprio**, com o seletor, o nome do arquivo escolhido e a ação de envio no mesmo agrupamento visual. O retorno do nome é **do lado do cliente** e não substitui, nem antecipa, a mensagem do servidor. 🟢
   - Origem no legado: `_reversa_sdd/addenda/021-seletor-de-arquivos-por-formato.md` (`accept` filtra e não valida).
   - Tipo: **nova**.

10. **RN-10:** Os três campos de nome (as duas pessoas da busca e o nome no GEDCOM) passam a ser um **combobox com lista filtrada**: digitar filtra os nomes da árvore aberta, as setas percorrem as opções, `Enter` escolhe e `Esc` fecha. O texto digitado continua **livre** — escolher da lista é conveniência, não exigência, e é exatamente o texto do campo que a busca recebe. 🟡
    - Origem no legado: `<datalist id="gedcom_names">`, alimentado por `all_names`.
    - Tipo: **alterada** — o dado é o mesmo; o componente é que passa a ter comportamento próprio.

11. **RN-11:** **Nenhum literal congelado muda.** Rótulos das fases 2 e 3, rótulo do seletor, rótulo do nome, botões, mensagens de sucesso e de erro, `title` e textos de `visually-hidden` permanecem idênticos. Textos explicativos **podem** encurtar, desde que não carreguem regra de domínio. 🟢
    - Origem no legado: `domain.md#5` (contrato de mensagens) e as asserções de `tests/test_lista_na_tela.py` e `tests/test_cabecalho_de_enquadramento.py`.
    - Tipo: **nova** (restrição).

12. **RN-12:** O controle de tema permanece **fixo no canto superior direito**, com ícone e rótulo de destino, `aria-pressed` e preferência lembrada; muda apenas a escala, para não competir com o cabeçalho. 🟢
    - Origem no legado: `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` e `026`.
    - Tipo: **alterada** (visual).

13. **RN-13:** A reorganização preserva a acessibilidade: contraste **WCAG AA** (Web Content Accessibility Guidelines, nível AA) nos dois temas para todo texto e para os indicadores de fase, foco visível em todos os controles, `aria-selected`/`aria-controls` na navegação, ícones decorativos com `aria-hidden` e nenhuma informação transmitida só por cor. O combobox segue o padrão de combobox da especificação ARIA — `aria-expanded`, `aria-controls`, `aria-activedescendant`, lista com `role="listbox"` e opções com `role="option"` — e o número de resultados é anunciado por região viva. 🟢
    - Tipo: **nova**.

14. **RN-14:** A área de **resultados** (título, contagem, cartões, bloco de descartados, observações do arquivo) **não é tocada** por esta feature. 🟢
    - Origem no legado: `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md`.
    - Tipo: **nova** (limite de escopo).

15. **RN-15:** A fase 1 mostra **dois contadores calculados da própria lista** — quantas árvores estão armazenadas e quantas estão disponíveis — e **nenhum número que a aplicação não saiba**. Números de vaidade e estados que o sistema não rastreia ficam de fora. 🟢
    - Tipo: **nova**.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Renderizar **três fases** numa barra lateral, na ordem 1–2–3, com os rótulos `1. Árvores GEDCOM`, `2. Buscar Conexão no GEDCOM` e `3. Analisador de DNA`, nos **dois** estados da tela (sem árvore e com árvore aberta) | Must | `GET /` com pasta vazia e `GET /` com árvore aberta produzem os três botões de fase, uma única vez cada, sem nenhuma aba superior | 🟢 |
| RF-02 | Na **fase 1**, renderizar a tabela de árvores armazenadas e o bloco de envio de nova árvore | Must | A tabela com `name="action" value="selecionar_arvore"` e o formulário com `value="upload_gedcom"` aparecem dentro do painel da fase 1 | 🟢 |
| RF-03 | Na **fase 2**, renderizar apenas os dois campos de pessoa e a ação de busca | Must | O painel da fase 2 contém `person1_name`, `person2_name` e `Encontrar Conexão`; não contém seletor de arquivo | 🟢 |
| RF-04 | Na **fase 3**, renderizar a escolha do CSV e o nome no GEDCOM com a ação de análise | Must | O painel da fase 3 contém `matches_csv_filename`, `matches_csv`, `root_name` e `Analisar Matches de DNA` | 🟢 |
| RF-05 | Sem árvore aberta, fases 2 e 3 exibem **estado vazio** que nomeia a fase 1, sem nenhum campo de formulário | Must | Com pasta vazia, os painéis 2 e 3 não contêm `<input>`, `<select>` nem `<form>` de busca/análise | 🟢 |
| RF-06 | Voltar de um envio ou de `selecionar_arvore` com a **fase 2 ativa** e a árvore já aberta | Must | A resposta do envio tem a fase 2 como painel ativo e mostra a árvore em uso | 🟢 |
| RF-07 | Exibir, por fase, **cabeçalho** (título + uma linha de objetivo) e **caixa de status** | Should | Cada painel tem um título de fase e uma caixa de status; na fase 1 ela nomeia a árvore em uso e oferece o link "Escolher outra árvore", ou diz que não há nenhuma | 🟡 |
| RF-08 | Posicionar a **ação principal** ao lado do campo que a dispara, uma por fase; largura total só abaixo de 576 px | Must | Em 768 px o botão e o campo dividem a linha; em 360 px o botão ocupa a largura e fica abaixo do campo | 🟢 |
| RF-09 | Apresentar a tabela com **linhas alternadas**, mais espaço entre colunas e botões de ação maiores e separados | Must | A tabela tem a classe de listramento e as duas ações de cada linha mantêm ao menos 8 px de separação | 🟢 |
| RF-10 | Apresentar o envio como **bloco próprio**, mostrando o nome do arquivo escolhido após a seleção e o texto padrão quando não houver arquivo | Should | Selecionar um arquivo troca o texto do bloco pelo nome; limpar o campo devolve o texto padrão | 🟡 |
| RF-11 | Manter o controle de tema fixo no topo direito, menor, com ícone e rótulo de destino, `aria-pressed` e preferência preservada | Must | O botão continua com `aria-pressed` alternando e o tema escolhido sobrevive ao recarregamento | 🟢 |
| RF-12 | Preservar **todos** os literais congelados da tela, mensagens de retorno e `visually-hidden` | Must | Os textos de `test_lista_na_tela.py`, `test_cabecalho_de_enquadramento.py` e os literais de `domain.md#5` continuam presentes sem edição de teste | 🟢 |
| RF-13 | Preservar a navegação por teclado e o estado acessível das fases | Must | Tab alcança as três fases; as setas percorrem a barra; a ativa expõe `aria-selected="true"`; o foco é visível em todos os controles | 🟢 |
| RF-14 | Não introduzir rolagem horizontal em 320 px | Should | Em 320 px a largura do documento não excede a da janela | 🟡 |
| RF-15 | Oferecer **combobox** nos três campos de nome, com lista filtrada a partir dos nomes da árvore aberta | Must | Digitar filtra a lista; ↓/↑ percorrem; `Enter` escolhe; `Esc` fecha; texto sem correspondência continua aceito e é o que a busca recebe; sem JavaScript, o campo continua um campo de texto comum | 🟢 |
| RF-16 | Exibir na fase 1 os **dois contadores**: árvores armazenadas e árvores disponíveis | Should | Com duas árvores na pasta, uma indisponível, os contadores mostram 2 e 1; com a pasta vazia a faixa não aparece | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Nenhuma requisição nova: as listas continuam vindo do processador de contexto, e o custo de renderizar três painéis é o mesmo de renderizar dois | `tela-de-entrada/contracts.md#1.2`; a listagem só faz `listdir` + `stat` | 🟢 |
| Acessibilidade | Contraste AA (≥ 4,5:1 para texto, ≥ 3:1 para indicadores) nos dois temas, com os pares medidos e registrados na folha | Prática já adotada nas `026`, `027` e `036` | 🟢 |
| Acessibilidade | A fase ativa não pode ser distinguida **só** por cor: precisa de peso, borda ou marcador textual | WCAG 1.4.1 | 🟢 |
| Robustez | Se o JavaScript falhar, os três formulários continuam funcionando, a fase 1 continua visível e o combobox volta a ser um campo de texto comum; nenhuma fase depende de script para existir no documento | Degradação progressiva; o documento já entrega todos os painéis | 🟢 |
| Manutenibilidade | Toda a apresentação nova fica em `src/assets/app.css` e em `index.html`; nenhum arquivo novo de estilo, nenhum framework de UI novo, nenhuma fonte nova por CDN | `architecture.md#3`; `addenda/013` | 🟢 |
| Manutenibilidade | As regras de fase devem ser escritas **uma vez** (macro ou laço), para que a fase 1 não vire uma cópia divergente das outras | O macro `tabela_de_arquivos` já existe por esse motivo | 🟡 |
| Testabilidade | A entrega vem com teste próprio que falha antes e passa depois, e `SHA_DA_TELA` é atualizado como **decisão declarada**, não como conserto de teste | Princípio III; `tests/test_icone_de_atalho.py` | 🟢 |
| Segurança | Nenhum dado novo no documento: a tela continua exibindo rótulo sem chave de conteúdo e nenhum caminho absoluto | `tela-de-entrada/requirements.md#RF-17` e `#BR-T-18` | 🟢 |
| Escalabilidade | A tabela pode crescer sem quebrar o layout: ela continua em contêiner responsivo | `table-responsive` atual | 🟡 |
| Desempenho | A lista de sugestões é filtrada no cliente e renderiza no máximo **50 opções** por vez, mesmo com uma árvore de dezenas de milhares de nomes | `all_names` é entregue inteiro no documento; sem teto, uma única letra montaria milhares de nós | 🟡 |
| Manutenibilidade | O combobox é escrito **uma vez** e usado pelos três campos; a troca de fase reusa o mecanismo de abas já presente em vez de introduzir um segundo mecanismo de painel | Evita duas implementações do mesmo comportamento | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Primeira abertura, pasta vazia
  Dado que nenhuma árvore está armazenada
  Quando o operador abre GET /
  Então as três fases aparecem nomeadas e numeradas
  E a fase 1 está ativa, com o bloco de envio visível
  E as fases 2 e 3 mostram o estado vazio que aponta para a fase 1

Cenário: Escolher uma árvore já armazenada
  Dado que a pasta contém uma árvore disponível
  Quando o operador abre a árvore pela fase 1
  Então a tela volta com a fase 2 ativa
  E a árvore em uso aparece nomeada, sem a chave de conteúdo
  E os dois campos de pessoa estão disponíveis

Cenário: Enviar uma árvore nova
  Dado que o operador está na fase 1
  Quando ele escolhe um arquivo GEDCOM e confirma o envio
  Então a tela responde com a mensagem de sempre
  E a fase 2 fica ativa com a árvore recém-carregada

Cenário: Tentar buscar sem árvore
  Dado que nenhuma árvore está aberta
  Quando o operador seleciona a fase 2
  Então nenhum campo de busca é oferecido
  E a tela explica que a árvore se abre na fase 1

Cenário: Envio de arquivo inválido pela fase 1
  Dado um arquivo que não é GEDCOM
  Quando o operador confirma o envio
  Então a mensagem de recusa é exatamente a de hoje
  E a fase 1 continua ativa, com a tabela intacta

Cenário: Tela de 320 px
  Dado um visor de 320 px de largura
  Quando o operador percorre as três fases
  Então nenhuma fase produz rolagem horizontal
  E a ação principal de cada fase fica abaixo do seu campo

Cenário: A tabela da fase 1 continua operável
  Dado que a fase 1 lista ao menos uma árvore disponível e uma indisponível
  Quando o operador percorre a tabela
  Então as linhas alternam de fundo e as colunas mantêm espaço entre si
  E a linha disponível oferece "Abrir" e "Apagar", e a indisponível só "Apagar", com o motivo escrito ao lado
  E os dois botões de uma mesma linha estão separados o bastante para não serem clicados por engano

Cenário: Retorno do arquivo escolhido
  Dado que o operador está na fase 1
  Quando ele escolhe um arquivo no seletor
  Então o bloco de envio passa a exibir o nome do arquivo escolhido
  E, ao limpar o seletor, o bloco volta ao texto padrão
  E nenhuma mensagem do servidor é antecipada por esse retorno

Cenário: Alternar o tema
  Dado que a tela está no tema claro
  Quando o operador aciona o controle de tema
  Então a tela passa ao tema escuro e o controle anuncia o destino "Tema claro"
  E, ao recarregar, a escolha é lembrada
  E os três rótulos de fase continuam legíveis no novo tema

Cenário: Navegação por teclado na barra de fases
  Dado que o foco está na barra lateral de fases
  Quando o operador avança com Tab e aciona com Enter ou Espaço
  Então cada uma das três fases é alcançável e ativável
  E a fase ativa expõe o estado selecionado ao leitor de tela
  E as setas percorrem as fases dentro da barra
  E o foco permanece visível em todos os controles alcançados

Cenário: Combobox de nomes
  Dado que existe uma árvore aberta com nomes conhecidos
  Quando o operador digita as primeiras letras de um desses nomes
  Então a lista oferece os nomes correspondentes, filtrando a cada tecla
  E as setas percorrem a lista e `Enter` preenche o campo
  E `Esc` fecha a lista sem apagar o que foi digitado
  E um nome digitado que não está na lista continua aceito e é enviado como está

Cenário: A tela continua falando a mesma língua
  Dado que a tela foi reorganizada
  Quando o operador lê os rótulos e as mensagens
  Então "Buscar Conexão no GEDCOM", "Analisador de DNA", "Enviar nova árvore", "Pessoa 1", "Pessoa 2", "Encontrar Conexão", "1. Lista de Matches (CSV)", "2. Seu Nome (como está no GEDCOM)" e "Analisar Matches de DNA" continuam com o mesmo texto
  E as mensagens de sucesso e de erro do envio e da análise continuam idênticas

Cenário: Combobox sem JavaScript
  Dado que o script da página não carregou
  Quando o operador usa um campo de nome
  Então o campo se comporta como campo de texto comum
  E o formulário continua enviando o nome digitado

Cenário: Contadores da fase 1
  Dado que a pasta tem duas árvores, uma delas indisponível
  Quando o operador abre a fase 1
  Então os contadores mostram duas árvores armazenadas e uma disponível
  E nenhum outro número é exibido
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03, RF-04 — as três fases e sua distribuição | Must | É o pedido central: sem elas a tela continua com duas abas e a fase 1 inexistente |
| RF-05 — estado vazio das fases 2 e 3 | Must | Sem ele, a fase 1 tira a lista do lugar onde hoje o operador a encontra, e a tela fica sem caminho |
| RF-06 — destino após abrir a árvore | Must | Abrir uma árvore e cair numa fase vazia é um beco sem saída |
| RF-12 — literais preservados | Must | Contrato congelado; quebrá-lo invalida a leitura do legado |
| RF-13, RF-11 — acessibilidade e tema | Must | Regressão de acessibilidade é defeito, não acabamento |
| RF-08, RF-09 — ação junto do campo e tabela legível | Must | São os dois itens com efeito direto de uso, e não de gosto |
| RF-07 — cabeçalho e caixa de status | Should | Dá contexto e reduz a carga cognitiva, mas a tela funciona sem ele |
| RF-10 — retorno do arquivo escolhido | Should | Evita o envio do arquivo errado; o servidor continua sendo a barreira |
| RF-15 — combobox de nomes | Must | Pedido explícito do operador na sessão de 2026-10-20 (`Q-02`); é a maior superfície nova da feature |
| RF-16 — contadores da fase 1 | Should | Dão noção do acervo sem inventar estado; a tela funciona sem eles |
| RF-14 — 320 px | Should | O uso principal é desktop, mas o telefone não pode quebrar |

## 9. Esclarecimentos

### Sessão 2026-10-20

- **Q:** A navegação entre as fases fica em abas superiores numeradas, numa barra lateral, numa barra lateral só em tela larga, ou nas duas como no mockup?
  **R:** **Barra lateral como no mockup (1b)**, como controle único: as abas superiores saem. Abaixo de 992 px a barra vira faixa horizontal.
- **Q:** "Autocomplete" significa manter o `<datalist>` nativo, construir um combobox próprio, ou manter o nativo agora e registrar o próprio como dívida?
  **R:** **Construir o combobox próprio (2b)**: lista filtrada, navegação por setas e acessibilidade própria; o texto digitado continua livre.
- **Q:** A faixa de estatísticas traz os três números do mockup, só os verificáveis, ou não entra?
  **R:** **Só os verificáveis (3a)**: árvores armazenadas e árvores disponíveis. "100% prontas" e "2 cliques" não entram.

> Sem instrução em contrário, a frase "Árvore aberta: … — escolher outra árvore" migra para a caixa de status da fase 1, com o rótulo "Árvore atualmente aberta" e o link "Escolher outra árvore", e deixa de aparecer acima das fases. O `GET /` continua respondendo 200 sem árvore aberta.

## 10. Lacunas

> Nenhuma lacuna em aberto. As três dúvidas desta feature foram resolvidas na sessão de 2026-10-20 (ver §9).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-20 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-20 | Sessão de esclarecimentos: barra lateral como navegação única, combobox próprio e contadores verificáveis. As três dúvidas foram resolvidas e a `RN-15`/`RF-16` entraram | `/reversa-clarify` |

## Emendas

### E001, 2026-10-20

O que muda: a masthead deixa de ser um bloco empilhado e centralizado e passa a **duas colunas** — subtítulo, título e os dois parágrafos à esquerda, arte à direita. Emenda a `RN-24` (adendo `011`), que exigia o texto centralizado numa coluna mais estreita que o cartão.
Motivo: o operador apontou que a parte superior da tela (arte, subtítulo, título e texto de apresentação) continua com a estética anterior, e pediu a redistribuição em duas colunas, como na referência visual enviada.
Arquivos previstos: `src/templates/index.html`, `src/assets/app.css`, `tests/test_banner_do_topo.py`, `tests/test_icone_de_atalho.py`.

### E002, 2026-10-20

O que muda: a área das fases passa a ficar **visivelmente separada** da masthead — mais ar acima, um respiro depois da linha e uma linha fina entre as duas áreas, nos dois temas.
Motivo: o operador apontou que a masthead e o bloco das fases estavam próximos demais (na imagem, a faixa vermelha entre os dois), e pediu que fossem afastados e separados por uma linha, sem perder a elegância.
Arquivos previstos: `src/assets/app.css`.

### E003, 2026-10-20

O que muda: o cabeçalho de cada fase passa a ocupar a **largura inteira** do painel — título e objetivo à esquerda, caixa de status à direita —, terminando na mesma borda da nota de ajuda. Antes, na fase 3, o cabeçalho quebrava em duas linhas e deixava um vazio à direita.
Motivo: o operador mostrou a fase 3 com o título e a caixa de status encolhidos à esquerda, e pediu que as duas áreas ficassem alinhadas com a nota de ajuda (a faixa que ele marcou de verde).
Arquivos previstos: `src/assets/app.css`.

### E004, 2026-10-20

O que muda: na fase 3, os rótulos `1. Lista de Matches (CSV)` e `2. Seu Nome (como está no GEDCOM)` passam a começar na mesma linha, assim como os campos abaixo deles.
Motivo: os dois rótulos nasciam em alturas diferentes, porque a coluna da esquerda tem um campo mais alto (o arquivo) e a grade alinhava as células por baixo.
Arquivos previstos: `src/assets/app.css`.

### E005, 2026-10-20

O que muda: entre a linha divisória e o painel das fases entram **três blocos informativos** de largura inteira, com `01 Carregar árvore GEDCOM`, `02 Encontrar conexão documental` e `03 Cruzar com evidência genética`, cada um com sua descrição.
Motivo: o operador mostrou a faixa de três blocos da referência e pediu que ela entrasse igual, acima do cabeçalho da fase 1.
Arquivos previstos: `src/templates/index.html`, `src/assets/app.css`, `tests/test_icone_de_atalho.py`.

### E006, 2026-10-20

O que muda: uma **fileira de três abas** entra acima do painel, entre os passos da jornada e a barra lateral, com os mesmos nomes das fases — `Árvores GEDCOM`, `Buscar Conexão no GEDCOM` e `Analisador de DNA`. Ela **não substitui** a barra lateral: os dois controles apontam para os mesmos três painéis, e um script sincroniza `.active` e `aria-selected` entre eles.
Motivo: o operador pediu as abas da referência visual como segundo controle das mesmas fases. A decisão `Q-01` (só a barra lateral) fica **parcialmente revertida**, de forma declarada.
Arquivos previstos: `src/templates/index.html`, `src/assets/app.css`, `tests/test_tres_fases_da_tela.py`, `tests/test_icone_de_atalho.py`.

### E007, 2026-10-20

O que muda: as três abas deixam de atravessar a largura inteira acima da barra lateral e passam a ficar **na coluna do conteúdo**, ao lado da barra — alinhadas com o topo dela e acima do painel da fase.
Motivo: o operador apontou que as abas estavam acima da coluna da barra lateral, e pediu que ficassem na lateral, na posição da referência visual.
Arquivos previstos: `src/assets/app.css`.

### E008, 2026-10-20

O que muda: a fileira de abas deixa de ter barra de rolagem. Em vez de rolar na horizontal, ela **quebra** em duas linhas quando não couber.
Motivo: o operador mostrou uma barra de rolagem aparecendo na própria fileira de abas, à direita, e pediu que ela saísse.
Arquivos previstos: `src/assets/app.css`.

### E009, 2026-10-20

O que muda: a arte da masthead passa a ficar dentro de uma **caixa** com fundo próprio, borda, cantos arredondados (16 px) e sombra curta, nos dois temas.
Motivo: o operador pediu sombra ou efeito equivalente na arte, e que ela ficasse dentro de uma caixa de cantos arredondados como na referência visual.
Arquivos previstos: `src/assets/app.css`.

### E010, 2026-10-20

O que muda: a tipografia do aplicativo passa a ser a da sugestão visual — **Cormorant Garamond** nos títulos e **Manrope** no texto —, com os pesos e os tratamentos daquela folha: `h1`/`h2`/`h3` em 700, `strong` em 800, *eyebrow* em caixa alta com 0,14 em de espaçamento, rótulos em 800, campos e botões com raio de 12 px. Se o CDN não responder, a pilha cai nas nativas (`Georgia` nos títulos, `system-ui`/`Segoe UI` no texto).
Motivo: o operador pediu para usar as definições detalhadas de `D:\dados-genealogicos\Importa.css`, com as nativas como plano B quando não houver internet.
Arquivos previstos: `src/templates/index.html`, `src/assets/app.css`, `tests/test_icone_de_atalho.py`.

### E011, 2026-10-20

O que muda: o bloco "Observações do arquivo" passa a nascer **fechado**; continua recolhível, com o mesmo título.
Motivo: o operador pediu o padrão fechado na aba "Analisador de DNA".
Arquivos previstos: `src/templates/index.html`, `tests/test_observacoes_do_arquivo.py`.

### E012, 2026-10-20

O que muda: os textos logo abaixo de "Resultados das Análises de Conexão" — a contagem em três faixas, a frase da árvore sugerida e a legenda do selo — passam a ser **um único parágrafo**, sem a quebra `<br>` no meio.
Motivo: o operador pediu que os textos ficassem num parágrafo só e organizados.
Arquivos previstos: `src/templates/index.html`.
