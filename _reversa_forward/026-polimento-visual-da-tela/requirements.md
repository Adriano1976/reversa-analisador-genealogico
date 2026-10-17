# Requirements: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Esta feature responde a três pontos levantados numa revisão visual da tela de entrada: o favicon e o
ícone de atalho no `<head>`; a cor do estado `INCONCLUSIVO` do confronto; e a visibilidade do `<h1>`
quando a arte do topo está presente.

A leitura do template, da folha e dos adendos que os governam mostra que **dois dos três pontos não
são defeito**: o ícone de atalho não é declarado no documento **de propósito** (`RN-02` da feature
009), e a arte do topo **não traz mais o nome do produto** desde 2026-10-16, data em que o `<h1>`
voltou a ser sempre visível (`RN-23`, adendo `023`). O que sobra de real está na folha de estilo: o
token `--inc` está morto, o estado `INCONCLUSIVO` tem uma segunda declaração com o mesmo literal do
texto neutro, e um comentário da folha ainda repete a premissa vencida do banner.

A entrega é, portanto: **as três decisões tomadas na sessão de 2026-10-17**, registradas com a
medição que as sustenta, e **nenhuma mudança de comportamento** — apenas o ajuste da folha: o cinza do
`INCONCLUSIVO` ganha declaração própria e comentário, os quatro tokens sem uso saem, e o comentário
falso do banner é corrigido. O template não é tocado, então o `SHA_DA_TELA` não se move e as 8 telas
literais ficam intactas. As alternativas recusadas e o custo de cada uma estão na §9.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/recursos-da-tela/requirements.md#requisitos-funcionais` | `RF-07`: o ícone de atalho é descoberto por **caminho convencional**, sem declaração no documento. `RF-08`: o ícone da aba continua **`data URI`**, e nenhuma segunda rota de ícone é criada. `RF-09`: `favicon.ico` e `apple-touch-icon-precomposed.png` continuam **sem resposta** | 🟢 |
| `_reversa_sdd/recursos-da-tela/requirements.md#a-masthead` | "O título sobrevive à arte ausente **por construção**, e não por depender do `alt`"; a ordem da masthead é imagem → subtítulo → título em texto → apresentação (`BR-E-29`) | 🟢 |
| `_reversa_sdd/recursos-da-tela/requirements.md#requisitos-não-funcionais` | Degradação silenciosa: arte ausente é `404` vazio, a tela continua de pé e **o título é texto** | 🟢 |
| `_reversa_sdd/addenda/009-rota-do-apple-touch-icon.md#regras-sob-vigilância` | `W027` vigia "o template **sem** declarar o ícone, e `GET /` byte a byte"; declará-lo "toca a tela, contraria a `RN-02` e arranha o `W005`" | 🟢 |
| `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md#o-que-este-adendo-reverte-do-adendo-013` | A emenda que escondia o `<h1>` foi **retirada**; a `RN-23` volta a valer como escrita: o título é **texto visível** | 🟢 |
| `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md#regras-sob-vigilância` | "O `<h1>` está sempre visível" tem sinal de quebra explícito: a classe do `h1` ganhar `visually-hidden` sem uma arte que traga o texto | 🟢 |
| `_reversa_sdd/state-machines.md#32-tabela-de-transições` | A ordem de conservadorismo é `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`; o estado é **nome de classe CSS** (`badge estado-{{ status }}`) | 🟢 |
| `_reversa_sdd/state-machines.md#33-fatos-de-contrato` | `INCONCLUSIVO` é o estado **inicial** e o caminho de falha: "nenhum estado seja afirmado por omissão" | 🟢 |
| `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md#regras-alteradas` | O `visually-hidden` do título existiu **enquanto a arte trazia o título desenhado**; a condição vinha do servidor porque "o CSS não sabe se uma imagem carregou" | 🟢 |
| `_reversa_forward/009-rota-do-apple-touch-icon/regression-watch.md` | `W027` — o item que existe porque a tentação de acrescentar `<link rel="apple-touch-icon">` "parece inofensiva" e não é necessária | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` | `RF-17`: as 8 telas literais mantêm **diff textual zero** | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md` | `W005`: as mensagens da camada de rota e as mensagens congeladas continuam **ao caractere**, e "um literal que melhora de redação é violação" | 🟢 |
| `.reversa/principles.md#ii` | Comportamento observável é preservado; mudança de comportamento é feature | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |

