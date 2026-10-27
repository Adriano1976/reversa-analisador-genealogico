# Investigation: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Ancoragem: `_reversa_sdd/architecture.md#1` e `#3`, `_reversa_sdd/addenda/046-paginacao-dos-resultados.md`

## 1. A pergunta

Como imprimir **um cartão** de resultado — uma pessoa, com as cinco seções e o diagrama — a partir de
uma tela que é um documento único, servido por `POST`, sem estado no servidor e sem reexecutar a
análise? E o que o modelo de impressão do navegador permite prometer?

## 2. Restrições que o projeto impõe

| Restrição | Origem | Consequência para o desenho |
|-----------|--------|------------------------------|
| A análise não é persistida; o servidor não guarda o resultado | `_reversa_sdd/architecture.md#1` | Um endpoint de impressão teria de reexecutar o núcleo (12 a 31 s, `046`) ou receber o payload de volta |
| A suíte **não executa JavaScript**; prende marcação renderizada | `tests/test_paginacao_na_tela.py#L17` | O teste da feature mede HTML e folha; o comportamento de script fica em verificação manual declarada |
| `SHA_DA_TELA` é invariante mantido à mão | `tests/test_icone_de_atalho.py#L189` | Qualquer script novo muda a tela vazia e exige a medição declarada no comentário |
| `requirements.txt` é lista de runtime | `_reversa_sdd/addenda/049-sistema-de-log.md` | Nada de biblioteca de PDF ou de imagem no caminho |
| Paridade compara **contexto**, não HTML | `_reversa_sdd/parity/harness.py#L191` | Mexer no template não quebra paridade; mexer no contexto, sim |
| O documento é um só, e os cartões nascem no HTML | `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` | Imprimir não precisa buscar nada: o conteúdo já está no DOM |

## 3. O modelo de impressão do navegador — o que dá e o que não dá

### 3.1 Contadores de página: **não**

`@page { @bottom-center { content: "página " counter(page) " de " counter(pages) } }` é CSS Paged
Media, e as caixas de margem **não são implementadas** por Chrome, Edge, Firefox nem Safari. Não há
API do documento para o número da página durante a impressão. Consequência: o `RF-04` não pode ser
cumprido na parte "página N de M".

O que existe é o cabeçalho/rodapé **nativo** do diálogo (data, título, endereço e "1/5"), que o
operador liga e desliga nas opções de impressão. Ele é do navegador, não do documento.

### 3.2 Cores de fundo: descartadas por padrão

O navegador não imprime fundos por padrão (`print-color-adjust: economy`). Isso atinge em cheio os
selos do cartão: `.badge[class*="estado-"]` usa **texto branco sobre cor cheia**. Sem o fundo, o texto
some no papel. Duas saídas:

- forçar `print-color-adjust: exact` nos selos (Chrome e Safari; Firefox usa `color-adjust`) — mantém
  a cor, mas continua ilegível numa impressora preto e branco se o tom for claro;
- **reestilizar os selos para papel**: borda na cor do estado e tinta escura sobre branco. É legível
  em preto e branco e não depende de suporte a `print-color-adjust`.

A segunda opção é a escolhida (`D-13`), porque o `RNF Papel` do requirements pede legibilidade em
preto e branco e porque nenhum estado pode depender **só** de cor.

### 3.3 Fragmentação

`break-before: page` e `break-inside: avoid` são suportados pelos quatro navegadores (com prefixos
históricos `page-break-*`). O que **não** é confiável é a altura exata da página: margens do diálogo,
cabeçalho nativo e escala do usuário mudam o resultado. Por isso a regra é conservadora: abre folha
antes do desenho e evita cortar linha de tabela — o resto flui.

### 3.4 Rodapé repetido em toda folha

`position: fixed` em mídia paginada repete o elemento em cada página em Chrome e Firefox. É o
mecanismo escolhido para a origem (`D-07`), com verificação manual nos quatro navegadores (`R-05`).
Se algum não repetir, o fallback é um rodapé no fim do documento.

### 3.5 Eventos de impressão

`beforeprint` e `afterprint` existem nos quatro navegadores. O `afterprint` dispara ao fechar o
diálogo, **inclusive no cancelamento** — é o gancho natural para desfazer o clone e restaurar o
cartão. Como a ordem e o momento variam (o `print()` é bloqueante em alguns e não em outros), a
restauração tem também um `setTimeout` de segurança e uma guarda de reentrância (`D-10`).

### 3.6 O desenho mede o contêiner

O `mermaid.initialize` da tela roda com `startOnLoad: false`, e o desenho só é renderizado quando o
`details` que o contém abre (`index.html#L1979-L1989`). Fechado, o contêiner tem tamanho zero e o SVG
sai quebrado — e marcado como `data-processed`, então abrir depois não conserta. É a mesma armadilha
que a `046` registrou ao revelar a página antes de abrir o cartão.

