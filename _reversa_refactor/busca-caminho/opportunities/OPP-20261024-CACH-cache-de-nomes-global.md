---
schema_version: 1
id: OPP-20261024-CACH
display_number: 52
context: busca-caminho
verb: decouple
title: Dois caches para o mesmo problema, e o de nomes é estado de módulo entre requisições
target:
  files:
    - src/core/documentary_relationship.py
  symbol: _INDICE_DE_NOMES, _indice_por_nome, _indice_de_filhos
smell: >
  O módulo memoiza duas varreduras caras do mesmo jeito errado e certo ao mesmo tempo. O
  índice pai para filhos é preso ao grafo da árvore (`setattr`), morre com ela e não
  atravessa requisições. O índice nome para ids é um dicionário mutável de módulo, com
  dois campos que precisam mudar juntos e um deles relido do global no `return`.
roi:
  confidence: yellow
  impact: >
    É o único ponto do arquivo que compartilha estado entre requisições. O projeto roda
    com quatro threads (`ANALISADOR_THREADS`) e a corrida entre requisições é a única
    lacuna crítica aberta (`L-16` / `M-03` / `P-02`). O `return` relê o global em vez de
    devolver o mapa que acabou de construir, então uma troca de árvore no meio da função
    faz a requisição receber o índice de outro GEDCOM.
  cost: low
  est_return: >
    Um único mecanismo de memoização por árvore, com a troca do índice feita por
    substituição atômica de uma referência, e o mapa devolvido vindo da variável local.
state: applied
traceability:
  soul: [.reversa/soul.md#3-decisoes-fundadoras, .reversa/soul.md#e7-parentesco_documental]
  specs:
    - _reversa_sdd/busca-caminho/design.md
    - _reversa_sdd/busca-caminho/requirements.md
---

## Antes observado

Dois mecanismos, no mesmo arquivo, para o mesmo problema:

| Índice | Onde vive | Chave de invalidação | Alcance |
|---|---|---|---|
| pai para filhos (`_indice_de_filhos`, linha 222) | atributo do grafo `arvore[2]`, via `setattr` na linha 228 | o próprio objeto grafo | a requisição dona da árvore |
| nome para ids (`_indice_por_nome`, linha 333) | dicionário de módulo `_INDICE_DE_NOMES`, linha 309 | `(len(people), primeira chave, última chave)` | o processo inteiro, todas as threads |

O segundo foi desenhado para sobreviver à troca de GEDCOM e por isso é global. A
consequência está nas três últimas linhas da função:

```python
        _INDICE_DE_NOMES["mapa"] = mapa
        _INDICE_DE_NOMES["chave"] = chave
    return _INDICE_DE_NOMES["mapa"]
```

A linha 351 relê o dicionário de módulo em vez de devolver `mapa`. Entre a escrita da
linha 349 e a leitura da linha 351 há espaço para outra thread publicar o mapa dela, e
então esta requisição devolve ids de outro arquivo. O comentário das linhas 54 a 71
explica, com medição, por que a chave não pode ser `id()`, mas não trata do caso de duas
requisições simultâneas com árvores diferentes.

Não é hipótese de leitura: o projeto declara quatro threads no servidor e a corrida entre
requisições concorrentes é a lacuna crítica que a extração de 2026-10-05 registrou como a
única ainda aberta.

## O que já está provado e o que não está

`tests/test_confrontacao_gedcom_dna.py` cobre a invalidação em sequência (o caso `test_6d`,
com dois GEDCOMs carregados um depois do outro). Nenhum teste monta duas threads com
árvores distintas, então a janela entre as linhas 349 e 351 não tem guarda.

## Transformação proposta

1. guardar os dois campos numa referência única e imutável, a tupla `(chave, mapa)`, e
   trocá-la por atribuição simples. Em CPython a atribuição de um nome é atômica, então
   quem lê vê o par inteiro ou o par anterior, nunca um campo novo com um campo velho;
2. ler a referência uma vez para uma variável local, comparar a chave e devolver o mapa
   dessa mesma leitura;
3. no caminho de construção, devolver o `mapa` local, sem reler o global;
4. opcionalmente, alinhar o índice de filhos ao mesmo formato, para que os dois deixem de
   parecer mecanismos diferentes.

O tipo `_CacheDeNomes` (TypedDict, linha 296) sai nesta transformação: um par de valores
trocado junto não é um dicionário de dois campos independentes, é um valor só.

## Fronteira de comportamento

Em execução single-thread nada muda: a mesma chave, o mesmo mapa, a mesma ordem de
inserção. O que muda é apenas o instante em que duas requisições concorrentes disputam a
publicação do índice, que hoje pode devolver o mapa errado. Esta é a única alteração de
comportamento do conjunto e ela é uma correção, no mesmo espírito da `OPP-20261023-ESTD`.

## Rede de segurança exigida

- suíte completa verde antes e depois, sem afrouxar asserção;
- teste de caracterização do caminho sequencial (duas árvores, invalidação em ordem) para
  que a correção não vire regressão silenciosa;
- teste novo com duas threads alternando árvores, com barreira no ponto de escrita, para
  provar a janela fechada. Sem esse teste a transformação fica 🟡 para sempre.

## Por que não a implementação alternativa

Prender o índice de nomes ao grafo, como o de filhos, eliminaria o estado de módulo por
completo e é a solução mais limpa. Foi descartada como primeiro passo porque a varredura
de 35 mil pessoas custa cerca de 0,9 s e o índice existe justamente para não pagá-la a
cada árvore: preso ao grafo, cada requisição pagaria de novo. O ganho de isolamento não
compensa a perda medida.

## Aplicada em 2026-10-24

Aprovada em plano e em diff, aplicada pelo `/reversa-decouple` na mesma data. O índice
passou a ser a tupla `(chave, mapa)`, publicada por uma atribuição, e o retorno vem da
referência lida uma vez. Saíram o `TypedDict _CacheDeNomes` e o import de `TypedDict`.

| Antes | Depois |
|---|---|
| 1 objeto mutável de módulo, 2 campos, 2 escritas separadas | 0 objetos mutáveis, 1 valor imutável, 1 atribuição |
| 2 leituras do global por chamada, uma delas relendo a própria escrita | 1 leitura, feita uma vez |
| 0 guardas sobre a janela | 3 guardas estruturais e 1 invariante sob carga |
| 1629 testes | 1635 testes, 9 pulados, mesmas 9 exclusões |

O defeito foi provado antes da correção e está em
[`before-after/prova-do-defeito.py`](../transformations/OPP-20261024-CACH-cache-de-nomes-global/before-after/prova-do-defeito.py).
O registro completo está no
[`transformation.md`](../transformations/OPP-20261024-CACH-cache-de-nomes-global/transformation.md).

---
*Gerado pelo Reversa-Refactor em 2026-10-24, na auditoria de `src/core/documentary_relationship.py`.*
