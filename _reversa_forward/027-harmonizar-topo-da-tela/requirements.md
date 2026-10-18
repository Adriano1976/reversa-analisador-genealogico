# Requirements: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O operador comparou a tela que usa e apontou que os cartões de resultado parecem mais bem desenhados
do que o topo. O topo acumula desencontros específicos: o alerta de retorno usa a cor padrão do
framework de CSS, **fora da paleta**, com borda quase invisível; a ação principal é uma barra verde de
largura total, mais pesada que qualquer elemento do resultado; a escala do topo salta do `h1` para o
corpo sem degrau intermediário; e o **comentário do template** ainda descreve o texto de introdução
como alinhado à esquerda, quando a decisão vigente (`RN-24`) é centralizado e em coluna estreita.
Esta feature harmoniza o topo com a gramática dos cartões — cor da paleta, escala compacta, ação leve
e comentário correto — sem mudar uma palavra da tela e **sem reabrir a `RN-24`**.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/recursos-da-tela/requirements.md#a-masthead` | A masthead segue a ordem imagem → subtítulo → título em texto → apresentação (`BR-E-29`); o título sobrevive à arte ausente por construção | 🟢 |
| `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md#3-regras-novas-que-a-feature-cria` | `RN-23`: o topo é uma masthead com arte a `w-50`, subtítulo, título em texto e apresentação. `RN-24`: o texto de apresentação fica **centralizado** e numa coluna mais estreita | 🟢 |
| `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md#regras-alteradas` | A revisão de design que criou a folha servida por rota, o controle de tema e o índice; a emenda do título foi depois revertida | 🟢 |
| `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` | A arte atual não traz o título e o `<h1>` voltou a ser sempre visível | 🟢 |
| `_reversa_sdd/addenda/026-polimento-visual-da-tela.md#regras-sob-vigilância` | Os quatro tokens `--st-*` são a única declaração das cores de estado; o cinza do `INCONCLUSIVO` é próprio e mede 6,11:1 | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` | `RF-17`: as 8 telas literais mantêm diff textual zero | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md` | `W005`: as mensagens da camada de rota e as congeladas continuam ao caractere | 🟢 |
| `_reversa_sdd/architecture.md#3` | A folha de estilo e o template fazem parte da borda de apresentação; nenhuma regra de domínio vive neles | 🟢 |
| `.reversa/principles.md#ii` | Comportamento observável é preservado; mudança de comportamento é feature | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |

### 2.1 O que foi medido nesta sessão (2026-10-17)

| Medição | Resultado |
|---------|-----------|
| Bloco de introdução | Os dois parágrafos estão dentro do `div.text-center` da masthead (`index.html:190-228`) **por decisão**: a `RN-24` pede texto centralizado e em coluna mais estreita, e `tests/test_banner_do_topo.py:270-298` proíbe `text-start` e exige `row justify-content-center` + `col-lg-*`. O comentário do template (`:185-187`) ficou para trás e ainda diz "alinhados a esquerda" — **o defeito é o comentário, não o layout** |
| Alerta de retorno | `alert alert-success`/`alert-danger` (`index.html:231`) **sem regra na folha**: herda a cor padrão do framework. Texto `#0a3622` sobre `#d1e7dd` = **10,35:1** (legível); a borda `#badbcc` sobre o mesmo fundo = **1,15:1** (imperceptível — o bloco lê como chapa lisa) |
| Ação principal | O botão fica em `div.d-grid`, ocupando a largura inteira do cartão; branco sobre `--primary` (`#3F6B2E`) = **6,26:1** |
| Selo de cM | `badge bg-secondary` (`index.html:541`), sem regra na folha: `#6c757d` com branco = **4,69:1** (passa, no limite) |
| Escala do topo | `h1` em `clamp(1.9rem, 4vw, 2.5rem)`; corpo 1rem; título do cartão de resultado 1.2rem; metadados 0.85/0.8rem. Não há degrau entre 2,5rem e 1rem |
| Cartões de resultado | Cabeçalho em `--surface-2`, borda `--line`, padding compacto, título em serif 1.2rem, metadados em `--muted` — a linguagem que o operador apontou como melhor |
| Superfícies do topo | Card branco + alerta colorido + linha da árvore + abas + card do formulário + card creme de observações: seis tratamentos empilhados |
| Abas | O markup das abas está **duplicado** nos dois ramos da tela (`index.html:244-251` e `:333-340`), de propósito, para a tela ser a mesma antes e depois de escolher a árvore |
| Cobertura da tela | `SHA_DA_TELA = c4a34f7b…`, 30.781 bytes |
| Linha de base da suíte | 1.048 passam, 9 pulados, 0 falham |

