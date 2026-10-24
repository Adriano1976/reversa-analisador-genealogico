---
schema_version: 1
id: OPP-20261024-SEPM
display_number: 53
context: busca-caminho
verb: modularize
title: 782 linhas com cinco assuntos que só compartilham a árvore
target:
  files:
    - src/core/documentary_relationship.py
  symbol: modulo
smell: >
  Datas, fichas de pessoa, homônimos, enumeração de caminhos alternativos e a montagem
  do cartão moram no mesmo arquivo. Nenhuma dessas partes conhece as outras por
  necessidade: todas recebem a mesma tupla `arvore` e leem registros do GEDCOM. Seis das
  vinte e seis funções passam de 45 linhas e a maior tem 102.
roi:
  confidence: yellow
  impact: >
    Coesão: o arquivo tem cinco razões independentes para mudar. Quem precisa mexer em
    data de nascimento abre o mesmo arquivo de quem mexe em colapso de pedigree. É o
    mesmo formato de problema que a `OPP-20261023-CTAO` resolveu em `core/dna_analysis.py`,
    com o mesmo procedimento disponível: fachada preservando os caminhos de importação.
  cost: medium
  est_return: >
    Quatro ou cinco módulos de 80 a 130 linhas, com a fachada mantendo os dezoito nomes
    que os quinze consumidores já importam.
