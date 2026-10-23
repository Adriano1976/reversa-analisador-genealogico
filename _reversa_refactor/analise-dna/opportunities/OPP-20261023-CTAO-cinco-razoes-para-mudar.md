---
schema_version: 1
id: OPP-20261023-CTAO
display_number: 47
context: analise-dna
verb: modularize
title: Módulo com cinco razões para mudar e o contrato de 40 chaves duplicado em dois construtores
target:
  files: [src/core/dna_analysis.py]
  symbol: Dependencias, ROTULOS_DE_VALIDACAO, _aviso_da_validacao, _explicacao_da_endogamia, _observacao_estrutural, _selo_da_endogamia, _validacao_do_cartao, _cartao_sem_correspondencia
smell: >
  Um mesmo arquivo reúne cinco responsabilidades que mudam por motivos diferentes:
  orquestrar o caso de uso, montar o cartão, decidir texto e classe CSS de tela,
  adaptar o veredito de validação e sustentar uma fachada de compatibilidade de 15
  nomes. A consequência medida é o contrato do cartão escrito duas vezes: o dicionário
  de 40 chaves do fluxo principal e o dicionário de 41 chaves do cartão sem
  correspondência precisam ser mantidos em sincronia à mão, e já estão em ordens
  diferentes.
roi:
  confidence: green
  impact: >
    Alta coesão por módulo é o que permite que cada mudança de tela encoste só no
    arquivo de tela. Hoje não encosta: quem muda o selo de endogamia, quem muda a
    validação temporal e quem muda o passo por kit editam o mesmo arquivo de 1.108
    linhas. O contrato duplicado é o risco concreto: uma chave acrescentada só em um
    dos construtores não gera erro, gera campo vazio na tela para um dos dois tipos de
    cartão.
  cost: medium
  est_return: >
    Oito arquivos com uma razão de mudar cada, de 43 a 470 linhas. `dna_analysis.py`
    fica com o caso de uso, a ordem e a fachada que os instrumentos congelados
    consomem.
state: applied
traceability:
  soul: []
  specs:
    - _reversa_sdd/analise-dna/requirements.md
    - _reversa_sdd/analise-dna/design.md
    - _reversa_sdd/adrs/34-ciclos-quebrados-e-superficies-removidas.md
---

## Antes observado

`src/core/dna_analysis.py`: 1.108 linhas, 10 funções e 1 classe. As razões de
mudança, com as linhas de cada uma:

| Razão de mudar | Símbolos | Linhas | Tamanho |
|---|---|---|---|
| Orquestrar o caso de uso | `dna_analysis` | 539-1091 | 553 |
| Montar o cartão | `_cartao_sem_correspondencia`, dict de 956-1051 | 413-536, 956-1051 | 124 + 96 |
| Decidir texto e classe CSS | `ROTULOS_DE_VALIDACAO`, `_aviso_da_validacao`, `_selo_da_endogamia`, `_explicacao_da_endogamia`, `_observacao_estrutural` | 205-208, 211-229, 257-356 | 4 + 19 + 18 + 17 + 61 |
| Adaptar o veredito | `_validacao_do_cartao` | 359-410 | 52 |
| Sustentar a fachada | imports de 42-98 e `__all__` | 42-98, 1102-1108 | 57 + 7 |
| Auxiliares que a spec ancora aqui | `_montar_diagrama`, `_observacoes` | 144-192 | 47 |

### O contrato duplicado, medido

Dois construtores produzem o mesmo cartão:

- o dicionário inline do fluxo principal (956-1051), com **40 chaves**;
- o retorno de `_cartao_sem_correspondencia` (490-536), com **41 chaves**.

Comparação das duas listas, por AST:

```
so no principal : []
so no sem_corr  : ['sem_correspondencia']
mesma ordem?    : False
```

Ou seja: o mesmo contrato, escrito duas vezes, já com a ordem divergente. A única
diferença legítima é a marca `sem_correspondencia`, que só um dos dois tipos de
cartão carrega. Qualquer chave nova precisa ser lembrada nos dois lugares, e o modo
de falha é silencioso: o template lê a chave ausente como vazia.

### A fachada, medida

O módulo importa **56 nomes de 21 módulos**. Doze desses nomes não são usados no
corpo:

```
match_candidates
drop_short_tokens, norm_name, soft_prefix_jaccard, split_name_pt,
surname_core_tokens, surnames_set, token_prefixes, top_given_tokens
demojibake, strip_bad_utf
```

Eles existem por causa de `__all__` (15 nomes). Os consumidores são dois
instrumentos congelados de `_reversa_sdd/parity/` (`_collect_cand.py`,
`_check_split_types.py`) e um teste (`tests/test_characterization_matching.py`).
A fachada não vira oportunidade própria por decisão de ROI: os módulos de origem já
estão carregados por outros caminhos, o ganho em tempo é nulo e o consumidor está em
caminho que a config não libera. Fica registrado aqui como motivo para o
`modularize` não tocar em `__all__`.

