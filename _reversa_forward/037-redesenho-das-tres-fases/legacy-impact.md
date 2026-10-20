# Impacto no legado: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `domain.md` e `tela-de-entrada/`)

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/templates/index.html` | Tela de entrada (`architecture.md#3`) | `regra-alterada` | MEDIUM | A navegação passa de duas abas horizontais para uma barra lateral com três fases; lista e envio migram para a fase 1; cada fase ganha cabeçalho e caixa de status |
| `src/templates/index.html` | Combobox de nomes (novo, dentro da tela) | `regra-nova` | MEDIUM | Os três campos de nome deixam de ser `<input list>` + `<datalist>` e passam a um combobox com lista filtrada, ARIA próprio e teclado |
| `src/assets/app.css` | Folha de estilo (`addenda/013`) | `regra-alterada` | LOW | Bloco novo para as fases, contadores, caixa de status, blocos, tabela listrada, combobox e ajuste de escala do botão de tema |
| `tests/test_icone_de_atalho.py` | Invariante `SHA_DA_TELA` (`recursos-da-tela`) | `delta-de-contrato-externo` | MEDIUM | O hash da tela vazia muda de `c4a34f7b…` (30.781 bytes) para `794711aa…` (38.484 bytes) — mudança declarada, com medição |

**Contagem por tipo:** `regra-alterada` 2 · `regra-nova` 1 · `delta-de-contrato-externo` 1 — **4 impactos**.

## Diff conceitual por componente

**Tela de entrada.** O bloco de `{% if %}`/`{% else %}` que duplicava a fileira de abas virou um esqueleto único com três painéis. Cada painel tem cabeçalho (`Fase N — <nome>`), objetivo de uma linha e caixa de status. A fase 1 concentra a lista e o envio; as fases 2 e 3 só têm formulário com árvore aberta, e sem árvore mostram um estado vazio que aponta para a fase 1. A fase ativa vem do servidor (`gedcom_filename` → fase 2). O caminho de volta deixou de ser um parágrafo acima das fases e passou a ser a caixa de status da fase 1, com o mesmo literal `escolher outra árvore` e o mesmo `href="/"`.

**Combobox de nomes.** A `<datalist id="gedcom_names">` saiu. `all_names` passa a ser escrita uma vez como JSON (`<script type="application/json" id="nomes-da-arvore">`), e um script embutido monta a lista filtrada (sem acento e sem caixa), com teto de 50 opções, `role="listbox"`, `aria-activedescendant`, ↑/↓/`Enter`/`Esc` e região viva. O texto digitado continua livre: nenhum campo virou `select` e nenhum `name` mudou.

**Folha de estilo.** Bloco novo prefixado por `.fases-da-tela`/`.fase-*`, mais a tabela listrada e o empilhamento das ações. Nenhum token de estado (`--st-*`) foi tocado; os quatro contrastes de estado da feature 026 continuam válidos.

## Preservadas

- `_reversa_sdd/domain.md#3.1` e `#3.2` — parentesco documental e evidência genética não se contaminam; a tela continua dizendo que o DNA não altera o parentesco.
- `_reversa_sdd/domain.md#3.6` — listar, escolher e aposentar; a listagem continua sem filtro, decidindo a fase pela extensão do nome cru.
- `_reversa_sdd/domain.md#5` — contrato de mensagens: nenhuma mensagem de sucesso ou erro foi alterada.
- `_reversa_sdd/tela-de-entrada/contracts.md#1.2` — as duas listas continuam vindo do processador de contexto; nenhuma variável nova.
- `_reversa_sdd/tela-de-entrada/contracts.md#2.1` e `#2.4` — colunas, disponibilidade e os dois motivos de indisponibilidade intactos.
- `_reversa_sdd/addenda/017` — observações do arquivo continuam fora dos cartões.
- `_reversa_sdd/addenda/019` — a tabela do índice de resultados **não** voltou.
- `_reversa_sdd/addenda/036` — a área de resultados (cartão em três faixas, barra, selos) não foi tocada.
- `_reversa_sdd/addenda/021` — `accept` continua filtrando o seletor e não validando.

