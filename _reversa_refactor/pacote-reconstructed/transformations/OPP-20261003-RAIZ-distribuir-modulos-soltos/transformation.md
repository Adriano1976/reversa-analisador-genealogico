---
schema_version: 1
id: OPP-20261003-RAIZ
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
  before: "5 modulos soltos na raiz do pacote; 3 subpacotes; 17 arquivos e 1425 linhas"
  after: "0 modulos soltos na raiz do pacote; 4 subpacotes; 18 arquivos e 1426 linhas"
change_set:
  - chg: CHG-001
    file: src/reconstructed/utils/__init__.py
    purpose: criar o subpacote de utilitarios, que nao existia
  - chg: CHG-002
    file: cinco modulos movidos, nenhum renomeado
    purpose: gedcom_state, path_search e dna_analysis vao para `core/`; text_cleaning e validate vao para `utils/`
  - chg: CHG-003
    file: sete modulos dos subpacotes existentes
    purpose: os imports que apontavam para a antiga raiz do pacote passam a apontar para `core/` ou `utils/`
  - chg: CHG-004
    file: src/app.py e oito arquivos de teste
    purpose: a aplicacao e a suite passam a importar pelos caminhos novos
  - chg: CHG-005
    file: _reversa_sdd/parity/harness.py, _check_split_types.py, _verify_fix_gives_parity.py
    purpose: os coletores embutidos e o script de contraprova passam a alcançar os modulos novos
  - chg: CHG-006
    file: README.md
    purpose: a arvore de `src/` passa a mostrar os quatro subpacotes e a raiz do pacote sem modulo solto
approval:
  by: user
  at: 2026-10-03
reversible_via:
  - CHG-001-utils-init.diff
  - CHG-002-movimentacao.diff
  - CHG-003-import-no-pacote.diff
  - CHG-004-app-e-testes.diff
  - CHG-005-paridade.diff
  - CHG-006-readme.diff
---

## O que foi feito

Cinco modulos mudaram de pasta, e nenhum mudou de nome:

| Modulo | De | Para |
|---|---|---|
| `gedcom_state.py` | raiz do pacote | `core/` |
| `path_search.py` | raiz do pacote | `core/` |
| `dna_analysis.py` | raiz do pacote | `core/` |
| `text_cleaning.py` | raiz do pacote | `utils/` (subpacote novo) |
| `validate.py` | raiz do pacote | `utils/` |

**A raiz do pacote ficou so com o `__init__.py`.** Isso torna a `OPP-20261003-FLAT` trivial: ela passa a ser subir quatro pastas um nivel e apagar o diretorio, sem tocar em arquivo nenhum.

## Medicao, antes e depois

| Metrica | Antes | Depois |
|---|---|---|
| Modulos soltos na raiz do pacote | 5 | **0** |
| Subpacotes | 3 | **4** |
| Arquivos do pacote | 17 | 18 |
| Linhas do pacote | 1425 | 1426 |
| Linhas de import e citacao reescritas | 0 | **42, em 21 arquivos** |
| Linhas de logica alteradas | 0 | **0** |

A linha acrescentada e o `utils/__init__.py`, de uma linha.

## Os tres que ficaram byte a byte identicos

`gedcom_state.py`, `text_cleaning.py` e `validate.py` **nao importam nada do pacote**. Movidos, o arquivo inteiro tem de continuar identico, e continua: a conferencia exige igualdade byte a byte, e nao apenas igualdade de AST. E a prova mais forte da serie, porque nao sobra margem para interpretacao.

Os outros dois mudaram apenas o que a movimentacao obriga. A classificacao de cada linha trocada foi conferida uma a uma:

| Modulo | Imports | Docstring | Comentario | Outro |
|---|---|---|---|---|
| `gedcom_state.py` | 0 | 0 | 0 | **0** |
| `path_search.py` | 3 | 1 | 0 | **0** |
| `dna_analysis.py` | 7 | 0 | 0 | **0** |
| `text_cleaning.py` | 0 | 0 | 0 | **0** |
| `validate.py` | 0 | 0 | 0 | **0** |

A unica linha que nao e import e a citacao de caminho no docstring de `path_search.py`, que dizia `reconstructed/dna_analysis.py` e passou a dizer `reconstructed/core/dna_analysis.py`.

## A armadilha que nenhum gate enxerga

O `_reversa_sdd/parity/_verify_fix_gives_parity.py` abre um arquivo **por nome**:

    alvo = os.path.join(STUB, "gedcom_state.py")

