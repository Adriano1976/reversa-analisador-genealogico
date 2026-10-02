---
schema_version: 1
id: OPP-20260929-H2YY
verb: simplify
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/caracterizacao-antes.txt
    - before-after/caracterizacao-depois.txt
    - safety-net/pytest-after-apply.txt
measurement:
  before: "Funcao de 191 linhas com 10 fechamentos de subgrafo posicionais (lines.append(\"end\")) e 10 literais subgraph espalhados, mais o bloco do casal ou ancestral duplicado em 12 linhas duas vezes. Indentacao maxima de 16 espacos"
  after: "Funcao de 178 linhas com 1 unico ponto de fechamento, dentro do helper subgrafo, e 1 unico literal subgraph. O bloco duplicado virou um helper. Indentacao maxima de 28 espacos, que e o custo do aninhamento lexico"
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/mermaid_render.py
    purpose: Troca o par posicional subgraph/end por um gerenciador de contexto e extrai o bloco do casal ou ancestral, sem mudar uma linha da saida
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-10-01T16:05:12-03:00
reversible_via: [CHG-001.diff]
---

## O que a propria oportunidade diz de si

A observacao final da OPP e literal: *"Esta e a transformacao com menor retorno de execucao da lista
deste contexto, e a de maior custo de leitura. E candidata natural a ficar por ultimo, ou a nao ser
feita."* O escopo aplicado foi escolhido no gate do plano, e a opcao de nao fazer foi oferecida duas
vezes.

## A logica antes

A funcao tinha 191 linhas e montava o texto do diagrama por acumulo literal numa lista, com quatro
funcoes internas ja existentes: `norm_ids`, `split_at`, `add_node` e `add_chain`.

Duas formas de complexidade acidental:

1. **Abertura e fechamento de subgrafo eram posicionais.** O par `subgraph X` mais `direction BT`
   aparecia 9 vezes e havia **10** chamadas de `lines.append("end")` espalhadas pelo fluxo. Nada no
   codigo ligava um `end` a sua abertura alem da ordem de execucao. Um `end` a mais muda a arvore do
   diagrama, o Mermaid continua sintaticamente valido, e o produto sai errado sem nenhum teste quebrar.
   E o risco que a OPP nomeia, e ela esta certa.
2. **O bloco do casal ou do ancestral aparecia duas vezes**, 12 linhas cada, identico a menos do
   sufixo das variaveis.

## O que e complexidade essencial, e nao foi tocado

A OPP e explicita: *"Parte da complexidade e regra de negocio legitima e congelada por paridade:
`split_path_by_marriage`, o par de conjuge no topo do ramo e as ancoras transparentes
`--- |Casamento| ---` sao comportamento especificado. A oportunidade e de forma, nao de regra."*

Tambem nao e acidental a assimetria entre os dois ramos. As colunas sao cortadas em ordem trocada de
proposito: no ramo `ESQ` a esquerda vem de `r1_down` e a direita de `r1_up_from_A`; no ramo `DIR` a
esquerda vem de `r2_up_from_B` e a direita de `r2_down`. Isso e regra, e e o motivo pelo qual a fusao
dos dois ramos (escopo 3) foi deixada de fora: um helper generico esconderia a troca em vez de
preserva-la.

## O que mudou

| Antes | Depois |
|-------|--------|
| `lines.append("subgraph X")`, `lines.append("direction BT")` e um `lines.append("end")` posicionado | `with subgrafo("X"):`, com abertura e fechamento num ponto so |
| 10 fechamentos posicionais | **1**, dentro do helper |
| 10 literais `subgraph` espalhados | **1** |
| O bloco do casal ou ancestral escrito duas vezes | `emit_couple_or_ancestor(...)`, escrito uma vez |

O helper central:

```python
@contextmanager
def subgrafo(header):
    """Abre o subgrafo, escreve a direcao e o fecha ao fim do bloco.
    ...
    Sem try/finally de proposito: `end` so e escrito se o corpo terminar, que
    e o comportamento da sequencia de append que este helper substitui.
    """
    lines.append("subgraph %s" % header)
    lines.append("direction BT")
    yield
    lines.append("end")
```

Sem `try/finally` de proposito: assim o `end` so e escrito se o corpo terminar, que e exatamente o
comportamento da sequencia de `append` substituida, inclusive no caminho de excecao.

## Uma correcao a proposta da OPP

Dos quatro itens que ela propoe, **o segundo ja estava implementado**: o `emit_chain(lines, seq)` que
ela pede existe no codigo como `add_chain`, nas linhas 161 a 166. Sobraram os itens 1 e 3, que sao os
dois helpers aplicados.

