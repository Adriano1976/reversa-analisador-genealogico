---
schema_version: 1
id: OPP-20261003-GUE7
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/estrutura.txt
    - safety-net/suite-depois.txt
    - safety-net/paridade-depois.txt
measurement:
  before: "1 subpacote (core/); 12 modulos soltos na raiz do pacote; 15 arquivos e 1422 linhas"
  after: "3 subpacotes (parsers/, core/, reporting/); 5 modulos na raiz; 18 arquivos e 1425 linhas"
change_set:
  - chg: CHG-001
    file: src/reconstructed/parsers/__init__.py, src/reconstructed/reporting/__init__.py
    purpose: tornar os dois subpacotes pacotes regulares, com o `__init__.py` deles, dentro de `src/reconstructed/`
  - chg: CHG-002
    file: sete modulos movidos, sem uma linha de logica alterada
    purpose: gedcom_parser e csv_ingest vao para `parsers/`; matching, name_normalization, path_finding e family_navigation vao para `core/`; mermaid_render vai para `reporting/`
  - chg: CHG-003
    file: src/reconstructed/dna_analysis.py, src/reconstructed/path_search.py, src/app.py
    purpose: as duas fachadas e a aplicacao passam a importar pelos caminhos novos
  - chg: CHG-004
    file: seis arquivos de test
    purpose: os testes passam a importar `reconstructed.parsers.gedcom_parser`
  - chg: CHG-005
    file: _reversa_sdd/parity/harness.py, _reversa_sdd/parity/_check_split_types.py
    purpose: as duas linhas que vivem DENTRO das strings dos coletores passam ao caminho novo
  - chg: CHG-006
    file: README.md
    purpose: a arvore de `src/` passa a mostrar os tres subpacotes e os papeis que eles expressam
approval:
  by: user
  at: 2026-10-03
reversible_via:
  - CHG-001-subpacotes.diff
  - CHG-002-movimentacao.diff
  - CHG-003-fachadas-e-app.diff
  - CHG-004-testes.diff
  - CHG-005-paridade.diff
  - CHG-006-readme.diff
---

## O que foi feito

Sete modulos mudaram de lugar, e a arvore passou a expressar os papeis que antes so os docstrings diziam:

    src/reconstructed/
    ├── __init__.py
    ├── parsers/     gedcom_parser.py, csv_ingest.py
    ├── core/        cm_estimator.py, matching.py, name_normalization.py,
    │                path_finding.py, family_navigation.py
    ├── reporting/   mermaid_render.py
    ├── gedcom_state.py
    ├── text_cleaning.py
    ├── validate.py
    ├── path_search.py
    └── dna_analysis.py

**Nenhuma linha de logica foi alterada nos sete modulos movidos**, e isso foi provado, nao afirmado: o AST de cada um, com as linhas de import removidas, e identico ao da copia congelada antes da transformacao. Seis dos sete sao identicos ate nas linhas de import, porque so os imports relativos mudaram de nivel.

## O que ficou na raiz, e por que

| Modulo | Razao |
|---|---|
| `gedcom_state.py` | E o estado do processo. Enfia-lo em `parsers/` faria o nucleo depender de um subpacote de parsing, e inverter a direcao das dependencias e o oposto de modularizar |
| `text_cleaning.py` | Utilitario puro, com fan-out 0. Nao pertence a nenhum dos tres papeis, e criar um `utils/` para um arquivo seria subpacote de conveniencia |
| `validate.py` | Validacao da requisicao HTTP, nao do dominio. O proprio registro da oportunidade ja havia recusado move-lo |
| `path_search.py` | Fachada. Os testes importam `_mermaid_label` e `_LABEL_SEGURO` daqui |
| `dna_analysis.py` | Fachada e orquestracao, consumida pelo `app.py`, com 18 nomes reexportados |

## Duas coisas do registro que NAO foram feitas

O plano apresentado no gate recusou duas partes do registro original, e o usuario aprovou a recusa:

| Item do registro | Por que nao foi feito |
|---|---|
| Fundir `matching` com `name_normalization` em `core/fuzzy_matcher.py`, e `path_finding` com `family_navigation` em `core/path_finder.py` | Desfaria duas transformacoes aplicadas. A `OPP-20260929-ZV52` separou nome de decisao porque sao ciclos de mudanca distintos; a `OPP-20260929-UXEF` separou navegacao de busca pela mesma razao. Fundir criaria dois modulos de quase 300 e quase 200 linhas com duas responsabilidades cada. A regra dura do verbo e nao fundir o que o projeto separou por proposito |
| Renomear `csv_ingest.py` e `mermaid_render.py` | Os nomes nao mentem: a `OPP-20261003-LMAY`, aplicada na mesma sessao, concluiu que esses dois ja seguem a convencao do pacote. Mover e renomear sao verbos diferentes, e renomear junto dobraria a superficie da transformacao de maior risco da serie |

Se a fusao for desejada algum dia, ela merece transformacao propria, com a decisao explicita de reverter a `ZV52` e a `UXEF`. A recusa fica registrada aqui, e nao apenas na conversa.

