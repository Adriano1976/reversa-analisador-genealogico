---
schema_version: 1
id: OPP-20261024-FLUX
display_number: 54
context: busca-caminho
verb: restructure
title: A função de 102 linhas que monta o cartão, com quatro blocos de aviso no meio
target:
  files:
    - src/core/documentary_relationship.py
  symbol: documentary_relationship
smell: >
  Uma única função encadeia busca do caminho, evidência por salto, caminhos
  alternativos, colapso de pedigree, aviso de homônimo e montagem do dicionário final.
  Cada bloco de aviso monta uma mensagem longa embutida, e o leitor só entende qual
  aviso sai depois de atravessar noventa linhas.
roi:
  confidence: green
  impact: >
    É a função que toda a tela de busca lê, chamada até vinte e cinco vezes por
    requisição pelo laço de combinações de `path_search`. Hoje as quatro mensagens de
    aviso competem por espaço com a lógica de percurso, e a ordem em que entram em
    `avisos` é contrato observável (a tela mostra a lista na ordem recebida).
  cost: medium
  est_return: >
    Seis etapas nomeadas de 5 a 20 linhas, cada uma devolvendo o seu pedaço, com o
    cartão montado no fim por um dicionário único.
state: applied
traceability:
  soul: [.reversa/soul.md#e7-parentesco_documental, .reversa/soul.md#3-decisoes-fundadoras]
  specs:
    - _reversa_sdd/busca-caminho/design.md
    - _reversa_sdd/state-machines.md
---

## Antes observado

`documentary_relationship` ocupa as linhas 667 a 768, 102 linhas. Dentro dela, na ordem:

| Bloco | Linhas | O que faz |
|---|---|---|
| guarda de pessoa ausente | 674 a 677 | devolve um cartão de quatro chaves |
| busca e desvio para o não encontrado | 679 a 684 | delega a `find_ancestral_path` |
| distâncias e rótulo | 686 a 688 | `indice`, `deg_a`, `deg_b`, `documentary_label` |
| evidência de cada salto | 690 a 695 | sobe até o MRCA e desce depois dele |
| aviso `data_impossivel` | 697 a 707 | uma mensagem de seis linhas por salto suspeito |
| caminhos alternativos | 709 a 717 | enumera e monta `alternativos` |
| aviso `caminhos_multiplos` | 719 a 725 | mensagem de cinco linhas |
| colapso de pedigree | 727 a 731 | laço com `_cadeias_ate` |
| aviso `colapso_de_pedigree` | 732 a 739 | mensagem montada por concatenação com gerador aninhado |
| aviso `homonimo` | 741 a 749 | mensagem de oito linhas, quase igual à de `documental_nao_encontrado` |
| montagem final | 751 a 768 | dicionário de dezesseis chaves |

Quatro blocos de aviso produzem dicionários de forma parecida (`code`, `message`, e às
vezes `family_id`), com a mensagem escrita em pedaços `f` encadeados. É o mesmo formato
que a `OPP-20261023-ETAP` encontrou em `_cartao_do_kit`, que caiu de 368 para 224 linhas
com seis etapas nomeadas.

## Transformação proposta

1. `_aviso_de_data_impossivel(item)` devolve o aviso a partir de um item de evidência;
2. `_avisos_de_data(evidencia)` devolve a lista dos avisos desse bloco;
3. `_alternativos_e_aviso(arvore, a_id, b_id, comuns, comum)` devolve
   `(alternativos, avisos)` e concentra a regra de "mais de um caminho";
4. `_colapso_e_aviso(arvore, a_id, comuns)` devolve `(colapso, avisos)`;
5. `_aviso_de_homonimo(homonimos, com_caminho=True)` devolve o aviso, e passa a ser a
   fonte única da mensagem que hoje está em dois lugares;
6. `documentary_relationship` fica com a sequência: guarda, busca, rótulo, evidência,
   alternativos, colapso, homônimo, montagem.

## Fronteira de comportamento

A ordem de `avisos` tem de ser preservada: `data_impossivel` (um por salto), depois
`caminhos_multiplos`, depois `colapso_de_pedigree`, depois `homonimo`. A tela lista os
avisos na ordem recebida e `path_search.py` converte cada `message` em observação, sem
reordenar. Por isso o encadeamento dos blocos é contrato, não estilo.

A mensagem de homônimo tem hoje dois finais diferentes de propósito: a do caminho
encontrado acrescenta que o caminho exibido pertence a um dos registros. O parâmetro
`com_caminho` preserva os dois textos palavra por palavra.

## Rede de segurança exigida

Suíte completa verde antes e depois. Além dela, um teste de ordem dos avisos para um par
que dispare dois códigos ao mesmo tempo, para que a extração não troque a sequência. O
alvo é o mesmo da `OPP-20261024-SEPM`: se as duas forem aprovadas, esta vem primeiro,
para que os módulos novos nasçam já com as etapas separadas.

## Aplicada em 2026-10-24

Aprovada em plano e em diff, aplicada pelo `/reversa-restructure` na mesma data, pelo
`CHG-001.diff` com 108 inserções e 67 remoções.

| Antes | Depois |
|---|---|
| `documentary_relationship` com 102 linhas | **54 linhas** |
| 4 blocos `if ...: avisos.append({...})` | 0, no lugar deles três construtores que devolvem `dict \| None` |
| mensagem de homônimo em 2 lugares | 1 |
| ordem dos avisos espalhada por 60 linhas | uma tupla de três construtores |
| módulo com 780 linhas | 821 |

A prova de equivalência comparou a saída da versão de `HEAD` com a do módulo em **3.928
casos, com zero divergência**, e os seis códigos de aviso foram exercitados (o menos
frequente, `pessoa_ausente`, 4 vezes; o mais, `caminhos_multiplos`, 2.941). Uma diferença
injetada de propósito foi acusada em 3.844 casos, o que calibra o instrumento.

Evidência em
[`before-after/`](../transformations/OPP-20261024-FLUX-funcao-de-102-linhas/before-after/) e
registro completo no
[`transformation.md`](../transformations/OPP-20261024-FLUX-funcao-de-102-linhas/transformation.md).

---
*Gerado pelo Reversa-Refactor em 2026-10-24, na auditoria de `src/core/documentary_relationship.py`.*
