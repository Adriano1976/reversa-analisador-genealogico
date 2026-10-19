# Requirements: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O operador pediu que a apresentação dos **Resultados das Análises de Conexão** ficasse com a estética
do desenho que ele anexou: o cartão de cada conexão deixa de ser uma ficha de duas linhas e passa a
ter **três faixas de leitura** — título, selos e sinais —, com o "Voltar" e o indicador de abrir
ancorados à direita como ações. O cartão ganha barra lateral de destaque, raio maior e uma superfície
que se separa do fundo da página.

O problema que a feature resolve é de **hierarquia**: hoje o título divide a linha com os selos, e o
cabeçalho — que é a visão geral de uma lista de até 142 conexões — lê como um bloco só. Nada do que o
operador lê muda de texto, nenhuma cor de veredito muda e nenhuma regra do domínio é tocada.

> **Dois termos deste documento.** *cM* (centimorgan) é a medida de DNA compartilhado que o CSV de
> matches traz. *Sinais* são as três leituras que o cabeçalho mostra com o cartão fechado: Parentesco
> documental, Janela de vida e Profundidade do caminho.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md#o-que-mudou` | O `card-header` fica **embrulhado** pelo `<summary>`; fechado, o cartão continua dizendo de quem é, quanto é e o veredito | 🟢 |
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md#nada-sai-do-documento` | O recolhimento é visual; o texto das cinco seções continua no HTML | 🟢 |
| `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md` | Com a tabela do índice fora, `cabecalho-sinais` (Parentesco, Janela de vida, Profundidade) subiu para o cabeçalho e passou a ser a visão geral | 🟢 |
| `_reversa_sdd/addenda/020-bloco-dos-descartados-recolhivel.md` | O bloco dos descartados usa a **mesma forma** recolhível dos cartões e, de propósito, a aparência de apêndice (`--muted`, 1.05rem) | 🟢 |
| `_reversa_sdd/addenda/026-polimento-visual-da-tela.md#regras-sob-vigilância` | Os quatro tokens `--st-*` são a única declaração das cores de estado; o cinza do `INCONCLUSIVO` mede 6,11:1 | 🟢 |
| `_reversa_sdd/addenda/027-harmonizar-topo-da-tela.md` | A gramática visual do topo passou a seguir a dos cartões: cor da paleta, escala compacta, ação leve | 🟢 |
| `_reversa_sdd/addenda/031-veredito-no-cartao.md` | O veredito de viabilidade temporal sobe ao cabeçalho com família própria de contorno (`.validacao-*`), sem cor cheia | 🟢 |
| `_reversa_sdd/architecture.md#3` | Template e folha são a borda de apresentação; nenhuma regra de domínio vive neles | 🟢 |
| `_reversa_sdd/domain.md#5` | O texto da tela é **contrato**: mensagens e rótulos são literais conferidos | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` (`RF-17`) | As 8 telas literais mantêm diff textual zero | 🟢 |
| `_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md` (`W005`) | As mensagens da camada de rota e as congeladas continuam **ao caractere** | 🟢 |
| `.reversa/principles.md#ii` | Comportamento observável é preservado; mudança de comportamento é feature | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |
| `.reversa/principles.md#i` | Nome real de pessoa, cM e kit nunca entram em artefato | 🟢 |

### 2.1 O que foi medido nesta sessão (2026-10-19)

