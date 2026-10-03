---
schema_version: 1
id: OPP-20261003-FLAT
display_number: 23
context: pacote-reconstructed
verb: modularize
title: o pacote reconstructed e um nivel de pacote que nao expressa responsabilidade
target:
  files: [src/reconstructed/]
  symbol: o nivel de pacote inteiro, tres subpacotes e cinco modulos soltos
smell: o nivel `reconstructed` existe pela proveniencia do codigo (foi reconstruido do legado), e nao por uma responsabilidade. As tres responsabilidades ja estao expressas nos subpacotes `parsers/`, `core/` e `reporting/`, entao o nivel de cima so acrescenta um componente a todo import (`reconstructed.core.matching`) sem informar nada. Nao ha outro nivel na arvore nomeado por um evento em vez de por funcao
roi:
  confidence: green
  impact: clareza da arvore e um nivel a menos em todo caminho de import. O pedido veio do usuario, e o argumento tecnico a favor e que o nome descreve historia, nao papel. Contra: dispara o watch `W001` e mexe em import de novo, pela terceira vez na serie
  cost: medium
  est_return: o codigo do nucleo pendurado direto em `src/`, sem o nivel de pacote intermediario
state: applied
traceability:
  soul:
    - .reversa/soul.md#proposito
    - .reversa/soul.md#decisoes-fundadoras
  specs:
    - _reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md#watch-principal
    - _reversa_sdd/addenda/003-renomear-pasta-app-para-src.md#atualizacao-2026-10-03
---

## Antes observado

A arvore de hoje, depois da `OPP-20261003-GUE7`, tem **18 modulos** em quatro niveis, sendo que os tres subpacotes ja expressam os papeis:

```text
src/
├── app.py
└── reconstructed/          <-- este nivel nao expressa papel nenhum
    ├── __init__.py
    ├── parsers/            gedcom_parser, csv_ingest
    ├── core/               cm_estimator, matching, name_normalization, path_finding, family_navigation
    ├── reporting/          mermaid_render
    ├── gedcom_state.py
    ├── text_cleaning.py
    ├── validate.py
    ├── path_search.py
    └── dna_analysis.py
```

O pedido do usuario e levar tudo o que esta em `reconstructed/` para `src/`, e apagar `reconstructed/` quando ele ficar vazio.

## Superficie medida

| Onde | Referencias vivas a `reconstructed` |
|---|---|
| `_reversa_sdd/parity/harness.py` | 7, sendo **1 dentro da string do coletor** |
| `_reversa_sdd/parity/_verify_fix_gives_parity.py` | 6 |
| `src/app.py` | 4 |
| seis arquivos de teste | 18 |
| `README.md` | 3 |
| `_reversa_sdd/parity/_check_split_types.py` | 2 |
| `src/reconstructed/path_search.py` | 1 |
| `pyrefly.toml` | 1 |
| **total** | **45 referencias em 15 arquivos, das quais 31 sao linhas de import** |

## Transformacao proposta

Mover os tres subpacotes e os cinco modulos soltos para `src/`, apagar `reconstructed/` (incluindo o `__init__.py`, cuja citacao ao nome do projeto e intencional pela observacao O5 da feature 003), e reescrever os imports:

| Antes | Depois |
|---|---|
| `from reconstructed.parsers import gedcom_parser` | `from parsers import gedcom_parser` |
| `from .core.name_normalization import (` | `from core.name_normalization import (` |
| `from reconstructed.path_search import path_search` | `from path_search import path_search` |

`pyrefly.toml` continua com `search-path = ["src"]`, e continua correto: e justamente porque `src` e raiz de caminho que os subpacotes passam a ser alcancaveis direto.

## Dois conflitos declarados, que precisam de decisao antes do gate

**1. Esta transformacao dispara o watch `W001`.** A condicao vigiada e literalmente *"o pacote do nucleo continua sendo importado pelo mesmo nome, `reconstructed.*`"*, e o gatilho de alerta e *"mudanca do nome do pacote do nucleo"*. O pedido e exatamente esse gatilho. Nao e proibicao: e um item de vigilancia de regressao criado pela feature 003, e a regra do framework e que ele seja avaliado, nao ignorado. A avaliacao honesta e: **nenhuma regra de negocio do nucleo muda**, a suite e a paridade continuam provando comportamento, e o que muda e o nome pelo qual o nucleo e importado. Se o usuario aceitar, o watch precisa ser atualizado na mesma feature.

**2. `src/__init__.py` nao entra aqui.** O exemplo do usuario inclui esse arquivo, e ele tem oportunidade propria (`OPP-20261003-INIT`), porque contradiz a `RN-01` da feature 003. Esta transformacao funciona **sem** ele: `src` continua raiz de caminho, e os tres subpacotes continuam pacotes regulares com o `__init__.py` deles.

## Ordem de encadeamento recomendada

Esta e a `OPP-20261003-RAIZ` andam juntas, e a ordem importa. Achatar **sem** distribuir os cinco modulos soltos troca um problema por outro: `gedcom_state`, `text_cleaning`, `validate`, `path_search` e `dna_analysis` passariam a ser nomes de modulo de **primeiro nivel** no caminho de importacao, com risco de colisao com qualquer pacote instalado de nome parecido. A ordem correta e: distribuir primeiro (`RAIZ`), achatar depois (`FLAT`), ou as duas no mesmo gate com um plano unico.

## Estado em 2026-10-03

**Aplicada.** A `RAIZ` veio primeiro e esvaziou a raiz do pacote, e o achatamento virou o que o plano previa: subir quatro pastas e apagar o diretorio. Foram 12 imports relativos entre subpacotes convertidos em absolutos, 31 linhas de import sem o prefixo `reconstructed.` e 10 citacoes em prosa ajustadas, com **zero linha de logica alterada**.

Tres coisas ficaram registradas alem do plano:

1. **Os imports entre subpacotes deixaram de poder ser relativos.** Agora que os quatro pacotes sao de primeiro nivel, `from ..X` e invalido. E uma mudanca de estilo de import, declarada no registro da transformacao.
2. **O `_verify_fix_gives_parity.py` tinha codigo apontando para `src/reconstructed`**, que deixou de existir. Quarta aparicao dessa classe de defeito na serie, e segunda seguida no mesmo arquivo. A conferencia passou a verificar os tres caminhos que o script monta.
3. **O watch `W001` foi reescrito** para a nova identidade do nucleo, com a avaliacao registrada. Sem isso ele ficaria permanentemente vermelho.

Risco declarado, e nao realizado: `core`, `parsers`, `reporting` e `utils` passaram a ser nomes de primeiro nivel, e os quatro estao **livres** em `site-packages` hoje.

Registro completo, cinco diffs e evidencia em `../transformations/OPP-20261003-FLAT-achatar-o-nivel-de-pacote/`.