### 2.2 O que **não** é defeito

- O texto de introdução ser **centralizado e estreito** é a `RN-24`, pedida pelo operador em
  2026-10-10 (`T045`) e presa por teste. Esta feature **não reabre** essa decisão.
- O título da seção de resultados ser centralizado (`h2.text-center`, `index.html:484`) está correto:
  é um título curto, e os cartões abaixo é que carregam o alinhamento à esquerda.
- O contraste do alerta atual **passa** em WCAG AA (10,35:1). O defeito é de **identidade visual** —
  cor fora da paleta e borda invisível —, não de legibilidade.
- O selo de cM em `bg-secondary` passa (4,69:1) e faz parte do rodapé que o operador elogiou; a
  decisão de escopo de 2026-10-17 foi **não** tocá-lo (ver `RF-06` e §9).

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (persona única, sem login) | Ler a tela sem sentir que o topo é de outro produto | Abre a tela, entende o que fazer e compara o resultado com a primeira dobra |
| Quem mantém a interface | Alterar o topo sem tocar no rodapé, nos textos nem na `RN-24` | Ajusta uma regra e confere que as 8 telas literais e o hash foram tratados |
| Revisor de acessibilidade | Confirmar que a harmonização não apagou foco, rótulo nem contraste | Roda a suíte e mede o alerta nos dois temas |

## 4. Regras de negócio novas ou alteradas

1. **RN-01: o topo e o resultado passam a compartilhar a mesma gramática visual.** Cor sempre da
   paleta, escala tipográfica compacta e ação principal sem mais peso que o conteúdo. A introdução
   mantém a `RN-24` (centralizada e em coluna estreita). 🟢
   - Origem no legado: `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md`; cartões de resultado
     descritos em `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md`
   - Tipo: nova
2. **RN-02: nenhum texto que o operador lê muda.** Alinhamento, cor, tamanho e espaçamento podem
   mudar; rótulo, mensagem, título e texto de apresentação não. 🟢
   - Origem no legado: `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` (`RF-17`) e
     `regression-watch.md` (`W005`)
   - Tipo: **preservada**
3. **RN-03: cor nova só entra pela paleta, e com contraste medido.** Alerta e demais superfícies
   usam tokens existentes ou tokens novos declarados na folha; todo par texto/fundo fica ≥ 4,5:1 nos
   dois temas, com o número registrado no comentário. 🟢
   - Origem no legado: `_reversa_sdd/addenda/026-polimento-visual-da-tela.md`; caso histórico do
     laranja em `src/assets/app.css:162`
   - Tipo: **preservada** (explicitada para esta feature)
4. **RN-04: a masthead mantém a ordem e o `<h1>` continua sempre visível.** Arte → subtítulo → título
   em texto → apresentação (`BR-E-29`); o título não recebe `visually-hidden`. 🟢
   - Origem no legado: `_reversa_sdd/recursos-da-tela/requirements.md#a-masthead`;
     `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md`
   - Tipo: **preservada**
5. **RN-05: as marcas de acessibilidade não mudam.** `aria-pressed` do botão de tema, os
   `visually-hidden` existentes e a regra de `focus-visible` continuam como estão. 🟢
   - Origem no legado: `tests/test_estilo_da_tela.py` e `tests/test_banner_do_topo.py`
   - Tipo: **preservada**
6. **RN-06: toda mudança de tela é declarada.** Alterar o template move o `SHA_DA_TELA`; a entrega
   atualiza o valor na mesma rodada e declara a mudança no adendo da feature. 🟢
   - Origem no legado: `tests/test_icone_de_atalho.py` (comentário do `SHA_DA_TELA`);
     `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md`
   - Tipo: **preservada**
