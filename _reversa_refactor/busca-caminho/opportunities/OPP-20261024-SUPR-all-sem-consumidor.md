---
schema_version: 1
id: OPP-20261024-SUPR
display_number: 56
context: busca-caminho
verb: standardize
title: Quatro nomes em __all__ sem um único consumidor
target:
  files:
    - src/core/documentary_relationship.py
  symbol: __all__
smell: >
  O módulo declara dezoito nomes públicos. Quatro deles não são importados de lugar
  nenhum, e dois são reexportações que o comentário do próprio arquivo justifica como
  "para quem já os importava". A justificativa não se sustenta na medição.
roi:
  confidence: green
  impact: >
    `__all__` é a superfície anunciada do módulo, e dezesseis módulos decidem o que
    importar olhando para ela. Nome anunciado sem cliente faz o próximo leitor supor um
    consumidor que não existe, e impede que a remoção seja reconhecida como segura.
  cost: low
  est_return: >
    `__all__` com catorze nomes, cada um com pelo menos um importador verificado, e o
    comentário das reexportações corrigido para dizer só o que é verdade.
state: applied
traceability:
  soul: [.reversa/soul.md#e7-parentesco_documental]
  specs:
    - _reversa_sdd/busca-caminho/design.md
---

## Antes observado

Varredura por AST de todo o repositório ( `src/`, `tests/`, `_reversa_bugs/`,
`_reversa_sdd/`, `_reversa_forward/` ), contando importação explícita de cada nome:

| Nome em `__all__` | Importadores | Situação |
|---|---|---|
| `documentary_relationship` | 10 | núcleo da superfície |
| `homonym_dossier` | 17 | idem |
| `birth_date` | 15 | idem |
| `parse_year` | 13 | idem |
| `person_summary` | 4 | idem |
| `documentary_label` | 4 | idem |
| `intervalo_de_geracao_mediano` | 3 | idem |
| `nome_do_grau` | 2 | reexport usado por dois testes |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | 2 cada | usado por `cirurgia_do_grafo` e `validator` |
| `documental_nao_encontrado` | 1 | usado por `passo_por_kit` |
| `normalizar` | 1 | usado por um teste |
| `death_date` | 1 | **só** sonda congelada em `_reversa_bugs/` |
| `get_children` | 1 | **só** sonda congelada em `_reversa_bugs/` |
| `hop_evidence` | **0** | usado só dentro do próprio módulo |
| `find_all_common_ancestors` | **0** | usado só dentro do próprio módulo |
| `ROMANO` | **0** | reexport sem nenhuma importação |
| `MAX_DEPTH` | **0** | reexport sem nenhuma importação |

Também verificado: nenhum arquivo do repositório faz `from ... import *`, então mexer em
`__all__` não altera nenhuma importação existente.

## O que a medição desmente

O bloco de comentário das linhas 777 a 779 afirma que `nome_do_grau`, `ROMANO` e
`MAX_DEPTH` continuam públicos "para quem já os importava". Vale para `nome_do_grau`, que
dois testes importam daqui de propósito. Não vale para `ROMANO` nem para `MAX_DEPTH`: a
varredura não encontra uma única importação dos dois a partir deste módulo. `ROMANO` é
usado internamente, por `documentary_label`, através do import da linha 36; `MAX_DEPTH` é
usado na mensagem de `documental_nao_encontrado`, e quem o importa de verdade pede a
`core.path_finding`.

É a mesma classe de achado da `OPP-20261006-ESKO`, que encontrou dezoito nomes em
`__all__` de `core/path_search.py`, dos quais doze nunca eram usados pelo módulo, e um
docstring com lista de consumidores inventada.

## Transformação proposta

1. remover `ROMANO`, `MAX_DEPTH`, `hop_evidence` e `find_all_common_ancestors` de
   `__all__`, mantendo as quatro funções e constantes onde estão: elas continuam
   importáveis por nome, apenas deixam de ser anunciadas;
2. reescrever o comentário das linhas 777 a 779 para citar apenas `nome_do_grau`, o único
   reexport com importador;
3. manter `death_date` e `get_children` em `__all__`. Os dois têm um importador real, ainda
   que congelado em `_reversa_bugs/`, e esse caminho não está liberado pela config. A
   `OPP-20261023-DOCF` já registrou o custo de tratar consumidor congelado como ausente.

## Fronteira de comportamento

Nenhuma. `__all__` não governa importação explícita, e não há `import *` no repositório.
As quatro funções e constantes continuam no módulo, com o mesmo nome e a mesma assinatura.

## Onde isto encaixa na ordem

Último da fila, entre as cinco desta auditoria: é o de menor retorno e o único que fica
mais barato depois que a `OPP-20261024-SEPM` decidir quais nomes cada módulo novo
realmente precisa anunciar. Se a `SEPM` for aprovada antes, esta se aplica sobre a
fachada já reduzida.

## Aplicada em 2026-10-24

Aprovada em plano e em diff, aplicada pelo `/reversa-standardize` na mesma data, depois da
`SEPM`, como a ordem previa.

| Antes | Depois |
|---|---|
| 18 nomes anunciados, 4 sem importador | **14 nomes**, cada um com importador verificado |
| comentário afirmando que `ROMANO` era reexportado "para quem já o importava" | comentário cita apenas `nome_do_grau`, que dois testes importam daqui |
| 1635 testes | 1635 testes, nada mudou de estado |

Nenhum import foi tocado: os quatro nomes continuam no módulo e continuam importáveis por
nome. A leitura agressiva, apagar o import de `ROMANO`, foi descartada porque `__all__` é
anúncio e a importação é comportamento.

`death_date` e `get_children` ficaram, com a medição: os dois têm consumidor real, ainda que
congelado em `_reversa_sdd/` e `_reversa_bugs/`.

O registro completo está no
[`transformation.md`](../transformations/OPP-20261024-SUPR-all-sem-consumidor/transformation.md).

---
*Gerado pelo Reversa-Refactor em 2026-10-24, na auditoria de `src/core/documentary_relationship.py`.*
