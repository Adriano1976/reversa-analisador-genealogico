---
schema_version: 1
id: OPP-20261023-ORQA
verb: restructure
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - safety-net/equivalencia.py
    - safety-net/equivalencia-antes.txt
    - safety-net/equivalencia-depois.txt
    - safety-net/equivalencia-no-projeto.txt
    - safety-net/suite-antes.txt
    - safety-net/suite-depois.txt
measurement:
  before: >
    `dna_analysis` com 539 linhas e 21 condicionais; laço por kit de 370 linhas
    capturando 18 nomes do escopo; módulo com 1.094 linhas
  after: >
    `dna_analysis` com 205 linhas e 13 condicionais; `_cartao_do_kit` com 368
    linhas recebendo 4 parâmetros e um contexto de 13 campos; módulo com 1.181
change_set:
  - chg: CHG-001
    file: src/core/dna_analysis.py
    purpose: >
      introduz `_ContextoDaAnalise`, promove `_dossie` a função de módulo, extrai
      `_cartao_do_kit` e troca o `continue` do caso sem candidato por retorno
  - chg: CHG-002
    file: tests/test_profundidade_do_caminho.py
    purpose: >
      troca a guarda textual da chamada por guarda por AST, que era o que prendia
      o teste aos nomes dos argumentos
approval:
  by: user
  at: 2026-10-23T15:02:18-03:00
  plan_at: 2026-10-23T14:49:31-03:00
reversible_via:
  - CHG-001-contexto-e-passo-por-kit.diff
  - CHG-002-guarda-por-ast.diff
---

## O que foi feito, por passo nomeado

| Passo | Refatoração (Fowler) | Efeito medido |
|---|---|---|
| 1 | Introduce Parameter Object | `_ContextoDaAnalise`, 13 campos congelados, incluindo os dois caches da análise |
| 2 | Extract Function | `_dossie` deixou de ser closure e passou a operar o cache do contexto |
| 3 | Extract Method | as 370 linhas do laço viraram `_cartao_do_kit`, com 5 parâmetros |
| 4 | Replace Control Flag with Return | o `continue` do caso sem candidato virou `return None, descarte, evidencia_mitigada` |

Contagem por AST, antes e depois:

| Medida | Antes | Depois |
|---|---|---|
| linhas do módulo | 1.094 | 1.181 |
| linhas de `dna_analysis` | 539 | **205** |
| condicionais em `dna_analysis` | 21 | 13 |
| linhas de `_cartao_do_kit` | não existia | 368 |
| nomes capturados do escopo | 18 | 0 |
| `continue` em `_cartao_do_kit` | não existia | 0 |

O módulo cresceu 87 linhas porque entraram a classe de contexto, a função do
dossiê e dois docstrings. O número que importa é o da função orquestradora.

## Como a movimentação foi garantida

O corpo extraído foi reescrito por `tokenize`, trocando **apenas tokens NAME**.
Comentários e strings não foram tocados, o que importa porque o corpo é denso em
comentários que justificam decisões. Foram 38 substituições de nome.

Quatro verificações mecânicas no gerador, que aborta se falharem:

- o corpo extraído não referencia `skipped_matches` nem `sem_candidatos`;
- o corpo extraído não referencia `chave_nome`, que é variável do laço externo;
- a chamada de `_dossie` recebe o contexto;
- o arquivo gerado compila.

## O fail do primeiro gate, e o que ele ensinou

O `CHG-001` foi aplicado e a suíte voltou com **1 failed, 1624 passed**. O teste
`tests/test_profundidade_do_caminho.py::test_o_nucleo_exige_impossivel_e_caminho_para_vetar`
lia o texto do módulo e prendia a chamada literal:

```
assert "documental_nao_encontrado(arvore, root_id, pid" in nucleo
```

Com o contexto, a chamada virou `documental_nao_encontrado(contexto.arvore,
contexto.root_id, pid`. **O comportamento não mudou**: o digest de equivalência
seguiu idêntico nos três cenários, antes e depois. O que quebrou foi um teste que
amarrou a guarda aos nomes dos argumentos do momento.

O diff foi **revertido** antes de qualquer outra tentativa, o projeto voltou ao
estado verde, e a decisão de como resolver foi levada ao usuário, com três opções.
A escolhida foi trocar a guarda textual por guarda por AST (`CHG-002`), que:

- continua exigindo a chamada `documental_nao_encontrado`;
- continua exigindo os três primeiros argumentos posicionais;
- para de depender dos nomes desses argumentos.

A prova de que a guarda nova não é mais fraca nem mais acomodada: ela passa
**também no código anterior**, antes da refatoração (`79 passed` no arquivo).
Uma guarda que passasse só depois seria uma guarda ajustada ao resultado.

## Prova de equivalência

O `safety-net/equivalencia.py` roda `dna_analysis` em três cenários e faz sha256
do JSON canônico de `(resultados, descartados, mensagem, observações, cobertura)`.
Compara o dicionário inteiro, não campos escolhidos.

| Cenário | O que exercita |
|---|---|
| `utf8` | cartão com caminho documental |
| `duplicado` | dois kits somados para o mesmo nome |
| `sem_intersecao` | o caso sem candidato, que é o `continue` convertido em retorno |

```
antes    COMBINADO b8d186c81a59c24cab00cd2e64070c147d7c1a7a47825d138a300dfab570b5dd
depois   COMBINADO b8d186c81a59c24cab00cd2e64070c147d7c1a7a47825d138a300dfab570b5dd
```

## Rede de segurança

| Momento | Resultado |
|---|---|
| suíte antes | **1625 passed, 9 skipped** em 106,01 s |
| suíte depois de `CHG-001` sozinho | **1 failed, 1624 passed** em 88,55 s (revertido) |
| suíte depois dos dois `CHG` | **1625 passed, 9 skipped** em 108,78 s |
| arquivo da guarda, sozinho, depois | **79 passed** em 5,85 s |

## O que ficou de fora

`_cartao_do_kit` tem 368 linhas: ganhou nome, assinatura e testabilidade, mas o
corpo continua encadeando catorze etapas sem fronteira interna. A decomposição
interna é a `OPP-20261023-ETAP`, aberta no mesmo dia, e ela só ficou barata
**depois** desta transformação: com o contexto, cada etapa custa 3 a 5 parâmetros.

A assinatura pública de `dna_analysis`, a ordem de apresentação e o conteúdo do
cartão não mudaram.

## Reversão

`git apply -R` nos dois diffs, na ordem inversa. O `CHG-001` foi verificado com
`git apply --check` antes de aplicar, e o `CHG-002` com `git apply --check
--reverse` depois de aplicado.

---
*Aplicado em 2026-10-23 pelo Reversa-Refactor, sob gate de plano e de diff aprovados pelo usuário.*
