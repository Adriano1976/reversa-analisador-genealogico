# Adendo: redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e `_reversa_sdd/tela-de-entrada/`)

## Vigência

Vigente desde 2026-10-20.

## Resumo da entrega

A tela de entrada deixou de ter **duas abas horizontais** e passou a ter **três fases numa barra lateral** — `1. Árvores GEDCOM`, `2. Buscar Conexão no GEDCOM` e `3. Analisador de DNA` —, iguais nos dois estados da tela (sem árvore e com árvore aberta). A lista de arquivos e o envio migraram para a fase 1, que ganhou dois contadores calculados da própria lista e uma caixa de status; as fases 2 e 3 só oferecem formulário com árvore aberta, e sem árvore explicam onde ela se abre.

A segunda entrega é funcional: os três campos de nome deixaram de ser `<input list>` + `<datalist>` e passaram a ser um **combobox** com lista filtrada (sem acento e sem caixa), teto de 50 opções, teclado e ARIA próprio. O texto digitado continua livre — a busca recebe exatamente o que o operador escreveu.

**Vinte e oito ações concluídas** (28 de 28). Suíte: 1309 → **1334 passam**, 11 pulados, zero falhas. `GET /` com pasta vazia: 30.781 bytes (`c4a34f7b…`) → **38.484 bytes (`794711aa…`)**, mudança declarada e medida.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `regra-alterada` | A tela de entrada (`src/templates/index.html`) passa a ter três painéis com cabeçalho e caixa de status, e a folha (`src/assets/app.css`, servida por `GET /app.css`) ganha um bloco `.fases-da-tela`. Nenhuma rota, `action` ou variável de template nova |
| `_reversa_sdd/architecture.md` | `#3` | `regra-nova` | Entra um componente de tela: o **combobox de nomes**, alimentado por um bloco `application/json` e operado por script embutido. Sem dependência nova e sem rota nova |
| `_reversa_sdd/tela-de-entrada/requirements.md` | `#requisitos-funcionais` (`RF-21`, `RF-22`) | `regra-alterada` | `RF-22` deixa de valer como "duas abas": são **três fases**, simétricas nos dois estados. O estado vazio de `RF-21` passou a apontar para a fase 1, e a fase 3 mantém a lista de relatórios quando ela existe |
| `_reversa_sdd/tela-de-entrada/contracts.md` | `#2.1` a `#2.4` (listagem) | `presença` | Colunas, agrupamento, rótulo, disponibilidade e os dois motivos de indisponibilidade continuam idênticos; só a leitura visual mudou |
| `_reversa_sdd/domain.md` | `#3.6` (listar, escolher e aposentar) | `presença` | Nenhuma regra de domínio mudou: a listagem continua sem filtro e a ação destrutiva continua sendo "aposentar" |
| `_reversa_sdd/domain.md` | `#3.1`, `#3.2` e `#5` | `presença` | Os eixos documental/genético continuam separados, e as mensagens de sucesso e erro são as mesmas |
| `_reversa_sdd/recursos-da-tela/requirements.md` | `#a-masthead` | `presença` | A masthead não foi tocada: arte, `<h1>` visível e `RN-24` continuam válidos |
| `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` | `RN-19` (caminho de volta) | `presença` | O link `escolher outra árvore` continua em `href="/"`, agora dentro da caixa de status da fase 1, e não mais acima das abas |
| `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md` | a tabela do índice de resultados | `presença` | Ela **não** voltou: a tabela que existe na fase 1 é a de arquivos armazenados, não a de resultados |
| `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` | o cartão de resultado | `presença` | A área de resultados não é alcançada por nenhuma regra nova; o cartão em três faixas continua como a `036` entregou |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 telas literais | `presença` | `GET /` com pasta vazia mudou de bytes e de hash: `c4a34f7b…` (30.781) → `794711aa…` (38.484). A declaração está em `tests/test_icone_de_atalho.py` |
| `_reversa_sdd/design-system/tokens-derived.md` | "Cores" | `presença` | ⚠️ O arquivo derivado continua anterior à folha servida por rota e **não** descreve a paleta atual nem o bloco das fases. Dívida documental declarada, não delta desta entrega |

