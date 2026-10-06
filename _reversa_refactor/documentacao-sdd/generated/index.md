<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-refactor em 2026-10-06 a partir de 1 oportunidade -->

# Índice de qualidade de código · documentacao-sdd

> Gerado em `2026-10-06`. Fonte de verdade: `../opportunities/*.md`.
> Desvio entre os artefatos de extração em `_reversa_sdd/` e o código depois das transformações
> de 2026-10-06.

## Oportunidades

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #33 | `OPP-20261006-W4KD` | standardize | green | 4 afirmações viraram falsas, duas delas sobre onde mora a decisão de negócio, e 2 módulos novos não existem em artefato algum | low | proposed | specs alinhadas ao código, com o ciclo extinto e os módulos novos registrados |

## Afirmações desatualizadas

| Locator | Situação |
|---|---|
| `architecture.md:68` | tabela do ciclo `core/` ↔ `reporting/`: seta removida pela `ULVW` |
| `architecture.md:73` | "`reporting/` não é folha, e não pode ser": falsa quanto ao mecanismo |
| `architecture.md:141` | dívida 5 lista dois ciclos; resta um |
| `c4-components.md:159` | tabela do ciclo, mesma seta |
| `c4-components.md:164` | "não é folha, e não pode ser" |
| `c4-context.md:46` e `architecture.md:47` | "os quatro pacotes não formam camadas acíclicas": agora é um ciclo |

## Módulos novos, ausentes de todo artefato

| Novo | Criado por | Deveria aparecer em |
|---|---|---|
| `src/core/diagram_domain.py` | `OPP-20261006-ULVW` | `inventory.md`, `c4-components.md`, `code-analysis.md` |
| `src/utils/name_keys.py` | `OPP-20261006-LIGH` | idem, mais `data-dictionary.md` |

## Bloqueio de política

Os alvos estão em `_reversa_sdd/`, que **não está nos `allowedPaths`**. Testado contra a lista:
`_reversa_sdd/architecture.md` e `_reversa_sdd/c4-components.md` são **recusados**. Nenhuma escrita
foi feita, e nenhuma será sem edição da config pelo usuário.

Três caminhos possíveis, e a escolha é do usuário: liberar `_reversa_sdd/**` e rotear a
`/reversa-standardize`; registrar um **adendo**, como o `addenda/003-renomear-pasta-app-para-src.md`
já faz para as transformações de 2026-10-03; ou nova re-extração.

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`

---
*Gerado pelo Reversa-Refactor em 2026-10-06.*
