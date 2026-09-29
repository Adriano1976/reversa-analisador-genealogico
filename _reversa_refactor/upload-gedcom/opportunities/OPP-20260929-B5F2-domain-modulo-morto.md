---
schema_version: 1
id: OPP-20260929-B5F2
display_number: 8
context: upload-gedcom
verb: prune
title: domain.py é módulo morto sustentado apenas pelos próprios testes
target:
  files: [analisador-genealogico/reconstructed/domain.py, tests/test_domain.py]
  symbol: Family, GenealogyGraph, DNAGroup, strip_bad_utf, demojibake
smell: módulo sem nenhum consumidor em produção, mantido vivo pela suíte que ele mesmo originou
roi:
  confidence: green
  impact: 124 linhas e 14 testes que não protegem nada do que roda; pistas falsas para quem investiga
  cost: low
  est_return: menos superfície de leitura, ao custo de decisão explícita sobre a linha de base de testes
state: proposed
traceability:
  soul: [.reversa/soul.md#entidades-centrais, .reversa/soul.md#lacunas-🔴-validação-humana]
  specs: [_reversa_sdd/architecture.md#3-erd-resumido, _reversa_sdd/reconstruction-plan.md#tarefa-01-entidades-de-domínio]
---

## Antes observado

Busca por importadores de `reconstructed.domain` em todo o `*.py` do projeto devolve exatamente dois:

| Consumidor | Uso |
|------------|-----|
| `tests/test_domain.py:15` | Importa `DNAGroup`, `GenealogyGraph`, `Family` e as funções de mojibake. É o único uso direto |
| `_reversa_sdd/parity/harness.py:162` | Importa o módulo, e o próprio harness comenta (linhas 203-205) que as funções de `domain.py` são implementação diferente e geram falso positivo de divergência |

Nenhum caminho de produção importa o módulo:

- `app.py` importa de `dna_analysis`, `path_search` e `upload`.
- `path_search.py` importa de `.upload`.
- `dna_analysis.py` importa de `.path_search` e `.upload`.

Achados adicionais dentro do módulo morto:

- `GenealogyGraph.g` (linhas 109-112) devolve `self.conexoes`, atributo que **nunca é definido** em
  nenhum ponto da classe. Chamar a propriedade levanta `AttributeError`. Nenhum teste a chama.
- `register_person` grava `name_clean` com o `demojibake` local, que diverge do `demojibake` vivo
  (ver `OPP-20260929-4LE3`).

## Transformação proposta

Duas saídas possíveis, e a escolha é do usuário porque uma delas mexe na linha de base de testes:

**Opção A, pruned.** Remover `domain.py` e `tests/test_domain.py`. A suíte cai de 50 para 36 testes.
Conflita com o princípio III, que exige os 50 testes passando antes e depois de qualquer refactor.
Exigiria, portanto, revisão explícita do princípio ou uma emenda que reconheça a remoção de testes
como resultado legítimo de `prune` comprovado.

**Opção B, promovida.** Transformar `domain.py` na autoridade de limpeza de nome e entidades,
absorvendo as funções de `dna_analysis.py` conforme a `OPP-20260929-4LE3`, e fazer `dna_analysis`
passar a importar dele. Aí o módulo deixa de ser morto e os 14 testes passam a proteger código vivo.
Não remove teste nenhum e não conflita com o princípio III.

A recomendação técnica deste registro é a **Opção B**: ela resolve o mesmo problema (duas
implementações divergentes) sem reduzir a rede de segurança, e o módulo já tem nome, docstring e
testes alinhados com a intenção original da Tarefa 01.

## Rede de segurança exigida

- Opção A: `preservation.method: death-proof` com a busca estática anexada, e confirmação humana sobre
  a linha de base de testes.
- Opção B: os 50 testes verdes antes e depois, e o harness de paridade verde.

## Risco

Na Opção A, o risco é de processo, não de código: derrubar 14 testes pode esconder que a suíte deixou
de cobrir mojibake, quando na verdade os testes de `dna_analysis` é que cobrem. Conferir a cobertura
efetiva antes de decidir.

## Ação bloqueada hoje

Qualquer das duas opções escreve em `analisador-genealogico/**` e `tests/**`, e o
`.reversa/reversa-config.json` está em `allowLegacyEdits: false`. O especialista vai travar no gate.
