# Investigation: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/027-harmonizar-topo-da-tela/requirements.md`

## 1. A pergunta que o plano precisava responder

O operador apontou que o rodapé parece mais bem desenhado que o topo. Antes de planejar, a pergunta
era: **o que exatamente faz o topo parecer menos cuidado — e o que disso é defeito, o que é decisão?**

A resposta separou três coisas: um **defeito de documentação** (comentário que contradiz a decisão), um
**defeito de identidade visual** (alerta fora da paleta) e **escolhas de peso** (ação em barra, escala
do topo). O alinhamento do texto, que parecia o maior defeito, é **decisão vigente**.

## 2. O que foi medido

| Objeto | Medição |
|--------|---------|
| Introdução | Dentro de `div.text-center` (`index.html:190-228`), com `row justify-content-center` + `col-lg-9`; a `RN-24` pede exatamente isso e o teste proíbe `text-start` |
| Comentário da introdução | `index.html:185-187` diz "os dois paragrafos ficam alinhados a esquerda" — falso desde a `T045` (2026-10-10) |
| Alerta de retorno | `alert alert-success`/`alert-danger` sem regra na folha; fundo `#d1e7dd`, texto `#0a3622` (**10,35:1**), borda `#badbcc` (**1,15:1** contra o fundo) |
| Ação principal | `div.d-grid` em três formulários (`index.html:288`, `:356`, `:405`); branco sobre `--primary` = **6,26:1** |
| Selo de cM | `badge bg-secondary` (`index.html:541`); branco sobre `#6c757d` = **4,69:1** |
| Escala | `h1` `clamp(1.9rem, 4vw, 2.5rem)`; arte `min(50%, 320px)`; cartão de resultado com título 1,2rem e metadados 0,85/0,8rem |
| Superfícies | Card branco + alerta colorido + linha + abas + formulário + card creme: seis tratamentos |
| Alerta dentro do resultado | `alert alert-warning` (`index.html:1015`), dentro de um cartão — não pode ser alcançado pela regra nova |

## 3. O achado que corrigiu o escopo

O texto centralizado parecia a maior evidência de "topo menos desenhado". Não é: a `RN-24` (adendo
`011`) registra o pedido do operador de 2026-10-10 — texto **centralizado** e em **coluna mais
estreita** —, e `tests/test_banner_do_topo.py:270-298` prende a estrutura (`row justify-content-center`
+ `col-lg-*`), proíbe `text-start` e ainda documenta que o alinhamento à esquerda era o comportamento
**anterior**.

O que ficou para trás foi o **comentário** do template, que ainda descreve o comportamento antigo. É
esse comentário que sustentou a leitura de "defeito" na revisão visual — inclusive a deste plano, antes
de o teste ser lido. A feature corrige o comentário e **não toca no layout**.

## 4. Por que o rodapé parece melhor

- **Gramática estável:** cada cartão repete título em serif 1,2rem, linha de selos e metadados em
  0,85rem, com padding compacto.
- **Um eixo:** o conteúdo dos cartões alinha à esquerda e as ações ficam à direita.
- **Cor da paleta:** os selos de estado saem de `--st-*`; o resto é `--muted` e `--line`.
- **Peso:** as ações secundárias são pílulas de contorno; o peso fica com o conteúdo.
- **Degraus:** 1,2 / 0,85 / 0,8rem, sem saltos.

O topo falha em três desses cinco pontos (cor, peso e degraus) e mantém o eixo central da `RN-24`, que
é legítimo para a introdução, não para o formulário.

## 5. Alternativas avaliadas

### 5.1 Alerta

| Alternativa | Custo | Veredito |
|-------------|-------|----------|
| Tematizar `.alert-success`/`.alert-danger` na folha | 4 tokens e 2 regras; sem markup novo | **escolhida** |
| Substituir por um componente próprio | Markup novo, classe nova, CSS novo | recusada: uma caixa de mensagem não justifica componente |
| Reusar `--aviso-bg` | Nenhum token novo | recusada: confunde aviso com sucesso e apaga a diferença semântica |

Candidatos medidos (texto `--ink` sobre o fundo, borda sobre o fundo): claro sucesso `#EDF4E6`
13,70:1 / `#3F6B2E` 5,57:1; claro perigo `#FBEDEA` 13,49:1 / `#A8321F` 5,86:1; escuro sucesso
`#1E2A17` 12,16:1 / `#8DBB6E` 6,77:1; escuro perigo `#2E1B18` 13,22:1 / `#EE9A88` 7,47:1.

### 5.2 Ação principal

| Alternativa | Custo | Veredito |
|-------------|-------|----------|
| CSS em `.d-grid > .btn` acima de 576 px | uma regra, três botões | **escolhida** |
| Trocar `d-grid` por `d-flex` no markup | três edições | recusada: mesmo efeito com mais churn |
| CTA em pílula | uma regra | recusada: inverte a hierarquia (primário igual a secundário) |

### 5.3 Escala

`h1` de 2,5rem para 2,2rem e arte de 320 px para 280 px. O piso do `clamp` sobe de 1,9 para 1,8rem
para compensar a redução do teto e manter o título acima dos títulos de cartão (1,2rem).

### 5.4 Ritmo

Medido: campos com 1rem, abas e masthead com 1,5rem, bloco de observações com 1,5rem. Os degraus são
consistentes entre si; a transição para o resultado (`mt-5`) fica no rodapé e **não é tocada**
(`RN-08`). A decisão é verificar e registrar, não reescrever.

## 6. Fontes

- `src/templates/index.html` (masthead, alerta, formulários, cartões)
- `src/assets/app.css` (tokens, estados, botões, media query)
- `tests/test_banner_do_topo.py:270-298` (`RN-24`) e `:219-240` (`h1` visível)
- `tests/test_estilo_da_tela.py` (contraste dos selos, classes, rota da folha)
- `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`)
- `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md#3-regras-novas-que-a-feature-cria` (`RN-23`, `RN-24`)
- `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md#regras-alteradas`
- `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md`
- `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md`
- `_reversa_sdd/addenda/026-polimento-visual-da-tela.md#regras-sob-vigilância`
- `_reversa_sdd/recursos-da-tela/requirements.md#a-masthead`
- WCAG 2.1, critérios 1.4.3 e 1.4.11