7. **RN-07: ação principal ocupa a largura toda no telefone e a largura natural no desktop.** O
   `d-grid` atual é correto no telefone; no desktop ele transforma a ação em barra. A quebra é o
   ponto de 575,98 px já usado na folha. 🟢
   - Origem no legado: `src/assets/app.css:345-347` (media query existente)
   - Tipo: nova
8. **RN-08: o rodapé é o alvo da comparação, não a superfície da mudança.** Nenhuma cor, selo ou
   espaçamento dos cartões de resultado muda — inclusive o selo de cM em `bg-secondary`. 🟢
   - Origem no legado: decisão 3a da sessão de esclarecimento de 2026-10-17 (§9)
   - Tipo: nova (restrição de escopo)
9. **RN-09: a introdução mantém a `RN-24`.** Texto centralizado, `col-lg-*` dentro de
   `row justify-content-center`, sem `text-start`; o comentário do template passa a descrever esse
   arranjo. 🟢
   - Origem no legado: `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md#3-regras-novas-que-a-feature-cria`
     (`RN-24`); `tests/test_banner_do_topo.py:270-298`
   - Tipo: **preservada** (explicitada para esta feature)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Corrigir o comentário do template que ainda descreve a introdução como alinhada à esquerda | Must | O comentário passa a descrever o arranjo da `RN-24` (centralizado, em coluna estreita); a estrutura `row justify-content-center` + `col-lg-*` permanece; `text-start` continua ausente | 🟢 |
| RF-02 | Trazer os alertas de retorno para a paleta, com borda visível, forma compacta e o botão de fechar preservado | Must | `.alert-success` usa fundo creme/verde suave e texto `--ink` ou `--primary`, com borda de contraste ≥ 3:1 contra o fundo; `.alert-danger` segue a mesma forma com `--danger`; o `btn-close` continua presente e estilizado na paleta; os dois medidos nos temas claro e escuro | 🟢 |
| RF-03 | Aliviar a ação principal: largura natural no desktop e largura total no telefone | Must | Acima de 576 px o botão não ocupa a largura do cartão; abaixo de 576 px ele continua de largura total; o raio e a altura conversam com as pílulas do resultado | 🟢 |
| RF-04 | Compactar a escala do topo | Should | `h1` com máximo de **2,2 rem** (era 2,5 rem); arte do topo com máximo de **280 px** (era 320 px); espaçamentos verticais do topo reduzidos em um degrau | 🟢 |
| RF-05 | Unificar rótulos e espaçamentos de seção entre o formulário e as observações | Should | Rótulos de seção usam o mesmo tratamento; a distância entre os blocos do topo segue o mesmo degrau; os cartões de resultado não mudam (`RN-08`) | 🟡 |
| RF-06 | Preservar o selo de cM e as cores dos cartões de resultado | Must | Nenhuma regra de `.badge.bg-secondary` nem das cores dos cartões muda; o rodapé continua como está | 🟢 |
| RF-07 | Preservar textos, `aria-pressed`, `visually-hidden` e `focus-visible` | Must | Nenhum literal muda; as três marcas continuam presentes e os testes de tema/contraste passam | 🟢 |
| RF-08 | Declarar a mudança e verificar se o HTML servido mudou | Must | O `sha256` de `GET /` é medido antes e depois; se mudar, o `SHA_DA_TELA` é atualizado com bloco datado; se não mudar, a razão (comentário Jinja removido do HTML) fica registrada no adendo | 🟢 |
| RF-09 | Não remover teste e entregar a suíte verde | Must | 1.048 passam, 9 pulados, 0 falhas; nenhum teste apagado ou desabilitado; o teste da `RN-24` continua verde | 🟢 |
| RF-10 | Medir e documentar o contraste do alerta novo nos dois temas | Must | Comentário na folha com os pares medidos; os quatro números (alerta claro/escuro, sucesso/perigo) ≥ 4,5:1 para texto | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Acessibilidade | Todo texto novo ou recolorido mantém ≥ 4,5:1 nos dois temas; elementos não textuais ≥ 3:1 | WCAG 2.1 AA; o alerta atual passa (10,35:1) mas a borda é 1,15:1 | 🟢 |
| Acessibilidade | O foco visível e as marcas ARIA não mudam | `src/assets/app.css:67`; `tests/test_estilo_da_tela.py` | 🟢 |
| Consistência | O topo usa a mesma escala e os mesmos tokens dos cartões | Medido: cartões em 1,2 / 0,85 / 0,8rem e `--surface-2`; topo em 2,5 / 1rem | 🟢 |
| Consistência | A `RN-24` e o teste da introdução continuam válidos | `tests/test_banner_do_topo.py:270-298` | 🟢 |
| Responsividade | A ação principal é de largura total abaixo de 576 px e natural acima | Breakpoint já usado na folha (`app.css:345-347`) | 🟢 |
| Regressão | As 8 telas literais mantêm diff textual zero; o hash é movido com declaração | `RF-17` da 006; `RN-06` | 🟢 |
| Regressão | A suíte continua verde e nenhum teste é removido | Linha de base 1.048/9; princípio III | 🟢 |
| Manutenibilidade | O markup das abas, duplicado nos dois ramos, não pode divergir; qualquer ajuste nas abas é aplicado nos dois lugares | `index.html:244-251` e `:333-340` | 🟢 |
| Desempenho | Nenhuma requisição nova e nenhuma dependência nova | A mudança é de folha e de markup local | 🟢 |
| Privacidade | Nenhum dado de pessoa, xref ou cM entra em artefato | Princípio I; a feature não lê dado de análise | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: introdução continua centralizada e o comentário a descreve
  Dado a tela de entrada
  Quando a introdução é renderizada
  Então os dois parágrafos continuam dentro de uma linha justify-content-center com col-lg-*
  E não existe text-start no documento
  E o comentário do template descreve esse arranjo