state: applied
traceability:
  soul: [.reversa/soul.md#e7-parentesco_documental]
  specs:
    - _reversa_sdd/busca-caminho/design.md
    - _reversa_sdd/busca-caminho/requirements.md
---

## Antes observado

Medição por AST nesta sessão:

```
total de linhas físicas : 782
funções e classes       : 26
linhas dentro de defs   : 593 (76%)
```

Distribuição por assunto, com as faixas de linha reais:

| Assunto | Faixa | Linhas | Funções |
|---|---|---|---|
| Datas e leitura de DATE/PLAC | 73 a 173 | 105 | `parse_year`, `_data_de`, `birth_date`, `death_date`, `_local_de`, `intervalo_de_geracao_mediano` |
| Fichas de pessoa | 176 a 257 | 82 | `_ids`, `_construir_indice_de_filhos`, `_indice_de_filhos`, `get_children`, `person_summary` |
| Homônimos e índice de nomes | 260 a 379 | 120 | `normalizar`, `_diferencas_de_fichas`, `_CacheDeNomes`, `_chave_de`, `_indice_por_nome`, `homonym_dossier` |
| Enumeração de caminhos | 46 a 50 e 514 a 604 | 96 | `_ancestor_depths`, `_cadeias_ate`, `_cadeia_curta`, `find_all_common_ancestors`, `_caminho_alternativo` |
| Rótulo do parentesco | 441 a 511 | 71 | `documentary_label` |
| Evidência e cartão | 382 a 434 e 607 a 768 | 215 | `hop_evidence`, `documental_nao_encontrado`, `documentary_relationship` |

Cinco assuntos, e as dependências entre eles são de mão única: o cartão usa tudo, as
fichas usam datas, os homônimos usam fichas, os caminhos não usam nenhum dos outros.
Não há ciclo a criar.

O arquivo é importado por **quinze** módulos de `src/`, com destaque para
`path_search.py`, `passo_por_kit.py`, `dna_analysis.py`, `contexto_da_analise.py`,
`evidence_comparison.py`, `cirurgia_do_grafo.py` e `validacao.py`. Nenhum deles importa
só uma parte: todos pedem do mesmo endereço.

## Transformação proposta

Mesmo desenho da `OPP-20261023-CTAO`, que dividiu `core/dna_analysis.py` em oito módulos
sem mover nenhum import de consumidor:

1. `src/core/datas_do_gedcom.py`: `parse_year`, `birth_date`, `death_date`, `_data_de`,
   `_local_de`, `intervalo_de_geracao_mediano`, `IDADE_MINIMA_GENITOR`,
   `IDADE_MAXIMA_GENITOR`;
2. `src/core/fichas_da_pessoa.py`: `_ids`, o índice de filhos (com o atributo do grafo),
   `get_children`, `person_summary`, `_diferencas_de_fichas`;
3. `src/core/homonimos.py`: `normalizar`, `_chave_de`, `_indice_por_nome`,
   `homonym_dossier`;
4. `src/core/caminhos_alternativos.py`: `_ancestor_depths`, `_cadeias_ate`,
   `_cadeia_curta`, `find_all_common_ancestors`, `_caminho_alternativo`,
   `MAX_DEPTH_ALTERNATIVOS`, `LIMITE_DE_CADEIAS`;
5. `src/core/documentary_relationship.py` fica com o que é de fato o parentesco:
   `documentary_label`, `hop_evidence`, `documental_nao_encontrado`,
   `documentary_relationship`, os `__all__` e os reexports que preservam cada endereço
   atual.

`documentary_label` pode ir para `core/graus_de_parentesco.py`, que já é o dono da série
de nomes. Não é obrigatório: aquele módulo foi desenhado sem import nenhum, e
`documentary_label` importa `nome_do_grau` e `nome_do_primo` dele. Deixar no cartão evita
transformar uma folha pura em módulo com lógica.

## Fronteira de comportamento

Nenhuma, desde que a fachada reexporte os dezoito nomes de `__all__` e os consumidores
internos que hoje importam privados não existam. Varredura feita: nenhum módulo importa
nome privado deste arquivo, e nenhum `from ... import *` existe em `src/` nem em `tests/`.

## Rede de segurança exigida

- suíte completa verde antes e depois (1629 passam, 9 pulados, medido nesta sessão);
- um digest de equivalência sobre as saídas do módulo, no molde do que a `OPP-20261023-ORQA`
  usou: o parentesco devolvido para um conjunto fixo de pares, incluindo um caso com
  homônimo ambíguo, um com data impossível e um com colapso de pedigree. A suíte cobre
  esses caminhos por asserção, mas não por igualdade byte a byte do cartão inteiro;
- as guardas por AST de `tests/test_profundidade_do_caminho.py` e
  `tests/test_veredito_no_nucleo.py` precisam ser conferidas antes, porque leem arquivo e
  módulo por caminho. A `ORQA` e a `CTAO` quebraram exatamente esse tipo de guarda, e a
  correção foi reescrever a guarda, nunca afrouxar asserção.

## O que esta transformação não resolve

A coesão no nível de dado continua baixa: o cartão segue sendo um dicionário de dezesseis
chaves e a ficha de doze. Isso é a `OPP-20261006-YTSH`, que já está registrada e
recomendada para não ser roteada, porque tipos de domínio mudam comportamento observável
e pertencem ao alvo.

## Aplicada em 2026-10-24

Aprovada em plano e em dois diffs, aplicada pelo `/reversa-modularize` na mesma data.

| Módulo | Linhas | Responsabilidade |
|---|---|---|
| `core/datas_do_gedcom.py` | 135 | o que o registro diz sobre data e local |
| `core/fichas_da_pessoa.py` | 98 | a ficha comparável e o índice pai para filhos |
| `core/homonimos.py` | 154 | reconhecer o mesmo nome e montar o dossiê |
| `core/caminhos_alternativos.py` | 116 | ancestrais comuns, cadeias e caminhos alternativos |
| `core/documentary_relationship.py` | 406 | **fachada**: o cartão, os avisos e as reexportações |

`core/` passou de 35 para 39 módulos. O conjunto cresceu de 821 para 909 linhas, porque cada
módulo carrega docstring e imports próprios. O que caiu foi a concentração: a fachada ficou
com metade do arquivo original, e nenhum dos quatro módulos passa de 154 linhas.

Duas funções privadas viraram públicas ao atravessar a fronteira: `_ids` virou `ids_com_tag`
e `_local_de` virou `birth_place`. Fora isso, cada trecho foi copiado verbatim, e o gerador
confere o token de início e de fim de cada fatia antes de escrever.

Dois testes mudaram, e só de endereço: o que lê o arquivo por AST passou a apontar para
`homonimos.py`, e o `monkeypatch` que contava fichas passou a ter `core.homonimos` como seam.
Nenhuma asserção foi afrouxada.

A prova de equivalência comparou a saída com a versão de `HEAD` em **3.928 casos, zero
divergência**, com os seis códigos de aviso exercitados. A suíte ficou em **1635 passed, 9
skipped** nas duas pontas.

Dívida de documentação criada: `c4-components.md:213` e `architecture.md:154` ainda descrevem
o arquivo único. Os dois caminhos estão fora dos globs, então não foram editados.

O registro completo está no
[`transformation.md`](../transformations/OPP-20261024-SEPM-separar-em-modulos/transformation.md).

---
*Gerado pelo Reversa-Refactor em 2026-10-24, na auditoria de `src/core/documentary_relationship.py`.*