## Modificadas

- `_reversa_sdd/tela-de-entrada/requirements.md#RF-22` (abas e rótulos idênticos nos dois estados) — **o conjunto de abas deixou de ser dois**. A simetria entre os dois estados continua, agora com três fases; o texto do RF precisa de emenda na extração.
- `_reversa_sdd/tela-de-entrada/requirements.md#RF-21` (estado vazio por aba) — o estado vazio da fase 3 passou a conviver com a lista de relatórios quando ela existe, e a orientação de envio mudou de "aba" para "fase".
- Nenhuma regra de `_reversa_sdd/domain.md` foi criada, alterada ou removida.

## Emendas

### E001, 2026-10-20 — masthead em duas colunas

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/templates/index.html` | Masthead (`recursos-da-tela#a-masthead`) | `regra-alterada` | MEDIUM | A arte, o subtítulo, o título e os dois parágrafos deixam de ser um bloco empilhado e centrado: passam a duas colunas nomeadas (`masthead-texto` e `masthead-arte`). A ordem do documento não muda — a arte continua sendo o primeiro elemento |
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | Entra a grade `.masthead` (duas colunas, uma no telefone) e a forma de sobretítulo do subtítulo |
| `tests/test_banner_do_topo.py` | Teste da `RN-24` | `regra-alterada` | MEDIUM | O teste que prendia "centralizado em `col-lg-*`" foi reescrito para prender a coluna própria e a grade; a regra antiga deixou de valer |
| `tests/test_icone_de_atalho.py` | Invariante `SHA_DA_TELA` | `delta-de-contrato-externo` | MEDIUM | `794711aa…` (38.484 bytes) → `c5fb4ff7…` (38.476 bytes): a masthead faz parte de `GET /` |

**Contagem da emenda:** `regra-alterada` 3 · `delta-de-contrato-externo` 1 — **4 impactos**.

Esta emenda **altera a `RN-24`** do adendo `011` ("texto centralizado em coluna mais estreita"), preservada pela entrega original desta feature. A mudança é declarada, não silenciosa: ela está registrada em `requirements.md#emendas` (`E001`) e no teste que a prendia.

- **Preservadas:** a ordem do documento (arte → subtítulo → título → texto), o `<h1>` sempre visível (`RN-23`), o `alt` que descreve a ilustração, o teto de 280 px da arte (`addenda/027`) e as três ênfases em negrito do texto.
- **Modificadas:** `RN-24` (adendo `011`) — de centralizado em coluna estreita para coluna própria à esquerda, com a arte ao lado.

### E002, 2026-10-20 — separação entre a masthead e as fases

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | `.fases-da-tela` ganha `margin-top`, `padding-top` e uma borda superior de 1 px na cor `--line`; no telefone os dois valores encolhem |

**Contagem da emenda:** `regra-alterada` 1 — **1 impacto**.

Só apresentação: nenhuma marcação, texto, rota ou variável mudou, e o `SHA_DA_TELA` continua `c5fb4ff7…` (38.476 bytes) — a mudança é de folha, e o hash mede o documento.

### E003, 2026-10-20 — cabeçalho da fase na largura inteira

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | `.identidade-da-fase` ganha `flex:1 1 auto` e `min-width:0`; a caixa de status perde o `max-width:100%` e ganha `flex:0 0 auto` com teto de 280 px; o cabeçalho deixa de quebrar em duas linhas no desktop e volta a quebrar no telefone |

**Contagem da emenda:** `regra-alterada` 1 — **1 impacto**.

Corrige um efeito colateral da `E002`: com a área mais larga, o cabeçalho da fase 3 quebrava antes de caber a caixa de status. `SHA_DA_TELA` **inalterado** (`c5fb4ff7…`, 38.476 bytes).

### E004, 2026-10-20 — rótulos da fase 3 alinhados pelo topo

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | `.linha-de-campos` passa de `align-items:end` para `start`, e `.campo-da-acao` ganha `align-self:end` para o botão continuar no rodapé da linha na fase 2 |

**Contagem da emenda:** `regra-alterada` 1 — **1 impacto**.

