---
schema_version: 1
id: OPP-20260929-AU76
verb: optimize
state: applied
safety_net:
  kind: characterization
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - safety-net/equivalence-after-apply.txt
    - safety-net/pytest-after-apply.txt
    - before-after/measurement.txt
    - before-after/measurement-after-apply.txt
measurement:
  before: "27,77 ms por match; 728,2 chamadas de norm_name por match (3.000 pessoas, 100 matches, mediana de 3)"
  after: "2,29 ms por match; 4,0 chamadas de norm_name por match; ganho de 12,13x"
  complexity: "O(M x P) antes e depois: o ganho e de fator constante, nao algoritmico"
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/dna_analysis.py
    purpose: Pre-calcula os atributos normalizados por pessoa em build_ged_indexes e os consome no laco de match_candidates, eliminando a renormalizacao repetida
    diff: CHG-001.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff]
---

## O que foi feito

O laco de candidatos renormalizava o nome do candidato a cada match do CSV, para um
valor que nao depende do CSV: 7,28 chamadas de `norm_name` por candidato.

Numero medido depois da aplicacao, contra a linha de base congelada: **27,77 ms para 2,29 ms por
match, 12,13x**, com as chamadas de fuzzy inalteradas (413 por match antes e depois), o que confirma
que a otimizacao mexeu apenas na renormalizacao. `build_ged_indexes` ficou 1,5x mais lento, porque
passou a calcular o cache: e trabalho deslocado para fora do laco.

Ponto de equilibrio em cerca de 15 matches por CSV. Abaixo disso ha regressao de no maximo 0,43 s por
analise, aceita porque um CSV do GEDmatch tem centenas a milhares de matches.

Prova de equivalencia: 2.206 comparacoes contra a linha de base, incluindo string vazia, `None`,
mojibake, truncamento e cM em 0, -1, 149,9, 150, 3720 e `None`. **Zero divergencias**, inclusive na
string de motivo que carrega os valores calculados. Suite verde.

Alternativas descartadas com motivo no plano: podar o pool com o `given_index` morto (muda o
vencedor, logo e Forward), `lru_cache` (cache global de crescimento nao limitado) e trocar `thefuzz`
por `rapidfuzz` direto (o backend ja e rapidfuzz, retorno zero).

## Estado dos arquivos

`409` linhas antes, `424` depois.
