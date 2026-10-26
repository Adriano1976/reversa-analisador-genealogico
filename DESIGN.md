---
name: Analisador Genealógico
description: Um arquivo paroquial digital para cruzar árvore GEDCOM e matches de DNA sem confundir evidência genética com parentesco documental.
colors:
  parchment: "#F5F1E6"
  parchment-dark: "#16140F"
  surface: "#FFFFFF"
  surface-dark: "#1F1C14"
  surface-2: "#F8F4E9"
  surface-2-dark: "#26221A"
  ink: "#2A2418"
  ink-dark: "#EDE7D6"
  head: "#4A3B1A"
  head-dark: "#E8D9B0"
  muted: "#6A6150"
  muted-dark: "#A99F88"
  line: "#DDD4BF"
  line-dark: "#3A3426"
  primary: "#3F6B2E"
  primary-dark: "#8DBB6E"
  primary-hover: "#335724"
  primary-hover-dark: "#A5CC8B"
  on-primary: "#FFFFFF"
  on-primary-dark: "#16140F"
  danger: "#A8321F"
  danger-dark: "#EE9A88"
  on-danger: "#FFFFFF"
  on-danger-dark: "#16140F"
  focus: "#8A5A2B"
  focus-dark: "#D9A85E"
  warning-surface: "#FBF3DC"
  warning-surface-dark: "#2B2512"
  warning-line: "#A8741F"
  warning-line-dark: "#D9A85E"
  warning-solid: "#D9A85E"
  on-warning-solid: "#2A2418"
  success-surface: "#EDF4E6"
  success-surface-dark: "#1E2A17"
  success-line: "#3F6B2E"
  success-line-dark: "#8DBB6E"
  danger-surface: "#FBEDEA"
  danger-surface-dark: "#2E1B18"
  danger-line: "#A8321F"
  danger-line-dark: "#EE9A88"
  state-compatible: "#2F6B3A"
  state-possible: "#7A4F00"
  state-conflicting: "#A8321F"
  state-inconclusive: "#6A6150"
  validation-valid: "#2F6B3A"
  validation-conflict: "#A8321F"
  on-solid: "#FFFFFF"
typography:
  display:
    fontFamily: "Cormorant Garamond, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(2.4rem, 4.1vw, 3.8rem)"
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: "normal"
  headline:
    fontFamily: "Cormorant Garamond, Georgia, 'Times New Roman', serif"
    fontSize: "clamp(1.7rem, 2.6vw, 2.1rem)"
    fontWeight: 700
    lineHeight: 1.15
  title:
    fontFamily: "Cormorant Garamond, Georgia, 'Times New Roman', serif"
    fontSize: "1.4rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Manrope, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Manrope, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "0.82rem"
    fontWeight: 800
    lineHeight: 1.4
  overline:
    fontFamily: "Manrope, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "0.75rem"
    fontWeight: 800
    lineHeight: 1.35
    letterSpacing: "0.14em"
  badge:
    fontFamily: "Manrope, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.01em"
    fontFeature: "lnum tnum"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
  3xl: "44px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: "6px 12px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.danger}"
    rounded: "{rounded.md}"
    padding: "6px 12px"
  input-text:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
  card-result:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "16px"
  nav-rail-active:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.head}"
    rounded: "{rounded.md}"
    padding: "10px 11px"
  badge-verdict:
    backgroundColor: "{colors.state-compatible}"
    textColor: "{colors.on-solid}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
  badge-metadata:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.head}"
    rounded: "{rounded.pill}"
    padding: "6px 9px"
---

# Design System: Analisador Genealógico

## Overview

**Creative North Star: "O Arquivo Paroquial"**

O sistema se comporta como um livro de registro sobre a mesa: papel creme, tinta marrom, uma única cor de selo para o que está vivo. Não é um painel de acompanhamento; é um arquivo que se consulta. Cada conexão é uma folha, com nome, data, distância e procedência, e a tela nunca levanta a voz além do que o registro sustenta.

A sobriedade é funcional, não estética. O valor do produto está na **negativa justificada**: dizer que um match não se sustenta, e por quê. Por isso o desenho favorece o que se audita — data, fonte, distância geracional, motivo do descarte — e trata cor como veredito, nunca como decoração.

