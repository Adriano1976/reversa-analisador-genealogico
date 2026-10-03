---
schema_version: 1
id: OPP-20261003-GUE7
display_number: 18
context: pacote-reconstructed
verb: modularize
title: O pacote reconstruido nao tem estrutura por responsabilidade
target:
  files: [src/reconstructed/]
  symbol: pacote inteiro, cinco modulos na raiz e tres subpacotes
smell: modulos planos misturando cinco responsabilidades distintas (parsing, nucleo de decisao, navegacao de grafo, renderizacao de diagrama e validacao de entrada), sem subpacote que expresse a fronteira
roi:
  confidence: green
  impact: clareza e fronteira. Antes, a unica forma de saber que `matching` pertence ao nucleo e que `csv_ingest` pertence ao parsing era ler o docstring de cada arquivo. A organizacao em subpacotes torna a fronteira visivel na arvore
  cost: high
  est_return: fronteiras explicitas entre parsing, nucleo, apresentacao e validacao, com a arvore do repositorio passando a documentar a arquitetura
state: applied
traceability:
  soul:
    - .reversa/soul.md#proposito
    - .reversa/soul.md#decisoes-fundadoras
  specs:
    - _reversa_sdd/architecture.md#1
    - _reversa_sdd/code-analysis.md#1
    - _reversa_sdd/addenda/003-renomear-pasta-app-para-src.md#2
    - _reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md#watch-principal
---

## Antes observado

O pacote tinha os modulos no mesmo nivel, sem subpasta, e a leitura dos docstrings mostrava cinco papeis distintos:

| Papel | Modulos |
|---|---|
| Parsing de entrada | `gedcom_parser.py`, `csv_ingest.py` |
| Nucleo de decisao | `matching.py`, `name_normalization.py`, `path_finding.py`, `family_navigation.py` |
| Renderizacao | `mermaid_render.py` |
| Validacao e apoio | `validate.py`, `text_cleaning.py` |
| Fachadas de compatibilidade | `path_search.py`, `dna_analysis.py` |

A proposta do usuario organiza isso em `parsers/`, `core/`, `models/`, `reporting/` e `utils/`. Tres desses subpacotes correspondem a papeis que **existem**: `parsers/`, `core/` e `reporting/`. Os outros dois nao correspondem, e a secao "Fora do escopo" explica por que.

**Inventario corrigido em 2026-10-03.** O registro original dizia 12 arquivos e 1363 linhas, e listava `upload.py` entre os alvos. Depois da `OPP-20261003-TWNT` e da `OPP-20261003-RGKA`, o estado real antes desta transformacao era: **15 arquivos e 1422 linhas**, com `gedcom_state.py` e `gedcom_parser.py` no lugar de `upload.py`, e `core/cm_estimator.py` ja em `core/`.

## Transformacao executada

| Subpacote | Modulo | Origem |
|---|---|---|
| `parsers/` | `gedcom_parser.py` | ja existia como modulo proprio, vindo de `upload.py` pela `TWNT` |
| `parsers/` | `csv_ingest.py` | movido |
| `core/` | `cm_estimator.py` | ja estava, recortado pela `RGKA` |
| `core/` | `matching.py` | movido |
| `core/` | `name_normalization.py` | movido |
| `core/` | `path_finding.py` | movido |
| `core/` | `family_navigation.py` | movido |
| `reporting/` | `mermaid_render.py` | movido |

Cinco modulos ficaram na raiz, cada um com razao declarada: `gedcom_state.py` (e o estado, e po-lo em `parsers/` inverteria a direcao das dependencias), `text_cleaning.py` (utilitario puro, sem papel entre os tres), `validate.py` (validacao de HTTP, e o proprio registro ja recusara move-lo), e as duas fachadas.

## Duas partes do registro original que NAO foram executadas

**1. As duas fusoes.** O registro propunha `core/fuzzy_matcher.py` como fusao de `matching.py` com `name_normalization.py`, e `core/path_finder.py` como fusao de `path_finding.py` com `family_navigation.py`. Nao foram feitas porque **desfariam duas transformacoes aplicadas**: a `OPP-20260929-ZV52` separou nome de decisao porque sao ciclos de mudanca distintos, e a `OPP-20260929-UXEF` separou navegacao de busca pela mesma razao. Fundir criaria dois modulos com duas responsabilidades cada, contra a regra dura do verbo. Se a fusao for desejada, merece transformacao propria, com a decisao explicita de reverter as duas anteriores.

