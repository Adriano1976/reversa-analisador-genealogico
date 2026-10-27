# Interface: bloco de impressão no documento de resultado

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Contrato afetado: **corpo HTML** de `POST /` com `action=dna_analysis`

## 1. Natureza do contrato

O contrato **HTTP não muda**: mesma rota, mesmo método, mesmo `action`, mesmos campos de formulário,
mesmos códigos de status e mesmas mensagens. O que muda é o **documento entregue no corpo**, que
ganha os nós abaixo. Nada viaja na requisição por causa da impressão.

| Elemento do contrato HTTP | Antes | Depois |
|---------------------------|-------|--------|
| Método, rota e `action` | `POST /`, `action=dna_analysis` | idênticos |
| Campos do formulário | os mesmos | idênticos |
| Status e mensagens | os mesmos | idênticos |
| Corpo HTML | o de hoje | ganha os nós deste documento |

## 2. Elementos e atributos

### 2.1 Contêiner de impressão

```html
<div id="area-de-impressao" aria-hidden="true"></div>
```

- Fica no fim do `<body>`, antes dos `<script>`.
- Nasce **vazio** e fica oculto na tela (`display:none`).
- É o único filho do `<body>` visível durante a impressão.

### 2.2 Comando por cartão

```html
<button type="button" class="imprimir-conexao"
        data-imprimir="resultado-3"
        aria-label="Imprimir a análise de conexão com <nome da pessoa>">
  Imprimir
</button>
```

- Dentro de `.controles-do-cabecalho`, **depois** do link `.voltar-ao-indice`.
- Dentro do `summary` do cartão: é o que o torna visível com o cartão fechado.
- `data-imprimir` aponta para o `id` do cartão (`resultado-N`), que é o mesmo alvo usado pelo `#` da
  barra de endereços.
- O nome acessível **identifica a pessoa**; o texto visível é só "Imprimir".

### 2.3 Identificação da folha (uma por cartão, oculta na tela)

```html
<div class="identificacao-da-impressao">
  <p class="linha-da-identificacao">
    <span><strong>Árvore:</strong> <referência armazenada></span>
    <span><strong>CSV:</strong> <referência armazenada></span>
    <span><strong>Raiz:</strong> <nome digitado></span>
  </p>
  <p class="momento-da-impressao">Impresso em <time class="quando-da-impressao"></time></p>
</div>
```

- Primeiro nó do corpo do cartão.
- `display:none` na tela; `display:block` na impressão.
- Os três campos vêm do contexto do resultado (`gedcom_filename`, `csv_filename_usado`,
  `root_name_usado`); o `<time>` é preenchido no clique.

### 2.4 Nós criados só na impressão (script)

| Nó | Atributo/estado | Regra |
|----|-----------------|-------|
| Clone do cartão | `class="cartao-em-impressao"` | `id` removido; `hidden` removido; todos os `details` com `open` |
| Folha do desenho | `class="folha-do-diagrama"` | Envolve o diagrama movido, com um título antes; abre folha nova |
| Rodapé | `class="origem-da-impressao"` | Fixo, repetido em toda folha |
| Corpo | `class="imprimindo"` | Ligado antes de `print()`, desligado no `afterprint` |

## 3. Sequência de comportamento

1. Clique no `.imprimir-conexao` → `preventDefault()` **e** `stopPropagation()` (o `summary` não pode
   recolher o cartão).
2. Se `body` já tem `imprimindo`, **retorna** (guarda de reentrância).
3. Guarda o estado: `open` do cartão e a posição de rolagem.
4. Abre o cartão (`open = true`), o que dispara o `toggle` existente e a renderização do desenho.
5. Preenche `.quando-da-impressao` com data e hora locais no formato `pt-BR`.
6. Espera todo `.mermaid` do cartão ter `svg`, com **teto de 2 s** (`MutationObserver`).
7. Clona o cartão, remove `id` e `hidden`, marca `cartao-em-impressao` e abre todos os `details`.
8. Move `.grafo-do-registro` e `.arvore-sugerida` do clone para `.folha-do-diagrama`, no fim.
9. Esvazia e preenche `#area-de-impressao`; adiciona `imprimindo` ao `body`.
10. `window.print()`.
11. No `afterprint` (ou no temporizador de segurança): remove `imprimindo`, esvazia o contêiner,
    restaura `open` e a rolagem.

## 4. Contrato de folha de estilo

