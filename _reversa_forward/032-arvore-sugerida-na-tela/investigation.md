# Investigation: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Escopo: por que a tela não pode chamar a cirurgia, por que Mermaid e não Graphviz, e como o desenho
> se encaixa no que o cartão já faz.

## 1. O número de gerações tem de sair de uma casa só

`arvore_sugerida` (feature `029`) faz quatro coisas: copia o grafo, corta a junção, injeta a cadeia e
confere o ramo. A tela precisa de **uma** delas — quantas gerações faltam — e ela é aritmética:

```
hiato = floor(geracoes_estimadas + 0.5) - a_up
```

`geracoes_estimadas` vem de `resultado["mrca_estimado"]["geracoes"]`; `a_up` de
`documental["degrees"]["a_up"]`. Nenhum grafo, nenhuma cópia, O(1).

Se a tela reimplementasse a fórmula, existiriam duas verdades: o cartão diria "3 gerações" e a
imagem diria "2", no mesmo caso, sem ninguém perceber. Por isso a função fica em
`core/cirurgia_do_grafo`, ao lado da fórmula original, e é chamada pelo núcleo do fluxo de DNA.

## 2. O custo de chamar `arvore_sugerida` por cartão

`desacoplar_identidade` faz `grafo.copy()`, que é O(V+E). Números medidos nesta sessão:

| Medida | Valor |
|--------|-------|
| Pessoas na árvore real | 35.460 |
| Cartões numa análise real | 142 |
| Cópias de grafo, se a tela chamasse a cirurgia | **142** |

Cada cópia é uma estrutura nova de dezenas de milhares de nós. Isso não é "um pouco lento": é a
requisição inviável. A tela deriva o número e desenha do caminho — o caminho tem dezenas de nós, não
dezenas de milhares.

## 3. Por que Mermaid, e não Graphviz

| # | Abordagem | Problema |
|---|-----------|----------|
| A | Servir o PNG/SVG gerado pelo Graphviz | Exige o binário `dot` **no servidor**; o container é `python:3.14-slim` + `pip install`, sem `apt-get`, e o `.dockerignore` é lista de permissão |
| B | Gerar a imagem sob demanda numa rota nova | Mesmo problema de A, mais uma rota, mais prazo de expiração e mais dado pessoal trafegando |
| C | Desenhar em Mermaid, no navegador | **Escolhida.** O cartão já desenha Mermaid, o Mermaid 10 já está carregado por CDN, e nada precisa ser instalado |

A consequência aceita: o desenho da tela é Mermaid, e o da imagem é Graphviz. São dois dialetos para
o mesmo conteúdo — e é por isso que as **cores e o rótulo da aresta são os mesmos** nos dois
(RN-03): o operador que comparar a tela com o PNG tem de reconhecer o mesmo código visual.

## 4. O que o Mermaid 10 oferece sem plugin

| Recurso | Como |
|---------|------|
| Cor de preenchimento e borda por classe | `classDef base fill:#a8e6cf,stroke:#4a7c68` + `n1["Doador"]:::base` |
| Tracejado | `classDef virt fill:#ffd3b6,stroke-dasharray:4 3` no nó; `-.->` na aresta |
| Aresta vermelha tracejada | `-.->|"rótulo"|` e `linkStyle <n> stroke:red,stroke-width:2px,stroke-dasharray:5 5` |
| Índice do `linkStyle` | é a ordem de definição das arestas — por isso a aresta rompida é emitida **por último** |

O `linkStyle` é a parte frágil: ele indexa por posição, não por id. Emitir a aresta rompida por
último é o que torna o índice previsível e testável.

## 5. O JS do cartão já resolve o "desenho dentro de bloco fechado"

`index.html:1244` ignora, no carregamento, os `.mermaid` que estão dentro de `details` fechado — um
container fechado tem tamanho zero e o Mermaid mede errado. E `index.html:1253-1263` pendura um
`toggle` em **qualquer** `details` que contenha `.mermaid`, re-renderizando ao abrir.

Consequência para esta feature: **o JavaScript não muda**. O bloco novo entra fechado e funciona
pelo mesmo caminho.

## 6. Fatos medidos no código

| Fato | Onde |
|------|------|
| O cartão já desenha o caminho documentado em Mermaid | `index.html:871-891` |
| O handler de `toggle` é genérico para `details` com `.mermaid` | `index.html:1253-1263` |
| O emissor Mermaid tem escape próprio, com lista branca | `reporting/mermaid_render.py:52-66` |
| `_mermaid_sid` produz id seguro `N_...` | `reporting/mermaid_render.py:31` |
| A fórmula do hiato está em `arvore_sugerida` | `core/cirurgia_do_grafo.py` (RN-07 da 029) |
| O dicionário do resultado já carrega `mrca_estimado` via `cm`/`geracoes` da validação | `core/dna_analysis.py` |

## 7. Alternativas de apresentação avaliadas

| # | Abordagem | Por que foi descartada (ou escolhida) |
|---|-----------|----------------------------------------|
| A | Só o resumo em texto | Perde o desenho, que era o pedido original |
| B | Só o diagrama | O número fica escondido atrás de um clique |
| C | Resumo no título + diagrama colapsável | **Escolhida.** Informação sem clique, desenho sob demanda |
| D | Tudo aberto | Soma um segundo diagrama aberto a um cartão com cinco seções |
| E | Substituir o diagrama documentado | São dois desenhos com propósitos diferentes |

## 8. Fontes externas

- Mermaid, flowchart (nós, `classDef`, estilos de aresta): <https://mermaid.js.org/syntax/flowchart.html>
- Mermaid, `linkStyle` e limites de índice: <https://mermaid.js.org/syntax/flowchart.html#styling-links>
- Bootstrap 5.3, `details`/`summary` não têm estilo próprio; o cartão usa CSS do projeto

## 9. Lacunas de investigação

- **Não foi medido** o tempo de `mermaid.run` com um caminho de 30 nós; o caminho real tem dezenas,
  e o custo é do navegador, não do servidor.
- **Não foi verificado** se o Mermaid 10 aceita `stroke-dasharray` dentro de `classDef` em todas as
  versões 10.x. Se não aceitar, o tracejado do nó virtual vira `style` inline — decisão do coding.
