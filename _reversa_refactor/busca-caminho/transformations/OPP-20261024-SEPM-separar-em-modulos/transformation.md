---
schema_version: 1
id: OPP-20261024-SEPM
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/prova-de-equivalencia.txt
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
    - CHG-001.diff
    - CHG-002.diff
measurement:
  before: >
    1 modulo com 821 linhas e cinco responsabilidades: leitura de data e local, ficha da
    pessoa, homonimos e cache de nomes, enumeracao de caminhos, e o cartao. 28 funcoes no
    mesmo namespace, e a maior delas com 54 linhas.
  after: >
    4 modulos de responsabilidade unica (98 a 154 linhas) e uma fachada de 406 linhas que
    mantem os 18 nomes e os 15 consumidores. 909 linhas no conjunto: 88 a mais, porque cada
    modulo carrega docstring e imports proprios.
change_set:
  - chg: CHG-001
    files:
      - src/core/datas_do_gedcom.py (novo)
      - src/core/fichas_da_pessoa.py (novo)
      - src/core/homonimos.py (novo)
      - src/core/caminhos_alternativos.py (novo)
      - src/core/documentary_relationship.py (vira fachada)
    purpose: >
      separar as cinco responsabilidades, mantendo a fachada com o cartao e as
      reexportacoes
  - chg: CHG-002
    files:
      - tests/test_indice_de_nomes_do_documental.py
      - tests/test_desempenho_das_fichas.py
    purpose: >
      corrigir o endereco do arquivo lido por AST e o seam do monkeypatch; nenhuma assercao
      muda
approval:
  by: user
  at: 2026-10-24T02:25:00-03:00
reversible_via: [CHG-001.diff, CHG-002.diff]
---

## A divisao

| Modulo | Responsabilidade unica | Linhas |
|---|---|---|
| `core/datas_do_gedcom.py` | o que o registro diz sobre data e local | 135 |
| `core/fichas_da_pessoa.py` | a ficha comparavel e o indice pai para filhos | 98 |
| `core/homonimos.py` | reconhecer o mesmo nome e montar o dossie | 154 |
| `core/caminhos_alternativos.py` | ancestrais comuns, cadeias e caminhos alternativos | 116 |
| `core/documentary_relationship.py` | **fachada**: o cartao, os avisos e as reexportacoes | 406 |

`core/` passou de 35 para 39 modulos. O conjunto cresceu de 821 para 909 linhas: cada modulo
novo carrega docstring e imports proprios, e a fachada manteve os que reexporta.

## O que mudou de nome, e por que

Duas funcoes privadas atravessavam a nova fronteira, e importar privado entre modulos e o que
a divisao deveria eliminar:

| Antes | Depois | Motivo |
|---|---|---|
| `_ids(people, sub_tag, pid)` | `ids_com_tag(...)` | usada pela ficha e pelo cartao |
| `_local_de(people, pid, tag)` | `birth_place(people, pid)` | usada so pela ficha; espelha `birth_date` e perde o `tag`, que era sempre `"BIRT"` |

Mesmo corpo e mesma saida nas duas. Fora isso, cada trecho foi copiado verbatim: o gerador
`gerar-modulos.py` confere o token de inicio e de fim de cada fatia antes de escrever.

## As dependencias, depois

```
registro ─────────────┐
family_navigation ────┤
                      ▼
              datas_do_gedcom ──► fichas_da_pessoa ──► homonimos
                      │                  │                 │
                      ▼                  │                 │
              caminhos_alternativos ◄────┘                 │
                      │                                    │
                      ▼                                    ▼
              documentary_relationship (fachada) ◄──────────┘
```

Nenhum ciclo. A direcao `parsers → core` e `core → utils` continua a mesma, e
`test_dependencias_nucleo.py` varre `core/` inteiro, entao os quatro modulos novos entraram na
guarda sem precisar de teste novo.

## O que a alma exigia, e como ficou

| Exigencia | Onde | Situacao |
|---|---|---|
| CACHE_DE_NOMES e o unico estado de modulo do nucleo | `soul.md:81` | continua sendo; agora mora em `homonimos.py`, que e o unico modulo do nucleo com estado |
| A arvore entra por parametro (RF-01) | `test_dependencias_nucleo.py` | nenhuma funcao nova guarda arvore |
| O nucleo nao importa `parsers` nem `reporting` | idem | os quatro importam so `core` e `utils` |
| Parentesco documental nunca le cM | `soul.md`, E7 | nenhum modulo novo toca evidencia genetica |

## As duas quebras em teste, e o tratamento

| Arquivo | Quebra | Correcao |
|---|---|---|
| `tests/test_indice_de_nomes_do_documental.py` | lia `documentary_relationship.py` por caminho e usava `dr._indice_por_nome` | `CAMINHO_DO_MODULO` aponta para `homonimos.py`, e as seis chamadas passam a `homonimos._indice_por_nome` |
| `tests/test_desempenho_das_fichas.py` | `monkeypatch.setattr(dr, "person_summary", ...)` deixaria de ser visto pelo dossie | o seam virou `homonimos.person_summary` |

Nenhuma assercao foi afrouxada: 12 insercoes e 11 remocoes, todas de endereco.

## Prova

Equivalencia por execucao, contra a versao de `HEAD`, dicionario por dicionario:

| Corpus | Comparacoes |
|---|---|
| Arvore real, 35.459 pessoas | 3.606 |
| Colapso sintetico | 34 |
| Seis fixtures de paridade | 204 |
| `documental_nao_encontrado` | 84 |
| **Total** | **3.928, com 0 divergencia** |

Os seis codigos de aviso foram exercitados: `caminhos_multiplos` 2.941, `homonimo` 2.815,
`sem_caminho` 440, `data_impossivel` 250, `colapso_de_pedigree` 148, `pessoa_ausente` 4.

Superficie da fachada: os 18 nomes de `__all__` continuam acessiveis em
`core.documentary_relationship`, e os quinze consumidores importam sem erro.

Suite completa: **1635 passed, 9 skipped** antes e depois, com as mesmas 9 exclusoes.

## Divida de documentacao criada

| Artefato | Afirmacao | Situacao |
|---|---|---|
| `_reversa_sdd/c4-components.md:213` | descreve o arquivo como "parentesco documental completo **e** o cache de nomes", 531 linhas | agora sao cinco arquivos, e o cache esta em `homonimos.py` |
| `_reversa_sdd/architecture.md:154` | cita `documentary_relationship._chave_de` | `_chave_de` mora em `core/homonimos.py` |

Os dois caminhos estao em `_reversa_sdd/**`, fora dos globs liberados pela config, e por isso
nao foram editados. E o mesmo bloqueio da `OPP-20261006-W4KD`.