O mundo é quase plano: superfícies claras sobre pergaminho, separadas por linha de 1 px e mudança de tom, com sombra só onde há estado. Verde, âmbar e terracota significam ação, aviso e perigo, e essa gramática é a mesma nos dois temas.

**Key Characteristics:**
- Pergaminho e tinta, não branco e cinza: nenhuma superfície é branco puro sobre a página.
- Uma cor de ação (verde-folha); vermelho só para perigo, âmbar só para aviso.
- Selo preenchido = veredito; selo de contorno = metadado.
- Serifa editorial nos títulos; sans em dado, rótulo e controle.
- Sombra quase plana; profundidade vem de borda, degradê e tom.
- Número é dado: sempre figuras de caixa alta e tabulares.

## Colors

Paleta quente de arquivo: neutros de papel e tinta, um verde de folha para ação e dois tons de consequência, âmbar e terracota.

### Primary

- **Verde-folha** (`#3F6B2E` no claro, `#8DBB6E` no escuro): a única cor de ação. Botão principal, item ativo da trilha, link, número da fase ativa. Não é cor de status, não é cor de destaque decorativo.

### Secondary

- **Âmbar de aviso** (`#A8741F` como linha, `#FBF3DC` como superfície, `#D9A85E` cheio): ressalvas que não são veredito — janela de vida suspeita, identidade a confirmar, profundidade divergente — e os painéis de escopo-arquivo (Observações do arquivo, Cobertura do arquivo), que reúnem ressalvas do arquivo inteiro. No escuro a linha clareia para `#D9A85E` e a superfície fecha em `#2B2512`.

### Tertiary

- **Terracota de perigo** (`#A8321F` no claro, `#EE9A88` no escuro): perigo real e contradição demonstrável. Por padrão é contorno; preenchido só dentro de selo de veredito.

### Neutral

- **Pergaminho** (`#F5F1E6` / `#16140F`): fundo da página nos dois temas. É o branco do sistema.
- **Superfície** (`#FFFFFF` / `#1F1C14`): cartão principal e cartão de resultado.
- **Superfície 2** (`#F8F4E9` / `#26221A`): cabeçalho de bloco, caixa de status, trilha ativa, selo de metadado.
- **Tinta** (`#2A2418` / `#EDE7D6`): texto corrente.
- **Tronco** (`#4A3B1A` / `#E8D9B0`): títulos e números de contador.
- **Apoio** (`#6A6150` / `#A99F88`): texto secundário, rótulo, resumo.
- **Linha** (`#DDD4BF` / `#3A3426`): toda borda, divisor e contorno de controle.
- **Estados de confronto**: quatro cores fixas nos dois temas (`#2F6B3A`, `#7A4F00`, `#A8321F`, `#6A6150`), sempre com texto branco. Não são redefinidas no escuro de propósito.

### Named Rules

**The One Voice Rule.** O verde é ação, nunca enfeite. Se duas áreas verdes competem na mesma dobra, uma delas está errada.

**The Filled-Means-Verdict Rule.** Selo preenchido carrega veredito; selo de contorno carrega metadado. Um cM, uma contagem ou um nome de arquivo nunca recebem preenchimento.

**The Warm Neutral Rule.** Nenhum cinza frio entra na paleta. `#6C757D` do Bootstrap é proibido; os utilitários do framework são remapeados para os tokens da casa.

## Typography

**Display Font:** Cormorant Garamond (fallback Georgia, 'Times New Roman', serif)
**Body Font:** Manrope (fallback system-ui, 'Segoe UI', sans-serif)

**Character:** A serifa é a caligrafia do livro de registro — nomes, títulos, números de seção. A sans é a máquina de escrever do escrivão — datas, cM, rótulos, controles. Duas vozes, divisão estrita.

### Hierarchy

