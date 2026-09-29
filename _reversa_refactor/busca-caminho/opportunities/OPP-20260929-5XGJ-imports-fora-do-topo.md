---
schema_version: 1
id: OPP-20260929-5XGJ
display_number: 15
context: busca-caminho
verb: standardize
title: imports fora do topo em path_search.py
target:
  files: [analisador-genealogico/reconstructed/path_search.py]
  symbol: import de .upload em três formatos diferentes
smell: o mesmo módulo é importado no topo, dentro de uma função e no rodapé do arquivo, sem explicação
roi:
  confidence: green
  impact: quem lê precisa entender por que três formatos coexistem, e um deles tem supressão de aviso
  cost: low
  est_return: uma única regra de import no arquivo, com o motivo escrito
state: proposed
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/busca-caminho/design.md#estado-interno]
---

## Antes observado

O módulo importa `upload` de três formas, e nada no arquivo explica a diferença:

| Linha | Forma |
|-------|-------|
| 20 | `from .upload import child_to_family, families, get_name, people` |
| 131 | `from .upload import graph`, **dentro de uma função** |
| 494 | `from .upload import ref_id  # noqa: E402`, no **rodapé do arquivo**, com aviso suprimido |

A razão existe, mas está implícita, e é sutil: `people`, `families` e `child_to_family` são mutados
in place por `load_gedcom_and_build_graph`, então um import no topo continua apontando para o objeto
vivo. Já `graph` é **reatribuído** (`graph = new_graph`), então um import no topo ficaria preso ao
valor antigo. Daí o import tardio.

Esta é a única ocorrência de `# noqa: E402` no projeto, e o aviso foi silenciado em vez de explicado.

## Transformação proposta

Padronizar sem mudar comportamento:

1. Mover o import do rodapé para o topo. `ref_id` é uma função, não é reatribuída, então o import no
   topo é seguro.
2. Manter o import de `graph` dentro da função, porque a semântica exige, mas **com um comentário de
   uma linha** dizendo exatamente isso: reatribuído a cada parse, por isso não pode vir do topo.
3. Repetir a distinção no bloco de imports do topo, para quem lê não precisar descobrir.

Nenhum corpo de função muda e nenhuma saída muda.

## Rede de segurança exigida

Suíte completa verde, com destaque para `tests/test_path_search.py` e
`tests/test_characterization_matching.py`, que exercitam o caminho que usa `graph` e o que usa
`people`.

## Risco

Baixo, mas não nulo, e o risco é exatamente o que o comentário vai documentar: mover o import de
`graph` para o topo **quebraria** o fluxo, porque depois do primeiro parse o nome ficaria apontando
para o grafo antigo. A transformação não faz isso; ela apenas documenta por que não faz.

## Observação

Retorno pequeno, custo pequeno. A `OPP-20260929-UXEF` vai tocar este mesmo arquivo para separar busca
de render, e é provável que resolva isto de passagem. As duas não devem ser feitas ao mesmo tempo.
