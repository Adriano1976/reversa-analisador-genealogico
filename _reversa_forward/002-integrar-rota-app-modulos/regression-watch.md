# Regression Watch — 002-integrar-rota-app-modulos

> Identificador da feature: `002-integrar-rota-app-modulos`
> Data: 2026-08-11
> Cenário: legado (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Watch principal

Nenhum watch item gerado nesta rodada: o `legacy-impact.md` não registra regras 🟢 do `domain.md` como "Modificadas" (nenhuma regra de negócio teve comportamento alterado ou removido — a mudança foi estrutural: localização do código).

## Observações

Itens sem peso de regressão (mudanças estruturais/refactor que uma futura extração deverá refletir, mas que não alteram regras 🟢):

| ID | Origem | Item | Tipo |
|----|--------|------|------|
| OBS-01 | `_reversa_sdd/architecture.md#5` (dívida técnica de acoplamento) | `app.py` deixou de conter a lógica inline duplicada; rotas delegam a `analisador-genealogico/reconstructed/`. A extração futura deve descrever o app como camada de rota fina + módulos internos. | presença |
| OBS-02 | `_reversa_sdd/reconstruction-report.md` | Módulos `upload.py`, `path_search.py`, `dna_analysis.py`, `domain.py` agora residem em `analisador-genealogico/reconstructed/` (fora da raiz). Importante para quem ler o mapeamento de arquivos. | presença |
| OBS-03 | `_reversa_sdd/confidence-report.md` (reclassificação do Reviewer) | `HARD_MIN=92` / `GIVEN_MIN=90` como código morto foi preservado nos módulos reconstruídos (declarados, não usados) — comportamento idêntico ao legado. | confidência |

## Histórico de re-extrações

### Re-extração 2026-10-05 03:05

| ID | Veredito | Observação |
|----|----------|------------|
| —  | ⚪ n/a | `## Watch principal` vazia nesta feature: nenhum watch item foi criado, portanto não há regra sob vigilância a conferir. |

**Verificações de contexto (itens de `## Observações`, sem peso de regressão):**

- `OBS-01` (`app.py` como camada de rota fina, presença) — ✅ **RESOLVIDO nesta re-extração.** O `architecture.md` regenerado descreve a rota como **camada fina de 267 linhas com zero regra de negócio**, e a dívida do monolito saiu da tabela de dívidas vivas (está na tabela de dívidas **fechadas**). O SDD anterior, congelado em 2026-08-03, é que ainda dizia "monolítico (~887 linhas)".
- `OBS-02` (módulos em `reconstructed/`, presença) — ✅ **RESOLVIDO nesta re-extração.** O nível `reconstructed/` **não existe mais**: o núcleo é `core/` + `parsers/` + `reporting/` + `utils/`, importados direto de `src/` (ver `adrs/11` e o `W001` da feature 003). Nenhum artefato regenerado cita `reconstructed/` como estrutura atual.
- `OBS-03` (`HARD_MIN`/`GIVEN_MIN` preservados, confidência) — ✅ **RESOLVIDO nesta re-extração.** O próprio OBS-03 estava errado (o código nunca os teve), e o adendo `003-refactor-code-quality` já o corrigia. Agora os artefatos principais também o corrigem: `adrs/08` e a nota de `analise-dna/tasks.md`.

> **Esta é a primeira re-extração REAL desde a publicação deste watch** — a passagem de 2026-09-30 conferiu o SDD de 2026-08-03, ainda congelado.

### Re-extração 2026-09-30 18:15

| ID | Veredito | Observação |
|----|----------|------------|
| —  | ⚪ n/a | `## Watch principal` vazia nesta feature: nenhum watch item (`W001`…) foi criado, portanto não há regra sob vigilância a conferir. |

**Verificações de contexto feitas nesta passagem (itens de `## Observações`, sem peso de regressão — não são watch items):**

- `OBS-01` (`app.py` como camada de rota fina, presença) — **ausente** do SDD principal. `architecture.md:101` ainda classifica "Código monolítico (app.py ~887 linhas) com rotas + lógica acopladas" como dívida técnica vigente, e a frase espelha o estado pré-feature. O adendo `002` já registra que a dívida nº 5 foi endereçada. Veredito 🟡 amarelo: expectativa não bateu no artefato ancorado, com delta registrado em adendo.
- `OBS-02` (módulos em `analisador-genealogico/reconstructed/`, presença) — parcialmente presente no SDD, mas no local **antigo**: `reconstruction-report.md` lista `reconstructed/domain.py`, `upload.py`, `path_search.py` e `dna_analysis.py` (raiz). O adendo `002` registra a promoção para `analisador-genealogico/reconstructed/`. Veredito 🟡 amarelo: mesma essência semântica, caminho desatualizado.
- `OBS-03` (`HARD_MIN`/`GIVEN_MIN` preservados na reconstrução, confidência) — **o próprio OBS-03 está errado**, não o SDD. O adendo `003-refactor-code-quality` (§ Impacto por artefato, linha de `regression-watch.md`) registra que "o código nunca os teve" e corrige este OBS-03 explicitamente. O SDD permanece 🟡 em `confidence-report.md` e `analise-dna/design.md`. Veredito 🔴 vermelho: item de observação refutado por evidência e já corrigido por adendo — nenhuma ação pendente, mantido como registro.

**Nota de cronologia — leia antes de confiar no SDD.** Os artefatos principais de `_reversa_sdd/` foram gerados na extração de **2026-08-03** e **não foram regenerados** desde então. Esta verificação não é uma re-extração real. Os adendos `_reversa_sdd/addenda/001`, `002` e `003` descrevem o código **posterior** a esse congelamento, inclusive a mudança estrutural desta feature, que `architecture.md` ainda não reflete. Trate os adendos como estado mais recente até que uma re-extração real rode.

## Arquivadas

*(Vazio.)*

---
*Gerado pelo Reversa-Coding em 2026-08-11.*