| Medição | Resultado |
|---------|-----------|
| Estrutura do cartão | `details.card.cartao-do-resultado` (fechado, `id="resultado-N"`) → `summary.sumario-do-cartao` → `div.card-header` → `h5` (`src/templates/index.html:580-684`) |
| O que vive dentro do `h5` | Título, selo de cM, selo de confronto, selo de identidade, selo de validação, o link `voltar-ao-indice` (`:652`) e o `span.cabecalho-sinais` (`:665-682`) — **tudo dentro do `h5`** |
| Faixas de leitura hoje | **Duas**: título e selos na mesma linha, `cabecalho-sinais` na segunda (o `clear:both` da folha é que o joga para baixo do "Voltar", que é `float:right`) |
| Faixas do desenho de referência | **Três**: título, selos e sinais — com a ação e o indicador à direita |
| Superfície do cabeçalho | `--bs-card-cap-bg: var(--surface-2)` contra o cartão `--surface`: **1,10:1** no claro e **1,07:1** no escuro — a separação é quase nula |
| Borda e raio | Borda `--line` contra a página `--bg`: **1,31:1** (claro) e **1,49:1** (escuro); o cartão `--surface` contra `--bg` só se separa por **1,13:1** e **1,08:1**; raio de 10 px; sem sombra (`app.css:91`) |
| Título | `h5` em `Newsreader`, 1.2rem (`app.css:93`); o `h2` da seção está em 1.6rem (`app.css:86`) |
| "Voltar" | Pílula de 0.85rem, `padding: .15rem .7rem`, `float:right`, sem ícone (`app.css:265-270`) |
| Indicador de abrir | Losango de 0.5rem desenhado com bordas em `--muted`, `margin-right: 1.1rem` (`app.css:104-109`) |
| Sublinhado no hover | `details>summary:hover{text-decoration:underline}` (`app.css:242`) alcança o `summary` do cartão: o cabeçalho inteiro sublinha ao passar o mouse |
| Contraste atual do texto | Título `--head` sobre `--surface-2`: **9,89:1** (claro) e **11,30:1** (escuro); sinais `--muted`: **5,56:1** e **6,03:1**; "Voltar" herda `--primary` do `summary`: **5,70:1** |
| Selo de cM | `badge bg-secondary` com branco: **4,69:1** — passa, no limite, e **não muda** |
| Contrastes dos selos | 6,39 / 7,13 / 6,69 / 6,11:1 (os quatro estados), medidos em 2026-10-17 |
| Cobertura da tela | `SHA_DA_TELA = c4a34f7b…`, 30.781 bytes (`tests/test_icone_de_atalho.py:140`); a mudança vive sob `{% if dna_results %}`, fora do que a tela vazia mede |
| Linha de base da suíte | **1.282 passam, 11 pulados, 0 falham**, em 86,46 s |
| Desenho de referência | `D:\dados-genealogicos\index.html`, 10.881 bytes, **fora do repositório** — referência visual, não dependência |

### 2.2 O que **não** é defeito

- O título dividir a linha com os selos **não é erro de marcação**: é o desenho vigente que o adendo
  `018` encontrou e preservou — o `h5` agrupa título, selos, "Voltar" e sinais num cabeçalho só, e é
  isso que faz o cartão fechado continuar dizendo de quem é, quanto é e o veredito.
- O "Voltar" continuar dentro do `summary` é **exigência de teste**
  (`tests/test_cartoes_recolhiveis.py:246`), não descuido: ele é a ação do cabeçalho.
- O selo de cM em `bg-secondary` passa em contraste (4,69:1) e foi declarado fora do escopo em
  2026-10-17 (`RN-08` da 027). Esta feature **não o reabre**.
- O bloco dos descartados parecer um apêndice é **de propósito** (adendo `020`): ele é o rodapé da
  análise, e não um resultado.
- O desenho de referência usa `Cormorant Garamond` e `Manrope`; o projeto usa `Newsreader` e
  `IBM Plex Sans`. Não entra fonte nova — a semelhança é de arranjo, não de tipografia.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (persona única, sem login) | Bater o olho no cabeçalho fechado e saber de quem é a conexão, quanto é o cM e qual o veredito | Percorre 142 cartões fechados e abre só os que interessam |
| Quem mantém a interface | Mudar a ficha sem tocar em texto, em regra de domínio ou nos blocos irmãos | Ajusta a folha e confere que as guardas de estrutura e contraste continuam verdes |
| Revisor de acessibilidade | Confirmar que o refino não apagou foco, rótulo nem contraste | Mede os pares novos nos dois temas e navega por teclado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01: o cabeçalho do cartão passa a ter três faixas de leitura.** Título em linha própria,
   selos em faixa própria e sinais (Parentesco, Janela de vida, Profundidade) na terceira faixa; a
   ação "Voltar" fica à direita, centrada verticalmente. 🟢
   - Origem no legado: `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` (o cabeçalho é a
     visão geral) e `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md`
   - Tipo: nova
