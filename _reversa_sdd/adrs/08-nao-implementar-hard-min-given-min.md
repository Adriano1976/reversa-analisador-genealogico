# ADR-08 — Não implementar `HARD_MIN` / `GIVEN_MIN`

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-08-07 (durante a reconstrução), reforçado em 2026-09-28
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O monolito original declarava duas constantes com nome de regra de negócio — `HARD_MIN = 92` e `GIVEN_MIN = 90` — na altura das regras de aceitação de candidatos. Elas **não eram referenciadas em lugar nenhum** do arquivo: os limiares reais viviam como literais dentro dos ramos de aceitação.

## Decisão

Tratar as duas constantes como **código morto** e **não** implementá-las na reconstrução, mantendo os limiares como **literais dentro das regras**. Não criar uma "constante canônica" que nunca existiu de fato.

## Evidência

- `_reversa_sdd/oracle/app_legacy_e43ca22.py:653-654` — as declarações originais.
- `empiricalFindings.deadCodeConfirmed` em `migration/.state.json` — *"HARD_MIN=92 (L653) e GIVEN_MIN=90 (L654) não são referenciados em nenhum outro ponto do arquivo"*.
- `migration/data_migration_plan.md` e `reconstruction-plan.md`.
- **Verificação no código de 2026-10-05:** zero ocorrências de `HARD_MIN` ou `GIVEN_MIN` em `src/`. Os limiares vivem nos cinco ramos de `src/core/matching.py:140-149`.

## Justificativa

Uma constante que ninguém lê **não é regra** — é ruído com aparência de regra. Promovê-la a configuração criaria uma alavanca inexistente e sugeriria ao reimplementador que os limiares são ajustáveis, quando a decisão humana de 2026-08-03 é que as regras de aceitação são **definitivas e preservadas com fidelidade**.

## Consequências

- ⚠️ **Consequência documental, e ela é instrutiva.** As specs da extração anterior passaram a afirmar que as constantes estavam *"declaradas mas não usadas **na reconstrução**"* — o que é **falso**, porque **nunca existiram** ali. A frase descrevia o monolito e foi escrita como se descrevesse o código novo. Isso é a origem de `OBS-03` da feature `002` estar errado, e está corrigido no `_reversa_sdd/addenda/003-refactor-code-quality.md`.
- 🟢 **A verificação que fechou o assunto foi por varredura de código, não por leitura de spec** — e é o mesmo padrão de erro (`AMB-023`, `DIV-001`) que motivou o oráculo congelado do ADR-04.
- 🟢 **Efeito prático hoje: nenhum.** O comportamento é idêntico ao do legado. A decisão existe para que ninguém "restaure" as constantes achando que encontrou uma regra perdida.

## Alternativas consideradas

- **Implementar as constantes como configuração e usá-las nos ramos.** Descartada: mudaria o comportamento (92 e 90 **não** são os limiares efetivos dos cinco ramos) e quebraria a paridade.
- **Implementar como constantes mortas, por fidelidade literal.** Descartada: preservaria o defeito de leitura que o ADR existe para eliminar.