**Contagem por tipo:** `regra-alterada` 2 · `regra-nova` 1 · `presença` 9 — **12 impactos**.

Nenhuma regra de `_reversa_sdd/domain.md` foi criada, alterada ou removida. Não há `delta-de-dados` (nenhum campo, tabela, payload ou migração) nem `delta-de-contrato-externo` (as rotas mantêm método, corpo e códigos; o documento de `GET /` mudou, o contrato HTTP não).

## Regras sob vigilância

`W001` a `W011`, definidos em
`_reversa_forward/037-redesenho-das-tres-fases/regression-watch.md`, mais as observações `OBS-01` a `OBS-04` do mesmo arquivo.

| Item | Cobre |
|------|-------|
| `W001` | Três fases na barra lateral, iguais nos dois estados |
| `W002` | Fases 2 e 3 sem campo quando não há árvore |
| `W003` | Tabela da fase 1: seis colunas, `Abrir` só no disponível |
| `W004` | Contadores apenas com total e disponíveis |
| `W005` | `<datalist>` e `gedcom_names` ausentes |
| `W006` | Nome com `</script>` não fecha o bloco JSON |
| `W007` | ARIA do combobox e da lista |
| `W008` | Literais congelados idênticos |
| `W009` | Link `escolher outra árvore` na caixa de status |
| `W010` | Área de resultados intocada |
| `W011` | `SHA_DA_TELA` = `794711aa…`, 38.484 bytes |

## Fontes

- `_reversa_forward/037-redesenho-das-tres-fases/requirements.md`
- `_reversa_forward/037-redesenho-das-tres-fases/roadmap.md`
- `_reversa_forward/037-redesenho-das-tres-fases/actions.md` (28 ações)
- `_reversa_forward/037-redesenho-das-tres-fases/legacy-impact.md`
- `_reversa_forward/037-redesenho-das-tres-fases/regression-watch.md`
- `_reversa_forward/037-redesenho-das-tres-fases/progress.jsonl` (28 linhas)
- `_reversa_forward/037-redesenho-das-tres-fases/evidence/RELATORIO.md`
- `_reversa_forward/037-redesenho-das-tres-fases/evidence/depois/hash.txt`
- `_reversa_sdd/tela-de-entrada/contracts.md#1.2` e `#2.2`
- `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md` (a folha servida por rota)
- `_reversa_sdd/addenda/021-seletor-de-arquivos-por-formato.md` (`accept` filtra e não valida)

## Atualização 2026-10-20

A emenda `E001` da mesma feature mudou a **masthead**, que a entrega original tinha deixado intocada. O bloco de arte, subtítulo, título e texto de apresentação deixou de ser empilhado e centralizado e passou a **duas colunas**: o texto na coluna da esquerda, alinhado à esquerda, e a arte na da direita. No telefone as colunas viram uma so, com a arte em cima — a ordem do documento não mudou (a arte continua sendo o primeiro elemento).

Isso **emenda a `RN-24`** do adendo `011`, que exigia o texto centralizado numa coluna mais estreita que o cartão. A emenda está declarada em `_reversa_forward/037-redesenho-das-tres-fases/requirements.md#emendas` (`E001`) e o teste que prendia a regra antiga foi reescrito para prender a coluna própria e a grade, com o motivo no docstring.

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/recursos-da-tela/requirements.md` | `#a-masthead` | `regra-alterada` | A masthead passa a ter duas colunas nomeadas (`masthead-texto` e `masthead-arte`); o `<h1>`, o `alt` e as três ênfases continuam iguais |
| `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` | `RN-24` | `regra-alterada` | A regra deixa de ser "centralizado em coluna estreita" e passa a ser "coluna própria à esquerda, com a arte ao lado" |
| `_reversa_sdd/addenda/027-harmonizar-topo-da-tela.md` | `W004` (escala do `h1` e da arte) | `presença` | O `h1` continua ≤ 2,2 rem e a arte continua com teto de 280 px; a arte agora preenche a coluna direita até esse teto |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 telas literais | `presença` | `GET /` com pasta vazia: `794711aa…` (38.484 bytes) → `c5fb4ff7…` (38.476 bytes, −8). O saldo negativo é a troca de `text-center` + `row justify-content-center` + `col-lg-9` pelas duas colunas |

