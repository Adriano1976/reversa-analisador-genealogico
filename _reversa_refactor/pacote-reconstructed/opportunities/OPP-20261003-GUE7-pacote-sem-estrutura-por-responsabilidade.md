---
schema_version: 1
id: OPP-20261003-GUE7
display_number: 18
context: pacote-reconstructed
verb: modularize
title: O pacote reconstruido nao tem estrutura por responsabilidade
target:
  files:
    - src/reconstructed/upload.py
    - src/reconstructed/csv_ingest.py
    - src/reconstructed/validate.py
    - src/reconstructed/domain.py
    - src/reconstructed/name_normalization.py
    - src/reconstructed/matching.py
    - src/reconstructed/family_navigation.py
    - src/reconstructed/path_finding.py
    - src/reconstructed/mermaid_render.py
    - src/reconstructed/path_search.py
    - src/reconstructed/dna_analysis.py
    - src/reconstructed/__init__.py
  symbol: pacote inteiro, 12 arquivos e 1363 linhas
smell: 12 modulos planos misturando cinco responsabilidades distintas (parsing, nucleo de decisao, navegacao de grafo, renderizacao de diagrama e validacao de entrada), sem subpacote que expresse a fronteira
roi:
  confidence: green
  impact: clareza e fronteira. Hoje a unica forma de saber que `matching` pertence ao nucleo e que `csv_ingest` pertence ao parsing e ler o docstring de cada arquivo. A organizacao em subpacotes torna a fronteira visivel na arvore
  cost: high
  est_return: fronteiras explicitas entre parsing, nucleo, apresentacao e validacao, com a arvore do repositorio passando a documentar a arquitetura
state: proposed
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

O pacote tem 12 modulos no mesmo nivel, sem subpasta. A leitura dos docstrings mostra cinco papeis distintos:

| Papel | Modulos |
|---|---|
| Parsing de entrada | `upload.py`, `csv_ingest.py` |
| Nucleo de decisao | `matching.py`, `name_normalization.py`, `path_finding.py`, `family_navigation.py` |
| Renderizacao | `mermaid_render.py` |
| Validacao de entrada | `validate.py`, `domain.py` |
| Fachadas de compatibilidade | `path_search.py`, `dna_analysis.py` |

A proposta do usuario organiza isso em `parsers/`, `core/`, `models/`, `reporting/` e `utils/`. Tres desses subpacotes correspondem a papeis que **existem hoje**: `parsers/`, `core/` e `reporting/`. Os outros dois nao correspondem, e a secao "Fora do escopo deste refactor" explica por que.

## Transformacao proposta

Criar `parsers/`, `core/` e `reporting/`, movendo os modulos sem alterar uma linha de logica:

| Subpacote | Modulo novo | Origem |
|---|---|---|
| `parsers/` | `gedcom_parser.py` | `upload.py` |
| `parsers/` | `dna_match_parser.py` | `csv_ingest.py` |
| `core/` | `fuzzy_matcher.py` | `matching.py` mais `name_normalization.py` |
| `core/` | `path_finder.py` | `path_finding.py` mais `family_navigation.py` |
| `core/` | `cm_estimator.py` | recorte de `dna_analysis.py`, ver a oportunidade `OPP-20261003-RGKA` |
| `reporting/` | `mermaid_generator.py` | `mermaid_render.py` |

## Tres restricoes que a medicao de 2026-10-03 impoe

**1. Nao criar `src/__init__.py`.** A arvore proposta inclui esse arquivo, e ele contradiz a regra RN-01 do requirements da feature 003, registrada no adendo `_reversa_sdd/addenda/003-renomear-pasta-app-para-src.md#1`: o diretorio que contem o codigo e uma **raiz de caminho de importacao, nao um pacote**. Criar `src/__init__.py` transforma `src` em pacote regular, o que (a) invalida o `search-path = ["src"]` de `pyrefly.toml`, que passaria a apontar para dentro do pacote, e (b) reintroduz a possibilidade de duplo carregamento de modulo com dois estados globais independentes, que foi medida nesta sessao (`reconstructed.upload` e um segundo caminho levando ao mesmo arquivo produzem objetos distintos e dois dicionarios `people` distintos). Subpacotes dentro de `src/reconstructed/` nao tem esse problema: cada um leva o seu proprio `__init__.py`, o que e correto e esperado.

**2. As fachadas `path_search.py` e `dna_analysis.py` precisam sobreviver a esta transformacao.** Elas reexportam o que era definido nelas antes das separacoes `OPP-20260929-UXEF` e `OPP-20260929-ZV52`, e declaram nominalmente seus consumidores externos no proprio docstring. Seus `__all__` incluem nomes privados que os testes importam (`_mermaid_label`, `_LABEL_SEGURO`). Remover as fachadas junto com a reorganizacao quebra consumidores em `tests/` e no harness de paridade. Ordem correta: primeiro migrar os consumidores, depois aposentar a fachada, em transformacao propria.

**3. O instrumento de paridade importa modulos por nome.** O `_reversa_sdd/parity/harness.py` faz `from reconstructed import upload, path_search, dna_analysis, domain`. Renomear `upload.py` e `domain.py` quebra o instrumento que prova a preservacao de comportamento, e `_reversa_sdd/parity/_verify_fix_gives_parity.py` guarda a linha literal do `sys.path` como texto de busca, a mesma armadilha identificada como D-08 no roadmap da feature 003. Ambos precisam ser atualizados na mesma transformacao, e a paridade precisa ser remedida em 100 porcento depois.

## Fora do escopo deste refactor

Quatro itens da arvore proposta **nao sao refactor** e nao podem ser tratados por especialista do time Code Quality, porque alteram comportamento observavel ou introduzem capacidade que hoje nao existe. Cada um e candidato a `/reversa-requirements`:

| Item proposto | Por que nao e refactor |
|---|---|
| `models/person.py` | O sistema **nao tem modelo de classes**: `Family`, `GenealogyGraph` e `DNAGroup` foram removidas em 2026-09-30 justamente por serem arquitetura abandonada sem consumidor. Recriar uma classe de pessoa reintroduz o que foi deliberadamente descartado |
| `models/relationship.py` (aresta tipada) | Tipar as arestas e **mudanca de comportamento**, e e o principio IV do projeto, ainda **nao implementado**: hoje `find_indirect_path` comprime nos de familia sem distinguir filiacao de casamento, e `split_path_by_marriage` reconhece apenas o primeiro par de conjuges adjacentes. O diagrama passaria a marcar arestas de casamento. O principio II e explicito: se o comportamento precisa mudar, isso e feature, nao refactor |
| `utils/logger.py` | O projeto **nao tem logging algum**. Criar logger e capacidade nova, nao reorganizacao |
| `utils/file_handler.py` com "limpeza de temporarios" | A limpeza **nao existe** hoje, entao implementa-la e comportamento novo. Alem disso, o item mistura duas coisas: mover `validate.py` para `utils/` renomearia um modulo que carrega contrato vigente (o adendo `bug-BUG-20260929-QMLY-v001` define a politica de aceitacao por conteudo, o teto de requisicao e a chave derivada do conteudo) |
| `reporting/report_factory.py` | Nao existe fabrica de relatorio: o fluxo monta a lista de resultados diretamente. Introduzir abstracao nova sem consumidor e o mesmo padrao que produziu as tres entidades removidas |