2. **RN-02: nenhum texto que o operador lê muda.** Título, nome, cM, vereditos, "Voltar" e o texto
   escondido do link continuam ao caractere; muda só o arranjo. 🟢
   - Origem no legado: `RF-17` da 006, `W005` e `_reversa_sdd/domain.md#5`
   - Tipo: **preservada**
3. **RN-03: cor nova entra por token, com contraste medido.** Nenhum literal de cor novo em regra;
   todo par texto/fundo fica ≥ 4,5:1 e todo elemento não textual ≥ 3:1 nos dois temas, com os
   números no comentário da folha. 🟢
   - Origem no legado: adendos `026` e `027`
   - Tipo: **preservada** (explicitada para esta feature)
4. **RN-04: as cores de significado são reservadas.** A barra lateral e a superfície do cartão não
   podem usar `--danger`, `--aviso-line`, `--st-*`, `--validacao-*` nem `--primary`: essas cores
   dizem veredito, aviso e ação. O destaque do cartão é neutro (marrom/pergaminho da paleta). 🟢
   - Origem no legado: adendos `026` e `031`; `app.css:213-234`
   - Tipo: nova (restrição)
5. **RN-05: a árvore do cartão não muda.** `details.card.cartao-do-resultado` →
   `summary.sumario-do-cartao` → `div.card-header` → `h5`; `voltar-ao-indice`, `cabecalho-sinais` e
   `rotulo-parentesco` continuam dentro do cabeçalho; **nenhum `<div>` novo dentro do
   `card-header`**; o cartão nasce fechado e o `id` fica no `details`. 🟢
   - Origem no legado: `tests/test_cartoes_recolhiveis.py:232-284`;
     `tests/test_estado_do_resultado.py:220-234`
   - Tipo: **preservada**
6. **RN-06: os selos continuam os mesmos.** Ordem, texto, classes e cores: cM em `bg-secondary`
   (4,69:1), os quatro estados, identidade, validação temporal, janela de vida e profundidade. O
   refino muda espaçamento e forma, nunca a cor de um selo. 🟢
   - Origem no legado: adendos `026` e `031`; `tests/test_estilo_da_tela.py:342-355`
   - Tipo: **preservada**
7. **RN-07: o escopo é o cartão de conexão, e só ele.** Os blocos `bloco-descartados` e
   `observacoes-do-arquivo` compartilham a forma de `summary` e **não** recebem a barra, o raio nem
   a sombra: continuam apêndice e aviso, como os adendos `020`/`022` decidiram. 🟢
   - Origem no legado: adendos `020` e `022`; `src/templates/index.html:1198`; sessão de
     2026-10-19 (§9, opção 1a)
   - Tipo: nova (restrição de escopo)
8. **RN-08: a tela vazia não muda.** A mudança vive no ramo `dna_results`; `GET /` deve continuar
   `c4a34f7b…` com 30.781 bytes. Se o hash mover, a entrega atualiza `SHA_DA_TELA` com bloco datado
   e declara a mudança no adendo. 🟢
   - Origem no legado: `tests/test_icone_de_atalho.py:140`; `RF-08` da 027
   - Tipo: **preservada**
9. **RN-09: o cabeçalho não sublinha no hover.** A regra global
   `details>summary:hover{text-decoration:underline}` (`app.css:242`) é neutralizada no `summary` do
   cartão: a pista de clique é o indicador e a superfície, não um sublinhado de três linhas. 🟢
   - Origem no legado: `app.css:240-242`; o desenho de referência não tem sublinhado
   - Tipo: **alterada** (correção)
10. **RN-10: sem movimento novo.** Nada de animação de entrada por cartão; só transições curtas de
    `hover`/`focus`, e o `prefers-reduced-motion` que já zera transições continua valendo. 🟢
    - Origem no legado: `app.css:417`; o desenho de referência é uma página de demonstração e não
      dita comportamento da tela real; sessão de 2026-10-19 (§9, opção 3a)
    - Tipo: nova (restrição)