Só apresentação: nenhuma marcação, texto, rota ou variável mudou. `SHA_DA_TELA` **inalterado** (`c5fb4ff7…`, 38.476 bytes).

### E005, 2026-10-20 — os três passos da jornada

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/templates/index.html` | Tela de entrada (`architecture.md#3`) | `regra-alterada` | MEDIUM | Entram três blocos informativos (`01 Carregar árvore GEDCOM`, `02 Encontrar conexão documental`, `03 Cruzar com evidência genética`) na primeira linha da grade das fases, antes da barra lateral |
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | `.passos-da-jornada` e `.passo*`: grade de três colunas que quebra sozinha, cartão em `--surface-2` e o número em círculo preenchido |
| `tests/test_icone_de_atalho.py` | Invariante `SHA_DA_TELA` | `delta-de-contrato-externo` | MEDIUM | `c5fb4ff7…` (38.476 bytes) → `ed4f8734…` (40.222 bytes, +1.746) |

**Contagem da emenda:** `regra-alterada` 2 · `delta-de-contrato-externo` 1 — **3 impactos**.

Os blocos são **informativos**: não são clicáveis, não entram no `tablist` e não substituem a navegação. O texto é o que o operador forneceu, literal.

### E006, 2026-10-20 — as três abas como segundo controle

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/templates/index.html` | Tela de entrada (`architecture.md#3`) | `regra-alterada` | MEDIUM | Entra uma fileira de três abas (`Árvores GEDCOM`, `Buscar Conexão no GEDCOM`, `Analisador de DNA`) entre os passos e a barra lateral, apontando para os mesmos painéis; entra também o script que sincroniza `.active` e `aria-selected` entre os dois controles |
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | `.abas-das-fases` ocupa a largura inteira na grade e rola na horizontal em tela estreita |
| `tests/test_tres_fases_da_tela.py` | Teste das fases | `regra-alterada` | MEDIUM | O teste que prendia "nenhuma fileira de abas" (`Q-01`) foi reescrito para prender os **dois controles por fase** |
| `tests/test_icone_de_atalho.py` | Invariante `SHA_DA_TELA` | `delta-de-contrato-externo` | MEDIUM | `ed4f8734…` (40.222 bytes) → `3bac6c24…` (42.293 bytes, +2.071) |

**Contagem da emenda:** `regra-alterada` 3 · `delta-de-contrato-externo` 1 — **4 impactos**.

**A `Q-01` fica parcialmente revertida**, de forma declarada: a resposta original era "barra lateral como controle único, as abas saem". O operador pediu as abas de volta como segundo controle; a barra lateral permanece, e o estado dos dois passa a ser sincronizado por script. O rótulo da primeira aba é `Árvores GEDCOM` (e não `Buscar Conexão no GEDCOM`, como no mockup), para não trocar de nome com a fase 2.

### E007, 2026-10-20 — as abas ao lado da barra

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | As abas passam de `grid-column:1 / -1` para a coluna 2; a barra lateral passa a ocupar `grid-row:2 / span 2`, começando na linha das abas; no telefone os quatro blocos voltam a `grid-column:1;grid-row:auto` |

**Contagem da emenda:** `regra-alterada` 1 — **1 impacto**.

Só folha: nenhuma marcação mudou, e o `SHA_DA_TELA` continua `3bac6c24…` (42.293 bytes).

### E008, 2026-10-20 — sem barra de rolagem nas abas

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | `.abas-das-fases` perde `flex-wrap:nowrap` e `overflow-x:auto`; a fileira volta ao `flex-wrap:wrap` do Bootstrap e quebra em vez de rolar |

**Contagem da emenda:** `regra-alterada` 1 — **1 impacto**.

Só folha: nenhuma marcação mudou, e o `SHA_DA_TELA` continua `3bac6c24…` (42.293 bytes).

### E009, 2026-10-20 — a arte dentro de uma caixa

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | LOW | `.masthead-arte` ganha `padding`, `background:var(--surface-2)`, `border`, `border-radius:16px` e `box-shadow` (mais opaca no tema escuro); a imagem mantém o teto de 280 px |