- **Display** (700, `clamp(2.4rem, 4.1vw, 3.8rem)`, 1.04): título da tela, uma linha só em todas as larguras medidas.
- **Headline** (700, `clamp(1.7rem, 2.6vw, 2.1rem)`, 1.15): título de seção de resultado e de fase.
- **Title** (700, 1.4rem, 1.2, tracking -0.01em): nome da conexão no cabeçalho do cartão.
- **Body** (400, 1rem, 1.6): texto corrente, a frase de contagem e a legenda dos selos. Na abertura dos resultados as duas frases ocupam a largura inteira do conteúdo — sem medida curta e sem corpo reduzido, para a quebra chegar à borda da caixa.
- **Label** (800, 0.82rem): rótulo de campo.
- **Overline** (800, 0.75rem, tracking 0.14em, caixa alta): rótulo de status, título de legenda, "evidências por laboratório".
- **Badge** (600, 0.75rem, 1, tracking 0.01em): selos e contagens dentro de selo.

### Named Rules

**The Lining Numbers Rule.** Todo numeral que é dado usa figuras de caixa alta e tabulares. O Cormorant cai em figuras antigas por padrão: sem `lining-nums`, o contador de árvores lê "I" e a idade lê "III" — por isso contador, cobertura e selos forçam a figura moderna.

**The Two Faces Rule.** A serifa não carrega número, unidade nem rótulo de controle; a sans não carrega título de página.

## Layout

Uma coluna centrada dentro de um cartão único, que é a página inteira. No desktop o cartão ocupa ~83% do contêiner (cerca de 1.070 px em 1.440), com 16 px de respiro interno e 24 px entre blocos; o espaçamento segue base de 4 px.

O topo é uma masthead de duas colunas na proporção 1,3 / 0,7 — texto à esquerda, arte à direita, com a arte limitada a 280 px — e vira uma coluna abaixo de 768 px, com a arte em primeiro lugar no documento.

As fases são uma grade de duas colunas: trilha fixa de 200 a 240 px à esquerda e painel à direita. Abaixo de 992 px a trilha sai de cena e as abas assumem a navegação; nunca as duas ao mesmo tempo. Os resultados ocupam a largura inteira do cartão, abaixo da grade, alinhados à esquerda. A seção abre com uma linha de 1 px na largura do conteúdo — o mesmo divisor que separa a masthead das fases —, e tudo dentro dela começa na mesma vertical: título, contagem, legenda dos selos, botões de expandir e paginação.

## Elevation & Depth

Quase plano. Profundidade é declarada por borda de 1 px, mudança de tom entre `surface` e `surface-2` e pelo degradê do cabeçalho do cartão. Sombra é resposta a estado — item ativo, lista flutuante, controle fixo — e nunca o único sinal de hierarquia. No tema escuro as sombras são pretas e mais opacas, porque o marrom do pergaminho desaparece sobre o fundo quase preto.

### Shadow Vocabulary

- **Repouso baixo** (`0 1px 2px rgba(0,0,0,.06)`): chip elevado, botão "Voltar", botão de tema.
- **Estado ativo** (`0 4px 14px rgba(69,52,29,.10)`): item ativo da trilha, com a barra interna verde.
- **Cartão** (`0 8px 24px rgba(69,52,29,.08)`): cartão de resultado em repouso, quase invisível sobre o pergaminho.
- **Flutuante alto** (`0 10px 24px rgba(69,52,29,.18)`): lista de nomes do combobox.

### Named Rules

**The Border-First Rule.** Para separar superfícies, mude primeiro a borda e o tom. A sombra vem depois e nunca sozinha.

## Shapes

Cantos suaves com três degraus e uma pílula: **8 px** para chip e controle pequeno, **12 px** para bloco, campo e botão, **16 px** para cartão, e **999 px** para pílula. O raio de fora é sempre maior que o de dentro — cartão 16, bloco 12, chip 8; um filho mais redondo que o pai é erro de sistema.

Bordas são sempre de 1 px em `line`; a exceção é a barra de 5 px que marca a borda esquerda do cartão de resultado, um degradê de `muted` a `head` que funciona como lombada. Formas fechadas são rectilíneas: nenhum recorte circular, nenhuma máscara geométrica.

## Components

### Buttons

- **Shape:** 12 px de raio, peso 700, altura de 36 px com padding de 6 px por 12 px; a ação principal ganha `min-width` de 12 rem e 24 px laterais a partir de 576 px.
- **Primary:** fundo `primary`, texto `on-primary`, borda na mesma cor do fundo. É o único botão que usa verde como superfície.
- **Hover / Focus:** o verde escurece para `primary-hover`; o foco é anel de 3 px em `focus`, com 2 px de afastamento, em todos os controles.
- **Danger:** fundo transparente, borda e texto em `danger`; no hover o fundo enche e o texto vira `on-danger`. É ação destrutiva, não ação secundária.

