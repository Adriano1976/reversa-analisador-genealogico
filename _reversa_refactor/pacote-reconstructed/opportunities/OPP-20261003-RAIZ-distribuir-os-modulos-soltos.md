---
schema_version: 1
id: OPP-20261003-RAIZ
display_number: 24
context: pacote-reconstructed
verb: modularize
title: cinco modulos ficam soltos na raiz do pacote, sem pasta que os agrupe
target:
  files: [src/reconstructed/gedcom_state.py, src/reconstructed/text_cleaning.py, src/reconstructed/validate.py, src/reconstructed/path_search.py, src/reconstructed/dna_analysis.py]
  symbol: os cinco modulos que nao foram para nenhum subpacote na OPP-20261003-GUE7
smell: a raiz do pacote mistura estado do processo, utilitario puro, validacao de requisicao HTTP e duas fachadas. Nenhum deles e parsing, nucleo ou apresentacao, e por isso nenhum entrou nos subpacotes, mas tambem nenhum tem pasta propria. Depois da `OPP-20261003-FLAT` eles passariam a ser nomes de modulo de primeiro nivel no caminho de importacao
roi:
  confidence: green
  impact: clareza e risco de colisao de nome. Hoje `gedcom_state`, `text_cleaning`, `validate`, `path_search` e `dna_analysis` vivem sob `reconstructed.*`, um espaco de nomes reservado ao projeto. Achatar sem distribuir poe os cinco no espaco de nomes global, onde `validate` e `state` sao nomes que qualquer pacote instalado pode reivindicar
  cost: medium
  est_return: raiz de `src/` limpa, com so o ponto de entrada e as pastas, como no exemplo do usuario
state: applied
traceability:
  soul:
    - .reversa/soul.md#entidades-centrais
    - .reversa/soul.md#decisoes-fundadoras
  specs:
    - _reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md
    - _reversa_sdd/architecture.md#1
---

## Antes observado

A `OPP-20261003-GUE7` distribuiu sete modulos em tres subpacotes e deixou cinco na raiz, cada um com razao declarada na epoca. As razoes continuam validas, mas elas respondem *"por que nao entrou em `parsers/`, `core/` ou `reporting/`"*, e nao *"onde este modulo deveria morar"*.

| Modulo | O que e | Quem depende dele |
|---|---|---|
| `gedcom_state.py` | o estado do processo: pessoas, familias, grafo | `parsers/gedcom_parser`, `core/matching`, `core/path_finding`, `core/family_navigation`, `dna_analysis`, `path_search`, cinco arquivos de teste e o harness |
| `text_cleaning.py` | utilitario puro, fan-out 0 | `parsers/csv_ingest`, `core/name_normalization`, `dna_analysis`, `tests/test_domain.py` e o harness |
| `validate.py` | validacao da requisicao HTTP de upload | `app.py`, e carregado tardiamente por `tests/test_upload_seguranca.py` |
| `path_search.py` | fachada da busca de caminhos | `app.py`, tres arquivos de teste e o harness |
| `dna_analysis.py` | fachada e orquestracao do cruzamento | `app.py`, dois arquivos de teste e o harness |

## Transformacao proposta

O exemplo do usuario nao deixa modulo nenhum na raiz: so `__init__.py` e o ponto de entrada. Aplicado a este projeto, o mapa e:

| Modulo | Destino proposto | Observacao |
|---|---|---|
| `gedcom_state.py` | `core/state.py` | e o estado do nucleo, e o nucleo e quem o consome. Muda de nome, entao `W001` tambem alcanca esta linha |
| `text_cleaning.py` | `utils/text_cleaning.py` | utilitario puro, sem papel entre os tres do nucleo |
| `validate.py` | `utils/validate.py` | **mantendo o nome do arquivo**. O registro da `GUE7` recusou mover `validate.py` para `utils/`, e a razao era o **rename** para `file_handler.py`, que renomearia um modulo carregando contrato vigente do `BUG-20260929-QMLY`. Mover para `utils/validate.py` preserva o nome do modulo |
| `path_search.py` | `core/path_search.py` | e a fachada do nucleo de busca, e o que ela reexporta mora em `core/` |
| `dna_analysis.py` | `core/analyzer.py` | e a orquestracao. O nome `analyzer` e o que o exemplo do usuario usa, e descreve melhor o papel do que `dna_analysis`, que diz o assunto e nao a funcao. Muda de nome, com a mesma ressalva do `W001` |

## Dois lotes, e a recomendacao de fazer so o primeiro agora

A tabela acima mistura duas coisas de verbos diferentes, e a serie ja estabeleceu que elas nao andam juntas: **movimentacao** e `modularize`, **renomeacao** e `standardize`. Separadas, ficam assim:

