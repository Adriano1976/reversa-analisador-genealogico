---
schema_version: 1
id: OPP-20260929-Z6IO
display_number: 17
context: verificacao-de-tipos
verb: prune
title: Supressoes de tipo obsoletas apos conserto da config do pyrefly
target:
  files: [pyrefly.toml, tests/test_characterization_matching.py, tests/test_characterization_mermaid.py, tests/test_dna_analysis.py, tests/test_domain.py, tests/test_path_search.py, tests/test_upload.py]
  symbol: "# pyrefly: ignore [missing-import]"
smell: seis supressoes de tipo carregando peso por causa de uma config de analise estatica que nunca funcionou
roi:
  confidence: green
  impact: a config que governa a resolucao de imports na checagem de tipos estava silenciosamente inerte, e as supressoes escondiam isso
  cost: low
  est_return: a checagem de tipos passa a resolver o pacote reconstruido de fato, e seis anotacoes mortas saem dos testes
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras, .reversa/principles.md#ii-comportamento-observável-é-preservado-em-refatoração, .reversa/principles.md#iii-nenhuma-mudança-sem-teste-que-a-cubra]
  specs: [_reversa_sdd/architecture.md#5-dívidas-técnicas-identificadas]
---

## Antes observado

`pyrefly.toml` declarava o search path dentro de uma tabela `[pyrefly]`:

```toml
[pyrefly]
search_path = ["analisador-genealogico"]
```

Num `pyrefly.toml` autonomo as opcoes ficam no topo do documento. Dentro de uma tabela, o pyrefly
le `pyrefly` como chave desconhecida, descarta o arquivo inteiro e segue em frente. O proprio pyrefly
denuncia isso, em `dump-config`:

```
WARN pyrefly.toml: Extra keys found in config: pyrefly
Resolving imports from:
  Import root (inferred from project layout): "<raiz do projeto>"
```

O `analisador-genealogico` nunca entrava no search path, e `reconstructed` nunca resolvia. O efeito
colateral foi a criacao de seis supressoes `# pyrefly: ignore [missing-import]` nos arquivos de
teste, que passaram a ser a unica coisa mantendo o checador quieto.

O erro e silencioso por natureza: a config e descartada sem falhar, e quem olha as supressoes conclui
que sao desleixo, quando sao o contrario, sao a mitigacao de um defeito de configuracao.

## Prova

Antes e depois medidos com o mesmo comando, escopo do projeto inteiro:

| Medida | Antes | Depois |
|--------|-------|--------|
| Erros totais | 43 | 40 |
| `missing-import` | 18 | 1 |
| Avisos de config | 1 (`Extra keys found in config: pyrefly`) | 0 |
| Search path resolvido | ausente | `Search path (from config file): [".../analisador-genealogico"]` |

O unico `missing-import` que sobra e `harness`, em `_reversa_sdd/parity/_profile_collector_costs.py`,
artefato do proprio Reversa e sem relacao com os testes.

Com o search path valendo, cada uma das seis supressoes deixou de suprimir qualquer coisa. A remocao
foi medida: depois de remove-las, `missing-import` continua em 1 e `unused-ignore` e 0.

## Transformacao aplicada

Dois `CHG`, nesta ordem, porque o segundo depende do primeiro:

1. `CHG-001`, a config: a tabela `[pyrefly]` sai, `search-path` passa ao topo do documento, com o
   motivo escrito ao lado para que ninguem reintroduza a tabela.
2. `CHG-002`, as seis supressoes: uma linha removida em cada um dos seis arquivos de teste.

## Conferência contra a alma

O principio II se aplica por vacuidade: nada aqui toca comportamento observavel, porque os dois `CHG`
mexem em configuracao de ferramenta e em comentarios. Nenhuma regra de negocio, nenhum limiar,
nenhuma travessia de grafo e nenhuma tabela de cM foi tocada.

O principio III se aplica de verdade, e foi honrado: a suite foi medida antes e depois, com o antes
capturado de forma genuina, guardando as mudancas dos testes e rodando sobre o estado anterior.

## Rede de seguranca

- Suite antes, com as seis supressoes presentes: **76 passed** (`safety-net/pytest-before.txt`).
- Suite depois, com as seis supressoes removidas: **76 passed** (`safety-net/pytest-after-apply.txt`).
- `pyrefly check` antes: 43 erros, 18 `missing-import` (`before-after/pyrefly-check-antes.txt`).
- `pyrefly check` depois da config: 40 erros, 1 `missing-import` (`before-after/pyrefly-check-depois.txt`).
- `pyrefly check` depois da remocao das supressoes: 40 erros, 1 `missing-import`, 0 `unused-ignore`
  (`before-after/pyrefly-check-apos-supressoes.txt`).
- `dump-config` antes e depois (`before-after/dump-config-antes.txt` e `dump-config-depois.txt`).

## Risco declarado

O conserto expoe 35 erros de tipo que ja existiam e que a config inerte mascarava em parte, embora
`missing-import` fosse o unico tipo realmente suprimido pelas seis anotacoes. Esses erros
(`unsupported-operation`, `missing-attribute`, `no-matching-overload`, `bad-argument-type`,
`unbound-name` e outros) nao foram tratados aqui: ficam registrados como divida, e a oportunidade
`OPP-20260929-5XGJ`, que trata de imports, pode ser reavaliada junto deles.

Nao ha ganho de comportamento nesta transformacao. O ganho e que a ferramenta passa a medir o que
alegava medir.
