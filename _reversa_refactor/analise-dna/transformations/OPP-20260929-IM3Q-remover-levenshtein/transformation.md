---
schema_version: 1
id: OPP-20260929-IM3Q
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
    kind: configuration
    artifact: analisador-genealogico/requirements.txt
    purpose: Remove python-Levenshtein, que nenhum arquivo importa e que a biblioteca consumidora nao exige
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff]
---

## O que foi feito

Removida a linha `python-Levenshtein` de `requirements.txt`. O manifesto passou de 7 para 6 linhas.

## Prova de morte

Três verificações independentes, todas reproduzíveis:

| Verificação | Resultado |
|-------------|-----------|
| Arquivos que importam `Levenshtein` | **0**, em todo o repositório |
| O que `thefuzz` exige | `['rapidfuzz <4.0.0,>=3.0.0']`, apenas |
| O que `thefuzz/fuzz.py` importa | `from rapidfuzz.fuzz import (` |

A terceira fecha o argumento: o `thefuzz` resolve para `rapidfuzz`, que é requisito próprio dele e
portanto sempre está instalado. O `python-Levenshtein` era o backend que o `thefuzz` usava em versões
antigas, antes de migrar para `rapidfuzz`. Nada no projeto o consome.

## Conferência contra a alma

Não há regra de negócio envolvida: é manifesto de dependência. O cálculo de similaridade de nomes, que
é regra de domínio confirmada em `domain.md`, continua idêntico, porque quem o executa é o `rapidfuzz`
antes e depois.

## Confirmação

- Suíte completa: **76 passed**, incluindo `tests/test_characterization_matching.py`, que congela as
  decisões do matching e depende do cálculo de similaridade.
- Nenhuma mudança de comportamento era esperada: a remoção é do manifesto, não do ambiente. A
  biblioteca continua instalada nesta máquina, e a suíte passa a rodar com ou sem ela, já que não é
  importada.

## Risco declarado

Remover do manifesto não desinstala de ambientes já montados. Um ambiente antigo com `thefuzz` preso a
uma versão que usava `python-Levenshtein` cairia no backend puro Python. O `requirements.txt` não
fixa versão de nada, então esse cenário já era possível por outro caminho, e é a dívida número 1 de
`architecture.md#5`, fora do escopo desta poda.

## Reversão

Pelo `CHG-001.diff`, ou por
`git checkout -- analisador-genealogico/requirements.txt`.

---
*Gerado pelo Reversa-Prune em 2026-09-29.*
