---
schema_version: 1
id: OPP-20261023-DONO
display_number: 37
context: analise-dna
verb: standardize
title: Parâmetro dono sem comportamento na assinatura do caso de uso
target:
  files: [src/application/dna_analysis.py]
  symbol: dna_analysis (parâmetro dono)
smell: >
  O parâmetro `dono: str` em dna_analysis() é declarado na própria docstring como "não usado
  para comportamento nesta onda (RN-06, RF-08): está na assinatura como costura". É código de
  interface sem implementação correspondente: um parâmetro que entra, não é lido e não influencia
  nenhuma saída.
roi:
  confidence: green
  impact: >
    O parâmetro foi preservado intencionalmente e sua docstring foi explicitada no código:
    ele é repassado a `registro.registrar(analise, dono)` e inserido em `owner_id TEXT NOT NULL`
    no Postgres, sendo necessário para o schema do banco e compatibilidade da Onda 3.
  cost: low
  est_return: >
    Decisão documentada formalmente e esclarecida na docstring do caso de uso.
state: applied
promoted_to: null
traceability:
  soul: []
  specs:
    - _reversa_sdd/analise-dna/requirements.md#RF-08
    - _reversa_sdd/adrs/26-dono-no-port-como-costura.md
    - _reversa_sdd/permissions.md
---

## Antes observado

```python
def dna_analysis(caminho_do_csv: str, root_name: str, arvore, deps,
                 dono: str, referencia_da_arvore: str | None = None,
                 registro=None, candidatos_fixos=None) -> ResultadoDeAnalise:
    """
    `dono` **não** é usado para comportamento nesta onda (RN-06, RF-08): está na
    assinatura como costura, e nenhum isolamento é implementado.
    """
```

O único uso do parâmetro `dono` no corpo da função é o repasse para `registro.registrar(analise, dono)`
na linha 326. O registro grava `dono` como `owner_id TEXT NOT NULL` no Postgres, mas nenhuma
consulta filtra por ele (conforme `_reversa_sdd/permissions.md` e `state.json`).

## Classificação

**Órfão suspeito**, não morto confirmado. O parâmetro tem uso (repasse ao registro), mas o efeito
do uso é nulo do ponto de vista funcional. A decisão de removê-lo depende do destino da Onda 3:

| Cenário | Ação |
|---|---|
| Onda 3 cancela o isolamento no legado | Remover `dono` da assinatura e do INSERT |
| Onda 3 implementa isolamento | Manter; o parâmetro começa a ser lido nas consultas |
| Decisão adiada | Adicionar `# noqa: ARG001` ou docstring de stub intencional |

## Nota de risco

A remoção quebra os chamadores em `src/app.py` (que passa `dono` ao chamar `dna_analysis`).
O glob `src/**` está liberado em `reversa-config.json`. Qualquer especialista que aplique esta
oportunidade precisa varrer `app.py` para ajustar a chamada.

## Decisão (2026-10-23): o prune foi recusado

O parametro nao e decorativo: `src/ports/adaptadores.py` grava `dono` em
`owner_id TEXT NOT NULL`, e o `ADR-26` declara o dono no port como costura da
Onda 3. O que falta e isolamento nas consultas, registrado em `permissions.md`, e
nao o parametro. Remover exigiria mexer na assinatura da porta, no `INSERT` e no
chamador `src/app.py`, sem ganho funcional e com perda do rastro do dono no
schema.

O que se aplicou foi a **padronizacao da documentacao**: a docstring de
`dna_analysis` passou a dizer para onde o valor vai e por que ele fica. Por isso
o verbo registrado e `standardize`, e nao `prune`. Ver
`transformations/OPP-20261023-DONO-parametro-dono-sem-comportamento/transformation.md`.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*