**Contagem desta atualização:** `regra-alterada` 2 · `presença` 2 — **4 impactos**, que somados aos 12 da entrega original dão **16** no adendo.

Suíte depois da emenda: **1334 passam, 11 pulados**, zero falhas. Nenhum teste removido — o da `RN-24` foi substituído por um que mede o novo arranjo.

As regras sob vigilância continuam sendo `W001` a `W011`; a `W011` passa a valer com o hash novo (`c5fb4ff7…`, 38.476 bytes), e a emenda acrescentou a `W012`, que cobre a masthead em duas colunas e a `RN-24` emendada.

## Atualização 2026-10-20 (emenda E002)

A emenda `E002` separou visualmente a **masthead** e o **bloco das fases**, que estavam encostados. A área das fases ganhou ar acima, respiro depois da linha e uma linha fina na cor `--line`, que é a mesma das bordas dos cartões e vale nos dois temas. No telefone os espaçamentos encolhem.

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (a folha de estilo) | `regra-alterada` | `.fases-da-tela` ganha `margin-top`, `padding-top` e `border-top`; nenhum componente, marcação, rota ou variável muda |

**Contagem desta atualização:** `regra-alterada` 1 — **1 impacto**, que somado aos 12 da entrega e aos 4 da `E001` dá **17** no adendo.

O `SHA_DA_TELA` **não** mudou (`c5fb4ff7…`, 38.476 bytes): a alteração é de folha, e o hash mede o documento. Suíte: **1334 passam, 11 pulados**.

## Atualização 2026-10-20 (emendas E003 a E005)

Três emendas de apresentação, todas vistas na tela renderizada:

- **`E003`** — o cabeçalho de cada fase passou a ocupar a largura inteira do painel, com a caixa de status ancorada na borda direita. Antes, o cabeçalho da fase 3 quebrava em duas linhas e deixava um vazio à direita.
- **`E004`** — os rótulos dos campos da fase 3 passaram a começar na mesma linha: a grade alinhava as células por baixo, e a coluna mais curta empurrava o próprio rótulo para baixo.
- **`E005`** — entraram **três blocos informativos** de largura inteira entre a linha divisória e o painel das fases: `01 Carregar árvore GEDCOM`, `02 Encontrar conexão documental` e `03 Cruzar com evidência genética`. Não são clicáveis e não entram na navegação.

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (a tela de entrada e a folha) | `regra-alterada` | A tela ganha a faixa de três blocos informativos antes da navegação; a folha ganha `.passos-da-jornada`/`.passo*`, o cabeçalho de fase de largura inteira e o alinhamento pelo topo da grade de campos |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 telas literais | `presença` | `GET /` com pasta vazia: `c5fb4ff7…` (38.476 bytes) → `ed4f8734…` (40.222 bytes, +1.746). O delta é a marcação e o texto dos três blocos — as emendas `E003` e `E004` foram só de folha e não moveram o hash |

**Contagem desta atualização:** `regra-alterada` 1 · `presença` 1 — **2 impactos**, que somados aos 17 anteriores dão **19** no adendo.

Suíte: **1334 passam, 11 pulados**, zero falhas. O `SHA_DA_TELA` foi atualizado com a conta declarada no próprio teste (+1.746 bytes).

## Atualização 2026-10-20 (emendas E006 e E007)

Duas emendas que mudaram a navegação:

- **`E006`** — entrou uma **fileira de três abas** com os mesmos nomes das fases (`Árvores GEDCOM`, `Buscar Conexão no GEDCOM`, `Analisador de DNA`), como **segundo controle** dos mesmos três painéis. A barra lateral não saiu. Um script escuta `shown.bs.tab` e iguala `.active` e `aria-selected` nos dois, para não existirem dois "selecionados" para um painel só.

  **A `Q-01` fica parcialmente revertida**, de forma declarada: a resposta de 2026-10-20 era "barra lateral como controle único, as abas saem". Agora as abas voltam, e a decisão vigente é "dois controles, um destino, estado sincronizado".