### 2.1 O que foi medido nesta sessão (2026-10-17)

| Medição | Resultado |
|---------|-----------|
| Ícone da aba | **1** `<link rel="icon" type="image/png" sizes="128x128">`; o `data URI` decodifica para **14.456 bytes**, IHDR **128×128**, profundidade 8, tipo de cor 6. `sizes` confere com o arquivo |
| Ícone de atalho no documento | **0** ocorrências da cadeia `apple-touch-icon` no HTML servido |
| Ícone de atalho na rota | `GET /apple-touch-icon.png` → `200`, `image/png`, **16.504 bytes**, **180×180**, tipo de cor **2** (sem canal alfa) |
| Token `--inc` | **1** definição (`#6A6150`) e **0** usos na folha e no template |
| Token `--st-inconclusivo` | **1** definição (`#6A6150`, apenas no tema claro) e **1** uso (`.estado-INCONCLUSIVO`) |
| `--muted` | claro `#6A6150`; escuro `#A99F88` |
| Contraste do texto branco dos selos | `COMPATIVEL` **6,39:1**; `POSSIVEL` **7,13:1**; `CONFLITANTE` **6,69:1**; `INCONCLUSIVO` **6,11:1** |
| Caso histórico do laranja | `#fd7e14` com texto branco = **2,57:1** (o comentário da folha registra a falha) |
| Armadilha do alias | branco sobre `--muted` no tema escuro (`#A99F88`) = **2,62:1** |
| Candidato a cor própria | `#5B6B7A` com branco = **5,48:1**; contra o `--muted` claro = **1,11:1** (a diferença é de matiz, não de luminância) |
| Cobertura da tela | `SHA_DA_TELA = c4a34f7b…`, **30.781 bytes** de `GET /`, medido em `tests/test_icone_de_atalho.py` |
| Folha de estilo | `src/assets/app.css`, **391 linhas**, servida por `GET /app.css` (rota própria, fora do hash da tela) |
| Linha de base da suíte | **1.048 passam, 9 pulados, 0 falham** (`_reversa_forward/025-desempenho-carga-arvore/evidence/depois/suite.txt`) |

### 2.2 Correções ao enunciado

1. **O caminho da folha é `src/assets/app.css`**, e não `src/app.css`; ela sai por `GET /app.css`, e a
   rota existe porque `src/static/` é proibida (`W004`) e diretório estático é proibido (`RN-07`).
2. **`--inc` não pinta nada.** O estado `INCONCLUSIVO` usa `--st-inconclusivo`; a duplicidade de
   literal existe, mas entre `--muted` e `--st-inconclusivo`, não com um token em uso chamado `--inc`.
3. **A arte do topo não mostra o nome do produto** desde 2026-10-16. O pedido nasceu de uma leitura
   anterior à troca da arte; a §10 pede a confirmação dessa premissa.
4. **`W005` não é da feature de ícones.** O `W005` da feature 006 vigia os literais de tela; o item que
   vigia a não declaração do ícone de atalho é o `W027` da feature 009. Os dois são citados, cada um no
   seu lugar.
5. **`--muted` não é a cor do valor de cM (centimorgans).** Ele pinta o texto secundário — rótulos,
   legendas, "Sem destaque", os rótulos do bloco de cM e o cabeçalho do bloco dos descartados. O
   número de cM usa `.destaque`, em `--ink`. A distinção importa para não se criar uma regra sobre um
   papel que o token não cumpre.

### 2.3 Termos usados

