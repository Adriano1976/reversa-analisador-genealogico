---
schema_version: 1
id: OPP-20261003-LMAY
display_number: 22
context: pacote-reconstructed
verb: standardize
title: dois modulos tem nome que descreve o que ja nao fazem
target:
  files: [src/reconstructed/upload.py, src/reconstructed/domain.py]
  symbol: nomes de modulo e os docstrings que os justificam
smell: nomenclatura fora do padrao do proprio pacote. Os demais modulos se chamam pelo que fazem (`matching`, `path_finding`, `mermaid_render`, `validate`), e estes dois se chamam pelo que faziam
roi:
  confidence: green
  impact: clareza. `upload.py` nao faz upload: quem recebe e valida o arquivo HTTP e o `app.py`, com as decisoes em `validate.py`. `domain.py` nao tem dominio: depois da remocao das entidades mortas em 2026-09-30, contem apenas `strip_bad_utf` e `demojibake`. Os dois nomes custam uma leitura de docstring em cada uso
  cost: low
  est_return: nomes alinhados ao papel real, incluindo os docstrings que hoje fariam um leitor novo procurar upload onde nao ha
state: proposed
traceability:
  soul:
    - .reversa/soul.md#entidades-centrais
    - .reversa/soul.md#decisoes-fundadoras
  specs:
    - _reversa_sdd/code-analysis.md#1
    - _reversa_sdd/domain.md#2.3
    - _reversa_sdd/inventory.md#3
---

## Antes observado

| Modulo | Nome sugere | Faz de fato |
|---|---|---|
| `upload.py` | receber e gravar o arquivo enviado | le o GEDCOM ja gravado, constroi o grafo e mantem o estado global |
| `domain.py` | camada de dominio | limpeza de mojibake, 84 linhas, duas funcoes |

O caso de `upload.py` e o mais custoso. O docstring do proprio modulo ja registra a divergencia, e o historico do projeto mostra o preco: o defeito `BUG-20260929-QMLY` nasceu de um residuo de caminho de upload que vivia nesse arquivo e resolvia a pasta pelo diretorio corrente. Esse residuo foi removido em 2026-10-03, e com ele o modulo perdeu a ultima coisa que fazia jus ao nome.

O caso de `domain.py` vem da remocao das entidades `Family`, `GenealogyGraph` e `DNAGroup`, decidida pelo usuario em 2026-09-30. O modulo ficou com a parte que de fato era consumida, e o nome nao acompanhou.

## Transformacao proposta

Renomear os dois modulos para o papel real, mantendo os nomes publicos alcancaveis:

| Antes | Depois |
|---|---|
| `upload.py` | `gedcom_parser.py`, ou o par `gedcom_state.py` mais `gedcom_parser.py` se a oportunidade `OPP-20261003-TWNT` vier antes |
| `domain.py` | `text_cleaning.py` |

**Dependencia de ordem.** Esta padronizacao e mais barata se executada **depois** de `OPP-20261003-TWNT`, porque o split de `upload.py` ja define os dois nomes finais. Feita antes, o nome escolhido aqui teria de ser revisto logo em seguida.

**Impacto fora do pacote.** Renomear `domain.py` toca `tests/test_domain.py` e o harness de paridade, que importa `reconstructed.domain` pelo nome. Renomear `upload.py` toca sete arquivos de teste e o mesmo harness. E o caso que exige atualizar tambem a string de busca de `_reversa_sdd/parity/_verify_fix_gives_parity.py`, a mesma armadilha do D-08.