Movendo `gedcom_state.py` para `core/`, esse script passaria a estourar `FileNotFoundError`. **Nada avisaria**: ele nao e executado pela suite nem pelo harness de paridade, entao os dois gates ficariam verdes enquanto a ferramenta de contraprova apodrecia. E a mesma classe de defeito registrada como `D-08`, e a terceira aparicao na serie.

A correcao entrou neste lote, e a conferencia passou a **verificar o caminho**: o `verificar-estrutura.py` extrai os caminhos que os scripts de instrumentacao montam com `os.path.join(STUB, ...)` e exige que existam no pacote. A saida registra `core/gedcom_state.py existe`.

## O que NAO foi feito, e para onde foi

O registro da oportunidade previa tambem dois **renomes**: `gedcom_state.py` para `core/state.py` e `dna_analysis.py` para `core/analyzer.py`. Eles **nao** entraram neste lote, por decisao do gate: renomeacao e `standardize`, e mistura-la com a movimentacao estragaria a prova por AST, porque o AST passaria a diferir por motivo alheio ao import.

Os dois renomes foram transferidos para a `OPP-20261003-PAST`, que ja e a oportunidade de nomes, e la convivem com os nomes das pastas.

## Fronteira da alma

| Fonte | Situacao |
|---|---|
| `.reversa/soul.md#entidades-centrais` (o grafo sustenta a busca) | preservada: o modulo do estado mudou de pasta, e a identidade do objeto nao mudou |
| `.reversa/soul.md#decisoes-fundadoras` (conexao direta antes de afinidade) | preservada: nenhuma ordem de estagio foi tocada |
| principio II (comportamento observavel preservado) | preservado: zero linha de logica alterada |
| regra dura do verbo (nao fundir o que o projeto separou) | respeitada: nada funde, nada separa, as fronteiras de modulo ficam intactas |

## Sobre o watch W001

**Este lote nao dispara o `W001`.** O watch vigia o nome do pacote do nucleo, `reconstructed.*`, e o prefixo continua identico: o que mudou foram caminhos internos (`reconstructed.path_search` passou a `reconstructed.core.path_search`). Quem dispara o `W001` e a `OPP-20261003-FLAT`, em gate proprio.

Um registro de precisao: a citacao da `RN-01` no registro da `GUE7` apontava para o adendo 003, e a regra nao esta la. Ela esta em `_reversa_forward/003-renomear-pasta-app-para-src/requirements.md#4`. O adendo foi sincronizado depois e cita o delta da feature, nao a regra.

## Rede de seguranca

| Instrumento | Antes | Depois |
|---|---|---|
| Suite de testes | 118 aprovados, 15 erros de ambiente | **118 aprovados, 15 erros de ambiente** |
| Paridade com o oraculo congelado | 100 por cento em 6 fixtures | **100 por cento, zero divergencia em 6 fixtures** |
| Resolucao de import por AST | nao existia para esta arvore | **134 imports em 31 arquivos, todos resolvem** |
| Coletores dentro de string | nao existia para esta arvore | **5 + 2 imports, todos resolvem** |
| Caminho do `_verify_fix_gives_parity.py` | apontava para arquivo que deixaria de existir | **`core/gedcom_state.py existe`** |
| AST dos cinco movidos | nao existia para esta arvore | **codigo identico nos cinco; byte a byte identico nos tres que nao importam o pacote** |
| Arvore do README contra o disco | nao existia para esta arvore | **bate, arquivo por arquivo** |

## Correcao declarada em relacao ao plano

O plano dizia **41 linhas de import em 21 arquivos**. O numero real e **42 linhas em 21 arquivos**: 41 sao linhas de import, e a 42a e a citacao de caminho dentro do docstring de `path_search.py`, que o plano contava a parte como "1 arvore" na linha do README. O total de arquivos tocados e 26, contando o README e o `utils/__init__.py`.

## Nota de metodo: o estado anterior congelado antes de tocar

Antes de mover qualquer arquivo, `src/` foi copiado inteiro para `before-after/src-antes/`. E obrigatorio: o `HEAD` esta atras da `LMAY` e da `GUE7`, entao o Git nao serve como estado anterior. Para os arquivos fora de `src/`, o estado anterior foi reconstruido pelo inverso exato de cada edicao, com assercao de que cada trecho aparece uma vez.

## Pendencias

- `OPP-20261003-FLAT`: com a raiz do pacote limpa, virou uma movimentacao de quatro pastas e a remocao do diretorio.
- `OPP-20261003-PAST`: absorveu os dois renomes que sairam deste lote.
- `OPP-20261003-INIT`: segue com recomendacao de nao rotear.
- `README.md` do registro de refactor continua dizendo que o harness "nao pode mais rodar" e que a suite tem 76 testes.