| Lote | O que faz | Verbo | Superficie |
|---|---|---|---|
| **A** | move os cinco modulos, **preservando os nomes**: `gedcom_state.py` para `core/`, `text_cleaning.py` e `validate.py` para `utils/`, `path_search.py` e `dna_analysis.py` para `core/` | modularize | so as linhas de import |
| **B** | renomeia `core/gedcom_state.py` para `core/state.py` e `core/dna_analysis.py` para `core/analyzer.py` | standardize | so as linhas de import, de novo, e mais o `__all__` da fachada |

**Recomendacao: fazer o lote A agora e deixar o lote B para a `OPP-20261003-PAST`**, que ja e a oportunidade de nomes. Duas razoes:

1. o lote A e puramente mecanico e prova-se por AST contra a copia congelada: os cinco modulos ficam identicos fora as linhas de import. Misturar renomeacao estraga essa prova, porque o AST passa a diferir por motivo alheio;
2. renomear `dna_analysis.py` mexe numa fachada com 18 nomes reexportados e quatro consumidores, e renomear `gedcom_state.py` mexe no modulo que o harness importa como `GS`. Cada um merece o proprio gate.

O gate do lote A decide: se o usuario preferir fazer A e B de uma vez, ele diz, e o plano registra que a prova de AST deixa de valer para esses dois modulos.

## Estado em 2026-10-03

**Lote A aplicado.** Os cinco modulos foram movidos, `utils/` foi criado, e a raiz do pacote ficou so com o `__init__.py`. Foram 42 linhas reescritas em 21 arquivos, com **zero linha de logica alterada**: `gedcom_state.py`, `text_cleaning.py` e `validate.py` continuam byte a byte identicos, e os outros dois mudaram so imports e uma citacao de caminho em docstring.

A armadilha do `_verify_fix_gives_parity.py`, que abria `gedcom_state.py` por nome, foi corrigida no mesmo lote, e a conferencia passou a verificar esse caminho.

**Lote B transferido para a `OPP-20261003-PAST`**, que ja e a oportunidade de nomes. Os dois renomes (`gedcom_state.py` para `state.py` e `dna_analysis.py` para `analyzer.py`) ficam la, e nao aqui, porque misturar renomeacao com movimentacao estragaria a prova por AST.

Registro completo, seis diffs e evidencia em `../transformations/OPP-20261003-RAIZ-distribuir-modulos-soltos/`.

## O que o exemplo pede e este projeto NAO tem



Tres pastas do exemplo nao tem conteudo real aqui, e duas delas nao podem ser criadas por refactor:

| Pasta do exemplo | Situacao neste projeto |
|---|---|
| `models/` | **Vazia.** O projeto nao tem modelo de classes: `Family`, `GenealogyGraph` e `DNAGroup` foram removidas em 2026-09-30 por decisao do usuario, por serem arquitetura abandonada sem consumidor. `models/person.py` recriaria o que foi descartado, e `models/relationship.py` com aresta tipada implementa o principio IV, que muda comportamento. **Nao e refactor**: vai para `/reversa-requirements` |
| `utils/logger.py` | **Nao existe logging algum no projeto.** Criar logger e capacidade nova, nao reorganizacao. `/reversa-requirements` |
| `utils/file_handler.py` | A limpeza de temporarios que ele descreve **nao existe**. E renomearia `validate.py`, que carrega contrato vigente. `/reversa-requirements` |
| `generator/` e `generator/code_generator.py` | O projeto nao gera codigo. O papel de saida de hoje e o diagrama Mermaid, que esta em `reporting/`. `/reversa-requirements`, se houver desejo |
| `generator/report_factory.py` | Nao existe fabrica de relatorio: o fluxo monta a lista de resultados direto. Abstração sem consumidor e exatamente o padrao que produziu as tres entidades removidas. `/reversa-requirements` |
| `parser/legacy_reader.py` | **Este projeto nao le codigo legado.** Ele le GEDCOM e CSV de DNA. O nome sugere o analisador de codigo do proprio framework Reversa, e nao este sistema |
| `src/main.py` | O ponto de entrada deste projeto e `src/app.py`, e o comando documentado e `python src/app.py`. Renomear para `main.py` muda o comando que o README ensina |

## Ordem de encadeamento

**Esta transformacao vem antes da `OPP-20261003-FLAT`.** Ela esvazia a raiz do pacote, e so depois disso apagar o nivel `reconstructed` deixa `src/` exatamente com a forma do exemplo: o ponto de entrada e as pastas. Feita depois, ela teria de mexer duas vezes nos mesmos imports.

O `OPP-20261003-PAST` (nome das pastas) e cosmético e vem por ultimo, se o usuario quiser.