11. **RN-11: as marcas de acessibilidade não mudam.** O `focus-visible` global, o `visually-hidden`
    do "Voltar" e a semântica nativa de `details`/`summary` continuam como estão; a ordem de
    tabulação não piora. 🟢
    - Origem no legado: `app.css:88`; `tests/test_estado_do_resultado.py:220-229`
    - Tipo: **preservada**

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Pôr o título em linha própria, com escala própria e a mesma voz tipográfica | Must | O título ocupa uma faixa só dele, em **1,4 rem**, `Newsreader` e `--head`; o `h2` da seção (1,6 rem) continua acima | 🟢 |
| RF-02 | Pôr os selos em faixa própria abaixo do título | Must | Os selos formam uma faixa `flex` com quebra e espaçamento constantes, na ordem atual: cM, confronto, identidade, validação; sem cM ou sem veredito, a faixa encolhe e não reserva altura vazia | 🟢 |
| RF-03 | Manter os sinais numa terceira faixa, legíveis com o cartão fechado | Must | `rotulo-parentesco` em `--muted` e os selos de janela/profundidade aparecem abaixo dos selos, sem depender de abrir o cartão | 🟢 |
| RF-04 | Ancorar o "Voltar" à direita do cabeçalho, como pílula com chevron à esquerda | Must | O link mantém `class="voltar-ao-indice"`, `href="#resultados"`, o texto `Voltar` e o `visually-hidden`; o chevron é desenhado em CSS, sem markup novo; alinhado ao centro vertical das três faixas | 🟢 |
| RF-05 | Transformar o indicador de abrir/fechar em caixa arredondada com chevron | Must | O indicador é uma caixa de ~2 rem com borda e chevron, à direita do cabeçalho; ao abrir, o chevron gira; o teste do `rotate` continua verde | 🟢 |
| RF-06 | Dar ao cartão superfície própria: barra lateral, raio maior, sombra sutil e borda | Must | Barra de ~5 px em token neutro da paleta; raio entre 16 e 18 px; sombra discreta no claro e separação por borda/superfície no escuro; nada de cor de significado (`RN-04`) | 🟢 |
| RF-07 | Tirar o sublinhado do cabeçalho no hover | Must | Passar o mouse sobre um cartão fechado não sublinha título, selos nem sinais; o "Voltar" continua com `text-decoration:none` | 🟢 |
| RF-08 | Empilhar o cabeçalho no telefone sem colisão | Must | Abaixo de 575,98 px o "Voltar" desce para a própria linha, alinhado à esquerda; o chevron não se sobrepõe ao texto; não há `overflow-x` | 🟢 |
| RF-09 | Preservar todo o texto visível e o escondido | Must | Nenhum literal muda; as 8 telas literais mantêm diff textual zero; o `visually-hidden` do "Voltar" continua com o destino escrito | 🟢 |
| RF-10 | Medir a tela servida antes e depois | Must | `GET /` continua com `c4a34f7b…` e 30.781 bytes; se mover, o `SHA_DA_TELA` é atualizado com bloco datado e a razão registrada | 🟢 |
| RF-11 | Entregar a suíte verde, sem remover teste | Must | ≥ 1.282 passam e 11 pulados, 0 falhas; nenhum teste apagado ou desabilitado; as guardas de estrutura do cartão e de contraste continuam verdes | 🟢 |
| RF-12 | Medir e registrar o contraste dos elementos novos | Must | Comentário na folha com os pares medidos: título, sinais, "Voltar", chevron e barra, nos dois temas; texto ≥ 4,5:1 e não-texto ≥ 3:1 | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Acessibilidade | Todo texto do cabeçalho mantém ≥ 4,5:1 nos dois temas; chevron, barra e bordas ≥ 3:1 quando carregam significado | WCAG 2.1 AA; título 9,89:1 e sinais 5,56:1 no claro, medidos | 🟢 |
| Acessibilidade | O foco visível e as marcas ARIA não mudam | `app.css:88`; `tests/test_estilo_da_tela.py` | 🟢 |
| Consistência | O cartão usa a mesma paleta, os mesmos tokens e a mesma família tipográfica do resto da tela | Nenhuma fonte ou cor literal nova (`RN-03`) | 🟢 |
| Consistência | Os blocos irmãos (descartados, observações) não são alcançados pelas regras novas | Regras escopadas em `.cartao-do-resultado` | 🟢 |
| Responsividade | O cabeçalho se lê em 320 px sem sobreposição e sem rolagem horizontal | Breakpoint de 575,98 px já usado na folha | 🟢 |
| Regressão | As 8 telas literais mantêm diff textual zero; o hash é medido e, se mover, declarado | `RF-17` da 006; `RN-08` | 🟢 |
| Regressão | A suíte continua verde e nenhum teste é removido | Linha de base 1.282/11; princípio III | 🟢 |
| Manutenibilidade | A mudança fica em duas superfícies: o `h5` do template e regras escopadas na folha | A folha é a autoridade única do estilo (`W004`/`RN-07`) | 🟢 |
| Desempenho | Nenhuma requisição, fonte, script ou dependência nova | O desenho de referência é referência visual, não dependência | 🟢 |
| Privacidade | Nenhum nome, xref, kit ou cM real entra em artefato; os exemplos usam dado sintético | Princípio I; o mockup do operador fica fora do repositório | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: cartão fechado em três faixas
  Dado o resultado de uma análise de conexão
  Quando o cartão é renderizado fechado
  Então o título ocupa a primeira faixa
  E os selos ocupam a segunda
  E os sinais ocupam a terceira
  E o "Voltar" fica à direita, centrado verticalmente