Cenário: alerta na paleta nos dois temas
  Dado uma análise que terminou com sucesso
  Quando o alerta de retorno é exibido
  Então o fundo e a borda vêm de tokens da folha
  E a borda tem pelo menos 3:1 contra o fundo
  E o texto tem pelo menos 4,5:1 no tema claro e no escuro
  E o botão de fechar continua presente e estilizado na paleta

Cenário: alerta de erro usa a mesma forma
  Dado uma análise recusada
  Quando o alerta de erro é exibido
  Então ele usa a forma do alerta de sucesso com a cor de perigo
  E o texto continua legível nos dois temas

Cenário: ação principal sem peso de barra no desktop
  Dado uma janela com mais de 576 px
  Quando o formulário é renderizado
  Então o botão de ação não ocupa a largura inteira do cartão
  E abaixo de 576 px ele continua de largura total

Cenário: escala do topo compactada
  Dado a tela de entrada
  Quando o topo é medido
  Então o h1 não passa de 2,2 rem
  E a arte não passa de 280 px de largura

Cenário: ritmo das seções do topo
  Dado a tela com a árvore aberta
  Quando a distância entre o formulário e as observações é medida
  Então os blocos seguem o mesmo degrau de espaçamento
  E os cartões de resultado não mudam

Cenário: rodapé intocado
  Dado o resultado de uma análise
  Quando as cores do selo de cM e dos cartões são comparadas com a linha de base
  Então o selo de cM continua em bg-secondary
  E nenhuma regra de cor dos cartões mudou

Cenário: nenhum texto mudou
  Dado qualquer uma das 8 telas literais
  Quando o texto é comparado com o golden correspondente
  Então o diff textual é zero
  E nenhum rótulo, mensagem ou título foi alterado

Cenário: a tela servida não mudou
  Dado o HTML servido em GET /
  Quando o sha256 é comparado com o valor da linha de base
  Então o valor é o mesmo (c4a34f7b…)
  E o teste do hash continua verde sem edição
  E a razão (o comentário é Jinja, removido do HTML) está registrada no adendo

