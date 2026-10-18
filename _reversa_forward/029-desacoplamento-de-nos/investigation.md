# Investigation: desacoplamento de nós e gerações virtuais

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Escopo: por que a cirurgia é feita em cópia, por que cada geração virtual precisa de um nó-família,
> como o id do nó sintético é derivado e o que foi descartado.

## 1. O problema, em termos de grafo

A árvore carregada é um **grafo bipartido não dirigido** `pessoa ↔ família`:

```
P(donor) — F1 — P(pai) — F2 — P(avô) — F3 — P(MRCA)
```

Cada aresta liga uma pessoa a uma família; **não existe aresta pessoa↔pessoa**. Quem é genitor e quem
é filho não está na aresta: está no registro da família (`HUSB`, `WIFE`, `CHIL`) e, no grafo, apenas
na posição relativa. Medido em `src/parsers/gedcom_parser.py`: `g.add_node(pid, label=..., type="person")`,
`g.add_node(fam_id, label="Familia", type="family")` e `g.add_edge(...)` sem atributo de tipo.

Isso tem três consequências diretas para esta feature:

1. **Inserir uma geração entre duas pessoas exige dois nós novos, não um.** Um nó de pessoa sozinho
   não se liga a ninguém: precisa de uma família para fazer o papel de aresta.
2. **"Cortar a linha" não é remover uma aresta pessoa↔pessoa** — é remover a aresta entre a família
   de junção e o genitor histórico.
3. **Uma família é uma hiperedges disfarçada.** Um casal com `n` filhos é uma relação de aridade
   `2 + n`; a representação bipartida é a forma padrão de transformar hipergrafo em grafo simples. É o
   mesmo padrão que os bancos de dados usam para `N:N` e que os motores de propriedade de grafo usam
   para hiperarestas.

## 2. Alternativas avaliadas

| # | Abordagem | Como seria | Por que foi descartada (ou escolhida) |
|---|-----------|------------|----------------------------------------|
| A | Reescrever o `.ged` com registros `INDI`/`FAM` novos | Montar um GEDCOM sintético com os nós virtuais e gravar em `uploads/` | Escreveria arquivo derivado no diretório de uploads, que é **imutável por conteúdo** (ADR-17/ADR-32) e some da lista por posição (ADR-30). Um `.ged` com pessoa sem nome é lido por qualquer programa como registro corrompido, não como "geração desconhecida" |
| B | Mutar o grafo em memória e desfazer depois | `remove_edge` + `add_edge` na árvore carregada, com `try/finally` restaurando | Viola `ADR-24` (a árvore é **valor**) e transforma um erro no meio da cirurgia em árvore corrompida para o resto da requisição. Desfazer à mão é a classe de defeito que a feature 005 eliminou |
| C | Não cortar: só marcar a aresta como suspeita | Atributo `suspeita=True` na aresta, sem remover | Resolve o diagnóstico, não o pedido: o operador continua sem a árvore de correção. Foi oferecida em §9 do requirements e recusada |
| D | Copiar o grafo, cortar e injetar sobre a cópia | `grafo.copy()` + cirurgia + verificação pós-condição | **Escolhida.** O original fica intacto, a sugestão é um valor, e a verificação pós-cirurgia detecta qualquer vazamento |
| E | Representar a geração virtual como atributo de aresta, sem nó | `peso=3` na aresta família→pessoa | Não é grafo: perde a possibilidade de percorrer a cadeia sugerida e de exibir "Geração 1, 2, 3" como nós. Um peso não atravessa `shortest_path` nem `get_parents` |

## 3. Por que `copy()` e não `deepcopy()`

`Graph.copy()` devolve um grafo com **estrutura independente** (dicionários de adjacência novos) mas
com os **mesmos dicionários de atributos** de nó e de aresta. `deepcopy` copiaria também os atributos,
o que só é necessário se eles forem mutados — e a cirurgia não muta nenhum atributo de nó existente:
ela só adiciona nós e arestas.

Custo: `copy()` é O(V+E) em tempo e memória; `deepcopy` é O(V+E) em tempo com custo constante muito
maior (introspecção por objeto). Na árvore real de 35.460 pessoas e ~6.930 famílias, a diferença é
ordem de grandeza, não de porcentagem.

Existe `copy(as_view=True)`, O(1), mas devolve uma **visão somente leitura** — qualquer `add_edge`
levanta erro. Não serve.

## 4. Identidade dos nós sintéticos

Três candidatos foram considerados:

| Candidato | Problema |
|-----------|----------|
| `uuid4()` | Quebra o determinismo: duas execuções do mesmo caso produzem ids diferentes, e a comparação de sugestões (diff, teste, cache) deixa de funcionar |
| `id(objeto)` | Reciclado pelo CPython depois que o objeto morre. O próprio projeto já registrou essa armadilha em `core/documentary_relationship.py` (`_chave_de`), quando o cache de nomes passou a ser chaveado por conteúdo |
| `contador global` | Estado de módulo, proibido por `ADR-24`; e a ordem de criação passaria a depender do histórico do processo |