Cenário: título em linha própria
  Dado um cartão de resultado
  Quando o cabeçalho é medido
  Então o título não divide a linha com nenhum selo
  E a escala do título fica em 1,4 rem

Cenário: selos preservados
  Dado um cartão com cM, confronto, identidade e validação
  Quando os selos são comparados com a linha de base
  Então a ordem e as classes continuam as mesmas
  E o selo de cM continua em bg-secondary
  E nenhuma cor de estado mudou

Cenário: "Voltar" continua o mesmo link
  Dado um cartão de resultado
  Quando o link de retorno é inspecionado
  Então ele continua com class="voltar-ao-indice" e href="#resultados"
  E o texto visível continua "Voltar"
  E o visually-hidden continua nomeando o destino

Cenário: indicador muda ao abrir
  Dado um cartão fechado
  Quando o operador o abre
  Então o chevron gira para a posição de aberto
  E o teste do indicador continua verde

Cenário: cabeçalho não sublinha
  Dado um cartão fechado
  Quando o mouse passa sobre o cabeçalho
  Então nenhum texto do cabeçalho fica sublinhado

Cenário: superfície nova nos dois temas
  Dado o tema claro e o tema escuro
  Quando o cartão é renderizado
  Então a barra lateral usa token neutro da paleta
  E o cartão se separa do fundo por borda e superfície
  E nada usa cor de veredito, aviso ou ação como decoração

Cenário: conexão mínima, sem cM e sem veredito
  Dado um payload de resultado só com nome e caminho documental
  Quando o cartão é renderizado fechado
  Então o título e os sinais continuam nas respectivas faixas
  E a faixa de selos não reserva altura vazia
  E nenhum selo é inventado para preencher o espaço

Cenário: nome longo quebra sem estourar a faixa
  Dado uma conexão cujo nome ocupa mais de uma linha
  Quando o cartão é renderizado em 320 px
  Então o nome quebra dentro da faixa do título
  E o "Voltar" e o chevron continuam alcançáveis
  E não há rolagem horizontal

Cenário: telefone sem sobreposição
  Dado uma janela de 320 px
  Quando o cartão fechado é renderizado
  Então o "Voltar" desce para a própria linha
  E o chevron não cobre texto
  E não há rolagem horizontal

Cenário: nenhum texto mudou
  Dado qualquer uma das 8 telas literais
  Quando o texto é comparado com o golden correspondente
  Então o diff textual é zero
  E nenhum rótulo, mensagem ou título foi alterado

Cenário: a tela vazia não mudou
  Dado o HTML servido em GET /
  Quando o sha256 é comparado com a linha de base
  Então o valor continua c4a34f7b…
  E o tamanho continua 30.781 bytes
  E nenhuma edição foi feita em SHA_DA_TELA