**2. Os dois renomes.** O registro propunha `dna_match_parser.py` para `csv_ingest.py` e `mermaid_generator.py` para `mermaid_render.py`. Nao foram feitos porque os nomes atuais nao mentem: a `OPP-20261003-LMAY`, aplicada na mesma sessao, concluiu que os dois ja seguem a convencao do pacote. Mover e renomear sao verbos diferentes, e renomear junto dobraria a superficie da transformacao de maior risco da serie.

## Tres restricoes que a medicao impunha

**1. Nao criar `src/__init__.py`.** A arvore proposta inclui esse arquivo, e ele contradiz a regra RN-01 do requirements da feature 003, registrada no adendo `_reversa_sdd/addenda/003-renomear-pasta-app-para-src.md#1`: o diretorio que contem o codigo e uma **raiz de caminho de importacao, nao um pacote**. Criar `src/__init__.py` invalida o `search-path = ["src"]` de `pyrefly.toml` e reintroduz a possibilidade de duplo carregamento de modulo com dois estados globais independentes, ja medida nesta serie. Subpacotes dentro de `src/reconstructed/` nao tem esse problema: cada um leva o seu proprio `__init__.py`. **Respeitada.**

**2. As fachadas `path_search.py` e `dna_analysis.py` precisam sobreviver.** Elas reexportam o que era definido nelas antes das separacoes `ZV52` e `UXEF`, e declaram nominalmente seus consumidores externos no proprio docstring. Seus `__all__` incluem nomes privados que os testes importam (`_mermaid_label`, `_LABEL_SEGURO`). **Respeitada:** nenhuma das duas se moveu, mudou de nome ou perdeu nome de `__all__`. Aposentar a fachada continua sendo transformacao propria, depois de migrar os consumidores.

**3. O instrumento de paridade importa modulos por nome.** O coletor do candidato vive **dentro de uma string** no `harness.py`, e a linha nao aparece em nenhuma leitura de AST do arquivo. **Respeitada:** a linha foi atualizada no mesmo lote, e a paridade foi remedida em 100 por cento. O `_verify_fix_gives_parity.py` nao precisou mudar, porque ele copia a arvore inteira e mexe em `gedcom_state.py`, que ficou na raiz.

## Fora do escopo deste refactor

Itens da arvore proposta que **nao sao refactor** e nao podem ser tratados por especialista do time Code Quality, porque alteram comportamento observavel ou introduzem capacidade que hoje nao existe. Cada um e candidato a `/reversa-requirements`:

| Item proposto | Por que nao e refactor |
|---|---|
| `models/person.py` | O sistema **nao tem modelo de classes**: `Family`, `GenealogyGraph` e `DNAGroup` foram removidas em 2026-09-30 justamente por serem arquitetura abandonada sem consumidor. Recriar uma classe de pessoa reintroduz o que foi deliberadamente descartado |
| `models/relationship.py` (aresta tipada) | Tipar as arestas e **mudanca de comportamento**, e e o principio IV do projeto, ainda **nao implementado** |
| `utils/logger.py` | O projeto **nao tem logging algum**. Criar logger e capacidade nova |
| `utils/file_handler.py` com limpeza de temporarios | A limpeza **nao existe** hoje, entao implementa-la e comportamento novo. Alem disso, mover `validate.py` para `utils/` renomearia um modulo que carrega contrato vigente (`BUG-20260929-QMLY`) |
| `reporting/report_factory.py` | Nao existe fabrica de relatorio. Introduzir abstracao nova sem consumidor e o mesmo padrao que produziu as tres entidades removidas |

## Estado em 2026-10-03

**Aplicada.** Sete modulos movidos, 30 linhas de import reescritas em 18 arquivos, **zero linha de logica alterada**, provado por AST contra a copia congelada antes da transformacao. Suite em 118 aprovados e 15 erros de ambiente, paridade em 100 por cento nas 6 fixtures, 134 imports resolvidos por AST incluindo os 7 que vivem dentro de strings, e a arvore do README batendo com o disco.

Registro completo, diffs por lote e evidencia em `../transformations/OPP-20261003-GUE7-reorganizar-em-subpacotes/`.