## Medicao, antes e depois

| Metrica | Antes | Depois |
|---|---|---|
| Subpacotes | 1 | **3** |
| Modulos soltos na raiz do pacote | 12 | **5** |
| Arquivos do pacote | 15 | 18 |
| Linhas do pacote | 1422 | 1425 |
| Linhas de import reescritas | 0 | **30, em 18 arquivos** |
| Linhas de logica alteradas | 0 | **0** |
| Nomes publicos alcancaveis pela fachada | 18 | 18, os mesmos |

As tres linhas acrescentadas sao os tres `__init__.py` de uma linha cada.

**Correcao em relacao ao plano aprovado.** O plano dizia 32 linhas de import reescritas, e o numero real e **30**. Dois dos imports internos nao precisaram mudar porque as duas pontas cairam no mesmo subpacote: `from .name_normalization import ...` em `matching.py`, e `from .family_navigation import get_parents` em `path_finding.py`. Os dois passaram a ser um import dentro de `core/`, e nao entre subpacotes. O total de linhas conferidas pela tabela de edicao continua sendo 32; o que muda e quantas foram reescritas de fato.

## A linha que vive dentro da string, terceira vez na serie

O coletor do candidato, embutido no `harness.py`, importa modulos por nome. E a terceira transformacao seguida em que esse ponto exige atencao: na `TWNT` ele quebrou por colisao de alias, na `DWJC` ele era invisivel a leitura por AST, e aqui ele estava numa das 30 linhas.

**O instrumento novo resolve isso estaticamente.** O `verificar-estrutura.py` nao se limita a varrer arquivos: ele extrai a constante `CANDIDATE_COLLECTOR` do `harness.py` e a constante `COLETOR` do `_check_split_types.py`, faz `ast.parse` do texto delas, e resolve os imports de dentro. Sao 5 imports dentro da string do harness e 2 dentro da do `_check_split_types.py`, e todos resolvem. Antes desta transformacao, esse ponto so era conferido em tempo de execucao, se alguem lembrasse de rodar a paridade.

## Rede de seguranca

| Instrumento | Antes | Depois |
|---|---|---|
| Suite de testes | 118 aprovados, 15 erros de ambiente | **118 aprovados, 15 erros de ambiente** |
| Paridade com o oraculo congelado | 100 por cento em 6 fixtures | **100 por cento, zero divergencia em 6 fixtures** |
| Resolucao de import por AST | nao existia | **134 imports em 30 arquivos, todos resolvem**, incluindo os 7 que vivem dentro de strings |
| AST dos modulos movidos, sem imports | nao existia | **os sete identicos** ao da copia congelada |
| Arvore do README contra o disco | nao existia | **bate, arquivo por arquivo** |
| `src/__init__.py` | nao existe | **continua nao existindo**, como a RN-01 exige |

O terceiro instrumento e o mais importante desta transformacao, porque mover arquivo quebra import de um jeito que so aparece em execucao. A conferencia estatica encontra o erro antes de rodar a suite, e cobre tambem os caminhos que a suite nao exercita, como o `validate.py`, que e carregado tardiamente por um teste so.

## As tres restricoes do registro

| Restricao | Situacao |
|---|---|
| Nao criar `src/__init__.py` | Respeitada. Os tres subpacotes levam o `__init__.py` deles, dentro de `src/reconstructed/` |
| As fachadas `path_search.py` e `dna_analysis.py` sobrevivem | Respeitadas: nenhuma das duas se moveu, mudou de nome ou perdeu nome de `__all__` |
| O instrumento de paridade importa modulos por nome | As duas linhas foram atualizadas no lote 5, e a paridade foi remedida. O `_verify_fix_gives_parity.py` **nao** precisou mudar: ele copia a arvore inteira e mexe em `gedcom_state.py`, que ficou na raiz |

## Nota de metodo: o estado anterior congelado antes de tocar

Antes de mover qualquer arquivo, `src/` foi copiado inteiro para `before-after/src-antes/`. Os diffs dos sete modulos movidos saem contra essa copia, e nao contra o Git: o `HEAD` e o estado **anterior a LMAY**, e a LMAY tocou `dna_analysis.py`, `harness.py` e `README.md`, que esta transformacao tambem toca.

Para os demais arquivos, o estado anterior foi reconstruido pelo inverso exato de cada edicao, e onde a copia congelada existia a conferencia exigiu que os dois coincidissem, arquivo por arquivo.

## Pendencias

- `README.md` do registro de refactor continua dizendo que o harness de paridade "nao pode mais rodar" e que a suite tem 76 testes. Ele roda, da 100 por cento, e a suite tem 118 aprovados.
- `OPP-20260929-EHNZ`, no contexto `upload-gedcom`, continua aberta por decisao: e registro de rastreabilidade, e nao proposta de execucao.
- `_reversa_sdd/` e `_reversa_docs/` continuam com os caminhos antigos (`analisador-genealogico/`, modulos na raiz). Sao artefatos de extracao e de documentacao publicada, de outros donos.
