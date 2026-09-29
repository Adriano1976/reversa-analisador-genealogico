---
schema_version: 1
id: OPP-20260929-U2NK
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
    - safety-net/pytest-before.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: Remove o import do modulo re, que nenhum ponto do arquivo le e que nenhuma entrada dinamica alcanca
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-09-29T00:00:00-03:00
reversible_via: [CHG-001.diff]
---

## O que foi feito

Removida a linha `import re` de `reconstructed/dna_analysis.py`. O arquivo passou de 396 para 395
linhas. A citacao da regex de ID no docstring do modulo e a implementacao dela permanecem intactas.

## Prova de morte

O verbo `prune` exige duas condicoes, e as duas foram verificadas por varredura completa, com o
resultado cru gravado em `before-after/death-proof.txt`.

**Condicao 1, sem referencia estatica:** o token `re` aparece **uma unica vez** no arquivo inteiro, e
essa ocorrencia e a propria linha de import. Nao existe nenhum uso de `re.`. Nenhum modulo do
repositorio importa `re` a partir de `dna_analysis`.

**Condicao 2, sem entrada dinamica:** zero ocorrencias de `globals()`, `getattr`, `__import__`,
`importlib`, `eval(` e `exec(` no arquivo. Um `import` comum nao e alcancavel por string, rota,
configuracao ou feature flag.

## Conferencia contra a alma

O ponto de atencao real estava no docstring. A linha 12 afirma "Regex de ID `[A-Z]{2}\d{7}`", o que
faz parecer que o `re` serviria a essa regra. Nao serve: a regra e implementada na linha 166 com
`df[c].astype(str).str.fullmatch(r"[A-Z]{2}\d{7}")`, de forma vetorizada sobre a coluna do pandas. A
regra de negocio continua de pe, com uma ocorrencia de `str.fullmatch` antes e depois.

`re` continua importado e usado de fato em `domain.py:9` (uso na linha 41) e em `path_search.py:14`
(usos nas linhas 190 e 202). Nenhum desses depende deste import.

## Confirmação

- Suite completa antes: **76 passed** (`safety-net/pytest-before.txt`).
- Suite completa depois: **76 passed** (`safety-net/pytest-after-apply.txt`).
- Verificacao por importacao real depois da remocao: o modulo importa, `hasattr(dna_analysis, "re")`
  e `False`, e `aggregate_matches`, `match_candidates`, `build_ged_indexes` e `dna_analysis` seguem
  presentes.

## Risco declarado

Nenhum dentro do repositorio. Um consumidor externo que fizesse
`from reconstructed.dna_analysis import re` quebraria, mas esse uso seria um erro de quem consome, e
nao existe na arvore. A remocao e de uma vinculacao de modulo, nao de comportamento.

## Reversão

Pelo `CHG-001.diff`, ou por
`git checkout -- analisador-genealogico/reconstructed/dna_analysis.py`.
