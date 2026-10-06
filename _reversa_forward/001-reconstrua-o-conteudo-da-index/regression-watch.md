# Regression Watch — 001-reconstrua-o-conteudo-da-index

> Identificador da feature: `001-reconstrua-o-conteudo-da-index`
> Data: 2026-08-11
> Cenário: legado (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Watch principal

Nenhum watch item gerado nesta rodada: o `legacy-impact.md` não registra regras 🟢 do `domain.md` como "Modificadas" (nenhuma regra de negócio foi alterada ou removida).

> Registro de contexto: a alteração funcional desta feature (Mermaid `securityLevel: 'strict'`) é decisão de frontend/segurança (D-02), não regra de domínio, e portanto não ganha peso de regressão no watch principal.

## Observações

Itens sem peso de regressão (originalmente 🟡/🔴 ou não derivados de regra 🟢 modificada):

| ID | Origem | Item | Tipo |
|----|--------|------|------|
| OBS-01 | `_reversa_sdd/confidence-report.md` (reclassificação do Reviewer) | `HARD_MIN=92` e `GIVEN_MIN=90` em `app.py` são código morto — os limiares reais são literais nas regras A/B/C/D. Reclassificado de 🟢 para 🟡. | confidência |
| OBS-02 | `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md#9` | Mermaid inicializado com `securityLevel: 'strict'` no `templates/index.html` (antes `'loose'`). Não é regra de domínio; será confirmado como 🟢 numa futura re-extração sobre o código atualizado. | presença |

## Histórico de re-extrações

### Re-extração 2026-10-05 03:05

| ID | Veredito | Observação |
|----|----------|------------|
| —  | ⚪ n/a | `## Watch principal` vazia nesta feature: nenhum watch item foi criado, portanto não há regra sob vigilância a conferir. |

**Verificações de contexto (itens de `## Observações`, sem peso de regressão):**

- `OBS-01` (`HARD_MIN`/`GIVEN_MIN`, confidência) — ✅ **RESOLVIDO nesta re-extração.** Os dois continuam **inexistentes** no código (zero ocorrências em `src/`), e agora isso está documentado nos artefatos **principais**: `analise-dna/requirements.md` (MoSCoW, `Won't`), `analise-dna/tasks.md` (aviso de não criar constantes nomeadas) e `adrs/08`. A reclassificação 🟢→🟡 que originou este OBS perdeu o objeto.
- `OBS-02` (`securityLevel: 'strict'`, presença) — ✅ **RESOLVIDO nesta re-extração.** A extração anterior não o registrava em artefato ancorado; esta registra em `inventory.md` §4 (configurações internas), `c4-context.md` (elemento "CDN web") e `c4-containers.md` (container 2). O código segue com `securityLevel: 'strict'` em `templates/index.html`.

> **Esta é a primeira re-extração REAL desde a publicação deste watch.** A passagem de 2026-09-30 conferiu o SDD de 2026-08-03, ainda congelado — a própria nota de cronologia dizia isso. Agora o `_reversa_sdd/` foi regenerado a partir do código de 2026-10-05.

### Re-extração 2026-09-30 18:15

| ID | Veredito | Observação |
|----|----------|------------|
| —  | ⚪ n/a | `## Watch principal` vazia nesta feature: nenhum watch item (`W001`…) foi criado, portanto não há regra sob vigilância a conferir. |

**Verificações de contexto feitas nesta passagem (itens de `## Observações`, sem peso de regressão — não são watch items):**

- `OBS-01` (`HARD_MIN`/`GIVEN_MIN` como código morto, confidência) — permanece reclassificado 🟡 no SDD atual: `confidence-report.md` e `analise-dna/design.md` seguem descrevendo ambos como declarados e nunca usados. O adendo `003-refactor-code-quality` corrigiu que os dois **não existem** no módulo reconstruído. Veredito 🟡 amarelo: expectativa não bateu e a divergência já está registrada em adendo.
- `OBS-02` (`securityLevel: 'strict'`, presença) — **ausente** de todos os artefatos principais do SDD. O comportamento está confirmado no código atual (`analisador-genealogico/templates/index.html:182`) e aparece nos goldens (`_reversa_sdd/screens/golden/SCR-001` e `SCR-G02`) e no adendo `001`, mas nunca em `architecture.md`, `domain.md` ou nos specs por feature. Veredito 🟡 amarelo: evidência presente nos artefatos de tela, ausente no artefato ancorado (`architecture.md#2`).

**Nota de cronologia — leia antes de confiar no SDD.** Os artefatos principais de `_reversa_sdd/` foram gerados na extração de **2026-08-03** e **não foram regenerados** desde então. Esta verificação não é uma re-extração real. Os adendos `_reversa_sdd/addenda/001`, `002` e `003` descrevem o código **posterior** a esse congelamento, e `architecture.md` ainda os contradiz (por exemplo, `architecture.md:101` ainda afirma "Código monolítico (app.py ~887 linhas)"). Trate os adendos como estado mais recente até que uma re-extração real rode.

## Arquivadas

*(Vazio.)*

---
*Gerado pelo Reversa-Coding em 2026-08-11.*