## Prova de equivalencia

Instrumento em `before-after/caracterizar.py`, que congela o sha256 da saida de cada caso em duas
frentes: `path_search` para todos os pares de cada fixture de GEDCOM, e
`generate_mermaid_graph_indirect_bridge` chamada **direto** para todo par com caminho indireto.

| Fixture | Pessoas | Pares | Fluxo | com ponte | Ponte direta |
|---------|---------|-------|-------|-----------|--------------|
| `affinity.ged` | 6 | 30 | 30 | 6 | 6 |
| `basic.ged` | 7 | 42 | 42 | 20 | 30 |
| `deep25.ged` | 25 | 60 | 60 | 28 | 56 |
| `mojibake_latin1.ged` | 3 | 6 | 6 | 4 | 6 |
| `no_name.ged` | 3 | 6 | 6 | 2 | 6 |
| `variants.ged` | 6 | 30 | 30 | 14 | 20 |
| **total** | **50** | **174** | **174** | **74** | **124** |

**298 casos.** O digest da caracterizacao e o mesmo antes e depois:

```
242512b451e243764b145461cd78ae329173c6a3695d35fc019ca67d92bb9eaf
```

E os dois arquivos JSON do corpus sao **byte a byte identicos**, o que e mais forte do que a igualdade
do digest: sao as 298 saidas comparadas uma a uma.

**O digest foi verificado como estavel** antes de ser usado como prova: rodei a caracterizacao duas
vezes sobre o codigo inalterado e o resultado foi identico, incluindo o JSON. Sem essa checagem, uma
diferenca de digest depois poderia ser ruido do instrumento, e nao regressao.

**Antes de aplicar**, o ensaio rodou o mesmo caracterizador contra um pacote espelho com a funcao nova:
digest identico. **Depois de aplicar**, o arquivo na arvore foi conferido por SHA-256 contra o espelho:
byte a byte igual.

**Suite completa**: 85 passed, 1 error, identico ao estado anterior. O erro e o `PermissionError` de
sandbox em `test_ensure_dirs_creates_uploads`.

**Harness de paridade diferencial**: **PARIDADE 100%, zero divergencia** nas 6 fixtures GEDCOM.

## A minha estimativa estava errada, e por isso o numero medido esta aqui

No plano eu estimei **≈ 45 linhas** economizadas para o escopo 1+2, somando ≈ 25 do subgrafo atomico
com ≈ 20 do bloco do casal. O medido foi:

| | Antes | Depois |
|---|-------|--------|
| Funcao | 191 linhas | **178** (−13) |
| Modulo | 296 linhas | **284** (−12) |

O erro foi contar a economia dos `append` substituidos e **nao contar as linhas dos proprios helpers**,
34 no total, quase todas docstring. Nao e diferenca de arredondamento: e uma estimativa mal feita, e o
escopo foi aprovado com esse numero errado na frente. O registro fica com o numero medido.

**O que justifica a mudanca, entao, nao e o tamanho:**

| Metrica | Antes | Depois |
|---------|-------|--------|
| Fechamentos posicionais de subgrafo | 10 | **1** |
| Literais `subgraph` espalhados | 10 | **1** |
| Indentacao maxima | 16 espacos | **28 espacos** |

A garantia estrutural e real: os 10 fechamentos que dependiam de posicao viraram um so, e um `end` a
mais deixa de ser possivel. O custo tambem e real: a indentacao mais profunda subiu de 16 para 28
espacos por causa dos quatro `with` aninhados, e isso nao estava medido no plano.

## O que nao foi tocado

Nao mudou: a assinatura de `generate_mermaid_graph_indirect_bridge`, a ordem de nenhuma linha emitida, as
cores, as ancoras transparentes, a regra de `split_path_by_marriage`, nem `_mermaid_sid`,
`_mermaid_label` ou `_LABEL_SEGURO`, que sao o contrato de escape da 5XGJ e do `BUG-20260929-J6PQ`.

Os quatro trechos internos que nao mudam (`norm_ids`, `split_at`, `add_node`, `add_chain`) foram
extraidos **byte a byte do original pelo AST** e reinseridos, em vez de redigitados, e o gerador confere
que cada um aparece exatamente uma vez no resultado.

## Estado do arquivo

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/mermaid_render.py` | 296 linhas | 284 linhas |
| `generate_mermaid_graph_indirect_bridge` | 191 linhas | 178 linhas |

## Reversao

Por `git apply -R CHG-001.diff`, ou por
`git checkout -- analisador-genealogico/reconstructed/mermaid_render.py`.

---
*Gerado pelo Reversa-Simplify em 2026-10-01.*
