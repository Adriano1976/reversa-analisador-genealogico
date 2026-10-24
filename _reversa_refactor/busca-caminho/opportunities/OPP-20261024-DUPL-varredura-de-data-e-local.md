---
schema_version: 1
id: OPP-20261024-DUPL
display_number: 55
context: busca-caminho
verb: simplify
title: A mesma varredura escrita duas vezes para DATE e para PLAC
target:
  files:
    - src/core/documentary_relationship.py
  symbol: _data_de, _local_de, hop_evidence
smell: >
  `_data_de` e `_local_de` são a mesma função com uma string trocada. Em `hop_evidence`
  a varredura de HUSB/WIFE aparece três vezes, e a montagem do casal repete o que
  `_construir_indice_de_filhos` já faz. Duplicação de estrutura, não de valor.
roi:
  confidence: green
  impact: >
    Divergência silenciosa: no dia em que a leitura de DATE ganhar um caso de fallback,
    PLAC fica para trás e a ficha passa a mostrar local de nascimento ausente só para
    algumas pessoas. O custo de corrigir depois é maior do que o de unificar agora.
  cost: low
  est_return: >
    Uma varredura parametrizada no lugar de duas, e um único `_casal_da_familia` no lugar
    de três leituras independentes de HUSB e WIFE.
state: applied
traceability:
  soul: [.reversa/soul.md#e7-parentesco_documental]
  specs:
    - _reversa_sdd/code-analysis.md
    - _reversa_sdd/data-dictionary.md
---

## Antes observado

As duas funções, lado a lado:

```python
def _data_de(people, pid, tag):          # linhas 93 a 102
    pessoa = people.get(pid)
    if not pessoa:
        return None
    for rec in pessoa.sub_records:
        if rec.tag == tag:
            for sub in rec.sub_records:
                if sub.tag == "DATE":
                    return str(sub.value)
    return None

def _local_de(people, pid, tag):         # linhas 113 a 122
    pessoa = people.get(pid)
    if not pessoa:
        return None
    for rec in pessoa.sub_records:
        if rec.tag == tag:
            for sub in rec.sub_records:
                if sub.tag == "PLAC":
                    return str(sub.value)
    return None
```

Vinte linhas para uma. A diferença é uma constante.

Em `hop_evidence` (linhas 386 a 434) a mesma varredura de cônjuges aparece três vezes:

```python
399: if candidata and parent_id in {ref_id(r.value) for r in candidata.sub_records if r.tag in ("HUSB", "WIFE")}:
407: pais = {ref_id(r.value) for r in fam.sub_records if r.tag in ("HUSB", "WIFE")}
413: husb = next((ref_id(r.value) for r in fam.sub_records if r.tag == "HUSB"), None)
414: wife = next((ref_id(r.value) for r in fam.sub_records if r.tag == "WIFE"), None)
```

E `_construir_indice_de_filhos` (linhas 203 a 210) faz a quarta leitura dos mesmos dois
tags, com a mesma semântica.

## Transformação proposta

1. `_sub_valor(people, pid, tag, sub_tag)` com a varredura única; `_data_de` e `_local_de`
   viram duas linhas cada, chamando com `"DATE"` e `"PLAC"`;
2. `_casal_da_familia(familia)` devolvendo `(husb, wife)`, usado por `hop_evidence` nas
   duas passagens e por `_construir_indice_de_filhos` no laço que hoje repete a leitura;
3. `_pais_da_familia(familia)` devolvendo o conjunto, para as duas checagens de
   pertencimento.

## Fronteira de comportamento

Nenhuma. As quatro leituras fazem exatamente a mesma coisa hoje, inclusive devolver o
primeiro HUSB e o primeiro WIFE quando o registro repete o tag, que é o que `next()`
faz e o que o laço de `_construir_indice_de_filhos` também faz ao sobrescrever a variável.
A ordem de varredura de `sub_records` é preservada em todas.

## O que fica de fora, e por quê

`hop_evidence` devolve doze chaves, e três delas nunca são lidas em lugar nenhum:
`link_source`, `family_husband` e `family_wife`. A varredura em `src/`, `tests/` e nos
templates devolve zero leituras para as três. Elas **não** entram nesta transformação
porque são contrato documentado, e não código morto:

| Artefato | O que fixa |
|---|---|
| `_reversa_sdd/data-dictionary.md:335` e `:338` | as três chaves, com tipo e valor |
| `_reversa_sdd/code-analysis.md:540` (`BR-C-48`) | "sem família localizada, `link_source` diz isso" |
| `_reversa_sdd/busca-caminho/requirements.md:77` e `tasks.md:127` (`T-18`) | critério de pronto que nomeia `link_source` |

Remover as três muda contrato de documento e pertence ao ciclo forward com atualização de
spec, não ao time Code Quality. Ficam registradas aqui para que ninguém as trate como
peso morto na próxima varredura.

## Aplicada em 2026-10-24

Aprovada em plano e em diff, aplicada pelo `/reversa-simplify` na mesma data. `_sub_valor`
substituiu as duas varreduras; `_pais_da_familia` e `_familia_que_liga` deram nome à regra
de "a primeira família que liga vence".

O `_casal_da_familia` que esta oportunidade propunha foi **descartado na aplicação**, com a
medição: o helper teria mais linhas do que as quatro leituras que substituiria e
acrescentaria uma passada sobre `sub_records` em `_construir_indice_de_filhos`.

Prova de equivalência contra a versão de `HEAD`, na árvore real de 35.459 pessoas:
86.497 casos comparados, **0 divergências**. O instrumento foi calibrado com uma diferença
injetada, que ele acusou em 221 casos.

| Antes | Depois |
|---|---|
| 2 funções de 10 linhas idênticas | 1 varredura de 10 linhas e 2 funções de 1 linha |
| 2 laços "primeira família que liga" | 1, dentro de `_familia_que_liga` |
| 21 linhas de `hop_evidence` | 8 |
| 1635 testes | 1635 testes, nada mudou de estado |

Evidência em
[`before-after/`](../transformations/OPP-20261024-DUPL-varredura-de-data-e-local/before-after/)
e registro completo no
[`transformation.md`](../transformations/OPP-20261024-DUPL-varredura-de-data-e-local/transformation.md).

---
*Gerado pelo Reversa-Refactor em 2026-10-24, na auditoria de `src/core/documentary_relationship.py`.*