| Termo | O que significa aqui |
|-------|----------------------|
| Selo (ou badge) | A etiqueta colorida que mostra o veredito de uma conexão; tem cor cheia e texto branco |
| `INCONCLUSIVO` / "Inconclusivo" | `INCONCLUSIVO` é o valor do estado e o nome da classe CSS; "Inconclusivo" é o rótulo que o operador lê |
| Token | Uma variável de cor da folha de estilo (`--muted`, `--st-inconclusivo`) |
| Arte do topo | O banner servido em `GET /banner.png`, derivado da fonte canônica |
| Golden | O HTML congelado de uma tela literal, em `_reversa_sdd/screens/golden/` |
| Hash da tela | O `sha256` do HTML de `GET /`, preso em `tests/test_icone_de_atalho.py` |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (persona única, sem login) | Reconhecer a tela pelo ícone certo e ler o veredito de cada conexão sem confundir "sem veredito" com "resultado neutro" | Salva o endereço na tela inicial do celular e percorre uma análise com conexões `INCONCLUSIVO` |
| Quem mantém a folha de estilo | Entender por que cada token existe, sem reintroduzir um alias que apague texto no tema escuro | Abre `app.css` para uma correção de cor e encontra a razão e o número medido ao lado do token |
| Revisor de acessibilidade e de paridade | Provar que o contraste dos quatro estados passa nos dois temas e que nenhum texto de tela mudou | Roda a suíte e compara as 8 telas literais com os goldens |

## 4. Regras de negócio novas ou alteradas

1. **RN-01: o documento continua com um único ícone de aba, embutido, e sem declaração de ícone de
   atalho.** O favicon é o `data URI` de 128×128; o ícone de atalho é descoberto pelo caminho
   convencional `/apple-touch-icon.png`. 🟢
   - Origem no legado: `_reversa_sdd/recursos-da-tela/requirements.md#requisitos-funcionais`
     (`RF-07`, `RF-08`, `RF-09`); `_reversa_sdd/addenda/009-rota-do-apple-touch-icon.md#regras-sob-vigilância`
   - Tipo: **preservada** (explicitada para esta feature)
2. **RN-02: é proibido declarar `<link rel="apple-touch-icon">` sem revogar a `RN-02` da feature 009 e
   o `W027`.** A proibição não é estética: a declaração move o documento, o hash da tela e o contrato
   de descoberta por convenção. 🟢
   - Origem no legado: `_reversa_sdd/addenda/009-rota-do-apple-touch-icon.md#regras-sob-vigilância`;
     `_reversa_forward/009-rota-do-apple-touch-icon/regression-watch.md` (`W027`)
   - Tipo: nova (proibitiva, derivada da decisão existente)
3. **RN-03: o estado `INCONCLUSIVO` não herda a cor do texto neutro.** Ele é o estado **inicial** e o
   caminho de falha do confronto — "nenhum estado afirmado por omissão" —, e por isso o cinza é
   semântico. O que não pode existir é a **dependência**: no tema escuro o texto neutro clareia para
   `#A99F88` e o selo não, de modo que um alias derrubaria o texto branco para **2,62:1**. 🟢
   - Origem no legado: `_reversa_sdd/state-machines.md#33-fatos-de-contrato`;
     `src/assets/app.css:33-35,161-166` (medido nesta sessão)
   - Tipo: nova (documenta a intenção que hoje é acidente de literal)
4. **RN-04: todo selo de estado mantém texto branco sobre cor cheia com, no mínimo, 4,5:1, nos dois
   temas.** O número medido vai para o comentário da folha, na mesma forma do caso histórico do
   laranja. 🟢
   - Origem no legado: `src/assets/app.css:161`; `tests/test_estilo_da_tela.py` (`TestOContrasteDosSelos`)
   - Tipo: **preservada** (o critério já existe; passa a exigir a medição escrita)
5. **RN-05: o `<h1>` "Analisador Genealógico" é texto sempre visível, e é ele que garante a
   identificação do produto quando a arte falha.** Esconder o `h1` com `visually-hidden` é proibido
   enquanto a arte do topo não trouxer o título desenhado. 🟢
   - Origem no legado: `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md`;
     `_reversa_sdd/recursos-da-tela/requirements.md#a-masthead`
   - Tipo: **preservada**
6. **RN-06: comentário e código não podem divergir sobre o que a arte do topo contém.** O comentário
   que afirma que o banner mostra o nome do produto é falso desde 2026-10-16 e precisa dizer o
   contrário: a arte atual não traz texto, e o `h1` é a identificação em português. 🟢
   - Origem no legado: `src/assets/app.css:353` × `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md`
   - Tipo: nova (regra de manutenção do arquivo)