Consequência para a impressão: **abrir o cartão e esperar o SVG aparecer** (`D-04`, `D-05`). O
`mermaid.run` é assíncrono e o `toggle` existente não devolve promessa; um `MutationObserver` no
cartão, com teto de 2 s, resolve sem tocar no caminho quente da tela.

## 4. Alternativas avaliadas

| Alternativa | Como funcionaria | Por que não |
|-------------|------------------|-------------|
| **PDF no servidor** | Nova rota que recebe a referência, reexecuta a análise e devolve um PDF | Reexecuta o núcleo (12 a 31 s), exige biblioteca nova no runtime e um segundo renderizador do cartão — o risco de os dois divergirem é permanente |
| **Rota de impressão** (`POST` com `action=imprimir`) | O formulário leva os campos ocultos e a rota devolve uma página limpa | Mesma reexecução; e o documento já está no navegador, então é trabalho redundante |
| **Janela nova com `document.write`** | Abre `window.open()` e escreve o HTML do cartão | Perde a folha de estilo servida por rota, o SVG já desenhado e o contexto; bloqueador de pop-up vira dependência |
| **Esconder ancestrais por CSS** | `body.imprimindo` + regras escondendo cabeçalho, fases e cartões irmãos | Cada mudança de layout quebra a lista de seletores; a página é grande e muda com frequência |
| **`visibility: hidden` + `position: absolute`** | Esconde tudo e reposiciona o cartão | `visibility` preserva o espaço: o documento imprime dezenas de folhas em branco |
| **`:has()`** | `body.imprimindo :not(:has(.cartao-em-impressao))` | Cobertura recente, e uma regra de impressão que falha em silêncio é pior que uma regra chata |
| **Clonar para um contêiner** | `#area-de-impressao` recebe o clone; `@media print` esconde `body > *` menos ele | **Escolhida**: ocultação de um seletor, original intocado, SVG já renderizado viaja no clone |
| **Imprimir a página inteira e recortar** | Deixar o operador imprimir tudo e recortar | Não é a funcionalidade pedida, e 68 cartões não cabem numa folha |

## 5. Como o projeto testa apresentação sem executar JavaScript

O precedente é a `046`: a marcação nasce no HTML (um controle montado no `DOMContentLoaded` passaria a
existir só no navegador, e nenhum teste o veria), e o teste prende **presença, contrato e ligação** —
não aparência. A folha é presa pelo par classe-no-template ↔ `.classe`-na-folha, e o script é preso
por asserções sobre o texto que liga o controle ao comportamento.

A feature segue o mesmo desenho: botão, bloco de identificação e contêiner no HTML; classes na folha;
script com os nomes e as guardas verificáveis por leitura. O que não é verificável assim — o clique
não recolher, a quebra de página, o rodapé repetido — entra no roteiro manual de `onboarding.md` e
como risco declarado.

## 6. Identificação da folha: referência ou rótulo visível

O contexto do resultado já carrega `gedcom_filename` e `csv_filename_usado`, e ambos são a
**referência** armazenada (`chave__rótulo.ext`), não o rótulo visível da lista. A `049` fixou a
referência como identidade de arquivo na auditoria (chave de conteúdo + extensão, nunca o rótulo).

Usar a referência na folha tem três vantagens e nenhuma desvantagem prática:

1. identifica o arquivo sem ambiguidade entre envios do mesmo nome;
2. carrega a mesma chave de conteúdo da trilha de auditoria, então folha e log falam a mesma língua;
3. **não exige variável de contexto nova** — nada muda no Python, e a paridade fica intocada.

O custo é a chave de 16 hexadecimais antes do nome, que é feia mas reconhecível no sufixo.

## 7. Custo e bytes

Cada cartão ganha um bloco de identificação oculto na tela. Com 68 cartões, o acréscimo é da ordem de
dezenas de KB num documento que já mede ≈ 3,9 MB (`046`). O contêiner de impressão é vazio. O script
novo é pequeno. A medição exata entra na fase de código, junto com o `SHA_DA_TELA`.

## 8. Fontes

- `_reversa_sdd/architecture.md#1` e `#3`
- `_reversa_sdd/addenda/046-paginacao-dos-resultados.md`
- `_reversa_sdd/addenda/049-sistema-de-log.md`
- `_reversa_sdd/parity/harness.py#L191`
- `src/templates/index.html#L1979-L1989` (renderização do desenho no `toggle`)
- `src/assets/app.css#L10-L66` (tokens do tema claro)
- `src/app.py#L566-L576` (contexto do resultado)
- MDN, *Printing* — <https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_media_queries/Printing>
- MDN, *CSS fragmentation* — <https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_fragmentation>
- MDN, *`window.print()`* — <https://developer.mozilla.org/en-US/docs/Web/API/Window/print>
