---
schema_version: 1
id: OPP-20260929-B5F2
verb: modularize
state: applied
safety_net:
  kind: characterization
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/impacto-da-opcao-b.txt
    - safety-net/equivalence-after-apply.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/domain.py
    purpose: Recebe, verbatim, os corpos vivos de strip_bad_utf e demojibake, extraidos de dna_analysis por AST, e perde o MOJIBAKE_MAP que so a implementacao morta usava
    diff: CHG-001.diff
  - chg: CHG-002
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: Perde as duas definicoes locais e passa a importar de .domain, sem criar ciclo
    diff: CHG-002.diff
  - chg: CHG-003
    kind: test
    artifact: tests/test_domain.py
    purpose: Deixa de importar MOJIBAKE_MAP e substitui a assercao que descrevia a implementacao morta por uma assercao do comportamento vivo
    diff: CHG-003.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff, CHG-002.diff, CHG-003.diff]
---

## O que foi feito

A opção B da `OPP-20260929-B5F2`: `domain.py` passou a ser a **autoridade única** da limpeza de nome,
absorvendo as funções que o `dna_analysis` usava de fato, e `dna_analysis` passou a importar de
`.domain`. Com isso o módulo deixou de ser morto sem remover nenhum teste, e a duplicação registrada
na `OPP-20260929-4LE3` deixou de existir.

Nenhum corpo de função foi redigitado. Os dois que migraram foram **extraídos por AST** do próprio
arquivo vivo, então o código executado é literalmente o mesmo objeto: a verificação confirma
`dna_analysis.strip_bad_utf is domain.strip_bad_utf` e o mesmo para `demojibake`.

## O que a medição corrigiu antes de aplicar

A descrição original da opção B afirmava que ela preservava os 50 testes. Isso estava **impreciso**, e
a checagem empírica mostrou por quê:

| Entrada | `domain` antes | `dna_analysis` vivo | Igual? |
|---------|----------------|---------------------|--------|
| `demojibake("FranÃ§isco")` | `'Françisco'` | `'Françisco'` | sim |
| `demojibake("A\u0303")` | `'Ã'` | `'A\u0303'` | não |
| `strip_bad_utf("FranÃ§isco")` | `'FranÃ§isco'` | `'Françisco'` | não |
| `strip_bad_utf("GouvA\ufffdo")` | `'GouvAo'` | `'Gouvço'` | não |
| `strip_bad_utf(None)` | `'None'` | `''` | não |

São 5 divergências em 9 casos para `strip_bad_utf` e 3 em 9 para `demojibake`. As duas implementações
não eram variações da mesma ideia: eram funções diferentes com o mesmo nome.

Rodando as asserções de `tests/test_domain.py` contra os corpos vivos, **1 de 6 quebrava**:
`test_demojibake_applies_known_map`, que afirmava que `demojibake("A\u0303")` conteria `"Ã"`. Esse
comportamento só existia na implementação morta. O teste estava caracterizando código que o sistema
não executava, e a mudança da expectativa foi aprovada explicitamente pelo usuário antes da aplicação.

`MOJIBAKE_MAP` era importado por `tests/test_domain.py:19`. Mantê-lo produziria código morto novo;
removê-lo sem ajustar o import derrubaria o módulo inteiro na coleta, com 14 testes. Por isso o
CHG-003 trata as duas coisas juntas.

## Preservação de comportamento

A prova é de **equivalência de saída**, isolada nesta transformação: o estado anterior foi congelado
em `.pytest-tmp/state-pre-b5f2/` e comparado com o posterior, no pipeline completo de `dna_analysis`
sobre o corpus sintético.

| Rede | Resultado |
|------|-----------|
| Equivalência isolada, pré contra pós | 2.206 comparações, **0 divergências** |
| Suíte completa | **76 passed**, sem nenhum teste removido |
| Ciclo de import | nenhum: `domain.py` tem zero imports relativos; a dependência é dna para domain |

O comportamento observável do sistema não muda porque o código executado é o mesmo. O que mudou foi o
comportamento de `domain.demojibake` e `domain.strip_bad_utf` vistos **de fora**, e isso só era
observado pelos testes do próprio módulo morto e por `register_person`, que não é chamado.

## Estado dos arquivos

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/domain.py` | 124 linhas, com `MOJIBAKE_MAP` e duas implementações próprias | 121 linhas, autoridade única, sem `MOJIBAKE_MAP` |
| `reconstructed/dna_analysis.py` | 421 linhas, com duas definições locais | 394 linhas, importando de `.domain` |
| `tests/test_domain.py` | 124 linhas, importando `MOJIBAKE_MAP` | 131 linhas, afirmando o comportamento vivo |

## Reversão

Pelos três diffs, ou por `git checkout --` dos três arquivos. O estado congelado em
`.pytest-tmp/state-pre-b5f2/` permite refazer a comparação a qualquer momento.
