---
schema_version: 1
id: OPP-20261023-DONO
verb: standardize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: pattern-only
  evidence:
    - before-after/suite-antes.txt
    - before-after/suite-depois.txt
measurement:
  before: "docstring do parametro `dono` declarava apenas 'nao e usado para comportamento nesta onda', sem dizer para onde o valor vai"
  after: "docstring declara a costura da Onda 3, o repasse a `registro.registrar` e a coluna `owner_id TEXT NOT NULL`"
change_set:
  - chg: CHG-LOTE
    file: src/application/dna_analysis.py
    purpose: reescreve a docstring do parametro `dono`; nenhuma linha executavel muda
approval:
  by: user
  at: 2026-10-23T00:53:05-03:00
reversible_via: [../OPP-20261023-MPRA-mistura-caso-uso-projecao/CHG-LOTE-extracao-e-mapper.diff]
---

# Transformacao: OPP-20261023-DONO (documentar a costura do `dono`)

## O prune foi avaliado e recusado

A oportunidade nasceu como `prune`, com a classificacao correta de **orfao
suspeito**: `dono` entra na assinatura de `dna_analysis` e o unico uso no corpo e
o repasse a `registro.registrar(analise, dono)`. A investigacao mostrou que o
valor nao e decorativo:

- `src/ports/adaptadores.py` grava `dono` na coluna `owner_id TEXT NOT NULL`;
- o `ADR-26` declara o dono no port como costura da Onda 3;
- `permissions.md` registra que **nenhuma consulta filtra por ele** — o que torna
  o parametro inerte hoje, e nao removivel sem quebrar contrato de porta e
  schema.

Remover o parametro exigiria mexer na assinatura da porta, no `INSERT` e no
chamador `src/app.py`, para nenhum ganho funcional e com perda de rastro do dono
no schema. A decisao registrada foi **recusar o prune**.

## O que foi aplicado

Só a docstring mudou:

```python
# antes
`dono` **nao** e usado para comportamento nesta onda (`RN-06`, `RF-08`): esta
na assinatura como costura, e nenhum isolamento e implementado.

# depois
`dono` e uma costura arquitetural intencional da Onda 3 (`RN-06`, `RF-08`,
`ADR-26`): e repassado para `registro.registrar(analise, dono)` e gravado na
coluna `owner_id TEXT NOT NULL` do Postgres. Nesta onda nao aplica isolamento
comportamental em consultas, sendo mantido para integridade de schema e futura
expansao.
```

Nenhuma linha executavel muda. `preservation.method: pattern-only`, porque a
transformacao e de documentacao: o que se prova e que a suite continua igual, e
nao uma equivalencia de saida.

## Nota de schema

A oportunidade estava registrada como `verb: prune` com `state: applied`, o que
contradiz a regra do proprio registro (prune aplicado exige `death-proof`, e nao
houve poda). A reconciliacao de 2026-10-23 mudou o verbo para `standardize` e
manteve `applied`, com a recusa do prune registrada no corpo da oportunidade.

## Diff acumulado

O diff e o das quatro transformacoes de `analise-dna`, pelo motivo declarado em
`OPP-20261023-MPRA`: as etapas foram empilhadas antes da captura.

## Rede de seguranca

| Momento | Resultado |
|---|---|
| linha de base HEAD 221b6c1 | 1615 passed, 9 skipped |
| working tree depois do lote | 1615 passed, 9 skipped |

Ver [suite-antes.txt](before-after/suite-antes.txt) e
[suite-depois.txt](before-after/suite-depois.txt).
