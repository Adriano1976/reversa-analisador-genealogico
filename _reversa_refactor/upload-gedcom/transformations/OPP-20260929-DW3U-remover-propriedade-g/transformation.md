---
schema_version: 1
id: OPP-20260929-DW3U
verb: prune
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: death-proof
  evidence:
    - before-after/death-proof.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/domain.py
    purpose: Remove a propriedade GenealogyGraph.g, que devolvia self.conexoes, atributo nunca definido em nenhum ponto da classe
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff]
---

## O que foi feito

Removida a propriedade `g` de `GenealogyGraph`, na opção B da oportunidade. Era o achado concreto do
registro: uma propriedade que devolvia `self.conexoes`, atributo que **nunca é definido** na classe.
Quem a chamasse receberia `AttributeError`, garantido.

## Prova de morte

Varredura no repositório inteiro, não só no app:

| Verificação | Resultado |
|-------------|-----------|
| Chamadas de `.g` fora da definição da classe | **0** |
| Pontos que definem o atributo `conexoes` | **0**, e a única menção a `conexoes` no projeto é a própria linha `return self.conexoes` |
| Usos de `GenealogyGraph` | 8, sendo 6 em `tests/test_domain.py`, 1 na definição da classe e 1 no docstring do módulo |
| Entrada dinâmica | nenhuma: a varredura por `getattr`, `setattr`, `globals()` e companhia continua encontrando apenas o `getattr(val, "xref_id", val)` do ged4py em `upload.py:30` |

Os 6 usos nos testes instanciam a classe e chamam `register_person`, `get_person` e
`register_family`. **Nenhum** acessa `.g`. Isso é o que torna a opção B barata: nenhum teste precisa
mudar, ao contrário da opção A, que removeria as entidades e derrubaria a linha de base.

## Conferência contra a alma

`g` não implementa regra de negócio confirmada. É um acessor preguiçoso para um grafo que o projeto
nunca guardou nessa classe: o grafo real vive em `upload.graph`, construído por `networkx`. A regra de
domínio que importa, a navegação pessoa a família, está em `path_search` e não depende disto.

## Confirmação

Verificado depois de aplicar, com importação real do módulo:

- `hasattr(GenealogyGraph, "g")` é `False`
- `register_person` mais `get_person` continuam funcionando
- `register_family` continua funcionando
- `DNAGroup` continua funcionando
- Suíte completa: **76 passed**

## Estado do arquivo

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/domain.py` | 121 linhas | 115 linhas |

## Reversão

Pelo `CHG-001.diff`, ou por
`git checkout -- analisador-genealogico/reconstructed/domain.py`.
