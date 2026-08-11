# Data Delta — integrar a rota index() do app.py com os modulos reconstruidos

> Identificador: `002-integrar-rota-app-modulos`
> Data: `2026-08-11`

## Resumo

**Nenhuma mudança no modelo de dados.** O sistema mantém o estado 100% em memória (dicionários `people`, `families`, `child_to_family` + grafo `networkx`), sem persistência, exatamente como descrito em `_reversa_sdd/architecture.md#3`.

## Diff conceitual

| Entidade | Antes | Depois | Mudança |
|----------|-------|--------|---------|
| `people` (PERSON) | Global em `app.py` | Global no módulo `upload.py` movido para `analisador-genealogico/` | movimentação de local, sem mudança de schema |
| `families` (FAMILIA) | Global em `app.py` | Global no módulo `upload.py` movido | movimentação de local |
| `graph` (networkx) | Global em `app.py` | Global no módulo `upload.py` movido | movimentação de local |
| `child_to_family` | Global em `app.py` | Global no módulo `upload.py` movido | movimentação de local |
| `DNA_MATCH` (agregado) | Derivado em memória no fluxo DNA | Derivado em `dna_analysis.py` movido | movimentação de local |

## Campos novos / removidos

- Nenhum campo novo.
- Nenhum campo removido.

## Migrações necessárias

- **n/a** — sem persistência, sem migração de dados. A única "migração" é de localização de código (mover módulos), tratada no plano de migração do `roadmap.md`.

## Impacto em fixtures de teste

- Os testes existentes (`tests/`) referenciam `reconstructed.*`. Com a movimentação, os imports dos testes precisam ser atualizados para o novo caminho (ex.: `analisador-genealogico.reconstructed.*` ou o novo subpacote). Isso é cobertura de código, não delta de dados.
