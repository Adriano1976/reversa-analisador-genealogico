---
schema_version: 1
id: OPP-20261024-FLUX
verb: restructure
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/prova-de-equivalencia.txt
    - before-after/controle-negativo.txt
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
    - CHG-001.diff
measurement:
  before: >
    `documentary_relationship` com 102 linhas: tres lacos e quatro blocos de aviso, cada um
    montando a mensagem no meio do percurso. O aviso de homonimo escrito em dois lugares.
  after: >
    `documentary_relationship` com 54 linhas, oito funcoes de intencao nomeada de 3 a 16
    linhas, e a mensagem de homonimo em um lugar so. A ordem dos avisos passou a caber numa
    tupla de tres construtores.
change_set:
  - chg: CHG-001
    file: src/core/documentary_relationship.py
    purpose: >
      Extract Method em oito pontos (evidencia, aviso de data, avisos de data, alternativos,
      colapso e os tres construtores de aviso) e Consolidate Duplicate Conditional Fragments
      no aviso de homonimo, compartilhado com `documental_nao_encontrado`
approval:
  by: user
  at: 2026-10-24T01:58:00-03:00
reversible_via: [CHG-001.diff]
---

## Os cheiros, e a refatoracao de cada um

| Cheiro | Refatoracao |
|---|---|
| Long Method, 102 linhas | Extract Method, em oito pontos |
| Mensagem de homonimo escrita em `documentary_relationship` e em `documental_nao_encontrado` | Extract Method e Consolidate Duplicate Conditional Fragments |
| Tres blocos com a forma `if x: avisos.append({...})` | construtor que devolve `dict | None` |
| `comuns`, `alternativos` e `colapso` aparecendo no meio da montagem | funcoes nomeadas, com o nome da intencao |

## Os oito nomes que a funcao ganhou

| Funcao | Linhas | O que ela responde |
|---|---|---|
| `_aviso_de_homonimo` | 16 | identidade ambigua, com o acrescimo que so faz sentido havendo caminho |
| `_evidencia_do_caminho` | 9 | a evidencia de cada salto, subindo ate o MRCA e descendo depois |
| `_aviso_de_data_impossivel` | 11 | o aviso de um salto com idade fora da faixa |
| `_avisos_de_data` | 3 | um aviso por salto implausivel |
| `_caminhos_alternativos` | 11 | os caminhos que passam por outros ancestrais comuns |
| `_colapso_de_pedigree` | 8 | os ancestrais alcancados por mais de uma cadeia |
| `_aviso_de_caminhos_multiplos` | 10 | o aviso de que existem caminhos alem do exibido, ou None |
| `_aviso_de_colapso` | 11 | o aviso de colapso, citando no maximo tres ancestrais, ou None |

## O corpo que sobrou

```python
    if a_id not in arvore[0] or b_id not in arvore[0]:
        return {...}

    path, comum = find_ancestral_path(arvore, a_id, b_id, max_depth=MAX_DEPTH)
    homonimos = homonyms or {}
    if not path:
        return documental_nao_encontrado(arvore, a_id, b_id, homonimos=homonimos)

    indice = path.index(comum) if comum in path else 0
    deg_a, deg_b = indice, len(path) - 1 - indice
    parentesco = documentary_label(deg_a, deg_b)

    evidencia = _evidencia_do_caminho(arvore, path, indice)
    comuns = find_all_common_ancestors(arvore, a_id, b_id)
    alternativos = _caminhos_alternativos(arvore, a_id, b_id, comuns, comum)
    colapso = _colapso_de_pedigree(arvore, a_id, comuns)

    avisos = _avisos_de_data(evidencia)
    for aviso in (
        _aviso_de_caminhos_multiplos(alternativos),
        _aviso_de_colapso(colapso),
        _aviso_de_homonimo(homonimos),
    ):
        if aviso is not None:
            avisos.append(aviso)

    return {...}
```

## Medicao

| Medida | Antes | Depois |
|---|---|---|
| Linhas de `documentary_relationship` | 102 | **54** |
| Linhas de `documental_nao_encontrado` | 58 | 52 |
| Lugares em que a mensagem de homonimo existe | 2 | **1** |
| Blocos `if ...: avisos.append({...})` | 4 | **0** |
| Ordem dos avisos legivel em um lugar | nao | sim, na tupla de tres construtores |
| Linhas do modulo | 780 | 821 |

O modulo cresceu 41 linhas: 108 insercoes contra 67 remocoes. Oito funcoes novas com docstring
e espacamento proprio custam mais linhas do que os blocos que substituem. O que diminuiu foi
a concentracao: a funcao que ninguem conseguia ler de uma vez virou uma sequencia de oito
passos nomeados.

## Prova de equivalencia

Comparacao da versao de HEAD com a do modulo, dicionario por dicionario, incluindo o texto de
cada aviso e a ordem da lista:

| Corpus | Comparacoes |
|---|---|
| Arvore real, 35.459 pessoas | 3.606 |
| Colapso sintetico (X e Y, filhos M, W e G; A filho de M e W; B filho de G) | 34 |
| `basic.ged`, `deep25.ged`, `variants.ged`, `affinity.ged`, `no_name.ged`, `mojibake_latin1.ged` | 204 |
| `documental_nao_encontrado`, 6 arvores x 6 pares x 2 dossies | 84 |
| **Total** | **3.928, com 0 divergencia** |

Cada comparacao foi feita com quatro dossies de homonimos: nenhum, o dossie real de dois
nomes repetidos da arvore, e um dossie ambiguo montado a mao.

Os seis codigos de aviso foram exercitados, e a contagem sai da propria execucao:

| Codigo | Ocorrencias comparadas |
|---|---|
| `caminhos_multiplos` | 2.941 |
| `homonimo` | 2.815 |
| `sem_caminho` | 440 |
| `data_impossivel` | 250 |
| `colapso_de_pedigree` | 148 |
| `pessoa_ausente` | 4 |

**O instrumento foi calibrado antes**: com uma diferenca injetada no rotulo, a mesma prova
acusou 3.844 divergencias em 3.928 comparacoes, e mostrou campo a campo o que mudou. Sem esse
controle, "0 divergencias" nao seria prova de nada.

## Fronteira de comportamento

Nenhuma nas quatro arvores e nas seis fixtures. A unica diferenca teorica, ja declarada no
plano: o aviso de homonimo passou a usar `.get()` nos dois valores, como o ramo de nao
encontrado ja fazia. Num dossie montado a mao sem `exact_count`, o ramo de caminho encontrado
levantaria `KeyError` e passa a escrever `None`. Todos os chamadores reais recebem o dossie de
`homonym_dossier`, que sempre traz as duas chaves.

## Rede de seguranca

Suite completa antes e depois: **1635 passed, 9 skipped** nas duas pontas, com as mesmas 9
exclusoes e nenhuma assercao afrouxada.
