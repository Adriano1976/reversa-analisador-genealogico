---
schema_version: 1
id: OPP-20260929-Z6IO
verb: prune
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: death-proof
  evidence:
    - before-after/dump-config-antes.txt
    - before-after/dump-config-depois.txt
    - before-after/pyrefly-check-antes.txt
    - before-after/pyrefly-check-depois.txt
    - before-after/pyrefly-check-apos-supressoes.txt
    - safety-net/pytest-before.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: configuration
    artifact: pyrefly.toml
    purpose: Tira as opcoes da tabela [pyrefly] e as poe no topo do documento, que e onde o pyrefly as le num pyrefly.toml autonomo
    diff: CHG-001.diff
  - chg: CHG-002
    kind: code
    artifact: tests/test_characterization_matching.py, tests/test_characterization_mermaid.py, tests/test_dna_analysis.py, tests/test_domain.py, tests/test_path_search.py, tests/test_upload.py
    purpose: Remove as seis supressoes pyrefly missing-import, que deixaram de suprimir qualquer coisa depois do CHG-001
    diff: CHG-002.diff
approval:
  by: user
  at: 2026-09-29T00:00:00-03:00
reversible_via: [CHG-001.diff, CHG-002.diff]
---

## O que foi feito

Dois `CHG`, aplicados nesta ordem.

**`CHG-001`, a causa raiz.** `pyrefly.toml` passou de

```toml
[pyrefly]
search_path = ["analisador-genealogico"]
```

para

```toml
search-path = ["analisador-genealogico"]
```

com o motivo escrito ao lado, para que a tabela nao seja reintroduzida. O arquivo nao cresceu em
opcoes, so em explicacao.

**`CHG-002`, a consequencia.** Seis linhas removidas, uma em cada arquivo de teste:

| Arquivo | Linha removida |
|---------|----------------|
| `tests/test_characterization_matching.py` | `# pyrefly: ignore [missing-import]` |
| `tests/test_characterization_mermaid.py` | `# pyrefly: ignore [missing-import]` |
| `tests/test_dna_analysis.py` | `# pyrefly: ignore [missing-import]` |
| `tests/test_domain.py` | `# pyrefly: ignore [missing-import]` |
| `tests/test_path_search.py` | `# pyrefly: ignore [missing-import]` |
| `tests/test_upload.py` | `# pyrefly: ignore [missing-import]` |

Nenhum `import` foi alterado, nenhum teste foi tocado, nenhuma expectativa mudou.

## Prova de morte

A supressao nao e codigo executavel, entao a prova de morte tem a forma que lhe cabe: **o erro que
cada uma suprimia deixou de existir**. A cadeia e medida, nao argumentada.

**Primeiro, a config estava inerte.** `dump-config` antes listava apenas o import root e emitia
`Extra keys found in config: pyrefly`. O `analisador-genealogico` nao aparecia em lugar nenhum da
resolucao de imports.

**Segundo, o conserto faz o search path valer.** `dump-config` depois passa a listar:

```
Search path (from config file): [".../analisador-genealogico"]
```

e o aviso desaparece.

**Terceiro, o erro sumiu.** Medicao no projeto inteiro, mesmo comando:

| Medida | Antes | Depois do CHG-001 | Depois do CHG-001 e do CHG-002 |
|--------|-------|-------------------|-------------------------------|
| Erros totais | 43 | 40 | 40 |
| `missing-import` | 18 | 1 | 1 |
| `unused-ignore` | 0 | 0 | 0 |

O `missing-import` que sobra e `harness`, em `_reversa_sdd/parity/_profile_collector_costs.py`, que
nao tem relacao com os testes nem com as supressoes removidas.

**Quarto, a remocao nao custou nada.** Se alguma das seis supressoes ainda estivesse suprimindo algo,
o numero de `missing-import` teria subido de 1 para 7 no terceiro cenario da tabela. Ele ficou em 1.

## Conferência contra a alma

O principio II e atendido por vacuidade: nada aqui toca comportamento observavel. Os dois `CHG` mexem
em configuracao de ferramenta e em comentarios. Nenhuma regra de negocio confirmada de `domain.md`
foi tocada, nenhum limiar, nenhuma travessia de grafo, nenhuma faixa de cM.

O principio III foi honrado com medicao genuina, e nao por suposicao: ver a secao seguinte.

## Confirmação

- Suite antes, com as seis supressoes presentes: **76 passed**.
- Suite depois, com as seis removidas: **76 passed**.

O antes foi capturado de forma real, e nao reconstruido de memoria: as mudancas em `tests/` foram
guardadas com `git stash push -- tests/`, a suite rodou sobre o estado anterior e as mudancas foram
devolvidas com `git stash pop`. Sem isso, o `green_before` seria uma afirmacao sem lastro, ja que a
suite nao muda de resultado por causa de comentario.

## Risco declarado

A config consertada expoe 35 erros de tipo que antes ficavam em parte mascarados. Eles nao foram
tratados nesta poda, porque nenhum deles e `missing-import`: sao `unsupported-operation`,
`missing-attribute`, `no-matching-overload`, `bad-argument-type`, `unbound-name`, `bad-context-manager`
e outros. Ficam como divida registrada, e a oportunidade `OPP-20260929-5XGJ` deve ser reavaliada
junto deles.

Uma alternativa mais conservadora existia: manter as supressoes e consertar so a config. Foi
descartada porque deixaria seis anotacoes declarando um erro que a medicao mostra nao existir, que e
exatamente o tipo de pista falsa que o registro combate.

## Reversão

Pelos dois diffs, nesta ordem inversa: `CHG-002.diff` restaura as supressoes e `CHG-001.diff` restaura
a tabela. Reverter apenas o `CHG-001` reintroduz o defeito de configuracao e deixa as supressoes
novamente necessarias, entao os dois andam juntos.