7. **RN-07: mudança de apresentação não altera o texto que o operador lê.** Nenhuma mensagem de erro,
   rótulo de botão, título de seção ou aviso muda; as 8 telas literais mantêm diff textual zero. 🟢
   - Origem no legado: `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` (`RF-17`);
     `_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md` (`W005`)
   - Tipo: **preservada**

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Registrar a verificação do ícone da aba: um único `rel="icon"`, embutido como `data URI`, com o tipo e o tamanho declarados coerentes com o arquivo | Must | O `data URI` do HTML servido decodifica para um PNG de **128×128**; há exatamente **1** `rel="icon"` e **1** `data:image` no documento | 🟢 |
| RF-02 | Manter o ícone de atalho **não declarado** e sem caminho alternativo | Must | O HTML servido não contém `apple-touch-icon`; `GET /apple-touch-icon.png` responde `200` com `image/png`; `GET /favicon.ico` responde `404` | 🟢 |
| RF-03 | Registrar a decisão dos três pontos, com a premissa de cada um e a evidência que a sustenta | Must | Adendo da feature com "Vigência", uma decisão por ponto e as fontes citadas; as três decisões são rastreáveis a uma medição desta §2.1 | 🟢 |
| RF-04 | Dar ao estado `INCONCLUSIVO` declaração própria, não copiada do token do texto neutro | Must | O token que pinta o selo tem valor próprio e comentário que explica por que **não** segue o texto neutro; a cor efetiva do selo não muda | 🟢 |
| RF-05 | Medir e documentar o contraste dos quatro estados nos dois temas | Must | Comentário na folha com os quatro números inteiros e a razão de o selo não seguir o texto neutro; os quatro ≥ 4,5:1 | 🟢 |
| RF-06 | Corrigir o comentário da folha que afirma que o banner mostra o nome do produto | Must | O comentário passa a declarar que a arte atual não traz texto e que o `h1` é a identificação em português | 🟢 |
| RF-07 | Preservar `aria-pressed`, os `visually-hidden` existentes e o `focus-visible` | Must | As três marcas continuam presentes e inalteradas; os testes de tema e de contraste seguem verdes | 🟢 |
| RF-08 | Preservar o texto que o operador lê nas 8 telas literais | Must | Nenhuma mensagem, rótulo ou aviso muda; os goldens de `_reversa_sdd/screens/golden/` não são editados | 🟢 |
| RF-09 | Não remover nem desabilitar teste, e entregar a suíte verde | Must | **1.048** passam, **9** pulados, **0** falhas; nenhum teste apagado ou desabilitado nesta feature | 🟢 |
| RF-10 | Se o template for tocado, mover o hash da tela na mesma entrega | Should | `SHA_DA_TELA` novo, calculado do HTML servido, com a diferença explicada no adendo e no comentário do próprio hash | 🟢 |
| RF-11 | Remover da folha os quatro tokens sem uso (`--inc`, `--ok`, `--poss`, `--conf`) | Must | Nenhuma das quatro definições resta na folha; nenhum seletor ou template as referencia; as cores efetivas dos quatro selos continuam as mesmas | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Acessibilidade | Os quatro selos de estado mantêm **≥ 4,5:1** entre texto e fundo nos temas claro e escuro (WCAG 2.1, nível AA, texto normal) | Medido: 6,39, 7,13, 6,69 e 6,11:1 com branco; o caso do laranja (2,57:1) é o precedente que a regra existe para não repetir | 🟢 |
| Acessibilidade | `visually-hidden` só é usado onde já era usado; o `h1` não o recebe | `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md#regras-sob-vigilância` | 🟢 |
| Acessibilidade | O foco visível dos elementos interativos não muda | `src/assets/app.css:67` é a regra única de `:focus-visible`; a feature não a toca | 🟢 |
| Regressão | A suíte continua verde e nenhum teste é removido ou desabilitado | Linha de base de **1.048 passam / 9 pulados**; princípio III | 🟢 |
| Regressão | Um ajuste só de folha não move o `sha256` de `GET /` | A folha sai por rota própria (`GET /app.css`) e não é embutida no documento | 🟢 |
| Isolamento | Nenhum arquivo de `application/`, `ports/`, `core/`, `parsers/` ou `reporting/` é tocado | A mudança é de apresentação; princípio II e coesão da feature | 🟢 |
| Manutenibilidade | Cada cor de estado tem **uma** declaração e o comentário diz por que ela é aquela | O mesmo literal aparece em **três** declarações (`--muted`, `--inc` e `--st-inconclusivo`), e uma delas (`--inc`) nunca é usada | 🟢 |
| Manutenibilidade | Nenhum token fica sem uso: os quatro sem uso (`--inc`, `--ok`, `--poss`, `--conf`) são removidos | Medido: zero referências na folha e no template | 🟢 |
| Compatibilidade | O documento servido continua o mesmo quando a mudança é só de folha | Sem atributo novo no HTML, sem requisição nova, sem dependência nova | 🟢 |
| Desempenho | A folha não cresce de forma perceptível | O ajuste é de comentário e de uma declaração de token; não há nova requisição | 🟡 |
| Privacidade | Nenhum dado de pessoa, xref ou cM entra em artefato da feature | Princípio I; a feature não lê dado de análise | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: ícone da aba presente e coerente
  Dado que a tela de entrada responde 200
  Quando o HTML servido é inspecionado
  Então existe exatamente um link rel="icon" com data URI
  E o PNG embutido tem 128 por 128 pixels
  E o atributo sizes declara 128x128