Estas regras são **obrigatórias** — cada classe do template precisa existir na folha (o projeto tem
teste que falha quando o par classe ↔ `.classe` se rompe):

| Regra | Papel |
|-------|-------|
| `#area-de-impressao { display: none }` | oculto na tela |
| `@media print { body.imprimindo > *:not(#area-de-impressao) { display: none } }` | isola o documento |
| `@media print { #area-de-impressao { display: block } }` | publica o clone |
| `@media print { .controles-do-cabecalho { display: none } }` | tira "Voltar", chevron e o próprio comando |
| `@media print { .identificacao-da-impressao { display: block } }` | mostra a identificação |
| `@media print { .folha-do-diagrama { break-before: page } }` | desenho em folha própria |
| `@media print { tr { break-inside: avoid } }` | não corta linha de tabela |
| `@media print { .origem-da-impressao { position: fixed; bottom: 0 } }` | origem repetida |
| `@media print { .badge { borda na cor do estado; fundo branco; tinta escura } }` | selo legível sem cor de fundo (`D-13`) |
| `@media print { body.imprimindo { tokens do tema claro } }` | papel sempre claro (`D-09`) |

> **Não use** caixas de margem de `@page` para numeração: não são implementadas nos navegadores-alvo
> (`roadmap.md#D-07`).

## 5. Falha e degradação

| Situação | O que acontece | O que **não** acontece |
|----------|----------------|------------------------|
| Desenho não renderiza em 2 s | O documento imprime sem o desenho | O diálogo não trava; o caminho textual continua na seção 1 |
| Sem internet (CDN fora) | Texto, tabelas e identificação saem; o desenho pode faltar | Nada de quadro vazio reservado |
| Folha de estilo não carrega | A página inteira é impressa | Nada é gravado ou enviado |
| `afterprint` não dispara | O temporizador de segurança restaura a tela | O cartão não fica aberto para sempre |
| Duplo clique no comando | O segundo clique é ignorado | Não abre dois diálogos |

## 6. Idempotência e concorrência

- Um único `print()` por acionamento; a guarda `imprimindo` cobre clique duplo e clique durante o
  diálogo.
- O contêiner é esvaziado antes de cada montagem e no fim; não acumula clones.
- Duas abas imprimindo ao mesmo tempo não se afetam: cada documento tem o próprio DOM e a própria
  guarda.
- Nenhum estado é persistido: recarregar a página não reproduz a impressão.

## 7. Acessibilidade

- O comando é um `<button type="button">` com nome acessível que **identifica a pessoa**.
- Entra na ordem de tabulação natural do cartão e responde a Enter e Espaço.
- Acioná-lo **não** abre nem fecha o cartão (guarda do item 3.1).
- A identificação e o rodapé são conteúdo de impressão: ficam fora da árvore de acessibilidade na
  tela (ocultos) e não são anunciados.

## 8. Compatibilidade

Alvo: último Chrome, Edge, Firefox e Safari de desktop (resposta de 2026-10-26). O diálogo é o do
sistema. A verificação de quebra de página, repetição do rodapé e legibilidade dos selos é **manual**,
com o roteiro de `onboarding.md#9`.

## 9. Invariantes

1. **Nenhuma requisição** é feita ao acionar a impressão.
2. Nenhum campo novo viaja no formulário.
3. Nenhum texto, contagem, ordem ou cartão existente muda (`RF-11`).
4. Nenhum dado é gravado no servidor, no repositório ou em `evidence/` (Princípio I).
5. Fora do contêiner de impressão, o DOM volta ao estado anterior depois de fechar o diálogo.
6. O contexto de render não ganha chave: a paridade não pode divergir por causa desta feature.

## 10. Como cada item é preso

| Contrato | Teste |
|----------|-------|
| Comando por cartão, com nome acessível e `data-imprimir` | Teste novo lê a resposta real de `POST /` |
| Identificação com os três campos | Teste novo lê a resposta real |
| Contêiner `#area-de-impressao` | Teste novo lê a resposta real |
| Par classe ↔ folha de estilo | Teste novo lê `src/assets/app.css` |
| Regras de `@media print` | Teste novo lê a folha |
| Ligação do script (nomes e guardas) | Teste novo lê o HTML |
| `SHA_DA_TELA` da tela vazia | `tests/test_icone_de_atalho.py` atualizado |
| Clique não recolhe, quebra de página, rodapé repetido | **Manual**, `onboarding.md#9` (risco `R-06`) |