Escolha: **id derivado do conteúdo**, `VIRTUAL:<doador>:<ancestral>:<lado>:<k>`. É estável entre
execuções, entre processos e entre versões do Python, e torna a sugestão comparável por igualdade.

## 5. Arredondamento: por que não `round()`

`round()` no Python usa arredondamento **bancário** (meio para o par): `round(2.5) == 2` e
`round(3.5) == 4`. Em gerações, o valor `2.5` é comum — a mediana das meioses dividida por 2 cai em
meio inteiro com frequência —, e perder meia geração para baixo significa **uma geração a menos** na
sugestão, sem nenhum aviso.

A fórmula adotada é `floor(x + 0.5)`, meio para cima, explícita no código e citada na docstring. A
literatura de ponto flutuante chama a escolha de *round-half-up*, e é a expectativa do operador
quando lê "arredonde 2,5 para 3".

## 6. A sugestão não é uma árvore para os leitores existentes

Os leitores atuais (`get_parents`, `documentary_relationship`, `path_finding`) trabalham com a tupla
`(people, families, graph, child_to_family)`, e consultam **os dicionários**, não o grafo. Um nó
virtual existe só no grafo: `people.get("VIRTUAL:...")` devolve `None`, e `get_parents` devolveria
`[]` — degradação silenciosa, exatamente o padrão que a lacuna `L-24` descreve para o cache de nomes.

Por isso a saída é declarada como **grafo + metadados**, e não como uma `Arvore` utilizável. Quem
quiser validar a sugestão precisa de uma feature futura que materialize os registros.

## 7. Fatos medidos no código (não inferidos)

| Fato | Onde foi medido |
|------|------------------|
| O grafo é `nx.Graph` não dirigido, com `label` e `type` por nó | `src/parsers/gedcom_parser.py` |
| `find_ancestral_path` devolve **só pessoas**; as famílias são comprimidas | `src/core/path_finding.py:51-52` |
| O resultado de `validar_comparacao` **não** carrega `path.ids` nem `evidence` | `src/core/validator.py:253-271` |
| `validar_arquivos` monta o `documental` por pessoa e o descarta depois do uso | `src/application/validacao.py:186-222` |
| Nenhum teste da `028` compara o conjunto exato de chaves do retorno | `tests/test_validacao_de_arquivos.py` (asserções por chave) |
| `networkx==3.7` já é dependência de runtime | `requirements.txt:22`; `_reversa_sdd/dependencies.md` |

## 8. Padrões aplicáveis

- **Copy-on-write**: a transformação devolve valor novo e nunca altera a entrada.
- **Pós-condição verificada em execução** (não só em teste): comparar o ramo protegido depois da
  cirurgia é o equivalente a uma transação com *check* antes do *commit*; se falhar, o resultado é
  descartado em vez de entregue.
- **Idempotência**: mesma entrada, mesma saída — o que permite comparar duas sugestões com `==` e
  detectar mudança de comportamento em revisão.
- **Rótulo honesto para dado derivado**: `origem="estimado"` e faixa em vez de data exata. É o mesmo
  critério que o projeto usa para `plausible: None` ("não sei" não é "falso").

## 9. Fontes externas

- NetworkX, `Graph.copy` — semântica de cópia rasa, atributos compartilhados, `as_view` somente
  leitura: <https://networkx.org/documentation/stable/reference/classes/generated/networkx.Graph.copy.html>
- NetworkX, estruturas de grafo bipartido e uso de nós intermediários como aresta:
  <https://networkx.org/documentation/stable/reference/algorithms/bipartite.html>
- Python, `round` e arredondamento bancário: <https://docs.python.org/3/library/functions.html#round>
- GEDCOM 5.5.1, especificação dos registros `INDI` e `FAM` (por que não existe registro de "pessoa
  desconhecida" utilizável): <https://gedcom.io/specifications/ged551.pdf>
- Fenner, J. N. *Cross-cultural estimation of the human generation interval for use in genetics-based
  population divergence studies*. Am J Phys Anthropol. 2005;128(2):415–423. DOI
  [10.1002/ajpa.20188](https://doi.org/10.1002/ajpa.20188) — sustenta a variabilidade do intervalo de
  geração usado pela `028` e herdado aqui.
- Shared cM Project 4.0 — tabela de cM por relação, em `src/core/relationship_hypotheses.py`; a
  estimativa de gerações vem de `core.validator.estimar_mrca`.

## 10. Lacunas de investigação

- O custo real de `graph.copy()` na árvore de 35.460 pessoas **não foi medido**. Está previsto como
  medição no teste de integração; se passar de ~1 s, o plano precisa reavaliar a cópia total.
- Não foi investigado se algum consumidor futuro precisaria dos nós virtuais em `people`. Hoje
  nenhum precisa, e `D-11` registra a limitação.