- **`E007`** — as abas deixaram de atravessar a largura inteira acima da barra e passaram para a **coluna do conteúdo**, ao lado da barra: a lateral começa na linha das abas (`grid-row:2 / span 2`) e as abas ficam em `grid-column:2; grid-row:2`, com o painel logo abaixo.

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (a tela de entrada e a folha) | `regra-alterada` | A tela de entrada passa a ter **dois controles** para as mesmas três fases (barra lateral e abas), com sincronia de estado por script; a folha posiciona os dois na grade |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 telas literais | `presença` | `GET /` com pasta vazia: `ed4f8734…` (40.222 bytes) → `3bac6c24…` (42.293 bytes, +2.071). A `E007` foi só de folha e não moveu o hash |

**Contagem desta atualização:** `regra-alterada` 1 · `presença` 1 — **2 impactos**, que somados aos 19 anteriores dão **21** no adendo.

Suíte: **1334 passam, 11 pulados**, zero falhas nas telas. Permanecem **duas falhas de ambiente** alheias a esta feature: `test_gera_png` e `test_gera_svg` falham em `import graphviz` desde que o binário `dot` passou a estar no PATH — o binding Python não está instalado.

## Atualização 2026-10-20 (emenda E008)

A fileira de abas deixou de ser um contêiner de rolagem. A `E006` a tinha deixado com `flex-wrap:nowrap` + `overflow-x:auto`, e o navegador passou a reservar a barra na própria fileira. Agora ela volta ao `flex-wrap: wrap` do Bootstrap: **quebra** em duas linhas quando não couber, em vez de rolar. Não há mais nenhum eixo com barra.

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (a folha de estilo) | `regra-alterada` | `.abas-das-fases` perde as duas declarações de rolagem e passa a quebrar a fileira; nenhuma marcação, rota ou variável muda |

**Contagem desta atualização:** `regra-alterada` 1 — **1 impacto**, que somado aos 21 anteriores dá **22** no adendo.

O `SHA_DA_TELA` **não** mudou (`3bac6c24…`, 42.293 bytes): a alteração é de folha. Suíte de telas: **90 passam** nos arquivos afetados.

## Atualização 2026-10-20 (emendas E009 e E010)

Duas emendas de aparência, ambas vindas da folha da sugestão visual:

- **`E009`** — a arte da masthead passou a ficar dentro de uma **caixa** com fundo `--surface-2`, borda, cantos de 16 px e sombra curta (mais opaca no escuro). O painel da direita deixou de ser o vazio em volta da ilustração.
- **`E010`** — a **tipografia** passou a ser a de `D:\dados-genealogicos\Importa.css`: `Cormorant Garamond` nos títulos e `Manrope` no texto, com `h1`/`h2`/`h3` em 700, `strong` em 800, rótulos em 800, o sobretítulo em caixa alta e 0,14 em, e campos e botões com raio de 12 px.

  **As nativas são o plano B:** a pilha cai em `Georgia` (títulos) e `system-ui`/`Segoe UI` (texto) se o CDN não responder, e o `display=swap` mostra o texto na nativa desde o primeiro quadro.

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (a folha de estilo) | `regra-alterada` | `.masthead-arte` vira uma superfície com sombra; `--serif`/`--bs-body-font-family` trocam de família e a escala tipográfica muda (títulos 700, `strong` 800, raios de 12 px) |
| `_reversa_sdd/architecture.md` | `#6` (Mapa de Integrações Externas) | `delta-de-contrato-externo` | As famílias carregadas do Google Fonts mudam de `Newsreader`/`IBM Plex Sans` para `Cormorant Garamond`/`Manrope`. Mesma origem, mesmo `display=swap`; sem rede, o app usa as nativas |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 telas literais | `presença` | `GET /` com pasta vazia: `3bac6c24…` (42.293 bytes) → `7375696d…` (42.290 bytes, −3): o link da fonte ficou três bytes mais curto |

**Contagem desta atualização:** `regra-alterada` 1 · `delta-de-contrato-externo` 1 · `presença` 1 — **3 impactos**, que somados aos 22 anteriores dão **25** no adendo.

Dois pontos que precisam sobreviver à próxima extração:

1. **A tipografia alcança a área de resultados.** A `RN-14` dizia "resultados intocados"; a troca de família é global, então o título de resultados e os cartões mudam de tipo. Nenhuma regra de layout, cor ou texto deles mudou.
2. **O `h1` fica abaixo do tamanho da referência.** A folha de origem vai a 4,9 rem; aqui o teto é 3,8 rem, porque o título divide a linha com a arte dentro de um cartão de largura fixa.

Suíte: **1334 passam, 9 pulados**, com as duas falhas de ambiente do `graphviz` (`test_gera_png` e `test_gera_svg`).

## Atualização 2026-10-20 (emendas E011 e E012)

Duas emendas na **área de resultados** — a primeira vez que esta feature mexe nela, o que emenda a `RN-14` dela própria.

- **`E011`** — o bloco **"Observações do arquivo" passa a nascer fechado**. Continua recolhível, no mesmo lugar e com o mesmo título; o padrão deixou de ser aberto.

  Isto **reverte uma decisão do adendo `022`**, que o deixou aberto porque o bloco carrega aviso, e o adendo `017` o havia tirado de dentro dos cartões justamente para ser lido. O custo está declarado: o título continua visível, e abrir é um clique. Se o bloco voltar a esconder informação que muda a leitura do resultado, é esta a decisão a revisitar.

- **`E012`** — os textos abaixo de "Resultados das Análises de Conexão" passaram a ser **um parágrafo só**: a contagem em três faixas, a frase da árvore sugerida (sem o `<br>` que a separava) e a legenda do selo correm juntas. A legenda virou `span.legenda-da-validacao` **dentro** do parágrafo, e a classe foi mantida para o teste que a procura.

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md` | a regra "nasce aberto" | `regra-alterada` | O bloco passa a nascer fechado; título, recolhimento e lugar não mudam |
| `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md` | os avisos fora dos cartões | `presença` | Os avisos continuam fora dos cartões e continuam sendo a explicação do zero; a leitura passa a exigir um clique |
| `_reversa_sdd/addenda/033-contador-em-tres-faixas.md` | a frase da contagem | `regra-alterada` | A frase mantém as três faixas e os números, mas divide o parágrafo com a sugestão e a legenda |
| `_reversa_sdd/addenda/031-veredito-no-cartao.md` | a legenda do selo | `presença` | A legenda continua com as duas classes de selo, agora como `span` dentro do parágrafo do resumo |

**Contagem desta atualização:** `regra-alterada` 2 · `presença` 2 — **4 impactos**, que somados aos 25 anteriores dão **29** no adendo.

O `SHA_DA_TELA` **não** mudou (`7375696d…`, 42.290 bytes): o resumo e o bloco de observações vivem sob `{% if dna_results %}` e `{% if observacoes_do_arquivo %}`, e o hash mede a tela vazia.

## Atualização 2026-10-21

**A emenda `E009` foi revertida.** A caixa da arte — `background: var(--surface-2)`, `border: 1px solid var(--line)`, `border-radius: 16px` e `box-shadow` — deixou de existir. O motivo não foi estético: em 2026-10-21 a arte do topo passou a chegar **transparente**, e o fundo da caixa virou a única superfície entre o desenho e o cartão. O operador pediu para tirar o fundo, e o fundo era a caixa.

A sombra que a `E009` criou **continua existindo**, agora como `filter: drop-shadow(...)` na própria imagem, que segue a silhueta do desenho em vez de desenhar um retângulo. Sem essa troca, uma `box-shadow` sobre fundo transparente viraria névoa quadrada atrás da arte.

O que a `E009` estabeleceu e **permanece**: a arte ocupa a coluna 2 da grade, alinhada ao bloco de texto por `align-items:center`. O que saiu foi só a superfície.

Registro completo — incluindo a troca da arte que motivou tudo — em `_reversa_sdd/addenda/2026-10-21-arte-transparente-e-sombra-na-silhueta.md`.

**Contagem desta atualização:** `regra-removida` 1 · `regra-alterada` 1 — **2 impactos**, que somados aos 29 anteriores dão **31** no adendo.

O `SHA_DA_TELA` **não** mudou: a alteração é de folha de estilo, e o hash mede o HTML.