Cenário: a suíte continua verde
  Dado o estado final da feature
  Quando a suíte completa é executada
  Então há zero falhas
  E o número de testes aprovados não é menor que 1.048
  E nenhum teste foi removido

Cenário: marcas de acessibilidade preservadas
  Dado o documento servido
  Quando o botão de tema e os textos auxiliares são inspecionados
  Então aria-pressed continua no botão de tema
  E os visually-hidden existentes continuam onde estavam
  E a regra de focus-visible continua na folha
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É o único defeito real de documentação: o comentário contradiz a `RN-24` |
| RF-02 | Must | O alerta é a única cor fora da paleta na primeira dobra |
| RF-03 | Must | A barra verde é o elemento mais pesado da tela e não tem par no resultado |
| RF-04 | Should | Reduz o "buraco" do topo; é a parte mais subjetiva da harmonização |
| RF-05 | Should | Fecha a diferença de ritmo entre os blocos do topo |
| RF-06 | Must | Decisão 3a: o rodapé é o alvo da comparação, não a superfície da mudança |
| RF-07 | Must | Restrição dura de acessibilidade e de conteúdo |
| RF-08 | Must | Sem isso, a suíte falha e a mudança fica sem declaração |
| RF-09 | Must | Princípio III e restrição do pedido |
| RF-10 | Must | Contraste sem medição escrita vira opinião |
| RNF de acessibilidade | Must | WCAG AA nos dois temas |
| RNF de responsividade | Must | A ação não pode encolher no telefone |

## 9. Esclarecimentos

### Sessão 2026-10-17

- **Q:** O topo continua com a masthead centralizada ou tudo passa a ter um eixo só?

  **R:** A masthead continua centralizada (opção 1a). **Correção de escopo na sessão de plano:** a
  resposta foi dada antes de localizar a `RN-24` e o teste que prendem a introdução. O texto de
  apresentação **permanece centralizado e estreito**, e o `RF-01` passou a ser a correção do
  comentário do template. Nenhuma mudança de alinhamento será feita.

- **Q:** A ação principal no desktop: largura natural ou barra mais baixa?

  **R:** Largura natural acima de 576 px e largura total abaixo (opção 2a), com o raio das pílulas do
  resultado. A barra de largura total fica restrita ao telefone.

- **Q:** O selo de cM entra no escopo?

  **R:** Não (opção 3a). Ele passa em contraste (4,69:1) e faz parte do rodapé que o operador elogiou;
  a decisão virou a restrição `RN-08` / `RF-06`.

- **Q:** O alerta de retorno continua dispensável?

  **R:** Continua (opção 4a): o botão de fechar é preservado e o X é estilizado na paleta. Removê-lo
  mudaria comportamento, e não só aparência.

## 10. Lacunas

Nenhuma dúvida aberta nesta data. As três dúvidas foram resolvidas na sessão de esclarecimento de
2026-10-17 (§9), com a correção de escopo da `RN-24` registrada na mesma seção.

- 🟡 **Resíduo declarado:** o markup das abas está duplicado nos dois ramos da tela
  (`src/templates/index.html:244-251` e `:333-340`). Esta feature não unifica o markup; qualquer
  ajuste nas abas precisa ser aplicado nos dois lugares, e o `NFR` de manutenibilidade registra isso.
- 🟡 **Fronteira declarada:** a `RN-24` não é reaberta. Se o operador quiser alinhar o texto ao
  formulário no futuro, é outra feature, com revogação da `RN-24` e reescrita de
  `test_o_texto_de_apresentacao_esta_centralizado_e_em_coluna_estreita`.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-17 | Sessão de esclarecimento: masthead centralizada, ação natural no desktop, rodapé fora do escopo e alerta dispensável | reversa |
| 2026-10-17 | Correção de escopo: a `RN-24` e o teste da introdução foram localizados; o texto permanece centralizado e o `RF-01` virou a correção do comentário | reversa |
| 2026-10-17 | Correção durante o coding: o comentário é Jinja e não chega ao HTML; o `SHA_DA_TELA` não se move e o `RF-08` passou a verificar em vez de exigir a mudança | reversa |