Cenário: ícone de atalho descoberto por convenção, sem declaração
  Dado que a tela de entrada responde 200
  Quando o HTML servido é procurado pela cadeia "apple-touch-icon"
  Então nenhuma ocorrência é encontrada
  E GET /apple-touch-icon.png responde 200 com image/png
  E GET /favicon.ico responde 404

Cenário: a decisão está registrada com a evidência
  Dado o adendo da feature
  Quando as três decisões são lidas
  Então cada uma cita a medição que a sustenta
  E cada uma declara o custo da alternativa que não foi escolhida

Cenário: estado Inconclusivo legível no tema claro
  Dado o tema claro
  Quando um selo "Inconclusivo" é renderizado
  Então o fundo vem do token próprio do estado
  E o texto branco sobre esse fundo tem pelo menos 4,5:1
  E os quatro números medidos estão escritos no comentário da folha

Cenário: tema escuro recusa o alias do texto neutro
  Dado o tema escuro
  Quando o fundo do selo "Inconclusivo" é trocado por um alias do texto neutro
  Então o contraste do texto branco cai para 2,62:1
  E o teste de contraste reprova a troca

Cenário: tokens mortos removidos
  Dado o arquivo src/assets/app.css
  Quando a folha é procurada por --inc, --ok, --poss e --conf
  Então nenhuma das quatro definições resta
  E as cores efetivas dos quatro selos continuam as mesmas

Cenário: o comentário da folha descreve a arte atual
  Dado o arquivo src/assets/app.css
  Quando o comentário do topo da tela é lido
  Então ele declara que a arte atual não traz o nome do produto
  E declara que o h1 é a identificação em português

Cenário: marcas de acessibilidade preservadas
  Dado o documento servido
  Quando o botão de tema e os textos auxiliares são inspecionados
  Então aria-pressed continua no botão de tema
  E os visually-hidden existentes continuam onde estavam
  E a regra de focus-visible continua na folha

Cenário: o h1 permanece visível com a arte presente
  Dado que a arte do topo responde 200
  Quando a tela de entrada é renderizada
  Então o h1 contém "Analisador Genealógico" como texto
  E a classe do h1 não contém visually-hidden

Cenário: o h1 é o fallback quando a arte não carrega
  Dado que a arte do topo responde 404
  Quando a tela de entrada é renderizada
  Então a tela responde 200
  E o h1 continua visível e com o texto do produto

Cenário: nenhum texto que o operador lê mudou
  Dado qualquer uma das 8 telas literais
  Quando o texto é comparado com o golden correspondente
  Então o diff textual é zero
  E nenhuma mensagem de erro ou rótulo de botão foi alterado

