# Correção de defeito — a busca de ancestral comum perdia caminho quando os dois lados tinham profundidades diferentes

**Data:** 2026-10-13
**Tipo:** defeito de algoritmo no núcleo, corrigido no código
**Arquivos alterados:** `src/core/path_finding.py`, `src/core/documentary_relationship.py`
**Teste novo:** `tests/test_busca_de_ancestral_comum.py`

## O sintoma que o operador viu

O cartão de `Therezinha Carvalho do Nascimento Souza` (31,9 cM, kit `NG2749622`) mostrava:

> **Caminho genealógico no GEDCOM:** *nenhum caminho encontrado*
> **Parentesco documental não encontrado**

O `GEDCOM` **tem** o caminho. A pessoa é filha de Estanislau Rodrigues do Nascimento e
Herotildes Menoquina de Carvalho (`@F2705@`) e mãe da Soraia (`@F2732@`) — os vínculos estão
no arquivo, e o caminho até `Adriano Santos` tem **16 nós**.

## A causa: o encontro era testado na saída da fila, e não no descobrimento

`find_ancestral_path` é uma BFS bidirecional que sobe por pais a partir das duas pessoas. O
teste de encontro ficava **só** no `popleft`:

```python
curr_id, path = q1.popleft()
if curr_id in visited2:        # <- teste AQUI, na saída
    return ...
for p_id in get_parents(arvore, curr_id):
    if p_id not in visited1:   # <- e NÃO aqui, na descoberta
```

Medido no `Arvore_Unificada_Oficial_V1_2.ged`:

| lado | ancestrais alcançados | profundidade |
|---|---|---|
| `Adriano Santos` (`@I6f405a00@`) | 149–190 | até 16 |
| `Therezinha` (`@Ied60620a@`) | 67 | até 7 |

A fronteira da Therezinha **esvazia** na oitava iteração — ela terminou de subir. A da raiz
ainda expandia e só chegaria à região comum na nona. Como o laço fazia
`if not q_size: break` quando **uma** fila esvaziava, o lado da raiz era abandonado.

E o pior: os quatro ancestrais comuns **já estavam nos dois conjuntos de visitados** no
momento em que a busca desistiu. As duas buscas se atravessaram sem se encontrar.

```
interseccao v1 & v2: 4
   Gonçalo de Souza Vieira    v1=9 passos, v2=6 passos
   Leonarda Vieira Dantas     v1=9 passos, v2=6 passos
   Águeda de Oliveira         v1=9 passos, v2=6 passos
   Manoel da Silva Vieira     v1=9 passos, v2=6 passos
```

**`MAX_DEPTH` não era o problema.** Subir o teto para 40, 60, 80, 120 e 200 não muda o
resultado — quem interrompe a busca é a fila vazia, não o limite de iterações. Por isso o teto
continua **20**: mexer nele esconderia a causa.

## A correção

Duas mudanças, ambas em `find_ancestral_path`:

1. **O encontro passa a ser testado no descobrimento.** Assim que um pai é alcançado, ele é
   comparado com a fronteira oposta — antes de qualquer coisa ser enfileirada.
2. **Uma fila vazia não encerra mais a busca.** Aquele lado terminou de subir; o outro pode
   ainda estar subindo. Quem encerra é o teto de iterações, ou as **duas** filas vazias.

   Consequência declarada: `MAX_DEPTH` conta **iterações**, e cada iteração agora processa os
   dois lados em vez de parar no primeiro que esvazia. Na prática isso dobra o alcance efetivo
   de busca — o que **só pode encontrar mais**, nunca menos. Um par que o código antigo achava
   é achado antes ou na mesma profundidade.

O caminho concatenado (`caminho1 + [encontro] + caminho2`, com `caminho2` já na ordem de
subida) foi preservado **exatamente** como estava: é o que os testes de caracterização
congelam, e girar a segunda metade mudaria a ordem exibida dos descendentes.

### Por que é seguro

A correção é **puramente aditiva**: só encontra pares que já têm ancestral comum no arquivo.
Não pode criar falso positivo nem derrubar um "não encontrado" que fosse correto. `MAX_DEPTH`,
o parser, o grafo e o `documentary_relationship` acima dela não mudaram.

## A mensagem que mandava o operador olhar o lugar errado

Em `documentary_relationship.py`, a observação de "sem caminho" dizia:

> "Isso não prova ausência de parentesco: **pode faltar vínculo no GEDCOM**."

Com o defeito, a mensagem apontava para o GEDCOM quando o problema era o algoritmo. Reescrita:

> "Isso não prova ausência de parentesco: as duas podem ser ligadas por irmandade, por outro
> ramo colateral que o GEDCOM não registra, ou por um vínculo que falte no arquivo."

## Consequência medida