**Contagem da emenda:** `regra-alterada` 1 — **1 impacto**.

O painel da direita deixou de ser o vazio em volta da arte e passou a ser uma superfície própria, com o mesmo peso do bloco de texto. No tema escuro a arte continua sobre a placa clara da feature 027 — a caixa emoldura a ilustração, não a substitui. `SHA_DA_TELA` **inalterado**.

### E010, 2026-10-20 — a tipografia da sugestão visual

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/templates/index.html` | `<head>` — carga de webfont | `delta-de-contrato-externo` | MEDIUM | O link do Google Fonts passa de `Newsreader` + `IBM Plex Sans` para `Cormorant Garamond` + `Manrope`, mesma origem e mesmo `display=swap`. Sem resposta do CDN, a pilha usa `Georgia` e `system-ui` |
| `src/assets/app.css` | Folha de estilo | `regra-alterada` | MEDIUM | `--serif` e `--bs-body-font-family` trocam de família; entram a escala da referência (`h1` 700 até 3,8 rem, `h2` até 2,1 rem), `strong` 800, rótulos 800, *eyebrow* em caixa alta e raio de 12 px em campos e botões |
| `tests/test_icone_de_atalho.py` | Invariante `SHA_DA_TELA` | `delta-de-contrato-externo` | MEDIUM | `3bac6c24…` (42.293 bytes) → `7375696d…` (42.290 bytes, −3): o link da fonte ficou três bytes mais curto |

**Contagem da emenda:** `regra-alterada` 1 · `delta-de-contrato-externo` 2 — **3 impactos**.

**A tipografia alcança a área de resultados.** A `RN-14` dizia que a área de resultados não seria tocada pela feature; a troca de família é global e muda a fonte do título de resultados e dos cartões. É mudança **declarada**, e não de estrutura: nenhuma regra de layout, cor, contraste ou texto dos resultados foi alterada.

**Tamanho do `h1` menor que a referência.** A folha de origem usa `clamp(2.8rem, 5vw, 4.9rem)`; aqui o teto é **3,8 rem**, porque o título divide a linha com a arte dentro de um cartão de largura fixa. Peso, família e entrelinha são os da referência.

### E011, 2026-10-20 — o bloco de observações nasce fechado

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md` | a regra "nasce aberto" | `regra-alterada` | MEDIUM | O bloco continua recolhível, com o mesmo título e o mesmo lugar, mas deixa de vir aberto: o padrão passa a ser fechado |
| `tests/test_observacoes_do_arquivo.py` | teste do bloco | `regra-alterada` | MEDIUM | O teste que prendia "nasce aberto" foi reescrito para prender "nasce fechado", com a regra anterior citada no docstring |

**Contagem da emenda:** `regra-alterada` 2 — **2 impactos**.

**A `RN-14` da feature (resultados intocados) fica emendada por esta e pela `E012`.** O adendo `017` tirou os avisos de dentro dos cartões para eles serem lidos, e o `022` os deixou abertos por isso. O custo da mudança está declarado no template: quem abre a análise vê o título do bloco, e o clique é um só.

### E012, 2026-10-20 — o resumo em um parágrafo

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `_reversa_sdd/addenda/033-contador-em-tres-faixas.md` | a frase da contagem | `regra-alterada` | LOW | A frase continua com as três faixas e os mesmos números, mas passa a dividir o parágrafo com a sugestão e a legenda; o `<br>` entre elas saiu |
| `_reversa_sdd/addenda/031-veredito-no-cartao.md` | a legenda do selo | `presença` | LOW | A legenda continua na tela, com as duas classes de selo; deixou de ser um `<p>` próprio e virou um `span.legenda-da-validacao` dentro do parágrafo do resumo |

**Contagem da emenda:** `regra-alterada` 1 · `presença` 1 — **2 impactos**.

Só marcação: nenhum número, texto de contrato ou regra de cálculo mudou. O `SHA_DA_TELA` **não** muda, porque o resumo vive dentro de `{% if dna_results %}` e o hash mede a tela vazia.










