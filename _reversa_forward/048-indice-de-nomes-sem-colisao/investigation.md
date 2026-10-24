# Investigation: índice de nomes sem colisão entre árvores

> Identificador: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`

## 1. O defeito, e como ele foi confirmado

`_chave_de(people)` devolvia `(len(people), primeira chave, última chave)`. O experimento de
2026-10-10 usou duas árvores de 4 pessoas com a mesma chave `(4, '@I1@', '@I9@')` e xrefs
interiores diferentes. O dossiê da segunda árvore respondeu `exact_count: 1` citando `@I2@` —
que **não existe nela** — e `person_summary` degradou para `"Sem Nome"`, sem levantar nada.

O gatilho medido não depende do conteúdo: **depende só da contagem**. Duas exportações do mesmo
exportador com o mesmo número de pessoas e os mesmos extremos colidem.

## 2. Alternativas avaliadas

| Alternativa | Veredito | Por quê |
|---|---|---|
| **Chave derivada do conteúdo (nomes)** | descartada | a varredura de nomes custa o mesmo que construir o índice (~0,9 s por 35 mil pessoas); a "correção" pagaria o custo que o cache existe para evitar |
| **Chave com todos os xrefs** | descartada | reexportação mantém os xrefs e muda os dados: duas versões do mesmo arquivo colidiriam |
| **Reter a árvore anterior e comparar por identidade** | descartada | prender `people` da árvore passada custa centenas de MB (a feature 047 mediu ~337 MB por árvore) |
| **`id()`** | descartada | é reciclado; o documento do módulo já proíbe explicitamente |
| **Índice preso ao grafo da árvore** | **escolhida** | chave zero, colisão impossível, e o índice morre com a árvore |

## 3. Precedente dentro do repositório

Duas estruturas já usam o padrão: `fichas_da_pessoa._indice_de_filhos` (prendendo o mapa ao grafo)
e `matching._ATRIBUTO_DOS_INDICES` (feature 047, índices de matching). A 048 fecha o trio: depois
dela, **nenhum** derivado de árvore é estado de módulo.

## 4. O que muda nos testes existentes

`tests/test_indice_de_nomes_do_documental.py` foi escrito em 2026-10-24 para guardar a **corrida**
entre duas requisições (a publicação em dois tempos do dicionário). Ele lê o módulo por AST, exige
a tupla `_INDICE_DE_NOMES` e proíbe subscrito dentro da função. Com o estado de módulo removido,
essas guardas deixam de ter objeto: não há publicação, não há janela, não há o que trocar.

O arquivo é reescrito para guardar o invariante novo: **cada árvore tem o seu mapa**, e duas
árvores de mesma assinatura não se contaminam.

## 5. Riscos que continuam fora

- `L-25` (ordem de `common_ancestors` dependente de `PYTHONHASHSEED`) não é tocado aqui.
- `L-20` (fichas completas por resultado) também não.

## 6. Fontes

- `_reversa_sdd/domain.md#7-lacunas` (`L-24`)
- `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas`
- `_reversa_sdd/flowcharts/busca-caminho.md#13`
- `_reversa_sdd/busca-caminho/tasks.md` (`TT-20`)
- `_reversa_sdd/gaps.md#3-lacunas-moderadas`
- `_reversa_sdd/addenda/047-cache-dos-indices-da-arvore.md`