Cenário: a suíte continua verde e sem remoção
  Dado o estado final da feature
  Quando a suíte completa é executada
  Então há zero falhas
  E o número de testes aprovados não é menor que 1.048
  E nenhum teste foi removido ou desabilitado

Cenário: mudança só de folha não move o hash da tela
  Dado que apenas src/assets/app.css foi alterado
  Quando o sha256 do HTML de GET / é medido
  Então o valor é o mesmo de antes da feature
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É a verificação pedida; o resultado pode ser "nada a corrigir", e isso precisa ficar registrado |
| RF-02 | Must | A ausência é decisão vigente e presa por teste; desfazê-la sem revogação quebra o contrato |
| RF-03 | Must | Sem a decisão escrita, o próximo revisor refaz a mesma investigação e chega à mesma dúvida |
| RF-04 | Must | É o defeito de cor real que o ponto 2 levanta; o RF-11 fecha a higiene dele |
| RF-05 | Must | Contraste sem medição escrita vira opinião; o arquivo já adotou a prática |
| RF-06 | Must | O comentário falso é a origem da premissa vencida do próprio pedido |
| RF-07 | Must | Acessibilidade é restrição dura do pedido |
| RF-08 | Must | `RF-17` da 006 é contrato de tela |
| RF-09 | Must | Princípio III e restrição explícita do pedido |
| RF-10 | Should | Só se aplica se o template for tocado; no caminho recomendado, o hash não se move |
| RF-11 | Must | Fecha a ambiguidade do ponto 2 na origem, sem mudar nenhuma cor efetiva |
| RNF de acessibilidade | Must | WCAG 2.1 AA nos dois temas é restrição explícita do pedido |
| RNF de isolamento | Must | Coesão e baixo acoplamento são princípio do pedido |

## 9. Esclarecimentos

### Sessão 2026-10-17

- **Q:** O ícone de atalho continua sem declaração no `<head>`?

  **R:** Continua (opção 1a). Nada muda no template: a `RN-02` da feature 009 e o `W027` permanecem,
  e o `SHA_DA_TELA` não se move. A alternativa — declarar `<link rel="apple-touch-icon">` — exigiria
  revogar a regra, reescrever `test_a_tela_nao_declara_o_icone_de_atalho` e mover o hash.

- **Q:** O estado `INCONCLUSIVO` mantém o cinza ou ganha cor própria?

  **R:** Mantém o cinza (opção 2a), com valor próprio, comentário com os quatro números medidos e sem
  dependência de `--muted`. A alternativa `#5B6B7A` (5,48:1) foi recusada por introduzir um matiz fora
  da paleta tirada da arte.

- **Q:** O `<h1>` "Analisador Genealógico" permanece sempre visível?

  **R:** Permanece (opção 3a), e o comentário falso da folha é corrigido. Esconder o `h1` exigiria
  reverter o adendo `023`, trocar a arte por uma que traga o título e prover fallback de imagem
  quebrada, que o CSS não observa.

- **Q:** Os quatro tokens mortos (`--inc`, `--ok`, `--poss`, `--conf`) saem da folha?

  **R:** Saem os quatro (opção 4a). Nenhum é usado, e o selo já usa a família `--st-*`.

## 10. Lacunas

Nenhuma dúvida aberta nesta data. As decisões dos três pontos — e a remoção dos quatro tokens sem uso
— foram tomadas na sessão de esclarecimento de 2026-10-17 (§9), e não há ponto sem resposta.

- 🟡 **Resíduo declarado:** o comentário do ícone da aba, no template, cita `.reversa/_favicon.py`,
  que não existe mais — o arquivo foi removido no commit `6b80641`. Corrigir o ponteiro exige tocar o
  template e mover o `SHA_DA_TELA`; fica fora desta feature, que decidiu não tocar o documento, e
  volta na próxima mudança de tela declarada.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-17 | Sessão de esclarecimento: ícone sem declaração, cinza próprio do `INCONCLUSIVO`, `h1` visível e remoção dos quatro tokens mortos | reversa |
