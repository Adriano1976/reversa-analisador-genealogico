---
schema_version: 1
id: OPP-20261003-LMAY
display_number: 22
context: pacote-reconstructed
verb: standardize
title: dois modulos tem nome que descreve o que ja nao fazem
target:
  files: [src/reconstructed/text_cleaning.py]
  symbol: nome do modulo e os docstrings que o justificam
smell: nomenclatura fora do padrao do proprio pacote. Os demais modulos se chamam pelo que fazem (`matching`, `path_finding`, `mermaid_render`, `validate`), e este se chamava pelo que fazia
roi:
  confidence: green
  impact: clareza. O modulo nao faz dominio: depois da remocao das entidades mortas em 2026-09-30, contem apenas `strip_bad_utf` e `demojibake`. O nome custava uma leitura de docstring em cada uso
  cost: low
  est_return: nome alinhado ao papel real, incluindo os docstrings que hoje fariam um leitor novo procurar dominio onde nao ha
state: applied
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

Registrada com dois nomes a corrigir. Um deles deixou de existir antes de a oportunidade ser executada:

| Modulo | Nome sugere | Faz de fato | Situacao |
|---|---|---|---|
| `upload.py` | receber e gravar o arquivo enviado | le o GEDCOM ja gravado, constroi o grafo e mantem o estado global | **resolvido** pela `OPP-20261003-TWNT`: virou `gedcom_state.py` mais `gedcom_parser.py` |
| `domain.py` | camada de dominio | limpeza de mojibake, 84 linhas, duas funcoes | alvo desta transformacao |

O caso de `domain.py` vem da remocao das entidades `Family`, `GenealogyGraph` e `DNAGroup`, decidida pelo usuario em 2026-09-30. O modulo ficou com a parte que de fato era consumida, e o nome nao acompanhou. O docstring do proprio modulo precisa de tres paragrafos para explicar que o dominio ja nao esta ali.

## Transformacao proposta

| Antes | Depois |
|---|---|
| `domain.py` | `text_cleaning.py` |
| `upload.py` | `gedcom_state.py` mais `gedcom_parser.py`, entregue pela `OPP-20261003-TWNT` |

**Dependencia de ordem, satisfeita.** A padronizacao era mais barata depois da `OPP-20261003-TWNT`, porque o split de `upload.py` ja definia os nomes finais. Foi o que aconteceu: a `TWNT` veio primeiro e resolveu metade do alvo.

**Impacto fora do pacote, medido antes de aplicar.** Doze referencias vivas ao nome antigo, em seis arquivos: tres imports dentro do pacote, um no teste, um **dentro de uma string** no harness de paridade e sete citacoes em docstring, comentario e README. A armadilha e o import do harness: ele nao aparece em leitura de AST nem em `grep` por `import domain`, e se ficasse para tras o instrumento de paridade morreria com `ImportError`, sem medicao.

## Estado em 2026-10-03

**Aplicada.** O modulo virou `src/reconstructed/text_cleaning.py`, com o corpo identico provado por AST sem os docstrings, e as doze referencias foram atualizadas. O comentario do harness que descrevia duas implementacoes divergentes passou a registro historico, porque a `OPP-20260929-B5F2` unificou os corpos e as duas funcoes hoje sao **o mesmo objeto**. A arvore de `src/` no README, que estava desatualizada por tres transformacoes, passou a bater com o disco.

Registro completo, diffs por lote e evidencia em `../transformations/OPP-20261003-LMAY-padronizar-nomes-de-modulo/`.

Exclusoes declaradas: renomear `tests/test_domain.py`, remover o import morto `DM` do harness (e `prune`, nao `standardize`) e atualizar `_reversa_sdd/` e `_reversa_docs/`, que sao de outros donos.