## Transformação proposta

```
src/core/
  dna_analysis.py          # caso de uso: dna_analysis, _ordem, _montar_diagrama,
                           # _observacoes, docstring do modulo, __all__   (~280 linhas)
  dependencias.py          # Dependencias                                   (~40 linhas, NOVO)
  rotulos_do_cartao.py     # ROTULOS_DE_VALIDACAO, _aviso_da_validacao,
                           # _selo_da_endogamia, _explicacao_da_endogamia,
                           # _observacao_estrutural                        (~160 linhas, NOVO)
  cartao_de_analise.py     # _cartao_sem_correspondencia, _validacao_do_cartao
                           # e o passo por kit da OPP-20261023-ORQA        (~380 linhas, NOVO)
```

### Por que `Dependencias` sai

`Dependencias` é a **única classe do módulo** e não tem dono declarado. Ela nasceu
aqui, mas `src/core/path_search.py:187` a consome (`deps.generate_mermaid_indirect`)
sem importar o tipo, e `src/app.py:22` a importa daqui para montar a instância única.
Ou seja: um contrato de três consumidores mora dentro de um arquivo de 1.108 linhas
que muda por outro motivo. Em `core/dependencias.py` ele passa a ter endereço
próprio, e o `path_search` deixa de depender implicitamente do módulo de DNA.

### Por que `_montar_diagrama` e `_observacoes` ficam

`_reversa_sdd/analise-dna/requirements.md:296` declara que
`src/core/dna_analysis.py` contém `dna_analysis`, `_montar_diagrama`, `_observacoes`
e `_ordem`. A spec não está em caminho liberado por `.reversa/reversa-config.json`
(globs: `src/**`, `tests/**` e mais quinze, sem `_reversa_sdd/**`). Mover esses três
símbolos criaria desvio documental que ninguém pode registrar nesta sessão.

O desvio já existe para outros símbolos: a linha 295 da mesma tabela ainda diz que
`projetar_analise` mora em `src/application/dna_analysis.py`, e ele foi para
`src/application/projecao_analise.py` na `OPP-20261023-MPRA`. A diferença é que
agora a escolha é consciente e está escrita.

## Fronteira de comportamento

Movimentação de código, sem reescrita: nenhuma expressão muda, só o arquivo onde
vive. Duas consequências precisam de tratamento explícito:

1. `tests/test_endogamia.py` importa `_observacao_estrutural` e `_selo_da_endogamia`
   de `core.dna_analysis` (linhas 37-41). O import passa a apontar para
   `core.rotulos_do_cartao`. `tests/**` está liberado pela config.
2. `_reversa_sdd/parity/_probe_sugestao.py` e os demais instrumentos importam
   `Dependencias` e `dna_analysis` de `core.dna_analysis`. `dna_analysis` continua
   lá; `Dependencias` continua acessível por reexportação em `dna_analysis.py`, de
   modo que nenhum instrumento congelado precisa ser editado.

## Rede de segurança

Suíte medida nesta sessão antes de qualquer escrita: **1625 passed, 9 skipped em
105,64 s**. O gate exige a mesma contagem depois, com a árvore de importação nova.

## Ordem de encadeamento

Esta transformação rende mais **depois** da `OPP-20261023-ORQA`: o passo por kit já
vai existir como função nomeada, e aí o `modularize` só muda de arquivo. Feita
antes, o mesmo corte teria de ser feito dentro de um arquivo de 1.108 linhas.

## Resultado da aplicação

Aplicada em 2026-10-23, sob gate de plano e de diff aprovados, em duas partes:
`CHG-001` no código e `CHG-002` nos dois testes que apontavam para o arquivo antigo.

Oito arquivos, um por responsabilidade:

| Arquivo | Linhas |
|---|---|
| `core/dependencias.py` | 43 |
| `core/contexto_da_analise.py` | 57 |
| `core/rotulos_do_cartao.py` | 152 |
| `core/validacao_no_cartao.py` | 72 |
| `core/endogamia_no_cartao.py` | 109 |
| `core/passo_por_kit.py` | 470 |
| `core/cartao_sem_correspondencia.py` | 139 |
| `core/dna_analysis.py` | 321 |

A `dna_analysis.py` caiu de 1.258 para 321 linhas. O total subiu para 1.363 por
cabeçalho de módulo, docstring e imports.

A estimativa falou em quatro módulos e no contrato do cartão definido uma única vez.
O número real é oito, e a unificação dos dois construtores de cartão ficou fora: é
mudança de estrutura interna, não `modularize`. Agora os dois estão em arquivos
vizinhos, e a duplicação está visível.

Suíte: **1625 passed, 9 skipped** antes (95,87 s) e depois (96,61 s). Digest de
equivalência idêntico. O registro completo está em
`../transformations/OPP-20261023-CTAO-cinco-razoes-para-mudar/transformation.md`.

---
*Gerado pelo Reversa-Refactor em 2026-10-23. Aplicada no mesmo dia.*