### Nos 62 cartões da análise real: **7 cartões**, nenhuma regressão

| Nome | cM | Caminho |
|---|---|---|
| Maria do Carmo Teixeira | 34,5 | 16 nós |
| **Therezinha C. do N. Souza** | 31,9 | **16 nós — "Primos de 5º grau com 3× remoção", 15 meioses** |
| Manoel Vieira da Silva (×2 cartões) | 25,4 | 12 e 10 nós |
| Maria Vieira de Souza | — | 15 nós |
| Margarida | 21,6 | 13 nós |
| *Primo Alves de Santana | 11,2 | 16 nós |
| JOSÉ VICENTE de Souza | — | 11 nós |

Balanço completo, com o **corpo do código antigo** rodado lado a lado para reconstruir o
"antes", sem tocar no código de produção:

| | cartões |
|---|---|
| já tinham caminho e continuam com ele | 4 |
| não tinham e continuam sem | 51 |
| **ganharam caminho** | **7** |
| **perderam caminho (regressão)** | **0** |

Os status finais: `not_found` 51, `found` 8, `ambiguous` 3. Além do parentesco, os que ganharam
passam a exibir **grafo Mermaid** — `_montar_diagrama` devolve `None` quando não há caminho,
então o cartão também ficava sem a rede visual.

### Na árvore inteira: dois terços dos parentescos encontrados

Os 62 cartões passam pelo funil do matching por nome e cobrem só parte da árvore. Numa amostra
determinística de **886 pessoas** (1 a cada 40 das 35.460), com a raiz `Adriano Santos`:

| | pessoas |
|---|---|
| já tinham caminho e continuam com ele | 22 |
| **ganharam caminho** | **38** |
| sem caminho nos dois códigos | 826 |
| **perderam** | **0** |

Dos **60 pares** da amostra que têm ancestral comum e estão dentro do teto, **38 (63%)** o
código antigo não encontrava. O defeito não era raro: era o caso **comum** — só funcionava
quando os dois lados tinham profundidades parecidas.


## O que **não** mudou

- `MAX_DEPTH = 20`, `MAX_HOPS = 40`, o grafo pessoa↔família e o parser.
- Nenhum par que já era encontrado mudou de caminho ou de ancestral comum: os testes de
  caracterização (`tests/test_characterization_matching.py`,
  `tests/test_characterization_mermaid.py`), `tests/test_path_search.py` e
  `tests/test_confrontacao_gedcom_dna.py` continuam verdes, sem edição.
- A relação entre DNA e documento: o DNA continua sem alterar o parentesco documental.

## O teste que prende a correção

`tests/test_busca_de_ancestral_comum.py`, com uma árvore sintética montada em memória:
cadeia de **10 níveis** de um lado e **4** do outro, ligadas por um ancestral comum no topo.

O ponto delicado do arquivo é a classe `TestODefeitoEraRealmenteExercitado`: ela roda o
**corpo do código antigo** sobre a mesma árvore e exige que ele devolva `None`. Sem essa
prova, uma árvore **simétrica** passaria nos dois códigos e todos os outros testes do arquivo
estariam medindo nada — a assimetria de profundidade é o que reproduz o defeito.

Dois testes medem a **continuidade** do caminho (cada salto acima do ancestral comum é um
`pai-de`; abaixo dele, a relação se inverte), que é o que separa "achou um caminho" de "achou
o caminho": uma concatenação errada das duas metades passaria nos testes de tamanho.

## Nota de método

Três medições deste trabalho nasceram **erradas** e foram corrigidas contra o comportamento
observado, não contra a suposição:

1. **"subir por pais não liga um ancestral a quem está abaixo dele"** — está errado. A busca
   sobe a partir de quem está abaixo e **chega** ao ancestral; o caminho existe e a segunda
   metade desce. O nome `common_ancestor` descreve o **nó**, não o sentido da travessia.
2. **o ramo raso da árvore sintética** — eu supus que a constante `RASO_P2` controlava a
   profundidade, mas era a construção que a determinava (uma família por salto). A constante
   passou a ser derivada, para não poder divergir.
3. **o alcance do defeito: 5 cartões** — a primeira medição cruzou os pares por `csv_name` num
   dicionário, e **dois cartões do mesmo par** (`Manoel Vieira da Silva` e `Manoel da Silva
   Vieira`) colapsaram numa chave só. E a ordenação de apresentação **muda** quando cartões
   ganham caminho, então os números de "antes" e "depois" se deslocaram entre as duas listas.
   A medição correta (7 cartões) compara por **pessoa**, rodando as duas buscas sobre os
   mesmos pares — e a varredura por amostra mostrou que o alcance real é bem maior que os
   cartões: **63% dos parentescos encontráveis** estavam sendo perdidos.