Cenário: a suíte continua verde
  Dado o estado final da feature
  Quando a suíte completa é executada
  Então há zero falhas
  E o número de testes aprovados não é menor que 1.282
  E nenhum teste foi removido

Cenário: contraste medido, não opinado
  Dado os elementos novos do cartão
  Quando os pares texto/fundo são medidos nos dois temas
  Então cada par de texto fica em ≥ 4,5:1
  E cada elemento não textual significativo fica em ≥ 3:1
  E os números estão no comentário da folha
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É a mudança de hierarquia que o operador pediu: o título deixa de dividir a linha |
| RF-02 | Must | Sem faixa própria, os selos voltam a competir com o título |
| RF-03 | Must | É a visão geral do cartão fechado (adendo 019): não pode sair nem esconder |
| RF-04 | Must | O "Voltar" é a ação do cabeçalho e tem contrato de teste |
| RF-05 | Must | O indicador é a única pista de que há o que abrir |
| RF-06 | Must | É o que dá ao cartão a superfície do desenho de referência |
| RF-07 | Must | O sublinhado de três linhas é defeito visível no desenho novo |
| RF-08 | Must | O cartão é lido no telefone; colisão ali é regressão |
| RF-09 | Must | Restrição dura de conteúdo (`RF-17`/`W005`) |
| RF-10 | Must | Sem medir, a mudança de HTML fica sem declaração |
| RF-11 | Must | Princípio III e restrição do pedido |
| RF-12 | Must | Contraste sem medição escrita vira opinião |
| RNF de acessibilidade | Must | WCAG AA nos dois temas |
| RNF de responsividade | Must | Sem rolagem horizontal em 320 px |

## 9. Esclarecimentos

### Sessão 2026-10-19

- **Q:** O tratamento novo do cartão (barra lateral, raio maior, sombra) alcança também os blocos
  que usam a mesma forma de `summary` — "Matches descartados" e "Observações do arquivo"?

  **R:** Não (opção 1a). Só o cartão de conexão recebe o tratamento. O bloco dos descartados
  continua como apêndice e o das observações como bloco de aviso, como os adendos `020`/`022`
  decidiram. O escopo virou a restrição `RN-07`.

- **Q:** Qual escala para o título do cartão? (o `h2` da seção está em 1,6 rem; hoje o título do
  cartão está em 1,2 rem)

  **R:** 1,4 rem (opção 2a). O `h2` continua claramente acima, e o título do cartão ganha um degrau
  visível sobre os 1,2 rem atuais. O `RF-01` passou a fixar o valor.

- **Q:** O desenho de referência tem animação de entrada (fade + subida); a tela real não tem
  nenhuma.

  **R:** Manter sem animação (opção 3a): só transições curtas de `hover`/`focus`, com o
  `prefers-reduced-motion` que já zera transições. Nenhum `IntersectionObserver` novo e nenhuma
  animação por cartão — numa lista de 142, entrada animada é custo sem ganho de leitura.

## 10. Lacunas

- 🟡 **Resíduo declarado — altura da lista.** O desenho de referência passa o cartão de ~97 px para
  ~171 px (medição das imagens). Numa análise de 142 conexões, a lista fica bem mais longa; o HTML
  não cresce (o recolhimento continua), o que cresce é a rolagem. O ganho é a leitura do cabeçalho;
  o custo é aceito pelo operador no desenho que ele escolheu.
- 🟡 **Resíduo declarado — verificação visual humana.** Sem navegador no loop, o que os testes provam
  é estrutura, contrato de classe e contraste resolvido pela cascata; o resultado renderizado
  (sombra, barra, alinhamento fino) depende de conferência humana, como já registrado no adendo
  `018`.
- 🟡 **Resíduo declarado — o mockup não entra no repositório.** `D:\dados-genealogicos\index.html`
  é referência visual; nenhuma fonte, script ou asset dele é copiado, e o nome de pessoa que aparece
  nele não é transcrito para artefato nenhum (princípio I).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-19 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-19 | Sessão de esclarecimento: escopo restrito ao cartão, título em 1,4 rem e nenhuma animação de entrada | reversa |
