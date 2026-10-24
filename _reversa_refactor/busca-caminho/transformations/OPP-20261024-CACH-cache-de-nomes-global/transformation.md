---
schema_version: 1
id: OPP-20261024-CACH
verb: decouple
state: applied
safety_net:
  kind: characterization
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
    - before-after/prova-do-defeito.txt
    - CHG-001.diff
measurement:
  before: >
    1 objeto mutável de módulo com 2 campos publicados por 2 escritas separadas; 2 leituras
    do global por chamada, uma delas relendo o valor que a função acabou de gravar; 1
    intervalo em que o par pode estar inconsistente; 0 testes que exercitam duas árvores
    concorrentes.
  after: >
    0 objetos mutáveis de módulo; 1 valor imutável de 2 posições publicado por 1 atribuição;
    1 leitura do global por chamada, feita uma única vez no início; 0 intervalos de
    inconsistência possíveis por construção; 3 guardas estruturais e 1 teste de invariante
    sob carga.
change_set:
  - chg: CHG-001
    file: src/core/documentary_relationship.py
    purpose: >
      o índice de nomes vira a tupla (chave, mapa), publicada por uma atribuição atômica,
      e o retorno passa a vir da referência lida uma vez; sai o TypedDict `_CacheDeNomes`
      e o import de `TypedDict`
  - chg: CHG-002
    file: tests/test_indice_de_nomes_do_documental.py
    purpose: >
      arquivo novo com 3 guardas estruturais, 2 de caracterização e 1 invariante sob carga;
      reversão = remover o arquivo
approval:
  by: user
  at: 2026-10-24T01:50:00-03:00
reversible_via: [CHG-001.diff]
---

## O que estava acoplado

O acoplamento não era de importação: o módulo importa cinco módulos do projeto e é
importado por quinze, e isso não mudou. O acoplamento era o **estado**: um dicionário de
módulo com dois campos que precisavam mudar juntos, escrito em dois tempos.

```python
_INDICE_DE_NOMES: _CacheDeNomes = {"chave": (), "mapa": {}}
...
        _INDICE_DE_NOMES["mapa"] = mapa     # linha 349
        _INDICE_DE_NOMES["chave"] = chave   # linha 350
    return _INDICE_DE_NOMES["mapa"]         # linha 351, relê o global
```

Duas consequências, as duas medidas antes da transformação em
[`prova-do-defeito.txt`](before-after/prova-do-defeito.txt):

1. entre as linhas 349 e 350 o par pode ficar com a chave de um GEDCOM e o mapa de outro,
   e essa combinação **fica** no cache, envenenando as chamadas seguintes;
2. a linha 351 relê o global em vez de devolver o mapa que a função montou, então a
   requisição pode receber o mapa que outra publicou no intervalo.

A prova foi determinística: a thread A foi estacionada dentro do `__setitem__` de `chave`
e a thread principal publicou o índice de outra árvore antes de liberá-la. A requisição
que pediu a árvore Alfa recebeu os três registros Beta.

## O que foi feito

`CHG-001` troca o dicionário por uma tupla única `(chave, mapa)`:

- a publicação passa a ser uma atribuição de nome, atômica em CPython: quem lê vê o par
  inteiro ou o par anterior;
- a leitura do global acontece uma vez (`publicado = _INDICE_DE_NOMES`) e é dela que sai
  o retorno (`publicado[1]`);
- o `TypedDict` `_CacheDeNomes` e o import de `TypedDict` saem, porque descreviam
  exatamente a forma que permitia a publicação em dois tempos.

`CHG-002` acrescenta `tests/test_indice_de_nomes_do_documental.py` com seis testes:

| Teste | Tipo | Papel |
|---|---|---|
| subscrito no índice dentro de `_indice_por_nome` | AST | falha no código de ontem (linhas 345, 349, 350, 351), passa no de hoje |
| declaração de módulo é tupla de dois | AST | falhava no código de ontem (dict) |
| índice é tupla de dois em execução | tempo de execução | falhava no código de ontem |
| duas chamadas, mesmo mapa | caracterização | fixa o acerto do cache |
| árvore nova invalida | caracterização | fixa a troca de chave |
| invariante sob carga | estresse | nenhuma requisição recebe índice de outra árvore |

A guarda é estrutural porque o defeito é da implementação, não do resultado: nenhuma
asserção de saída distingue, de forma determinística, um mapa correto de um mapa trocado
sem forçar o entrelaçamento dentro da janela. O teste de estresse **não** é a guarda, e o
docstring dele diz isso com a medição: 240 tentativas com a janela aberta não
reproduziram o entrelaçamento.

## Fronteira de comportamento

Uma requisição por vez e duas árvores em sequência dão exatamente o mesmo resultado:
mesmo mapa, mesma ordem de inserção, mesma invalidação por conteúdo. A única diferença
observável está na concorrência, e é a correção.

`_chave_de`, a assinatura de `_indice_por_nome`, o nome do estado e os dezoito nomes de
`__all__` continuam iguais. Nada mais do módulo foi tocado.

## Prova

| Verificação | Resultado |
|---|---|
| `git apply --check CHG-001.diff` antes de aplicar | aplica limpo, sem fuzz |
| `git apply --check --reverse CHG-001.diff` depois de aplicar | passa: o arquivo é byte a byte o do patch |
| `git diff --no-index` entre o teste estagiado e o instalado | vazio: byte a byte igual |
| Sonda do defeito depois da transformação | `type(_INDICE_DE_NOMES) = tuple`; o espião não é mais instalável |
| Arquivo novo isolado | 6 passed |
| Suíte completa | **1635 passed, 9 skipped** em 128,08 s (antes: 1629, 9, 102,82 s) |

O arquivo do módulo passou de 782 para 777 linhas.

## O que esta transformação não resolve

O índice continua sendo estado de módulo, compartilhado pelo processo. A diferença é que
agora ele é um valor imutável trocado de uma vez, e não dois campos mutáveis escritos em
dois tempos. Prender o índice ao grafo, como o índice de filhos, eliminaria o estado de
módulo por completo, mas pagaria a varredura de 35 mil pessoas a cada árvore carregada; a
medição está na oportunidade e a decisão de não fazer está registrada.
