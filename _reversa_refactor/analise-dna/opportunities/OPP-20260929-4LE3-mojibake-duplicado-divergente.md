---
schema_version: 1
id: OPP-20260929-4LE3
display_number: 4
context: analise-dna
verb: modularize
title: Duas implementações divergentes de strip_bad_utf e demojibake
target:
  files: [analisador-genealogico/reconstructed/dna_analysis.py, analisador-genealogico/reconstructed/domain.py]
  symbol: strip_bad_utf, demojibake, MOJIBAKE_MAP
smell: funções de mesmo nome com corpos diferentes em dois módulos, uma delas sem uso em produção
roi:
  confidence: green
  impact: risco de correção no lugar errado. Quem for ajustar mojibake tem dois alvos plausíveis
  cost: low
  est_return: uma única autoridade sobre limpeza de nome, com a divergência documentada em vez de escondida
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/domain.md#23-regras-de-namespace-de-nome-matching-viral, _reversa_sdd/parity/harness.py#162]
---

## Executada dentro da B5F2 (2026-09-29)

Esta oportunidade **não teve transformação própria**: ela foi executada como o CHG-001 e o CHG-002 da
`OPP-20260929-B5F2`, que escolheu a opção B. `domain.py` passou a ser a autoridade da limpeza de nome,
com os corpos vivos extraídos de `dna_analysis` por AST, e `dna_analysis` passou a importar de
`.domain`. A duplicação deixou de existir e a divergência entre as duas implementações foi resolvida
em favor da que estava viva.

Prova: equivalência isolada do pipeline, pré-B5F2 contra pós-B5F2, com 2.206 comparações e zero
divergências, mais suíte verde. Ver
`../upload-gedcom/transformations/OPP-20260929-B5F2-unificar-limpeza-de-nome/transformation.md`.

Fica registrado aqui, e não apagado, porque a numeração e o histórico desta oportunidade explicam por
que a limpeza de nome tem um dono só.

## Recusa de verbo e dependência de decisão (2026-09-29)

Ao acionar `/reversa-restructure OPP-20260929-4LE3`, o especialista **recusou o alvo**, e com razão
pelas regras do próprio verbo: `restructure` melhora a estrutura interna de um trecho e "não move
módulos nem muda dependências". Resolver esta duplicação exige escolher um dono para a limpeza de
nome e fazer o outro módulo depender dele, o que é mudança de dependência entre módulos. O verbo
deste registro foi corrigido para **`modularize`**.

Mais importante: a varredura mostra que **esta oportunidade não tem existência independente**. Ela é
consequência de uma decisão que já está na fila, a `OPP-20260929-B5F2` (o que fazer com
`domain.py`):

| Decisão na B5F2 | O que acontece com a 4LE3 |
|-----------------|--------------------------|
| **Opção A**, remover `domain.py` e seus 14 testes | A duplicação **desaparece sozinha**. Sobra apenas a implementação viva de `dna_analysis.py`, e não há mais nada a unificar. A 4LE3 deixa de existir como trabalho |
| **Opção B**, promover `domain.py` a autoridade | A 4LE3 passa a ser a execução dessa promoção: `dna_analysis` deixa de ter as suas cópias e passa a importar de `domain`. É `modularize`, com a dependência invertida |

Ou seja: não faz sentido rotear a 4LE3 antes de decidir a B5F2. Registrado como item que **não deve
ser roteado** enquanto a decisão não existir.

Varredura que sustenta isso: existem exatamente duas definições de cada função, sem terceira cópia.
`domain.py:29,43` (morta na aplicação, chamada só dentro de `register_person`, que também é morto, e
pelos testes e pelo harness) e `dna_analysis.py:74,147` (viva, chamada nas linhas 94, 207 e 378).
Nenhum outro módulo define ou importa qualquer das duas.

## Antes observado

Existem duas famílias de funções com os mesmos nomes:

| Função | `dna_analysis.py` (viva) | `domain.py` (morta na aplicação) |
|--------|--------------------------|----------------------------------|
| `strip_bad_utf` | Linhas 74-90: dicionário de 15 correções (`Ã§` para `ç`, `JoA?o` para `João`, ...) mais `re.sub` de saneamento | Linhas 29-40: apenas remove `U+FFFD` |
| `demojibake` | Linhas 147-157: tenta `encode("latin1").decode("utf-8")` e valida o resultado | Linhas 43-57: aplica `MOJIBAKE_MAP` e dois `replace` fixos |

Os corpos são diferentes e os resultados não coincidem. A autoridade de fato é `dna_analysis.py`,
porque é ela que o fluxo de análise usa.

A evidência mais forte de que a divergência é conhecida está no harness:
`_reversa_sdd/parity/harness.py:203-205` comenta que `domain.strip_bad_utf` "só remove U+FFFD" e que
`domain.demojibake` é "implementação diferente", concluindo que comparar `domain.strip_bad_utf` com o
oráculo gera "FALSO POSITIVO de divergência". Ou seja: o harness trata as funções de `domain.py` como
não autoritativas.

## Transformação proposta

1. Declarar `dna_analysis.py` como autoridade da limpeza de nome, no docstring do módulo.
2. Reduzir `domain.py` a entidades de domínio, sem as duas funções, ou mantê-las delegando para as de
   `dna_analysis.py`, conforme a decisão sobre a `OPP-20260929-B5F2` (o módulo inteiro está em questão).
3. Registrar no docstring por que a versão do oráculo não foi preservada: é decisão de fidelidade já
   tomada, e o harness a documenta.

A escolha entre remover e delegar depende do que se decide sobre `domain.py`. As duas oportunidades se
resolvem juntas, mas foram registradas separadas porque o verbo e a prova são diferentes.

## Rede de segurança exigida

- `tests/test_domain.py` cobre as funções de `domain.py` com expectativas próprias, alinhadas ao corpo
  de `dna_analysis.py` (o teste de `demojibake` verifica cedilha e o mapa conhecido). Conferir se os
  dois corpos satisfazem os mesmos testes é o primeiro passo da caracterização.
- `tests/test_dna_analysis.py` verde.

## Risco

Médio se a remoção for feita sem conferir o teste. `tests/test_domain.py` afirma coisas sobre
`demojibake` que o corpo de `dna_analysis.py` pode não satisfazer, porque o mapa de entrada difere.
Antes de mexer, rodar os testes de `domain.py` contra as funções de `dna_analysis.py` e ver o que
quebra. Se quebrar, a divergência é real e maior do que parece: dois contratos para o mesmo nome.