### Chips

- **Verdict:** preenchido com a cor do estado, texto branco, peso 600, 8 px de raio. Quatro estados fixos nos dois temas.
- **Metadata:** contorno de 1 px em `line`, fundo `surface-2`, texto `head`, forma de pílula. É onde entram cM, idade, "não atribuível ao doador".

### Cards / Containers

- **Corner Style:** 16 px, com 12 px nos blocos internos.
- **Background:** degradê vertical de `surface` para `surface-2`; o cabeçalho é transparente e a página por trás é `parchment`.
- **Shadow Strategy:** ver Elevation — o cartão de resultado usa a sombra de cartão, os demais blocos nenhuma.
- **Border:** 1 px em `line`, mais a lombada de 5 px à esquerda no cartão de resultado.
- **Internal Padding:** 16 px no corpo; 14 px a 21 px no cabeçalho, com 5 px extras à esquerda para compensar a lombada.
- **Painéis de escopo-arquivo:** Observações do arquivo e Cobertura do arquivo usam a moldura de aviso inteira (`warning-surface` com borda `warning-line`) porque tratam de limites do arquivo, não de um resultado. Dentro deles, as ressalvas viram itens com barra à esquerda; os números da cobertura ficam em superfície branca, sem cor de estado.

### Inputs / Fields

- **Style:** fundo `surface`, borda 1 px em `line`, 12 px de raio, padding de 10 px por 14 px.
- **Focus:** borda em `primary` e halo de 25% do verde, além do anel de foco de teclado.
- **File input:** o botão nativo é substituído por superfície `surface-2` com divisor à direita, na mesma linguagem dos botões secundários.

### Navigation

- **Trilha lateral:** itens de 12 px de raio, número em círculo, título e resumo em duas linhas. O ativo tem fundo `surface`, borda `line`, barra interna de 4 px em `primary` e sombra de estado ativo.
- **Abas:** sublinhado de 3 px na ativa, reservadas para telas abaixo de 992 px, quando a trilha não cabe. As duas nunca aparecem juntas.
- **Foco:** anel de 3 px em `focus`, com 2 px de afastamento, inclusive nos cartões recolhíveis.

### Callouts

Blocos de aviso usam fundo `warning-surface`, borda de 1 px em `warning-line` e uma barra lateral de 3 a 5 px. O veredito do doador e o alerta de janela de vida usam `danger` na barra. A barra lateral grossa é assinatura herdada deste sistema: fica confinada aos avisos e aos painéis de escopo-arquivo, e em Don'ts está registrada como dívida que não deve virar dispositivo genérico.

## Do's and Don'ts

### Do:

- **Do** usar o verde só em ação: CTA, item ativo, link. Se não é clicável, não é verde.
- **Do** manter veredito preenchido e metadado em contorno.
- **Do** forçar `lining-nums` e `tabular-nums` em qualquer número que o operador vá comparar.
- **Do** respeitar a escada de raio 16 / 12 / 8 / pílula, com o filho sempre menos redondo que o pai.
- **Do** separar superfícies com borda e tom antes de recorrer a sombra.
- **Do** medir contraste nos dois temas e rodar `tests/test_estilo_da_tela.py` depois de mexer em cor.

### Don't:

- **Don't** introduzir cinza frio, azul de framework ou um segundo acento.
- **Don't** usar a serifa para número, unidade ou rótulo de controle.
- **Don't** preencher selo de metadado nem contornar selo de veredito.
- **Don't** acrescentar olho ou kicker acima de título: o sobretítulo da masthead é dívida herdada e não deve ser replicado.
- **Don't** criar ícones novos em glifo Unicode: o botão de tema e as marcas da tabela são dívida herdada.
- **Don't** empilhar superfícies com sombra; o cartão em repouso é plano.
- **Don't** escrever uma segunda navegação para os mesmos destinos na mesma largura.
- **Don't** usar a barra colorida grossa fora dos avisos e dos painéis de escopo-arquivo (Observações e Cobertura); ela é dívida herdada, não um dispositivo de layout.
