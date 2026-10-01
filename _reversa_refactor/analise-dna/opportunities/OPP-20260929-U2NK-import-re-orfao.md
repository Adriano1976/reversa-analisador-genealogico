---
schema_version: 1
id: OPP-20260929-U2NK
display_number: 16
context: analise-dna
verb: prune
title: Import re orfao no modulo de analise de DNA
target:
  files: [analisador-genealogico/reconstructed/dna_analysis.py]
  symbol: import re
smell: importacao sem nenhum uso estatico e sem entrada dinamica no modulo
roi:
  confidence: green
  impact: clareza do modulo e uma pista falsa sobre onde a regex de ID vive
  cost: low
  est_return: uma linha a menos e nenhuma ambiguidade sobre a origem da regex de ID
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/analise-dna/design.md]
---

## Antes observado

`analisador-genealogico/reconstructed/dna_analysis.py:16` importa o modulo `re`. Nenhum ponto do
arquivo le o nome: a varredura de `\bre\.` no arquivo inteiro retorna zero ocorrencias. O import
existe desde a reconstrucao e nao acompanha nenhum uso.

O ponto que exige cuidado esta no docstring do proprio modulo. A linha 12 afirma
"Regex de ID `[A-Z]{2}\d{7}`", o que faz parecer que o `re` serve a essa regra. Nao serve: a regra e
implementada na linha 166 com `df[c].astype(str).str.fullmatch(r"[A-Z]{2}\d{7}")`, de forma
vetorizada sobre a coluna, e o modulo `re` nao participa dela. A regra de negocio continua de pe
sem esta linha.

## Prova de morte

O verbo `prune` exige as duas condicoes, e as duas foram verificadas por varredura completa.

**Condicao 1, sem referencia estatica:**

| Verificacao | Resultado |
|-------------|-----------|
| Usos de `re.` em `dna_analysis.py` | 0 |
| Modulos que importam `re` a partir de `dna_analysis` | 0 |
| Quem mais importa `re` no pacote | `domain.py:9` (usado na linha 41) e `path_search.py:14` (usado nas linhas 190 e 202), ambos com uso efetivo e independentes deste import |

**Condicao 2, sem entrada dinamica:** o modulo nao contem `globals()`, `getattr`, `__import__`,
`importlib`, `eval` nem `exec`. `import re` e uma vinculacao de modulo comum, nao alcancavel por
string, configuracao, rota ou feature flag.

**Conferencia contra a alma:** nenhuma regra de negocio confirmada e servida por esta linha. A regex
de ID, que e regra confirmada, vive no `str.fullmatch` do pandas e permanece intacta.

Classificacao: **morto**, elegivel para remocao. Nao ha orfao suspeito nesta oportunidade.

## Transformacao proposta

Remover a linha 16. Um arquivo, uma linha, um `CHG`. Reversivel pelo diff.

## O que NAO sera removido

| Item | Por que fica |
|------|--------------|
| A citacao da regex de ID no docstring, linha 12 | Descreve comportamento real do modulo |
| A implementacao da regex, linha 166 | Executa a regra confirmada, via pandas |
| `import re` em `domain.py:9` e `path_search.py:14` | Tem uso efetivo, nas linhas 41, 190 e 202 |
| `from __future__ import annotations`, linha 14 | Diretiva de compilador, aparece uma vez por nao ter uso em tempo de execucao |
| `string` e `unicodedata`, linhas 17 e 18 | Tem uso efetivo no arquivo |

## Rede de seguranca exigida

Suite completa antes e depois. A remocao nao altera nenhum resultado observavel, porque nenhum ponto
do modulo le o nome `re`.

## Risco

Nenhum identificado. Se algum consumidor externo ao repositorio fizer `from reconstructed.dna_analysis
import re`, a remocao o quebraria, mas esse uso seria um erro de quem consome, e nao existe no
repositorio.

---
*Gerado pelo Reversa-Refactor em 2026-09-29.*
