---
schema_version: 1
id: OPP-20260929-ZV52
display_number: 3
context: analise-dna
verb: modularize
title: dna_analysis mistura normalização, IO de CSV, agregação e matching
target:
  files: [analisador-genealogico/reconstructed/dna_analysis.py]
  symbol: módulo inteiro, 409 linhas
smell: arquivo que faz coisas demais, com cinco fronteiras de responsabilidade no mesmo lugar
roi:
  confidence: yellow
  impact: acoplamento e clareza. É o módulo mais difícil de testar em partes e o que mais muda
  cost: medium
  est_return: cada responsabilidade testável isoladamente, sem tocar em nenhuma regra de negócio
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras, .reversa/soul.md#entidades-centrais]
  specs: [_reversa_sdd/analise-dna/design.md#interface, _reversa_sdd/analise-dna/design.md#fluxo-principal]
---

## Antes observado

`dna_analysis.py` tem 409 linhas e cinco blocos que não compartilham motivo de mudança:

| Bloco | Linhas | Responsabilidade |
|-------|--------|------------------|
| Tabela de cM e vocabulário | 31-60 | Regra de domínio congelada |
| Normalização e decomposição de nome | 74-176 | Tratamento de texto, inclusive mojibake |
| Leitura e agregação do CSV | 183-223 | I/O de arquivo e pandas |
| Índices e matching difuso | 230-347 | Algoritmo de decisão |
| Fluxo principal | 354-409 | Orquestração e montagem da resposta |

O módulo importa `pandas`, `thefuzz`, `networkx` indiretamente e o próprio `path_search`, tudo no topo.
Testar a normalização de nome exige importar o módulo inteiro, com pandas e thefuzz carregados.

## Transformação proposta

Extrair por fronteira de responsabilidade, na ordem do menor risco para o maior:

1. `name_normalization.py` (ou reaproveitar `domain.py`, ver `OPP-20260929-4LE3`): `strip_bad_utf`,
   `norm_name`, `split_name_pt`, `surnames_set`, `demojibake`, `drop_short_tokens`,
   `surname_core_tokens`, `top_given_tokens`, `token_prefixes`, `soft_prefix_jaccard`.
2. `csv_ingest.py`: `read_csv_with_fallback`, `detect_columns`, `aggregate_matches`.
3. `matching.py`: `build_ged_indexes`, `match_candidates`.
4. `dna_analysis.py` fica com a tabela de cM, `get_relationships_by_cm` e o fluxo principal.

A extração é mecânica: mover função, atualizar import, reexportar o nome antigo se algum teste
importar de `dna_analysis`. Nenhum corpo de função muda.

## Rede de segurança exigida

- `tests/test_dna_analysis.py` (11 testes) verde antes e depois.
- `tests/test_domain.py` verde, se o passo 1 reusar `domain.py`.
- Harness de paridade verde, que é o que garante que a extração não alterou nenhum caminho de decisão.

## Risco

Médio, e concentrado num ponto: os testes importam de `reconstructed.dna_analysis`. Se a extração não
reexportar os nomes antigos, os testes quebram por import e mascaram uma regressão real. Reexportar
durante a transição e só depois limpar.

## Observação

Este é o passo que habilita a `OPP-20260929-AU76` a ficar menor e mais legível, mas não é pré-requisito
dela. A otimização pode ser feita antes, sozinha e com diff pequeno.

---
*Gerado pelo Reversa-Refactor em 2026-09-29.*
